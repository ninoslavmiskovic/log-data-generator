import json
import os
import csv
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_session import Session
import tempfile
import threading
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

# Import the log generation functions and data generators
from generate_logs import (
    ingest_logs_to_es, create_data_view_so_7_11,
    generate_discover_sessions_7_11, write_and_import_so
)
from data_generators import DATA_GENERATORS

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Configuration file path
CONFIG_FILE = 'config.json'

# Default configuration
DEFAULT_CONFIG = {
    'elasticsearch': {
        'host': 'http://localhost:9200',
        'username': 'elastic',
        'password': 'changeme'
    },
    'kibana': {
        'host': 'http://localhost:5601',
        'username': 'elastic',
        'password': 'changeme'
    },
    'log_generation': {
        'default_entries': 1000,
        'max_entries': 1000000
    }
}

# Global variables for tracking operations
operation_status = {}
operation_lock = threading.Lock()

def load_config():
    """Load configuration from file or create default"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """Save configuration to file"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def update_operation_status(operation_id, status, message=None, progress=None):
    """Update operation status with thread safety"""
    with operation_lock:
        if operation_id not in operation_status:
            operation_status[operation_id] = {}
        operation_status[operation_id].update({
            'status': status,
            'message': message,
            'progress': progress,
            'timestamp': datetime.now().isoformat()
        })

@app.route('/')
def index():
    """Main dashboard"""
    config = load_config()
    return render_template('index.html', config=config)

@app.route('/config', methods=['GET', 'POST'])
def config():
    """Configuration page"""
    if request.method == 'POST':
        try:
            new_config = {
                'elasticsearch': {
                    'host': request.form.get('es_host', '').strip(),
                    'username': request.form.get('es_username', '').strip(),
                    'password': request.form.get('es_password', '').strip()
                },
                'kibana': {
                    'host': request.form.get('kibana_host', '').strip(),
                    'username': request.form.get('kibana_username', '').strip(),
                    'password': request.form.get('kibana_password', '').strip()
                },
                'log_generation': {
                    'default_entries': int(request.form.get('default_entries', 1000)),
                    'max_entries': int(request.form.get('max_entries', 1000000))
                }
            }
            save_config(new_config)
            flash('Configuration saved successfully!', 'success')
            return redirect(url_for('config'))
        except Exception as e:
            flash(f'Error saving configuration: {str(e)}', 'error')
    
    current_config = load_config()
    return render_template('config.html', config=current_config)

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    """Log generation page"""
    config = load_config()
    
    if request.method == 'POST':
        try:
            num_entries = int(request.form.get('num_entries', config['log_generation']['default_entries']))
            data_type = request.form.get('data_type', 'unstructured_logs')
            generate_csv = request.form.get('generate_csv') == 'on'
            ingest_to_es = request.form.get('ingest_to_es') == 'on'
            create_kibana_objects = request.form.get('create_kibana_objects') == 'on'
            
            if num_entries > config['log_generation']['max_entries']:
                flash(f'Number of entries cannot exceed {config["log_generation"]["max_entries"]}', 'error')
                return render_template('generate.html', config=config, data_generators=DATA_GENERATORS)
            
            if data_type not in DATA_GENERATORS:
                flash('Invalid data type selected', 'error')
                return render_template('generate.html', config=config, data_generators=DATA_GENERATORS)
            
            # Start background task
            operation_id = str(uuid.uuid4())
            thread = threading.Thread(target=run_log_generation, args=(
                operation_id, num_entries, data_type, generate_csv, ingest_to_es, create_kibana_objects, config
            ))
            thread.start()
            
            session['current_operation'] = operation_id
            return redirect(url_for('progress', operation_id=operation_id))
            
        except Exception as e:
            flash(f'Error starting log generation: {str(e)}', 'error')
    
    return render_template('generate.html', config=config, data_generators=DATA_GENERATORS)

@app.route('/progress/<operation_id>')
def progress(operation_id):
    """Progress tracking page"""
    return render_template('progress.html', operation_id=operation_id)

@app.route('/api/status/<operation_id>')
def get_status(operation_id):
    """API endpoint to get operation status"""
    with operation_lock:
        status = operation_status.get(operation_id, {
            'status': 'not_found',
            'message': 'Operation not found',
            'progress': 0
        })
    return jsonify(status)

