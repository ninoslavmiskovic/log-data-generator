import csv
import random
import datetime
import os
from faker import Faker

fake = Faker()

# Define log levels and sources
log_levels = ['INFO', 'WARN', 'ERROR', 'DEBUG']
sources = ['AuthService', 'PaymentService', 'DatabaseService', 'NotificationService', 'CacheService']

# Complete messages dictionary
messages = {
    'AuthService': {
        'INFO': [
            "User '{user}' logged in successfully from IP address {ip_address}",
            "Password reset initiated for user '{user}'; verification email sent",
        ],
        'WARN': [
            "Multiple failed login attempts detected for user '{user}'; account locked for 30 minutes",
        ],
        'ERROR': [
            "Critical security vulnerability detected: unauthorized access attempt to admin panel from IP '{ip_address}'",
            "Authentication service failed to validate token for user '{user}'",
        ],
        'DEBUG': [
            "Generated authentication token for session ID '{session_id}' with expiration time of 2 hours",
            "Password hash generated using SHA-256 algorithm for user '{user}'",
            "Session expired for user ID '{user_id}'; prompting re-authentication",
        ]
    },
    'PaymentService': {
        'INFO': [
            "Refund processed for order ID '{order_id}'; amount refunded: ${amount}",
            "Large volume of transactions processed: {transaction_count} transactions in the last hour",
            "Payment completed successfully for transaction ID '{transaction_id}'",
        ],
        'WARN': [
            "Payment processing delayed due to network latency exceeding {latency}ms threshold",
            "Currency conversion rate not available for '{from_currency}' to '{to_currency}'; using last known rate",
            "Suspicious transaction pattern detected for user '{user}'; flagging for manual review",
        ],
        'ERROR': [
            "Transaction ID '{transaction_id}' declined due to insufficient funds in the user's account",
            "Payment gateway error: {gateway_response}",
        ],
        'DEBUG': [
            "Debugging payment flow for transaction ID '{transaction_id}'",
            "Payment gateway response: {gateway_response}",
        ]
    },
    'DatabaseService': {
        'INFO': [
            "Database query executed successfully: {query}",
            "Backup completed successfully; backup file stored at '{backup_location}'",
            "Connection established to database '{database_name}'",
        ],
        'WARN': [
            "Disk space usage at {disk_usage}%; consider cleaning up old logs and backups",
            "Slow query detected: {query}",
        ],
        'ERROR': [
            "Timeout while executing query: {query}",
            "Data corruption detected in '{table}' table; initiating recovery procedures",
            "Failed to connect to database '{database_name}'",
        ],
        'DEBUG': [
            "Executing query plan optimization for query: {query}",
            "Connection pool status: {pool_status}",
            "Database transaction started for session ID '{session_id}'",
        ]
    },
    'NotificationService': {
        'INFO': [
            "Email notification sent to '{email}' regarding {subject}",
            "Push notification sent to device ID '{device_id}' with message '{message_content}'",
            "SMS sent to '{phone_number}' with message '{message_content}'",
        ],
        'WARN': [
            "Email quota nearing limit; only {emails_remaining} emails remaining for the day",
            "Delayed delivery of notifications due to high server load",
        ],
        'ERROR': [
            "Failed to send SMS to '{phone_number}' due to {error_reason}",
            "Email delivery failed to '{email}' due to SMTP server timeout",
            "Notification service encountered an unexpected error: {error_reason}",
        ],
        'DEBUG': [
            "SMTP server response: {smtp_response}",
            "Notification queue size: {queue_size}",
            "Notification payload: {notification_payload}",
        ]
    },
    'CacheService': {
        'INFO': [
            "Cache updated for key '{cache_key}' after {update_reason}",
            "Cache cleared for user ID '{user_id}'",
        ],
        'WARN': [
            "Cache miss for key '{cache_key}'; fetching data from the database instead",
            "High cache eviction rate detected",
        ],
        'ERROR': [
            "Redis server not responding; attempting to reconnect in {retry_interval} seconds",
            "Cache corruption detected; reinitializing cache",
        ],
        'DEBUG': [
            "Cache eviction policy applied to key '{cache_key}'",
            "Current cache size: {cache_size} items",
            "Cache hit ratio: {cache_hit_ratio}%",
        ]
    },
}

