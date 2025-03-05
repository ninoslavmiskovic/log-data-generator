import csv
import random
import datetime
import os
import json
import uuid
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
        if random.random() < 0.05:
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
# 4) Generate Discover Sessions with DISSECT & GROK, plus others
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
            "index": {
                "id": "unstructured-logs",
                "title": "unstructured-logs",
                "timeFieldName": "@timestamp",
                "sourceFilters": [],
                "type": "esql",
                "fieldFormats": {},
                "runtimeFieldMap": {},
                "allowNoIndex": False,
                "name": "unstructured-logs",
                "allowHidden": False
            },
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
    
    with open(ndjson_path, "rb") as f:
        files = {
            "file": ("kibana_saved_objects.ndjson", f)
        }
        resp = requests.post(
            f"{KIBANA_HOST}/api/saved_objects/_import?overwrite=true",
            auth=(KIBANA_USER, KIBANA_PASS),
            headers={"kbn-xsrf": "true"},
            files=files
        )
    if resp.status_code == 200:
        print("Data view and discover sessions imported into Kibana!")
    else:
        print(f"Error importing NDJSON: {resp.status_code} -> {resp.text}")

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
    discover_sos = generate_discover_sessions_7_11()

    # 5) Write NDJSON and import via Kibana's Saved Objects API
    write_and_import_so(data_view_so, discover_sos)
