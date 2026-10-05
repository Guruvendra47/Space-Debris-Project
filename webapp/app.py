import os
import json
import time
import math
import logging
import threading
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Flask, send_from_directory, request, Response, jsonify, stream_with_context

try:
    from flask_compress import Compress
except ImportError:
    Compress = None

app = Flask(__name__, static_folder='.')
app.config['COMPRESS_MIME_TYPES'] = [
    'text/html', 'text/css', 'text/plain', 'application/json',
    'application/javascript', 'application/xml', 'image/svg+xml'
]
app.config['COMPRESS_LEVEL'] = 6
if Compress:
    Compress(app)

# --- Request Logging (item 11) ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('space-debris-tracker')

_app_start_time = time.time()

@app.before_request
def log_request_start():
    request._start_time = time.time()
    logger.info(f'{request.method} {request.path} from {request.remote_addr}')

@app.after_request
def log_request_end(response):
    elapsed = getattr(request, '_start_time', time.time())
    duration_ms = round((time.time() - elapsed) * 1000, 1)
    logger.info(f'{request.method} {request.path} -> {response.status_code} ({duration_ms}ms)')
    return response

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

# --- Rate Limiting (per IP, in-memory, burst-tolerant, thread-safe) (item 4) ---
_request_counts = {}
_rate_limit_lock = threading.Lock()

def rate_limit(max_per_minute=120, burst_size=None):
    burst = burst_size or max_per_minute
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            ip = request.remote_addr or 'unknown'
            now = time.time()
            with _rate_limit_lock:
                if ip not in _request_counts:
                    _request_counts[ip] = []
                _request_counts[ip] = [t for t in _request_counts[ip] if now - t < 60]
                if len(_request_counts[ip]) >= burst:
                    return jsonify({'error': 'Rate limit exceeded', 'retry_after': 60}), 429
                _request_counts[ip].append(now)
                if len(_request_counts) > 50000:
                    stale = [k for k, v in _request_counts.items() if not v or now - v[-1] > 120]
                    for k in stale:
                        del _request_counts[k]
            return f(*args, **kwargs)
        return wrapper
    return decorator

