# Multi-Format Data Generator

A powerful tool for generating **8 different types of synthetic observability and security data** with both **command-line** and **modern web interface** options. Generate realistic data for testing, development, and demonstration purposes across the entire observability stack.

![Dashboard Overview](screenshots/dashboard-overview.png)
*Modern web interface dashboard - your control center for data generation*

## 🆕 8 Data Types Supported

This project now supports **8 comprehensive data types** covering the entire observability and security spectrum:

### 📊 **Observability Data**
- **🗂️ Unstructured Logs** - Traditional log files with free-form text messages
- **💻 Structured Logs** - JSON-formatted logs with consistent fields and metadata  
- **🔗 Distributed Traces** - OpenTelemetry-style tracing data showing request flows
- **📈 Metrics & Time Series** - Counter, gauge, histogram and summary metrics
- **⚡ APM Data** - Application Performance Monitoring with transactions and errors

### 🔒 **Security & Infrastructure Data**
- **🛡️ Security Events** - SIEM-style security events with threat intelligence
- **🚨 Alerts & Notifications** - Alert manager style alerts with firing/resolved states  
- **🌐 Network Traffic** - Network flow logs with connection details and protocols

![Data Type Selection](screenshots/data-type-selection.png)
*Choose from 8 different data types with interactive selection interface*

## 🆕 New Web Interface

This project now includes a **modern, responsive web UI** that makes log generation accessible to everyone - no command line experience required!

### ✨ Key Features

- 🎨 **Modern Web Interface** - Clean, responsive design built with Bootstrap 5
- ⚙️ **Easy Configuration** - Web-based setup for Elasticsearch and Kibana connections  
- 📊 **Real-time Progress Tracking** - Live updates during log generation and ingestion
- 🧪 **Connection Testing** - Verify your Elasticsearch and Kibana settings
- 📈 **Multiple Output Options** - CSV files, Elasticsearch ingestion, and Kibana objects
- 🎯 **Pre-built Dashboards** - Automatic creation of data views and discover sessions
- 🔒 **Secure Configuration** - Encrypted storage of connection credentials

## 🚀 Quick Start (Web Interface)

