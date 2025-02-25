import csv
import random
import datetime
import os
import json
from faker import Faker

fake = Faker()

# Define log.level values and sources
log_levels_list = ['INFO', 'WARN', 'ERROR', 'DEBUG']
sources = ['AuthService', 'PaymentService', 'DatabaseService', 'NotificationService', 'CacheService']

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

# Generate a random timestamp within the last year
def random_timestamp(start, end):
    return start + datetime.timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

# Get next sequence number for log CSV filename
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

# Generate log entries and save as CSV using "log.level" as the field name.
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
        
        # Use "log.level" as the key (with a dot) for ES|QL compatibility
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
        # Fieldnames include "log.level" (with a dot)
        fieldnames = ["@timestamp", "log.level", "source", "message"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for entry in entries:
            writer.writerow(entry)
    print(f"Dataset generated successfully! File saved as '{filepath}'")

# Generate Kibana Discover Saved Search objects as NDJSON.
def generate_kibana_saved_objects():
    # Saved search definitions with explanatory titles and ES|QL queries.
    saved_search_definitions = [
        {
            "title": "Retrieve All Logs",
            "description": "Displays all logs sorted by timestamp in ascending order.",
            "query": (
                "FROM unstructured-logs\n"
                "| where @timestamp >= now() - 1y // filter for logs from the last 1 year\n"
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
                "| where @timestamp >= now() - 1y // filter for logs from the last 1 year\n"
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
                "| where @timestamp >= now() - 1y // filter for logs from the last 1 year\n"
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
                "| where @timestamp >= now() - 1y // filter for logs from the last 1 year\n"
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
                "| where @timestamp >= now() - 1y // filter for logs from the last 1 year\n"
                "| dissect message \"User '%{user}' logged in successfully from IP address %{ip_address}\" // extract user and ip_address from message using dissect\n"
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
                "| where @timestamp >= now() - 1y // filter for logs from the last 1 year\n"
                "| grok message \"User '%{USERNAME:user}' logged in successfully from IP address %{IP:ip_address}\" // extract user and ip_address using grok\n"
                "| where source == \"AuthService\" and log.level == \"INFO\" // filter for AuthService info logs\n"
                "| sort @timestamp desc // sort logs by timestamp in descending order\n"
                "| keep @timestamp, user, ip_address // keep only timestamp, user, and ip_address fields"
            ),
            "columns": [],
            "sort": []
        }
    ]
    
    # Use a fixed index object (as in your modified example)
    index_obj = {
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
    }
    
    # Compute time range: last 12 months from now
    now_dt = datetime.datetime.utcnow()
    one_year_ago_dt = now_dt - datetime.timedelta(days=365)
    now_iso = now_dt.isoformat() + "Z"
    one_year_ago_iso = one_year_ago_dt.isoformat() + "Z"
    
    now_str = now_iso
    created_by = "u_mGBROF_q5bmFCATbLXAcCwKa0k8JvONAwSruelyKA5E_0"
    version = "WzExLDFd"
    
    ndjson_lines = []
    # Create each saved search object with ID as Discover_session_X and the descriptive title.
    for i, ss in enumerate(saved_search_definitions, start=1):
        search_source = {
            "query": {"esql": ss["query"]},
            "index": index_obj,
            "filter": []
        }
        saved_object = {
            "id": f"Discover_session_{i}",
            "type": "search",
            "namespaces": ["default"],
            "updated_at": now_str,
            "created_at": now_str,
            "created_by": created_by,
            "updated_by": created_by,
            "version": version,
            "attributes": {
                "title": ss["title"],
                "description": ss["description"],
                "hits": 0,
                "columns": ss["columns"],
                "sort": ss["sort"],
                "kibanaSavedObjectMeta": {
                    "searchSourceJSON": json.dumps(search_source)
                },
                "grid": {},
                "hideChart": False,
                "isTextBasedQuery": True,
                "timeRestore": False,
                "timeRange": {
                    "from": one_year_ago_iso,
                    "to": now_iso
                }
            },
            "references": [],
            "managed": False,
            "coreMigrationVersion": "8.8.0",
            "typeMigrationVersion": "10.5.0"
        }
        ndjson_lines.append(json.dumps(saved_object))
    
    output_dir = "output_saved_objects"
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, "kibana_saved_searches.ndjson")
    with open(filepath, "w", encoding="utf-8") as f:
        for line in ndjson_lines:
            f.write(line + "\n")
    print(f"Kibana Saved Search objects generated successfully! File saved as '{filepath}'")

if __name__ == "__main__":
    generate_logs()
    generate_kibana_saved_objects()
