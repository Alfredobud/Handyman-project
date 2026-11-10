#!/usr/bin/env python3
"""Modelo 3D (three.js) do privacy screen a partir da MESMA geometria das pranchas.

Uso: python3 gerar_3d.py [pasta_spec] [--topo 2x|4x]
  pasta_spec padrão: orcamento-c/cedro-4x6 ; --topo 2x reproduz a rev. 9 (vigas 2x8, caibros 2x6)
Saída: renders/<nome>/cerca-3d.html (interativo, girar com o mouse) e PNGs de cada vista.
"""
import json
import math
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))


def _skills(d):
    while not os.path.isdir(os.path.join(d, ".claude", "skills")):
        d = os.path.dirname(d)
    return os.path.join(d, ".claude", "skills")


SK = _skills(AQUI)
sys.path.insert(0, os.path.join(SK, "desenho-madeira", "templates"))
sys.path.insert(0, os.path.join(SK, "desenho-madeira", "scripts"))
import privacy_screen as ps  # noqa: E402
from cad import _chromium  # noqa: E402


def cena(G):
    """Lista de sólidos: caixas {t:'box', p:[x0,y0,z0], s:[dx,dy,dz], m} e extrusões
    {t:'ext', plano:'xy'|'zy', pts:[[a,b],...], de:[ini, fim] no eixo restante, m}."""
    g = G.g
    S = []

    def box(x0, y0, z0, dx, dy, dz, m):
        S.append({"t": "box", "p": [x0, y0, z0], "s": [dx, dy, dz], "m": m})
    col = g["colar_concreto"]
    for i in range(G.n):
        xp, xn, W = G.xp[i], G.xn[i], G.W[i]
        cx = G.cx[i]
        w = col["largura"]
        box(cx - w / 2, 0, G.D / 2 - w / 2, w, col["altura"], w, "concreto")
        # faces (param embaixo da viga quando faceada)
        box(xp + G.mf[i], G.y_rev0, 0, G.fl, G.comp_face, G.fe, "madeira")
        box(xp + G.mf[i], G.y_rev0, G.fe + G.nucz, G.fl, G.comp_face, G.fe, "madeira")
        # laterais (serrilhada/lisa) e núcleo no topo
        box(xp, G.y_rev0, G.fe, G.tl[i], G.comp_rev, G.nucz, "madeira2")
        box(xn + G.nuc, G.y_rev0, G.fe, G.tr[i], G.comp_rev, G.nucz, "madeira2")
        box(xn, G.y_rev0, G.fe, G.nuc, G.comp_rev, G.nucz, "pt")
    r = g["ripa"]
    for i in range(G.n - 1):
        x0 = G.bay_ini(i) - (G.s - r["folga_ponta"])
        for yr in G.ripas_y:
            box(x0, yr, G.z_r0, G.comp_ripa, r["larg"], r["esp"], "ripa")
    vg, cb = g["viga"], g["caibro"]
    for z0, z1 in G.zv:
        if G.com_cap:
            pts = [[G.x_viga0, G.y_viga0], [G.x_viga1, G.y_viga0], [G.x_viga1, G.y_vtopo], [G.x_viga0, G.y_vtopo]]
        else:
            a, b = G.x_viga0, G.x_viga1
            pts = [[a + 3, G.y_viga0], [b - 3, G.y_viga0], [b, G.y_viga0 + 3], [b, G.y_vtopo], [a, G.y_vtopo], [a, G.y_viga0 + 3]]
        S.append({"t": "ext", "plano": "xy", "pts": pts, "de": [z0, z1], "m": "viga"})
        zf = z0 if z0 < 0.5 else z1                            # face externa da viga
        npf = int(vg.get("parafusos_por_poste", 1))
        for cx in G.cx:
            for k in range(npf):
                dx = ((k % 2) - 0.5) * 1.6 if npf > 1 else 0
                dy = ((k // 2) - 0.5) * 2.6 if npf > 2 else 0
                S.append({"t": "bolt", "c": [cx + dx, G.y_viga0 + vg["alt"] / 2 + dy, zf], "lado": -1 if zf < 1 else 1})
    perfil = ps.perfil_caibro(G.zc0, cb["comprimento"], G.y_cb0, cb["alt"], cb["perfil"])
    for xc in G.xc:
        S.append({"t": "ext", "plano": "zy", "pts": [[z, y] for z, y in perfil], "de": [xc, xc + cb["esp"]], "m": "caibro"})
    return S


HTML = r"""<!doctype html><html><head><meta charset="utf-8"><title>Kitchen Privacy Screen 3D</title>
<style>html,body{margin:0;height:100%;background:#cfdde8;overflow:hidden;font-family:sans-serif}
#info{position:absolute;left:10px;bottom:8px;font-size:12px;color:#223;background:#ffffffaa;padding:4px 8px;border-radius:4px}</style>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
"three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}</script></head><body>
<div id="info">__INFO__</div>
<script type="module">
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const S = __CENA__, VIEWS = __VIEWS__;
const W = innerWidth, H = innerHeight;
const r = new THREE.WebGLRenderer({antialias:true, preserveDrawingBuffer:true});
r.setSize(W, H); r.setPixelRatio(Math.min(devicePixelRatio, 2)); r.shadowMap.enabled = true; r.shadowMap.type = THREE.PCFSoftShadowMap;
r.toneMapping = THREE.ACESFilmicToneMapping; r.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(r.domElement);
const sc = new THREE.Scene(); sc.background = new THREE.Color(0xcfdde8);
const cam = new THREE.PerspectiveCamera(35, W/H, 1, 5000);
sc.add(new THREE.HemisphereLight(0xeaf2ff, 0x6b5a45, 1.1));
const sun = new THREE.DirectionalLight(0xfff1dc, 2.2); sun.position.set(-380, 520, 260);
const fill = new THREE.DirectionalLight(0xdde8ff, 0.7); fill.position.set(400, 300, -400); sc.add(fill); sun.castShadow = true;
sun.shadow.mapSize.set(4096, 4096); Object.assign(sun.shadow.camera, {left:-260, right:260, top:260, bottom:-260, near:10, far:1600});
sun.target.position.set(130, 40, 0); sc.add(sun, sun.target);
function wood(base){ // textura simples de veios
  const c = document.createElement('canvas'); c.width = 512; c.height = 64; const x = c.getContext('2d');
  x.fillStyle = base; x.fillRect(0,0,512,64);
  for(let i=0;i<70;i++){ x.strokeStyle = `rgba(90,45,15,${0.05+Math.random()*0.12})`; x.lineWidth = 0.5+Math.random()*1.5;
    const y = Math.random()*64; x.beginPath(); x.moveTo(0,y); for(let k=0;k<=512;k+=32) x.lineTo(k, y+Math.sin(k/60+i)*2); x.stroke(); }
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.colorSpace = THREE.SRGBColorSpace; return t; }
const M = {
  madeira: new THREE.MeshStandardMaterial({map: wood('__C1__'), roughness:0.75}),
  madeira2: new THREE.MeshStandardMaterial({map: wood('__C2__'), roughness:0.75}),
  ripa: new THREE.MeshStandardMaterial({map: wood('__C1__'), roughness:0.75}),
  viga: new THREE.MeshStandardMaterial({map: wood('__C3__'), roughness:0.7}),
  caibro: new THREE.MeshStandardMaterial({map: wood('__C3__'), roughness:0.7}),
  pt: new THREE.MeshStandardMaterial({color:0x9c9a6a, roughness:0.85}),
  concreto: new THREE.MeshStandardMaterial({color:0xbdbdb8, roughness:0.95}),
  aco: new THREE.MeshStandardMaterial({color:0x8a9096, metalness:0.7, roughness:0.35})};
function add(mesh){ mesh.castShadow = mesh.receiveShadow = true; sc.add(mesh); }
for (const o of S){
  if (o.t==='box'){ const m = new THREE.Mesh(new THREE.BoxGeometry(o.s[0],o.s[1],o.s[2]), M[o.m]);
    m.position.set(o.p[0]+o.s[0]/2, o.p[1]+o.s[1]/2, o.p[2]+o.s[2]/2);
    const t = m.material.map; if (t){ m.geometry.attributes.uv.array.forEach((v,i,a)=>{}); } add(m); }
  else if (o.t==='ext'){ const sh = new THREE.Shape(o.pts.map(p=>new THREE.Vector2(p[0],p[1])));
    const g = new THREE.ExtrudeGeometry(sh, {depth: o.de[1]-o.de[0], bevelEnabled:false});
    const m = new THREE.Mesh(g, M[o.m]);
    if (o.plano==='xy'){ m.position.z = o.de[0]; }
    else { m.rotation.y = -Math.PI/2; m.position.x = o.de[1]; } // shape (z,y) extrudado ao longo de x
    g.computeVertexNormals(); add(m); }
  else if (o.t==='bolt'){ const g = new THREE.CylinderGeometry(0.55,0.55,0.35,16); const m = new THREE.Mesh(g, M.aco);
    m.rotation.x = Math.PI/2; m.position.set(o.c[0], o.c[1], o.c[2] + o.lado*0.17); add(m); }
}
const chao = new THREE.Mesh(new THREE.PlaneGeometry(2000, 2000), new THREE.MeshStandardMaterial({color:0x7f9a5a, roughness:1}));
chao.rotation.x = -Math.PI/2; chao.receiveShadow = true; sc.add(chao);
const piso = new THREE.Mesh(new THREE.PlaneGeometry(330, 40), new THREE.MeshStandardMaterial({color:0xa0705a, roughness:0.95}));
piso.rotation.x = -Math.PI/2; piso.position.set(132, 0.2, __ZD__ + 30); piso.receiveShadow = true; sc.add(piso);
const ctl = new OrbitControls(cam, r.domElement);
function view(n){ const v = VIEWS[n] || VIEWS.geral; cam.position.set(...v.pos); ctl.target.set(...v.alvo); cam.fov = v.fov || 35; cam.updateProjectionMatrix(); ctl.update(); }
view((location.hash || '#geral').slice(1));
addEventListener('hashchange', ()=>view(location.hash.slice(1)));
(function loop(){ requestAnimationFrame(loop);
  if (r.domElement.width !== Math.round(innerWidth*r.getPixelRatio()) || r.domElement.height !== Math.round(innerHeight*r.getPixelRatio())){ r.setSize(innerWidth, innerHeight); cam.aspect = innerWidth/innerHeight; cam.updateProjectionMatrix(); }
  r.render(sc, cam); })();
window.__pronto = true;
</script></body></html>"""


def main():
    args = sys.argv[1:]
    topo = "2x"
    if "--topo" in args:
        k = args.index("--topo"); topo = args[k + 1]; del args[k:k + 2]
    pasta = args[0] if args else "orcamento-c/cedro-4x6"
    spec = json.load(open(os.path.join(AQUI, pasta, "spec.json"), encoding="utf-8"))
    g = ps.mescla(ps.PADRAO, spec["geometria"])
    esp = 1.5 if topo == "2x" else 3.5
    g["viga"]["esp"] = esp; g["caibro"]["esp"] = esp
    G = ps.Geo(g)
    S = cena(G)
    L, D, T = G.L, G.D, G.y_topo
    views = {
        "geral": {"pos": [-90, 130, 260], "alvo": [L * 0.5, 45, 0], "fov": 38},
        "vizinho": {"pos": [L / 2, 55, 300], "alvo": [L / 2, 50, 0], "fov": 40},
        "topo": {"pos": [-55, T + 30, 70], "alvo": [10, T - 8, D / 2], "fov": 40},
        "ripas": {"pos": [G.cx[1] + 26, 46, 44], "alvo": [G.cx[1], 40, D / 2], "fov": 40},
        "casa": {"pos": [L * 0.62, 75, -300], "alvo": [L * 0.5, 48, 0], "fov": 40},
        "base": {"pos": [G.cx[0] - 30, 22, 46], "alvo": [G.cx[0] + 6, 8, D / 2], "fov": 40},
    }
    cedro = all(spec["geometria"].get("materiais", {}).get(k, "cedro") == "cedro" for k in ("ripa", "viga"))
    cores = ("#c98b4f", "#b97a40", "#c4844a") if cedro else ("#b8a77a", "#ad9c6e", "#b3a172")
    info = (f"Kitchen Privacy Screen — {G.n} posts, {ps.pes_pol(L)} x {ps.pes_pol(T)}, {G.fiadas} slats/bay, "
            f"top {topo} ({'cedar' if cedro else 'treated pine'}) — drag to orbit, scroll to zoom")
    html = (HTML.replace("__CENA__", json.dumps(S)).replace("__VIEWS__", json.dumps(views)).replace("__INFO__", info)
            .replace("__C1__", cores[0]).replace("__C2__", cores[1]).replace("__C3__", cores[2]).replace("__ZD__", f"{D:.2f}"))
    nome = os.path.basename(pasta.rstrip("/")) + f"-topo{topo}"
    out = os.path.join(AQUI, "renders", nome)
    os.makedirs(out, exist_ok=True)
    hp = os.path.join(out, "cerca-3d.html")
    open(hp, "w", encoding="utf-8").write(html)
    nav = _chromium()
    for v in views:
        png = os.path.join(out, f"3d-{v}.png")
        subprocess.run([nav, "--headless", "--no-sandbox", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
                        "--hide-scrollbars", "--window-size=1600,1000", "--virtual-time-budget=25000", f"--screenshot={png}",
                        f"file://{hp}#{v}"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=240)
        print(png)


if __name__ == "__main__":
    main()
