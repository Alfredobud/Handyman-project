'use strict';
// Gera dist/atalaia-demo.html: um único arquivo com CSS, JS e os dados atuais embutidos.
// Uso: node scripts/build-standalone.js [url do servidor] [código de membro]
// Com um código, o arquivo leva os dados completos; sem código, leva a amostra gratuita.
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const base = process.argv[2] || 'http://localhost:8080';
const code = process.argv[3] || '';

(async () => {
  let cookie = '';
  if (code) {
    const r = await fetch(base + '/unlock', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code }) });
    if (!r.ok) throw new Error('Código recusado pelo servidor.');
    cookie = (r.headers.get('set-cookie') || '').split(';')[0];
  }
  const feed = await (await fetch(base + '/feed', { headers: cookie ? { cookie } : {} })).json();
  feed.offer = { trial_hours: 0, contact: '' };
  const read = (f) => fs.readFileSync(path.join(root, 'public', f), 'utf8');
  const inline = (s) => s.replace(/<\/(script)/gi, '<\\/$1');
  const icon = 'data:image/svg+xml;base64,' + Buffer.from(read('icon.svg')).toString('base64');
  const html = read('index.html')
    .replace('<link rel="manifest" href="/manifest.webmanifest">\n', '')
    .replace(/href="\/icon\.svg"|src="\/icon\.svg"/g, (m) => m.replace('/icon.svg', icon))
    .replace('<a class="brand" href="/">', '<a class="brand" href="#">')
    .replace('<link rel="stylesheet" href="/styles.css">', () => `<style>\n${read('styles.css')}</style>`)
    .replace('<script src="/app.js"></script>', () => `<script>window.__SNAPSHOT__ = ${inline(JSON.stringify(feed))};</script>\n<script>\n${inline(read('app.js'))}</script>`);
  fs.mkdirSync(path.join(root, 'dist'), { recursive: true });
  const out = path.join(root, 'dist', 'atalaia-demo.html');
  fs.writeFileSync(out, html);
  console.log(`${out} (${Math.round(html.length / 1024)} KB, ${feed.unlocked ? 'dados completos' : 'amostra gratuita'})`);
})().catch((e) => { console.error(e.message); process.exit(1); });
