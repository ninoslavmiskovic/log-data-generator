# Unstructured Log Data Generator

This Python script generates a synthetic dataset of unstructured logs in CSV format, simulating logs from various services over a one-year period. The logs include different severity levels, sources, and detailed messages with dynamic content—suitable for testing, analysis, or demonstration purposes.

## Ensuring Unique Datasets on Each Execution

Because the script relies on randomization without a fixed seed, each time you run it:

- **New Log Entries:** You’ll get a fresh set of log entries with different timestamps, sources, levels, and messages.  
- **Varied Data:** Usernames, IP addresses, transaction details, and other data points will be unique.  
- **Different Patterns:** While the overall structure and patterns (like error spikes) remain consistent, the specific details and timing will vary.

This behavior is beneficial for:

- **Testing:** Allows you to test your log analysis tools or applications with varied data.  
- **Simulation:** Helps simulate real-world scenarios where log data is never the same.  
- **Learning:** Provides diverse datasets for practice in data analysis, machine learning, or cybersecurity.

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
- **Dynamic message content** powered by the [Faker](https://faker.readthedocs.io/en/master/) library for realistic data.
- **Now Produces Discover Sessions (Saved Objects) with ES|QL Queries:**  
  In addition to the CSV logs, the script can generate an NDJSON file containing Kibana Discover session objects that include ES|QL queries for analyzing the unstructured data.

## Requirements

- **Python** 3.6 or higher
- **Faker** library

## Installation

### 1. Clone the Repository

If you're using a GitHub repository, clone and navigate into it:

```bash
git clone https://github.com/ninoslavmiskovic/log-data-generator.git
cd log-data-generator
```

### **2. Set Up a Virtual Environment (Recommended)**

It's best practice to use a virtual environment to manage dependencies.

#### **2.1 Create a virtual environment

```bash
python3 -m venv venv
```

#### ***2.2 Activate the virtual environment
```bash
source venv/bin/activate
```

### **3. Install Dependencies**

Install the required Python packages using `pip`.

```bash
pip install Faker
```

### **4. Usage**

Run the script to generate the log dataset.

```bash
python3 generate_logs.py
```

The script will create a file named logs_dataset.csv in the current directory.

- The dataset will contain log entries with the following fields:
  - @timestamp
  -	log.level
  -	source
  -	message 

### Importing the Saved Objects
To see your ES|QL queries in Kibana:

1. Open Kibana and go to Management > Saved Objects.
2. Import the NDJSON file (e.g., kibana_saved_searches.ndjson).
```bash
curl -X POST "http://localhost:5601/api/saved_objects/_import?overwrite=true" \
     -H "kbn-xsrf: true" \
     --form file=@output_saved_objects/kibana_saved_objects.ndjson
```
3. Open Discover, select one of the imported sessions, and run the ES|QL queries to analyze your unstructured logs.

### **5. Customization**

#### **5.1. Adjust the Number of Log Entries**

## Customization

### Adjust the Number of Log Entries

Change the `num_entries` variable in the script to generate more or fewer log entries.

```
num_entries = 10000  # Set to desired number of entries
```

#### **5.2. Modify Log Levels Distribution**

Alter the weights in the `random.choices` function to change the frequency of each log level.

```
level = random.choices(
    log_levels,
    weights=[0.7, 0.1, 0.1, 0.1]  # Adjust weights for INFO, WARN, ERROR, DEBUG
)[0]
```

#### **5.3. Update Message Templates**

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

### **6. Example Output**

An excerpt from the generated `logs_dataset.csv` file:

```csv
Timestamp,Level,Source,Message
2022-10-02T03:12:45Z,INFO,AuthService,User 'jane_doe' logged in successfully from IP address 192.168.1.100
2022-11-05T10:45:37Z,ERROR,DatabaseService,Database connection failed: unable to reach primary database cluster 'db-cluster-1'
2023-08-05T04:00:25Z,ERROR,AuthService,Critical security vulnerability detected: unauthorized access attempt to admin panel from IP '10.0.0.5'
...
```

There is a file in the repo: ***"example_output_logs_dataset.csv"*** you can download and see an example of the output csv.

### **7. Generating Multiple Datasets**

Each time you run the script, it will generate a new CSV file with an incremented sequence number and place it in the `output_csv` directory.

- **Output Files:**

  - Files are named in the format `unstructured-logs-001.csv`, `unstructured-logs-002.csv`, etc.
  - Located in the `output_csv` directory.

**INFO:** Make sure to name your index: ```unstructured-logs``` to make the ES|QL queries work properly. 

### **8. Troubleshooting**

#### **8.1. ModuleNotFoundError: No module named 'faker'**

- Ensure that you have activated your virtual environment (if using one).
- Install the Faker library:

```bash
pip install Faker
```
- If Python 3 is not installed, install it via Homebrew or from the official website: https://www.python.org/downloads/

---

### **9. Contributing**

Contributions are welcome! Please feel free to submit a pull request or open an issue if you have suggestions or find any bugs.

### **10.License**

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