# Function to generate a random timestamp within the last year
def random_timestamp(start, end):
    return start + datetime.timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

# Function to get the next sequence number for the output file
def get_next_sequence_number(output_dir):
    existing_files = [f for f in os.listdir(output_dir) if f.startswith('logs_dataset_') and f.endswith('.csv')]
    sequence_numbers = []
    for filename in existing_files:
        try:
            seq_num = int(filename.split('_')[-1].split('.csv')[0])
            sequence_numbers.append(seq_num)
        except ValueError:
            continue
    if sequence_numbers:
        return max(sequence_numbers) + 1
    else:
        return 1

# Main script
def generate_logs():
    num_entries = 10000  # Adjust as needed
    entries = []

    start_date = datetime.datetime.now() - datetime.timedelta(days=365)
    end_date = datetime.datetime.now()

    # Introduce spikes and patterns
    error_spike_dates = [
        start_date + datetime.timedelta(days=30 * i) for i in range(1, 13)
    ]

    for i in range(num_entries):
        # Randomly select or introduce a spike
        if random.random() < 0.05:  # 5% chance to be in a spike
            timestamp = random.choice(error_spike_dates) + datetime.timedelta(seconds=random.randint(0, 3600))
            level = 'ERROR'
        else:
            timestamp = random_timestamp(start_date, end_date)
            level = random.choices(
                log_levels,
                weights=[0.7, 0.1, 0.1, 0.1]  # Adjust weights for INFO, WARN, ERROR, DEBUG
            )[0]

        source = random.choice(sources)
        message_list = messages.get(source, {}).get(level)

        # Handle cases where message_list might be empty
        if not message_list:
            message_list = ["Generic log message"]

        message_template = random.choice(message_list)

        # Generate dynamic message content
        message_data = {
            'user': fake.user_name(),
            'ip_address': fake.ipv4(),
            'session_id': fake.uuid4(),
            'user_id': random.randint(1000, 9999),
            'order_id': random.randint(100000, 999999),
            'amount': f"{random.uniform(10.0, 500.0):.2f}",
            'transaction_count': random.randint(5000, 15000),
            'latency': random.randint(200, 1000),
            'from_currency': random.choice(['USD', 'EUR', 'GBP']),
            'to_currency': random.choice(['USD', 'EUR', 'GBP']),
            'transaction_id': random.randint(1000000, 9999999),
            'gateway_response': fake.sentence(),
            'query': fake.sentence(),
            'backup_location': fake.file_path(),
            'disk_usage': random.randint(80, 99),
            'table': fake.word(),
            'pool_status': fake.sentence(),
            'email': fake.email(),
            'subject': fake.sentence(),
            'device_id': fake.uuid4(),
            'message_content': fake.sentence(),
            'emails_remaining': random.randint(10, 100),
            'phone_number': fake.phone_number(),
            'error_reason': fake.sentence(),
            'smtp_response': fake.sentence(),
            'queue_size': random.randint(0, 1000),
            'cache_key': fake.word(),
            'update_reason': fake.sentence(),
            'retry_interval': random.randint(1, 10),
            'cache_size': random.randint(1000, 10000),
            'database_name': fake.word(),
            'notification_payload': fake.json(),
            'cache_hit_ratio': f"{random.uniform(50.0, 99.9):.1f}",
        }

        try:
            message = message_template.format(**message_data)
        except KeyError as e:
            print(f"KeyError: Missing key {e} in message template for Source: '{source}', Level: '{level}'")
            message = "Incomplete log message due to missing data."

        entries.append({
            '@timestamp': timestamp.isoformat() + 'Z',
            'log.level': level,
            'source': source,
            'message': message
        })

    # Sort entries by timestamp
    entries.sort(key=lambda x: x['@timestamp'])

    # Create output directory if it doesn't exist
    output_dir = 'output_csv'
    os.makedirs(output_dir, exist_ok=True)

    # Determine the next sequence number for the output file
    next_seq_num = get_next_sequence_number(output_dir)
    filename = f"logs_dataset_{next_seq_num:04d}.csv"
    filepath = os.path.join(output_dir, filename)

    # Write to CSV file
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['@timestamp', 'log.level', 'source', 'message']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for entry in entries:
            writer.writerow(entry)

    print(f"Dataset generated successfully! File saved as '{filepath}'")

if __name__ == "__main__":
    generate_logs()