# --- Static file routes with long cache headers (item 5) ---
_STATIC_CACHE_TYPES = {'.js', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.woff', '.woff2', '.css'}

@app.route('/')
def index():
    resp = send_from_directory('.', 'index.html')
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return resp

@app.route('/<path:filename>')
def serve_file(filename):
    resp = send_from_directory('.', filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext in _STATIC_CACHE_TYPES:
        resp.headers['Cache-Control'] = 'public, max-age=300'
    return resp

# --- API Endpoints with Cache-Control Headers ---

@app.route('/api/orbital-data')
@rate_limit(max_per_minute=120)
def api_orbital_data():
    data = _load_data('orbital', 'orbital_data.json')
    if data is None:
        return jsonify({'error': 'Data unavailable'}), 503
    resp = jsonify(data)
    resp.headers['Cache-Control'] = 'public, max-age=300'
    resp.headers['X-Data-Source'] = 'server-cache'
    return resp

@app.route('/api/catalog')
@rate_limit(max_per_minute=120)
def api_catalog():
    data = _load_data('catalog', 'satcat_catalog.json')
    if data is None:
        return jsonify({'error': 'Data unavailable'}), 503
    resp = jsonify(data)
    resp.headers['Cache-Control'] = 'public, max-age=300'
    resp.headers['X-Data-Source'] = 'server-cache'
    return resp

# --- Full SATCAT Export (fetches all 70K from Celestrak, cached 24h) ---
_satcat_full_cache = {'data': None, 'ts': 0}

def _fetch_full_satcat():
    """Fetch full SATCAT from Celestrak, cache for 24 hours."""
    now = time.time()
    if _satcat_full_cache['data'] and (now - _satcat_full_cache['ts']) < 86400:
        return _satcat_full_cache['data']
    try:
        url = 'https://celestrak.org/satcat/records.php?format=json'
        req = urllib.request.Request(url, headers={'User-Agent': 'OrbitalIntelligence/1.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = json.loads(resp.read().decode('utf-8'))
        _satcat_full_cache['data'] = raw
        _satcat_full_cache['ts'] = now
        logger.info(f'Fetched full SATCAT: {len(raw)} records')
        return raw
    except Exception as e:
        logger.warning(f'Celestrak SATCAT fetch error: {e}')
        # Fallback to local 1000-record file
        local = _load_data('catalog', 'satcat_catalog.json')
        return local or []

@app.route('/api/export')
@rate_limit(max_per_minute=30)
def api_export():
    """Export full SATCAT as CSV/JSON/TLE with server-side filtering."""
    fmt = request.args.get('format', 'csv').lower()
    obj_type = request.args.get('type', 'all')
    status = request.args.get('status', 'all')
    regime = request.args.get('regime', 'all')
    search = request.args.get('search', '').lower()
    
    records = _fetch_full_satcat()
    
    # Apply filters
    filtered = []
    for o in records:
        # Type filter
        if obj_type != 'all' and o.get('OBJECT_TYPE', o.get('ObjectType', '')) != obj_type:
            continue
        # Status filter
        is_decayed = o.get('DECAYED', o.get('IsDecayed', 0))
        if isinstance(is_decayed, str):
            is_decayed = 1 if is_decayed.lower() in ('1','true','yes') else 0
        if status == 'active' and is_decayed:
            continue
        if status == 'decayed' and not is_decayed:
            continue
        # Regime filter
        if regime != 'all':
            apo = o.get('APOGEE', o.get('Apogee', 0)) or 0
            per = o.get('PERIGEE', o.get('Perigee', 0)) or 0
            avg_alt = (apo + per) / 2
            if regime == 'leo' and avg_alt > 2000:
                continue
            elif regime == 'meo' and (avg_alt < 2000 or avg_alt > 35000):
                continue
            elif regime == 'geo' and not (34000 <= avg_alt <= 37000):
                continue
            elif regime == 'heo' and avg_alt < 37000:
                continue
        # Search filter
        if search:
            name = (o.get('OBJECT_NAME', o.get('ObjectName', '')) or '').lower()
            norad = str(o.get('NORAD_CAT_ID', o.get('CatalogID', '')) or '').lower()
            owner = (o.get('OWNER', o.get('Owner', '')) or '').lower()
            if search not in name and search not in norad and search not in owner:
                continue
        filtered.append(o)
    
    if fmt == 'json':
        def generate_json():
            yield '['
            for i, o in enumerate(filtered):
                row = {
                    'NORAD_ID': o.get('NORAD_CAT_ID', o.get('CatalogID', '')),
                    'ObjectName': o.get('OBJECT_NAME', o.get('ObjectName', '')),
                    'ObjectType': o.get('OBJECT_TYPE', o.get('ObjectType', '')),
                    'Owner': o.get('OWNER', o.get('Owner', '')),
                    'OrbitClass': o.get('ORBIT_CLASS', o.get('OrbitClass', '')),
                    'Inclination': o.get('INCLINATION', o.get('Inclination', 0)),
                    'Apogee': o.get('APOGEE', o.get('Apogee', 0)),
                    'Perigee': o.get('PERIGEE', o.get('Perigee', 0)),
                    'LaunchDate': o.get('LAUNCH_DATE', o.get('LaunchDate', '')),
                    'RadarSize': o.get('RADAR_SIZE', o.get('RadarSize', '')),
                    'Status': 'Decayed' if o.get('DECAYED', o.get('IsDecayed', 0)) else 'Active'
                }
                yield json.dumps(row)
                if i < len(filtered) - 1:
                    yield ', '
            yield ']'
        resp = Response(stream_with_context(generate_json()), mimetype='application/json')
        resp.headers['Content-Disposition'] = f'attachment; filename=catalog_{len(filtered)}_records.json'
        return resp
    
    elif fmt == 'tle':
        def generate_tle():
            for o in filtered:
                name = o.get('OBJECT_NAME', o.get('ObjectName', 'UNKNOWN'))
                tle1 = o.get('TLE_LINE1', '')
                tle2 = o.get('TLE_LINE2', '')
                if tle1 and tle2:
                    yield f'{name}\n{tle1}\n{tle2}\n'
        resp = Response(stream_with_context(generate_tle()), mimetype='text/plain')
        resp.headers['Content-Disposition'] = f'attachment; filename=catalog_{len(filtered)}_objects.tle'
        return resp
    
    else:  # CSV
        def generate_csv():
            yield 'NORAD_ID,ObjectName,Type,Owner,OrbitClass,Inclination,Apogee,Perigee,LaunchDate,RadarSize,Status\n'
            for o in filtered:
                row = [
                    str(o.get('NORAD_CAT_ID', o.get('CatalogID', '')) or ''),
                    str(o.get('OBJECT_NAME', o.get('ObjectName', '')) or ''),
                    str(o.get('OBJECT_TYPE', o.get('ObjectType', '')) or ''),
                    str(o.get('OWNER', o.get('Owner', '')) or ''),
                    str(o.get('ORBIT_CLASS', o.get('OrbitClass', '')) or ''),
                    str(o.get('INCLINATION', o.get('Inclination', 0)) or ''),
                    str(o.get('APOGEE', o.get('Apogee', 0)) or ''),
                    str(o.get('PERIGEE', o.get('Perigee', 0)) or ''),
                    str(o.get('LAUNCH_DATE', o.get('LaunchDate', '')) or ''),
                    str(o.get('RADAR_SIZE', o.get('RadarSize', '')) or ''),
                    'Decayed' if o.get('DECAYED', o.get('IsDecayed', 0)) else 'Active'
                ]
                yield '"' + '","'.join(row) + '"\n'
        resp = Response(stream_with_context(generate_csv()), mimetype='text/csv')
        resp.headers['Content-Disposition'] = f'attachment; filename=catalog_{len(filtered)}_records.csv'
        return resp

@app.route('/api/predictions')
@rate_limit(max_per_minute=120)
def api_predictions():
    data = _load_data('predictions', 'ml_predictions.json')
    if data is None:
        return jsonify({'error': 'Data unavailable'}), 503
    resp = jsonify(data)
    resp.headers['Cache-Control'] = 'public, max-age=300'
    resp.headers['X-Data-Source'] = 'server-cache'
    return resp

@app.route('/api/collision')
@rate_limit(max_per_minute=120)
def api_collision():
    data = _load_data('collision', 'collision_risk.json')
    if data is None:
        return jsonify({'error': 'Data unavailable'}), 503
    resp = jsonify(data)
    resp.headers['Cache-Control'] = 'public, max-age=300'
    resp.headers['X-Data-Source'] = 'server-cache'
    return resp

# --- NOAA Space Weather (real-time from SWPC) ---
_space_weather_cache = {'data': None, 'ts': 0}

def _fetch_noaa_kp():
    """Fetch real Kp index from NOAA SWPC."""
    url = 'https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'OrbitalIntelligence/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = json.loads(resp.read().decode('utf-8'))
        if raw and len(raw) > 1:
            recent = raw[-24:]
            current_kp = float(recent[-1][1]) if recent[-1][1] not in ('', None) else 0.0
            kp_history = [float(r[1]) for r in recent if r[1] not in ('', None)]
            return {'current_kp': current_kp, 'history': kp_history, 'readings': recent[-1][0]}
    except Exception as e:
        logger.error(f'NOAA Kp fetch error: {e}')
    return None

def _fetch_noaa_solar_wind():
    """Fetch real-time solar wind data from NOAA SWPC ACE satellite feed."""
    url = 'https://services.swpc.noaa.gov/products/solar-wind/mag-1-day.json'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'OrbitalIntelligence/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = json.loads(resp.read().decode('utf-8'))
        if raw and len(raw) > 1:
            latest = raw[-1]
            return {
                'time': latest[0],
                'bt': float(latest[4]) if len(latest) > 4 and latest[4] not in ('', None) else 0.0,
                'bz': float(latest[3]) if len(latest) > 3 and latest[3] not in ('', None) else 0.0,
            }
    except Exception as e:
        logger.error(f'NOAA solar wind fetch error: {e}')
    return None

def _fetch_noaa_flare_flux():
    """Fetch F10.7 solar flux from NOAA SWPC."""
    url = 'https://services.swpc.noaa.gov/json/f107_cm_flux.json'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'OrbitalIntelligence/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = json.loads(resp.read().decode('utf-8'))
        if raw and len(raw) > 0:
            latest = raw[-1]
            return {'f107': float(latest.get('flux', 0) or 0), 'date': latest.get('date', '')}
    except Exception as e:
        logger.error(f'NOAA F10.7 fetch error: {e}')
    return None

def _fetch_noaa_3day_forecast():
    """Fetch 3-day geomagnetic forecast from NOAA SWPC."""
    url = 'https://services.swpc.noaa.gov/json/3_day_forecast.json'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'OrbitalIntelligence/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = json.loads(resp.read().decode('utf-8'))
        if raw and isinstance(raw, list) and len(raw) > 0:
            return raw[-72:]
    except Exception as e:
        logger.error(f'NOAA 3-day forecast fetch error: {e}')
    return None

def _get_space_weather():
    """Aggregate space weather data with 5-minute cache."""
    now = time.time()
    if _space_weather_cache['data'] and (now - _space_weather_cache['ts']) < 300:
        return _space_weather_cache['data']
    
    try:
        kp_data = _fetch_noaa_kp()
    except Exception as e:
        logger.warning(f'NOAA Kp fetch error: {e}')
        kp_data = None
    try:
        solar_wind = _fetch_noaa_solar_wind()
    except Exception as e:
        logger.warning(f'NOAA solar wind fetch error: {e}')
        solar_wind = None
    try:
        f107_data = _fetch_noaa_flare_flux()
    except Exception as e:
        logger.warning(f'NOAA F10.7 fetch error: {e}')
        f107_data = None
    try:
        forecast_3day = _fetch_noaa_3day_forecast()
    except Exception as e:
        logger.warning(f'NOAA 3-day forecast fetch error: {e}')
        forecast_3day = None
    
    # Fallback: serve stale cache if all external fetches failed (item 6)
    _stale = _space_weather_cache.get('data') or {}
    if not kp_data and not solar_wind and not f107_data and _stale:
        logger.warning('All NOAA fetches failed, serving stale space weather cache')
        return _stale
    
    # Use stale cache value for any individual field that failed, else sensible default
    if kp_data:
        kp = kp_data['current_kp']
    elif 'kp_index' in _stale:
        kp = _stale['kp_index']
        logger.info('Kp fetch failed, using stale cache value: %s', kp)
    else:
        kp = 2.7
    if kp >= 9: g_scale = 'G5 (Extreme)'
    elif kp >= 8: g_scale = 'G4 (Severe)'
    elif kp >= 7: g_scale = 'G3 (Strong)'
    elif kp >= 6: g_scale = 'G2 (Moderate)'
    elif kp >= 5: g_scale = 'G1 (Minor)'
    elif kp >= 4: g_scale = 'Active'
    elif kp >= 2: g_scale = 'Quiet/Unsettled'
    else: g_scale = 'Quiet'
    
    f107 = f107_data['f107'] if f107_data else 142.3
    if f107 > 150 or kp > 5:
        drag_status = 'High - Sun is very active, extra drag on satellites'
        drag_color = '#ef4444'
    elif f107 > 120 or kp > 4:
        drag_status = 'Moderate - Sun slightly active, minor drag effects'
        drag_color = '#f59e0b'
    else:
        drag_status = 'Normal - Stable conditions, minimal drag on satellites'
        drag_color = '#10b981'
    
    data = {
        'kp_index': kp,
        'g_scale': g_scale,
        'kp_history': kp_data['history'] if kp_data else [],
        'kp_timestamp': kp_data['readings'] if kp_data else None,
        'f107_flux': f107,
        'f107_date': f107_data['date'] if f107_data else None,
        'solar_wind_bt': solar_wind['bt'] if solar_wind else 0.0,
        'solar_wind_bz': solar_wind['bz'] if solar_wind else 0.0,
        'solar_wind_time': solar_wind['time'] if solar_wind else None,
        'drag_status': drag_status,
        'drag_color': drag_color,
        'forecast_3day': forecast_3day or [],
        'source': 'NOAA SWPC (Live)' if kp_data else 'Simulated (NOAA unavailable)',
        'timestamp': now,
        'fetched_at': now * 1000
    }
    _space_weather_cache['data'] = data
    _space_weather_cache['ts'] = now
    return data

@app.route('/api/space-weather')
@rate_limit(max_per_minute=120)
def api_space_weather():
    data = _get_space_weather()
    resp = jsonify(data)
    resp.headers['Cache-Control'] = 'public, max-age=300'
    resp.headers['X-Data-Source'] = 'noaa-swpc-live'
    return resp

# --- Launch Library 2 API (The Space Devs) ---
_launch_cache = {'data': None, 'ts': 0}

def _get_launches():
    """Fetch upcoming launches from Launch Library 2 API with 10-minute cache."""
    now = time.time()
    if _launch_cache['data'] and (now - _launch_cache['ts']) < 600:
        return _launch_cache['data']
    
    url = 'https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=20&ordering=net'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'OrbitalIntelligence/1.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = json.loads(resp.read().decode('utf-8'))
        launches = []
        for item in raw.get('results', []):
            launches.append({
                'name': item.get('name', 'Unknown'),
                'mission': item.get('mission', {}).get('name', '') if item.get('mission') else '',
                'rocket': item.get('rocket', {}).get('configuration', {}).get('name', '') if item.get('rocket') else '',
                'launch_provider': item.get('launch_service_provider', {}).get('name', '') if item.get('launch_service_provider') else '',
                'pad': item.get('pad', {}).get('name', '') if item.get('pad') else '',
                'location': item.get('pad', {}).get('location', {}).get('name', '') if item.get('pad') else '',
                'net': item.get('net', ''),
                'window_start': item.get('window_start', ''),
                'window_end': item.get('window_end', ''),
                'status': item.get('status', {}).get('name', '') if item.get('status') else '',
                'image': item.get('image', '') if item.get('image') else '',
                'url': item.get('info_url', '') or item.get('wiki_url', '') or '',
            })
        _launch_cache['data'] = {'launches': launches, 'count': len(launches)}
        _launch_cache['ts'] = now
        return _launch_cache['data']
    except Exception as e:
        logger.error(f'Launch Library fetch error: {e}')
        if _launch_cache['data']:
            logger.warning('Serving stale launch cache')
            return _launch_cache['data']
        return {'launches': [], 'count': 0, 'error': str(e)}

@app.route('/api/launches')
@rate_limit(max_per_minute=120)
def api_launches():
    data = _get_launches()
    resp = jsonify(data)
    resp.headers['Cache-Control'] = 'public, max-age=600'
    resp.headers['X-Data-Source'] = 'launch-library-2'
    return resp

# --- Threat Level (derived from collision data + space weather) ---
@app.route('/api/threat-level')
@rate_limit(max_per_minute=120)
def api_threat_level():
    collision = _load_data('collision', 'collision_risk.json')
    sw = _get_space_weather()
    
    threat_score = 0
    threat_factors = []
    
    if collision:
        rd = collision.get('risk_distribution', {})
        critical = rd.get('Critical', 0)
        high = rd.get('High', 0)
        if critical > 20000:
            threat_score += 60
            threat_factors.append(f'{critical:,} high-risk objects in orbit')
        elif critical > 5000:
            threat_score += 40
            threat_factors.append(f'{critical:,} high-risk objects')
        else:
            threat_score += 20
            threat_factors.append(f'{critical:,} high-risk objects')
        if high > 10:
            threat_score += 15
            threat_factors.append(f'{high} close approaches predicted')
    
    kp = sw.get('kp_index', 0)
    if kp >= 7:
        threat_score += 25
        threat_factors.append(f'Strong magnetic storm (level {kp}/9)')
    elif kp >= 5:
        threat_score += 15
        threat_factors.append(f'Magnetic storm active (level {kp}/9)')
    elif kp >= 4:
        threat_score += 5
        threat_factors.append(f'Increased magnetic activity (level {kp}/9)')
    
    f107 = sw.get('f107_flux', 0)
    if f107 > 180:
        threat_score += 10
        threat_factors.append(f'High sun activity (energy level {f107:.0f})')
    
    if threat_score >= 70:
        level = 'SEVERE'
        color = '#ef4444'
        description = 'High debris density in orbit \u2014 many objects need tracking'
    elif threat_score >= 50:
        level = 'ELEVATED'
        color = '#f59e0b'
        description = 'Above-average debris levels \u2014 extra monitoring in place'
    elif threat_score >= 25:
        level = 'ACTIVE'
        color = '#3b82f6'
        description = 'Normal space traffic \u2014 routine tracking continues'
    else:
        level = 'CALM'
        color = '#10b981'
        description = 'Stable orbital environment \u2014 all clear'
    
    return jsonify({
        'level': level,
        'color': color,
        'score': threat_score,
        'description': description,
        'factors': threat_factors,
        'kp_index': kp,
        'f107_flux': f107,
        'source': 'derived-from-collision-data-and-noaa-swpc'
    })

# --- Satellite Pass Predictions (TLE propagation via skyfield) ---
_skyfield_ts = None

def _get_timescale():
    global _skyfield_ts
    if _skyfield_ts is None:
        try:
            from skyfield.api import load
            _skyfield_ts = load.timescale()
        except Exception:
            pass
    return _skyfield_ts

def _compute_passes_tle(tle_str, observer_lat, observer_lon, observer_alt, hours_ahead=24, min_elevation=10.0):
    """Compute satellite passes over an observer location using skyfield."""
    try:
        from skyfield.api import load, EarthSatellite, wgs84
    except ImportError:
        return None, 'skyfield not installed'
    
    ts = _get_timescale()
    if not ts:
        ts = load.timescale()
        global _skyfield_ts
        _skyfield_ts = ts
    
    # Parse TLE (two lines separated by newline)
    tle_lines = tle_str.strip().split('\n')
    if len(tle_lines) < 2:
        return None, 'Invalid TLE format'
    
    line1 = tle_lines[0].strip()
    line2 = tle_lines[1].strip()
    
    try:
        sat = EarthSatellite(line1, line2, 'SAT', ts)
    except Exception as e:
        return None, f'TLE parse error: {str(e)}'
    
    observer = wgs84.latlon(observer_lat, observer_lon, observer_alt)
    
    now = datetime.now(timezone.utc)
    t0 = ts.utc(now.year, now.month, now.day, now.hour, now.minute, now.second)
    end = now + timedelta(hours=hours_ahead)
    t1 = ts.utc(end.year, end.month, end.day, end.hour, end.minute, end.second)
    
    try:
        t, events = sat.find_events(observer, t0, t1, altitude_degrees=min_elevation)
    except Exception as e:
        return None, f'Pass computation error: {str(e)}'
    
    # Event types: 0=rise, 1=culminate, 2=set
    passes = []
    current_pass = {}
    for ti, event in zip(t, events):
        dt = ti.utc_datetime()
        iso_time = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Compute topocentric position
        difference = sat - observer
        topocentric = difference.at(ti)
        alt_val, az_val, distance = topocentric.altaz()
        
        entry = {
            'time': iso_time,
            'time_display': dt.strftime('%b %d, %H:%M UTC'),
            'elevation': round(alt_val.degrees, 1),
            'azimuth': round(az_val.degrees, 1),
            'range_km': round(distance.km, 1),
            'azimuth_compass': _azimuth_to_compass(az_val.degrees)
        }
        
        if event == 0:  # rise
            current_pass = {'rise': entry, 'culminate': None, 'set': None}
        elif event == 1:  # culminate
            current_pass['culminate'] = entry
        elif event == 2:  # set
            current_pass['set'] = entry
            if current_pass.get('rise'):
                # Compute pass duration
                rise_dt = datetime.strptime(current_pass['rise']['time'], '%Y-%m-%dT%H:%M:%SZ')
                set_dt = datetime.strptime(current_pass['set']['time'], '%Y-%m-%dT%H:%M:%SZ')
                duration_sec = (set_dt - rise_dt).total_seconds()
                current_pass['duration_sec'] = round(duration_sec)
                current_pass['duration_display'] = f"{int(duration_sec // 60)}m {int(duration_sec % 60)}s"
                
                # Determine pass quality from max elevation
                max_el = current_pass['culminate']['elevation'] if current_pass['culminate'] else 0
                if max_el >= 60:
                    current_pass['quality'] = 'Excellent'
                    current_pass['quality_color'] = '#10b981'
                elif max_el >= 30:
                    current_pass['quality'] = 'Good'
                    current_pass['quality_color'] = '#3b82f6'
                elif max_el >= 15:
                    current_pass['quality'] = 'Fair'
                    current_pass['quality_color'] = '#f59e0b'
                else:
                    current_pass['quality'] = 'Low'
                    current_pass['quality_color'] = '#94a3b8'
                
                # Compute pass path points for polar chart (az/el at intervals)
                path_points = []
                pass_duration = duration_sec
                steps = min(20, max(5, int(pass_duration / 15)))
                for s in range(steps + 1):
                    frac = s / steps
                    pass_time = rise_dt + timedelta(seconds=frac * pass_duration)
                    pt = ts.utc(pass_time.year, pass_time.month, pass_time.day,
                                pass_time.hour, pass_time.minute, pass_time.second)
                    diff = sat - observer
                    topo = diff.at(pt)
                    a, az, d = topo.altaz()
                    path_points.append({
                        'azimuth': round(az.degrees, 1),
                        'elevation': round(a.degrees, 1),
                        'azimuth_compass': _azimuth_to_compass(az.degrees)
                    })
                current_pass['path'] = path_points
                passes.append(current_pass)
            current_pass = {}
    
    return passes, None

def _azimuth_to_compass(az_deg):
    """Convert azimuth degrees to compass direction."""
    dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
            'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    idx = round(az_deg / 22.5) % 16
    return dirs[idx]

@app.route('/api/pass-predictions')
@rate_limit(max_per_minute=60, burst_size=80)
def api_pass_predictions():
    sat_name = request.args.get('sat', '')
    try:
        lat = float(request.args.get('lat', 0))
        lon = float(request.args.get('lon', 0))
        alt = float(request.args.get('alt', 0))
        hours = int(request.args.get('hours', 24))
        min_el = float(request.args.get('min_el', 10.0))
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid parameters'}), 400
    
    if not sat_name:
        return jsonify({'error': 'Satellite name required'}), 400
    
    catalog = _load_data('catalog', 'satcat_catalog.json')
    if not catalog:
        return jsonify({'error': 'Catalog data unavailable'}), 503
    
    # Find satellite by name (case-insensitive, partial match)
    sat = None
    sat_name_upper = sat_name.upper()
    for obj in catalog:
        if obj.get('ObjectName', '').upper() == sat_name_upper:
            sat = obj
            break
    if not sat:
        for obj in catalog:
            if sat_name_upper in obj.get('ObjectName', '').upper():
                sat = obj
                break
    if not sat:
        return jsonify({'error': f'Satellite "{sat_name}" not found in catalog'}), 404
    
    tle = sat.get('TLE', '')
    if not tle:
        return jsonify({'error': 'No TLE data for this satellite'}), 404
    
    passes, error = _compute_passes_tle(tle, lat, lon, alt, hours, min_el)
    if error:
        return jsonify({'error': error}), 500
    
    return jsonify({
        'satellite': sat['ObjectName'],
        'catalog_id': sat.get('CatalogID', ''),
        'orbit_class': sat.get('OrbitClass', ''),
        'observer': {'lat': lat, 'lon': lon, 'alt': alt},
        'hours_ahead': hours,
        'min_elevation': min_el,
        'pass_count': len(passes),
        'passes': passes,
        'computed_at': datetime.now(timezone.utc).isoformat()
    })

@app.route('/api/geocode')
@rate_limit(max_per_minute=60)
def api_geocode():
    """Search for a place by name and return coordinates (uses OpenStreetMap Nominatim)."""
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'places': []})
    try:
        url = 'https://nominatim.openstreetmap.org/search?q=' + urllib.parse.quote(query) + '&format=json&limit=5&addressdetails=1'
        req = urllib.request.Request(url, headers={'User-Agent': 'OrbitalIntelligence/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            results = json.loads(resp.read().decode('utf-8'))
        places = []
        for r in results:
            display = r.get('display_name', '')
            # Shorten to city, country for readability
            addr = r.get('address', {})
            short_name = ', '.join(filter(None, [
                addr.get('city') or addr.get('town') or addr.get('village') or addr.get('hamlet') or addr.get('suburb'),
                addr.get('state') or addr.get('region'),
                addr.get('country')
            ])) or display.split(',')[0]
            places.append({
                'name': short_name,
                'full_name': display,
                'lat': float(r.get('lat', 0)),
                'lon': float(r.get('lon', 0))
            })
        return jsonify({'places': places})
    except Exception as e:
        logger.error(f'Geocode error: {e}')
        return jsonify({'places': [], 'error': str(e)})

@app.route('/api/reverse-geocode')
@rate_limit(max_per_minute=60)
def api_reverse_geocode():
    """Convert lat/lon to a place name (uses OpenStreetMap Nominatim)."""
    lat = request.args.get('lat', '')
    lon = request.args.get('lon', '')
    if not lat or not lon:
        return jsonify({'name': ''})
    try:
        url = f'https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&zoom=10&addressdetails=1'
        req = urllib.request.Request(url, headers={'User-Agent': 'OrbitalIntelligence/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode('utf-8'))
        addr = result.get('address', {})
        short_name = ', '.join(filter(None, [
            addr.get('city') or addr.get('town') or addr.get('village') or addr.get('hamlet') or addr.get('county'),
            addr.get('country')
        ])) or result.get('display_name', 'Unknown location').split(',')[0]
        return jsonify({'name': short_name, 'full_name': result.get('display_name', '')})
    except Exception as e:
        logger.error(f'Reverse geocode error: {e}')
        return jsonify({'name': ''})

@app.route('/api/search-satellites')
@rate_limit(max_per_minute=120)
def api_search_satellites():
    """Search catalog for satellite names for autocomplete."""
    query = request.args.get('q', '').upper().strip()
    if not query or len(query) < 2:
        return jsonify({'results': []})
    
    catalog = _load_data('catalog', 'satcat_catalog.json')
    if not catalog:
        return jsonify({'results': []})
    
    results = []
    for obj in catalog:
        name = obj.get('ObjectName', '')
        if query in name.upper():
            results.append({
                'name': name,
                'catalog_id': obj.get('CatalogID', ''),
                'type': obj.get('ObjectType', ''),
                'orbit_class': obj.get('OrbitClass', '')
            })
            if len(results) >= 20:
                break
    return jsonify({'results': results})

@app.route('/api/health')
def api_health():
    return jsonify({
        'status': 'ok',
        'timestamp': time.time(),
        'uptime_seconds': round(time.time() - _app_start_time, 1),
        'data_loaded': {k: v is not None for k, v in _data_cache.items()},
        'sse_connections': _sse_connections,
        'rate_limited_ips': len(_request_counts),
        'space_weather_cached': _space_weather_cache['data'] is not None,
        'launches_cached': _launch_cache['data'] is not None
    })

# --- Server-Sent Events with Connection Cap and Auto-Timeout (item 3) ---
_sse_connections = 0
_sse_lock = threading.Lock()
_MAX_SSE_CONNECTIONS = 100
_SSE_TIMEOUT_SECONDS = 300

@app.route('/api/stream')
def api_stream():
    # SSE not supported on Vercel serverless (no persistent connections)
    if _IS_VERCEL:
        return jsonify({
            'status': 'ok',
            'message': 'SSE not available in serverless mode',
            'space_weather': _get_space_weather(),
            'launches': _get_launches(),
            'threat_level': None
        }), 200
    global _sse_connections
    with _sse_lock:
        if _sse_connections >= _MAX_SSE_CONNECTIONS:
            return jsonify({'error': 'Too many concurrent stream connections'}), 503
        _sse_connections += 1
    
    def event_stream():
        global _sse_connections
        try:
            start = time.time()
            while time.time() - start < _SSE_TIMEOUT_SECONDS:
                data = {
                    'type': 'heartbeat',
                    'timestamp': time.time(),
                    'message': 'sync-check'
                }
                yield f"data: {json.dumps(data)}\n\n"
                time.sleep(30)
            yield f"data: {json.dumps({'type': 'close', 'message': 'Connection timeout, please reconnect'})}\n\n"
        finally:
            with _sse_lock:
                _sse_connections -= 1
    
    return Response(
        stream_with_context(event_stream()),
        content_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )

# --- Background Refresh Thread for External APIs (item 7) ---
def _background_refresh_loop():
    """Refresh external API data (NOAA, Launch Library) every 5 minutes."""
    while True:
        try:
            time.sleep(300)
            logger.info('Background refresh: fetching NOAA space weather...')
            _get_space_weather()
            logger.info('Background refresh: fetching Launch Library...')
            _get_launches()
        except Exception as e:
            logger.error(f'Background refresh error: {e}')

_bg_thread = None

def _start_background_refresh():
    global _bg_thread
    if _bg_thread is None or not _bg_thread.is_alive():
        _bg_thread = threading.Thread(target=_background_refresh_loop, daemon=True)
        _bg_thread.start()
        logger.info('Background refresh thread started')

# --- Data Status (real-time freshness, no hardcoded timestamps) ---
@app.route('/api/data-status')
@rate_limit(max_per_minute=120)
def api_data_status():
    """Return real data freshness info based on file modification times and server uptime."""
    data_files = {
        'collision': 'collision_risk.json',
        'orbital': 'orbital_data.json',
        'catalog': 'satcat_catalog.json',
        'predictions': 'ml_predictions.json'
    }
    sources = {}
    for name, filename in data_files.items():
        try:
            mtime = os.path.getmtime(filename)
            sources[name] = datetime.fromtimestamp(mtime, timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
        except Exception:
            sources[name] = None

    # Most recent data file modification = when data was last synced
    valid_times = [t for t in sources.values() if t]
    last_data_sync = valid_times[0] if valid_times else None

    status = {
        'server_time': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
        'last_data_sync': last_data_sync,
        'data_sources': sources,
        'server_uptime_seconds': round(time.time() - _app_start_time, 0),
        'space_weather_live': _space_weather_cache['ts'] > 0,
        'space_weather_last_fetch': datetime.fromtimestamp(_space_weather_cache['ts'], timezone.utc).strftime('%Y-%m-%d %H:%M UTC') if _space_weather_cache['ts'] > 0 else None,
        'launches_live': _launch_cache['ts'] > 0,
        'launches_last_fetch': datetime.fromtimestamp(_launch_cache['ts'], timezone.utc).strftime('%Y-%m-%d %H:%M UTC') if _launch_cache['ts'] > 0 else None,
    }
    resp = jsonify(status)
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return resp

# --- Preload data caches when imported as a module (gunicorn workers or Vercel) ---
_IS_VERCEL = os.environ.get('VERCEL') is not None
if __name__ != '__main__':
    logger.info('Pre-loading local data cache...')
    _load_data('orbital', 'orbital_data.json')
    _load_data('catalog', 'satcat_catalog.json')
    _load_data('predictions', 'ml_predictions.json')
    _load_data('collision', 'collision_risk.json')
    if _IS_VERCEL:
        # On Vercel serverless: skip external API on cold start (10s timeout)
        # APIs fetch on-demand when called: background thread not supported
        logger.info('Vercel detected: skipping background refresh and external API preloading.')
    else:
        logger.info('Pre-loading space weather from NOAA SWPC...')
        _get_space_weather()
        logger.info('Pre-loading launches from Launch Library 2...')
        _get_launches()
        _start_background_refresh()
        logger.info('Data cache ready. App initialized.')

if __name__ == '__main__':
    # Start via gunicorn for production (item 1), or fall back to Flask dev server
    port = int(os.environ.get('DATABRICKS_APP_PORT', 8000))
    try:
        import sys
        from gunicorn.app.wsgiapp import run as gunicorn_run
        sys.argv = [
            'gunicorn',
            '--bind', f'0.0.0.0:{port}',
            '--workers', '4',
            '--threads', '8',
            '--timeout', '120',
            '--graceful-timeout', '30',
            '--max-requests', '1000',
            '--max-requests-jitter', '100',
            'app:app'
        ]
        logger.info(f'Starting gunicorn on 0.0.0.0:{port} with 4 workers x 8 threads')
        gunicorn_run()
    except ImportError:
        logger.warning('gunicorn not installed, falling back to Flask dev server')
        _load_data('orbital', 'orbital_data.json')
        _load_data('catalog', 'satcat_catalog.json')
        _load_data('predictions', 'ml_predictions.json')
        _load_data('collision', 'collision_risk.json')
        _get_space_weather()
        _get_launches()
        _start_background_refresh()
        app.run(host='0.0.0.0', port=port, threaded=True)