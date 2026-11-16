'use strict';
/* Atalaia — frontend em JavaScript puro. Todo texto vindo do servidor passa por esc() antes de virar HTML. */
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const safeUrl = (u) => (/^https?:\/\//i.test(u || '') ? esc(u) : '#');
const link = (u, text) => `<a href="${safeUrl(u)}" target="_blank" rel="noopener noreferrer">${text}</a>`;
const fmt = (n) => Number(n || 0).toLocaleString('pt-BR');
const ls = { get: (k) => { try { return localStorage.getItem(k); } catch (e) { return null; } }, set: (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} } };
function ago(iso) {
  const m = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (!isFinite(m)) return '';
  if (m < 1) return 'agora';
  if (m < 60) return `há ${m} min`;
  if (m < 1440) return `há ${Math.round(m / 60)} h`;
  return `há ${Math.round(m / 1440)} d`;
}
function km(a, b) {
  const R = 6371, r = Math.PI / 180, dLat = (b.lat - a.lat) * r, dLng = (b.lng - a.lng) * r;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

// ------------------------------------------------------------------ camadas
const LV = { 1: '#44d38a', 2: '#a6d84a', 3: '#ffd23f', 4: '#ff9a3c', 5: '#ff5a4d' };
const CAT_LABEL = { attack: 'Conflito', unrest: 'Protesto', outbreak: 'Surto', cyber: 'Cibernético', infra: 'Infraestrutura', general: 'Geral' };
const newsPop = (kind) => (d) => `<span class="tag" style="--c:${LAYER[kind].color}">${LAYER[kind].label}</span><b>${esc(d.title)}</b><small>${esc(d.flag)} ${esc(d.country)} · ${esc(d.source)} · ${ago(d.at)}</small>${link(d.link, 'Abrir a notícia ↗')}`;
const LAYERS = [
  { key: 'attacks', label: 'Conflitos', color: '#ff5a4d', r: () => 7, pop: (d) => newsPop('attacks')(d) },
  { key: 'unrest', label: 'Protestos', color: '#ff9a3c', r: () => 6, pop: (d) => newsPop('unrest')(d) },
  { key: 'aircraft', label: 'Aeronaves militares', color: '#5cc8ff', r: (d) => (d.role === 'other' ? 3.5 : 5.5),
    c: (d) => ({ recon: '#ff5a4d', bomber: '#ff5a4d', tanker: '#ffd23f' }[d.role] || '#5cc8ff'),
    pop: (d) => `<b>${esc(d.callsign || d.reg || d.id)}</b><small>${esc(d.role_label)} · ${esc(d.desc || d.type)}</small><small>${d.alt_ft === 'ground' ? 'no solo' : fmt(d.alt_ft) + ' pés'} · ${fmt(Math.round(d.speed_kt || 0))} nós · rumo ${Math.round(d.heading || 0)}°</small>` },
  { key: 'hazards', label: 'Desastres', color: '#ffd23f', r: (d) => ({ Red: 9, Orange: 7 }[d.level] || 5),
    c: (d) => ({ Red: '#ff5a4d', Orange: '#ff9a3c' }[d.level] || '#44d38a'),
    pop: (d) => `<span class="tag" style="--c:${{ Red: '#ff5a4d', Orange: '#ff9a3c' }[d.level] || '#44d38a'}">${esc(d.level)}</span><b>${esc(d.title)}</b><small>${esc(d.kind_label)} · ${esc(d.country)}</small><small>${esc(d.severity)}</small>${link(d.link, 'Relatório GDACS ↗')}` },
  { key: 'quakes', label: 'Terremotos', color: '#b48cff', r: (d) => Math.max(3, (d.mag || 2.5) * 1.6),
    pop: (d) => `<b>M${esc((d.mag || 0).toFixed(1))} · ${esc(d.place)}</b><small>${ago(d.at)} · profundidade ${fmt(Math.round(d.depth_km || 0))} km${d.tsunami ? ' · ⚠ alerta de tsunami' : ''}</small>${link(d.link, 'USGS ↗')}` },
  { key: 'events', label: 'Incêndios e tempestades', color: '#ff7a59', r: () => 4.5,
    c: (d) => ({ fire: '#ff7a59', volcano: '#ff5a4d', storm: '#5cc8ff', flood: '#3c8cff' }[d.kind] || '#ff7a59'),
    pop: (d) => `<b>${esc(d.title)}</b><small>${esc(d.kind_label)}${d.magnitude ? ' · ' + esc(d.magnitude) : ''} · ${ago(d.at)}</small>${link(d.link, 'Fonte ↗')}` },
  { key: 'outbreaks', label: 'Surtos', color: '#44d38a', r: () => 7,
    pop: (d) => `<b>${esc(d.disease)}</b><small>${esc(d.flag)} ${esc(d.country)} · OMS · ${ago(d.at)}</small>${link(d.link, 'Boletim da OMS ↗')}` },
  { key: 'cyber', label: 'Cibernético', color: '#e06bff', r: () => 6, pop: (d) => newsPop('cyber')(d) },
  { key: 'infra', label: 'Energia e abastecimento', color: '#ffb020', r: () => 6, pop: (d) => newsPop('infra')(d) },
  { key: 'news', label: 'Notícias por país', color: '#8d9aa5', r: (d) => Math.min(11, 4 + d.n), on: false,
    pop: (d) => `<b>${esc(d.flag)} ${esc(d.country)} · ${fmt(d.n)} manchete(s)</b><ul>${d.articles.map((a) => `<li>${link(a.link, esc(a.title))}<small>${esc(a.source)} · ${ago(a.at)}</small></li>`).join('')}</ul>${d.articles_locked ? `<small>🔒 mais ${fmt(d.articles_locked)} com acesso completo</small>` : ''}` },
];
const LAYER = Object.fromEntries(LAYERS.map((l) => [l.key, l]));

const SNAPSHOT = window.__SNAPSHOT__ || null;   // presente só no arquivo único (dist/atalaia-demo.html)
const LIVE = window.__LIVE__ || null;           // presente só no arquivo único ao vivo (dist/atalaia-ao-vivo.html)
const LOCAL = !!(SNAPSHOT || LIVE);             // sem servidor: não há login, chat nem conta
let feed = null;
let mode = 'none';           // 'none' | 'near' | 'plan'
let visible = null;          // Set com as camadas ligadas
let mapReady = false;

// ------------------------------------------------------------------ mapa
const hasGl = (() => { try { const c = document.createElement('canvas'); return !!(c.getContext('webgl2') || c.getContext('webgl')); } catch (e) { return false; } })();
// Mapas base sem chave de API. Todos funcionam com a página aberta direto do disco.
const ESRI = (svc) => [`https://server.arcgisonline.com/ArcGIS/rest/services/${svc}/MapServer/tile/{z}/{y}/{x}`];
const GIBS = (layer, date, ext) => [`https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/${layer}/default/${date}/GoogleMapsCompatible_Level8/{z}/{y}/{x}.${ext}`];
const ESRI_ATTR = 'Tiles © Esri e colaboradores', NASA_ATTR = 'Imagens NASA GIBS / EOSDIS';
const BASEMAPS = {
  dark: { label: 'Escuro', layers: [{ tiles: ESRI('Canvas/World_Dark_Gray_Base'), maxzoom: 16 }, { tiles: ESRI('Canvas/World_Dark_Gray_Reference'), maxzoom: 16 }], attribution: ESRI_ATTR },
  satellite: { label: 'Satélite', layers: [{ tiles: ESRI('World_Imagery'), maxzoom: 18, paint: { 'raster-brightness-max': 0.8 } }], attribution: ESRI_ATTR },
  streets: { label: 'Ruas', layers: [{ tiles: ESRI('World_Street_Map'), maxzoom: 18 }], attribution: ESRI_ATTR },
  topo: { label: 'Relevo', layers: [{ tiles: ESRI('World_Topo_Map'), maxzoom: 18 }], attribution: ESRI_ATTR },
  night: { label: 'Luzes noturnas (NASA)', layers: [{ tiles: GIBS('VIIRS_Black_Marble', '2016-01-01', 'png'), maxzoom: 8 }], attribution: NASA_ATTR },
  bluemarble: { label: 'Blue Marble (NASA)', layers: [{ tiles: GIBS('BlueMarble_ShadedRelief_Bathymetry', '2004-08-01', 'jpeg'), maxzoom: 8, paint: { 'raster-brightness-max': 0.75 } }], attribution: NASA_ATTR },
  simple: { label: 'Simples (sem internet)', layers: [] },
};
function setBasemap(id) {
  if (!BASEMAPS[id]) id = 'dark';
  for (let i = 0; i < 2; i++) { if (map.getLayer('base' + i)) map.removeLayer('base' + i); if (map.getSource('base' + i)) map.removeSource('base' + i); }
  BASEMAPS[id].layers.forEach((l, i) => {
    map.addSource('base' + i, { type: 'raster', tileSize: 256, maxzoom: l.maxzoom, tiles: l.tiles, attribution: BASEMAPS[id].attribution });
    map.addLayer({ id: 'base' + i, type: 'raster', source: 'base' + i, paint: l.paint || {} }, 'near-fill');   // abaixo dos marcadores
  });
  ls.set('atl_base', id);
}
$('#basemap').innerHTML = Object.entries(BASEMAPS).map(([k, b]) => `<option value="${k}">${b.label}</option>`).join('');
$('#basemap').value = BASEMAPS[ls.get('atl_base')] ? ls.get('atl_base') : 'dark';
$('#basemap').addEventListener('change', (e) => { if (mapReady) setBasemap(e.target.value); });

let map = null;
if (hasGl && window.maplibregl) {
  map = new maplibregl.Map({
    container: 'map', center: [20, 22], zoom: 2.1, attributionControl: { compact: true },
    style: {
      version: 8, projection: { type: ls.get('atl_proj') || 'globe' },
      // O contorno dos países vem embutido (world.json), então o globo aparece mesmo se os tiles falharem.
      sources: { world: { type: 'geojson', data: window.__WORLD__ || '/world.json' } },
      layers: [{ id: 'bg', type: 'background', paint: { 'background-color': '#070b0f' } },
        { id: 'land', type: 'fill', source: 'world', paint: { 'fill-color': '#18222b' } },
        { id: 'borders', type: 'line', source: 'world', paint: { 'line-color': '#34434f', 'line-width': 0.7 } }],
    },
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
  map.on('load', () => {
    const empty = { type: 'FeatureCollection', features: [] };
    map.addSource('near', { type: 'geojson', data: empty });
    map.addLayer({ id: 'near-fill', type: 'fill', source: 'near', paint: { 'fill-color': '#5cc8ff', 'fill-opacity': 0.08 } });
    map.addLayer({ id: 'near-line', type: 'line', source: 'near', paint: { 'line-color': '#5cc8ff', 'line-width': 1.5 } });
    // de trás para a frente: as camadas mais importantes ficam por cima
    for (const l of [...LAYERS].reverse()) {
      map.addSource(l.key, { type: 'geojson', data: empty });
      map.addLayer({ id: l.key, type: 'circle', source: l.key, paint: {
        'circle-radius': ['get', 'r'], 'circle-color': ['get', 'c'], 'circle-opacity': 0.85,
        'circle-stroke-width': 1, 'circle-stroke-color': '#05080a' } });
      map.on('click', l.key, (e) => {
        if (mode !== 'none') return;
        const d = feed.map[l.key][e.features[0].properties.i];
        if (d) new maplibregl.Popup({ maxWidth: '300px' }).setLngLat([d.lng, d.lat]).setHTML(`<div class="pop">${l.pop(d)}</div>`).addTo(map);
      });
      map.on('mouseenter', l.key, () => { if (mode === 'none') map.getCanvas().style.cursor = 'pointer'; });
      map.on('mouseleave', l.key, () => { map.getCanvas().style.cursor = ''; });
    }
    map.addSource('plan-line', { type: 'geojson', data: empty });
    map.addSource('plan-pts', { type: 'geojson', data: empty });
    map.addLayer({ id: 'plan-line', type: 'line', source: 'plan-line', paint: { 'line-color': '#ffb020', 'line-width': 2.5, 'line-dasharray': [2, 1.5] } });
    map.addLayer({ id: 'plan-pts', type: 'circle', source: 'plan-pts', paint: { 'circle-radius': 8, 'circle-color': '#ffb020', 'circle-stroke-width': 2, 'circle-stroke-color': '#fff' } });
    setBasemap($('#basemap').value);
    mapReady = true;
    if (feed) drawMap();
    drawPlan(); drawNear();
  });
  map.on('click', (e) => {
    const p = { lat: e.lngLat.lat, lng: e.lngLat.lng };
    if (mode === 'near') { setMode('none'); near.center = p; drawNear(); }
    else if (mode === 'plan') addWaypoint(p);
  });
} else {
  $('#map').innerHTML = '<p style="padding:24px;color:#8d9aa5">Seu navegador não tem WebGL ativo, então o globo não pode ser desenhado. As listas e painéis abaixo continuam funcionando.</p>';
}

function setMode(m) {
  mode = m;
  const hint = $('#mapHint');
  hint.hidden = m === 'none';
  hint.textContent = m === 'near' ? 'Clique no mapa para escolher o ponto' : m === 'plan' ? 'Modo plano: clique no mapa para adicionar um ponto' : '';
  if (map) map.getCanvas().style.cursor = m === 'none' ? '' : 'crosshair';
  $('#planBtn').classList.toggle('on', m === 'plan');
}

function drawMap() {
  if (!mapReady) return;
  for (const l of LAYERS) {
    const items = feed.map[l.key] || [];
    map.getSource(l.key).setData({ type: 'FeatureCollection', features: items.map((d, i) => ({
      type: 'Feature', geometry: { type: 'Point', coordinates: [d.lng, d.lat] },
      properties: { i, r: l.r(d), c: l.c ? l.c(d) : l.color } })) });
    map.setLayoutProperty(l.key, 'visibility', visible.has(l.key) ? 'visible' : 'none');
  }
}

function drawChips() {
  $('#chips').innerHTML = LAYERS.filter((l) => !(feed.sources[l.key] || {}).unavailable).map((l) => {
    const n = (feed.map[l.key] || []).length, locked = feed.locked[l.key] || 0;
    return `<button class="chip ${visible.has(l.key) ? '' : 'off'}" data-k="${l.key}" style="--c:${l.color}" aria-pressed="${visible.has(l.key)}"><i></i>${esc(l.label)} <span>${fmt(n)}</span>${locked ? `<span class="lock" title="Disponível com acesso completo">+${fmt(locked)} 🔒</span>` : ''}</button>`;
  }).join('');
}
$('#chips').addEventListener('click', (e) => {
  const b = e.target.closest('.chip'); if (!b) return;
  const k = b.dataset.k;
  if (visible.has(k)) visible.delete(k); else visible.add(k);
  ls.set('atl_layers', JSON.stringify([...visible]));
  drawChips(); drawMap(); drawNear();
});
$('#proj').addEventListener('click', () => {
  if (!map) return;
  const globe = map.getProjection().type !== 'globe';
  map.setProjection({ type: globe ? 'globe' : 'mercator' });
  ls.set('atl_proj', globe ? 'globe' : 'mercator');
  $('#proj').textContent = globe ? '🗺 Mapa plano' : '🌐 Globo';
});
if (ls.get('atl_proj') === 'mercator') $('#proj').textContent = '🌐 Globo';

// ------------------------------------------------------------------ painéis
function drawThreat() {
  const t = feed.threat, box = $('#threat');
  box.style.setProperty('--lv', LV[t.level]);
  $('#lvlNum').textContent = t.level;
  $('#lvlLabel').textContent = t.label;
  $('#lvlReasons').innerHTML = t.reasons.map((r) => `<li>${esc(r)}</li>`).join('');
  $('#updated').textContent = (LIVE ? '● Ao vivo · atualizado ' : 'Atualizado ') + new Date(feed.generated_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}
function drawHeadlines() {
  const all = feed.headlines || [], h = showAll ? all : all.slice(0, 15);
  $('#headlines').innerHTML = (h.length ? h.map((n) => `<div class="it">${n.cat !== 'general' ? `<span class="tag" style="--c:${({ attack: '#ff5a4d', unrest: '#ff9a3c', outbreak: '#44d38a', cyber: '#e06bff', infra: '#ffb020' })[n.cat]}">${CAT_LABEL[n.cat]}</span>` : ''}${link(n.link, esc(n.title))}<small>${n.country ? esc(n.flag) + ' ' + esc(n.country) + ' · ' : ''}${esc(n.source)} · ${ago(n.at)}</small></div>`).join('') : '<p class="dim">Carregando manchetes…</p>')
    + (all.length > h.length ? `<p><button class="btn btn-ghost" id="showAll">Mostrar mais ${fmt(all.length - h.length)} manchetes</button></p>` : '')
    + (feed.headlines_locked ? `<div class="lockbox">🔒 Mais ${fmt(feed.headlines_locked)} manchetes com acesso completo. <a href="#acesso">Liberar acesso</a></div>` : '');
}
let showAll = false;
$('#headlines').addEventListener('click', (e) => { if (e.target.id === 'showAll') { showAll = true; drawHeadlines(); } });
function drawSpace() {
  const s = feed.space;
  if (!s) { $('#space').innerHTML = '<p class="dim">Fonte indisponível no momento.</p>'; return; }
  $('#space').innerHTML = `<div class="big">Kp ${esc(s.kp)}</div><div class="dim">${esc(s.label)} · máximo em 24h: Kp ${esc(s.kp_max_24h)}</div>
    <div class="spark" title="Índice Kp, últimas 72h">${s.series.map((p) => `<i style="height:${Math.max(4, (p.kp / 9) * 100)}%;background:${p.kp >= 7 ? '#ff5a4d' : p.kp >= 5 ? '#ff9a3c' : '#5cc8ff'}"></i>`).join('')}</div>
    <p class="dim" style="margin-top:8px">Kp 5 ou mais indica tempestade geomagnética: pode afetar rádio, GPS e, em casos fortes, redes elétricas.</p>`;
}
function drawWeather() {
  const w = feed.weather;
  if (!w) { $('#weather').innerHTML = '<p class="dim">Fonte indisponível no momento.</p>'; return; }
  $('#weather').innerHTML = `<div class="big">${fmt(w.total)}</div><div class="dim">alertas severos ativos · ${fmt(w.extreme)} extremos</div>`
    + w.by_event.map(([ev, n]) => `<div class="kv"><span>${esc(ev)}</span><span>${fmt(n)}</span></div>`).join('')
    + (feed.unlocked ? w.items.slice(0, 8).map((a) => `<div class="kv"><span>${esc(a.event)}</span><span>${esc(a.area.slice(0, 60))}</span></div>`).join('') : '<div class="lockbox">🔒 Lista detalhada por região com acesso completo.</div>');
}
function drawQuakes() {
  const q = (feed.map.quakes || []).slice(0, 6);
  $('#quakeList').innerHTML = q.length ? q.map((d) => `<div class="kv"><span><b>M${esc((d.mag || 0).toFixed(1))}</b> ${esc(d.place)}</span><span>${ago(d.at)}</span></div>`).join('') : '<p class="dim">Nenhum terremoto relevante.</p>';
}
function drawSources() {
  const names = { quakes: 'USGS', hazards: 'GDACS', events: 'NASA EONET', aircraft: 'ADS-B', space: 'NOAA SWPC', weather: 'NWS', outbreaks: 'OMS', news: 'Notícias' };
  $('#sources').innerHTML = Object.entries(feed.sources).map(([k, s]) => `<span class="src ${s.ok ? 'ok' : s.unavailable ? 'na' : 'bad'}" title="${s.ok ? 'Atualizado ' + ago(s.at) : s.unavailable ? esc(s.error) : 'Falhou ' + ago(s.at) + (s.stale ? ' · mostrando o último dado bom' : '')}">${esc(names[k] || k)}</span>`).join('');
}
function drawOffer() {
  const o = feed.offer;
  const cards = [['Mensal', o.monthly_price, o.monthly_link, 'por mês · cancele quando quiser'], ['Anual', o.yearly_price, o.yearly_link, 'por ano'], ['Vitalício', o.lifetime_price, o.lifetime_link, 'pagamento único']]
    .filter((c) => c[1] && /^https:\/\//.test(c[2]));
  $('#plans').innerHTML = cards.length
    ? cards.map(([name, price, url, note]) => `<div class="plan-card"><h3>${name}</h3><div class="big">${esc(price)}</div><div class="dim">${note}</div><a class="btn btn-cta" href="${safeUrl(url)}" target="_blank" rel="noopener">Assinar ${name.toLowerCase()}</a></div>`).join('')
    : `<div class="lockbox">Os códigos de acesso são emitidos pelo administrador deste painel.${o.contact ? ' Contato: ' + esc(o.contact) : ''}</div>`;
  $('#trialBox').hidden = !(o.trial_hours > 0);
  $('#trialTxt').textContent = `Acesso completo por ${o.trial_hours} hora${o.trial_hours === 1 ? '' : 's'}, sem cadastro. Um teste por dispositivo.`;
}
let trialTick = null;
function drawTrial() {
  clearInterval(trialTick);
  const bar = $('#trialBar');
  if (!feed.trial_ends) { bar.hidden = true; return; }
  const tick = () => {
    const left = Math.max(0, new Date(feed.trial_ends) - Date.now());
    bar.textContent = `Teste grátis: restam ${Math.floor(left / 60000)} min ${String(Math.floor(left / 1000) % 60).padStart(2, '0')} s`;
    if (!left) { clearInterval(trialTick); load(); }
  };
  bar.hidden = false; tick(); trialTick = setInterval(tick, 1000);
}

// ------------------------------------------------------------------ perto de mim
const near = { center: null };
function circle(c, radiusKm) {
  const pts = [], R = 6371, lat = c.lat * Math.PI / 180, lng = c.lng * Math.PI / 180, d = radiusKm / R;
  for (let i = 0; i <= 72; i++) {
    const b = (i * 5) * Math.PI / 180;
    const la = Math.asin(Math.sin(lat) * Math.cos(d) + Math.cos(lat) * Math.sin(d) * Math.cos(b));
    const lo = lng + Math.atan2(Math.sin(b) * Math.sin(d) * Math.cos(lat), Math.cos(d) - Math.sin(lat) * Math.sin(la));
    pts.push([lo * 180 / Math.PI, la * 180 / Math.PI]);
  }
  return { type: 'Feature', geometry: { type: 'Polygon', coordinates: [pts] }, properties: {} };
}
function drawNear() {
  const out = $('#nearOut'), c = near.center, r = +$('#nearKm').value;
  $('#nearClear').hidden = !c;
  if (mapReady) map.getSource('near').setData({ type: 'FeatureCollection', features: c ? [circle(c, r)] : [] });
  if (!c || !feed) { out.innerHTML = ''; return; }
  const found = [];
  for (const l of LAYERS) for (const d of feed.map[l.key] || []) {
    const dist = km(c, d);
    if (dist <= r) found.push({ l, d, dist });
  }
  found.sort((a, b) => a.dist - b.dist);
  const title = (f) => f.d.title || f.d.callsign || (f.d.country ? `${f.d.country}: ${f.d.n} manchete(s)` : f.d.id);
  out.innerHTML = `<p><b>${fmt(found.length)}</b> item(ns) em um raio de ${fmt(r)} km de ${c.lat.toFixed(2)}, ${c.lng.toFixed(2)}.</p>`
    + found.slice(0, 40).map((f) => `<div class="near-it"><span><span class="tag" style="--c:${f.l.color}">${esc(f.l.label)}</span>${esc(title(f))}</span><span>${fmt(Math.round(f.dist))} km</span></div>`).join('')
    + (feed.unlocked ? '' : '<div class="lockbox">🔒 Você está vendo só a amostra gratuita de cada camada, então podem existir eventos próximos que não aparecem aqui. <a href="#acesso">Liberar acesso</a></div>');
}
$('#nearGeo').addEventListener('click', () => {
  if (!navigator.geolocation) { $('#nearOut').innerHTML = '<p class="msg err">Seu navegador não oferece localização. Use "Escolher no mapa".</p>'; return; }
  $('#nearOut').innerHTML = '<p class="dim">Obtendo sua localização…</p>';
  navigator.geolocation.getCurrentPosition((p) => {
    near.center = { lat: p.coords.latitude, lng: p.coords.longitude };
    drawNear();
    if (map) map.flyTo({ center: [near.center.lng, near.center.lat], zoom: 4 });
  }, () => { $('#nearOut').innerHTML = '<p class="msg err">Não foi possível obter a localização. Use "Escolher no mapa".</p>'; }, { timeout: 10000 });
});
$('#nearPick').addEventListener('click', () => { if (!map) return; setMode('near'); $('#map').scrollIntoView({ block: 'center' }); });
$('#nearKm').addEventListener('change', drawNear);
$('#nearClear').addEventListener('click', () => { near.center = null; drawNear(); });

// ------------------------------------------------------------------ modo plano (salvo só neste navegador)
const WP = { base: '🏠 Base', cache: '📦 Esconderijo', meet: '🤝 Ponto de encontro', water: '💧 Água', exit: '🚗 Rota de saída' };
let wps = [];
try { const j = JSON.parse(ls.get('atl_plan') || '[]'); if (Array.isArray(j)) wps = j.filter((w) => WP[w.type] && isFinite(w.lat) && isFinite(w.lng)); } catch (e) {}
function addWaypoint(p) { wps.push({ type: $('#wpType').value, lat: +p.lat.toFixed(5), lng: +p.lng.toFixed(5) }); drawPlan(); }
function drawPlan() {
  ls.set('atl_plan', JSON.stringify(wps));
  let total = 0;
  $('#wpList').innerHTML = wps.map((w, i) => {
    const leg = i ? km(wps[i - 1], w) : 0; total += leg;
    return `<li>${WP[w.type]} · ${w.lat.toFixed(4)}, ${w.lng.toFixed(4)}${i ? ` · <span class="dim">+${fmt(Math.round(leg))} km (total ${fmt(Math.round(total))} km)</span>` : ''} <button data-i="${i}" aria-label="Remover ponto">✕</button></li>`;
  }).join('') || '<li class="dim" style="list-style:none">Nenhum ponto ainda.</li>';
  if (!mapReady) return;
  const show = !$('#plan').hidden;
  map.getSource('plan-pts').setData({ type: 'FeatureCollection', features: show ? wps.map((w) => ({ type: 'Feature', geometry: { type: 'Point', coordinates: [w.lng, w.lat] }, properties: {} })) : [] });
  map.getSource('plan-line').setData({ type: 'FeatureCollection', features: show && wps.length > 1 ? [{ type: 'Feature', geometry: { type: 'LineString', coordinates: wps.map((w) => [w.lng, w.lat]) }, properties: {} }] : [] });
}
$('#wpList').addEventListener('click', (e) => { const b = e.target.closest('button'); if (b) { wps.splice(+b.dataset.i, 1); drawPlan(); } });
$('#planBtn').addEventListener('click', () => {
  if (!feed || !feed.unlocked) { location.hash = '#acesso'; return; }
  const open = $('#plan').hidden;
  $('#plan').hidden = !open;
  setMode(open && map ? 'plan' : 'none');
  drawPlan();
});
function download(name, text, type) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([text], { type })); a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}
$('#gpx').addEventListener('click', () => {
  if (!wps.length) return;
  const pt = (tag, w) => `<${tag} lat="${w.lat}" lon="${w.lng}"><name>${esc(WP[w.type].replace(/^\S+\s/, ''))}</name></${tag}>`;
  download('atalaia-plano.gpx', `<?xml version="1.0" encoding="UTF-8"?>\n<gpx version="1.1" creator="Atalaia" xmlns="http://www.topografix.com/GPX/1/1">\n${wps.map((w) => pt('wpt', w)).join('\n')}\n<rte><name>Plano</name>${wps.map((w) => pt('rtept', w)).join('')}</rte>\n</gpx>\n`, 'application/gpx+xml');
});
$('#backup').addEventListener('click', () => download('atalaia-plano.json', JSON.stringify(wps, null, 1), 'application/json'));
$('#restore').addEventListener('change', async (e) => {
  try {
    const j = JSON.parse(await e.target.files[0].text());
    if (Array.isArray(j)) { wps = j.filter((w) => WP[w.type] && isFinite(w.lat) && isFinite(w.lng)).slice(0, 200).map((w) => ({ type: w.type, lat: +w.lat, lng: +w.lng })); drawPlan(); }
  } catch (err) { alert('Arquivo de backup inválido.'); }
  e.target.value = '';
});
$('#wpClear').addEventListener('click', () => { if (wps.length && confirm('Apagar todos os pontos deste navegador?')) { wps = []; drawPlan(); } });

// ------------------------------------------------------------------ chat
const chat = { last: 0, timer: null, name: null };
async function post(url, body) {
  if (LOCAL) return { ok: false, error: 'Indisponível sem o servidor.' };
  try {
    const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) });
    return await r.json();
  } catch (e) { return { ok: false, error: 'Não foi possível falar com o servidor.' }; }
}
async function chatPoll() {
  try {
    const j = await (await fetch('/chat?after=' + chat.last)).json();
    if (!j.ok) return;
    chat.name = j.me;
    $('#nameForm').hidden = !!j.me; $('#chatForm').hidden = !j.me;
    const log = $('#chatLog'), stick = log.scrollTop + log.clientHeight >= log.scrollHeight - 30;
    for (const m of j.messages) {
      const p = document.createElement('p'), b = document.createElement('b'), t = document.createElement('time');
      b.textContent = m.name; t.textContent = new Date(m.at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
      p.append(b, t, document.createElement('br'), document.createTextNode(m.text));   // texto puro: nada vira HTML
      log.append(p); chat.last = Math.max(chat.last, m.id);
    }
    if (!log.childElementCount) log.innerHTML = '<p class="dim" id="chatEmpty">Ninguém escreveu ainda. Comece a conversa.</p>';
    else if (j.messages.length) { const e = $('#chatEmpty'); if (e) e.remove(); if (stick) log.scrollTop = log.scrollHeight; }
  } catch (e) {}
}
function chatSync() {
  const on = feed && feed.unlocked && !LOCAL;
  if (on && !chat.timer) { chatPoll(); chat.timer = setInterval(() => { if (!document.hidden) chatPoll(); }, 5000); }
  if (!on && chat.timer) { clearInterval(chat.timer); chat.timer = null; chat.last = 0; $('#chatLog').innerHTML = ''; }
}
$('#nameForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const j = await post('/chat/name', { name: $('#chatName').value });
  $('#chatMsg').className = 'msg ' + (j.ok ? 'ok' : 'err'); $('#chatMsg').textContent = j.ok ? '' : j.error;
  if (j.ok) chatPoll();
});
$('#chatForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const text = $('#chatText').value.trim(); if (!text) return;
  const j = await post('/chat', { text });
  $('#chatMsg').className = 'msg ' + (j.ok ? 'ok' : 'err'); $('#chatMsg').textContent = j.ok ? '' : j.error;
  if (j.ok) { $('#chatText').value = ''; chatPoll(); }
});

