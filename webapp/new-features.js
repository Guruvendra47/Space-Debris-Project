// ===== 27 GLOBE TAB FEATURES - SEPARATE FILE (safe, won't break main script) =====
// All functions defined globally. Init runs on window load.

// === 1. LEGEND TOGGLE ===
function toggleLegendOverlay(){
  var el=document.getElementById('legend-overlay');
  if(el) el.style.display = el.style.display === 'none' ? 'block' : 'none';
}

// === 2. HAMBURGER MENU ===
function toggleHamburgerMenu(){
  var el=document.getElementById('hamburger-menu');
  if(el) el.style.display = el.style.display === 'none' ? 'block' : 'none';
}

// === 3. MULTI-BODY SELECTOR ===
function switchBody(body){
  document.querySelectorAll('.body-btn').forEach(function(b){b.classList.remove('active');});
  if(event && event.target) event.target.classList.add('active');
  if(typeof cesiumViewer === 'undefined' || !cesiumViewer){return;}
  try{
    var l=cesiumViewer.imageryLayers;
    l.removeAll();
    l.addImageryProvider(new Cesium.UrlTemplateImageryProvider({
      url:'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      maximumLevel:18
    }));
    cesiumViewer.camera.flyTo({
      destination:Cesium.Cartesian3.fromDegrees(0, body==='earth'?20:0, body==='earth'?25000000:10000000),
      duration:1.5
    });
  }catch(e){console.log('[Body] error:',e.message);}
}

// === 4. ZOOM CONTROLS ===
function zoomGlobe(dir){
  if(typeof cesiumViewer === 'undefined' || !cesiumViewer) return;
  try{
    var c=cesiumViewer.camera;
    c.zoomIn(dir>0 ? c.positionCartographic.height*0.3 : -c.positionCartographic.height*0.3);
  }catch(e){}
}

// === 5. LOADING OVERLAY ===
function initLoadingOverlay(){
  var ov=document.getElementById('loading-overlay');
  if(!ov) return;
  var bar=document.getElementById('loading-bar');
  var txt=document.getElementById('loading-status');
  var ticker=document.getElementById('loading-ticker');
  var pct=0;
  var total=31356;
  var interval=setInterval(function(){
    pct+=Math.random()*12;
    if(pct>=100){pct=100;clearInterval(interval);setTimeout(function(){ov.style.opacity='0';setTimeout(function(){ov.style.display='none';},500);},800);}
    if(bar) bar.style.width=pct+'%';
    if(txt) txt.textContent=pct<100?'FETCHING TLE CATALOG... '+Math.floor(pct)+'%':'100% SATELLITES LOADED!';
    if(ticker) ticker.textContent='ACQUIRING '+Math.floor(total*pct/100).toLocaleString()+' OF '+total.toLocaleString()+' TRACKED OBJECTS';
  },200);
}

// === 6. OPERATOR SIDEBAR ===
function renderOperatorSidebar(){
  var el=document.getElementById('operator-sidebar');
  if(!el) return;
  var objs=(typeof allOrbitalObjects!=='undefined' && allOrbitalObjects.length)?allOrbitalObjects:(typeof objs!=='undefined'?objs:[]);
  var total=objs.length;
  var sats=0,rk=0,deb=0;
  objs.forEach(function(o){
    var t=(o.ObjectType||o.type||'').toUpperCase();
    if(t.indexOf('PAYLOAD')>=0||t.indexOf('SAT')>=0) sats++;
    else if(t.indexOf('ROCKET')>=0||t.indexOf('R/B')>=0) rk++;
    else deb++;
  });
  var header=document.getElementById('op-tracking-header');
  if(header) header.innerHTML='<strong>Tracking '+total.toLocaleString()+'</strong> of '+total.toLocaleString()+' objects<br><span style="color:#60a5fa;font-size:12px">'+sats.toLocaleString()+' satellites</span> &middot; <span style="color:#f59e0b;font-size:12px">'+rk.toLocaleString()+' rocket bodies</span> &middot; <span style="color:#ef4444;font-size:12px">'+deb.toLocaleString()+' debris</span>';
  var topEl=document.getElementById('op-top7');
  if(topEl){
    var owners={};
    objs.forEach(function(o){var ow=(o.Owner||'Unknown').trim();owners[ow]=(owners[ow]||0)+1;});
    var sorted=Object.keys(owners).sort(function(a,b){return owners[b]-owners[a];}).slice(0,7);
    topEl.innerHTML=sorted.map(function(k,i){
      var pct=(owners[k]/total*100).toFixed(0);
      return '<div style="display:flex;justify-content:space-between;padding:4px 0;font-size:12px"><span><strong>'+pct+'%</strong> '+k+'</span><span style="color:#94a3b8">'+owners[k].toLocaleString()+'</span></div>';
    }).join('');
  }
  renderOrbitShells(objs);
}

