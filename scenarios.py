"""Pre-built correlated scenario generators.

Each scenario spans multiple data types with shared service names, overlapping
time windows, and realistic causal relationships — e.g. a deployment failure
that causes metric spikes, error logs, and alert firing simultaneously.
"""

import datetime
import random
from faker import Faker

from data_generators import (
    DATA_GENERATORS,
    StructuredLogsGenerator,
    MetricsGenerator,
    AlertsGenerator,
    SecurityEventsGenerator,
    NetworkTrafficGenerator,
    APMDataGenerator,
    DistributedTracesGenerator,
)

fake = Faker()

# ---------------------------------------------------------------------------
# Scenario registry
# ---------------------------------------------------------------------------

SCENARIOS = {
    "deployment_failure": {
        "name": "Deployment Failure",
        "description": (
            "A bad software deployment causes elevated error rates, service latency "
            "spikes, CPU saturation, and critical alerts across order-service and its "
            "upstream dependencies."
        ),
        "icon": "fas fa-bomb",
        "color": "danger",
        "types": ["structured_logs", "metrics", "alerts", "apm_data"],
    },
    "security_incident": {
        "name": "Security Incident",
        "description": (
            "A brute-force authentication attack from a single IP triggers cascading "
            "security events, firewall blocks, and critical alerting — with correlated "
            "401 errors appearing in application logs."
        ),
        "icon": "fas fa-skull-crossbones",
        "color": "danger",
        "types": ["security_events", "network_traffic", "alerts", "structured_logs"],
    },
    "database_slowdown": {
        "name": "Database Slowdown",
        "description": (
            "Connection pool exhaustion on the database causes cascading slow queries "
            "visible in APM transaction durations, metric gauges, application warn/error "
            "logs, and latency spikes in distributed traces."
        ),
        "icon": "fas fa-database",
        "color": "warning",
        "types": ["apm_data", "metrics", "structured_logs", "distributed_traces"],
    },
}


# ---------------------------------------------------------------------------
# Scenario base
# ---------------------------------------------------------------------------

class _BaseScenario:
    def __init__(self, start_date=None, end_date=None):
        now = datetime.datetime.now()
        self.end_date = end_date or now
        self.start_date = start_date or (now - datetime.timedelta(hours=6))
        self._init_incident_window()

    def _incident_window(self, frac_start: float, duration_hours: float):
        total = (self.end_date - self.start_date).total_seconds()
        w_start = self.start_date + datetime.timedelta(seconds=total * frac_start)
        w_end = min(w_start + datetime.timedelta(hours=duration_hours), self.end_date)
        return w_start, w_end

    def _init_incident_window(self):
        self.incident_start, self.incident_end = self._incident_window(0.3, 2.0)

    def _in_incident(self, ts: datetime.datetime) -> bool:
        return self.incident_start <= ts <= self.incident_end

    def _parse_ts(self, entry: dict) -> datetime.datetime:
        return datetime.datetime.fromisoformat(entry["@timestamp"].rstrip("Z"))


# ---------------------------------------------------------------------------
# Deployment Failure
# ---------------------------------------------------------------------------

class DeploymentFailureScenario(_BaseScenario):
    FAILING_SERVICES = ["order-service", "payment-service", "inventory-service"]

    def __init__(self, start_date=None, end_date=None):
        super().__init__(start_date, end_date)
        self.failing_service = random.choice(self.FAILING_SERVICES)
        self._struct_gen = StructuredLogsGenerator(self.start_date, self.end_date)
        self._metrics_gen = MetricsGenerator(self.start_date, self.end_date)
        self._alerts_gen = AlertsGenerator(self.start_date, self.end_date)
        self._apm_gen = APMDataGenerator(self.start_date, self.end_date)

    def generate_structured_log(self) -> dict:
        entry = self._struct_gen.generate_entry()
        ts = self._parse_ts(entry)
        if self._in_incident(ts) and entry.get("service.name") == self.failing_service:
            entry["log.level"] = "ERROR"
            entry["http.status_code"] = random.choice([500, 502, 503])
            entry["http.response_time_ms"] = random.randint(3_000, 12_000)
            entry["message"] = random.choice([
                f"Deployment rollout failed: OutOfMemoryError in {self.failing_service}",
                f"Health check failed for {self.failing_service}: connection refused",
                f"Circuit breaker OPEN for downstream {self.failing_service}",
            ])
        return entry

    def generate_metric(self) -> dict:
        entry = self._metrics_gen.generate_entry()
        ts = self._parse_ts(entry)
        if self._in_incident(ts) and entry.get("service.name") == self.failing_service:
            entry["metric.name"] = random.choice(["cpu_usage_percent", "error_rate", "active_connections"])
            entry["metric.type"] = "gauge"
            entry["metric.value"] = random.uniform(85.0, 100.0)
        return entry

    def generate_alert(self) -> dict:
        entry = self._alerts_gen.generate_entry()
        ts = self._parse_ts(entry)
        if self._in_incident(ts):
            svc = self.failing_service.replace("-", "_")
            entry["alert.state"] = "firing"
            entry["alert.severity"] = "critical"
            entry["alert.name"] = f"DeploymentFailure_{svc}"
            entry["labels"] = {
                "service": self.failing_service,
                "environment": "production",
                "team": "platform",
            }
            entry["annotations"] = {
                "summary": f"Deployment failure detected in {self.failing_service}",
                "description": "Error rate > 50 % and P99 latency > 10 s for more than 5 min",
                "runbook_url": "https://wiki.internal/runbooks/deployment-failure",
            }
        return entry

    def generate_apm(self) -> dict:
        entry = self._apm_gen.generate_entry()
        ts = self._parse_ts(entry)
        apm_affected = {"web-app", "api-service"}
        if self._in_incident(ts) and entry.get("service.name") in apm_affected:
            entry["transaction.result"] = "error"
            entry["transaction.duration.ms"] = random.randint(5_000, 20_000)
            entry["error.type"] = "ServiceUnavailableError"
            entry["error.message"] = f"Upstream {self.failing_service} unavailable"
        return entry


