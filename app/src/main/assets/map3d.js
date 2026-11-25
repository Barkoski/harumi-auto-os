/* Mapa 3D da Harumi (MapLibre GL JS 6.16.0, vetores OpenFreeMap via gateway map-api/vt). Adaptador minimo usado por road-map.js.
   Se qualquer coisa falhar (WebGL, worker, estilo), o adaptador chama opts.onFail(motivo) e road-map.js volta ao Leaflet 2D. */
import {Map as MLMap, Marker, AttributionControl, LngLatBounds, setWorkerUrl} from './vendor/maplibre/maplibre-gl.mjs';

const NAV_PITCH = 66, MAX_PITCH = 72, PLAN_PITCH = 16, ZOOM_SHIFT = 1, NAV_ZOOM_SHIFT = 0.5; /* zoom do Leaflet (tiles 256 px) -> MapLibre (tiles 512 px); na navegacao chega um pouco mais perto para os predios aparecerem em volume */
const FATAL = /webgl|context|shader|worker|framebuffer|texture/i;
let styleCache = null;

function reduced() { return !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches); }
function baseUrl() { return new URL('map-api/', document.baseURI).href; }
async function loadStyle() {
  if (!styleCache) {
    const r = await fetch('map-style-harumi.json?v=0317');
    if (!r.ok) throw new Error('style ' + r.status);
    styleCache = await r.text();
  }
  return JSON.parse(styleCache.split('{{BASE}}').join(baseUrl()));
}
/* Lugares uteis ao motorista: camada 'poi' do OpenMapTiles (class/subclass) -> rotulo curto em pt-BR. Quem nao esta aqui e ignorado. */
const POI_SOURCE = 'openmaptiles';
const POI_BY_CLASS = {fuel: 'Posto', restaurant: 'Restaurante', fast_food: 'Lanchonete', cafe: 'Café', lodging: 'Hotel', parking: 'Estacionamento', pharmacy: 'Farmácia', attraction: 'Atração', museum: 'Museu', theme_park: 'Parque temático', bank: 'Banco', atm: 'Caixa eletrônico', police: 'Polícia', fire_station: 'Bombeiros'};
const POI_BY_SUB = {
  hospital: {hospital: 'Hospital', clinic: 'Clínica'},
  car: {car_repair: 'Oficina', car: 'Concessionária', car_parts: 'Autopeças', car_wash: 'Lava-jato'},
  grocery: {supermarket: 'Supermercado', department_store: 'Loja de departamentos'},
  shop: {mall: 'Shopping', department_store: 'Loja de departamentos', supermarket: 'Supermercado'},
  lodging: {guest_house: 'Pousada', hotel: 'Hotel', motel: 'Motel', hostel: 'Hostel'}
};
function poiLabel(cls, sub) {
  const t = POI_BY_SUB[cls];
  if (t) return t[sub] || (cls === 'lodging' ? 'Hotel' : null);
  return POI_BY_CLASS[cls] || null;
}
function dist(aLat, aLon, bLat, bLon) {
  const C = window.HarumiNavCore;
  if (C && C.haversine) return C.haversine({lat: aLat, lon: aLon}, {lat: bLat, lon: bLon});
  const R = Math.PI / 180, x = Math.sin((bLat - aLat) * R / 2) ** 2 + Math.cos(aLat * R) * Math.cos(bLat * R) * Math.sin((bLon - aLon) * R / 2) ** 2;
  return 12742000 * Math.asin(Math.min(1, Math.sqrt(x)));
}
const SVGNS = 'http://www.w3.org/2000/svg';
function carElement() {
  const d = document.createElement('div'); d.className = 'm3-car';
  d.style.width = '84px'; d.style.height = '84px'; /* tamanhos inline: o road-map.css ainda define 72 px / 124 px */
  const glow = document.createElement('i'); glow.style.cssText = 'left:-33px;top:-33px;width:150px;height:150px;background:radial-gradient(circle,rgba(232,170,208,.45) 0,rgba(232,170,208,0) 68%)'; d.appendChild(glow);
  const svg = document.createElementNS(SVGNS, 'svg'); svg.setAttribute('viewBox', '0 0 48 48'); svg.setAttribute('aria-hidden', 'true'); svg.style.width = '84px'; svg.style.height = '84px';
  const p = document.createElementNS(SVGNS, 'path'); p.setAttribute('d', 'M24 4L41 41L24 32L7 41Z'); p.setAttribute('fill', '#d2a0bd'); p.setAttribute('stroke', '#f6eef4'); p.setAttribute('stroke-width', '3'); p.setAttribute('stroke-linejoin', 'round');
  svg.appendChild(p); d.appendChild(svg);
  return d;
}

