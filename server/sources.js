'use strict';
// Coletores: cada um busca uma fonte pública e devolve itens normalizados.
// Se uma fonte falhar, o último resultado bom continua sendo servido.
const { locate, flag, jitter } = require('./geo');

const UA = process.env.HTTP_USER_AGENT || 'atalaia-threat-map/1.0';

async function get(url, { json = true, timeout = 25000, tries = 2 } = {}) {
  let lastErr;
  for (let i = 0; i < tries; i++) {
    try {
      const r = await fetch(url, {
        headers: { 'User-Agent': UA, Accept: json ? 'application/json, application/geo+json' : '*/*' },
        signal: AbortSignal.timeout(timeout),
      });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return json ? await r.json() : await r.text();
    } catch (e) {
      lastErr = e;
      await new Promise((ok) => setTimeout(ok, 1500));
    }
  }
  throw lastErr;
}

const num = (v) => (Number.isFinite(+v) ? +v : null);
const okPos = (lat, lng) => Number.isFinite(lat) && Number.isFinite(lng) && Math.abs(lat) <= 90 && Math.abs(lng) <= 180;
const iso = (d) => { const t = new Date(d); return isNaN(t) ? null : t.toISOString(); };
const hoursAgo = (d) => (Date.now() - new Date(d).getTime()) / 36e5;

// ---------- Terremotos (USGS) ----------
async function quakes() {
  const d = await get('https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson');
  return d.features.map((f) => {
    const [lng, lat, depth] = f.geometry.coordinates;
    return {
      id: f.id, title: f.properties.title, mag: num(f.properties.mag), place: f.properties.place,
      depth_km: num(depth), tsunami: !!f.properties.tsunami, at: iso(f.properties.time),
      link: f.properties.url, lat, lng, source: 'USGS',
    };
  }).filter((q) => okPos(q.lat, q.lng)).sort((a, b) => (b.mag || 0) - (a.mag || 0));
}

// ---------- Desastres (GDACS) ----------
const GDACS_KIND = { EQ: 'Terremoto', TC: 'Ciclone tropical', FL: 'Enchente', VO: 'Vulcão', WF: 'Incêndio florestal', DR: 'Seca' };
async function hazards() {
  const d = await get('https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH?eventlist=EQ;TC;FL;VO;WF;DR&alertlevel=Green;Orange;Red');
  const rank = { Red: 3, Orange: 2, Green: 1 };
  return (d.features || []).map((f) => {
    const p = f.properties || {};
    const [lng, lat] = (f.geometry && f.geometry.coordinates) || [];
    return {
      id: p.eventtype + p.eventid, kind: p.eventtype, kind_label: GDACS_KIND[p.eventtype] || p.eventtype,
      title: p.name || p.description, country: p.country || '', level: p.alertlevel || 'Green',
      severity: (p.severitydata && p.severitydata.severitytext) || '', at: iso(p.fromdate), until: iso(p.todate),
      link: p.url && p.url.report, lat, lng, source: 'GDACS',
    };
  }).filter((h) => okPos(h.lat, h.lng) && (h.level !== 'Green' || hoursAgo(h.at) < 96))
    .sort((a, b) => rank[b.level] - rank[a.level]);
}

// ---------- Eventos naturais (NASA EONET): incêndios, vulcões, tempestades ----------
const EONET_KIND = { wildfires: ['fire', 'Incêndio'], volcanoes: ['volcano', 'Vulcão'], severeStorms: ['storm', 'Tempestade severa'], floods: ['flood', 'Enchente'] };
async function events() {
  const d = await get('https://eonet.gsfc.nasa.gov/api/v3/events?status=open&days=20&limit=600', { timeout: 40000 });
  const out = [];
  for (const e of d.events || []) {
    const cat = (e.categories[0] || {}).id;
    if (!EONET_KIND[cat]) continue;
    const g = [...(e.geometry || [])].reverse().find((x) => x.type === 'Point');
    if (!g) continue;
    const [lng, lat] = g.coordinates;
    if (!okPos(lat, lng)) continue;
    out.push({
      id: e.id, kind: EONET_KIND[cat][0], kind_label: EONET_KIND[cat][1], title: e.title, at: iso(g.date),
      magnitude: g.magnitudeValue ? `${g.magnitudeValue} ${g.magnitudeUnit || ''}`.trim() : '',
      link: (e.sources[0] || {}).url || e.link, lat, lng, source: 'NASA EONET',
    });
  }
  return out.sort((a, b) => new Date(b.at) - new Date(a.at));
}

