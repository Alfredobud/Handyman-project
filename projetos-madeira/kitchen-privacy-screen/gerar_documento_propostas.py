#!/usr/bin/env python3
"""Monta o documento único das propostas (7 e 10 postes) + pranchas, em inglês.

Uso: python3 gerar_documento_propostas.py
Saída: propostas/Kitchen-Privacy-Screen-Proposals.pdf
Lê orcamento*/orcamento.json (rodar orcamento.py antes) e desenhos/*/privacy-screen.pdf.
"""
import html
import json
import os
import subprocess
import sys
import tempfile

from pypdf import PdfReader, PdfWriter

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "..", ".claude", "skills", "desenho-madeira", "templates"))
sys.path.insert(0, os.path.join(AQUI, "..", "..", ".claude", "skills", "desenho-madeira", "scripts"))
import privacy_screen as ps  # noqa: E402
from cad import _chromium  # noqa: E402

OPCOES = [("A", "10 posts", "orcamento", "10-postes"), ("B", "7 posts", "orcamento-7-postes", "7-postes")]
OPC_KEYS = ("manta_paisagismo", "borda_paisagismo", "pedra_rio")


def usd(v):
    return f"${v:,.0f}"


def carregar(pasta):
    s = json.load(open(os.path.join(AQUI, pasta, "spec.json"), encoding="utf-8"))
    r = json.load(open(os.path.join(AQUI, pasta, "orcamento.json"), encoding="utf-8"))
    G = ps.Geo(ps.mescla(ps.PADRAO, s["geometria"]))
    t, p = r["totais"], r["parametros"]
    shop = sum(m["horas"] for m in r["mao_de_obra"] if str(m["tarefa"]).startswith("oficina"))
    opt = (sum(c["subtotal"] for c in r["compra"] if c["material"] in OPC_KEYS) * (1 + p["imposto_material"])
           + sum(m["horas"] for m in r["mao_de_obra"] if m["tarefa"] == "paisagismo_base") * p["taxa_hora_usd"])
    rent = sum(c["subtotal"] for c in r["compra"] if c["material"] in ("aluguel_mini_skid_auger", "frete_equipamento"))
    return dict(s=s, r=r, G=G, t=t, p=p, shop=shop, field=t["horas"] - shop, opt=opt, rent=rent)


def tabela_materiais(dados):
    GA, GB = dados[0]["G"], dados[1]["G"]

    def q(G, k):
        nb = G.n - 1
        return {"core": G.n, "faces": 2 * G.n, "notched": 2 * nb, "plain": 2, "slats": G.fiadas * nb,
                "top": 2 * len(G.pecas_viga), "caps": 2, "rafters": len(G.xc)}[k]
    linhas = [
        ("Post core (buried 24\")", "core", "Pressure-treated Southern Yellow Pine 4x4, #2, ground contact (UC4B)", "S4S (planed)", "3 1/2\" x 3 1/2\" x 10'"),
        ("Post faces (house + neighbor)", "faces", "Western Red Cedar 2x6, kiln-dried", "S4S (planed)", f"1 1/2\" x 5 1/2\" x {ps.pes_pol(GA.comp_rev)}"),
        ("Notched side boards", "notched", "Western Red Cedar 5/4x6, kiln-dried, ripped to 3 1/2\"", "S4S, eased edges", f"1\" x 3 1/2\" x {ps.pes_pol(GA.comp_rev)}"),
        ("Plain side boards (end posts)", "plain", "Western Red Cedar 5/4x6, kiln-dried, ripped to 3 1/2\"", "S4S, eased edges", f"1\" x 3 1/2\" x {ps.pes_pol(GA.comp_rev)}"),
        ("Slats (laid flat)", "slats", "Western Red Cedar 2x4, kiln-dried", "S4S (planed)", f"1 1/2\" x 3 1/2\" x {ps.pes_pol(GA.comp_ripa)} (A) / {ps.pes_pol(GB.comp_ripa)} (B)"),
        ("Top boards (notched for rafters)", "top", "Western Red Cedar 2x8, kiln-dried", "S4S (planed)", "1 1/2\" x 7 1/4\" (3 pieces per side, 8')"),
        ("Top-board end caps", "caps", "Western Red Cedar 2x8, kiln-dried", "S4S (planed)", f"1 1/2\" x 7 1/4\" x {ps.pes_pol(GA.fech_larg)}"),
        ("Pergola rafters (cloud-lift ends)", "rafters", "Western Red Cedar 2x6, kiln-dried", "S4S (planed)", "1 1/2\" x 5 1/2\" x 36\""),
    ]
    out = ["<table class='mat'><tr><th>Part</th><th>Material (species, grade, treatment)</th><th>Surface</th><th>Actual size</th>"
           "<th>Qty A<br>10 posts</th><th>Qty B<br>7 posts</th></tr>"]
    for nome, k, mat, sup, tam in linhas:
        out.append(f"<tr><td>{html.escape(nome)}</td><td>{html.escape(mat)}</td><td>{sup}</td><td>{html.escape(tam)}</td>"
                   f"<td class='n'>{q(GA, k)}</td><td class='n'>{q(GB, k)}</td></tr>")
    out.append("</table>")
    return "\n".join(out)


