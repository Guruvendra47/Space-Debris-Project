// orbital-worker.js - Web Worker for heavy orbital data processing
// Runs in a background thread to keep the UI responsive on low-end devices

var _debrisData = [];
var _catalogData = [];

function estAM(type, rcs) {
  if (type === 'Debris') return 0.05 + Math.random() * 0.95;
  if (type === 'Rocket Body') return 0.01 + Math.random() * 0.04;
  if (type === 'Payload') return 0.005 + Math.random() * 0.045;
  return 0.01 + Math.random() * 0.1;
}

function getDebrisSource(name, type) {
  if (!name) return 'other';
  var n = name.toUpperCase();
  if (n.indexOf('FENGYUN') >= 0 || n.indexOf('FY-1C') >= 0) return 'fengyun';
  if (n.indexOf('IRIDIUM') >= 0 && n.indexOf('33') >= 0) return 'iridium';
  if (n.indexOf('COSMOS') >= 0 && n.indexOf('1408') >= 0) return 'cosmos1408';
  if (n.indexOf('SHAKTI') >= 0 || n.indexOf('MICROSAT-R') >= 0) return 'shakti';
  if (type === 'Rocket Body' && (n.indexOf('SL-') >= 0 || n.indexOf('COSMOS') >= 0 || n.indexOf('R/B') >= 0)) return 'rocket';
  return 'other';
}

var ar = {leo:[0,2000], meo:[0,35785], geo:[35785,36000], heo:[36000,999999]};

self.onmessage = function(e) {
  var msg = e.data;
  if (msg.type === 'init') {
    _debrisData = msg.debrisData || [];
    _catalogData = msg.catalogData || [];
    self.postMessage({type: 'ready', debrisCount: _debrisData.length, catalogCount: _catalogData.length});
    return;
  }
  if (msg.type === 'filterDebris') {
    self.postMessage({type: 'debrisResult', reqId: msg.reqId, data: _filterDebris(msg.params)});
    return;
  }
  if (msg.type === 'filterCatalog') {
    self.postMessage({type: 'catalogResult', reqId: msg.reqId, data: _filterCatalog(msg.params)});
    return;
  }
};

function _filterDebris(p) {
  var s = (p.search || '').toLowerCase();
  var a = p.altitude || 'all';
  var ty = p.type || 'all';
  var rk = p.risk || 'all';
  var src = p.source || 'all';
  var colaQuick = p.colaQuick || false;
  var hideUnattr = p.hideUnattr || false;
  var sortCol = p.sortCol;
  var sortAsc = p.sortAsc;
  var visible = p.visible || 100;
  var f = _debrisData.slice();
  if (ty !== 'all') f = f.filter(function(o) { return o.ObjectType === ty; });
  if (s) f = f.filter(function(o) { return (o.Name || '').toLowerCase().indexOf(s) >= 0 || (o.NORAD_ID || '').indexOf(s) >= 0 || (o.Owner || '').toLowerCase().indexOf(s) >= 0; });
  if (a !== 'all') { var r = ar[a]; f = f.filter(function(o) { return (o.AltitudeKM || 0) >= r[0] && (o.AltitudeKM || 0) < r[1]; }); }
  if (rk === 'High') f = f.filter(function(o) { return o.RiskLevel === 'High'; });
  else if (rk === 'Medium') f = f.filter(function(o) { return o.RiskLevel === 'High' || o.RiskLevel === 'Medium'; });
  else if (rk === 'Low') f = f.filter(function(o) { return o.RiskLevel === 'Low'; });
  if (src !== 'all') f = f.filter(function(o) { return getDebrisSource(o.Name, o.ObjectType) === src; });
  if (colaQuick) f = f.filter(function(o) { return o.ColA === 'MANEUVER REQUIRED' || o.TCA_Hours > 0 || o.MissDistance_km > 0; });
  if (hideUnattr) f = f.filter(function(o) { var ow = (o.Owner || '').toLowerCase(); return ow && ow !== 'unknown' && ow !== 'unk' && ow !== '-' && ow !== 'n/a'; });
  f.forEach(function(o) { if (!o.amRatio) o.amRatio = estAM(o.ObjectType, o.RadarSize); });
  if (sortCol) { f = [].concat(f).sort(function(a, b) { var va = a[sortCol] || 0, vb = b[sortCol] || 0; if (sortCol === 'DecayProbability') { va = a.DecayProbability || 0; vb = b.DecayProbability || 0; } if (sortCol === 'amRatio') { va = a.amRatio || 0; vb = b.amRatio || 0; } return sortAsc ? (va > vb ? 1 : va < vb ? -1 : 0) : (va < vb ? 1 : va > vb ? -1 : 0); }); }
  var total = f.length; f = f.slice(0, visible);
  return { rows: f, total: total };
}

function _filterCatalog(p) {
  var s = (p.search || '').toLowerCase();
  var t = p.type || 'all';
  var st = p.status || 'all';
  var rg = p.regime || 'all';
  var sortCol = p.sortCol;
  var sortAsc = p.sortAsc;
  var visible = p.visible || 100;
  var f = _catalogData.slice();
  if (s) f = f.filter(function(o) { return (o.ObjectName || '').toLowerCase().indexOf(s) >= 0 || (o.CatalogID || '').indexOf(s) >= 0 || (o.Owner || '').toLowerCase().indexOf(s) >= 0; });
  if (t !== 'all') f = f.filter(function(o) { return o.ObjectType === t; });
  if (st === 'active') f = f.filter(function(o) { return o.IsDecayed === 0; });
  if (st === 'decayed') f = f.filter(function(o) { return o.IsDecayed === 1; });
  if (rg !== 'all') { var rm = {leo:'Low', meo:'Medium', geo:'Geosync', heo:'High'}; f = f.filter(function(o) { return (o.OrbitClass || '').indexOf(rm[rg]) >= 0; }); }
  if (sortCol) { f = [].concat(f).sort(function(a, b) { var va = a[sortCol] || 0, vb = b[sortCol] || 0; return sortAsc ? (va > vb ? 1 : va < vb ? -1 : 0) : (va < vb ? 1 : va > vb ? -1 : 0); }); }
  var total = f.length; f = f.slice(0, visible);
  return { rows: f, total: total };
}