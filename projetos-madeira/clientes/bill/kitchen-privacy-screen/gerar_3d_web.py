#!/usr/bin/env python3
"""Página 3D para celular (publicável como Artifact): uma página com as opções A (cedro) e B (PT),
botões de vista e controle por toque. Usa a mesma geometria de gerar_3d.py / das pranchas.

Uso: python3 gerar_3d_web.py [--topo 2x|4x]
Saída: renders/web/kitchen-privacy-screen-3d.html
"""
import json
import os
import sys

import gerar_3d as g3

ps = g3.ps
AQUI = g3.AQUI


def geo(pasta, esp):
    spec = json.load(open(os.path.join(AQUI, pasta, "spec.json"), encoding="utf-8"))
    g = ps.mescla(ps.PADRAO, spec["geometria"])
    g["viga"]["esp"] = esp
    g["caibro"]["esp"] = esp
    return ps.Geo(g)


PAGE = r"""<title>Bill's Kitchen Privacy Screen</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
/* Layout: full-bleed 3D canvas; option switch on top, view chips on the bottom, both clear of safe areas */
:root{
  --bg:#dfe7ec; --panel:rgba(250,248,244,.92); --ink:#2b2420; --muted:#6d625a;
  --accent:#9a5a2b; --accent-ink:#fffaf4; --line:rgba(43,36,32,.14);
  --font-ui:"Inter",system-ui,-apple-system,"Segoe UI",sans-serif;
  --font-head:"Space Grotesk","Inter",system-ui,sans-serif;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bg:#1b1d1f; --panel:rgba(30,28,26,.9); --ink:#f1e9e1; --muted:#b3a79c;
  --accent:#d08a52; --accent-ink:#1d140d; --line:rgba(241,233,225,.16); color-scheme:dark}}
:root[data-theme="dark"]{
  --bg:#1b1d1f; --panel:rgba(30,28,26,.9); --ink:#f1e9e1; --muted:#b3a79c;
  --accent:#d08a52; --accent-ink:#1d140d; --line:rgba(241,233,225,.16); color-scheme:dark}
html,body{height:100%}
body{background:var(--bg);color:var(--ink);font-family:var(--font-ui);overflow:hidden;
  padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
#c{position:fixed;inset:0;width:100%;height:100%;touch-action:none;display:block}
.bar{position:fixed;left:0;right:0;z-index:2;display:flex;flex-wrap:wrap;gap:8px;align-items:center;
  padding-left:max(12px,env(safe-area-inset-left,0px));padding-right:max(12px,env(safe-area-inset-right,0px));pointer-events:none}
.bar>*{pointer-events:auto}
.top{top:0;padding-top:calc(10px + env(safe-area-inset-top,0px));justify-content:space-between}
.bottom{bottom:0;padding-bottom:calc(10px + env(safe-area-inset-bottom,0px));justify-content:center}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:8px 12px;
  backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);min-width:0}
h1{font-family:var(--font-head);font-size:16px;font-weight:600;margin:0;text-wrap:balance}
.spec{font-size:12px;color:var(--muted);margin-top:2px;font-variant-numeric:tabular-nums}
.seg{display:flex;padding:3px;gap:3px;border-radius:10px}
button{font:500 13px var(--font-ui);color:var(--ink);background:transparent;border:0;border-radius:7px;
  padding:8px 11px;cursor:pointer;min-height:36px}
button[aria-pressed="true"]{background:var(--accent);color:var(--accent-ink)}
button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.views{display:flex;flex-wrap:wrap;gap:4px;justify-content:center;max-width:640px}
.hint{width:100%;text-align:center;font-size:11px;color:var(--muted);text-shadow:0 0 6px var(--bg)}
#load{position:fixed;inset:0;display:grid;place-items:center;font-size:14px;color:var(--muted);z-index:1}
</style>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@600&display=swap">
<canvas id="c"></canvas>
<div id="load">Loading 3D model…</div>
<div class="bar top">
  <div class="card"><h1>Kitchen Privacy Screen</h1><div class="spec">__SPEC__</div></div>
  <div class="card seg" role="group" aria-label="Material option">
    <button id="optA" aria-pressed="true">A · Cedar</button>
    <button id="optB" aria-pressed="false">B · Treated pine</button>
  </div>
</div>
<div class="bar bottom">
  <div class="card views" role="group" aria-label="Views" id="views"></div>
  <div class="hint">Drag to rotate · pinch or scroll to zoom · two fingers to pan</div>
</div>
<script src="https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js"></script>
<script>
(function(){
const S = __CENA__, VIEWS = __VIEWS__, ZD = __ZD__, LEN = __LEN__;
const PAL = {A:["#c98b4f","#b97a40","#c4844a"], B:["#b8a77a","#ad9c6e","#b3a172"]};
const NAMES = {overall:"Overall", top:"Top detail", slats:"Slats", base:"Base", neighbor:"Neighbor side", house:"House side"};
const canvas = document.getElementById('c');
const mobile = matchMedia('(pointer: coarse)').matches || innerWidth < 700;
const r = new THREE.WebGLRenderer({canvas, antialias:true});
r.setPixelRatio(Math.min(devicePixelRatio, mobile ? 1.75 : 2));
r.shadowMap.enabled = true; r.shadowMap.type = THREE.PCFSoftShadowMap;
r.toneMapping = THREE.ACESFilmicToneMapping; r.outputColorSpace = THREE.SRGBColorSpace;
const sc = new THREE.Scene(); sc.background = new THREE.Color(0xcfdde8);
const cam = new THREE.PerspectiveCamera(38, 1, 1, 5000);
sc.add(new THREE.HemisphereLight(0xeaf2ff, 0x6b5a45, 1.1));
const sun = new THREE.DirectionalLight(0xfff1dc, 2.2); sun.position.set(-380, 520, 260); sun.castShadow = true;
const sm = mobile ? 2048 : 4096; sun.shadow.mapSize.set(sm, sm);
Object.assign(sun.shadow.camera, {left:-260, right:260, top:260, bottom:-260, near:10, far:1600});
sun.target.position.set(LEN/2, 40, 0); sc.add(sun, sun.target);
const fill = new THREE.DirectionalLight(0xdde8ff, 0.7); fill.position.set(400, 300, -400); sc.add(fill);
function grain(){ const c = document.createElement('canvas'); c.width = 512; c.height = 64; const x = c.getContext('2d');
  x.fillStyle = '#fff'; x.fillRect(0,0,512,64);
  for(let i=0;i<70;i++){ x.strokeStyle = `rgba(90,45,15,${0.06+Math.random()*0.14})`; x.lineWidth = 0.5+Math.random()*1.5;
    const y = Math.random()*64; x.beginPath(); x.moveTo(0,y); for(let k=0;k<=512;k+=32) x.lineTo(k, y+Math.sin(k/60+i)*2); x.stroke(); }
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.colorSpace = THREE.SRGBColorSpace; return t; }
const tex = grain();
const wood = () => new THREE.MeshStandardMaterial({map:tex, roughness:0.75});
const M = {madeira:wood(), madeira2:wood(), ripa:wood(), viga:wood(), caibro:wood(),
  pt: new THREE.MeshStandardMaterial({color:0x9c9a6a, roughness:0.85}),
  concreto: new THREE.MeshStandardMaterial({color:0xbdbdb8, roughness:0.95}),
  aco: new THREE.MeshStandardMaterial({color:0x5c6166, metalness:0.7, roughness:0.35})};
function paint(o){ const p = PAL[o]; M.madeira.color.set(p[0]); M.ripa.color.set(p[0]); M.madeira2.color.set(p[1]);
  M.viga.color.set(p[2]); M.caibro.color.set(p[2]);
  document.getElementById('optA').setAttribute('aria-pressed', o==='A'); document.getElementById('optB').setAttribute('aria-pressed', o==='B'); }
function add(m){ m.castShadow = m.receiveShadow = true; sc.add(m); }
for (const o of S){
  if (o.t==='box'){ const m = new THREE.Mesh(new THREE.BoxGeometry(o.s[0],o.s[1],o.s[2]), M[o.m]);
    m.position.set(o.p[0]+o.s[0]/2, o.p[1]+o.s[1]/2, o.p[2]+o.s[2]/2); add(m); }
  else if (o.t==='ext'){ const sh = new THREE.Shape(o.pts.map(p=>new THREE.Vector2(p[0],p[1])));
    const g = new THREE.ExtrudeGeometry(sh, {depth:o.de[1]-o.de[0], bevelEnabled:false});
    const m = new THREE.Mesh(g, M[o.m]);
    if (o.plano==='xy') m.position.z = o.de[0]; else { m.rotation.y = -Math.PI/2; m.position.x = o.de[1]; }
    add(m); }
  else if (o.t==='bolt'){ const m = new THREE.Mesh(new THREE.CylinderGeometry(0.55,0.55,0.35,16), M.aco);
    m.rotation.x = Math.PI/2; m.position.set(o.c[0], o.c[1], o.c[2] + o.lado*0.17); add(m); }
}
const chao = new THREE.Mesh(new THREE.PlaneGeometry(2000,2000), new THREE.MeshStandardMaterial({color:0x7f9a5a, roughness:1}));
chao.rotation.x = -Math.PI/2; chao.receiveShadow = true; sc.add(chao);
const piso = new THREE.Mesh(new THREE.PlaneGeometry(LEN+65, 40), new THREE.MeshStandardMaterial({color:0xa0705a, roughness:0.95}));
piso.rotation.x = -Math.PI/2; piso.position.set(LEN/2, 0.2, ZD + 30); piso.receiveShadow = true; sc.add(piso);

/* Orbit control written in-page: one finger/mouse rotates, pinch/wheel zooms, two fingers/right button pans */
const tgt = new THREE.Vector3(); let rad = 300, th = 0, ph = 1.2;
function apply(){ ph = Math.max(0.08, Math.min(1.62, ph)); rad = Math.max(12, Math.min(900, rad));
  cam.position.set(tgt.x + rad*Math.sin(ph)*Math.sin(th), tgt.y + rad*Math.cos(ph), tgt.z + rad*Math.sin(ph)*Math.cos(th));
  cam.lookAt(tgt); }
const pts = new Map(); let last = null;
function pan(dx, dy){ const k = rad/innerHeight*1.1; const right = new THREE.Vector3().setFromMatrixColumn(cam.matrix, 0);
  const up = new THREE.Vector3().setFromMatrixColumn(cam.matrix, 1); tgt.addScaledVector(right, -dx*k).addScaledVector(up, dy*k); }
canvas.addEventListener('pointerdown', e=>{ canvas.setPointerCapture(e.pointerId); pts.set(e.pointerId, {x:e.clientX, y:e.clientY, b:e.button}); last = null; });
canvas.addEventListener('pointermove', e=>{ if (!pts.has(e.pointerId)) return; const p = pts.get(e.pointerId);
  const dx = e.clientX - p.x, dy = e.clientY - p.y; p.x = e.clientX; p.y = e.clientY;
  if (pts.size === 1){ if (p.b === 2 || e.shiftKey) pan(dx, dy); else { th -= dx*0.006; ph -= dy*0.006; } }
  else if (pts.size === 2){ const [a,b] = [...pts.values()]; const d = Math.hypot(a.x-b.x, a.y-b.y);
    if (last) { rad *= last/d; } last = d; pan(dx/2, dy/2); }
  apply(); });
const up = e=>{ pts.delete(e.pointerId); last = null; };
canvas.addEventListener('pointerup', up); canvas.addEventListener('pointercancel', up);
canvas.addEventListener('contextmenu', e=>e.preventDefault());
canvas.addEventListener('wheel', e=>{ e.preventDefault(); rad *= Math.exp(e.deltaY*0.0012); apply(); }, {passive:false});

function view(n){ const v = VIEWS[n] ? n : 'overall'; const V = VIEWS[v];
  tgt.set(...V.alvo); const d = new THREE.Vector3(...V.pos).sub(tgt);
  const asp = innerWidth/innerHeight; const k = asp < 1.3 && V.wide ? Math.pow(1.3/asp, 0.55) : 1;
  rad = d.length()*k; ph = Math.acos(d.y/d.length()); th = Math.atan2(d.x, d.z); apply();
  document.querySelectorAll('#views button').forEach(b=>b.setAttribute('aria-pressed', b.dataset.v===v)); }
const vb = document.getElementById('views');
for (const k of Object.keys(VIEWS)){ const b = document.createElement('button'); b.textContent = NAMES[k]; b.dataset.v = k;
  b.setAttribute('aria-pressed','false'); b.onclick = ()=>{ if (location.hash.slice(1) === k) view(k); else location.hash = k; }; vb.appendChild(b); }
document.getElementById('optA').onclick = ()=>paint('A');
document.getElementById('optB').onclick = ()=>paint('B');
function size(){ const w = innerWidth, h = innerHeight; r.setSize(w, h, false); cam.aspect = w/h; cam.updateProjectionMatrix(); }
addEventListener('resize', ()=>{ size(); });
addEventListener('hashchange', ()=>view(location.hash.slice(1)));
size(); paint('A'); view(location.hash.slice(1));
document.getElementById('load').remove();
window.__orbit = (a,b,c,x,y,z)=>{ th=a; ph=b; rad=c; if (x!==undefined) tgt.set(x,y,z); apply(); };
window.__get = ()=>({th, ph, rad, tgt:[tgt.x,tgt.y,tgt.z]}); window.__view = view; window.__paint = paint;
(function loop(){ requestAnimationFrame(loop); r.render(sc, cam); })();
})();
</script>
"""


