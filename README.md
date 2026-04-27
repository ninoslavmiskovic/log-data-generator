# Multi-Format Data Generator

A powerful tool for generating **8 different types of synthetic observability and security data** with both **command-line** and **modern web interface** options. Generate realistic data for testing, development, and demonstration purposes across the entire observability stack.

![Dashboard](screenshots/dashboard.png)
*Modern web interface — hero banner, stat cards, and quick-action cards*

---

## 8 Data Types Supported

This project supports **8 comprehensive data types** covering the entire observability and security spectrum:

### Observability Data
- **Unstructured Logs** — Traditional log files with free-form text messages
- **Structured Logs** — JSON-formatted logs with consistent fields and metadata
- **Distributed Traces** — OpenTelemetry-style tracing data showing request flows
- **Metrics & Time Series** — Counter, gauge, histogram, and summary metrics
- **APM Data** — Application Performance Monitoring with transactions and errors

### Security & Infrastructure Data
- **Security Events** — SIEM-style security events with threat intelligence
- **Alerts & Notifications** — Alert manager style alerts with firing/resolved states
- **Network Traffic** — Network flow logs with connection details and protocols

---

## Web Interface

A modern, responsive web UI makes data generation accessible to everyone — no command-line experience required.

![Generate Page](screenshots/generate.png)
*Color-coded data type picker — each category has its own icon and accent color*

### Key Features

- **Modern UI** — Inter font, indigo/violet gradient design system, Bootstrap 5.3
- **Easy Configuration** — Web-based setup for Elasticsearch and Kibana connections
- **Real-time Progress Tracking** — Live progress bar and timeline during generation
- **Connection Testing** — Verify Elasticsearch and Kibana settings before generating
- **Multiple Output Options** — CSV export, Elasticsearch ingestion, and Kibana objects
- **Pre-built Dashboards** — Automatic creation of data views and Discover sessions
- **Password Visibility Toggle** — Show/hide credentials on the Settings page

---

## Quick Start

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

> The app runs on port 8080 by default to avoid conflicts with macOS AirPlay Receiver.

### 4. First-Time Setup
1. **Navigate to Settings** in the navigation bar
2. **Configure your connections** (Elasticsearch host, credentials, Kibana host)
3. **Test connections** to verify everything works
4. **Start generating data**

![Settings Page](screenshots/config.png)
*Settings page — color-coded sections for Elasticsearch, Kibana, and generation limits*

---

## User Workflows

### Workflow 1: First-Time Setup

1. Launch the application and navigate to http://localhost:8080
2. Go to **Settings** → configure Elasticsearch and Kibana connections
3. Click **Test Connections** to verify
4. Click **Save Settings**

### Workflow 2: Generate Logs (CSV Only)

1. Navigate to **Generate** → set number of entries (1–1,000,000)
2. Enable **Export as CSV file** (checked by default)
3. Click **Start Generation** → watch real-time progress
4. CSV saved to `output_csv/`

### Workflow 3: Full Elasticsearch + Kibana Integration

1. Configure connections in Settings
2. Navigate to **Generate** → set parameters and select a data type
3. Enable all options:
   - Export as CSV file
   - Ingest into Elasticsearch
   - Create Kibana Objects
4. Monitor progress → automatic redirect to the progress page
5. Open Kibana → your data view and Discover sessions are ready

### Workflow 4: Bulk Data Generation

1. Adjust max entries in Settings (up to 10 M entries)
2. Use CSV-only mode for fastest generation
3. Monitor system resources during generation
4. Batch-import to Elasticsearch using separate tools if needed

---

## Generated Data Formats

#### Unstructured Logs
```json
{
  "@timestamp": "2024-03-15T14:30:25.123Z",
  "log.level": "INFO",
  "source": "AuthService",
  "message": "User 'john_doe' logged in successfully from IP address 192.168.1.100"
}
```

#### Structured Logs
```json
{
  "@timestamp": "2024-03-15T14:30:25.123Z",
  "service.name": "user-api",
  "service.version": "2.1.3",
  "log.level": "INFO",
  "environment": "production",
  "trace.id": "550e8400-e29b-41d4-a716-446655440000",
  "http.method": "POST",
  "http.status_code": 200,
  "http.response_time_ms": 145,
  "message": "User profile updated successfully"
}
```

