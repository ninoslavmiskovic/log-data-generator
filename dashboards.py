"""Kibana dashboard builder using the Saved Objects import API (Kibana 8.x compatible).

Each data type gets a dashboard with:
  - A markdown header panel (description + usage tips)
  - 6 Lens visualisation panels appropriate for the data shape

Panels are assembled as a Kibana "dashboard" saved object with panelsJSON
and imported via POST /api/saved_objects/_import?overwrite=true.
"""

import json
import os
import tempfile
import uuid

import requests

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _uid() -> str:
    return uuid.uuid4().hex[:12]


# ---------------------------------------------------------------------------
# Column builders
# Produce {col_id: column_definition} dicts for formBased layer columns.
# ---------------------------------------------------------------------------

def _col_count(col_id: str, label: str = "Count of records") -> dict:
    return {col_id: {
        "label": label,
        "dataType": "number",
        "operationType": "count",
        "isBucketed": False,
        "scale": "ratio",
        "sourceField": "___records___",
        "params": {"emptyAsNull": True},
        "customLabel": True,
    }}


def _col_date_histogram(col_id: str, field: str = "@timestamp") -> dict:
    return {col_id: {
        "label": field,
        "dataType": "date",
        "operationType": "date_histogram",
        "sourceField": field,
        "isBucketed": True,
        "scale": "interval",
        "params": {"interval": "auto", "includeEmptyRows": True, "dropPartials": False},
    }}


def _col_terms(col_id: str, field: str, size: int = 8,
               sort_col: str | None = None) -> dict:
    return {col_id: {
        "label": field,
        "dataType": "string",
        "operationType": "terms",
        "sourceField": field,
        "isBucketed": True,
        "scale": "ordinal",
        "params": {
            "size": size,
            "orderBy": ({"type": "column", "columnId": sort_col}
                        if sort_col else {"type": "records"}),
            "orderDirection": "desc",
            "otherBucket": True,
            "missingBucket": False,
            "parentFormat": {"id": "terms"},
            "secondaryFields": [],
        },
        "customLabel": True,
    }}


def _col_avg(col_id: str, field: str, label: str | None = None) -> dict:
    return {col_id: {
        "label": label or f"Avg {field}",
        "dataType": "number",
        "operationType": "average",
        "sourceField": field,
        "isBucketed": False,
        "scale": "ratio",
        "params": {"emptyAsNull": True},
        "customLabel": True,
    }}


def _col_sum(col_id: str, field: str, label: str | None = None) -> dict:
    return {col_id: {
        "label": label or f"Sum {field}",
        "dataType": "number",
        "operationType": "sum",
        "sourceField": field,
        "isBucketed": False,
        "scale": "ratio",
        "params": {"emptyAsNull": True},
        "customLabel": True,
    }}


def _ref(layer_id: str, data_view_id: str) -> dict:
    return {
        "type": "index-pattern",
        "id": data_view_id,
        "name": f"indexpattern-datasource-layer-{layer_id}",
    }


# ---------------------------------------------------------------------------
# Panel builders
# Each returns a panel dict ready to go into panelsJSON.
# ---------------------------------------------------------------------------

def _lens_panel(panel_id: str, title: str, x: int, y: int, w: int, h: int,
                vis_type: str, layer_id: str, data_view_id: str,
                visualization: dict, columns: dict, column_order: list,
                filter_kql: str = "") -> dict:
    """Generic Lens panel factory (shared by all chart types)."""
    return {
        "type": "lens",
        "panelIndex": panel_id,
        "gridData": {"x": x, "y": y, "w": w, "h": h, "i": panel_id},
        "embeddableConfig": {
            "hidePanelTitles": False,
            "enhancements": {},
            "attributes": {
                "title": "",
                "description": "",
                "visualizationType": vis_type,
                "type": "lens",
                "references": [_ref(layer_id, data_view_id)],
                "state": {
                    "visualization": visualization,
                    "datasourceStates": {
                        "formBased": {
                            "layers": {
                                layer_id: {
                                    "columns": columns,
                                    "columnOrder": column_order,
                                    "incompleteColumns": {},
                                }
                            }
                        }
                    },
                    "query": {"query": filter_kql, "language": "kuery"},
                    "filters": [],
                    "internalReferences": [],
                    "adHocDataViews": {},
                },
            },
        },
        "title": title,
    }


