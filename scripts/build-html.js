'use strict';
// Gera um único arquivo HTML com CSS e JS embutidos, para abrir direto no navegador.
//
//   node scripts/build-html.js live
//       dist/atalaia-ao-vivo.html: busca as fontes direto do navegador e se atualiza sozinho.
//       Não precisa de servidor. Só entram as fontes que liberam leitura pelo navegador (CORS).
//
//   node scripts/build-html.js demo [url do servidor] [código de membro]
//       dist/atalaia-demo.html: fotografia dos dados do servidor naquele momento; não se atualiza.
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const [mode = 'live', base = 'http://localhost:8080', code = ''] = process.argv.slice(2);

const read = (...p) => fs.readFileSync(path.join(root, ...p), 'utf8');
const inline = (s) => s.replace(/<\/(script)/gi, '<\\/$1');

// Roda os mesmos módulos do servidor (geo, sources, core) dentro da página, com um "require" mínimo.
function liveRuntime() {
  const mod = (name) => `def(${JSON.stringify(name)}, function (module, exports, require, process) {\n${read('server', name + '.js')}\n});`;
  return `window.__LIVE__ = (function () {
const process = { env: {} }, mods = {};
const require = (n) => mods[n.replace('./', '')];
function def(name, fn) { const module = { exports: {} }; fn(module, module.exports, require, process); mods[name] = module.exports; }
${mod('geo')}
${mod('sources')}
${mod('core')}
const { collectors } = mods.sources, core = mods.core;
// fontes que não liberam leitura direta pelo navegador
const SKIP = { aircraft: 'Esta fonte não permite leitura direta pelo navegador; ela só funciona na versão com servidor.' };
const state = {}, status = {};
const api = {
  onUpdate: null,
  feed() {
    const map = core.buildMap(state);
    return {
      generated_at: new Date().toISOString(), tier: 'live', unlocked: true, trial_ends: null, default_layers: null,
      threat: core.threatLevel(map, state.space, state.weather), map, locked: {},
      counts: Object.fromEntries(Object.entries(map).map(([k, v]) => [k, v.length])),
      headlines: core.headlinesOf(state).slice(0, 150), headlines_locked: 0,
      space: state.space || null, weather: state.weather || null, sources: status, offer: { trial_hours: 0, contact: '' },
    };
  },
};
async function run(name) {
  try {
    const data = await collectors[name][0]();
    state[name] = data;
    status[name] = { ok: true, at: new Date().toISOString(), count: Array.isArray(data) ? data.length : 1 };
  } catch (e) {
    status[name] = { ok: false, at: new Date().toISOString(), error: String(e.message || e).slice(0, 120), stale: name in state };
  }
  if (api.onUpdate) api.onUpdate();
}
for (const name of Object.keys(collectors)) {
  if (SKIP[name]) { status[name] = { ok: false, at: new Date().toISOString(), error: SKIP[name], unavailable: true }; continue; }
  run(name);
  setInterval(() => run(name), collectors[name][1] * 1000);
}
// ao voltar para a aba, atualiza na hora o que ficou velho (abas em segundo plano têm os timers atrasados)
document.addEventListener('visibilitychange', () => {
  if (document.hidden) return;
  for (const name of Object.keys(collectors)) {
    const s = status[name];
    if (!SKIP[name] && s && Date.now() - new Date(s.at) > collectors[name][1] * 1000) run(name);
  }
});
return api;
})();`;
}

(async () => {
  let data, name;
  if (mode === 'live') {
    data = liveRuntime(); name = 'atalaia-ao-vivo.html';
  } else {
    let cookie = '';
    if (code) {
      const r = await fetch(base + '/unlock', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code }) });
      if (!r.ok) throw new Error('Código recusado pelo servidor.');
      cookie = (r.headers.get('set-cookie') || '').split(';')[0];
    }
    const feed = await (await fetch(base + '/feed', { headers: cookie ? { cookie } : {} })).json();
    feed.offer = { trial_hours: 0, contact: '' };
    data = `window.__SNAPSHOT__ = ${JSON.stringify(feed)};`; name = 'atalaia-demo.html';
  }
  const icon = 'data:image/svg+xml;base64,' + Buffer.from(read('public', 'icon.svg')).toString('base64');
  const html = read('public', 'index.html')
    .replace('<link rel="manifest" href="/manifest.webmanifest">\n', '')
    .replace(/href="\/icon\.svg"|src="\/icon\.svg"/g, (m) => m.replace('/icon.svg', icon))
    .replace('<a class="brand" href="/">', '<a class="brand" href="#">')
    .replace('<link rel="stylesheet" href="/styles.css">', () => `<style>\n${read('public', 'styles.css')}</style>`)
    .replace('<script src="/app.js"></script>', () => `<script>\n${inline(data)}\n</script>\n<script>\n${inline(read('public', 'app.js'))}</script>`);
  fs.mkdirSync(path.join(root, 'dist'), { recursive: true });
  const out = path.join(root, 'dist', name);
  fs.writeFileSync(out, html);
  console.log(`${out} (${Math.round(html.length / 1024)} KB)`);
})().catch((e) => { console.error(e.message); process.exit(1); });