function create(el, opts) {
  opts = opts || {};
  let map = null, dead = false, ready = false, mode = 'plan', failed = false, netBad = false;
  const queue = [], pins = [], data = {route: null, done: null};
  let car = null, zoomBox = null, fog = null, watchdog = 0;

  function fail(why) {
    if (failed || dead) return; failed = true; clearTimeout(watchdog);
    try { if (opts.onFail) opts.onFail(String(why)); } catch (e) { /* o chamador decide */ }
  }
  function whenMap(fn) { if (map) fn(); else queue.push(fn); }
  function feature(coords) { return coords && coords.length > 1 ? {type: 'Feature', geometry: {type: 'LineString', coordinates: coords}, properties: {}} : {type: 'FeatureCollection', features: []}; }
  function applyData() {
    if (!ready) return;
    const r = map.getSource('route'), d = map.getSource('done');
    if (r) r.setData(feature(data.route));
    if (d) d.setData(feature(data.done));
  }
  function makeZoomButtons() {
    const box = document.createElement('div'); box.className = 'm3-zoom';
    [['+', 'Aproximar', 1], ['−', 'Afastar', -1]].forEach(function (b) {
      const btn = document.createElement('button'); btn.type = 'button'; btn.textContent = b[0]; btn.setAttribute('aria-label', b[1]);
      btn.addEventListener('click', function () { whenMap(function () { reduced() ? map.jumpTo({zoom: map.getZoom() + b[2]}) : map.easeTo({zoom: map.getZoom() + b[2], duration: 250}); }); });
      box.appendChild(btn);
    });
    el.parentNode.appendChild(box); return box;
  }
  function start(style) {
    if (dead) return;
    try {
      try { setWorkerUrl(new URL('./vendor/maplibre/maplibre-gl-worker.mjs', import.meta.url).href); } catch (e) { /* usa o padrao derivado de import.meta.url */ }
      map = new MLMap({
        container: el, style: style, center: [-52, -18], zoom: 4, minZoom: 2.5, maxZoom: 19, pitch: 0, maxPitch: MAX_PITCH,
        pixelRatio: Math.min(window.devicePixelRatio || 1, 1.5), fadeDuration: 120, renderWorldCopies: false,
        attributionControl: false, canvasContextAttributes: {antialias: false, failIfMajorPerformanceCaveat: false, powerPreference: 'high-performance'},
        dragRotate: false, touchPitch: false, pitchWithRotate: false
      });
    } catch (e) { fail('create: ' + (e && e.message)); return; }
    map.touchZoomRotate.disableRotation();
    map.addControl(new AttributionControl({compact: false, customAttribution: 'OpenFreeMap · OpenMapTiles'}), 'bottom-left');
    let bad = false;
    map.on('error', function (e) {
      const msg = String((e && e.error && e.error.message) || (e && e.message) || '');
      if (e && e.error && (e.error.name === 'AbortError' || /abort/i.test(msg))) return; /* tile cancelado porque a camera saltou: nao e falha de rede */
      const c = e && e.tile && e.tile.tileID && e.tile.tileID.canonical;
      if (c && !FATAL.test(msg)) { /* tile que falhou: confere de novo antes de avisar; saltos da camera cancelam pedidos e isso nao e queda de rede */
        fetch(baseUrl() + 'vt/' + c.z + '/' + c.x + '/' + c.y + '.pbf').then(function (r) { if (!r.ok) throw new Error('http ' + r.status); }).catch(function () { bad = true; netBad = true; if (opts.onStatus) opts.onStatus(false); });
        return;
      }
      if (e && (e.tile || e.sourceId)) { bad = true; netBad = true; if (opts.onStatus) opts.onStatus(false); return; }
      if (FATAL.test(msg)) fail('error: ' + msg); else { bad = true; netBad = true; if (opts.onStatus) opts.onStatus(false); }
    });
    map.on('idle', function () { if (!bad && netBad) { netBad = false; if (opts.onStatus) opts.onStatus(true); } bad = false; if (opts.onIdle) { try { opts.onIdle(); } catch (e) { /* ouvinte do chamador */ } } });
    map.on('dragstart', function (e) { if (e && e.originalEvent && opts.onDrag) opts.onDrag(); });
    map.getCanvas().addEventListener('webglcontextlost', function () { fail('webglcontextlost'); }, false);
    map.once('load', function () { ready = true; clearTimeout(watchdog); applyData(); if (opts.onLoad) opts.onLoad(); });
    watchdog = setTimeout(function () { if (!ready) fail('timeout: estilo nao carregou em 25 s'); }, 25000);
    while (queue.length) { try { queue.shift()(); } catch (e) { /* um comando atrasado nao derruba os demais */ } }
  }
  zoomBox = makeZoomButtons();
  fog = document.createElement('div'); fog.className = 'm3-fog'; fog.style.height = '26%'; fog.style.background = 'linear-gradient(to bottom,rgba(58,45,68,.9) 0,rgba(176,122,160,.62) 5%,rgba(120,82,114,.3) 14%,rgba(59,46,61,0) 100%)'; /* faixa de horizonte luminosa; o ceu do estilo (setSky) nao aparece de forma confiavel no headless */ fog.hidden = true; fog.setAttribute('aria-hidden', 'true'); el.parentNode.appendChild(fog);
  loadStyle().then(start, function (e) { fail('style: ' + (e && e.message)); });

  const api = {
    get map() { return map; },
    isReady: function () { return ready; },
    getState: function () { return map ? {pitch: map.getPitch(), bearing: map.getBearing(), zoom: map.getZoom(), center: map.getCenter().toArray(), loaded: ready && map.loaded(), mode: mode} : null; },
    resize: function () { whenMap(function () { map.resize(); }); },
    setView: function (lat, lon, zoom) { whenMap(function () { map.jumpTo({center: [lon, lat], zoom: zoom - ZOOM_SHIFT}); }); },
    fitBounds: function (coords, o) {
      o = o || {};
      whenMap(function () {
        const pd = o.padding == null ? 60 : o.padding; /* numero (todos os lados) ou objeto {top,left,right,bottom} */
        const b = new LngLatBounds(); coords.forEach(function (c) { b.extend(c); });
        map.fitBounds(b, {padding: pd, maxZoom: (o.maxZoom || 14) - ZOOM_SHIFT, pitch: mode === 'nav' ? NAV_PITCH : PLAN_PITCH, bearing: 0, duration: reduced() ? 0 : 600, essential: false});
      });
    },
    /* Enquadra um ponto (planejador): zoom no padrao do Leaflet, pitch suave, sem rumo nem padding de navegacao. */
    frame: function (lat, lon, zoom, pitch) {
      const z = (zoom == null ? 13 : zoom) - ZOOM_SHIFT, p = pitch == null ? 30 : pitch;
      whenMap(function () {
        const cam = {center: [lon, lat], zoom: z, pitch: p, bearing: 0, padding: {top: 0, bottom: 0, left: 0, right: 0}};
        if (reduced() || Math.abs(map.getZoom() - z) > 3) map.jumpTo(cam); /* salto grande (Brasil -> cidade): animar baixaria tiles de todos os zooms do caminho */ else map.easeTo(Object.assign(cam, {duration: 600, essential: false}));
      });
    },
    /* Lugares perto de (lat,lon) a partir dos tiles ja carregados (querySourceFeatures nao baixa nada). Os tiles do OpenFreeMap so trazem 'poi'
       no zoom 14 (nos zooms 12-13 quase nada), entao a lista depende de a camera estar em zoom MapLibre >= ~13.5 perto do ponto.
       Devolve [{name,label,cls,sub,lat,lon,dist}] sem repeticao de nome, no maximo um por tipo primeiro (varia a lista), ordenado por distancia. */
    nearbyPlaces: function (lat, lon, raioM, max) {
      if (!ready || !map || !isFinite(lat) || !isFinite(lon)) return [];
      let feats;
      try { feats = map.querySourceFeatures(POI_SOURCE, {sourceLayer: 'poi'}); } catch (e) { return []; }
      const lim = raioM > 0 ? raioM : 3000, n = max > 0 ? max : 4, seen = {};
      for (let i = 0; i < feats.length; i++) {
        const f = feats[i], p = f.properties || {}, g = f.geometry, name = String(p.name || '').trim();
        if (!name || !g || g.type !== 'Point' || !g.coordinates) continue;
        const label = poiLabel(p.class, p.subclass); if (!label) continue;
        const plon = g.coordinates[0], plat = g.coordinates[1], d = dist(lat, lon, plat, plon);
        if (!(d <= lim)) continue;
        const key = name.toLowerCase() + '|' + label, old = seen[key];
        if (!old || d < old.dist) seen[key] = {name: name, label: label, cls: p.class, sub: p.subclass, lat: plat, lon: plon, dist: d};
      }
      const all = Object.keys(seen).map(function (k) { return seen[k]; }).sort(function (a, b) { return a.dist - b.dist; });
      const picked = [], labels = {};
      all.forEach(function (it) { if (picked.length < n && !labels[it.label]) { labels[it.label] = 1; picked.push(it); } });
      all.forEach(function (it) { if (picked.length < n && picked.indexOf(it) < 0) picked.push(it); });
      return picked.sort(function (a, b) { return a.dist - b.dist; });
    },
    setRoute: function (coords) { data.route = coords; data.done = null; applyData(); },
    setDone: function (coords) { data.done = coords; applyData(); },
    clearRoute: function () { data.route = null; data.done = null; applyData(); },
    addPin: function (lat, lon, text, title) {
      const d = document.createElement('div'); d.className = 'route-pin'; d.style.width = '30px'; d.style.height = '30px'; d.textContent = text; if (title) d.title = title;
      const m = new Marker({element: d, anchor: 'center'}); m.setLngLat([lon, lat]);
      const h = {remove: function () { m.remove(); const i = pins.indexOf(h); if (i >= 0) pins.splice(i, 1); }, getElement: function () { return d; }};
      pins.push(h); whenMap(function () { if (pins.indexOf(h) >= 0) m.addTo(map); }); return h;
    },
    setCar: function (lat, lon, bearing) {
      whenMap(function () {
        if (!car) { car = new Marker({element: carElement(), anchor: 'center', rotationAlignment: 'map', pitchAlignment: 'map'}); car.setLngLat([lon, lat]).setRotation(bearing || 0).addTo(map); }
        else car.setLngLat([lon, lat]).setRotation(bearing || 0);
      });
    },
    clearCar: function () { if (car) { car.remove(); car = null; } },
    setMode: function (m) {
      mode = m;
      whenMap(function () {
        if (m === 'nav') { map.setMaxZoom(18); }
        else { map.setMaxZoom(19); map.jumpTo({pitch: PLAN_PITCH, bearing: 0, padding: {top: 0, bottom: 0, left: 0, right: 0}}); }
      });
      if (zoomBox) zoomBox.hidden = m === 'nav';
      if (fog) fog.hidden = m !== 'nav';
    },
    /* Camera de navegacao: atras do carro, inclinada, girada para o rumo; carro no terco inferior via padding (nao gira o container). */
    follow: function (lat, lon, bearing, kmh, o) {
      o = o || {};
      whenMap(function () {
        const H = el.clientHeight || 400, z = (o.zoom != null ? o.zoom : 16) - NAV_ZOOM_SHIFT;
        const cam = {center: [lon, lat], bearing: bearing || 0, pitch: NAV_PITCH, zoom: z, padding: {top: Math.round(H * 0.40), bottom: 0, left: 0, right: 0}};
        if (o.force || reduced()) map.jumpTo(cam);
        else map.easeTo(Object.assign(cam, {duration: 900, easing: function (t) { return t; }, essential: true}));
      });
    },
    destroy: function () {
      dead = true; clearTimeout(watchdog);
      pins.slice().forEach(function (p) { p.remove(); });
      if (car) { car.remove(); car = null; }
      [zoomBox, fog].forEach(function (n) { if (n && n.parentNode) n.parentNode.removeChild(n); });
      if (map) { try { map.remove(); } catch (e) { /* ja liberado */ } map = null; }
    }
  };
  window.HarumiMap3D.current = api; /* ajuda de depuracao/testes */
  return api;
}

window.HarumiMap3D = {create: create, version: '6.16.0', current: null};
window.dispatchEvent(new Event('harumi-map3d-ready'));
