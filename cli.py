"""Command-line interface for log-data-generator.

Install:
    pip install -e .

Usage:
    ldg generate --type unstructured_logs --entries 5000 --ingest
    ldg generate --type all --entries 1000 --ingest --dashboards
    ldg scenario  --name deployment_failure --entries 500 --ingest
    ldg stream    --type apm_data --rate 120
    ldg stop
    ldg status
    ldg dashboard --type all
    ldg cleanup   --es --csv
"""

import sys
import json
import csv as _csv_mod
import os
import time
import datetime
import click

# ---------------------------------------------------------------------------
# Shared connection options (ES + Kibana)
# ---------------------------------------------------------------------------

_ES_OPTS = [
    click.option("--es-host",     envvar="ES_HOST",       default=None, help="Elasticsearch URL"),
    click.option("--es-user",     envvar="ES_USERNAME",   default=None, help="ES username"),
    click.option("--es-pass",     envvar="ES_PASSWORD",   default=None, help="ES password"),
    click.option("--kibana-host", envvar="KIBANA_HOST",   default=None, help="Kibana URL"),
    click.option("--kibana-user", envvar="KIBANA_USERNAME", default=None, help="Kibana username"),
    click.option("--kibana-pass", envvar="KIBANA_PASSWORD", default=None, help="Kibana password"),
]


def _with_es_opts(fn):
    for opt in reversed(_ES_OPTS):
        fn = opt(fn)
    return fn


def _load_cfg(es_host=None, es_user=None, es_pass=None,
              kibana_host=None, kibana_user=None, kibana_pass=None) -> dict:
    """Load config.json then overlay any explicitly-provided CLI values."""
    try:
        import app as _app
        cfg = _app.load_config()
    except Exception:
        cfg = {
            "elasticsearch": {"host": "http://localhost:9200",
                              "username": "elastic", "password": "changeme"},
            "kibana": {"host": "http://localhost:5601",
                       "username": "elastic", "password": "changeme"},
            "log_generation": {"default_entries": 1000, "max_entries": 1_000_000},
        }
    if es_host:     cfg["elasticsearch"]["host"]     = es_host
    if es_user:     cfg["elasticsearch"]["username"] = es_user
    if es_pass:     cfg["elasticsearch"]["password"] = es_pass
    if kibana_host: cfg["kibana"]["host"]             = kibana_host
    if kibana_user: cfg["kibana"]["username"]         = kibana_user
    if kibana_pass: cfg["kibana"]["password"]         = kibana_pass
    return cfg


def _parse_date_range(date_range: str) -> tuple:
    deltas = {
        "24h":       datetime.timedelta(hours=24),
        "7d":        datetime.timedelta(days=7),
        "30d":       datetime.timedelta(days=30),
        "90d":       datetime.timedelta(days=90),
        "last_year": datetime.timedelta(days=365),
    }
    end = datetime.datetime.now()
    return end - deltas[date_range], end


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------

@click.group()
@click.version_option("1.0.0", prog_name="ldg")
def cli():
    """Log Data Generator — synthetic observability data for Elasticsearch/Kibana."""


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------

@cli.command("generate")
@click.option("--type", "data_type", default="unstructured_logs", show_default=True,
              help="Data type (or 'all').")
@click.option("--entries", default=1000, show_default=True,
              help="Number of entries to generate.")
@click.option("--csv/--no-csv", default=False, help="Write output to a CSV file.")
@click.option("--ingest/--no-ingest", default=False, help="Ingest into Elasticsearch.")
@click.option("--dashboards/--no-dashboards", default=False,
              help="Create Kibana data views and dashboards.")
@click.option("--date-range", default="last_year", show_default=True,
              type=click.Choice(["24h", "7d", "30d", "90d", "last_year"]),
              help="Timestamp range for generated data.")
@_with_es_opts
def cmd_generate(data_type, entries, csv, ingest, dashboards, date_range,
                 es_host, es_user, es_pass, kibana_host, kibana_user, kibana_pass):
    """Generate synthetic observability data."""
    from data_generators import DATA_GENERATORS
    import app as _app

    cfg = _load_cfg(es_host, es_user, es_pass, kibana_host, kibana_user, kibana_pass)
    start_dt, end_dt = _parse_date_range(date_range)

    all_types = list(DATA_GENERATORS.keys())
    types = all_types if data_type == "all" else [data_type]

    if data_type != "all" and data_type not in DATA_GENERATORS:
        click.echo(f"Unknown data type '{data_type}'. "
                   f"Choose from: {all_types + ['all']}", err=True)
        sys.exit(1)

    for dt in types:
        index_name = DATA_GENERATORS[dt]["index_pattern"]
        click.echo(f"  {dt} ({entries} entries)...", nl=False)
        try:
            gen_class = DATA_GENERATORS[dt]["generator"]
            gen = gen_class(start_date=start_dt, end_date=end_dt)
            all_entries = [gen.generate_entry() for _ in range(entries)]

            if csv:
                os.makedirs("output_csv", exist_ok=True)
                path = os.path.join("output_csv", f"{dt}-cli.csv")
                from app import flatten_dict
                flat = [flatten_dict(e) for e in all_entries]
                fieldnames = sorted({k for row in flat for k in row})
                with open(path, "w", newline="", encoding="utf-8") as fh:
                    writer = _csv_mod.DictWriter(fh, fieldnames=fieldnames,
                                                 extrasaction="ignore")
                    writer.writeheader()
                    writer.writerows(flat)
                click.echo(f" csv:{path}", nl=False)

            if ingest:
                _app.ingest_data_to_es(all_entries, index_name, dt, cfg)
                click.echo(f" ingested:{entries}", nl=False)

            if dashboards:
                _create_kibana_objects(dt, index_name, cfg)
                click.echo(" dashboards:ok", nl=False)

            click.echo(" ✓")
        except Exception as exc:
            click.echo(f" ✗ {exc}", err=True)