def panel_markdown(content: str, x: int, y: int, w: int, h: int) -> dict:
    pid = _uid()
    return {
        "type": "visualization",
        "panelIndex": pid,
        "gridData": {"x": x, "y": y, "w": w, "h": h, "i": pid},
        "embeddableConfig": {
            "hidePanelTitles": True,
            "enhancements": {},
            "savedVis": {
                "id": "",
                "title": "",
                "description": "",
                "type": "markdown",
                "params": {
                    "fontSize": 12,
                    "openLinksInNewTab": False,
                    "markdown": content,
                },
                "uiState": {},
                "data": {
                    "aggs": [],
                    "searchSource": {
                        "query": {"query": "", "language": "kuery"},
                        "filter": [],
                    },
                },
            },
        },
        "title": "",
    }


def panel_metric(title: str, data_view_id: str,
                 x: int, y: int, w: int, h: int,
                 filter_kql: str = "") -> dict:
    pid, lid, cid = _uid(), _uid(), _uid()
    viz = {
        "layerId": lid,
        "layerType": "data",
        "metricAccessor": cid,
        "secondaryTrend": {"type": "none"},
        "secondaryLabelPosition": "before",
    }
    return _lens_panel(pid, title, x, y, w, h, "lnsMetric", lid, data_view_id,
                       viz, {**_col_count(cid, title)}, [cid], filter_kql)


def panel_donut(title: str, data_view_id: str, slice_field: str,
                x: int, y: int, w: int, h: int,
                filter_kql: str = "", size: int = 8) -> dict:
    pid, lid = _uid(), _uid()
    term_id, count_id = _uid(), _uid()
    viz = {
        "shape": "donut",
        "layers": [{
            "layerId": lid,
            "layerType": "data",
            "primaryGroups": [term_id],
            "metrics": [count_id],
            "numberDisplay": "percent",
            "categoryDisplay": "default",
            "legendDisplay": "default",
            "nestedLegend": False,
        }],
    }
    cols = {**_col_terms(term_id, slice_field, size=size, sort_col=count_id),
            **_col_count(count_id)}
    return _lens_panel(pid, title, x, y, w, h, "lnsPie", lid, data_view_id,
                       viz, cols, [term_id, count_id], filter_kql)


def panel_bar_time_split(title: str, data_view_id: str, split_field: str,
                         x: int, y: int, w: int, h: int,
                         filter_kql: str = "", series_type: str = "bar_stacked",
                         size: int = 6) -> dict:
    pid, lid = _uid(), _uid()
    date_id, term_id, count_id = _uid(), _uid(), _uid()
    viz = {
        "preferredSeriesType": series_type,
        "layers": [{
            "layerId": lid,
            "layerType": "data",
            "seriesType": series_type,
            "xAccessor": date_id,
            "splitAccessor": term_id,
            "accessors": [count_id],
        }],
        "legend": {"isVisible": True, "position": "right", "showSingleSeries": True},
        "valueLabels": "hide",
        "axisTitlesVisibilitySettings": {"x": False, "yLeft": True, "yRight": True},
        "tickLabelsVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
        "gridlinesVisibilitySettings": {"x": False, "yLeft": True, "yRight": False},
    }
    cols = {**_col_date_histogram(date_id),
            **_col_terms(term_id, split_field, size=size, sort_col=count_id),
            **_col_count(count_id)}
    return _lens_panel(pid, title, x, y, w, h, "lnsXY", lid, data_view_id,
                       viz, cols, [date_id, term_id, count_id], filter_kql)


