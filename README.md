# Log Data Generator

This Python script generates a synthetic dataset of unstructured logs in CSV format, simulating logs from various services over a one-year period. The logs include different severity levels, sources, and detailed messages with dynamic content, suitable for testing, analysis, or demonstration purposes.

## Features

- **Simulates realistic log data** from multiple services:
  - `AuthService`
  - `PaymentService`
  - `DatabaseService`
  - `NotificationService`
  - `CacheService`
- **Generates over 10,000 log entries** with timestamps spanning the past year.
- **Includes various log levels**:
  - `INFO`
  - `WARN`
  - `ERROR`
  - `DEBUG`
- **Introduces spikes and patterns** to mimic real-world scenarios:
  - Error spikes occurring monthly.
  - Security incidents and performance issues.
- **Dynamic message content** using the [Faker](https://faker.readthedocs.io/en/master/) library for realistic data.

## Requirements

- **Python** 3.6 or higher
- **Faker** library

## Installation

### 1. Clone the Repository (If Applicable)

If you're using a GitHub repository:

```bash
git clone https://github.com/your-username/log-data-generator.git
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
  - Timestamp
  -	Level
  -	Source
  -	Message 

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

---

### **7. Troubleshooting**

#### **7.1. ModuleNotFoundError: No module named 'faker'**

- Ensure that you have activated your virtual environment (if using one).
- Install the Faker library:

```bash
pip install Faker
```
- If Python 3 is not installed, install it via Homebrew or from the official website: https://www.python.org/downloads/

---

### **8. Contributing**

Contributions are welcome! Please feel free to submit a pull request or open an issue if you have suggestions or find any bugs.

### **9.License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

