// Captura o material-fonte do Reel (pranchas, proposta, 3D) em marketing/build/src/.
// Uso: node marketing/capturar_fontes.js   (a partir da pasta do projeto)
// Tudo é anonimizado antes de renderizar: nada de nome do cliente, cidade ou preços.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const P = path.resolve(__dirname, '..');
const OUT = path.join(__dirname, 'build', 'src');
fs.mkdirSync(OUT, { recursive: true });

const anon = s => s.replace(/Bill/g, 'Homeowner')
  .replace(/Cornelius, NC/g, 'Lake Norman area, NC').replace(/Cornelius/g, 'Lake Norman area')
  .replace(/Mecklenburg/g, 'local');

function check(txt, what) {
  if (/Bill|Cornelius|Mecklenburg/.test(txt)) throw new Error(`dado do cliente sobrou em ${what}`);
}

const SHEETS = {
  'rev7-A-1': 'desenhos/arquivo-rev7/7-postes/privacy-screen-A-1.svg',
  'rev7-10-A-1': 'desenhos/arquivo-rev7/10-postes/privacy-screen-A-1.svg',
  'rev9-A-1': 'desenhos/rev9-a-cedro/privacy-screen-A-1.svg',
  'rev9-A-2': 'desenhos/rev9-a-cedro/privacy-screen-A-2.svg',
  'rev9-A-3': 'desenhos/rev9-a-cedro/privacy-screen-A-3.svg',
  'rev9-B-1': 'desenhos/rev9-b-pinus/privacy-screen-B-1.svg',
};

(async () => {
  const browser = await chromium.launch({
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
  });

  // 1. Pranchas (SVG 1700x1100 -> 3400x2200)
  {
    const page = await browser.newPage({ viewport: { width: 1700, height: 1100 }, deviceScaleFactor: 2 });
    for (const [k, f] of Object.entries(SHEETS)) {
      const svg = anon(fs.readFileSync(path.join(P, f), 'utf8'));
      check(svg, f);
      await page.setContent(`<html><body style="margin:0;background:#fff">${svg.replace(/width="17.0in" height="11.0in"/, 'width="1700" height="1100"')}</body></html>`);
      await page.screenshot({ path: path.join(OUT, `${k}.png`) });
    }
    await page.close();
  }

  // 2. Proposta rev9: só a primeira página, preços removidos
  {
    const page = await browser.newPage({ viewport: { width: 816, height: 1056 }, deviceScaleFactor: 2 });
    let html = anon(fs.readFileSync(path.join(P, 'propostas/proposal-rev9.html'), 'utf8'));
    html = html.replace(/\$[0-9][0-9,.]*/g, '');
    check(html, 'proposta');
    await page.setContent(html);
    await page.addStyleTag({ content: 'body{margin:0.6in} .pb ~ *{display:none !important}' });
    await page.screenshot({ path: path.join(OUT, 'proposta-p1.png') });
    await page.close();
  }

  // 3. 3D: giro (sem UI) e telas de celular (com UI)
  const url = 'file://' + path.join(P, 'renders/web/kitchen-privacy-screen-3d.html');
  const wait3d = async page => {
    await page.waitForFunction(() => !document.getElementById('load') && window.__get, null, { timeout: 60000 });
    await page.waitForTimeout(800);
  };
  {
    const page = await browser.newPage({ viewport: { width: 540, height: 960 }, deviceScaleFactor: 2 });
    await page.goto(url);
    await wait3d(page);
    await page.addStyleTag({ content: '.bar{display:none}' });
    for (const opt of ['A', 'B']) {
      await page.evaluate(o => { window.__paint(o); window.__view('overall'); }, opt);
      await page.waitForTimeout(300);
      await page.screenshot({ path: path.join(OUT, `3d-${opt}-overall.png`) });
      await page.evaluate(() => window.__view('top'));
      await page.waitForTimeout(300);
      await page.screenshot({ path: path.join(OUT, `3d-${opt}-top.png`) });
    }
    await page.close();
  }
  {
    const page = await browser.newPage({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 2 });
    await page.goto(url);
    await wait3d(page);
    // esconde o título do projeto (genérico, mas mantemos limpo) — não tem nome do cliente
    await page.screenshot({ path: path.join(OUT, 'phone-1-overall.png') });
    await page.getByRole('button', { name: 'Top detail' }).click();
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(OUT, 'phone-2-top.png') });
    await page.getByRole('button', { name: 'B · Treated pine' }).click();
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(OUT, 'phone-3-top-B.png') });
    // giro do modelo B na vista geral, 24 quadros, UI visível (é o celular)
    await page.getByRole('button', { name: 'Overall' }).click();
    await page.waitForTimeout(400);
    const g = await page.evaluate(() => window.__get());
    for (let i = 0; i < 24; i++) {
      await page.evaluate(([g, i]) => window.__orbit(g.th + i * 0.035, g.ph, g.rad, ...g.tgt), [g, i]);
      await page.waitForTimeout(60);
      await page.screenshot({ path: path.join(OUT, `phone-spin-${String(i).padStart(2, '0')}.png`) });
    }
    await page.close();
  }
  await browser.close();
  console.log('ok ->', OUT);
})().catch(e => { console.error(e); process.exit(1); });