def panel_line_avg_split(title: str, data_view_id: str,
                         metric_field: str, split_field: str,
                         x: int, y: int, w: int, h: int,
                         filter_kql: str = "", size: int = 6) -> dict:
    pid, lid = _uid(), _uid()
    date_id, term_id, avg_id = _uid(), _uid(), _uid()
    viz = {
        "preferredSeriesType": "line",
        "layers": [{
            "layerId": lid,
            "layerType": "data",
            "seriesType": "line",
            "xAccessor": date_id,
            "splitAccessor": term_id,
            "accessors": [avg_id],
        }],
        "legend": {"isVisible": True, "position": "right", "showSingleSeries": True},
        "valueLabels": "hide",
        "axisTitlesVisibilitySettings": {"x": False, "yLeft": True, "yRight": True},
    }
    cols = {**_col_date_histogram(date_id),
            **_col_terms(term_id, split_field, size=size, sort_col=avg_id),
            **_col_avg(avg_id, metric_field)}
    return _lens_panel(pid, title, x, y, w, h, "lnsXY", lid, data_view_id,
                       viz, cols, [date_id, term_id, avg_id], filter_kql)


def panel_bar_horizontal(title: str, data_view_id: str, group_field: str,
                         x: int, y: int, w: int, h: int,
                         filter_kql: str = "", size: int = 10,
                         metric_field: str | None = None,
                         metric_op: str = "count") -> dict:
    pid, lid = _uid(), _uid()
    term_id, metric_id = _uid(), _uid()
    if metric_field and metric_op == "sum":
        metric_col = _col_sum(metric_id, metric_field)
    elif metric_field and metric_op == "avg":
        metric_col = _col_avg(metric_id, metric_field)
    else:
        metric_col = _col_count(metric_id)
    viz = {
        "preferredSeriesType": "bar_horizontal",
        "layers": [{
            "layerId": lid,
            "layerType": "data",
            "seriesType": "bar_horizontal",
            "xAccessor": term_id,
            "accessors": [metric_id],
        }],
        "legend": {"isVisible": False, "position": "right"},
        "valueLabels": "inside",
        "axisTitlesVisibilitySettings": {"x": True, "yLeft": False, "yRight": True},
    }
    cols = {**_col_terms(term_id, group_field, size=size, sort_col=metric_id),
            **metric_col}
    return _lens_panel(pid, title, x, y, w, h, "lnsXY", lid, data_view_id,
                       viz, cols, [term_id, metric_id], filter_kql)


def panel_table(title: str, data_view_id: str, group_field: str,
                x: int, y: int, w: int, h: int,
                filter_kql: str = "", size: int = 10,
                metric_field: str | None = None,
                metric_op: str = "count") -> dict:
    pid, lid = _uid(), _uid()
    term_id, metric_id = _uid(), _uid()
    if metric_field and metric_op == "sum":
        metric_col = _col_sum(metric_id, metric_field)
    elif metric_field and metric_op == "avg":
        metric_col = _col_avg(metric_id, metric_field)
    else:
        metric_col = _col_count(metric_id)
    viz = {
        "layerId": lid,
        "layerType": "data",
        "columns": [
            {"columnId": term_id, "isTransposed": False},
            {"columnId": metric_id, "isTransposed": False},
        ],
        "paginationSize": 10,
        "rowHeight": "auto",
        "rowHeightLines": 1,
        "headerRowHeight": "auto",
        "headerRowHeightLines": 1,
    }
    cols = {**_col_terms(term_id, group_field, size=size, sort_col=metric_id),
            **metric_col}
    return _lens_panel(pid, title, x, y, w, h, "lnsDatatable", lid, data_view_id,
                       viz, cols, [term_id, metric_id], filter_kql)


# ---------------------------------------------------------------------------
# Dashboard layout helpers
# ---------------------------------------------------------------------------

def _collect_references(panels: list, index_name: str) -> list:
    """Build the dashboard-level references list from all Lens panels."""
    refs = []
    for panel in panels:
        if panel.get("type") != "lens":
            continue
        pid = panel["panelIndex"]
        for ref in panel["embeddableConfig"]["attributes"].get("references", []):
            if ref["type"] == "index-pattern":
                refs.append({
                    "type": "index-pattern",
                    "id": ref["id"],
                    "name": f"{pid}:{ref['name']}",
                })
    return refs