### 1. Installation
```bash
git clone https://github.com/ninoslavmiskovic/log-data-generator.git
cd log-data-generator
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Launch Web Interface
```bash
python app.py
```

### 3. Access the Application
Open your browser and navigate to: **http://localhost:8080**

> **Note:** The app runs on port 8080 by default to avoid conflicts with macOS AirPlay Receiver which uses port 5000.

### 4. First-Time Setup
1. **Navigate to Settings** (⚙️ Settings in the navigation)
2. **Configure your connections** (see Configuration section below)
3. **Test connections** to verify everything works
4. **Start generating data!**

![Configuration Screen](screenshots/configuration-screen.png)
*Easy-to-use configuration interface for Elasticsearch and Kibana*

## 📋 User Workflows

### Workflow 1: First-Time Setup

1. **Launch the application** and navigate to http://localhost:8080
2. **Go to Settings** → Configure your Elasticsearch and Kibana connections
3. **Test connections** to verify everything is working
4. **Save configuration** for future use

![Settings Flow](screenshots/settings-flow.png)
*Step-by-step configuration process*

### Workflow 2: Generate Logs (CSV Only)

Perfect for users who just want sample data files:

1. **Navigate to Generate** → Set number of entries (1-1,000,000)
2. **Enable "Generate CSV file"** (checked by default)
3. **Click "Start Generation"** → Watch real-time progress
4. **Download your CSV** from the `output_csv/` directory

![Generation Process](screenshots/generation-process.png)
*Real-time progress tracking with detailed status updates*

### Workflow 3: Full Elasticsearch + Kibana Integration

For users who want the complete experience:

1. **Configure connections** (Settings page)
2. **Navigate to Generate** → Set your parameters
3. **Enable all options:**
   - ✅ Generate CSV file
   - ✅ Ingest logs into Elasticsearch  
   - ✅ Create Kibana saved objects
4. **Monitor progress** → Automatic redirect to progress tracking
5. **Access Kibana** → Your data view and discover sessions are ready!

![Kibana Integration](screenshots/kibana-integration.png)
*Pre-built Kibana discover sessions with DISSECT and GROK parsing examples*

### Workflow 4: Bulk Data Generation

For power users generating large datasets:

1. **Adjust max entries** in Settings (up to 10M entries)
2. **Use CSV-only mode** for faster generation
3. **Monitor system resources** during generation
4. **Batch import** to Elasticsearch using separate tools if needed

## 🎯 Generated Content & Examples

### Data Formats by Type

#### 🗂️ **Unstructured Logs**
```json
{
  "@timestamp": "2024-03-15T14:30:25.123Z",
  "log.level": "INFO",
  "source": "AuthService", 
  "message": "User 'john_doe' logged in successfully from IP address 192.168.1.100"
}
```

#### 💻 **Structured Logs**
```json
{
  "@timestamp": "2024-03-15T14:30:25.123Z",
  "service.name": "user-api",
  "service.version": "2.1.3",
  "log.level": "INFO",
  "environment": "production",
  "host.name": "web-server-01",
  "trace.id": "550e8400-e29b-41d4-a716-446655440000",
  "span.id": "6ba7b810-9dad-11d1",
  "user.id": "user-123",
  "http.method": "POST",
  "http.status_code": 200,
  "http.response_time_ms": 145,
  "message": "User profile updated successfully"
}
```

#### 🔗 **Distributed Traces**
```json
{
  "@timestamp": "2024-03-15T14:30:25.123Z",
  "trace.id": "550e8400-e29b-41d4-a716-446655440000",
  "span.id": "6ba7b810-9dad-11d1",
  "span.parent_id": "6ba7b810-9dad-11d0",
  "span.name": "user-service.authenticate",
  "service.name": "user-service",
  "operation.name": "authenticate",
  "span.kind": "server",
  "span.status": "OK",
  "duration.ms": 45,
  "user.id": "user-123",
  "user.email": "john@example.com"
}
```

#### 📈 **Metrics & Time Series**
```json
{
  "@timestamp": "2024-03-15T14:30:25.123Z",
  "metric.type": "counter",
  "metric.name": "requests_total",
  "metric.value": 1547,
  "service.name": "api-gateway",
  "host.name": "gateway-01",
  "environment": "production",
  "labels": {
    "method": "GET",
    "status": "success"
  }
}
```

#### 🛡️ **Security Events**
```json
{
  "@timestamp": "2024-03-15T14:30:25.123Z",
  "event.type": "authentication",
  "event.id": "sec-001-2024-03-15",
  "event.severity": "high",
  "event.action": "login_attempt",
  "event.outcome": "failure",
  "source.ip": "192.168.1.100",
  "user.name": "admin",
  "authentication.method": "password",
  "threat.indicator": "brute_force",
  "message": "Failed login attempt for user"
}
```

#### 🚨 **Alerts & Notifications**
```json
{
  "@timestamp": "2024-03-15T14:30:25.123Z",
  "alert.name": "HighCPUUsage",
  "alert.state": "firing",
  "alert.severity": "critical",
  "alert.id": "alert-cpu-001",
  "metric.value": 95,
  "metric.threshold": 85,
  "labels": {
    "service": "database",
    "environment": "production",
    "instance": "db-server-01"
  },
  "annotations": {
    "summary": "CPU usage is above threshold",
    "description": "CPU usage has exceeded the configured threshold"
  }
}
```

#### 🌐 **Network Traffic**
```json
{
  "@timestamp": "2024-03-15T14:30:25.123Z",
  "flow.id": "flow-001-2024-03-15",
  "network.protocol": "tcp",
  "source.ip": "10.0.1.100",
  "destination.ip": "10.0.2.200",
  "source.port": 45123,
  "destination.port": 443,
  "network.bytes": 8547,
  "network.packets": 12,
  "network.direction": "outbound",
  "event.action": "allowed"
}
```

#### ⚡ **APM Data**
```json
{
  "@timestamp": "2024-03-15T14:30:25.123Z",
  "transaction.id": "txn-001-2024-03-15",
  "transaction.type": "request",
  "transaction.name": "GET /api/users",
  "service.name": "web-app",
  "transaction.duration.ms": 234,
  "transaction.result": "success",
  "user.id": "user-123",
  "trace.id": "550e8400-e29b-41d4-a716-446655440000",
  "http.method": "GET",
  "http.status_code": 200,
  "http.url": "https://api.company.com/users"
}
```

### Index Patterns Created

When you enable Elasticsearch integration, the following indices are created:

- `logs-unstructured` - Unstructured log data
- `logs-structured` - Structured log data  
- `traces` - Distributed tracing data
- `metrics` - Time series metrics
- `security-events` - Security and threat data
- `alerts` - Alert and notification data
- `network-traffic` - Network flow data
- `apm` - Application performance data

### Kibana Objects Created

**Data Views:**
- Automatic index pattern creation with proper field mapping
- Time field configuration (@timestamp)
- Field type optimization for search and visualization

**Discover Sessions (for Unstructured Logs):**
1. **Retrieve All Logs** - Complete log overview sorted by timestamp
2. **Count Logs by Level** - Aggregation showing log level distribution
3. **Count Logs by Source** - Breakdown by service/source
4. **Retrieve Error Logs** - Error-only filtering for troubleshooting
5. **Parse AuthService (DISSECT)** - Extract user/IP using DISSECT parsing
6. **Parse AuthService (GROK)** - Extract user/IP using GROK parsing

> **Note:** Different data types will have their own appropriate saved searches and visualizations.

![Discover Sessions](screenshots/discover-sessions.png)
*Ready-to-use ES|QL queries demonstrating parsing techniques*

## 🛠️ Command Line Usage (Advanced)

For automation and scripting, the original command-line interface is still available:

```bash
# Activate virtual environment
source venv/bin/activate