# ---------------------------------------------------------------------------
# Security Incident
# ---------------------------------------------------------------------------

class SecurityIncidentScenario(_BaseScenario):
    TARGET_USERS = ["admin", "root", "elasticsearch", "kibana", "ubuntu", "deploy"]
    TARGET_HOST = "auth-server-prod-01"

    def __init__(self, start_date=None, end_date=None):
        super().__init__(start_date, end_date)
        # Single attacker IP for the whole scenario
        self.attacker_ip = (
            f"185.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"
        )
        self._init_incident_window()
        self._sec_gen = SecurityEventsGenerator(self.start_date, self.end_date)
        self._net_gen = NetworkTrafficGenerator(self.start_date, self.end_date)
        self._alerts_gen = AlertsGenerator(self.start_date, self.end_date)
        self._struct_gen = StructuredLogsGenerator(self.start_date, self.end_date)

    def _init_incident_window(self):
        self.incident_start, self.incident_end = self._incident_window(0.2, 3.0)

    def generate_security_event(self) -> dict:
        entry = self._sec_gen.generate_entry()
        ts = self._parse_ts(entry)
        if self._in_incident(ts) and random.random() < 0.65:
            entry["event.type"] = "authentication"
            entry["event.action"] = "login_attempt"
            entry["event.outcome"] = "failure"
            entry["event.severity"] = random.choice(["high", "critical"])
            entry["source.ip"] = self.attacker_ip
            entry["user.name"] = random.choice(self.TARGET_USERS)
            entry["host.name"] = self.TARGET_HOST
            entry["message"] = (
                f"Brute-force login attempt for user '{entry['user.name']}' "
                f"from {self.attacker_ip}"
            )
        return entry

    def generate_network_event(self) -> dict:
        entry = self._net_gen.generate_entry()
        ts = self._parse_ts(entry)
        if self._in_incident(ts) and random.random() < 0.55:
            entry["source.ip"] = self.attacker_ip
            entry["destination.port"] = random.choice([22, 443, 9200, 5601, 3306])
            entry["event.action"] = "blocked"
            entry["network.packets"] = random.randint(500, 5_000)
            entry["network.bytes"] = entry["network.packets"] * random.randint(64, 512)
        return entry

    def generate_alert(self) -> dict:
        entry = self._alerts_gen.generate_entry()
        ts = self._parse_ts(entry)
        if self._in_incident(ts):
            entry["alert.state"] = "firing"
            entry["alert.severity"] = "critical"
            entry["alert.name"] = "BruteForceLoginDetected"
            entry["labels"] = {
                "host": self.TARGET_HOST,
                "source_ip": self.attacker_ip,
                "environment": "production",
            }
            entry["annotations"] = {
                "summary": f"Brute-force attack from {self.attacker_ip}",
                "description": "> 200 failed logins in 5 min from a single source IP",
                "runbook_url": "https://wiki.internal/runbooks/brute-force",
            }
        return entry

    def generate_structured_log(self) -> dict:
        entry = self._struct_gen.generate_entry()
        ts = self._parse_ts(entry)
        if self._in_incident(ts) and random.random() < 0.45:
            entry["log.level"] = "WARN"
            entry["service.name"] = "user-api"
            entry["http.status_code"] = 401
            entry["message"] = (
                f"Authentication failure from {self.attacker_ip} for user "
                f"'{random.choice(self.TARGET_USERS)}'"
            )
        return entry


# ---------------------------------------------------------------------------
# Database Slowdown
# ---------------------------------------------------------------------------

