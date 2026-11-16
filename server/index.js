'use strict';
// Atalaia — servidor HTTP sem dependências (Node 20+).
const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { collectors } = require('./sources');
const { db, save, sha, newCode, checkCode } = require('./store');

const PORT = +(process.env.PORT || 8080);
const PUBLIC = path.join(__dirname, '..', 'public');
const TRIAL_HOURS = +(process.env.TRIAL_HOURS || 1);
const MEMBER_DAYS = 30; // duração do cookie de sessão

if (!db.admin_token) { db.admin_token = process.env.ADMIN_TOKEN || crypto.randomBytes(18).toString('base64url'); save(); }
if (process.env.ADMIN_TOKEN && process.env.ADMIN_TOKEN !== db.admin_token) { db.admin_token = process.env.ADMIN_TOKEN; save(); }

// ------------------------------------------------------------------ coleta
const state = {};   // nome → dados
const status = {};  // nome → {ok, at, error, count}

async function runCollector(name) {
  const [fn] = collectors[name];
  try {
    const data = await fn();
    state[name] = data;
    status[name] = { ok: true, at: new Date().toISOString(), count: Array.isArray(data) ? data.length : 1 };
  } catch (e) {
    status[name] = { ok: false, at: new Date().toISOString(), error: String(e.message || e).slice(0, 120), stale: name in state };
    console.warn(`[fonte] ${name} falhou: ${e.message}`);
  }
  feedCache = {};
}
for (const name of Object.keys(collectors)) {
  runCollector(name);
  setInterval(() => runCollector(name), collectors[name][1] * 1000).unref();
}

// ------------------------------------------------------------------ feed
// Quantos itens de cada camada o visitante sem acesso recebe. O restante nunca sai do servidor.
const SAMPLE = { quakes: 8, hazards: 6, events: 12, aircraft: 5, attacks: 3, unrest: 3, outbreaks: 1, cyber: 1, infra: 2, news: 8 };
const HEADLINES_FREE = 6;

function threatLevel(m, space, weather) {
  let score = 0;
  const reasons = [];
  const add = (pts, why) => { score += pts; reasons.push(why); };
  const att24 = m.attacks.filter((a) => Date.now() - new Date(a.at) < 864e5).length;
  if (att24 >= 3) add(Math.min(4, 1 + Math.floor(att24 / 6)), `${att24} relatos de ataques/conflito em 24h`);
  const red = m.hazards.filter((h) => h.level === 'Red').length;
  const orange = m.hazards.filter((h) => h.level === 'Orange').length;
  if (red) add(Math.min(3, red + 1), `${red} desastre(s) em alerta vermelho (GDACS)`);
  else if (orange >= 3) add(1, `${orange} desastres em alerta laranja (GDACS)`);
  const big = m.quakes.filter((q) => q.mag >= 6.5);
  if (big.length) add(big.some((q) => q.mag >= 7.5) ? 2 : 1, `terremoto M${Math.max(...big.map((q) => q.mag)).toFixed(1)} nas últimas 24h`);
  if (space && space.kp_max_24h >= 7) add(2, `tempestade geomagnética forte (Kp ${space.kp_max_24h})`);
  else if (space && space.kp_max_24h >= 5) add(1, `tempestade geomagnética (Kp ${space.kp_max_24h})`);
  if (m.outbreaks.length >= 4) add(1, `${m.outbreaks.length} surtos reportados pela OMS`);
  if (m.unrest.length >= 6) add(1, `${m.unrest.length} focos de protesto/instabilidade`);
  const recon = m.aircraft.filter((a) => a.role === 'recon' || a.role === 'bomber').length;
  if (recon >= 12) add(1, `${recon} aeronaves estratégicas no ar`);
  if (weather && weather.extreme >= 5) add(1, `${weather.extreme} alertas climáticos extremos nos EUA`);
  const level = score >= 9 ? 5 : score >= 6 ? 4 : score >= 3 ? 3 : score >= 1 ? 2 : 1;
  return { level, label: ['', 'BAIXO', 'MODERADO', 'ELEVADO', 'ALTO', 'SEVERO'][level], score, reasons: reasons.length ? reasons : ['Nenhum sinal fora do normal nas fontes monitoradas'] };
}

