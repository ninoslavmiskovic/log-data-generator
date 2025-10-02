# Unstructured Log Data Generator

A powerful tool for generating synthetic log data with both **command-line** and **modern web interface** options. Generate realistic, unstructured logs and automatically ingest them into Elasticsearch with pre-built Kibana dashboards and saved searches.

![Dashboard Overview](screenshots/dashboard-overview.png)
*Modern web interface dashboard - your control center for log generation*

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

## 🎯 Generated Content

### Log Structure
```json
{
  "@timestamp": "2024-03-15T14:30:25.123Z",
  "log.level": "INFO",
  "source": "AuthService", 
  "message": "User 'john_doe' logged in successfully from IP address 192.168.1.100"
}
```

### Log Sources & Levels
- **Sources:** AuthService, PaymentService, DatabaseService, NotificationService, CacheService
- **Levels:** INFO (70%), WARN (10%), ERROR (10%), DEBUG (10%)
- **Time Range:** Last 365 days with realistic error spikes

### Kibana Objects Created
When you enable Kibana integration, you get:

**Data View:**
- Index pattern: `unstructured-logs`
- Time field: `@timestamp`

**6 Pre-built Discover Sessions:**
1. **Retrieve All Logs** - Complete log overview
2. **Count Logs by Level** - Level distribution analysis  
3. **Count Logs by Source** - Source service breakdown
4. **Retrieve Error Logs** - Error-only filtering
5. **Parse AuthService (DISSECT)** - Extract user/IP with DISSECT
6. **Parse AuthService (GROK)** - Extract user/IP with GROK

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

## 🔍 Troubleshooting

### Common Issues

**Port 5000 already in use:**
```bash
# The app now runs on port 8080 by default
# Access at: http://localhost:8080
```

**Connection errors:**
- Use the "Test Connections" feature in Settings
- Verify Elasticsearch/Kibana are running
- Check credentials and network connectivity

**Large dataset generation:**
- Monitor system memory during generation
- Consider CSV-only mode for very large datasets
- Increase Elasticsearch heap size if needed

**Installation issues:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Upgrade pip if needed
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

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

- **Security Testing** - Generate realistic security logs for SIEM testing
- **Performance Testing** - Stress test your Elasticsearch clusters
- **Training & Education** - Learn ES|QL, Kibana, and log analysis
- **Development** - Mock data for application development
- **Demonstrations** - Showcase Elastic Stack capabilities
- **Proof of Concepts** - Validate log processing pipelines

## 🌟 What's New

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