# Run with default settings (1000 entries)
python generate_logs.py

# Customize in the script
num_entries = 50000  # Edit this value in generate_logs.py
```

### Command Line Features
- **Bulk generation** of up to billions of entries
- **Automatic Elasticsearch ingestion**
- **Kibana saved objects creation**
- **Scriptable and automatable**

## ⚙️ Configuration Options

### Web Interface Configuration
All settings are managed through the web interface:

- **Elasticsearch:** Host, username, password, API keys
- **Kibana:** Host, username, password  
- **Generation:** Default entries, maximum limits
- **Output:** File paths, naming conventions

![Configuration Options](screenshots/configuration-options.png)
*Comprehensive configuration management*

### Environment Variables (Optional)
```bash
export SECRET_KEY="your-secret-key-here"
export ES_HOST="http://localhost:9200"
export ES_USERNAME="elastic"
export ES_PASSWORD="your-password"
export KIBANA_HOST="http://localhost:5601"
export KIBANA_USERNAME="elastic"
export KIBANA_PASSWORD="your-password"
```

## 📊 Progress Tracking

Real-time monitoring of all operations:

- **Live progress bars** with percentage completion
- **Detailed status messages** for each step
- **Timeline view** of all completed actions
- **Error handling** with detailed error messages
- **Success confirmation** with next steps

![Progress Tracking](screenshots/progress-tracking.png)
*Real-time progress tracking with detailed timeline*

## 🔧 Technical Details

### Architecture
- **Backend:** Flask web application with threaded operations
- **Frontend:** Bootstrap 5 with vanilla JavaScript
- **Storage:** JSON configuration files
- **Session Management:** Flask-Session for operation tracking

### File Structure
```
├── app.py                    # Flask web application
├── generate_logs.py          # Core log generation logic  
├── requirements.txt          # Python dependencies
├── config.json              # User configuration (auto-generated)
├── templates/               # HTML templates
│   ├── index.html          # Dashboard
│   ├── config.html         # Configuration page
│   ├── generate.html       # Generation interface
│   └── progress.html       # Progress tracking
├── static/css/style.css    # Custom styling
├── output_csv/             # Generated CSV files
└── output_saved_objects/   # Kibana saved objects
```

### Performance Considerations
- **Memory efficient** - Streams large datasets
- **Background processing** - Non-blocking web interface
- **Progress tracking** - Real-time status updates
- **Error recovery** - Graceful handling of failures

### Performance Tips & Optimization

**For Large Datasets (100K+ entries):**
- Start with smaller batches for testing (1K-10K entries)
- Monitor system memory usage during generation
- Use CSV-only mode for very large datasets to avoid Elasticsearch timeouts
- Consider generating multiple smaller batches instead of one large batch

**Elasticsearch Optimization:**
```bash
# Increase JVM heap size for large ingestions
# In elasticsearch.yml or via environment:
ES_JAVA_OPTS="-Xms2g -Xmx2g"

# Disable replicas during bulk loading (re-enable after)
PUT /your-index/_settings
{
  "number_of_replicas": 0
}

# Use bulk ingestion settings
PUT /_cluster/settings
{
  "transient": {
    "indices.memory.index_buffer_size": "40%"
  }
}
```

**System Resource Management:**
- **Memory:** Each data type uses ~50-100MB per 100K entries during generation
- **Disk:** CSV files are ~50-200KB per 1K entries depending on data type
- **CPU:** Generation is CPU-intensive, consider running during off-peak hours
- **Network:** Elasticsearch ingestion bandwidth depends on entry size and network latency

**Development & Production:**
```bash
# Development mode with auto-reload
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py

# Production deployment with gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

## 🔧 Troubleshooting

### Common Issues

**Port 8080 already in use:**
```bash
# Change the port in app.py if needed
# Line 493: app.run(debug=True, host='0.0.0.0', port=8080)
# Change 8080 to another port like 3000 or 5001
```

