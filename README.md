# Unstructured Log Data Generator

This Python script generates a synthetic dataset of unstructured logs in CSV format, simulating logs from various services over a one-year period. The logs include different severity levels, sources, and detailed messages with dynamic content—suitable for testing, analysis, or demonstration purposes.

In this updated version, the script not only generates and saves logs but also:
- **Automatically ingests the logs into Elasticsearch** under the index `unstructured-logs`.
- **Creates a Kibana data view (index-pattern) named `unstructured-logs`** via the Saved Objects API.
- **Generates Discover Session saved objects** with ES|QL queries that reference the newly created data view.
- **Automatically imports** the saved objects into Kibana using the Saved Objects API (via multipart/form-data).

This end-to-end automation lets you run the script once and have your log data, data view, and discover sessions all set up in your local environment—no manual uploads required.

---

## Ensuring Unique Datasets on Each Execution

Because the script relies on randomization without a fixed seed, each time you run it:
- **New Log Entries:** A fresh set of log entries with different timestamps, sources, levels, and messages is generated.
- **Varied Data:** Usernames, IP addresses, transaction details, and other data points are unique.
- **Different Patterns:** While the overall structure and patterns (like error spikes) remain consistent, the specific details and timing will vary.

This is beneficial for:
- **Testing:** Your log analysis tools or applications can be tested with varied data.
- **Simulation:** Real-world scenarios, where log data is never the same, can be mimicked.
- **Learning:** It provides diverse datasets for practice in data analysis, machine learning, or cybersecurity.

---

## Features

- **Simulates realistic log data** from multiple services:
  - `AuthService`
  - `PaymentService`
  - `DatabaseService`
  - `NotificationService`
  - `CacheService`
- **Generates over 10,000 log entries** with timestamps spanning the past year.
- **Includes various log levels:**
  - `INFO`
  - `WARN`
  - `ERROR`
  - `DEBUG`
- **Introduces spikes and patterns** to mimic real-world scenarios:
  - Monthly error spikes.
  - Security incidents and performance issues.
- **Dynamic message content** powered by the [Faker](https://faker.readthedocs.io/en/master/) library.
- **Automatic ingestion into Elasticsearch:**
  - Logs are bulk-indexed into the `unstructured-logs` index.
- **Automatic creation of a Kibana data view:**
  - A data view (index-pattern) with the ID `unstructured-logs` is created so that Discover, Visualize, and Dashboard apps can use it.
- **Generates Discover Sessions with ES|QL queries:**
  - Saved objects for Discover sessions are generated referencing the data view.
- **Automatic import of Saved Objects:**
  - The NDJSON file containing the data view and Discover sessions is automatically imported into Kibana via the Saved Objects API.

---

## Requirements

- **Python** 3.6 or higher
- **Faker** and **requests** libraries

---

## Installation

### 1. Clone the Repository

```
git clone https://github.com/ninoslavmiskovic/log-data-generator.git
cd log-data-generator
```

### 2. Set Up a Virtual Environment (Recommended)**

It's best practice to use a virtual environment to manage dependencies.

#### 2.1 Create a virtual environment

```
python3 -m venv venv
```

#### 2.2 Activate the virtual environment

```
source venv/bin/activate
```

### 3. Install Dependencies**

Install the required Python packages using `pip`.

```
pip install Faker requests
```

### 4. Usage**

Run the script to perform the full end-to-end process:

```
python3 generate_logs.py
```

This will:

1. **Generate logs** and write them to a CSV file in output_csv/ (e.g., unstructured-logs-001.csv).
2. **Bulk ingest the logs** into Elasticsearch under the index unstructured-logs.
3. **Automatically create a data view** (index-pattern) with ID unstructured-logs, using @timestamp as the time field.
4. **Generate Discover Session saved objects** with ES|QL queries
5. **Write the saved objects** to output_saved_objects/kibana_saved_objects.ndjson and **automatically import them into Kibana** using the Saved Objects API.

The script will create a file named logs_dataset.csv in the current directory.

- The dataset will contain log entries with the following fields:
  - @timestamp
  -	log.level
  -	source
  -	message 

### Importing the Saved Objects Manually (Optional)
If needed, you can manually import the NDJSON file:

1. Open Kibana and go to Management > Saved Objects.
2. Import the NDJSON file (e.g., kibana_saved_searches.ndjson).
```bash
curl -X POST "http://localhost:5601/api/saved_objects/_import?overwrite=true" \
     -H "kbn-xsrf: true" \
     --form file=@output_saved_objects/kibana_saved_objects.ndjson
```
3. Open Discover, select one of the imported sessions, and run the ES|QL queries to analyze your unstructured logs.

### 5. Customization**

#### 5.1. Adjust the Number of Log Entries

## Customization

### Adjust the Number of Log Entries

Change the `num_entries` variable in the script to generate more or fewer log entries.

```
num_entries = 10000  # Set to desired number of entries
```

#### 5.2. Modify Log Levels Distribution

Alter the weights in the `random.choices` function to change the frequency of each log level.

```
level = random.choices(
    log_levels,
    weights=[0.7, 0.1, 0.1, 0.1]  # Adjust weights for INFO, WARN, ERROR, DEBUG
)[0]
```

#### 5.3. Update Message Templates

Edit the `messages` dictionary in the script to add or modify message templates for different services and log levels.

```
messages = {
    'AuthService': {
        'INFO': [
            "User '{user}' logged in successfully from IP address {ip_address}",
            # Add more templates as needed
        ],
        # ... other levels and services
    },
    # ... other services
}
```

### 6. Example Output**

An excerpt from the generated `logs_dataset.csv` file:

```csv
Timestamp,Level,Source,Message
2022-10-02T03:12:45Z,INFO,AuthService,User 'jane_doe' logged in successfully from IP address 192.168.1.100
2022-11-05T10:45:37Z,ERROR,DatabaseService,Database connection failed: unable to reach primary database cluster 'db-cluster-1'
2023-08-05T04:00:25Z,ERROR,AuthService,Critical security vulnerability detected: unauthorized access attempt to admin panel from IP '10.0.0.5'
...
```

There is a file in the repo: ***"example_output_logs_dataset.csv"*** you can download and see an example of the output csv.

### 7. Generating Multiple Datasets

Each time you run the script, it will generate a new CSV file with an incremented sequence number and place it in the `output_csv` directory.

- Output Files:

  - Files are named in the format `unstructured-logs-001.csv`, `unstructured-logs-002.csv`, etc.
  - Located in the `output_csv` directory.

**INFO:** Make sure to name your index: ```unstructured-logs``` to make the ES|QL queries work properly. 

### 8. Troubleshooting

#### **8.1. ModuleNotFoundError: No module named 'faker'**

- Ensure that you have activated your virtual environment (if using one).
- Install the Faker library:

```bash
pip install Faker
```
- If Python 3 is not installed, install it via Homebrew or from the official website: https://www.python.org/downloads/

---

### 9. Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue if you have suggestions or find any bugs.

### 10.License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

