import csv
import random
import datetime
import os
import json
import requests
from faker import Faker

fake = Faker()

# ------------------------------------------------------------------------------
# Elasticsearch & Kibana Configuration
# ------------------------------------------------------------------------------
ELASTICSEARCH_HOST = "http://localhost:9200"
KIBANA_HOST = "http://localhost:5601"  # Adjust if Kibana is under a path (e.g., /pga)
ELASTICSEARCH_USER = "elastic"
ELASTICSEARCH_PASS = "changeme"
KIBANA_USER = "elastic"
KIBANA_PASS = "changeme"

# ------------------------------------------------------------------------------
# 1) Generate Logs -> CSV
# ------------------------------------------------------------------------------
log_levels_list = ["INFO", "WARN", "ERROR", "DEBUG"]
sources = ["AuthService", "PaymentService", "DatabaseService", "NotificationService", "CacheService"]

messages = {
    "AuthService": {
        "INFO": [
            "User '{user}' logged in successfully from IP address {ip_address}",
            "Password reset initiated for user '{user}'; verification email sent"
        ],
        "WARN": [
            "Multiple failed login attempts detected for user '{user}'; account locked for 30 minutes"
        ],
        "ERROR": [
            "Critical security vulnerability detected: unauthorized access attempt to admin panel from IP '{ip_address}'",
            "Authentication service failed to validate token for user '{user}'"
        ],
        "DEBUG": [
            "Generated authentication token for session '{session_id}'",
            "Password hash generated using SHA-256 algorithm for user '{user}'"
        ]
    },
    "PaymentService": {
        "INFO": [
            "Refund processed for order ID '{order_id}'; amount refunded: ${amount}",
            "Large volume of transactions processed: {transaction_count} transactions in the last hour",
            "Payment completed successfully for transaction ID '{transaction_id}'"
        ],
        "WARN": [
            "Payment processing delayed due to network latency exceeding {latency}ms threshold",
            "Currency conversion rate not available for '{from_currency}' to '{to_currency}'",
            "Suspicious transaction pattern detected for user '{user}'"
        ],
        "ERROR": [
            "Transaction ID '{transaction_id}' declined due to insufficient funds",
            "Payment gateway error: {gateway_response}"
        ],
        "DEBUG": [
            "Debugging payment flow for transaction ID '{transaction_id}'",
            "Payment gateway response: {gateway_response}"
        ]
    },
    # Additional definitions for DatabaseService, NotificationService, CacheService can be added similarly.
}

def random_timestamp(start, end):
    return start + datetime.timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

def generate_logs(num_entries=1000):
    """
    Generates log docs in memory, writes them to CSV,
    and returns a list of doc dicts for ingestion.
    """
    entries = []
    start_date = datetime.datetime.now() - datetime.timedelta(days=365)
    end_date = datetime.datetime.now()
    error_spike_dates = [start_date + datetime.timedelta(days=30 * i) for i in range(1, 13)]

    for _ in range(num_entries):
        if random.random() < 0.10:
            timestamp = random.choice(error_spike_dates) + datetime.timedelta(seconds=random.randint(0, 3600))
            level = "ERROR"
        else:
            timestamp = random_timestamp(start_date, end_date)
            level = random.choices(log_levels_list, weights=[0.7, 0.1, 0.1, 0.1])[0]

        source = random.choice(sources)
        tmpl_list = messages.get(source, {}).get(level, ["Generic log message"])
        tmpl = random.choice(tmpl_list)

        msg_data = {
            "user": fake.user_name(),
            "ip_address": fake.ipv4(),
            "session_id": fake.uuid4()
        }

        try:
            message = tmpl.format(**msg_data)
        except KeyError:
            message = "Incomplete log message."

        doc = {
            "@timestamp": timestamp.isoformat() + "Z",
            "log.level": level,
            "source": source,
            "message": message
        }
        entries.append(doc)

    entries.sort(key=lambda x: x["@timestamp"])
    os.makedirs("output_csv", exist_ok=True)
    csv_path = os.path.join("output_csv", "unstructured-logs-001.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["@timestamp", "log.level", "source", "message"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for e in entries:
            writer.writerow(e)
    print(f"Generated logs -> {csv_path}")
    return entries

# ------------------------------------------------------------------------------
# 2) Ingest Logs into Elasticsearch
# ------------------------------------------------------------------------------
def ingest_logs_to_es(docs):
    index_url = f"{ELASTICSEARCH_HOST}/unstructured-logs"
    resp = requests.put(
        index_url,
        auth=(ELASTICSEARCH_USER, ELASTICSEARCH_PASS),
        headers={"Content-Type": "application/json"},
        json={
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            },
            "mappings": {
                "properties": {
                    "@timestamp": {"type": "date_nanos"},
                    "log.level": {"type": "keyword"},
                    "source": {"type": "keyword"},
                    "message": {"type": "text"}
                }
            }
        }
    )
    if resp.status_code not in (200, 400):
        print("Index creation error:", resp.text)
    else:
        print("Index 'unstructured-logs' created or exists.")
    
    bulk_data = []
    for d in docs:
        bulk_data.append(json.dumps({"index": {}}))
        bulk_data.append(json.dumps(d))
    bulk_body = "\n".join(bulk_data) + "\n"
    
    resp2 = requests.post(
        f"{index_url}/_bulk",
        auth=(ELASTICSEARCH_USER, ELASTICSEARCH_PASS),
        headers={"Content-Type": "application/x-ndjson"},
        data=bulk_body
    )
    if resp2.status_code == 200:
        print("Logs successfully ingested into 'unstructured-logs'.")
    else:
        print("Bulk ingest error:", resp2.text)