def bloco_opcao(letra, nome, d):
    G, t, p = d["G"], d["t"], d["p"]
    warp = ("Slat span is well under the 36\" limit we use to prevent warping." if G.vao <= 36 else
            f"Slat span ({ps.pes_pol(G.vao)}) is above our conservative 36\" limit (still under the 48\" maximum for 2x4 cedar): "
            "slightly more risk of bowing over time than Option A.")
    phi = "φ³ (Fibonacci 55/13)" if G.n == 10 else "φ⁴ (Fibonacci 89/13)" if G.n == 7 else ""
    return f"""
<section class="opt">
<h2>Option {letra} — {nome}</h2>
<ul>
<li><b>{G.n} composite posts</b> at {ps.pes_pol(G.entre_eixos)} on center, clear bay {ps.pes_pol(G.vao)}
    (bay-to-post ratio {G.vao / G.W[1]:.2f} ≈ {phi}). {html.escape(warp)}</li>
<li><b>{G.fiadas * (G.n - 1)} cedar slats</b> ({G.fiadas} per bay, {ps.pes_pol(G.espaco)} gaps), {ps.pes_pol(G.comp_ripa)} long, held in notched side boards.</li>
<li><b>Pergola top:</b> {2 * len(G.pecas_viga)} notched cedar top boards, 2 end caps, {len(G.xc)} rafters with cloud-lift ends.</li>
<li>Drawings: sheets {letra}-1 to {letra}-3 at the end of this document.</li>
</ul>
<table class="price">
<tr><td>Materials <span class="s">(incl. 8.25% Mecklenburg sales tax and equipment rental {usd(d['rent'])})</span></td><td>{usd(t['material_total'])}</td></tr>
<tr><td>Labor — shop pre-cutting {d['shop']:.0f} h + on-site installation {d['field']:.0f} h <span class="s">({t['horas']:.0f} h × ${p['taxa_hora_usd']:.0f}/h)</span></td><td>{usd(t['mao_de_obra_total'])}</td></tr>
<tr><td>Service fee</td><td>{usd(t['taxa_fixa'])}</td></tr>
<tr class="tot"><td>Total Option {letra}</td><td>{usd(t['total_geral'])}</td></tr>
</table>
<p class="s">Included option: landscaping strip (landscape fabric, edging and river rock along the neighbor side), about {usd(d['opt'])} of the total; can be removed.</p>
</section>"""


def main():
    dados = [carregar(p) for _, _, p, _ in OPCOES]
    A, B = dados
    css = """
@page{size:Letter;margin:0.6in}
body{font-family:'DejaVu Sans',Arial,sans-serif;font-size:10pt;color:#222;line-height:1.35}
h1{font-size:19pt;margin:0 0 2pt} h2{font-size:13pt;border-bottom:2px solid #b46a2c;padding-bottom:2pt;margin:16pt 0 6pt}
h3{font-size:11pt;margin:12pt 0 4pt}
.sub{color:#555;margin-bottom:10pt}
table{border-collapse:collapse;width:100%;page-break-inside:avoid} td,th{border:1px solid #bbb;padding:4pt 6pt;vertical-align:top}
th{background:#f1e6da;text-align:left} .n{text-align:center}
table.cmp td:nth-child(n+2), table.cmp th:nth-child(n+2){text-align:right;width:22%}
table.price td:last-child{text-align:right;width:20%;white-space:nowrap} tr.tot td{font-weight:bold;background:#f7efe6}
table.mat{font-size:8.5pt} .s{color:#555;font-size:8.5pt}
.pb{page-break-before:always} section.opt{page-break-inside:avoid} ul{margin:4pt 0 8pt 16pt;padding:0} li{margin-bottom:3pt}
"""
    cmp_rows = [
        ("Posts", "10", "7"),
        ("Post spacing (on center)", ps.pes_pol(A["G"].entre_eixos), ps.pes_pol(B["G"].entre_eixos)),
        ("Clear bay (slat span)", ps.pes_pol(A["G"].vao), ps.pes_pol(B["G"].vao)),
        ("Warping risk", "Low (< 36\")", "Moderate (> 36\")"),
        ("Slats", str(A["G"].fiadas * 9), str(B["G"].fiadas * 6)),
        ("Materials", usd(A["t"]["material_total"]), usd(B["t"]["material_total"])),
        ("Labor (shop + site)", f"{usd(A['t']['mao_de_obra_total'])} ({A['t']['horas']:.0f} h)", f"{usd(B['t']['mao_de_obra_total'])} ({B['t']['horas']:.0f} h)"),
        ("Service fee", usd(A["t"]["taxa_fixa"]), usd(B["t"]["taxa_fixa"])),
    ]
    cmp_html = ("<table class='cmp'><tr><th></th><th>Option A — 10 posts</th><th>Option B — 7 posts</th></tr>"
                + "".join(f"<tr><td>{html.escape(a)}</td><td>{html.escape(b)}</td><td>{html.escape(c)}</td></tr>" for a, b, c in cmp_rows)
                + f"<tr class='tot'><td>Total</td><td>{usd(A['t']['total_geral'])}</td><td>{usd(B['t']['total_geral'])}</td></tr></table>")
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body>
<h1>Kitchen Privacy Screen — Proposal</h1>
<div class="sub">Cornelius, NC · November 10, 2026 · valid for 30 days · two options</div>