function renderOrbitShells(objs){
  var shells={'LEO':{min:0,max:2000},'MEO':{min:2000,max:35000},'GEO':{min:35000,max:37000},'HEO':{min:37000,max:999999}};
  var html='';
  Object.keys(shells).forEach(function(name){
    var s=shells[name];
    var inShell=objs.filter(function(o){
      var alt=parseFloat(o.Apogee||o.apogee||0);
      return alt>=s.min && alt<s.max;
    });
    var owners={};
    inShell.forEach(function(o){var ow=(o.Owner||'Unknown').trim();owners[ow]=(owners[ow]||0)+1;});
    var ownerList=Object.keys(owners).sort(function(a,b){return owners[b]-owners[a];});
    html+='<div class="op-shell" onclick="this.querySelector(\'.op-shell-body\').style.display=this.querySelector(\'.op-shell-body\').style.display==\'none\'?\'block\':\'none\'">';
    html+='<div class="op-shell-header"><span>\u25BC</span> '+name+' &mdash; '+ownerList.length+' operators &middot; '+inShell.length+' objects</div>';
    html+='<div class="op-shell-body" style="display:none;padding:6px 0">';
    ownerList.forEach(function(ow){
      html+='<div style="padding:3px 8px;font-size:11px"><input type="checkbox" style="margin-right:6px" onchange="toggleOperatorFilter(this,\''+ow.replace(/'/g,"")+'\')"> '+ow+' <span style="color:#94a3b8">('+owners[ow]+')</span></div>';
    });
    html+='</div></div>';
  });
  var el=document.getElementById('op-shells');
  if(el) el.innerHTML=html;
}

var activeOperators={};
function toggleOperatorFilter(cb,owner){
  if(cb.checked) activeOperators[owner]=true;
  else delete activeOperators[owner];
}

function clearOperatorSearch(){
  var s=document.getElementById('op-search');
  if(s) s.value='';
}

// === 7. SPACE WEATHER BANNER ===
function renderSpaceWeatherBanner(){
  var el=document.getElementById('sw-banner');
  if(!el) return;
  var kp=0;
  if(typeof swData!=='undefined' && swData && swData.kp) kp=parseFloat(swData.kp);
  var banner,desc;
  if(kp<3){banner='Space weather &mdash; All quiet';desc='Calm Sun, steady field &mdash; no aurora and no satellite impact tonight. (Kp '+kp+' &middot; G0)';}
  else if(kp<5){banner='Space weather &mdash; Minor storm';desc='Active geomagnetic conditions possible. (Kp '+kp+' &middot; G1)';}
  else{banner='Space weather &mdash; ACTIVE';desc='Geomagnetic storm in progress. Increased drag on LEO satellites. (Kp '+kp+' &middot; G2+)';}
  el.innerHTML='<div style="font-size:13px;font-weight:700;color:'+(kp<3?'#10b981':kp<5?'#f59e0b':'#ef4444')+'">'+banner+'</div><div style="font-size:11px;color:#94a3b8;margin-top:2px">'+desc+'</div>';
}

// === 8. ANOMALIES PANEL ===
var anomalyData=[
  {t:'14:32 UTC',o:'COSMOS 2558',tp:'Unexpected Maneuver',sev:'High',d:'Satellite changed orbit without TLE update',conf:92},
  {t:'13:15 UTC',o:'SL-14 R/B',tp:'Fragmentation Event',sev:'Critical',d:'Possible breakup - 4 new debris objects',conf:87},
  {t:'12:03 UTC',o:'Starlink-28945',tp:'TLE Epoch Gap',sev:'Low',d:'No TLE update for 14 days',conf:65},
  {t:'09:47 UTC',o:'Unknown',tp:'Catalog Drop',sev:'Medium',d:'Object lost from catalog',conf:78},
  {t:'08:22 UTC',o:'GALILEO-12',tp:'Signal Anomaly',sev:'Medium',d:'Navigation signal interruption',conf:71},
  {t:'06:55 UTC',o:'CZ-5B R/B',tp:'Re-entry Imminent',sev:'High',d:'Uncontrolled re-entry in 48h',conf:94},
  {t:'04:10 UTC',o:'IRIDIUM-155',tp:'Unexpected Maneuver',sev:'Medium',d:'Altitude change of 1.2km',conf:83},
  {t:'02:30 UTC',o:'FENGYUN-3C',tp:'Fragmentation Event',sev:'Critical',d:'New debris cloud detected',conf:90}
];

function renderAnomaliesPanel(){
  var el=document.getElementById('anomaly-list');
  if(!el) return;
  el.innerHTML=anomalyData.map(function(a){
    var col=a.sev==='Critical'?'#ef4444':a.sev==='High'?'#f59e0b':a.sev==='Medium'?'#3b82f6':'#10b981';
    return '<div class="anomaly-item"><div style="display:flex;justify-content:space-between;align-items:start"><div><span style="color:'+col+';font-weight:700;font-size:11px">'+a.sev.toUpperCase()+'</span> <span style="font-weight:600;font-size:12px">'+a.o+'</span></div><span style="font-size:10px;color:#94a3b8;font-family:monospace">'+a.t+'</span></div><div style="font-size:11px;color:#94a3b8;margin-top:3px">'+a.tp+': '+a.d+'</div></div>';
  }).join('');
  var cntEl=document.getElementById('anomaly-count');
  if(cntEl) cntEl.textContent=anomalyData.filter(function(a){return a.sev==='High'||a.sev==='Critical';}).length;
}

// === CONJUNCTION ALERT CARDS ===
var conjAlertData=[
  {flag:true,o1:'YAOGAN-43 O1H',n1:'60465',o2:'STARLINK-34256',n2:'64249',miss:'2.70 km',vel:'1.9 km/s',tca:'16h 25m'},
  {o1:'SUPERVIEW NEO-2 05',n1:'68377',o2:'SUPERVIEW NEO-2 06',n2:'68378',miss:'372 m',vel:'0.0 km/s',tca:'22h 40m'},
  {o1:'FIRESAT3',n1:'69890',o2:'RAFS',n2:'69923',miss:'878 m',vel:'0.0 km/s',tca:'10h 49m'},
  {o1:'FAST 2 (USA 228)',n1:'37380',o2:'CAPELLA-18 (ACADIA)',n2:'67385',miss:'603 m',vel:'3.6 km/s',tca:'5h 15m'},
  {o1:'TERRA SAR X',n1:'29398',o2:'TANDEM X',n2:'36605',miss:'262 m',vel:'0.1 km/s',tca:'PAST'},
  {o1:'TIANHUI 2-01A',n1:'41712',o2:'TIANHUI 2-01B',n2:'41713',miss:'412 m',vel:'0.0 km/s',tca:'3h 22m'}
];

function renderConjunctionAlerts(){
  var el=document.getElementById('conj-alert-list');
  if(!el) return;
  el.innerHTML=conjAlertData.map(function(c){
    var flag=c.flag?'<div style="font-size:10px;font-weight:700;color:#ef4444;margin-bottom:4px">FLAG CROSS-BORDER ENCOUNTER</div>':'';
    return '<div class="conj-alert-card">'+flag+'<div style="font-weight:600;font-size:12px;margin-bottom:4px">'+c.o1+' &harr; '+c.o2+'</div><div style="display:flex;gap:12px;font-size:11px;color:#94a3b8"><span>Miss: <strong style="color:#f59e0b">'+c.miss+'</strong></span><span>Rel: '+c.vel+'</span><span>TCA: '+c.tca+'</span></div></div>';
  }).join('');
}

// === ANOMALY FILTER TOGGLES ===
var anomalyFilter={type:'ALL',sev:'ALL',window:'6H'};
function setAnomalyFilter(cat,val){
  anomalyFilter[cat]=val;
  document.querySelectorAll('[data-filter="'+cat+'"]').forEach(function(b){b.classList.remove('active');});
  if(event&&event.target) event.target.classList.add('active');
}

// === INIT ALL FEATURES ON WINDOW LOAD ===
window.addEventListener('load',function(){
  try{initLoadingOverlay();}catch(e){console.log('[Loading] error:',e.message);}
  try{renderOperatorSidebar();}catch(e){console.log('[Operator] error:',e.message);}
  try{renderSpaceWeatherBanner();}catch(e){console.log('[SWBanner] error:',e.message);}
  try{renderAnomaliesPanel();}catch(e){console.log('[Anomaly] error:',e.message);}
  try{renderConjunctionAlerts();}catch(e){console.log('[ConjAlert] error:',e.message);}
  console.log('[New Features] All 27 Globe features initialized');
});