function buildMap() {
  const news = state.news || [];
  const located = news.filter((n) => n.country);
  const pick = (cat) => located.filter((n) => n.cat === cat).map((n) => ({
    id: sha(n.link).slice(0, 12), title: n.title, country: n.country, flag: n.flag, at: n.at, link: n.link, source: n.source, lat: n.lat, lng: n.lng,
  }));
  // notícias gerais: um marcador por país, com a lista de manchetes
  const byCountry = {};
  for (const n of located) {
    const g = (byCountry[n.iso] ||= { id: n.iso, country: n.country, flag: n.flag, lat: n.clat, lng: n.clng, n: 0, articles: [] });
    g.n++;
    if (g.articles.length < 8) g.articles.push({ title: n.title, link: n.link, source: n.source, at: n.at, cat: n.cat });
  }
  return {
    quakes: state.quakes || [], hazards: state.hazards || [], events: state.events || [], aircraft: state.aircraft || [],
    attacks: pick('attack'), unrest: pick('unrest'), cyber: pick('cyber'), infra: pick('infra'),
    outbreaks: state.outbreaks || [],
    news: Object.values(byCountry).sort((a, b) => b.n - a.n),
  };
}

const OFFER = {
  monthly_price: process.env.PRICE_MONTHLY || '', monthly_link: process.env.CHECKOUT_MONTHLY || '',
  yearly_price: process.env.PRICE_YEARLY || '', yearly_link: process.env.CHECKOUT_YEARLY || '',
  lifetime_price: process.env.PRICE_LIFETIME || '', lifetime_link: process.env.CHECKOUT_LIFETIME || '',
  contact: process.env.CONTACT || '', trial_hours: TRIAL_HOURS,
};

let feedCache = {};
function buildFeed(tier) {
  if (feedCache[tier]) return feedCache[tier];
  const full = buildMap();
  const threat = threatLevel(full, state.space, state.weather);
  const headlines = (state.news || []).map((n) => ({ title: n.title, link: n.link, source: n.source, at: n.at, cat: n.cat, country: n.country || '', flag: n.flag || '' }));
  const counts = Object.fromEntries(Object.entries(full).map(([k, v]) => [k, v.length]));
  const base = {
    generated_at: new Date().toISOString(), threat, counts, space: state.space || null,
    sources: status, offer: OFFER, default_layers: db.default_layers,
  };
  let out;
  if (tier === 'teaser') {
    const map = {};
    const locked = {};
    for (const [k, v] of Object.entries(full)) {
      map[k] = v.slice(0, SAMPLE[k] ?? 5);
      if (k === 'news') map[k] = map[k].map((g) => ({ ...g, articles: g.articles.slice(0, 2), articles_locked: Math.max(0, g.n - 2) }));
      locked[k] = Math.max(0, v.length - map[k].length);
    }
    const w = state.weather;
    out = {
      ...base, tier, unlocked: false, map, locked,
      headlines: headlines.slice(0, HEADLINES_FREE), headlines_locked: Math.max(0, headlines.length - HEADLINES_FREE),
      weather: w ? { total: w.total, extreme: w.extreme, by_event: w.by_event.slice(0, 3), items: [], source: w.source } : null,
    };
  } else {
    out = { ...base, tier, unlocked: true, map: full, locked: {}, headlines: headlines.slice(0, 150), headlines_locked: 0, weather: state.weather || null };
  }
  return (feedCache[tier] = out);
}

// ------------------------------------------------------------------ sessão
const sign = (s) => crypto.createHmac('sha256', db.secret).update(s).digest('base64url');
function makeToken(payload) {
  const body = Buffer.from(JSON.stringify(payload)).toString('base64url');
  return body + '.' + sign(body);
}
function readSession(req) {
  const m = /(?:^|;\s*)atl=([^;]+)/.exec(req.headers.cookie || '');
  if (!m) return null;
  const [body, mac] = m[1].split('.');
  if (!body || !mac) return null;
  const good = sign(body);
  if (mac.length !== good.length || !crypto.timingSafeEqual(Buffer.from(mac), Buffer.from(good))) return null;
  try {
    const s = JSON.parse(Buffer.from(body, 'base64url').toString());
    if (s.exp < Date.now()) return null;
    if (s.t === 'member') { const c = db.codes[s.id]; if (!c || c.revoked || (c.expires && c.expires < Date.now())) return null; }
    return s;
  } catch (e) { return null; }
}
function cookie(req, value, maxAgeSec) {
  const secure = (req.headers['x-forwarded-proto'] || '').includes('https') ? '; Secure' : '';
  return `atl=${value}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${maxAgeSec}${secure}`;
}
const ipOf = (req) => String(req.headers['cf-connecting-ip'] || req.headers['x-forwarded-for'] || req.socket.remoteAddress || '').split(',')[0].trim();