# ------------------------------------------------------------------------------
# 3) Create Data View (Index Pattern) Saved Object with ID 'unstructured-logs'
# ------------------------------------------------------------------------------
def create_data_view_so_7_11():
    now_str = datetime.datetime.utcnow().isoformat() + "Z"
    return {
        "id": "unstructured-logs",
        "type": "index-pattern",
        "namespaces": ["default"],
        "updated_at": now_str,
        "created_at": now_str,
        "version": "WzFd",
        "attributes": {
            "title": "unstructured-logs",
            "timeFieldName": "@timestamp",
            "fields": "[]"
        },
        "references": [],
        "managed": False,
        "coreMigrationVersion": "7.11.0",
        "typeMigrationVersion": "7.11.0"
    }

# ------------------------------------------------------------------------------
# 4a) Per-type Discover session definitions
# ------------------------------------------------------------------------------
SESSION_DEFS = {
    "unstructured_logs": [
        {"title": "Retrieve All Logs",           "desc": "All logs sorted ascending by @timestamp.",                                                  "query": "FROM {index}\n| sort @timestamp asc",                                                                                                                               "columns": ["@timestamp", "log.level", "source", "message"]},
        {"title": "Count Logs by Level",         "desc": "Count logs grouped by log.level, sorted descending.",                                       "query": "FROM {index}\n| stats count_all = count() by log.level\n| sort count_all desc",                                                                                "columns": ["log.level", "count_all"]},
        {"title": "Count Logs by Source",        "desc": "Count logs grouped by source, sorted descending.",                                          "query": "FROM {index}\n| stats count_all = count() by source\n| sort count_all desc",                                                                                    "columns": ["source", "count_all"]},
        {"title": "Retrieve Error Logs",         "desc": "Logs with log.level == ERROR, sorted descending.",                                          "query": "FROM {index}\n| where log.level == \"ERROR\"\n| sort @timestamp desc\n| keep @timestamp, source, message",                                                   "columns": ["@timestamp", "source", "message"]},
        {"title": "Parse AuthService (DISSECT)", "desc": "Extracts user and IP address from AuthService logs using dissect.",                         "query": "FROM {index}\n| dissect message \"User '%{user}' logged in successfully from IP address %{ip_address}\"\n| where source == \"AuthService\" and log.level == \"INFO\"\n| sort @timestamp desc\n| keep @timestamp, user, ip_address", "columns": ["@timestamp", "user", "ip_address"]},
        {"title": "Parse AuthService (GROK)",    "desc": "Extracts user and IP address from AuthService logs using grok.",                            "query": "FROM {index}\n| grok message \"User '%{USERNAME:user}' logged in successfully from IP address %{IP:ip_address}\"\n| where source == \"AuthService\" and log.level == \"INFO\"\n| sort @timestamp desc\n| keep @timestamp, user, ip_address",    "columns": ["@timestamp", "user", "ip_address"]},
    ],
    "structured_logs": [
        {"title": "All Structured Logs",         "desc": "All structured logs sorted by timestamp.",                                                  "query": "FROM {index}\n| sort @timestamp desc",                                                                                                                             "columns": ["@timestamp", "service.name", "log.level", "message"]},
        {"title": "Error Rate by Service",       "desc": "Count of ERROR logs grouped by service.",                                                   "query": "FROM {index}\n| where log.level == \"ERROR\"\n| stats errors = count() by `service.name`\n| sort errors desc",                                               "columns": ["service.name", "errors"]},
        {"title": "Slow Requests (>500 ms)",     "desc": "Requests where response time exceeded 500 ms.",                                             "query": "FROM {index}\n| where `http.response_time_ms` > 500\n| sort `http.response_time_ms` desc\n| keep @timestamp, `service.name`, `http.method`, `http.status_code`, `http.response_time_ms`", "columns": ["@timestamp", "service.name", "http.method", "http.response_time_ms"]},
        {"title": "Logs by Environment",         "desc": "Count of logs grouped by environment.",                                                     "query": "FROM {index}\n| stats count = count() by environment\n| sort count desc",                                                                                      "columns": ["environment", "count"]},
    ],
    "distributed_traces": [
        {"title": "All Spans",                   "desc": "All trace spans sorted by timestamp.",                                                      "query": "FROM {index}\n| sort @timestamp desc",                                                                                                                             "columns": ["@timestamp", "service.name", "span.name", "duration.ms", "span.status"]},
        {"title": "Error Spans",                 "desc": "Spans with ERROR or TIMEOUT status.",                                                        "query": "FROM {index}\n| where `span.status` == \"ERROR\" or `span.status` == \"TIMEOUT\"\n| sort @timestamp desc",                                                 "columns": ["@timestamp", "service.name", "span.name", "span.status", "duration.ms"]},
        {"title": "Slowest Spans by Service",    "desc": "P99 duration grouped by service.",                                                          "query": "FROM {index}\n| stats p99 = PERCENTILE(`duration.ms`, 99) by `service.name`\n| sort p99 desc",                                                               "columns": ["service.name", "p99"]},
        {"title": "Span Count per Trace",        "desc": "Number of spans in each trace.",                                                            "query": "FROM {index}\n| stats spans = count() by `trace.id`\n| sort spans desc",                                                                                      "columns": ["trace.id", "spans"]},
    ],
    "metrics": [
        {"title": "All Metrics",                 "desc": "All metric documents sorted by timestamp.",                                                  "query": "FROM {index}\n| sort @timestamp desc",                                                                                                                             "columns": ["@timestamp", "metric.type", "metric.name", "metric.value", "service.name"]},
        {"title": "Gauge Metrics",               "desc": "Gauge-type metrics.",                                                                        "query": "FROM {index}\n| where `metric.type` == \"gauge\"\n| sort @timestamp desc",                                                                                   "columns": ["@timestamp", "service.name", "metric.name", "metric.value"]},
        {"title": "Counter Metrics by Service",  "desc": "Total counter value grouped by service.",                                                   "query": "FROM {index}\n| where `metric.type` == \"counter\"\n| stats total = SUM(`metric.value`) by `service.name`\n| sort total desc",                          "columns": ["service.name", "total"]},
        {"title": "P99 Latency Summary",         "desc": "P99 of metric values grouped by metric name.",                                              "query": "FROM {index}\n| stats p99 = PERCENTILE(`metric.value`, 99) by `metric.name`\n| sort p99 desc",                                                              "columns": ["metric.name", "p99"]},
    ],
    "security_events": [
        {"title": "All Security Events",         "desc": "All security events sorted by timestamp.",                                                   "query": "FROM {index}\n| sort @timestamp desc",                                                                                                                             "columns": ["@timestamp", "event.type", "event.severity", "user.name", "source.ip"]},
        {"title": "Authentication Failures",     "desc": "Authentication events only.",                                                               "query": "FROM {index}\n| where `event.type` == \"authentication\"\n| sort @timestamp desc",                                                                           "columns": ["@timestamp", "user.name", "source.ip", "event.severity"]},
        {"title": "Critical Severity Events",    "desc": "Events with severity == critical.",                                                          "query": "FROM {index}\n| where `event.severity` == \"critical\"\n| sort @timestamp desc",                                                                             "columns": ["@timestamp", "event.type", "user.name", "source.ip", "host.name"]},
        {"title": "Malware Detections",          "desc": "Malware-type security events.",                                                              "query": "FROM {index}\n| where `event.type` == \"malware\"\n| sort @timestamp desc",                                                                                   "columns": ["@timestamp", "host.name", "user.name", "event.severity"]},
    ],
    "alerts": [
        {"title": "All Alerts",                  "desc": "All alert documents sorted by timestamp.",                                                   "query": "FROM {index}\n| sort @timestamp desc",                                                                                                                             "columns": ["@timestamp", "alert.name", "alert.state", "alert.severity"]},
        {"title": "Currently Firing Alerts",     "desc": "Alerts in firing state.",                                                                    "query": "FROM {index}\n| where `alert.state` == \"firing\"\n| sort @timestamp desc",                                                                                   "columns": ["@timestamp", "alert.name", "alert.severity", "metric.value", "metric.threshold"]},
        {"title": "Alerts by Severity",          "desc": "Count of alerts grouped by severity.",                                                       "query": "FROM {index}\n| stats count = count() by `alert.severity`\n| sort count desc",                                                                                "columns": ["alert.severity", "count"]},
        {"title": "Alert Resolution Times",      "desc": "Firing alerts with resolution timestamps.",                                                  "query": "FROM {index}\n| where `alert.state` == \"resolved\"\n| keep @timestamp, `alert.name`, `alert.started_at`, `alert.resolved_at`\n| sort @timestamp desc",  "columns": ["alert.name", "alert.started_at", "alert.resolved_at"]},
    ],
    "network_traffic": [
        {"title": "All Network Flows",           "desc": "All network flow documents sorted by timestamp.",                                            "query": "FROM {index}\n| sort @timestamp desc",                                                                                                                             "columns": ["@timestamp", "network.protocol", "source.ip", "destination.ip", "network.bytes"]},
        {"title": "Blocked Connections",         "desc": "Flows where event.action == blocked.",                                                       "query": "FROM {index}\n| where `event.action` == \"blocked\"\n| sort @timestamp desc",                                                                               "columns": ["@timestamp", "source.ip", "destination.ip", "network.protocol", "destination.port"]},
        {"title": "HTTP and HTTPS Traffic",      "desc": "Flows on ports 80 or 443.",                                                                  "query": "FROM {index}\n| where `destination.port` == 80 or `destination.port` == 443\n| sort @timestamp desc",                                                    "columns": ["@timestamp", "source.ip", "destination.ip", "destination.port", "network.bytes"]},
        {"title": "Top Source IPs",              "desc": "Source IPs by total bytes transferred.",                                                     "query": "FROM {index}\n| stats total_bytes = SUM(`network.bytes`) by `source.ip`\n| sort total_bytes desc",                                                         "columns": ["source.ip", "total_bytes"]},
    ],
    "apm_data": [
        {"title": "All Transactions",            "desc": "All APM transaction documents sorted by timestamp.",                                         "query": "FROM {index}\n| sort @timestamp desc",                                                                                                                             "columns": ["@timestamp", "service.name", "transaction.name", "transaction.duration.ms", "transaction.result"]},
        {"title": "Failed Transactions",         "desc": "Transactions with transaction.result == error.",                                             "query": "FROM {index}\n| where `transaction.result` == \"error\"\n| sort @timestamp desc",                                                                          "columns": ["@timestamp", "service.name", "transaction.name", "transaction.duration.ms"]},
        {"title": "Slow Database Queries",       "desc": "Database transactions exceeding 200 ms.",                                                    "query": "FROM {index}\n| where `transaction.type` == \"database_query\" and `transaction.duration.ms` > 200\n| sort `transaction.duration.ms` desc",              "columns": ["@timestamp", "service.name", "transaction.name", "transaction.duration.ms"]},
        {"title": "Error Rate by Service",       "desc": "Count of failed transactions grouped by service.",                                           "query": "FROM {index}\n| where `transaction.result` == \"error\"\n| stats errors = count() by `service.name`\n| sort errors desc",                              "columns": ["service.name", "errors"]},
    ],
}