**Connection errors:**
- Use the "Test Connections" feature in Settings
- Verify Elasticsearch/Kibana are running
- Check credentials and network connectivity
- Ensure your Elasticsearch cluster accepts connections from your IP

**Kibana saved object import errors (415 Unsupported Media Type):**
```bash
# This is a known issue with some Kibana versions
# The data is still generated and ingested successfully
# You can manually import saved objects if needed:
curl -X POST "http://localhost:5601/api/saved_objects/_import?overwrite=true" \
  -H "kbn-xsrf: true" \
  -H "Authorization: Basic $(echo -n 'elastic:your-password' | base64)" \
  --form file=@output_saved_objects/kibana_saved_objects.ndjson
```

**Large dataset generation:**
- Monitor system memory during generation
- Consider CSV-only mode for very large datasets (1M+ entries)
- Increase Elasticsearch heap size if needed for ingestion
- Use smaller batch sizes for testing first

**Installation issues:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Upgrade pip if needed
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# If you get SSL warnings, they're harmless and won't affect functionality
```

**Data not appearing in Kibana:**
1. **Check index creation:** Verify the index was created in Elasticsearch
2. **Refresh index pattern:** Go to Kibana → Management → Index Patterns → Refresh
3. **Check time range:** Ensure Kibana time picker covers the generated data range (last 365 days)
4. **Verify data ingestion:** Check Elasticsearch directly: `GET /your-index/_count`

### Getting Help
- 📖 Check the [WEB_UI_README.md](WEB_UI_README.md) for detailed web interface documentation
- 🐛 Report issues on GitHub
- 💡 Feature requests welcome

## 🤝 Contributing

We welcome contributions! Whether you're:
- 🎨 Improving the UI/UX
- 🔧 Adding new features  
- 🐛 Fixing bugs
- 📚 Improving documentation

Please feel free to submit pull requests or open issues.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 🎯 Use Cases

### 🔍 **Observability & Monitoring**
- **Performance Testing** - Generate realistic metrics and APM data for load testing dashboards
- **Distributed Tracing** - Test trace correlation and service dependency mapping
- **Log Analysis** - Practice log parsing, correlation, and alerting with structured/unstructured logs
- **Metrics Monitoring** - Validate monitoring systems with time-series data

### 🛡️ **Security & Compliance**
- **SIEM Testing** - Generate security events for testing detection rules and workflows
- **Incident Response** - Practice security incident investigation with realistic attack data
- **Compliance Auditing** - Test audit log collection and compliance reporting
- **Threat Hunting** - Create datasets for threat detection and analysis training

### 🧪 **Development & Testing**
- **Application Development** - Mock data for APM and logging integrations
- **Infrastructure Testing** - Stress test your Elasticsearch clusters with realistic data
- **Training & Education** - Learn ES|QL, Kibana, and observability best practices
- **Proof of Concepts** - Validate observability and security tooling with diverse datasets

### 🎪 **Demonstrations & Showcases**
- **Elastic Stack Demos** - Showcase full observability capabilities across all data types
- **Security Tool Demos** - Demonstrate SIEM capabilities with realistic security events
- **Architecture Presentations** - Illustrate distributed systems with realistic trace data
- **Vendor Evaluations** - Test observability platforms with comprehensive data types

## 🌟 What's New

### v3.0 - Multi-Format Data Generator 🚀
- 🎯 **8 Data Types** - Complete observability and security data spectrum
- 📊 **Advanced Data Types** - Traces, metrics, security events, APM data, network traffic
- 🎨 **Interactive Selection** - Visual data type picker with detailed descriptions
- 🗂️ **Smart Indexing** - Automatic Elasticsearch mappings for each data type
- 📈 **Comprehensive Schemas** - Industry-standard formats (OpenTelemetry, ECS, etc.)

### v2.0 - Web Interface Release
- ✨ Complete web-based interface
- 📊 Real-time progress tracking  
- ⚙️ Web-based configuration management
- 🧪 Built-in connection testing
- 📈 Enhanced user experience
- 🔒 Secure credential storage

### v1.x - Command Line Tool
- 🚀 Original Python script
- 📝 CSV generation
- 🔄 Elasticsearch ingestion
- 📊 Kibana saved objects
- 🎯 ES|QL query examples

---

**Ready to generate some logs?** 🚀

[**Launch Web Interface →**](http://localhost:8080) | [**View Documentation →**](WEB_UI_README.md) | [**Download Release →**](https://github.com/ninoslavmiskovic/log-data-generator/releases)