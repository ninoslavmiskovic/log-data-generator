import csv
import random
import datetime
import os
import json
import uuid
from faker import Faker

fake = Faker()

# ------------------------------
# Part 1: Generate CSV Logs
# ------------------------------

# Define log.level values and sources
log_levels_list = ["INFO", "WARN", "ERROR", "DEBUG"]
sources = ["AuthService", "PaymentService", "DatabaseService", "NotificationService", "CacheService"]

# Log messages dictionary
messages = {
    "AuthService": {
        "INFO": [
            "User '{user}' logged in successfully from IP address {ip_address}",
            "Password reset initiated for user '{user}'; verification email sent",
        ],
        "WARN": [
            "Multiple failed login attempts detected for user '{user}'; account locked for 30 minutes",
        ],
        "ERROR": [
            "Critical security vulnerability detected: unauthorized access attempt to admin panel from IP '{ip_address}'",
            "Authentication service failed to validate token for user '{user}'",
        ],
        "DEBUG": [
            "Generated authentication token for session ID '{session_id}' with expiration time of 2 hours",
            "Password hash generated using SHA-256 algorithm for user '{user}'",
            "Session expired for user ID '{user_id}'; prompting re-authentication",
        ]
    },
    "PaymentService": {
        "INFO": [
            "Refund processed for order ID '{order_id}'; amount refunded: ${amount}",
            "Large volume of transactions processed: {transaction_count} transactions in the last hour",
            "Payment completed successfully for transaction ID '{transaction_id}'",
        ],
        "WARN": [
            "Payment processing delayed due to network latency exceeding {latency}ms threshold",
            "Currency conversion rate not available for '{from_currency}' to '{to_currency}'; using last known rate",
            "Suspicious transaction pattern detected for user '{user}'; flagging for manual review",
        ],
        "ERROR": [
            "Transaction ID '{transaction_id}' declined due to insufficient funds in the user's account",
            "Payment gateway error: {gateway_response}",
        ],
        "DEBUG": [
            "Debugging payment flow for transaction ID '{transaction_id}'",
            "Payment gateway response: {gateway_response}",
        ]
    },
    "DatabaseService": {
        "INFO": [
            "Database query executed successfully: {query}",
            "Backup completed successfully; backup file stored at '{backup_location}'",
            "Connection established to database '{database_name}'",
        ],
        "WARN": [
            "Disk space usage at {disk_usage}%; consider cleaning up old logs and backups",
            "Slow query detected: {query}",
        ],
        "ERROR": [
            "Timeout while executing query: {query}",
            "Data corruption detected in '{table}' table; initiating recovery procedures",
            "Failed to connect to database '{database_name}'",
        ],
        "DEBUG": [
            "Executing query plan optimization for query: {query}",
            "Connection pool status: {pool_status}",
            "Database transaction started for session ID '{session_id}'",
        ]
    },
    "NotificationService": {
        "INFO": [
            "Email notification sent to '{email}' regarding {subject}",
            "Push notification sent to device ID '{device_id}' with message '{message_content}'",
            "SMS sent to '{phone_number}' with message '{message_content}'",
        ],
        "WARN": [
            "Email quota nearing limit; only {emails_remaining} emails remaining for the day",
            "Delayed delivery of notifications due to high server load",
        ],
        "ERROR": [
            "Failed to send SMS to '{phone_number}' due to {error_reason}",
            "Email delivery failed to '{email}' due to SMTP server timeout",
            "Notification service encountered an unexpected error: {error_reason}",
        ],
        "DEBUG": [
            "SMTP server response: {smtp_response}",
            "Notification queue size: {queue_size}",
            "Notification payload: {notification_payload}",
        ]
    },
    "CacheService": {
        "INFO": [
            "Cache updated for key '{cache_key}' after {update_reason}",
            "Cache cleared for user ID '{user_id}'",
        ],
        "WARN": [
            "Cache miss for key '{cache_key}'; fetching data from the database instead",
            "High cache eviction rate detected",
        ],
        "ERROR": [
            "Redis server not responding; attempting to reconnect in {retry_interval} seconds",
            "Cache corruption detected; reinitializing cache",
        ],
        "DEBUG": [
            "Cache eviction policy applied to key '{cache_key}'",
            "Current cache size: {cache_size} items",
            "Cache hit ratio: {cache_hit_ratio}%",
        ]
    },
}

def random_timestamp(start, end):
    return start + datetime.timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