def generate_discover_sessions_for_type(data_type, index_name):
    """Return a list of Discover session saved objects for the given data type."""
    now_str = datetime.datetime.utcnow().isoformat() + "Z"
    created_by = "u_mGBROF_q5bmFCATbLXAcCwKa0k8JvONAwSruelyKA5E_0"
    defs = SESSION_DEFS.get(data_type, SESSION_DEFS["unstructured_logs"])
    sessions = []
    for i, sdef in enumerate(defs, start=1):
        query = sdef["query"].replace("{index}", index_name)
        search_source = {
            "query": {"esql": query},
            "index": index_name,
            "filter": []
        }
        sessions.append({
            "id": f"{data_type}_session_{i}",
            "type": "search",
            "namespaces": ["default"],
            "updated_at": now_str,
            "created_at": now_str,
            "created_by": created_by,
            "updated_by": created_by,
            "version": "WzFd",
            "attributes": {
                "title": sdef["title"],
                "description": sdef["desc"],
                "hits": 0,
                "columns": sdef["columns"],
                "sort": [],
                "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps(search_source)},
                "grid": {},
                "hideChart": False,
                "isTextBasedQuery": True,
                "timeRestore": False,
            },
            "references": [{"name": "kibanaSavedObjectMeta.searchSourceJSON.index",
                            "type": "index-pattern", "id": index_name}],
            "managed": False,
        })
    return sessions

