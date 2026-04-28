import json
import os
import csv
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_session import Session
import tempfile
import threading
import uuid
import requests
# Import the log generation functions and data generators
from generate_logs import create_data_view_so_7_11, generate_discover_sessions_for_type
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
    """Load config from file then overlay environment variables (highest priority)."""
    cfg = {s: dict(v) for s, v in DEFAULT_CONFIG.items()}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                file_cfg = json.load(f)
            for section in ('elasticsearch', 'kibana', 'log_generation'):
                if section in file_cfg:
                    cfg[section].update(file_cfg[section])
        except (json.JSONDecodeError, OSError):
            pass
    env_map = {
        ('elasticsearch', 'host'):     'ES_HOST',
        ('elasticsearch', 'username'): 'ES_USERNAME',
        ('elasticsearch', 'password'): 'ES_PASSWORD',
        ('kibana',        'host'):     'KIBANA_HOST',
        ('kibana',        'username'): 'KIBANA_USERNAME',
        ('kibana',        'password'): 'KIBANA_PASSWORD',
    }
    for (section, key), env_var in env_map.items():
        val = os.environ.get(env_var)
        if val:
            cfg[section][key] = val
    return cfg

def get_env_overrides():
    """Return set of (section, key) pairs currently controlled by env vars."""
    env_map = {
        ('elasticsearch', 'host'):     'ES_HOST',
        ('elasticsearch', 'username'): 'ES_USERNAME',
        ('elasticsearch', 'password'): 'ES_PASSWORD',
        ('kibana',        'host'):     'KIBANA_HOST',
        ('kibana',        'username'): 'KIBANA_USERNAME',
        ('kibana',        'password'): 'KIBANA_PASSWORD',
    }
    return {k for k, env_var in env_map.items() if os.environ.get(env_var)}

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
            existing = load_config()
            es_pw = request.form.get('es_password', '').strip()
            kb_pw = request.form.get('kibana_password', '').strip()
            new_config = {
                'elasticsearch': {
                    'host': request.form.get('es_host', '').strip(),
                    'username': request.form.get('es_username', '').strip(),
                    'password': es_pw if es_pw else existing['elasticsearch']['password']
                },
                'kibana': {
                    'host': request.form.get('kibana_host', '').strip(),
                    'username': request.form.get('kibana_username', '').strip(),
                    'password': kb_pw if kb_pw else existing['kibana']['password']
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
    env_overrides = get_env_overrides()
    return render_template('config.html', config=current_config, env_overrides=env_overrides)

def validate_es_connection(config):
    """Return (True, '') or (False, error_message)."""
    try:
        resp = requests.get(
            f"{config['elasticsearch']['host']}/_cluster/health",
            auth=(config['elasticsearch']['username'], config['elasticsearch']['password']),
            timeout=5
        )
        if resp.status_code == 200:
            return True, ''
        return False, f"Elasticsearch returned HTTP {resp.status_code}"
    except requests.exceptions.ConnectionError:
        return False, f"Cannot connect to {config['elasticsearch']['host']}"
    except requests.exceptions.Timeout:
        return False, "Connection timed out after 5 seconds"
    except Exception as e:
        return False, str(e)

def _resolve_date_range(form):
    """Parse date_range form fields into (start_date, end_date) datetimes."""
    now = datetime.now()
    preset = form.get('date_range', 'last_year')
    presets = {
        '24h':      datetime.timedelta(hours=24),
        '7d':       datetime.timedelta(days=7),
        '30d':      datetime.timedelta(days=30),
        '90d':      datetime.timedelta(days=90),
        'last_year': datetime.timedelta(days=365),
    }
    if preset == 'custom':
        try:
            from datetime import date as _date
            start = datetime.fromisoformat(form.get('date_from', ''))
            end   = datetime.fromisoformat(form.get('date_to', ''))
            if start >= end:
                raise ValueError("date_from must be before date_to")
            return start, end
        except (ValueError, TypeError):
            pass  # fall back to last year
    delta = presets.get(preset, datetime.timedelta(days=365))
    return now - delta, now

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    """Log generation page"""
    config = load_config()

    if request.method == 'POST':
        try:
            try:
                num_entries = int(request.form.get('num_entries', config['log_generation']['default_entries']))
            except (ValueError, TypeError):
                flash('Number of entries must be a valid integer', 'error')
                return render_template('generate.html', config=config, data_generators=DATA_GENERATORS)

            data_type = request.form.get('data_type', 'unstructured_logs')
            generate_csv = request.form.get('generate_csv') == 'on'
            ingest_to_es = request.form.get('ingest_to_es') == 'on'
            create_kibana_objects = request.form.get('create_kibana_objects') == 'on'

            if num_entries <= 0:
                flash('Number of entries must be greater than 0', 'error')
                return render_template('generate.html', config=config, data_generators=DATA_GENERATORS)

            if num_entries > config['log_generation']['max_entries']:
                flash(f'Number of entries cannot exceed {config["log_generation"]["max_entries"]}', 'error')
                return render_template('generate.html', config=config, data_generators=DATA_GENERATORS)

            if data_type != 'all' and data_type not in DATA_GENERATORS:
                flash('Invalid data type selected', 'error')
                return render_template('generate.html', config=config, data_generators=DATA_GENERATORS)

            if ingest_to_es or create_kibana_objects:
                ok, err = validate_es_connection(config)
                if not ok:
                    flash(f'Cannot reach Elasticsearch: {err}. Check Settings before generating.', 'error')
                    return render_template('generate.html', config=config, data_generators=DATA_GENERATORS)

            start_date, end_date = _resolve_date_range(request.form)
            operation_id = str(uuid.uuid4())

            if data_type == 'all':
                thread = threading.Thread(target=run_all_generation, args=(
                    operation_id, num_entries, generate_csv, ingest_to_es,
                    create_kibana_objects, config, start_date, end_date
                ))
            else:
                thread = threading.Thread(target=run_log_generation, args=(
                    operation_id, num_entries, data_type, generate_csv,
                    ingest_to_es, create_kibana_objects, config, start_date, end_date
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

def _generate_entries(data_type, num_entries, operation_id, start_date, end_date, progress_base=10, progress_range=20):
    """Generate entries for one data type and return them."""
    generator_class = DATA_GENERATORS[data_type]['generator']
    generator = generator_class(start_date=start_date, end_date=end_date)
    entries = []
    for i in range(num_entries):
        if i % 1000 == 0:
            pct = progress_base + (i / num_entries) * progress_range
            update_operation_status(operation_id, 'running', f'Generated {i}/{num_entries} entries...', pct)
        entries.append(generator.generate_entry())
    return entries

def run_log_generation(operation_id, num_entries, data_type, generate_csv,
                       ingest_to_es, create_kibana_objects, config,
                       start_date=None, end_date=None):
    """Background task for single data-type generation."""
    try:
        update_operation_status(operation_id, 'running', 'Starting data generation...', 0)

        if start_date is None:
            from datetime import timedelta
            start_date = datetime.now() - timedelta(days=365)
        if end_date is None:
            end_date = datetime.now()

        update_operation_status(operation_id, 'running', f'Generating {DATA_GENERATORS[data_type]["name"]} data...', 10)
        entries = _generate_entries(data_type, num_entries, operation_id, start_date, end_date)
        update_operation_status(operation_id, 'running', f'Generated {len(entries)} entries', 30)

        if generate_csv:
            update_operation_status(operation_id, 'running', 'Writing CSV file...', 35)
            csv_path = write_csv_file(entries, data_type)
            update_operation_status(operation_id, 'running', f'CSV written to {csv_path}', 45)

        if ingest_to_es:
            update_operation_status(operation_id, 'running', 'Ingesting data to Elasticsearch...', 50)
            index_name = DATA_GENERATORS[data_type]['index_pattern']
            ingest_data_to_es(entries, index_name, data_type, config)
            update_operation_status(operation_id, 'running', 'Data ingested successfully', 70)

        if create_kibana_objects:
            update_operation_status(operation_id, 'running', 'Creating Kibana objects...', 80)
            index_name = DATA_GENERATORS[data_type]['index_pattern']
            try:
                create_kibana_objects_for_data_type(data_type, index_name, config)
                update_operation_status(operation_id, 'running', 'Kibana objects created', 95)
            except Exception as e:
                print(f"Kibana objects creation failed (non-critical): {e}")
                update_operation_status(operation_id, 'running',
                    f'Kibana objects failed ({e}). Data is in index: {index_name}', 95)

        update_operation_status(operation_id, 'completed', 'All operations completed successfully!', 100)

    except Exception as e:
        update_operation_status(operation_id, 'error', f'Error: {str(e)}', None)

def run_all_generation(operation_id, num_entries, generate_csv, ingest_to_es,
                       create_kibana_objects, config, start_date=None, end_date=None):
    """Background task: generate all 8 data types sequentially."""
    if start_date is None:
        from datetime import timedelta
        start_date = datetime.now() - timedelta(days=365)
    if end_date is None:
        end_date = datetime.now()

    types = list(DATA_GENERATORS.keys())
    failed = []

    update_operation_status(operation_id, 'running', f'Starting generation for all {len(types)} data types...', 0)

    for idx, data_type in enumerate(types):
        base_pct = int((idx / len(types)) * 100)
        name = DATA_GENERATORS[data_type]['name']
        update_operation_status(operation_id, 'running',
            f'[{idx + 1}/{len(types)}] Generating {name}...', base_pct)
        try:
            entries = _generate_entries(data_type, num_entries, operation_id,
                                        start_date, end_date,
                                        progress_base=base_pct, progress_range=4)
            if generate_csv:
                write_csv_file(entries, data_type)
            if ingest_to_es:
                ingest_data_to_es(entries, DATA_GENERATORS[data_type]['index_pattern'], data_type, config)
            if create_kibana_objects:
                create_kibana_objects_for_data_type(data_type, DATA_GENERATORS[data_type]['index_pattern'], config)
        except Exception as e:
            failed.append(f"{name}: {e}")
            print(f"run_all_generation: {data_type} failed: {e}")

    if failed:
        msg = f'Completed with errors on {len(failed)} type(s): ' + '; '.join(failed)
        update_operation_status(operation_id, 'completed', msg, 100)
    else:
        update_operation_status(operation_id, 'completed',
            f'All {len(types)} data types generated successfully!', 100)

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
        raise Exception(f"Bulk ingest HTTP error: {resp2.text[:500]}")

    bulk_result = resp2.json()
    if bulk_result.get("errors"):
        failed_items = [item for item in bulk_result.get("items", [])
                        if item.get("index", {}).get("error")]
        sample = failed_items[0]["index"]["error"] if failed_items else {}
        raise Exception(
            f"Bulk ingest: {len(failed_items)}/{len(entries)} documents failed. "
            f"Error: {sample.get('type')}: {sample.get('reason', '')[:200]}"
        )

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
    """Create Kibana data view + Discover sessions for the given data type."""
    data_view_so = create_data_view_so_7_11()
    data_view_so['attributes']['title'] = index_name
    data_view_so['id'] = index_name
    discover_sos = generate_discover_sessions_for_type(data_type, index_name)
    import_kibana_objects_improved([data_view_so] + discover_sos, config)

def import_kibana_objects_improved(objects, config):
    """Import Kibana saved objects via the bulk import API."""
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.ndjson', delete=False) as f:
        for obj in objects:
            f.write(json.dumps(obj) + '\n')
        temp_path = f.name

    try:
        with open(temp_path, 'rb') as f:
            resp = requests.post(
                f"{config['kibana']['host']}/api/saved_objects/_import?overwrite=true",
                auth=(config['kibana']['username'], config['kibana']['password']),
                headers={"kbn-xsrf": "true"},
                files={"file": ("saved_objects.ndjson", f, "application/ndjson")},
            )

        if resp.status_code == 200:
            result = resp.json()
            if result.get("success", False):
                print(f"Successfully imported {result.get('successCount', 0)} Kibana objects")
            else:
                print(f"Import completed with issues: {result}")
        else:
            print(f"Kibana import error: {resp.status_code} -> {resp.text}")
    except Exception as e:
        print(f"Exception during Kibana import: {str(e)}")
    finally:
        try:
            os.unlink(temp_path)
        except OSError:
            pass

@app.route('/api/cleanup/es', methods=['POST'])
def cleanup_es():
    """Delete all test indices from Elasticsearch."""
    config = load_config()
    results = {}
    for data_type, meta in DATA_GENERATORS.items():
        index = meta['index_pattern']
        try:
            resp = requests.delete(
                f"{config['elasticsearch']['host']}/{index}",
                auth=(config['elasticsearch']['username'], config['elasticsearch']['password']),
                timeout=10
            )
            results[index] = 'deleted' if resp.status_code in (200, 404) else f"error {resp.status_code}"
        except Exception as e:
            results[index] = f"error: {e}"
    return jsonify({'status': 'done', 'indices': results})

@app.route('/api/cleanup/csv', methods=['POST'])
def cleanup_csv():
    """Delete all CSV files from output_csv/."""
    deleted, errors = [], []
    csv_dir = 'output_csv'
    if os.path.exists(csv_dir):
        for fname in os.listdir(csv_dir):
            if fname.endswith('.csv'):
                try:
                    os.remove(os.path.join(csv_dir, fname))
                    deleted.append(fname)
                except OSError as e:
                    errors.append(str(e))
    return jsonify({'deleted': deleted, 'errors': errors})

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=8080)