// ---------- Aeronaves militares (ADS-B aberto) ----------
const AC_ROLES = [
  [/^(R135|RC135|E3TF|E3CF|E3|E6|E4|E8|U2|RQ4|Q4|P8|P3|E2|E7|RC12|MQ9|Q9)/, 'recon', 'Reconhecimento / comando'],
  [/^(K35R|K35E|KC135|K46|KC10|A332|MRTT|KC30|A30B)/, 'tanker', 'Reabastecimento'],
  [/^(B52|B1|B2|B21|TU95|TU160)/, 'bomber', 'Bombardeiro'],
  [/^(C17|C5M|C5|C130|C30J|A400|IL76|C2|AN12|AN124|C160)/, 'transport', 'Transporte'],
  [/^(F15|F16|F18|F22|F35|EUFI|TYPH|RFAL|SU|MIG|A10|GRIP)/, 'fighter', 'Caça'],
  [/^(H60|H47|H64|UH60|CH47|AH64|V22|H53|EC45|NH90|LYNX)/, 'helo', 'Helicóptero'],
];
async function aircraft() {
  // duas fontes abertas com o mesmo formato; a segunda cobre quando a primeira cai
  let d, source = 'adsb.fi';
  try { d = await get('https://opendata.adsb.fi/api/v2/mil'); }
  catch (e) { d = await get('https://api.adsb.lol/v2/mil', { tries: 3 }); source = 'adsb.lol'; }
  return (d.ac || []).map((a) => {
    const type = String(a.t || '').toUpperCase();
    const role = AC_ROLES.find((r) => r[0].test(type));
    return {
      id: a.hex, callsign: String(a.flight || '').trim(), type, desc: a.desc || '',
      role: role ? role[1] : 'other', role_label: role ? role[2] : 'Outro militar',
      alt_ft: typeof a.alt_baro === 'number' ? a.alt_baro : null, speed_kt: num(a.gs), heading: num(a.track),
      lat: num(a.lat), lng: num(a.lon), reg: a.r || '', source,
    };
  }).filter((a) => okPos(a.lat, a.lng) && a.alt_ft !== null)
    .sort((a, b) => (a.role === 'other') - (b.role === 'other'));
}

// ---------- Clima espacial (NOAA SWPC) ----------
async function space() {
  const d = await get('https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json');
  const rows = Array.isArray(d[0]) ? d.slice(1).map((r) => ({ time_tag: r[0], Kp: r[1] })) : d;
  const series = rows.map((r) => ({ at: iso(String(r.time_tag).replace(' ', 'T') + (/Z$/.test(r.time_tag) ? '' : 'Z')), kp: num(r.Kp) })).filter((r) => r.kp !== null);
  const last = series[series.length - 1] || { kp: 0 };
  const max24 = Math.max(0, ...series.slice(-8).map((r) => r.kp));
  const label = (k) => (k >= 8 ? 'Tempestade severa' : k >= 7 ? 'Tempestade forte' : k >= 6 ? 'Tempestade moderada' : k >= 5 ? 'Tempestade fraca' : k >= 4 ? 'Ativo' : 'Calmo');
  return { kp: last.kp, kp_max_24h: max24, label: label(max24), at: last.at, series: series.slice(-24), source: 'NOAA SWPC' };
}

// ---------- Alertas severos nos EUA (NWS) ----------
async function weather() {
  const d = await get('https://api.weather.gov/alerts/active?status=actual&severity=Extreme,Severe');
  const list = (d.features || []).map((f) => f.properties).map((p) => ({
    event: p.event, area: p.areaDesc, severity: p.severity, headline: p.headline || '', at: iso(p.sent), until: iso(p.expires),
  }));
  const byEvent = {};
  for (const a of list) byEvent[a.event] = (byEvent[a.event] || 0) + 1;
  return {
    total: list.length,
    extreme: list.filter((a) => a.severity === 'Extreme').length,
    by_event: Object.entries(byEvent).sort((a, b) => b[1] - a[1]).slice(0, 8),
    items: list.sort((a, b) => (b.severity === 'Extreme') - (a.severity === 'Extreme')).slice(0, 40),
    source: 'NWS',
  };
}

// ---------- Surtos (OMS / Disease Outbreak News) ----------
async function outbreaks() {
  const d = await get('https://www.who.int/api/news/diseaseoutbreaknews?$top=40&$orderby=PublicationDate%20desc&$select=Title,PublicationDate,ItemDefaultUrl');
  const out = [];
  for (const v of d.value || []) {
    if (hoursAgo(v.PublicationDate) > 24 * 120) continue;
    const title = String(v.Title || '').trim();
    const c = locate(title);
    if (!c) continue;
    const [dy, dx] = jitter(title, 1.2);
    out.push({
      id: v.ItemDefaultUrl, title, disease: title.split(/\s[–-]\s/)[0], country: c.name, flag: flag(c.iso),
      at: iso(v.PublicationDate), link: 'https://www.who.int/emergencies/disease-outbreak-news/item' + v.ItemDefaultUrl,
      lat: c.lat + dy, lng: c.lng + dx, source: 'OMS',
    });
  }
  return out;
}