// limite de tentativas por IP (em memória)
const hits = new Map();
function limited(req, bucket, max, windowSec) {
  const k = bucket + ':' + ipOf(req);
  const now = Date.now();
  const h = (hits.get(k) || []).filter((t) => now - t < windowSec * 1000);
  h.push(now);
  hits.set(k, h);
  return h.length > max;
}
setInterval(() => { const now = Date.now(); for (const [k, v] of hits) if (!v.some((t) => now - t < 36e5)) hits.delete(k); }, 6e5).unref();

// ------------------------------------------------------------------ http
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json', '.webmanifest': 'application/manifest+json', '.svg': 'image/svg+xml', '.png': 'image/png', '.ico': 'image/x-icon', '.txt': 'text/plain; charset=utf-8' };

function send(res, code, body, headers = {}) {
  const isObj = typeof body === 'object' && !Buffer.isBuffer(body);
  const buf = isObj ? JSON.stringify(body) : body;
  res.writeHead(code, { 'Content-Type': isObj ? 'application/json' : 'text/plain; charset=utf-8', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'strict-origin-when-cross-origin', ...headers });
  res.end(buf);
}
function readBody(req) {
  return new Promise((ok, fail) => {
    let size = 0; const chunks = [];
    req.on('data', (c) => { size += c.length; if (size > 20000) { fail(new Error('grande demais')); req.destroy(); } else chunks.push(c); });
    req.on('end', () => { try { ok(chunks.length ? JSON.parse(Buffer.concat(chunks).toString()) : {}); } catch (e) { fail(e); } });
    req.on('error', fail);
  });
}
function serveStatic(req, res, pathname) {
  let rel = pathname === '/' ? '/index.html' : pathname;
  const file = path.normalize(path.join(PUBLIC, rel));
  if (!file.startsWith(PUBLIC + path.sep)) return send(res, 403, 'Proibido');
  fs.readFile(file, (err, buf) => {
    if (err) return send(res, 404, 'Não encontrado');
    const ext = path.extname(file);
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream', 'Cache-Control': ext === '.html' || rel === '/sw.js' ? 'no-cache' : 'public, max-age=300', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'strict-origin-when-cross-origin' });
    res.end(buf);
  });
}

const isAdmin = (req) => {
  const t = (req.headers.authorization || '').replace(/^Bearer\s+/i, '');
  return t.length === db.admin_token.length && crypto.timingSafeEqual(Buffer.from(t), Buffer.from(db.admin_token));
};
const chatId = (s) => (s.t === 'member' ? s.id : 't' + s.sid);
const cleanName = (n) => String(n || '').trim().replace(/\s+/g, ' ');