# ------------------------------------------------------------------------------
# 4b) Legacy: Discover Sessions with DISSECT & GROK (unstructured logs only)
# ------------------------------------------------------------------------------
def generate_discover_sessions_7_11():
    now_str = datetime.datetime.utcnow().isoformat() + "Z"
    one_year_ago_str = (datetime.datetime.utcnow() - datetime.timedelta(days=365)).isoformat() + "Z"
    created_by = "u_mGBROF_q5bmFCATbLXAcCwKa0k8JvONAwSruelyKA5E_0"
    
    # Definitions for 6 discover sessions
    session_defs = [
        {
            "title": "Retrieve All Logs",
            "description": "All logs sorted ascending by @timestamp.",
            "query": "FROM unstructured-logs\n| sort @timestamp asc",
            "columns": ["@timestamp", "log.level", "source", "message"]
        },
        {
            "title": "Count Logs by Level",
            "description": "Count logs grouped by log.level, sorted descending.",
            "query": "FROM unstructured-logs\n| stats count_all = count() by log.level\n| sort count_all desc",
            "columns": ["log.level", "count_all"]
        },
        {
            "title": "Count Logs by Source",
            "description": "Count logs grouped by source, sorted descending.",
            "query": "FROM unstructured-logs\n| stats count_all = count() by source\n| sort count_all desc",
            "columns": ["source", "count_all"]
        },
        {
            "title": "Retrieve Error Logs",
            "description": "Logs with log.level == ERROR, sorted descending, keeping specific fields.",
            "query": "FROM unstructured-logs\n| where log.level == \"ERROR\"\n| sort @timestamp desc\n| keep @timestamp, source, message",
            "columns": ["@timestamp", "source", "message"]
        },
        {
            "title": "Parse AuthService Logs with Dissect",
            "description": "Extracts user and IP address from AuthService logs using dissect.",
            "query": "FROM unstructured-logs\n| dissect message \"User '%{user}' logged in successfully from IP address %{ip_address}\"\n| where source == \"AuthService\" and log.level == \"INFO\"\n| sort @timestamp desc\n| keep @timestamp, user, ip_address",
            "columns": ["@timestamp", "user", "ip_address"]
        },
        {
            "title": "Parse AuthService Logs with Grok",
            "description": "Extracts user and IP address from AuthService logs using grok.",
            "query": "FROM unstructured-logs\n| grok message \"User '%{USERNAME:user}' logged in successfully from IP address %{IP:ip_address}\"\n| where source == \"AuthService\" and log.level == \"INFO\"\n| sort @timestamp desc\n| keep @timestamp, user, ip_address",
            "columns": ["@timestamp", "user", "ip_address"]
        }
    ]
    
    sessions = []
    for i, sdef in enumerate(session_defs, start=1):
        search_source = {
            "query": {"esql": sdef["query"]},
            "index": "unstructured-logs",  # plain string required by Kibana 8.13+
            "filter": []
        }
        so = {
            "id": f"Discover_session_{i}",
            "type": "search",
            "namespaces": ["default"],
            "updated_at": now_str,
            "created_at": now_str,
            "created_by": created_by,
            "updated_by": created_by,
            "version": "WzFd",
            "attributes": {
                "title": sdef["title"],
                "description": sdef["description"],
                "hits": 0,
                "columns": sdef["columns"],
                "sort": [],
                "kibanaSavedObjectMeta": {
                    "searchSourceJSON": json.dumps(search_source)
                },
                "grid": {},
                "hideChart": False,
                "isTextBasedQuery": True,
                "timeRestore": True,
                "timeRange": {
                    "from": one_year_ago_str,
                    "to": now_str
                }
            },
            "references": [
                {
                    "name": "kibanaSavedObjectMeta.searchSourceJSON.index",
                    "type": "index-pattern",
                    "id": "unstructured-logs"
                }
            ],
            "managed": False,
            "coreMigrationVersion": "7.11.0",
            "typeMigrationVersion": "7.11.0"
        }
        sessions.append(so)
    return sessions

