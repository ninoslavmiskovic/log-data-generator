import csv
import random
import datetime
import os
import json
import uuid
import requests
from faker import Faker

fake = Faker()

# -----------------------------------------------------------------
# Elasticsearch & Kibana Configuration
# -----------------------------------------------------------------
ELASTICSEARCH_HOST = "http://localhost:9200"
KIBANA_HOST = "http://localhost:5601" # add /xxx if you have a custom base path like in dev mode. e.g http://localhost:5601/pga  
ELASTICSEARCH_USER = "elastic"
ELASTICSEARCH_PASS = "changeme"
KIBANA_USER = "elastic"
KIBANA_PASS = "changeme"

# -----------------------------------------------------------------
# 1) Generate Logs -> CSV
# -----------------------------------------------------------------
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
    # Add additional messages if desired for other services
}

def random_timestamp(start, end):
    return start + datetime.timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

def generate_logs(num_entries=1000):
    """
    Generates logs in memory, writes them to a CSV: unstructured-logs-001.csv.
    Returns the list of doc dicts for ingestion.
    """
    entries = []
    start_date = datetime.datetime.now() - datetime.timedelta(days=365)
    end_date = datetime.datetime.now()
    error_spike_dates = [start_date + datetime.timedelta(days=30*i) for i in range(1, 13)]
    
    for _ in range(num_entries):
        if random.random() < 0.05:
            timestamp = (random.choice(error_spike_dates)
                         + datetime.timedelta(seconds=random.randint(0, 3600)))
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
    
    # Sort & write CSV
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

# -----------------------------------------------------------------
# 2) Ingest logs into Elasticsearch
# -----------------------------------------------------------------
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
        print("Index 'unstructured-logs' created or already exists.")
    
    # Bulk
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

# -----------------------------------------------------------------
# 3) Create Data View (Index Pattern) with ID='unstructured-logs'
#    with Kibana 7.11-compatible migration versions
# -----------------------------------------------------------------
def create_data_view_so_7_11():
    """
    Returns a single saved object representing a data view (index-pattern)
    with ID='unstructured-logs', timeFieldName=@timestamp,
    using 7.11.0-compatible migration versions.
    """
    now_str = datetime.datetime.utcnow().isoformat() + "Z"
    return {
        "id": "unstructured-logs",
        "type": "index-pattern",
        "namespaces": ["default"],
        "updated_at": now_str,
        "created_at": now_str,
        # NOTE: Avoid references if not needed
        "version": "WzFd",
        "attributes": {
            "title": "unstructured-logs",
            "timeFieldName": "@timestamp",
            "fields": "[]"
        },
        "references": [],
        "managed": False,
        # Kibana 7.11-friendly migrations:
        "coreMigrationVersion": "7.11.0",
        "typeMigrationVersion": "7.11.0"
    }

# -----------------------------------------------------------------
# 4) Generate Discover Sessions referencing that data view ID
# -----------------------------------------------------------------
def generate_discover_sessions_7_11():
    """
    Builds discover sessions referencing data view ID='unstructured-logs'
    with Kibana 7.11-friendly migration versions.
    """
    now_str = datetime.datetime.utcnow().isoformat() + "Z"
    one_year_ago_str = (datetime.datetime.utcnow() - datetime.timedelta(days=365)).isoformat() + "Z"
    created_by = "u_mGBROF_q5bmFCATbLXAcCwKa0k8JvONAwSruelyKA5E_0"

    session_defs = [
        {
            "title": "Retrieve All Logs",
            "description": "All logs sorted ascending by @timestamp.",
            "query": "FROM unstructured-logs\n| sort @timestamp asc"
        },
        {
            "title": "Count Logs by Level",
            "description": "Count logs grouped by log.level, sorted desc.",
            "query": (
                "FROM unstructured-logs\n"
                "| stats count_all = count() by log.level\n"
                "| sort count_all desc"
            )
        },
        {
            "title": "Error Logs",
            "description": "Only logs with log.level == ERROR",
            "query": (
                "FROM unstructured-logs\n"
                "| where log.level == \"ERROR\"\n"
                "| sort @timestamp desc"
            )
        }
    ]
    so_list = []
    for i, sdef in enumerate(session_defs, start=1):
        search_source = {
            "query": {"esql": sdef["query"]},
            "index": {
                "id": "unstructured-logs",  # data-view ID
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
        so_obj = {
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
                "columns": [],
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
            # Set 7.11 versions
            "coreMigrationVersion": "7.11.0",
            "typeMigrationVersion": "7.11.0"
        }
        so_list.append(so_obj)
    return so_list

# -----------------------------------------------------------------
# 5) Write NDJSON & Import (multipart/form-data)
# -----------------------------------------------------------------
def write_and_import_so(data_view_obj, discover_objs):
    os.makedirs("output_saved_objects", exist_ok=True)
    ndjson_path = os.path.join("output_saved_objects", "kibana_saved_objects.ndjson")
    
    all_objs = [data_view_obj] + discover_objs
    with open(ndjson_path, "w", encoding="utf-8") as f:
        for obj in all_objs:
            f.write(json.dumps(obj) + "\n")
    print(f"Saved data view + discover sessions -> {ndjson_path}")

    # Import
    with open(ndjson_path, "rb") as f:
        files = {
            # Let requests pick the form boundary,
            # do not explicitly set "application/ndjson"
            "file": ("kibana_saved_objects.ndjson", f)
        }
        resp = requests.post(
            f"{KIBANA_HOST}/api/saved_objects/_import?overwrite=true",
            auth=(KIBANA_USER, KIBANA_PASS),
            headers={"kbn-xsrf": "true"},
            files=files
        )
    if resp.status_code == 200:
        print("Data view + discover sessions imported into Kibana 7.11!")
    else:
        print(f"Import error: {resp.status_code} => {resp.text}")

# -----------------------------------------------------------------
# Main
# -----------------------------------------------------------------
if __name__ == "__main__":
    # 1) Generate logs -> CSV
    docs = generate_logs(num_entries=500)

    # 2) Ingest logs into ES
    ingest_logs_to_es(docs)

    # 3) Build data view object with 7.11-friendly versions
    data_view_so = create_data_view_so_7_11()

    # 4) Build discover sessions referencing that data view
    discover_sos = generate_discover_sessions_7_11()

    # 5) Write NDJSON + import
    write_and_import_so(data_view_so, discover_sos)