def _dashboard_so(title: str, dashboard_id: str, panels: list, index_name: str) -> dict:
    """Wrap a panels list into a Kibana dashboard saved object."""
    return {
        "type": "dashboard",
        "id": dashboard_id,
        "coreMigrationVersion": "8.8.0",
        "typeMigrationVersion": "10.3.0",
        "managed": False,
        "attributes": {
            "title": title,
            "description": f"Auto-generated dashboard for {index_name}",
            "version": 1,
            "timeRestore": True,
            "timeFrom": "now-7d",
            "timeTo": "now",
            "optionsJSON": json.dumps({
                "useMargins": True,
                "syncColors": True,
                "syncCursor": True,
                "syncTooltips": False,
                "hidePanelTitles": False,
            }),
            "panelsJSON": json.dumps(panels),
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({
                    "filter": [],
                    "query": {"query": "", "language": "kuery"},
                }),
            },
        },
        "references": _collect_references(panels, index_name),
    }


# ---------------------------------------------------------------------------
# Per-type dashboard builders
# Grid: 48 columns wide. Layout per dashboard:
#   Row  0, h=5  — markdown header (full width)
#   Row  5, h=8  — 3 stat/donut/bar panels (12 + 18 + 18)
#   Row 13, h=16 — main time-series chart (full width)
#   Row 29, h=12 — two bottom panels (24 + 24)
# ---------------------------------------------------------------------------

def _build_unstructured_logs(dv: str) -> list:
    md = (
        "## Unstructured Logs\n"
        "Free-form application log messages from **5 services**: "
        "AuthService, PaymentService, DatabaseService, NotificationService, CacheService.\n\n"
        "Use these panels to spot **log-level trends**, identify **chatty services**, "
        "and detect **error spikes** over the selected time window."
    )
    return [
        panel_markdown(md, 0, 0, 48, 5),
        panel_metric("Total Log Entries", dv, 0, 5, 12, 8),
        panel_donut("Log Level Distribution", dv, "log.level", 12, 5, 18, 8),
        panel_bar_horizontal("Top Sources by Volume", dv, "source", 30, 5, 18, 8),
        panel_bar_time_split("Log Volume Over Time by Level", dv, "log.level", 0, 13, 48, 16),
        panel_bar_time_split("Errors Over Time by Source", dv, "source",
                             0, 29, 24, 12, filter_kql='log.level : "ERROR"'),
        panel_table("Top Sources by Error Count", dv, "source",
                    24, 29, 24, 12, filter_kql='log.level : "ERROR"'),
    ]


def _build_structured_logs(dv: str) -> list:
    md = (
        "## Structured Logs\n"
        "JSON-formatted application logs from **5 microservices** with consistent fields "
        "for service name, HTTP details, trace IDs, and response times.\n\n"
        "Correlate **log levels**, **HTTP status codes**, and **response latency** across "
        "services. Use `trace.id` to pivot to related spans in Distributed Traces."
    )
    return [
        panel_markdown(md, 0, 0, 48, 5),
        panel_metric("Total Log Entries", dv, 0, 5, 12, 8),
        panel_donut("Log Level Distribution", dv, "log.level", 12, 5, 18, 8),
        panel_donut("HTTP Method Mix", dv, "http.method", 30, 5, 18, 8),
        panel_bar_time_split("Log Volume Over Time by Level", dv, "log.level", 0, 13, 48, 16),
        panel_line_avg_split("Avg Response Time by Service (ms)", dv,
                             "http.response_time_ms", "service.name", 0, 29, 24, 12),
        panel_table("Top Services by Error Count", dv, "service.name",
                    24, 29, 24, 12, filter_kql='log.level : "ERROR"'),
    ]


def _build_distributed_traces(dv: str) -> list:
    md = (
        "## Distributed Traces\n"
        "OpenTelemetry-style spans across **6 services**: frontend, user-service, "
        "order-service, payment-service, inventory-service, notification-service.\n\n"
        "Track **request flows**, surface **slow operations**, and identify "
        "**error-prone services**. Child spans always start after their parent."
    )
    return [
        panel_markdown(md, 0, 0, 48, 5),
        panel_metric("Total Spans", dv, 0, 5, 12, 8),
        panel_donut("Span Status", dv, "span.status", 12, 5, 18, 8),
        panel_bar_horizontal("Spans by Service", dv, "service.name", 30, 5, 18, 8),
        panel_bar_time_split("Spans Over Time by Status", dv, "span.status", 0, 13, 48, 16),
        panel_line_avg_split("Avg Span Duration by Service (ms)", dv,
                             "duration.ms", "service.name", 0, 29, 24, 12),
        panel_table("Slowest Operations (Avg ms)", dv, "operation.name",
                    24, 29, 24, 12, metric_field="duration.ms", metric_op="avg"),
    ]