class DatabaseSlowdownScenario(_BaseScenario):
    DB_SERVICE = "database"
    AFFECTED_SERVICES = ["web-app", "api-service", "worker"]
    SLOW_STATEMENTS = [
        "SELECT * FROM orders o JOIN order_items oi ON o.id = oi.order_id WHERE o.status = 'pending'",
        "UPDATE inventory SET quantity = quantity - 1 WHERE product_id IN (SELECT id FROM products WHERE category = 'electronics')",
        "DELETE FROM sessions WHERE expires_at < NOW() - INTERVAL '30 days'",
    ]

    def __init__(self, start_date=None, end_date=None):
        super().__init__(start_date, end_date)
        self._init_incident_window()
        self._apm_gen = APMDataGenerator(self.start_date, self.end_date)
        self._metrics_gen = MetricsGenerator(self.start_date, self.end_date)
        self._struct_gen = StructuredLogsGenerator(self.start_date, self.end_date)
        self._traces_gen = DistributedTracesGenerator(self.start_date, self.end_date)

    def _init_incident_window(self):
        self.incident_start, self.incident_end = self._incident_window(0.25, 2.5)

    def generate_apm(self) -> dict:
        entry = self._apm_gen.generate_entry()
        ts = self._parse_ts(entry)
        if self._in_incident(ts):
            if entry.get("service.name") in self.AFFECTED_SERVICES:
                # Upstream services become slow waiting on DB
                entry["transaction.duration.ms"] = random.randint(2_000, 8_000)
            if entry.get("transaction.type") == "database_query":
                entry["transaction.duration.ms"] = random.randint(8_000, 30_000)
                entry["db.statement"] = random.choice(self.SLOW_STATEMENTS)
                entry["db.type"] = "postgresql"
                entry["transaction.result"] = random.choice(["error", "error", "success"])
        return entry

    def generate_metric(self) -> dict:
        entry = self._metrics_gen.generate_entry()
        ts = self._parse_ts(entry)
        if self._in_incident(ts) and entry.get("service.name") == self.DB_SERVICE:
            entry["metric.type"] = "gauge"
            entry["metric.name"] = random.choice(["active_connections", "cpu_usage_percent"])
            if entry["metric.name"] == "active_connections":
                entry["metric.value"] = random.randint(450, 500)
            else:
                entry["metric.value"] = random.uniform(88.0, 100.0)
        return entry

    def generate_structured_log(self) -> dict:
        entry = self._struct_gen.generate_entry()
        ts = self._parse_ts(entry)
        if self._in_incident(ts) and entry.get("service.name") in self.AFFECTED_SERVICES:
            entry["log.level"] = random.choices(["WARN", "ERROR"], weights=[60, 40])[0]
            entry["http.response_time_ms"] = random.randint(5_000, 20_000)
            entry["message"] = random.choice([
                "Database query exceeded 5 s threshold — connection pool exhausted",
                "Slow query detected: acquiring connection took > 3 s",
                "Database connection timeout after 10 s",
            ])
        return entry

    def generate_trace(self) -> dict:
        entry = self._traces_gen.generate_entry()
        ts = self._parse_ts(entry)
        op = entry.get("operation.name", "")
        if self._in_incident(ts) and any(kw in op for kw in ("query", "select", "update", "insert")):
            entry["duration.ms"] = random.randint(8_000, 30_000)
            entry["span.status"] = random.choice(["TIMEOUT", "ERROR"])
        return entry


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_SCENARIO_CLASSES: dict = {
    "deployment_failure": DeploymentFailureScenario,
    "security_incident": SecurityIncidentScenario,
    "database_slowdown": DatabaseSlowdownScenario,
}

# Maps scenario type keys → generator method name on the scenario object
_TYPE_METHODS: dict[str, str] = {
    "structured_logs": "generate_structured_log",
    "metrics": "generate_metric",
    "alerts": "generate_alert",
    "apm_data": "generate_apm",
    "security_events": "generate_security_event",
    "network_traffic": "generate_network_event",
    "distributed_traces": "generate_trace",
}


def generate_scenario_entries(
    scenario_name: str,
    num_entries_per_type: int,
    start_date=None,
    end_date=None,
) -> dict[str, list[dict]]:
    """Return {data_type: [entries]} for every type in the scenario."""
    if scenario_name not in _SCENARIO_CLASSES:
        raise ValueError(f"Unknown scenario '{scenario_name}'. "
                         f"Choose from: {list(_SCENARIO_CLASSES)}")

    scenario_obj = _SCENARIO_CLASSES[scenario_name](start_date=start_date, end_date=end_date)
    types = SCENARIOS[scenario_name]["types"]

    results: dict[str, list[dict]] = {}
    for data_type in types:
        method_name = _TYPE_METHODS.get(data_type)
        if not method_name:
            continue
        gen_fn = getattr(scenario_obj, method_name, None)
        if gen_fn is None:
            continue
        results[data_type] = [gen_fn() for _ in range(num_entries_per_type)]

    return results