def get_next_sequence_number(output_dir):
    existing_files = [f for f in os.listdir(output_dir) if f.startswith("unstructured-logs-") and f.endswith(".csv")]
    sequence_numbers = []
    for filename in existing_files:
        try:
            seq_num = int(filename.replace("unstructured-logs-", "").replace(".csv", ""))
            sequence_numbers.append(seq_num)
        except ValueError:
            continue
    return max(sequence_numbers) + 1 if sequence_numbers else 1

def generate_logs():
    num_entries = 10000  # Adjust as needed
    entries = []
    start_date = datetime.datetime.now() - datetime.timedelta(days=365)
    end_date = datetime.datetime.now()
    # Create error spikes roughly every 30 days
    error_spike_dates = [start_date + datetime.timedelta(days=30 * i) for i in range(1, 13)]
    
    for i in range(num_entries):
        if random.random() < 0.05:  # 5% chance for an error spike
            timestamp = random.choice(error_spike_dates) + datetime.timedelta(seconds=random.randint(0, 3600))
            level = "ERROR"
        else:
            timestamp = random_timestamp(start_date, end_date)
            level = random.choices(log_levels_list, weights=[0.7, 0.1, 0.1, 0.1])[0]
            
        source = random.choice(sources)
        message_list = messages.get(source, {}).get(level, ["Generic log message"])
        message_template = random.choice(message_list)
        message_data = {
            "user": fake.user_name(),
            "ip_address": fake.ipv4(),
            "session_id": fake.uuid4(),
            "user_id": random.randint(1000, 9999),
            "order_id": random.randint(100000, 999999),
            "amount": f"{random.uniform(10.0, 500.0):.2f}",
            "transaction_count": random.randint(5000, 15000),
            "latency": random.randint(200, 1000),
            "from_currency": random.choice(["USD", "EUR", "GBP"]),
            "to_currency": random.choice(["USD", "EUR", "GBP"]),
            "transaction_id": random.randint(1000000, 9999999),
            "gateway_response": fake.sentence(),
            "query": fake.sentence(),
            "backup_location": fake.file_path(),
            "disk_usage": random.randint(80, 99),
            "table": fake.word(),
            "pool_status": fake.sentence(),
            "email": fake.email(),
            "subject": fake.sentence(),
            "device_id": fake.uuid4(),
            "message_content": fake.sentence(),
            "emails_remaining": random.randint(10, 100),
            "phone_number": fake.phone_number(),
            "error_reason": fake.sentence(),
            "smtp_response": fake.sentence(),
            "queue_size": random.randint(0, 1000),
            "cache_key": fake.word(),
            "update_reason": fake.sentence(),
            "retry_interval": random.randint(1, 10),
            "cache_size": random.randint(1000, 10000),
            "database_name": fake.word(),
            "notification_payload": fake.json(),
            "cache_hit_ratio": f"{random.uniform(50.0, 99.9):.1f}",
        }
        
        try:
            message = message_template.format(**message_data)
        except KeyError as e:
            print(f"KeyError: Missing key {e} for source '{source}', level '{level}'")
            message = "Incomplete log message due to missing data."
        
        # Use "log.level" as the key (with a dot) for ES|QL compatibility.
        entries.append({
            "@timestamp": timestamp.isoformat() + "Z",
            "log.level": level,
            "source": source,
            "message": message
        })
    
    entries.sort(key=lambda x: x["@timestamp"])
    output_dir = "output_csv"
    os.makedirs(output_dir, exist_ok=True)
    next_seq_num = get_next_sequence_number(output_dir)
    filename = f"unstructured-logs-{next_seq_num:03d}.csv"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["@timestamp", "log.level", "source", "message"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for entry in entries:
            writer.writerow(entry)
    print(f"Dataset generated successfully! File saved as '{filepath}'")

# ------------------------------
# Part 2: Generate Saved Objects (Discover sessions, Lens, Dashboard)
# ------------------------------

def generate_saved_searches():
    definitions = [
        {
            "title": "Retrieve All Logs",
            "description": "Displays all logs sorted by timestamp in ascending order.",
            "query": (
                "FROM unstructured-logs\n"
                "| sort @timestamp asc // sort logs by timestamp in ascending order"
            ),
            "columns": [],
            "sort": []
        },
        {
            "title": "Count Logs by Level",
            "description": "Counts the number of logs for each log level.",
            "query": (
                "FROM unstructured-logs\n"
                "| stats count_all = count() by log.level // count logs grouped by log.level\n"
                "| sort count_all desc // sort counts in descending order"
            ),
            "columns": [],
            "sort": []
        },
        {
            "title": "Count Logs by Source",
            "description": "Counts the number of logs for each source.",
            "query": (
                "FROM unstructured-logs\n"
                "| stats count_all = count() by source // count logs grouped by source\n"
                "| sort count_all desc // sort counts in descending order"
            ),
            "columns": ["count_all", "source"],
            "sort": []
        },
        {
            "title": "Retrieve Error Logs",
            "description": "Shows error logs with timestamp, source, and message.",
            "query": (
                "FROM unstructured-logs\n"
                "| where log.level == \"ERROR\" // filter for error logs\n"
                "| sort @timestamp desc // sort logs by timestamp in descending order\n"
                "| keep @timestamp, source, message // keep only timestamp, source, and message fields"
            ),
            "columns": [],
            "sort": []
        },
        {
            "title": "Parse AuthService Logs with Dissect",
            "description": "Parses AuthService info logs using dissect to extract user and IP address.",
            "query": (
                "FROM unstructured-logs\n"
                "| dissect message \"User '%{user}' logged in successfully from IP address %{ip_address}\" // extract user and ip_address using dissect\n"
                "| where source == \"AuthService\" and log.level == \"INFO\" // filter for AuthService info logs\n"
                "| sort @timestamp desc // sort logs by timestamp in descending order\n"
                "| keep @timestamp, user, ip_address // keep only timestamp, user, and ip_address fields"
            ),
            "columns": [],
            "sort": []
        },
        {
            "title": "Parse AuthService Logs with Grok",
            "description": "Parses AuthService info logs using grok to extract user and IP address.",
            "query": (
                "FROM unstructured-logs\n"
                "| grok message \"User '%{USERNAME:user}' logged in successfully from IP address %{IP:ip_address}\" // extract user and ip_address using grok\n"
                "| where source == \"AuthService\" and log.level == \"INFO\" // filter for AuthService info logs\n"
                "| sort @timestamp desc // sort logs by timestamp in descending order\n"
                "| keep @timestamp, user, ip_address // keep only timestamp, user, and ip_address fields"
            ),
            "columns": [],
            "sort": []
        }
    ]
    
    now_dt = datetime.datetime.utcnow()
    one_year_ago_dt = now_dt - datetime.timedelta(days=365)
    now_iso = now_dt.isoformat() + "Z"
    one_year_ago_iso = one_year_ago_dt.isoformat() + "Z"
    
    created_by = "u_mGBROF_q5bmFCATbLXAcCwKa0k8JvONAwSruelyKA5E_0"
    version = "8.9.0"
    now_str = now_iso

    saved_searches = []
    for d in definitions:
        panel_uuid = str(uuid.uuid4())
        panel_ref = f"{panel_uuid}:panel_{panel_uuid}"
        search_source = {
            "query": {"esql": d["query"]},
            "index": {
                "id": "dbe3d33b8a15e80b61e4f52b8275675f49f957abaf82d186f114f1518eea4733",
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
        obj = {
            "id": f"Discover_session_{len(saved_searches)+1}",
            "type": "search",
            "namespaces": ["default"],
            "updated_at": now_str,
            "created_at": now_str,
            "created_by": created_by,
            "updated_by": created_by,
            "version": version,
            "attributes": {
                "title": d["title"],
                "description": d["description"],
                "hits": 0,
                "columns": d["columns"],
                "sort": d["sort"],
                "kibanaSavedObjectMeta": {
                    "searchSourceJSON": json.dumps(search_source)
                },
                "grid": {},
                "hideChart": False,
                "isTextBasedQuery": True,
                "timeRestore": True,
                "timeRange": {
                    "from": one_year_ago_iso,
                    "to": now_iso
                }
            },
            "references": [
                {
                    "name": panel_ref,
                    "type": "search",
                    "id": f"Discover_session_{len(saved_searches)+1}"
                }
            ],
            "managed": False,
            "coreMigrationVersion": "8.9.0",
            "typeMigrationVersion": "8.9.0"
        }
        obj["panelRefName"] = panel_ref
        saved_searches.append(obj)
    return saved_searches

def generate_lens_saved_object():
    now_dt = datetime.datetime.utcnow()
    now_iso = now_dt.isoformat() + "Z"
    created_by = "u_mGBROF_q5bmFCATbLXAcCwKa0k8JvONAwSruelyKA5E_0"
    version = "8.9.0"
    # Use "state" instead of "lensState" to avoid strict dynamic mapping errors.
    lens_obj = {
        "id": "Sample_Lens_1",
        "type": "lens",
        "namespaces": ["default"],
        "updated_at": now_iso,
        "created_at": now_iso,
        "created_by": created_by,
        "updated_by": created_by,
        "version": version,
        "attributes": {
            "title": "Sample Lens Visualization",
            "visualizationType": "lnsXY",
            "state": {
                "datasourceStates": {
                    "textBased": {
                        "layers": {}
                    }
                },
                "visualization": {},
                "query": {"query": "", "language": "kuery"},
                "filters": []
            }
        },
        "references": [],
        "managed": False,
        "coreMigrationVersion": "8.9.0",
        "typeMigrationVersion": "8.9.0"
    }
    return lens_obj

def generate_dashboard(saved_searches, lens_obj):
    now_dt = datetime.datetime.utcnow()
    now_iso = now_dt.isoformat() + "Z"
    created_by = "u_mGBROF_q5bmFCATbLXAcCwKa0k8JvONAwSruelyKA5E_0"
    version = "8.9.0"
    dashboard_id = str(uuid.uuid4())

    panels = []
    references = []
    # Arrange each Discover session in a 2-column grid.
    for ss in saved_searches:
        panels.append({
            "type": "search",
            "title": ss["attributes"]["title"],
            "panelRefName": ss["panelRefName"],
            "embeddableConfig": {
                "description": ss["attributes"]["description"]
            },
            "panelIndex": ss["panelRefName"],
            "gridData": {
                "x": 0 if len(panels) % 2 == 0 else 24,
                "y": (len(panels) // 2) * 15,
                "w": 24,
                "h": 15,
                "i": ss["panelRefName"]
            }
        })
        references.append({
            "name": ss["panelRefName"],
            "type": "search",
            "id": ss["id"]
        })
    # Create a unique panel for the Lens visualization by reference.
    lens_uuid = str(uuid.uuid4())
    lens_ref = f"{lens_uuid}:panel_{lens_uuid}"
    panels.append({
        "type": "lens",
        "title": lens_obj["attributes"]["title"],
        "panelRefName": lens_ref,
        "embeddableConfig": {
            "description": lens_obj["attributes"]["title"],
            "query": {"esql": "FROM unstructured-logs\n| sort @timestamp asc\n| eval week = DATE_TRUNC(1w, @timestamp) | stats count(*) by week"}
        },
        "panelIndex": lens_ref,
        "gridData": {
            "x": 0,
            "y": (len(saved_searches) // 2) * 15,
            "w": 48,
            "h": 15,
            "i": lens_ref
        }
    })
    references.append({
        "name": lens_ref,
        "type": "lens",
        "id": lens_obj["id"]
    })
    
    dashboard_obj = {
        "id": dashboard_id,
        "type": "dashboard",
        "namespaces": ["default"],
        "updated_at": now_iso,
        "created_at": now_iso,
        "created_by": created_by,
        "updated_by": created_by,
        "version": version,
        "attributes": {
            "version": 3,
            "description": "",
            "refreshInterval": {"pause": True, "value": 60000},
            "timeRestore": True,
            "timeFrom": "now-1y",
            "timeTo": "now",
            "title": "Dashboard_example_with_all_ES|QL_panels",
            "controlGroupInput": {},
            "optionsJSON": json.dumps({
                "useMargins": True,
                "syncColors": False,
                "syncCursor": True,
                "syncTooltips": False,
                "hidePanelTitles": False
            }),
            "panelsJSON": json.dumps(panels),
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({"filter": [], "query": {"query": "", "language": "kuery"}})
            }
        },
        "references": references,
        "managed": False,
        "coreMigrationVersion": "8.9.0",
        "typeMigrationVersion": "8.9.0"
    }
    return dashboard_obj

def write_saved_objects():
    saved_searches = generate_saved_searches()
    lens_obj = generate_lens_saved_object()
    dashboard_obj = generate_dashboard(saved_searches, lens_obj)
    
    all_objects = []
    all_objects.extend(saved_searches)
    all_objects.append(lens_obj)
    all_objects.append(dashboard_obj)
    
    output_dir = "output_saved_objects"
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, "kibana_saved_objects.ndjson")
    with open(filepath, "w", encoding="utf-8") as f:
        for obj in all_objects:
            f.write(json.dumps(obj) + "\n")
    print(f"Kibana Saved Objects generated successfully! File saved as '{filepath}'")

# ------------------------------
# Main
# ------------------------------

if __name__ == "__main__":
    generate_logs()
    write_saved_objects()
