#!/usr/bin/env python3
"""Proposta rev. 9.1 (EN) — SOMENTE cedro, com stain/selador Ready Seal Natural Cedar em todo o cedro.
Uso: python3 gerar_documento_rev9_1.py [--previa]  (--previa: só PNGs das páginas de texto)
Base anterior — rev. 9 (EN): mesmo desenho (7 postes, 8 ft, núcleo 4x6, viga parafusada no núcleo),
Opção A cedro aparente x Opção B 100% pinus tratado. Anexa as pranchas A-1..A-3 e B-1..B-3.
Uso: python3 gerar_documento_rev9.py  (depois de gerar_opcao_c.py e dos desenhos rev9-*)"""
import html
import json
import os
import subprocess
import sys
import tempfile

from pypdf import PdfReader, PdfWriter

AQUI = os.path.dirname(os.path.abspath(__file__))


def _skills(d):
    while not os.path.isdir(os.path.join(d, ".claude", "skills")):
        d = os.path.dirname(d)
    return os.path.join(d, ".claude", "skills")


SK = _skills(AQUI)
sys.path.insert(0, os.path.join(SK, "desenho-madeira", "templates"))
sys.path.insert(0, os.path.join(SK, "desenho-madeira", "scripts"))
sys.path.insert(0, os.path.join(SK, "orcamento-madeira", "scripts"))
import privacy_screen as ps  # noqa: E402
import orcamento as orc  # noqa: E402
from cad import _chromium  # noqa: E402

fmt = ps.pes_pol
OP = [("A", "Cedar", "orcamento-rev9-1/opcao-a-cedro-stain", "desenhos/rev9-a-cedro"),
      ("B", "Pressure-treated pine", "orcamento-rev9-1/opcao-b-pt", "desenhos/rev9-b-pinus")]
REV9_A = 7580.00   # total da Opção A na rev. 9 (sem stain)


def usd(v):
    return f"${v:,.0f}"


def carregar(pasta):
    s = json.load(open(os.path.join(AQUI, pasta, "spec.json"), encoding="utf-8"))
    r = json.load(open(os.path.join(AQUI, pasta, "orcamento.json"), encoding="utf-8"))
    G = ps.Geo(ps.mescla(ps.PADRAO, s["geometria"]))
    t = r["totais"]
    shop = sum(m["horas"] for m in r["mao_de_obra"] if str(m["tarefa"]).lower().startswith("oficina"))
    rent = sum(c["subtotal"] for c in r["compra"] if c["material"] in ("aluguel_mini_skid_auger", "frete_equipamento"))
    return dict(s=s, r=r, G=G, t=t, p=r["parametros"], shop=shop, field=t["horas"] - shop, rent=rent)


def extra_paisagismo(taxa, imp):
    cat = orc.carregar_precos([os.path.join(orc.REF_DIR, "precos.csv"), os.path.join(AQUI, "orcamento", "precos.csv")])
    prod = orc.carregar_produtividade(os.path.join(orc.REF_DIR, "produtividade.csv"))
    mat = cat["manta_paisagismo"]["preco"] + 2 * cat["borda_paisagismo"]["preco"] + 9 * cat["pedra_rio"]["preco"]
    return mat * (1 + imp) + 22 * prod["paisagismo_base"]["horas"] * taxa