const routes = {
  'GET /feed': (req, res, s) => {
    const feed = buildFeed(s ? 'full' : 'teaser');
    send(res, 200, { ...feed, tier: s ? s.t : 'teaser', trial_ends: s && s.t === 'trial' ? new Date(s.exp).toISOString() : null });
  },
  'GET /health': (req, res) => send(res, 200, { ok: true, sources: status }),

  'POST /unlock': async (req, res) => {
    if (limited(req, 'unlock', 10, 600)) return send(res, 429, { ok: false, error: 'Muitas tentativas. Aguarde alguns minutos.' });
    const { code } = await readBody(req);
    const id = checkCode(code);
    if (!id) return send(res, 401, { ok: false, error: 'Código inválido ou expirado.' });
    const tok = makeToken({ t: 'member', id, exp: Date.now() + MEMBER_DAYS * 864e5 });
    send(res, 200, { ok: true }, { 'Set-Cookie': cookie(req, tok, MEMBER_DAYS * 86400) });
  },
  'POST /trial': (req, res, s) => {
    if (s) return send(res, 200, { ok: true });
    if (TRIAL_HOURS <= 0) return send(res, 403, { ok: false, error: 'Teste grátis desativado.' });
    const key = sha('trial:' + ipOf(req));
    if (db.trials[key] || /(?:^|;\s*)atl_t=1/.test(req.headers.cookie || '')) return send(res, 403, { ok: false, error: 'O teste grátis já foi usado neste dispositivo ou rede.' });
    db.trials[key] = Date.now(); save();
    const exp = Date.now() + TRIAL_HOURS * 36e5;
    const tok = makeToken({ t: 'trial', sid: crypto.randomBytes(8).toString('hex'), exp });
    send(res, 200, { ok: true, ends: new Date(exp).toISOString() }, { 'Set-Cookie': [cookie(req, tok, TRIAL_HOURS * 3600), 'atl_t=1; Path=/; Max-Age=31536000; SameSite=Lax'] });
  },
  'POST /logout': (req, res) => send(res, 200, { ok: true }, { 'Set-Cookie': cookie(req, '', 0) }),

  // ---- chat (somente com acesso)
  'GET /chat': (req, res, s, url) => {
    if (!s) return send(res, 401, { ok: false, error: 'Somente membros.' });
    const after = +url.searchParams.get('after') || 0;
    send(res, 200, { ok: true, me: db.names[chatId(s)] || null, messages: db.chat.filter((m) => m.id > after).slice(-100) });
  },
  'POST /chat/name': async (req, res, s) => {
    if (!s) return send(res, 401, { ok: false, error: 'Somente membros.' });
    const id = chatId(s);
    if (db.names[id]) return send(res, 409, { ok: false, error: 'Você já escolheu um nome.' });
    const name = cleanName((await readBody(req)).name);
    if (!/^[\p{L}\p{N} _.-]{2,20}$/u.test(name)) return send(res, 400, { ok: false, error: 'Use de 2 a 20 letras, números, espaço, _ - ou ponto.' });
    if (Object.values(db.names).some((n) => n.toLowerCase() === name.toLowerCase())) return send(res, 409, { ok: false, error: 'Esse nome já está em uso.' });
    db.names[id] = name; save();
    send(res, 200, { ok: true, name });
  },
  'POST /chat': async (req, res, s) => {
    if (!s) return send(res, 401, { ok: false, error: 'Somente membros.' });
    if (limited(req, 'chat', 8, 60)) return send(res, 429, { ok: false, error: 'Devagar: muitas mensagens em pouco tempo.' });
    const name = db.names[chatId(s)];
    if (!name) return send(res, 400, { ok: false, error: 'Escolha um nome primeiro.' });
    const text = String((await readBody(req)).text || '').replace(/\s+/g, ' ').trim().slice(0, 500);
    if (!text) return send(res, 400, { ok: false, error: 'Mensagem vazia.' });
    const msg = { id: ++db.chat_seq, name, text, at: new Date().toISOString() };
    db.chat.push(msg);
    if (db.chat.length > 500) db.chat.splice(0, db.chat.length - 500);
    save();
    send(res, 200, { ok: true, message: msg });
  },

  // ---- administração (Authorization: Bearer <ADMIN_TOKEN>)
  'POST /admin/codes': async (req, res) => {
    if (!isAdmin(req)) return send(res, 401, { ok: false, error: 'Não autorizado.' });
    const { note, days } = await readBody(req);
    send(res, 200, { ok: true, code: newCode(note, +days || 0) });
  },
  'GET /admin/codes': (req, res) => {
    if (!isAdmin(req)) return send(res, 401, { ok: false, error: 'Não autorizado.' });
    send(res, 200, { ok: true, codes: Object.entries(db.codes).map(([id, c]) => ({ id, ...c })) });
  },
  'POST /admin/revoke': async (req, res) => {
    if (!isAdmin(req)) return send(res, 401, { ok: false, error: 'Não autorizado.' });
    const { id } = await readBody(req);
    if (!db.codes[id]) return send(res, 404, { ok: false, error: 'Código não encontrado.' });
    db.codes[id].revoked = true; save();
    send(res, 200, { ok: true });
  },
  'POST /admin/chat/delete': async (req, res) => {
    if (!isAdmin(req)) return send(res, 401, { ok: false, error: 'Não autorizado.' });
    const { id } = await readBody(req);
    const i = db.chat.findIndex((m) => m.id === +id);
    if (i >= 0) { db.chat.splice(i, 1); save(); }
    send(res, 200, { ok: i >= 0 });
  },
  'POST /admin/default-layers': async (req, res) => {
    if (!isAdmin(req)) return send(res, 401, { ok: false, error: 'Não autorizado.' });
    const { layers } = await readBody(req);
    db.default_layers = Array.isArray(layers) ? layers.map(String).slice(0, 30) : null; save();
    send(res, 200, { ok: true });
  },
};

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, 'http://x');
    const handler = routes[`${req.method} ${url.pathname}`];
    if (handler) return await handler(req, res, readSession(req), url);
    if (req.method === 'GET' || req.method === 'HEAD') return serveStatic(req, res, decodeURIComponent(url.pathname));
    send(res, 405, 'Método não permitido');
  } catch (e) {
    if (!res.headersSent) send(res, 400, { ok: false, error: 'Requisição inválida.' });
  }
});

server.listen(PORT, () => {
  console.log(`Atalaia no ar: http://localhost:${PORT}`);
  console.log(`Token de administrador: ${db.admin_token}`);
  if (!Object.keys(db.codes).length) console.log(`Primeiro código de membro: ${newCode('código inicial')}`);
});