// ------------------------------------------------------------------ acesso
$('#unlockForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const m = $('#unlockMsg');
  const j = await post('/unlock', { code: $('#code').value });
  m.className = 'msg ' + (j.ok ? 'ok' : 'err'); m.textContent = j.ok ? 'Acesso liberado. Carregando…' : j.error;
  if (j.ok) { await load(); window.scrollTo({ top: 0, behavior: 'smooth' }); }
});
$('#trialBtn').addEventListener('click', async () => {
  const m = $('#trialMsg');
  const j = await post('/trial');
  m.className = 'msg ' + (j.ok ? 'ok' : 'err'); m.textContent = j.ok ? 'Teste iniciado.' : j.error;
  if (j.ok) { await load(); window.scrollTo({ top: 0, behavior: 'smooth' }); }
});
$('#logout').addEventListener('click', async () => {
  await post('/logout');
  if (window.caches) { try { await caches.delete('atl-data-1'); } catch (e) {} }
  $('#plan').hidden = true; setMode('none');
  load();
});

// ------------------------------------------------------------------ ciclo
async function load() {
  let j = LIVE ? LIVE.feed() : SNAPSHOT;
  if (!j) { try { j = await (await fetch('/feed', { cache: 'no-store' })).json(); } catch (e) { return; } }
  feed = j;
  document.body.classList.toggle('unlocked', !!j.unlocked);
  if (!visible) {
    let saved = null;
    try { saved = JSON.parse(ls.get('atl_layers')); } catch (e) {}
    const def = Array.isArray(saved) ? saved : Array.isArray(j.default_layers) ? j.default_layers : LAYERS.filter((l) => l.on !== false).map((l) => l.key);
    visible = new Set(def.filter((k) => LAYER[k]));
  }
  drawThreat(); drawChips(); drawMap(); drawHeadlines(); drawSpace(); drawWeather(); drawQuakes(); drawSources(); drawOffer(); drawTrial(); drawNear(); chatSync();
}
load();
if (LOCAL) {
  $('#chat').hidden = true; $('#logout').hidden = true;
  document.querySelectorAll('.top nav a[href="#chat"]').forEach((a) => { a.hidden = true; });
}
if (LIVE) {
  // arquivo único ao vivo: os coletores rodam nesta página e redesenham a tela a cada fonte que chega
  let t = null;
  LIVE.onUpdate = () => { clearTimeout(t); t = setTimeout(load, 300); };
  setInterval(load, 30000);   // mantém os "há X min" em dia
} else if (SNAPSHOT) {
  // arquivo único de demonstração: dados congelados no momento em que foi gerado
  const bar = $('#trialBar');
  bar.hidden = false;
  bar.textContent = 'Demonstração offline: dados congelados em ' + new Date(SNAPSHOT.generated_at).toLocaleString('pt-BR') + '. A versão ao vivo roda no servidor.';
} else {
  setInterval(() => { if (!document.hidden) load(); }, 60000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) load(); });
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});
}
