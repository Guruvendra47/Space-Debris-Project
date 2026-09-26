import os
import json
import time
from functools import wraps
from flask import Flask, send_from_directory, request, Response, jsonify, stream_with_context

app = Flask(__name__, static_folder='.')

# --- In-Memory Data Cache (pre-loaded on startup) ---
_data_cache = {}

def _load_data(name, filename):
    if name not in _data_cache:
        try:
            with open(filename, 'r') as f:
                _data_cache[name] = json.load(f)
        except Exception:
            _data_cache[name] = None
    return _data_cache[name]

# --- Simple Rate Limiting (per IP, in-memory) ---
_request_counts = {}

def rate_limit(max_per_minute=60):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            ip = request.remote_addr or 'unknown'
            now = time.time()
            if ip not in _request_counts:
                _request_counts[ip] = []
            _request_counts[ip] = [t for t in _request_counts[ip] if now - t < 60]
            if len(_request_counts[ip]) >= max_per_minute:
                return jsonify({'error': 'Rate limit exceeded', 'retry_after': 60}), 429
            _request_counts[ip].append(now)
            return f(*args, **kwargs)
        return wrapper
    return decorator

# --- Static file routes (existing, unchanged) ---
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory('.', filename)

# --- API Endpoints with Cache-Control Headers ---

@app.route('/api/orbital-data')
@rate_limit(max_per_minute=30)
def api_orbital_data():
    data = _load_data('orbital', 'orbital_data.json')
    if data is None:
        return jsonify({'error': 'Data unavailable'}), 503
    resp = jsonify(data)
    resp.headers['Cache-Control'] = 'public, max-age=300'
    resp.headers['X-Data-Source'] = 'server-cache'
    return resp

@app.route('/api/catalog')
@rate_limit(max_per_minute=30)
def api_catalog():
    data = _load_data('catalog', 'satcat_catalog.json')
    if data is None:
        return jsonify({'error': 'Data unavailable'}), 503
    resp = jsonify(data)
    resp.headers['Cache-Control'] = 'public, max-age=300'
    resp.headers['X-Data-Source'] = 'server-cache'
    return resp

@app.route('/api/predictions')
@rate_limit(max_per_minute=30)
def api_predictions():
    data = _load_data('predictions', 'ml_predictions.json')
    if data is None:
        return jsonify({'error': 'Data unavailable'}), 503
    resp = jsonify(data)
    resp.headers['Cache-Control'] = 'public, max-age=300'
    resp.headers['X-Data-Source'] = 'server-cache'
    return resp

@app.route('/api/collision')
@rate_limit(max_per_minute=30)
def api_collision():
    data = _load_data('collision', 'collision_risk.json')
    if data is None:
        return jsonify({'error': 'Data unavailable'}), 503
    resp = jsonify(data)
    resp.headers['Cache-Control'] = 'public, max-age=300'
    resp.headers['X-Data-Source'] = 'server-cache'
    return resp

@app.route('/api/health')
def api_health():
    return jsonify({
        'status': 'ok',
        'timestamp': time.time(),
        'data_loaded': {k: v is not None for k, v in _data_cache.items()}
    })

# --- Server-Sent Events for Live Push ---
@app.route('/api/stream')
def api_stream():
    def event_stream():
        while True:
            data = {
                'type': 'heartbeat',
                'timestamp': time.time(),
                'message': 'sync-check'
            }
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(30)
    return Response(
        stream_with_context(event_stream()),
        content_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )

if __name__ == '__main__':
    # Pre-load data into memory cache on startup
    print('Pre-loading data cache...')
    _load_data('orbital', 'orbital_data.json')
    _load_data('catalog', 'satcat_catalog.json')
    _load_data('predictions', 'ml_predictions.json')
    _load_data('collision', 'collision_risk.json')
    print('Data cache ready.')
    app.run(host='0.0.0.0', port=os.environ.get('DATABRICKS_APP_PORT', 8000), threaded=True)