# ---------------------------------------------------------------------------
# scenario
# ---------------------------------------------------------------------------

@cli.command("scenario")
@click.option("--name", required=True,
              help="Scenario name (deployment_failure, security_incident, database_slowdown).")
@click.option("--entries", default=500, show_default=True,
              help="Entries per data type.")
@click.option("--ingest/--no-ingest", default=False, help="Ingest into Elasticsearch.")
@click.option("--dashboards/--no-dashboards", default=False,
              help="Create Kibana data views and dashboards.")
@click.option("--date-range", default="7d", show_default=True,
              type=click.Choice(["24h", "7d", "30d"]),
              help="Time window for the scenario.")
@_with_es_opts
def cmd_scenario(name, entries, ingest, dashboards, date_range,
                 es_host, es_user, es_pass, kibana_host, kibana_user, kibana_pass):
    """Generate a pre-built correlated scenario across multiple data types."""
    from data_generators import DATA_GENERATORS
    from scenarios import SCENARIOS, generate_scenario_entries
    import app as _app

    if name not in SCENARIOS:
        click.echo(f"Unknown scenario '{name}'. "
                   f"Available: {list(SCENARIOS)}", err=True)
        sys.exit(1)

    cfg = _load_cfg(es_host, es_user, es_pass, kibana_host, kibana_user, kibana_pass)
    start_dt, end_dt = _parse_date_range(date_range)

    meta = SCENARIOS[name]
    click.echo(f"\nScenario: {meta['name']}")
    click.echo(f"  {meta['description']}\n")

    results = generate_scenario_entries(name, entries, start_dt, end_dt)

    for dt, type_entries in results.items():
        index_name = DATA_GENERATORS[dt]["index_pattern"]
        click.echo(f"  {dt}: {len(type_entries)} entries", nl=False)
        try:
            if ingest:
                _app.ingest_data_to_es(type_entries, index_name, dt, cfg)
                click.echo(f" ingested", nl=False)
            if dashboards:
                _create_kibana_objects(dt, index_name, cfg)
                click.echo(f" dashboard:ok", nl=False)
            click.echo(" ✓")
        except Exception as exc:
            click.echo(f" ✗ {exc}", err=True)


# ---------------------------------------------------------------------------
# stream / stop / status
# ---------------------------------------------------------------------------

@cli.command("stream")
@click.option("--type", "data_type", required=True,
              help="Data type to stream continuously.")
@click.option("--rate", default=60, show_default=True,
              help="Target events per minute.")
@click.option("--max", "max_events", default=0,
              help="Stop after this many events (0 = unlimited).")
@_with_es_opts
def cmd_stream(data_type, rate, max_events,
               es_host, es_user, es_pass, kibana_host, kibana_user, kibana_pass):
    """Stream data continuously to Elasticsearch at a target rate."""
    import streaming
    cfg = _load_cfg(es_host, es_user, es_pass, kibana_host, kibana_user, kibana_pass)

    ok, err = streaming.start_streaming(data_type, rate, cfg, max_events)
    if not ok:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)

    limit_msg = f" (max {max_events})" if max_events else " (unlimited)"
    click.echo(f"Streaming {data_type} at {rate} events/min{limit_msg}.")
    click.echo("Press Ctrl+C to stop.\n")

    try:
        while streaming.get_status()["active"]:
            s = streaming.get_status()
            click.echo(
                f"\r  {s['total_generated']:>8} events | "
                f"{s['actual_rate']:>6.1f}/min | "
                f"elapsed {s['elapsed_seconds']}s",
                nl=False,
            )
            time.sleep(2)
    except KeyboardInterrupt:
        streaming.stop_streaming()

    s = streaming.get_status()
    click.echo(f"\nStopped. Total generated: {s['total_generated']} events.")
    if s.get("last_error"):
        click.echo(f"Last error: {s['last_error']}", err=True)