<h2>Scope (both options)</h2>
<ul>
<li>22'-1" long, 8'-0" tall horizontal privacy screen with pergola top, finished on both sides, matching the reference image.</li>
<li><b>Posts:</b> pressure-treated pine 4x4 core (ground contact), set <b>24" deep</b> in concrete over 6" of gravel, holes dug with a rented mini skid steer and auger. Above grade, each post is clad in cedar: 2x6 faces and 1" side boards, all 5 1/2" wide with flush faces. The buried part is treated pine only, for lower cost and longer life in the soil.</li>
<li><b>Slats:</b> cedar 2x4 laid flat, held in notched side boards (even spacing, no visible fasteners on the slat faces).</li>
<li><b>Pergola top:</b> notched cedar 2x8 top boards on both sides, end caps for a solid-beam look, cedar 2x6 rafters with cloud-lift ends, one per post.</li>
<li><b>Fasteners:</b> coated trim-head deck screws (small countersunk heads, rated for treated lumber) and 1/2" galvanized through-bolts.</li>
<li>All visible parts are pre-cut, notched and eased in our shop to keep on-site work short. Cleanup and debris removal included.</li>
</ul>

<h2>Comparison</h2>
{cmp_html}
<p class="s">Option A uses the golden-ratio spacing with the shortest slat span (best against warping). Option B uses fewer posts and fewer parts (lower cost), with longer slats.</p>

<div class="pb"></div>
<h2>Materials and finish</h2>
{tabela_materiais(dados)}
<p class="s"><b>Finish:</b> all cedar is Western Red Cedar, kiln-dried and <b>S4S (surfaced/planed on 4 sides)</b>, so every piece has true, consistent dimensions and the post faces, side boards and notches line up. Rough-sawn cedar (as stocked at some big-box stores in 2x6/2x8) is not used; if S4S is not stocked locally, it will be sourced from a lumber yard. Cedar is left natural (no stain needed) and will weather to silver-gray; sealer available on request.</p>

{bloco_opcao("A", "10 posts", A)}
{bloco_opcao("B", "7 posts", B)}

<h2>Installation sequence (both options)</h2>
<ol style='columns:2'><li>Holes (machine auger)</li><li>Posts (treated pine cores in concrete)</li><li>Level post tops</li><li>Notched side boards (pre-cut), from the neighbor side</li><li>Slats (pre-cut)</li><li>Front closure (2x6 faces)</li><li>Side closure (end posts)</li><li>Top boards (pre-notched)</li><li>End caps (pre-cut)</li><li>Pergola rafters (pre-cut)</li></ol>

<h2>Notes, exclusions and payment</h2>
<ul>
<li>Material prices are based on current Lowe's / Home Depot pricing and lumber-yard estimates; they will be confirmed at purchase. Changes above 5% may be adjusted.</li>
<li>Not included: permits/HOA fees, surveys, rock or root removal beyond normal digging, plants/vines. We will call NC811 before digging.</li>
<li>Payment: 40% deposit to order materials and start shop work · 40% when posts and slats are installed · 20% on completion.</li>
</ul>
<p class="s">Drawings follow: Option A (10 posts) sheets A-1 to A-3, then Option B (7 posts) sheets B-1 to B-3.</p>
</body></html>"""
    saida = os.path.join(AQUI, "propostas", "Kitchen-Privacy-Screen-Proposals.pdf")
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    nav = _chromium()
    with tempfile.TemporaryDirectory() as td:
        hp = os.path.join(td, "p.html")
        open(hp, "w", encoding="utf-8").write(doc)
        txt = os.path.join(td, "texto.pdf")
        subprocess.run([nav, "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={txt}", "file://" + hp], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        w = PdfWriter()
        for f in [txt] + [os.path.join(AQUI, "desenhos", d, "privacy-screen.pdf") for _, _, _, d in OPCOES]:
            for pg in PdfReader(f).pages:
                w.add_page(pg)
        with open(saida, "wb") as f:
            w.write(f)
    with open(os.path.join(AQUI, "propostas", "proposals.html"), "w", encoding="utf-8") as f:
        f.write(doc)
    print(saida)


if __name__ == "__main__":
    main()