#### Distributed Traces
```json
{
  "@timestamp": "2024-03-15T14:30:25.123Z",
  "trace.id": "550e8400-e29b-41d4-a716-446655440000",
  "span.id": "6ba7b810-9dad-11d1",
  "span.parent_id": "6ba7b810-9dad-11d0",
  "span.name": "user-service.authenticate",
  "service.name": "user-service",
  "span.kind": "server",
  "span.status": "OK",
  "duration.ms": 45
}
```

#### Metrics & Time Series
```json
{
  "@timestamp": "2024-03-15T14:30:25.123Z",
  "metric.type": "counter",
  "metric.name": "requests_total",
  "metric.value": 1547,
  "service.name": "api-gateway",
  "environment": "production",
  "labels": { "method": "GET", "status": "success" }
}
```

#### Security Events
```json
{
  "@timestamp": "2024-03-15T14:30:25.123Z",
  "event.type": "authentication",
  "event.severity": "high",
  "event.action": "login_attempt",
  "event.outcome": "failure",
  "source.ip": "192.168.1.100",
  "user.name": "admin",
  "threat.indicator": "brute_force"
}
```

#### Alerts & Notifications
```json
{
  "@timestamp": "2024-03-15T14:30:25.123Z",
  "alert.name": "HighCPUUsage",
  "alert.state": "firing",
  "alert.severity": "critical",
  "metric.value": 95,
  "metric.threshold": 85,
  "labels": { "service": "database", "environment": "production" }
}
```

#### Network Traffic
```json
{
  "@timestamp": "2024-03-15T14:30:25.123Z",
  "network.protocol": "tcp",
  "source.ip": "10.0.1.100",
  "destination.ip": "10.0.2.200",
  "source.port": 45123,
  "destination.port": 443,
  "network.bytes": 8547,
  "network.direction": "outbound",
  "event.action": "allowed"
}
```

#### APM Data
```json
{
  "@timestamp": "2024-03-15T14:30:25.123Z",
  "transaction.id": "txn-001-2024-03-15",
  "transaction.type": "request",
  "transaction.name": "GET /api/users",
  "service.name": "web-app",
  "transaction.duration.ms": 234,
  "transaction.result": "success",
  "http.method": "GET",
  "http.status_code": 200
}
```

---

## Elasticsearch Indices & Kibana Objects

### Index Patterns Created

| Index | Data Type |
|-------|-----------|
| `logs-unstructured` | Unstructured logs |
| `logs-structured` | Structured logs |
| `traces` | Distributed traces |
| `metrics` | Time-series metrics |
| `security-events` | Security & threat data |
| `alerts` | Alerts & notifications |
| `network-traffic` | Network flow data |
| `apm` | APM transactions & errors |

### Kibana Discover Sessions (Unstructured Logs)

1. **Retrieve All Logs** — Full log overview sorted by timestamp
2. **Count Logs by Level** — Log level distribution aggregation
3. **Count Logs by Source** — Breakdown by service/source
4. **Retrieve Error Logs** — Error-only filtering for troubleshooting
5. **Parse AuthService (DISSECT)** — Extract user/IP using DISSECT
6. **Parse AuthService (GROK)** — Extract user/IP using GROK

---

## Command-Line Usage

For automation and scripting, the original CLI is still available:

```bash
source venv/bin/activate

# Run with default settings (1 000 entries)
python generate_logs.py

# Customise entry count in the script
# Edit num_entries= in generate_logs.py
```

---

## Configuration

### Web Interface
All settings are managed through the Settings page:

- **Elasticsearch** — Host URL, username, password
- **Kibana** — Host URL, username, password
- **Generation** — Default entries, maximum limit

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

---

## Progress Tracking

Real-time monitoring during every generation run:

- **Live progress bar** with percentage completion
- **Status badge** (Running / Completed / Failed) in the card header
- **Timeline** of each step with entrance animations and timestamps
- **Success panel** with action buttons on completion
- **Error panel** with retry link on failure

---

## Technical Details

### Architecture

- **Backend** — Flask 3.x with threaded background operations
- **Frontend** — Bootstrap 5.3, Font Awesome 6.5, Inter (Google Fonts), vanilla JS
- **Design system** — CSS custom properties: indigo/violet gradient palette, 8-step shadow scale, easing tokens
- **Storage** — JSON configuration file
- **Session management** — Flask-Session for operation state tracking

### File Structure