// ---------- Notícias (RSS) ----------
const FEEDS = [
  ['BBC', 'https://feeds.bbci.co.uk/news/world/rss.xml'],
  ['Al Jazeera', 'https://www.aljazeera.com/xml/rss/all.xml'],
  ['The Guardian', 'https://www.theguardian.com/world/rss'],
  ['DW', 'https://rss.dw.com/rdf/rss-en-world'],
  ['France 24', 'https://www.france24.com/en/rss'],
].concat((process.env.EXTRA_FEEDS || '').split(',').filter(Boolean).map((u) => [new URL(u).hostname.replace(/^www\./, ''), u]));

const ENT = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ' };
const decode = (s) => String(s || '')
  .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, '$1')
  .replace(/<[^>]+>/g, ' ')
  .replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
  .replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(+n))
  .replace(/&([a-z]+);/gi, (m, n) => ENT[n.toLowerCase()] ?? m)
  .replace(/\s+/g, ' ').trim();
const tag = (xml, name) => { const m = new RegExp(`<${name}(?:\\s[^>]*)?>([\\s\\S]*?)</${name}>`, 'i').exec(xml); return m ? decode(m[1]) : ''; };

function parseRss(xml, source) {
  const items = [];
  const re = /<item[\s>][\s\S]*?<\/item>/gi;
  let m;
  while ((m = re.exec(xml))) {
    const x = m[0];
    const title = tag(x, 'title');
    const link = tag(x, 'link');
    const at = iso(tag(x, 'pubDate') || tag(x, 'dc:date'));
    if (!title || !/^https?:\/\//.test(link)) continue;
    items.push({ title, link, at: at || new Date().toISOString(), summary: tag(x, 'description').slice(0, 240), source });
  }
  return items;
}

// Categorias por palavras-chave no título (simples e transparente; fácil de ajustar).
const CATS = [
  ['unrest', /\b(protest(s|ers)?|riots?|clashes|unrest|coup|uprising|demonstrat(ion|ors)|crackdown|curfew|state of emergency|general strike)\b/i],
  ['outbreak', /\b(outbreak|ebola|cholera|measles|mpox|bird flu|avian flu|epidemic|pandemic|quarantine)\b/i],
  ['cyber', /\b(cyber ?attacks?|hack(ed|ers|ing)?|ransomware|data breach|malware)\b/i],
  ['infra', /\b(blackout|power (cut|outage)s?|grid (failure|collapse)|fuel shortages?|shortages?|pipeline|supply chain|food prices|famine)\b/i],
  ['attack', /\b(air ?strikes?|strikes? (on|in|hits?|kills?)|missiles?|shelling|shelled|bomb(ing|ed|s)?|drone (attack|strike)s?|rockets?|explosions?|gunm[ae]n|shooting|killed in|attack(s|ed)? (on|in|by)|ambush|invasion|offensive|ceasefire|troops|war on|at war|warplanes?)\b/i],
];
const classify = (t) => (CATS.find((c) => c[1].test(t)) || ['general'])[0];

async function news() {
  const results = await Promise.allSettled(FEEDS.map(([name, url]) => get(url, { json: false }).then((x) => parseRss(x, name))));
  if (results.every((r) => r.status === 'rejected')) throw results[0].reason;
  const seen = new Set();
  const all = [];
  for (const r of results) {
    if (r.status !== 'fulfilled') continue;
    for (const it of r.value) {
      const key = it.title.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim().slice(0, 70);
      if (seen.has(key) || hoursAgo(it.at) > 72) continue;
      seen.add(key);
      const c = locate(it.title) || locate(it.summary);
      it.cat = classify(it.title);
      if (c) {
        const [dy, dx] = jitter(it.title);
        Object.assign(it, { country: c.name, iso: c.iso, flag: flag(c.iso), lat: c.lat + dy, lng: c.lng + dx, clat: c.lat, clng: c.lng });
      }
      all.push(it);
    }
  }
  return all.sort((a, b) => new Date(b.at) - new Date(a.at));
}

module.exports = {
  // nome → [função, intervalo em segundos]
  collectors: {
    quakes: [quakes, 300], hazards: [hazards, 900], events: [events, 1800], aircraft: [aircraft, 120],
    space: [space, 900], weather: [weather, 600], outbreaks: [outbreaks, 3600], news: [news, 600],
  },
};