@app.route('/test-connection', methods=['POST'])
def test_connection():
    """Test Elasticsearch and Kibana connections"""
    config = load_config()
    results = {}
    
    import requests
    
    # Test Elasticsearch
    try:
        es_url = f"{config['elasticsearch']['host']}/_cluster/health"
        response = requests.get(
            es_url,
            auth=(config['elasticsearch']['username'], config['elasticsearch']['password']),
            timeout=10
        )
        if response.status_code == 200:
            results['elasticsearch'] = {'status': 'success', 'message': 'Connection successful'}
        else:
            results['elasticsearch'] = {'status': 'error', 'message': f'HTTP {response.status_code}'}
    except Exception as e:
        results['elasticsearch'] = {'status': 'error', 'message': str(e)}
    
    # Test Kibana
    try:
        kibana_url = f"{config['kibana']['host']}/api/status"
        response = requests.get(
            kibana_url,
            auth=(config['kibana']['username'], config['kibana']['password']),
            timeout=10
        )
        if response.status_code == 200:
            results['kibana'] = {'status': 'success', 'message': 'Connection successful'}
        else:
            results['kibana'] = {'status': 'error', 'message': f'HTTP {response.status_code}'}
    except Exception as e:
        results['kibana'] = {'status': 'error', 'message': str(e)}
    
    return jsonify(results)

def run_log_generation(operation_id, num_entries, data_type, generate_csv, ingest_to_es, create_kibana_objects, config):
    """Background task for log generation"""
    try:
        update_operation_status(operation_id, 'running', 'Starting data generation...', 0)
        
        # Set global configuration for the generate_logs module
        import generate_logs
        generate_logs.ELASTICSEARCH_HOST = config['elasticsearch']['host']
        generate_logs.ELASTICSEARCH_USER = config['elasticsearch']['username']
        generate_logs.ELASTICSEARCH_PASS = config['elasticsearch']['password']
        generate_logs.KIBANA_HOST = config['kibana']['host']
        generate_logs.KIBANA_USER = config['kibana']['username']
        generate_logs.KIBANA_PASS = config['kibana']['password']
        
        # Step 1: Generate data
        update_operation_status(operation_id, 'running', f'Generating {DATA_GENERATORS[data_type]["name"]} data...', 10)
        
        # Initialize the appropriate generator
        generator_class = DATA_GENERATORS[data_type]['generator']
        generator = generator_class()
        
        # Generate data entries
        entries = []
        for i in range(num_entries):
            if i % 1000 == 0:  # Update progress every 1000 entries
                progress = 10 + (i / num_entries) * 20  # 10-30% for generation
                update_operation_status(operation_id, 'running', f'Generated {i}/{num_entries} entries...', progress)
            
            entry = generator.generate_entry()
            entries.append(entry)
        
        update_operation_status(operation_id, 'running', f'Generated {len(entries)} {DATA_GENERATORS[data_type]["name"]} entries', 30)
        
        # Step 2: Write CSV file (if requested)
        if generate_csv:
            update_operation_status(operation_id, 'running', 'Writing CSV file...', 35)
            csv_path = write_csv_file(entries, data_type)
            update_operation_status(operation_id, 'running', f'CSV file written to {csv_path}', 45)
        
        # Step 3: Ingest to Elasticsearch (if requested)
        if ingest_to_es:
            update_operation_status(operation_id, 'running', 'Ingesting data to Elasticsearch...', 50)
            index_name = DATA_GENERATORS[data_type]['index_pattern']
            ingest_data_to_es(entries, index_name, data_type, config)
            update_operation_status(operation_id, 'running', 'Data ingested successfully', 70)
        
        # Step 4: Create Kibana objects (if requested)
        if create_kibana_objects:
            update_operation_status(operation_id, 'running', 'Creating Kibana saved objects...', 80)
            index_name = DATA_GENERATORS[data_type]['index_pattern']
            
            # Try to create Kibana objects, but don't fail if it doesn't work
            try:
                create_kibana_objects_for_data_type(data_type, index_name, config)
                update_operation_status(operation_id, 'running', 'Kibana objects created successfully', 95)
            except Exception as e:
                # Log the error but continue - this is not critical for data generation
                print(f"Kibana objects creation failed (non-critical): {str(e)}")
                update_operation_status(operation_id, 'running', 
                    f'Data generated successfully. Kibana objects import failed - please create manually. Index: {index_name}', 95)
        
        # Provide helpful completion message
        completion_message = 'All operations completed successfully!'
        if create_kibana_objects:
            completion_message += f' Index created: {DATA_GENERATORS[data_type]["index_pattern"]}. If data views are missing, create manually in Kibana.'
        
        update_operation_status(operation_id, 'completed', completion_message, 100)
        
    except Exception as e:
        update_operation_status(operation_id, 'error', f'Error: {str(e)}', None)

