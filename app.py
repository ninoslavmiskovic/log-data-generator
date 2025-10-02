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

# Import the log generation functions
from generate_logs import (
    generate_logs, ingest_logs_to_es, create_data_view_so_7_11,
    generate_discover_sessions_7_11, write_and_import_so
)

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
            generate_csv = request.form.get('generate_csv') == 'on'
            ingest_to_es = request.form.get('ingest_to_es') == 'on'
            create_kibana_objects = request.form.get('create_kibana_objects') == 'on'
            
            if num_entries > config['log_generation']['max_entries']:
                flash(f'Number of entries cannot exceed {config["log_generation"]["max_entries"]}', 'error')
                return render_template('generate.html', config=config)
            
            # Start background task
            operation_id = str(uuid.uuid4())
            thread = threading.Thread(target=run_log_generation, args=(
                operation_id, num_entries, generate_csv, ingest_to_es, create_kibana_objects, config
            ))
            thread.start()
            
            session['current_operation'] = operation_id
            return redirect(url_for('progress', operation_id=operation_id))
            
        except Exception as e:
            flash(f'Error starting log generation: {str(e)}', 'error')
    
    return render_template('generate.html', config=config)

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

def run_log_generation(operation_id, num_entries, generate_csv, ingest_to_es, create_kibana_objects, config):
    """Background task for log generation"""
    try:
        update_operation_status(operation_id, 'running', 'Starting log generation...', 0)
        
        # Set global configuration for the generate_logs module
        import generate_logs
        generate_logs.ELASTICSEARCH_HOST = config['elasticsearch']['host']
        generate_logs.ELASTICSEARCH_USER = config['elasticsearch']['username']
        generate_logs.ELASTICSEARCH_PASS = config['elasticsearch']['password']
        generate_logs.KIBANA_HOST = config['kibana']['host']
        generate_logs.KIBANA_USER = config['kibana']['username']
        generate_logs.KIBANA_PASS = config['kibana']['password']
        
        # Step 1: Generate logs
        update_operation_status(operation_id, 'running', 'Generating log data...', 10)
        docs = generate_logs.generate_logs(num_entries)
        
        update_operation_status(operation_id, 'running', f'Generated {len(docs)} log entries', 30)
        
        # Step 2: Ingest to Elasticsearch (if requested)
        if ingest_to_es:
            update_operation_status(operation_id, 'running', 'Ingesting logs to Elasticsearch...', 50)
            generate_logs.ingest_logs_to_es(docs)
            update_operation_status(operation_id, 'running', 'Logs ingested successfully', 70)
        
        # Step 3: Create Kibana objects (if requested)
        if create_kibana_objects:
            update_operation_status(operation_id, 'running', 'Creating Kibana saved objects...', 80)
            data_view_so = generate_logs.create_data_view_so_7_11()
            discover_sos = generate_logs.generate_discover_sessions_7_11()
            generate_logs.write_and_import_so(data_view_so, discover_sos)
            update_operation_status(operation_id, 'running', 'Kibana objects created successfully', 95)
        
        update_operation_status(operation_id, 'completed', 'All operations completed successfully!', 100)
        
    except Exception as e:
        update_operation_status(operation_id, 'error', f'Error: {str(e)}', None)

if __name__ == '__main__':
    # Create templates and static directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=8080)