@cli.command("stop")
def cmd_stop():
    """Stop the active streaming session."""
    import streaming
    ok, msg = streaming.stop_streaming()
    click.echo("Stream stop signal sent." if ok else f"Error: {msg}")


@cli.command("status")
def cmd_status():
    """Show current streaming status."""
    import streaming
    s = streaming.get_status()
    if s["active"]:
        click.echo("Status: ACTIVE")
        click.echo(f"  Data type : {s['data_type']}")
        click.echo(f"  Target    : {s['rate_per_min']} events/min")
        click.echo(f"  Actual    : {s['actual_rate']:.1f} events/min")
        click.echo(f"  Total     : {s['total_generated']}")
        click.echo(f"  Elapsed   : {s['elapsed_seconds']}s")
    else:
        click.echo("Status: INACTIVE")
        if s.get("total_generated"):
            click.echo(f"  Last run  : {s['total_generated']} events")
        if s.get("stopped_at"):
            click.echo(f"  Stopped   : {s['stopped_at']}")
    if s.get("last_error"):
        click.echo(f"  Last error: {s['last_error']}", err=True)


# ---------------------------------------------------------------------------
# dashboard
# ---------------------------------------------------------------------------

@cli.command("dashboard")
@click.option("--type", "data_type", default="all",
              help="Data type (or 'all').")
@_with_es_opts
def cmd_dashboard(data_type, es_host, es_user, es_pass,
                  kibana_host, kibana_user, kibana_pass):
    """Create Kibana data views and dashboards."""
    from data_generators import DATA_GENERATORS
    cfg = _load_cfg(es_host, es_user, es_pass, kibana_host, kibana_user, kibana_pass)
    types = list(DATA_GENERATORS.keys()) if data_type == "all" else [data_type]

    for dt in types:
        index_name = DATA_GENERATORS[dt]["index_pattern"]
        click.echo(f"  {dt}...", nl=False)
        try:
            _create_kibana_objects(dt, index_name, cfg)
            click.echo(" ✓")
        except Exception as exc:
            click.echo(f" ✗ {exc}", err=True)


# ---------------------------------------------------------------------------
# cleanup
# ---------------------------------------------------------------------------

@cli.command("cleanup")
@click.option("--es", "clean_es", is_flag=True, help="Delete Elasticsearch indices.")
@click.option("--csv", "clean_csv", is_flag=True, help="Delete CSV files from output_csv/.")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
@_with_es_opts
def cmd_cleanup(clean_es, clean_csv, yes,
                es_host, es_user, es_pass, kibana_host, kibana_user, kibana_pass):
    """Remove test data from Elasticsearch and/or local CSV files."""
    import requests as _req
    from data_generators import DATA_GENERATORS

    if not clean_es and not clean_csv:
        click.echo("Specify --es, --csv, or both.")
        return

    if not yes:
        what = " + ".join(filter(None, [
            "ES indices" if clean_es else "", "CSV files" if clean_csv else "",
        ]))
        click.confirm(f"Delete {what}?", abort=True)

    cfg = _load_cfg(es_host, es_user, es_pass, kibana_host, kibana_user, kibana_pass)

    if clean_es:
        es = cfg["elasticsearch"]
        for dt, meta in DATA_GENERATORS.items():
            index = meta["index_pattern"]
            click.echo(f"  DELETE {index}...", nl=False)
            try:
                r = _req.delete(f"{es['host']}/{index}",
                                auth=(es["username"], es["password"]), timeout=10)
                click.echo(" deleted" if r.status_code in (200, 404) else f" {r.status_code}")
            except Exception as exc:
                click.echo(f" error: {exc}", err=True)

    if clean_csv:
        csv_dir = "output_csv"
        if not os.path.exists(csv_dir):
            click.echo("No output_csv/ directory found.")
        else:
            removed = 0
            for fname in os.listdir(csv_dir):
                if fname.endswith(".csv"):
                    try:
                        os.remove(os.path.join(csv_dir, fname))
                        removed += 1
                    except OSError as exc:
                        click.echo(f"  Could not remove {fname}: {exc}", err=True)
            click.echo(f"  {removed} CSV file(s) removed.")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _create_kibana_objects(data_type: str, index_name: str, config: dict) -> None:
    """Create data view + Discover sessions + dashboard for a data type."""
    import app as _app
    from generate_logs import create_data_view_so_7_11, generate_discover_sessions_for_type

    dv = create_data_view_so_7_11()
    dv["attributes"]["title"] = index_name
    dv["id"] = index_name
    sessions = generate_discover_sessions_for_type(data_type, index_name)
    _app.import_kibana_objects_improved([dv] + sessions, config)

    try:
        from dashboards import create_kibana_dashboard
        create_kibana_dashboard(data_type, index_name, config)
    except Exception:
        pass  # dashboard module may not exist yet; Discover sessions still imported


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cli()