```
├── app.py                    # Flask web application
├── data_generators.py        # 8 data type generator classes
├── generate_logs.py          # CLI log generation & Kibana objects
├── requirements.txt          # Python dependencies
├── config.json               # Connection settings (auto-generated)
├── templates/
│   ├── index.html            # Dashboard with hero & stat cards
│   ├── generate.html         # Data type picker & generation form
│   ├── config.html           # Settings with color-coded sections
│   └── progress.html         # Live progress & timeline
├── static/css/style.css      # Design system (CSS custom properties)
├── screenshots/              # UI screenshots
├── output_csv/               # Generated CSV files
└── output_saved_objects/     # Kibana saved objects
```

### Performance Tips

**For large datasets (100 K+ entries):**
- Test with smaller batches (1 K–10 K) first
- Use CSV-only mode to avoid Elasticsearch timeouts on very large runs
- Monitor system memory; each data type uses ~50–100 MB per 100 K entries

**Elasticsearch bulk loading:**
```bash
# Disable replicas during load (re-enable after)
PUT /your-index/_settings
{ "number_of_replicas": 0 }

# Increase index buffer size
PUT /_cluster/settings
{ "transient": { "indices.memory.index_buffer_size": "40%" } }
```

**Production deployment:**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

---

## Troubleshooting

**Port 8080 in use:**
Edit the last line of `app.py` and change `port=8080` to another port (e.g. `3000`).

**Connection errors:**
- Use **Test Connections** on the Settings page
- Verify Elasticsearch / Kibana are running
- Check credentials and firewall rules

**Kibana 415 Unsupported Media Type:**
```bash
# Manual import as a workaround
curl -X POST "http://localhost:5601/api/saved_objects/_import?overwrite=true" \
  -H "kbn-xsrf: true" \
  -H "Authorization: Basic $(echo -n 'elastic:password' | base64)" \
  --form file=@output_saved_objects/kibana_saved_objects.ndjson
```

**Data not appearing in Kibana:**
1. Verify the index was created in Elasticsearch
2. Refresh the index pattern in Kibana → Management → Index Patterns
3. Ensure the Kibana time picker covers the last 365 days
4. Check entry count: `GET /your-index/_count`

---

## What's New

### v4.0 — UI Redesign
- New design system with CSS custom properties (color tokens, shadow scale, easing)
- Inter font throughout all pages
- Gradient navbar (deep indigo → violet) with animated active pill
- **Dashboard** — hero banner with radial glow, stat cards, data types showcase grid, live connection status dots
- **Generate** — color-coded data type cards (8 distinct accent colors), keyboard-accessible selection
- **Settings** — sectioned form layout with colored headers (indigo / green / amber), password visibility toggle
- **Progress** — animated spinner, gradient progress bar, success/error icon circles, timeline with dot connectors
- Bootstrap 5.1 → **5.3.3**, Font Awesome 6.0 → **6.5.0**

### v3.0 — Multi-Format Data Generator
- 8 data types covering the full observability and security spectrum
- Visual data type picker with descriptions and detail panel
- Automatic Elasticsearch mappings per data type
- Industry-standard schemas (OpenTelemetry, ECS)

### v2.0 — Web Interface
- Complete web-based interface
- Real-time progress tracking
- Web-based configuration management
- Built-in connection testing

### v1.x — Command-Line Tool
- Python script for CSV generation
- Elasticsearch ingestion
- Kibana saved objects
- ES|QL query examples

---

## Use Cases

### Observability & Monitoring
- **Performance Testing** — Generate realistic metrics and APM data for dashboard load testing
- **Distributed Tracing** — Test trace correlation and service dependency mapping
- **Log Analysis** — Practice log parsing and alerting with structured/unstructured logs

### Security & Compliance
- **SIEM Testing** — Generate security events for testing detection rules
- **Incident Response** — Practice investigation with realistic attack data
- **Threat Hunting** — Build datasets for detection and analysis training

### Development & Testing
- **Application Development** — Mock data for APM and logging integrations
- **Infrastructure Testing** — Stress test Elasticsearch clusters with realistic data
- **Training & Education** — Learn ES|QL, Kibana, and observability best practices

### Demos & Showcases
- **Elastic Stack Demos** — Showcase full observability across all 8 data types
- **Vendor Evaluations** — Evaluate observability platforms with comprehensive datasets

---

## Contributing

Contributions are welcome:
- Improving the UI/UX
- Adding new data types or fields
- Fixing bugs
- Improving documentation

Please submit pull requests or open issues on GitHub.

## License

MIT License — see [LICENSE](LICENSE) for details.

---

**Ready to generate some data?**

[Launch Web Interface →](http://localhost:8080) | [View WEB_UI_README →](WEB_UI_README.md)
