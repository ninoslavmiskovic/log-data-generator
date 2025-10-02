# Log Data Generator Web UI

A modern web interface for generating synthetic log data and ingesting it into Elasticsearch/Kibana.

## Features

- **Modern Web UI**: Clean, responsive interface built with Bootstrap 5
- **Configurable Log Generation**: Generate 1 to 1,000,000 log entries with realistic data
- **Multiple Log Sources**: AuthService, PaymentService, DatabaseService, NotificationService, CacheService
- **Realistic Data**: Timestamps spanning the last 365 days with error spikes
- **Multiple Output Formats**: CSV export and Elasticsearch ingestion
- **Kibana Integration**: Automatic creation of data views and saved searches
- **Real-time Progress Tracking**: Live updates during generation and ingestion
- **Connection Testing**: Verify Elasticsearch and Kibana connectivity
- **Configuration Management**: Persistent settings with JSON configuration

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   cd /path/to/log-data-generator
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the web application**:
   ```bash
   python app.py
   ```

4. **Open your browser** and navigate to:
   ```
   http://localhost:5000
   ```

## Configuration

### Initial Setup

1. Navigate to **Settings** in the web interface
2. Configure your Elasticsearch connection:
   - Host URL (e.g., `http://localhost:9200`)
   - Username (default: `elastic`)
   - Password (default: `changeme`)

3. Configure your Kibana connection:
   - Host URL (e.g., `http://localhost:5601`)  
   - Username (default: `elastic`)
   - Password (default: `changeme`)

4. Click **Test Connections** to verify your settings
5. Click **Save Configuration** to persist your settings

### Environment Variables (Optional)

You can also set configuration via environment variables:

```bash
export SECRET_KEY="your-secret-key-here"
export ES_HOST="http://localhost:9200"
export ES_USERNAME="elastic"
export ES_PASSWORD="your-password"
export KIBANA_HOST="http://localhost:5601"
export KIBANA_USERNAME="elastic"
export KIBANA_PASSWORD="your-password"
```

## Usage

### Generate Logs

1. Go to **Generate** page
2. Set the number of log entries (1-1,000,000)
3. Choose your options:
   - **Generate CSV file**: Creates a CSV file in `output_csv/`
   - **Ingest logs into Elasticsearch**: Creates index and ingests data
   - **Create Kibana saved objects**: Creates data view and discover sessions

4. Click **Start Generation**
5. Monitor progress on the progress page

### Generated Content

When you enable Kibana integration, the following objects are created:

**Data View:**
- Index pattern: `unstructured-logs`
- Time field: `@timestamp`

**Discover Sessions:**
1. **Retrieve All Logs** - All logs sorted by timestamp
2. **Count Logs by Level** - Aggregation by log level
3. **Count Logs by Source** - Aggregation by source service
4. **Retrieve Error Logs** - Error-level logs only
5. **Parse AuthService (DISSECT)** - Extract user/IP using DISSECT
6. **Parse AuthService (GROK)** - Extract user/IP using GROK

### Log Data Structure

Generated logs include:
- `@timestamp`: ISO timestamp
- `log.level`: INFO (70%), WARN (10%), ERROR (10%), DEBUG (10%)
- `source`: Service name (AuthService, PaymentService, etc.)
- `message`: Realistic log message with dynamic data

## API Endpoints

The web application provides these API endpoints:

- `GET /` - Dashboard
- `GET /config` - Configuration page
- `POST /config` - Save configuration
- `GET /generate` - Log generation page
- `POST /generate` - Start log generation
- `GET /progress/<operation_id>` - Progress tracking page
- `GET /api/status/<operation_id>` - Get operation status (JSON)
- `POST /test-connection` - Test Elasticsearch/Kibana connections

## File Structure

```
├── app.py                 # Flask web application
├── generate_logs.py       # Original log generation script
├── requirements.txt       # Python dependencies
├── config.json           # Configuration file (auto-generated)
├── templates/            # HTML templates
│   ├── index.html        # Dashboard
│   ├── config.html       # Configuration page
│   ├── generate.html     # Log generation page
│   └── progress.html     # Progress tracking
├── static/
│   └── css/
│       └── style.css     # Custom CSS styles
├── output_csv/           # Generated CSV files
└── output_saved_objects/ # Kibana saved objects (NDJSON)
```

## Troubleshooting

### Connection Issues

1. **Elasticsearch connection failed**:
   - Verify Elasticsearch is running
   - Check host URL and port
   - Verify credentials
   - Check firewall/network settings

2. **Kibana connection failed**:
   - Verify Kibana is running
   - Check host URL and port
   - Verify credentials
   - Ensure Kibana can connect to Elasticsearch

3. **Permission errors**:
   - Ensure user has permissions to create indices
   - Verify user can create saved objects in Kibana

### Performance Tips

- Start with smaller datasets (1,000-10,000 entries) for testing
- Use CSV-only generation for very large datasets
- Monitor system resources during large generations
- Consider increasing Elasticsearch heap size for large ingestions

### Development

To run in development mode:

```bash
export FLASK_ENV=development
python app.py
```

This enables debug mode with auto-reloading.

## Security Considerations

- Change default passwords in production
- Use HTTPS for external connections
- Consider using API keys instead of passwords
- Set a secure `SECRET_KEY` environment variable
- Restrict network access to Elasticsearch/Kibana

## License

This project is licensed under the same terms as the original log data generator.