def write_csv_file(entries, data_type):
    """Write entries to CSV file"""
    os.makedirs("output_csv", exist_ok=True)
    
    # Get existing CSV files to determine next number
    existing_files = [f for f in os.listdir("output_csv") if f.startswith(f"{data_type}-") and f.endswith(".csv")]
    next_num = len(existing_files) + 1
    
    csv_filename = f"{data_type}-{next_num:03d}.csv"
    csv_path = os.path.join("output_csv", csv_filename)
    
    if entries:
        # Get all possible fieldnames from all entries
        fieldnames = set()
        for entry in entries:
            fieldnames.update(flatten_dict(entry).keys())
        
        fieldnames = sorted(list(fieldnames))
        
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for entry in entries:
                flattened = flatten_dict(entry)
                writer.writerow(flattened)
    
    return csv_path

def flatten_dict(d, parent_key='', sep='.'):
    """Flatten nested dictionaries for CSV output"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # Convert lists to JSON strings for CSV
            items.append((new_key, json.dumps(v)))
        else:
            items.append((new_key, v))
    return dict(items)

def ingest_data_to_es(entries, index_name, data_type, config):
    """Ingest data entries into Elasticsearch"""
    import requests
    
    es_host = config['elasticsearch']['host']
    es_user = config['elasticsearch']['username']
    es_pass = config['elasticsearch']['password']
    
    index_url = f"{es_host}/{index_name}"
    
    # Create index with appropriate mapping
    mapping = get_mapping_for_data_type(data_type)
    resp = requests.put(
        index_url,
        auth=(es_user, es_pass),
        headers={"Content-Type": "application/json"},
        json={
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            },
            "mappings": mapping
        }
    )
    
    if resp.status_code not in (200, 400):
        raise Exception(f"Index creation error: {resp.text}")
    
    # Bulk ingest data
    bulk_data = []
    for entry in entries:
        bulk_data.append(json.dumps({"index": {}}))
        bulk_data.append(json.dumps(entry))
    
    bulk_body = "\n".join(bulk_data) + "\n"
    
    resp2 = requests.post(
        f"{index_url}/_bulk",
        auth=(es_user, es_pass),
        headers={"Content-Type": "application/x-ndjson"},
        data=bulk_body
    )
    
    if resp2.status_code != 200:
        raise Exception(f"Bulk ingest error: {resp2.text}")

def get_mapping_for_data_type(data_type):
    """Get appropriate Elasticsearch mapping for data type"""
    mappings = {
        "unstructured_logs": {
            "properties": {
                "@timestamp": {"type": "date"},
                "log.level": {"type": "keyword"},
                "source": {"type": "keyword"},
                "message": {"type": "text"}
            }
        },
        "structured_logs": {
            "properties": {
                "@timestamp": {"type": "date"},
                "service.name": {"type": "keyword"},
                "service.version": {"type": "keyword"},
                "log.level": {"type": "keyword"},
                "environment": {"type": "keyword"},
                "host.name": {"type": "keyword"},
                "trace.id": {"type": "keyword"},
                "span.id": {"type": "keyword"},
                "user.id": {"type": "keyword"},
                "http.method": {"type": "keyword"},
                "http.status_code": {"type": "integer"},
                "http.response_time_ms": {"type": "integer"},
                "message": {"type": "text"}
            }
        },
        "distributed_traces": {
            "properties": {
                "@timestamp": {"type": "date"},
                "trace.id": {"type": "keyword"},
                "span.id": {"type": "keyword"},
                "span.parent_id": {"type": "keyword"},
                "span.name": {"type": "keyword"},
                "service.name": {"type": "keyword"},
                "operation.name": {"type": "keyword"},
                "span.kind": {"type": "keyword"},
                "span.status": {"type": "keyword"},
                "duration.ms": {"type": "integer"},
                "span.start_time": {"type": "date"},
                "span.end_time": {"type": "date"}
            }
        },
        "metrics": {
            "properties": {
                "@timestamp": {"type": "date"},
                "metric.type": {"type": "keyword"},
                "metric.name": {"type": "keyword"},
                "metric.value": {"type": "double"},
                "service.name": {"type": "keyword"},
                "host.name": {"type": "keyword"},
                "environment": {"type": "keyword"}
            }
        },
        "security_events": {
            "properties": {
                "@timestamp": {"type": "date"},
                "event.type": {"type": "keyword"},
                "event.id": {"type": "keyword"},
                "event.severity": {"type": "keyword"},
                "event.action": {"type": "keyword"},
                "event.outcome": {"type": "keyword"},
                "source.ip": {"type": "ip"},
                "destination.ip": {"type": "ip"},
                "user.name": {"type": "keyword"},
                "host.name": {"type": "keyword"}
            }
        },
        "alerts": {
            "properties": {
                "@timestamp": {"type": "date"},
                "alert.name": {"type": "keyword"},
                "alert.state": {"type": "keyword"},
                "alert.severity": {"type": "keyword"},
                "alert.id": {"type": "keyword"},
                "alert.started_at": {"type": "date"},
                "alert.resolved_at": {"type": "date"},
                "metric.value": {"type": "double"},
                "metric.threshold": {"type": "double"}
            }
        },
        "network_traffic": {
            "properties": {
                "@timestamp": {"type": "date"},
                "flow.id": {"type": "keyword"},
                "network.protocol": {"type": "keyword"},
                "source.ip": {"type": "ip"},
                "destination.ip": {"type": "ip"},
                "source.port": {"type": "integer"},
                "destination.port": {"type": "integer"},
                "network.bytes": {"type": "long"},
                "network.packets": {"type": "integer"},
                "network.direction": {"type": "keyword"},
                "event.action": {"type": "keyword"}
            }
        },
        "apm_data": {
            "properties": {
                "@timestamp": {"type": "date"},
                "transaction.id": {"type": "keyword"},
                "transaction.type": {"type": "keyword"},
                "transaction.name": {"type": "keyword"},
                "service.name": {"type": "keyword"},
                "service.version": {"type": "keyword"},
                "transaction.duration.ms": {"type": "integer"},
                "transaction.result": {"type": "keyword"},
                "user.id": {"type": "keyword"},
                "trace.id": {"type": "keyword"},
                "span.id": {"type": "keyword"},
                "http.method": {"type": "keyword"},
                "http.status_code": {"type": "integer"},
                "error.type": {"type": "keyword"},
                "error.message": {"type": "text"}
            }
        }
    }
    
    return mappings.get(data_type, {"properties": {"@timestamp": {"type": "date"}}})

def create_kibana_objects_for_data_type(data_type, index_name, config):
    """Create Kibana saved objects for the specified data type"""
    try:
        # Create data view
        data_view_so = create_data_view_so_7_11()
        data_view_so['attributes']['title'] = index_name
        data_view_so['id'] = index_name
        
        # Create basic discover session
        discover_sos = [{
            "id": f"{data_type}_basic_view",
            "type": "search", 
            "attributes": {
                "title": f"{DATA_GENERATORS[data_type]['name']} - Basic View",
                "description": f"Basic view of {DATA_GENERATORS[data_type]['name']} data",
                "hits": 0,
                "columns": ["@timestamp"],
                "sort": [],
                "kibanaSavedObjectMeta": {
                    "searchSourceJSON": json.dumps({
                        "query": {"query": "", "language": "kuery"},
                        "filter": [],
                        "index": index_name
                    })
                }
            },
            "references": [{
                "name": "kibanaSavedObjectMeta.searchSourceJSON.index",
                "type": "index-pattern", 
                "id": index_name
            }],
            "namespaces": ["default"],
            "coreMigrationVersion": "8.0.0",
            "typeMigrationVersion": "8.0.0"
        }]
        
        # Use the improved import function
        import_kibana_objects_improved([data_view_so] + discover_sos, config)
        
    except Exception as e:
        print(f"Error creating Kibana objects: {str(e)}")

def import_kibana_objects_improved(objects, config):
    """Improved Kibana objects import with better error handling"""
    import tempfile
    
    # Create temporary NDJSON file
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.ndjson', delete=False) as f:
        for obj in objects:
            f.write(json.dumps(obj) + '\n')
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            files = {
                "file": ("saved_objects.ndjson", f, "application/ndjson")
            }
            headers = {
                "kbn-xsrf": "true",
                "kbn-version": "8.0.0"
            }
            
            resp = requests.post(
                f"{config['kibana']['host']}/api/saved_objects/_import?overwrite=true",
                auth=(config['kibana']['username'], config['kibana']['password']),
                headers=headers,
                files=files
            )
            
        if resp.status_code == 200:
            result = resp.json()
            if result.get("success", False):
                print(f"Successfully imported {result.get('successCount', 0)} Kibana objects")
            else:
                print(f"Import completed with issues: {result}")
        else:
            print(f"Kibana import error: {resp.status_code} -> {resp.text}")
            # Retry without version header
            print("Retrying without version header...")
            
            with open(temp_path, 'rb') as f:
                files = {
                    "file": ("saved_objects.ndjson", f, "application/ndjson")
                }
                headers = {"kbn-xsrf": "true"}
                
                resp2 = requests.post(
                    f"{config['kibana']['host']}/api/saved_objects/_import?overwrite=true",
                    auth=(config['kibana']['username'], config['kibana']['password']),
                    headers=headers,
                    files=files
                )
                
            if resp2.status_code == 200:
                result = resp2.json()
                print(f"Retry successful: imported {result.get('successCount', 0)} objects")
            else:
                print(f"Retry failed: {resp2.status_code} -> {resp2.text}")
                
    except Exception as e:
        print(f"Exception during Kibana import: {str(e)}")
    finally:
        # Clean up temp file
        import os
        try:
            os.unlink(temp_path)
        except:
            pass

if __name__ == '__main__':
    # Create templates and static directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=8080)