# ------------------------------------------------------------------------------
# 5) Write NDJSON & Import into Kibana using Saved Objects API
# ------------------------------------------------------------------------------
def write_and_import_so(data_view_obj, discover_objs):
    os.makedirs("output_saved_objects", exist_ok=True)
    ndjson_path = os.path.join("output_saved_objects", "kibana_saved_objects.ndjson")
    
    all_objs = [data_view_obj] + discover_objs
    with open(ndjson_path, "w", encoding="utf-8") as f:
        for obj in all_objs:
            f.write(json.dumps(obj) + "\n")
    print(f"Saved objects NDJSON written to {ndjson_path}")
    
    # Import into Kibana with correct headers and format
    try:
        with open(ndjson_path, "rb") as f:
            files = {
                "file": ("kibana_saved_objects.ndjson", f, "application/ndjson")
            }
            headers = {
                "kbn-xsrf": "true",
                "kbn-version": "8.0.0"  # Add version header for compatibility
            }
            
            resp = requests.post(
                f"{KIBANA_HOST}/api/saved_objects/_import?overwrite=true",
                auth=(KIBANA_USER, KIBANA_PASS),
                headers=headers,
                files=files
            )
            
        if resp.status_code == 200:
            result = resp.json()
            if result.get("success", False):
                print("Data view and discover sessions imported into Kibana!")
                if result.get("successCount", 0) > 0:
                    print(f"Successfully imported {result['successCount']} objects")
            else:
                print(f"Import completed but with issues: {result}")
        else:
            print(f"Error importing NDJSON: {resp.status_code} -> {resp.text}")
            # Try alternative approach without version header
            print("Retrying without version header...")
            
            with open(ndjson_path, "rb") as f:
                files = {
                    "file": ("kibana_saved_objects.ndjson", f, "application/ndjson")
                }
                headers = {"kbn-xsrf": "true"}
                
                resp2 = requests.post(
                    f"{KIBANA_HOST}/api/saved_objects/_import?overwrite=true",
                    auth=(KIBANA_USER, KIBANA_PASS),
                    headers=headers,
                    files=files
                )
                
            if resp2.status_code == 200:
                result = resp2.json()
                print("Data view and discover sessions imported into Kibana (retry successful)!")
                if result.get("successCount", 0) > 0:
                    print(f"Successfully imported {result['successCount']} objects")
            else:
                print(f"Retry also failed: {resp2.status_code} -> {resp2.text}")
                print("\nManual import instructions:")
                print(f"1. Open Kibana at {KIBANA_HOST}")
                print("2. Go to Management > Saved Objects")
                print(f"3. Click 'Import' and select: {ndjson_path}")
                print("4. Enable 'Automatically overwrite conflicts'")
                
    except Exception as e:
        print(f"Exception during import: {str(e)}")
        print("\nManual import instructions:")
        print(f"1. Open Kibana at {KIBANA_HOST}")
        print("2. Go to Management > Saved Objects") 
        print(f"3. Click 'Import' and select: {ndjson_path}")
        print("4. Enable 'Automatically overwrite conflicts'")

# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    # 1) Generate logs and write CSV
    docs = generate_logs(num_entries=1000)

    # 2) Ingest logs into Elasticsearch
    ingest_logs_to_es(docs)

    # 3) Create data view saved object with ID 'unstructured-logs'
    data_view_so = create_data_view_so_7_11()

    # 4) Generate Discover Sessions referencing the data view ID 'unstructured-logs'
    discover_sos = generate_discover_sessions_for_type('unstructured_logs', 'logs-unstructured')

    # 5) Write NDJSON and import via Kibana's Saved Objects API
    write_and_import_so(data_view_so, discover_sos)