def main():
    args = sys.argv[1:]
    topo = args[args.index("--topo") + 1] if "--topo" in args else "2x"
    esp = 1.5 if topo == "2x" else 3.5
    G = geo("orcamento-c/cedro-4x6", esp)
    assert g3.cena(G) == g3.cena(geo("orcamento-c/pt-4x6", esp)), "geometria A e B diferem"
    S = g3.cena(G)
    L, D, T = G.L, G.D, G.y_topo
    views = {
        "overall": {"pos": [-90, 130, 260], "alvo": [L * 0.5, 45, 0], "wide": True},
        "top": {"pos": [-55, T + 30, 70], "alvo": [10, T - 8, D / 2]},
        "slats": {"pos": [G.cx[1] + 26, 46, 44], "alvo": [G.cx[1], 40, D / 2]},
        "base": {"pos": [G.cx[0] - 30, 22, 46], "alvo": [G.cx[0] + 6, 8, D / 2]},
        "neighbor": {"pos": [L / 2, 55, 300], "alvo": [L / 2, 50, 0], "wide": True},
        "house": {"pos": [L * 0.62, 75, -300], "alvo": [L * 0.5, 48, 0], "wide": True},
    }
    viga = "2x8 beams, 2x6 rafters" if topo == "2x" else "4x8 beams, 4x6 rafters"
    spec = f"{G.n} posts · {ps.pes_pol(L)} × {ps.pes_pol(T)} · {G.fiadas} slats per bay · {viga}"
    html = (PAGE.replace("__CENA__", json.dumps(S, separators=(",", ":"))).replace("__VIEWS__", json.dumps(views))
            .replace("__SPEC__", spec).replace("__ZD__", f"{D:.2f}").replace("__LEN__", f"{L:.2f}"))
    out = os.path.join(AQUI, "renders", "web")
    os.makedirs(out, exist_ok=True)
    hp = os.path.join(out, f"kitchen-privacy-screen-3d{'' if topo == '2x' else '-topo4x'}.html")
    open(hp, "w", encoding="utf-8").write(html)
    print(hp)


if __name__ == "__main__":
    main()