def main():
    A = carregar(OP[0][2])
    G = A["G"]
    t, p = A["t"], A["p"]
    n, nb = G.n, G.n - 1
    area = next(c["tarefa_qtd"] for c in A["s"]["componentes"] if c.get("material") == "stain_readyseal_natural_cedar_5gal")
    css = """@page{size:Letter;margin:0.6in} body{font-family:'DejaVu Sans',Arial,sans-serif;font-size:9.5pt;color:#222;line-height:1.3}
h1{font-size:19pt;margin:0 0 2pt} h2{font-size:13pt;border-bottom:2px solid #b46a2c;padding-bottom:2pt;margin:14pt 0 6pt}
.sub{color:#555;margin-bottom:8pt} table{border-collapse:collapse;width:100%;page-break-inside:avoid}
td,th{border:1px solid #bbb;padding:3pt 5pt;vertical-align:top} th{background:#f1e6da;text-align:left} .n{text-align:center}
.r{text-align:right;white-space:nowrap} tr.tot td{font-weight:bold;background:#f7efe6} .s{color:#555;font-size:8.5pt}
.pb{page-break-before:always} ul{margin:4pt 0 8pt 16pt;padding:0} li{margin-bottom:3pt} table.mat{font-size:8.5pt}
.box{background:#f7efe6;border-left:4px solid #b46a2c;padding:5pt 8pt;margin:6pt 0}"""
    WRC, PT = "Western Red Cedar, kiln-dried", "Pressure-treated Southern Yellow Pine #2"
    mat_rows = [
        ("Post core (buried 36\")", f"{PT} 4x6, ground contact (UC4B)", "S4S", "3 1/2\" x 5 1/2\" x 12' (5 1/2\" across the fence)", n, "No (hidden)"),
        ("Post faces (house + neighbor)", f"{WRC} 2x6", "S4S", f"1 1/2\" x 5 1/2\" x {fmt(G.comp_face)}", 2 * n, "Yes"),
        ("Notched side boards", f"{WRC} 5/4x6", "S4S, eased edges", f"1\" x 5 1/2\" x {fmt(G.comp_rev)}", 2 * nb, "Yes"),
        ("Plain side boards (end posts)", f"{WRC} 5/4x6", "S4S, eased edges", f"1\" x 5 1/2\" x {fmt(G.comp_rev)}", 2, "Yes"),
        ("Slats", f"{WRC} 2x2", "S4S", f"1 1/2\" x 1 1/2\" x {fmt(G.comp_ripa)}", G.fiadas * nb, "Yes"),
        ("Beams (both sides, notched)", f"{WRC} 2x8", "S4S", f"1 1/2\" x 7 1/4\" x {fmt(G.pecas_viga[0])}", 2 * len(G.pecas_viga), "Yes"),
        ("Pergola rafters (cloud-lift ends)", f"{WRC} 2x6", "S4S", "1 1/2\" x 5 1/2\" x 36\"", len(G.xc), "Yes"),
    ]
    mat_html = ("<table class='mat'><tr><th>Part</th><th>Material</th><th>Surface</th><th>Actual size</th><th>Qty</th><th>Stained &amp; sealed</th></tr>"
                + "".join(f"<tr><td>{html.escape(a)}</td><td>{html.escape(b)}</td><td>{c}</td><td>{html.escape(d)}</td><td class='n'>{q}</td><td class='n'>{e}</td></tr>"
                          for a, b, c, d, q, e in mat_rows) + "</table>")
    passos = ["Holes (machine auger), Ø16\" x 42\"", "Posts: treated-pine 4x6 cores, 36\" deep in concrete", "Level post tops",
              "Shop: pre-cut, ease edges and stain/seal all cedar on 4 sides",
              "Notched side boards (pre-cut), from the neighbor side", "Slats (pre-cut)", "Front closure: face boards, ending under the beams",
              "Side closure (end posts)", "Beams (pre-notched), bolted straight to the cores (4 x 1/2\" thru-bolts per post)",
              "Pergola rafters (pre-cut), posts + mid-bay", "Stain touch-up on site (cuts, notches, rafter ends, screw heads)"]
    extra = extra_paisagismo(p["taxa_hora_usd"], p["imposto_material"])
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body>
<h1>Kitchen Privacy Screen — Proposal (rev. 9.1)</h1>
<div class="sub">Prepared for <b>Bill</b> · Cornelius, NC · November 11, 2026 · valid for 30 days · cedar, stained &amp; sealed</div>
<p class="box"><b>What changed since rev. 9:</b> as requested, the cedar option now includes <b>staining and sealing all exposed cedar on both sides, including the pergola top</b>. Total: {usd(REV9_A)} → <b>{usd(t["total_geral"])}</b> (+{usd(t["total_geral"] - REV9_A)}). Design and dimensions are unchanged.</p>
<h2>Scope</h2>
<ul>
<li>22'-1" long, <b>8'-0" tall</b> horizontal privacy screen with pergola top, finished on both sides, following the reference image.</li>
<li><b>{n} clad posts</b> (treated-pine core + cedar cladding) at {fmt(G.entre_eixos)} on center, clear bay {fmt(G.vao)}. Core: <b>treated pine 4x6</b>, set with its 5 1/2" side across the fence, <b>embedded 36"</b> in Ø16" concrete footings over 6" of gravel (holes dug with a rented mini skid steer and auger). Above grade each post is clad with cedar 2x6 faces and 1" side boards, 5 1/2" wide with flush faces.</li>
<li><b>{G.fiadas} cedar slats per bay</b> (2x2, about {fmt(G.espaco)} gaps), held in notched side boards: even spacing, no visible fasteners on the slats.</li>
<li><b>Pergola top:</b> cedar 2x8 beams on both sides, <b>bolted straight to the post cores</b> with 4 x 1/2" thru-bolts per post (the face boards end under the beams), angled beam ends (no end caps), and <b>{len(G.xc)} cedar 2x6 rafters</b> with cloud-lift ends at each post and mid-bay, set in notches in the beams.</li>
<li><b>Stain &amp; sealer on all cedar</b> (faces, side boards, slats, beams and rafters), both sides: Ready Seal, color Natural Cedar. Details below.</li>
<li>Solid wood only, <b>no composite</b>; all lumber planed on 4 sides (S4S). Coated trim-head deck screws (hidden) and galvanized thru-bolts.</li>
<li>All visible parts are pre-cut, eased and finished in our shop to keep on-site work short. Cleanup and debris removal included.</li>
</ul>
<h2>Price</h2>
<table>
<tr><td>Materials <span class='s'>(incl. stain &amp; sealer, 8.25% Mecklenburg sales tax and equipment rental {usd(A['rent'])}; subject to stock availability)</span></td><td class='r'>{usd(t['material_total'])}</td></tr>
<tr><td>Labor — shop pre-cutting and finishing {A['shop']:.0f} h + on-site installation {A['field']:.0f} h <span class='s'>({t['horas']:.0f} h × ${p['taxa_hora_usd']:.0f}/h)</span></td><td class='r'>{usd(t['mao_de_obra_total'])}</td></tr>
<tr><td>Service fee</td><td class='r'>{usd(t['taxa_fixa'])}</td></tr>
<tr class='tot'><td>Total</td><td class='r'>{usd(t['total_geral'])}</td></tr></table>
<div class="pb"></div>
<h2>Finish — stain &amp; sealer</h2>
<table>
<tr><th style="width:24%">Product</th><td><b>Ready Seal Exterior Stain &amp; Sealer for Wood</b>: oil-based, semi-transparent penetrating stain and sealer in one product (no separate sealer coat; no surface film to peel)</td></tr>
<tr><th>Color</th><td><b>Natural Cedar (#512)</b>: warm natural cedar tone that keeps the grain visible. Other colors in the same line at the same price on request (e.g. Light Oak, Pecan).</td></tr>
<tr><th>Where</th><td>All exposed cedar on both sides: post faces, notched and plain side boards, all {G.fiadas * nb} slats, both beams and all {len(G.xc)} pergola rafters (about {area} sq ft of wood surface). The treated-pine core is hidden and is not stained.</td></tr>
<tr><th>Application</th><td>Sprayed in the shop on all four sides of every piece before assembly (hidden faces are protected too, which helps the boards stay straight), saturating coat applied wet-on-wet; on-site touch-up after installation. Applied above 50°F, in dry weather.</td></tr>
<tr><th>Quantity</th><td>One 5-gal pail + one 1-gal can (touch-ups and a spare for future maintenance)</td></tr>
<tr><th>Maintenance</th><td>Clean and re-coat every 2–3 years, no stripping or sanding needed (same product and color).</td></tr>
</table>
<h2>Materials</h2>
{mat_html}
<p class="s">All lumber is S4S (planed on 4 sides) so faces, side boards and notches line up; no rough-sawn lumber and no composite.<br>
<b>Material prices may vary with supplier stock and availability at the time of purchase</b>; final material cost is confirmed when the order is placed.</p>
<h2>Optional extra (not included)</h2>
<p><b>Landscaping strip</b> along the neighbor side (22 ft): landscape fabric, edging and river rock border: <b>{usd(extra)}</b> (materials + labor).</p>
<h2>Installation sequence</h2>
<ol style="columns:2;column-gap:28pt;padding-left:18pt">{"".join(f"<li>{html.escape(x)}</li>" for x in passos)}</ol>
<h2>Notes, exclusions and payment</h2>
<ul>
<li><b>Material pricing:</b> based on current Lowe's / Home Depot pricing and lumber-yard estimates; <b>material cost may vary depending on stock availability</b> (species, grade, S4S sizes and lengths, substitutions). Final material cost is confirmed when the order is placed; changes above 5% will be reviewed with you before purchasing.</li>
<li>Staining requires dry weather above 50°F; in cold months the shop finishing can be done ahead and the on-site touch-up scheduled on a suitable day.</li>
<li>Not included: landscaping strip (optional above), permits/HOA fees, surveys, rock or root removal beyond normal digging, plants/vines. We will call NC811 before digging.</li>
<li>Payment: 40% deposit to order materials and start shop work · 40% when posts and slats are installed · 20% on completion.</li>
</ul>
<p class="s">Drawings follow: sheets A-1 to A-3 (cedar).</p>
</body></html>"""
    saida = os.path.join(AQUI, "propostas", "Kitchen-Privacy-Screen-Proposal-rev9.1-cedar.pdf")
    with tempfile.TemporaryDirectory() as td:
        hp = os.path.join(td, "p.html")
        open(hp, "w", encoding="utf-8").write(doc)
        txt = os.path.join(td, "t.pdf")
        subprocess.run([_chromium(), "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={txt}", "file://" + hp], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        if "--previa" in sys.argv:
            pre = os.path.join(AQUI, "propostas", "previa-rev9.1")
            for f in os.listdir(pre) if os.path.isdir(pre) else []:
                os.remove(os.path.join(pre, f))
            os.makedirs(pre, exist_ok=True)
            subprocess.run(["pdftoppm", "-png", "-r", "80", txt, os.path.join(pre, "pagina")], check=True)
            print(pre)
            return
        w = PdfWriter()
        for f in [txt, os.path.join(AQUI, OP[0][3], "privacy-screen.pdf")]:
            for pg in PdfReader(f).pages:
                w.add_page(pg)
        with open(saida, "wb") as f:
            w.write(f)
    open(os.path.join(AQUI, "propostas", "proposal-rev9.1-cedar.html"), "w", encoding="utf-8").write(doc)
    print(saida)


if __name__ == "__main__":
    main()
