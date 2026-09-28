import os
import json
import time
import math
import urllib.request
from datetime import datetime, timedelta, timezone
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
        print(f'NOAA Kp fetch error: {e}')
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
        print(f'NOAA solar wind fetch error: {e}')
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
        print(f'NOAA F10.7 fetch error: {e}')
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
        print(f'NOAA 3-day forecast fetch error: {e}')
    return None

def _get_space_weather():
    """Aggregate space weather data with 5-minute cache."""
    now = time.time()
    if _space_weather_cache['data'] and (now - _space_weather_cache['ts']) < 300:
        return _space_weather_cache['data']
    
    kp_data = _fetch_noaa_kp()
    solar_wind = _fetch_noaa_solar_wind()
    f107_data = _fetch_noaa_flare_flux()
    forecast_3day = _fetch_noaa_3day_forecast()
    
    kp = kp_data['current_kp'] if kp_data else 0.0
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
        drag_status = 'ELEVATED - Increased atmospheric drag at LEO altitudes'
        drag_color = '#ef4444'
    elif f107 > 120 or kp > 4:
        drag_status = 'MODERATE - Slightly elevated drag conditions'
        drag_color = '#f59e0b'
    else:
        drag_status = 'NOMINAL - Stable atmospheric density for re-entry forecasting'
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
        'timestamp': now
    }
    _space_weather_cache['data'] = data
    _space_weather_cache['ts'] = now
    return data

@app.route('/api/space-weather')
@rate_limit(max_per_minute=20)
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
            })
        _launch_cache['data'] = {'launches': launches, 'count': len(launches)}
        _launch_cache['ts'] = now
        return _launch_cache['data']
    except Exception as e:
        print(f'Launch Library fetch error: {e}')
        return {'launches': [], 'count': 0, 'error': str(e)}

@app.route('/api/launches')
@rate_limit(max_per_minute=20)
def api_launches():
    data = _get_launches()
    resp = jsonify(data)
    resp.headers['Cache-Control'] = 'public, max-age=600'
    resp.headers['X-Data-Source'] = 'launch-library-2'
    return resp

# --- Threat Level (derived from collision data + space weather) ---
@app.route('/api/threat-level')
@rate_limit(max_per_minute=30)
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
            threat_factors.append(f'{critical:,} critical-risk objects in orbit')
        elif critical > 5000:
            threat_score += 40
            threat_factors.append(f'{critical:,} critical-risk objects')
        else:
            threat_score += 20
            threat_factors.append(f'{critical:,} critical-risk objects')
        if high > 10:
            threat_score += 15
            threat_factors.append(f'{high} high-risk conjunctions')
    
    kp = sw.get('kp_index', 0)
    if kp >= 7:
        threat_score += 25
        threat_factors.append(f'Geomagnetic storm G3+ (Kp={kp})')
    elif kp >= 5:
        threat_score += 15
        threat_factors.append(f'Geomagnetic storm (Kp={kp})')
    elif kp >= 4:
        threat_score += 5
        threat_factors.append(f'Elevated geomagnetic activity (Kp={kp})')
    
    f107 = sw.get('f107_flux', 0)
    if f107 > 180:
        threat_score += 10
        threat_factors.append(f'High solar flux F10.7={f107:.1f}')
    
    if threat_score >= 70:
        level = 'CRITICAL'
        color = '#ef4444'
        description = 'Severe orbital environment \u2014 multiple critical threats active'
    elif threat_score >= 50:
        level = 'GUARDED'
        color = '#f59e0b'
        description = 'Elevated threat conditions \u2014 enhanced monitoring recommended'
    elif threat_score >= 25:
        level = 'ELEVATED'
        color = '#3b82f6'
        description = 'Moderate threat level \u2014 routine monitoring active'
    else:
        level = 'NOMINAL'
        color = '#10b981'
        description = 'Nominal orbital environment \u2014 no significant threats detected'
    
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
@rate_limit(max_per_minute=15)
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

@app.route('/api/search-satellites')
@rate_limit(max_per_minute=30)
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
    print('Pre-loading space weather from NOAA SWPC...')
    _get_space_weather()
    print('Pre-loading launches from Launch Library 2...')
    _get_launches()
    print('Data cache ready.')
    app.run(host='0.0.0.0', port=os.environ.get('DATABRICKS_APP_PORT', 8000), threaded=True)