def _build_metrics(dv: str) -> list:
    md = (
        "## Metrics & Time Series\n"
        "Prometheus-style metrics — **counters**, **gauges**, **histograms**, and "
        "**summaries** — from 5 services: frontend, api-gateway, user-service, "
        "order-service, database.\n\n"
        "Monitor metric type distribution, track gauge values over time, and compare "
        "service activity levels at a glance."
    )
    return [
        panel_markdown(md, 0, 0, 48, 5),
        panel_metric("Total Metric Points", dv, 0, 5, 12, 8),
        panel_donut("Metric Type Distribution", dv, "metric.type", 12, 5, 18, 8),
        panel_bar_horizontal("Metric Points by Service", dv, "service.name", 30, 5, 18, 8),
        panel_bar_time_split("Metric Volume Over Time by Type", dv, "metric.type", 0, 13, 48, 16),
        panel_line_avg_split("Avg Metric Value by Service", dv,
                             "metric.value", "service.name", 0, 29, 24, 12),
        panel_table("Top Metric Names by Count", dv, "metric.name", 24, 29, 24, 12),
    ]


def _build_security_events(dv: str) -> list:
    md = (
        "## Security Events\n"
        "SIEM-style events covering **authentication**, **authorization**, **network "
        "anomalies**, **malware**, **data access**, and **system** events.\n\n"
        "Spot attack patterns, track severity trends, and identify compromised hosts. "
        "Critical events are intentionally rare (~5%) to reflect realistic threat landscapes."
    )
    return [
        panel_markdown(md, 0, 0, 48, 5),
        panel_metric("Total Security Events", dv, 0, 5, 12, 8),
        panel_donut("Severity Distribution", dv, "event.severity", 12, 5, 18, 8),
        panel_donut("Event Type Distribution", dv, "event.type", 30, 5, 18, 8),
        panel_bar_time_split("Events Over Time by Severity", dv, "event.severity", 0, 13, 48, 16),
        panel_bar_horizontal("Top Source IPs", dv, "source.ip",
                             0, 29, 24, 12, size=10),
        panel_table("Critical Events by Host", dv, "host.name",
                    24, 29, 24, 12, filter_kql='event.severity : "critical"'),
    ]


def _build_alerts(dv: str) -> list:
    md = (
        "## Alerts & Notifications\n"
        "Alert-manager style events with **firing** and **resolved** states across "
        "critical, high, medium, and low severities.\n\n"
        "Track active alerts, identify noisy alert rules, and measure time-to-resolve "
        "trends. Alert names, labels, and annotations mirror real Prometheus/Alertmanager output."
    )
    return [
        panel_markdown(md, 0, 0, 48, 5),
        panel_metric("Total Alerts", dv, 0, 5, 12, 8),
        panel_donut("Alert Severity", dv, "alert.severity", 12, 5, 18, 8),
        panel_donut("Alert State", dv, "alert.state", 30, 5, 18, 8),
        panel_bar_time_split("Alert Volume Over Time by Severity", dv, "alert.severity", 0, 13, 48, 16),
        panel_bar_time_split("Firing Alerts Over Time by Name", dv, "alert.name",
                             0, 29, 24, 12,
                             filter_kql='alert.state : "firing"',
                             series_type="area_stacked"),
        panel_table("Noisiest Alert Rules", dv, "alert.name", 24, 29, 24, 12),
    ]


