"""Continuous data streaming — generates and ingests at a configured events-per-minute rate."""

import threading
import time
import json
import datetime
import requests
from data_generators import DATA_GENERATORS

# ---------------------------------------------------------------------------
# Module-level state (access via _lock for thread safety)
# ---------------------------------------------------------------------------
_state: dict = {
    "active": False,
    "data_type": None,
    "rate_per_min": 0,
    "total_generated": 0,
    "started_at": None,
    "stopped_at": None,
    "last_error": None,
}
_lock = threading.Lock()
_stop_event = threading.Event()
_thread: threading.Thread | None = None


def get_status() -> dict:
    """Return a copy of the streaming state, augmented with derived fields."""
    with _lock:
        s = dict(_state)
        started_at = s["started_at"]

    elapsed = 0.0
    actual_rate = 0.0
    if s["active"] and started_at:
        elapsed = (datetime.datetime.now() - started_at).total_seconds()
        actual_rate = round(s["total_generated"] / max(elapsed / 60.0, 0.01), 1)

    s["elapsed_seconds"] = int(elapsed)
    s["actual_rate"] = actual_rate
    s["started_at"] = started_at.isoformat() if started_at else None
    stopped = s.get("stopped_at")
    s["stopped_at"] = stopped.isoformat() if stopped else None
    return s


def start_streaming(data_type: str, rate_per_min: int, config: dict,
                    max_events: int = 0) -> tuple[bool, str]:
    """Spawn the background streaming thread.

    Returns (True, '') on success or (False, reason) if already active or invalid.
    """
    global _thread, _stop_event

    with _lock:
        if _state["active"]:
            return False, "A stream is already active. Stop it first."
        if data_type not in DATA_GENERATORS:
            return False, f"Unknown data type: {data_type}"
        if not (1 <= rate_per_min <= 10_000):
            return False, "Rate must be between 1 and 10,000 events/minute."

        _stop_event = threading.Event()
        _state.update({
            "active": True,
            "data_type": data_type,
            "rate_per_min": rate_per_min,
            "total_generated": 0,
            "started_at": datetime.datetime.now(),
            "stopped_at": None,
            "last_error": None,
        })

    _thread = threading.Thread(
        target=_worker,
        args=(data_type, rate_per_min, config, max_events, _stop_event),
        daemon=True,
    )
    _thread.start()
    return True, ""


def stop_streaming() -> tuple[bool, str]:
    """Signal the active streaming thread to stop."""
    with _lock:
        if not _state["active"]:
            return False, "No active stream to stop."
    _stop_event.set()
    return True, ""


def _worker(data_type: str, rate_per_min: int, config: dict,
            max_events: int, stop_event: threading.Event) -> None:
    """Background thread: generate entries and bulk-ingest to ES at the target rate."""
    gen_class = DATA_GENERATORS[data_type]["generator"]
    index_name = DATA_GENERATORS[data_type]["index_pattern"]
    es_host = config["elasticsearch"]["host"]
    es_auth = (config["elasticsearch"]["username"], config["elasticsearch"]["password"])

    # Target: one batch per second. Batch size = events expected in one second.
    batch_size = max(1, min(int(rate_per_min / 60) + 1, 500))
    sleep_secs = batch_size / (rate_per_min / 60.0)

    gen = gen_class()
    total = 0

    try:
        while not stop_event.is_set():
            if max_events and total >= max_events:
                break

            actual_batch = min(batch_size, max_events - total) if max_events else batch_size

            entries = [gen.generate_entry() for _ in range(actual_batch)]

            bulk_lines = []
            for entry in entries:
                bulk_lines.append(json.dumps({"index": {}}))
                bulk_lines.append(json.dumps(entry, default=str))

            try:
                resp = requests.post(
                    f"{es_host}/{index_name}/_bulk",
                    auth=es_auth,
                    headers={"Content-Type": "application/x-ndjson"},
                    data="\n".join(bulk_lines) + "\n",
                    timeout=15,
                )
                if resp.status_code == 200:
                    total += actual_batch
                    with _lock:
                        _state["total_generated"] = total
                else:
                    with _lock:
                        _state["last_error"] = f"HTTP {resp.status_code}: {resp.text[:200]}"
            except Exception as exc:
                with _lock:
                    _state["last_error"] = str(exc)[:200]

            # Sleep for the remainder of the batch interval (interruptible)
            stop_event.wait(max(0.0, sleep_secs))

    finally:
        with _lock:
            _state["active"] = False
            _state["stopped_at"] = datetime.datetime.now()
            _state["total_generated"] = total