def _build_network_traffic(dv: str) -> list:
    md = (
        "## Network Traffic\n"
        "NetFlow-style connection records with **source/destination IPs**, **protocols**, "
        "**port numbers**, **byte counts**, and **geo-location**.\n\n"
        "Identify top talkers, detect blocked connections, analyse protocol mix, "
        "and track traffic volume trends over time."
    )
    return [
        panel_markdown(md, 0, 0, 48, 5),
        panel_metric("Total Flow Records", dv, 0, 5, 12, 8),
        panel_donut("Protocol Distribution", dv, "network.protocol", 12, 5, 18, 8),
        panel_donut("Traffic Direction", dv, "network.direction", 30, 5, 18, 8),
        panel_bar_time_split("Traffic Volume Over Time by Protocol", dv, "network.protocol", 0, 13, 48, 16),
        panel_bar_horizontal("Top Source IPs by Byte Volume", dv, "source.ip",
                             0, 29, 24, 12,
                             metric_field="network.bytes", metric_op="sum"),
        panel_table("Blocked Connections by Destination IP", dv, "destination.ip",
                    24, 29, 24, 12, filter_kql='event.action : "blocked"'),
    ]


def _build_apm(dv: str) -> list:
    md = (
        "## APM Data\n"
        "Application Performance Monitoring transactions from **web-app**, **api-service**, "
        "**worker**, and **database** — covering HTTP requests, background jobs, tasks, "
        "and database queries.\n\n"
        "Monitor transaction throughput, track error rates by service, identify slow "
        "database queries, and compare latency across services."
    )
    return [
        panel_markdown(md, 0, 0, 48, 5),
        panel_metric("Total Transactions", dv, 0, 5, 12, 8),
        panel_donut("Transaction Result", dv, "transaction.result", 12, 5, 18, 8),
        panel_donut("Transaction Type", dv, "transaction.type", 30, 5, 18, 8),
        panel_bar_time_split("Transactions Over Time by Result", dv, "transaction.result", 0, 13, 48, 16),
        panel_line_avg_split("Avg Duration by Service (ms)", dv,
                             "transaction.duration.ms", "service.name", 0, 29, 24, 12),
        panel_table("Slowest Transaction Names (Avg ms)", dv, "transaction.name",
                    24, 29, 24, 12,
                    metric_field="transaction.duration.ms", metric_op="avg"),
    ]


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_BUILDERS: dict = {
    "unstructured_logs": ("Unstructured Logs Dashboard",  _build_unstructured_logs),
    "structured_logs":   ("Structured Logs Dashboard",    _build_structured_logs),
    "distributed_traces":("Distributed Traces Dashboard", _build_distributed_traces),
    "metrics":           ("Metrics Dashboard",            _build_metrics),
    "security_events":   ("Security Events Dashboard",    _build_security_events),
    "alerts":            ("Alerts Dashboard",             _build_alerts),
    "network_traffic":   ("Network Traffic Dashboard",    _build_network_traffic),
    "apm_data":          ("APM Dashboard",                _build_apm),
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_dashboard_so(data_type: str, index_name: str) -> dict | None:
    """Return the Kibana dashboard saved object dict for the given data type, or None."""
    if data_type not in _BUILDERS:
        return None
    title, builder = _BUILDERS[data_type]
    panels = builder(index_name)
    dashboard_id = f"{index_name}-dashboard"
    return _dashboard_so(title, dashboard_id, panels, index_name)


def create_kibana_dashboard(data_type: str, index_name: str, config: dict) -> None:
    """Build and import a Kibana dashboard via the Saved Objects import API."""
    so = build_dashboard_so(data_type, index_name)
    if so is None:
        return

    kibana_host = config["kibana"]["host"]
    kibana_user = config["kibana"]["username"]
    kibana_pass = config["kibana"]["password"]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".ndjson", delete=False,
                                     encoding="utf-8") as fh:
        fh.write(json.dumps(so) + "\n")
        tmp = fh.name

    try:
        with open(tmp, "rb") as fh:
            resp = requests.post(
                f"{kibana_host}/api/saved_objects/_import?overwrite=true",
                auth=(kibana_user, kibana_pass),
                headers={"kbn-xsrf": "true"},
                files={"file": ("dashboard.ndjson", fh, "application/ndjson")},
                timeout=30,
            )
        if resp.status_code != 200:
            raise Exception(
                f"Dashboard import failed (HTTP {resp.status_code}): {resp.text[:400]}"
            )
        result = resp.json()
        if not result.get("success"):
            errors = result.get("errors", [])
            raise Exception(f"Dashboard import errors: {errors[:2]}")
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass
