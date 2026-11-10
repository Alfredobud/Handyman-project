#!/usr/bin/env python3
"""Plano de corte da oficina (PDF para imprimir) a partir do spec de uma proposta.

Uso: python3 gerar_plano_corte.py orcamento-7-postes
Saída: plano-corte/plano-de-corte-<pasta>.pdf (+ .html)

Usa a mesma geometria dos desenhos (privacy_screen.Geo) e o mesmo otimizador/catálogo
do orçamento (orcamento.otimizar), então as tábuas batem com a lista de compra.
Gabaritos 1:1: imprimir em "Tamanho real / 100%" e conferir o quadrado de 1".
"""
import html
import math
import os
import subprocess
import sys
import tempfile
from collections import defaultdict

AQUI = os.path.dirname(os.path.abspath(__file__))

def _skills_dir(inicio):
    """Sobe a partir desta pasta até achar .claude/skills (funciona em qualquer profundidade)."""
    d = inicio
    while True:
        cand = os.path.join(d, ".claude", "skills")
        if os.path.isdir(cand):
            return cand
        pai = os.path.dirname(d)
        if pai == d:
            raise SystemExit("não achei .claude/skills acima de " + inicio)
        d = pai


SKILLS = _skills_dir(os.path.dirname(os.path.abspath(__file__)))

RAIZ = SKILLS
sys.path.insert(0, os.path.join(RAIZ, "desenho-madeira", "templates"))
sys.path.insert(0, os.path.join(RAIZ, "desenho-madeira", "scripts"))
sys.path.insert(0, os.path.join(RAIZ, "orcamento-madeira", "scripts"))
import json  # noqa: E402
import privacy_screen as ps  # noqa: E402
import orcamento as orc  # noqa: E402
from cad import _chromium  # noqa: E402

fmt = ps.pes_pol

CORES = {"N": "#c9cfa3", "S": "#9fc5e8", "L": "#b4d7a8", "R": "#ffd966", "F": "#f4b183",
         "T": "#d5a6bd", "E": "#b7b7b7", "K": "#e06666"}


def pecas(G, spec):
    """Marca, nome, material (id do catálogo), comprimento, qtd, operações."""
    m = {c["material"] for c in spec["componentes"]}
    def mat(prefixos):
        for p in prefixos:
            for x in m:
                if x.startswith(p):
                    return x
        return prefixos[0]
    nb = G.n - 1
    m54, m24, m26, m28 = mat(["pt_5_4x6", "cedro_5_4x6"]), mat(["pt_2x4", "cedro_2x4"]), mat(["pt_2x6", "cedro_2x6"]), mat(["pt_2x8", "cedro_2x8"])
    L = [
        ("N", "Núcleo do poste 4x4 (enterrar 24\"; topo cortado na obra)", mat(["pt_4x4"]), round(G.comp_nucleo + 1.5, 3), G.n,
         "Cortar com sobra de 1 1/2\"; cortar o topo na obra no nível laser. Preservativo na ponta enterrada."),
        ("S", "Lateral serrilhada (1\" x 3 1/2\")", m54, G.comp_rev, 2 * nb,
         f"Ripar 5/4x6 para 3 1/2\". {G.fiadas} encaixes (tabela 1). Deixar a aresta arredondada do lado de fora."),
        ("L", "Lateral lisa, postes de ponta (1\" x 3 1/2\")", m54, G.comp_rev, 2, "Ripar 5/4x6 para 3 1/2\". Ajustar o topo na obra (etapa 7)."),
        ("R", "Ripa 2x4 deitada", m24, round(G.comp_ripa, 3), G.fiadas * nb, "Corte com batente; quebrar arestas."),
        ("F", "Face do poste 2x6", m26, G.comp_rev, 2 * G.n, "Corte com batente; quebrar arestas."),
    ]
    for j, c in enumerate(G.pecas_viga):
        L.append((f"T{j + 1}", f"Tábua de topo 2x8 — peça {j + 1} de {len(G.pecas_viga)} (fazer 2: uma de cada lado)", m28, round(c, 3), 2,
                  "Entalhes dos caibros conforme tabela 2; furo do parafuso passante em cada poste."))
    L += [
        ("E", "Fechamento da ponta das tábuas de topo 2x8", m28, G.fech_larg, 2, "Corte reto; quebrar arestas."),
        ("K", "Caibro do pergolado 2x6 (ponta tipo nuvem)", m26, G.g["caibro"]["comprimento"], len(G.xc),
         "Traçar as duas pontas com o gabarito 1:1 (pág. de gabaritos); tico-tico e lixa."),
    ]
    return L


def otimizar_por_material(L, cat, kerf, perda):
    por_mat = defaultdict(list)
    for marca, nome, mat, comp, qtd, _ in L:
        por_mat[mat] += [(comp, marca)] * qtd
    res = {}
    for mat, cortes in por_mat.items():
        tab = orc.otimizar(cortes, cat[mat]["comprimentos"], kerf)
        extra = 0 if mat.startswith("pt_4x4") else math.ceil(len(tab) * perda)   # núcleos: sem sobra (igual ao orçamento)
        res[mat] = (tab, extra)
    return res


def svg_tabua(t, kerf, escala=6.0, alt=26):
    """Barra da tábua com os cortes (escala px por polegada)."""
    W = t["comprimento_in"] * escala
    o = [f'<svg width="{W + 2:.0f}" height="{alt + 2}" viewBox="-1 -1 {W + 2:.0f} {alt + 2}">',
         f'<rect x="0" y="0" width="{W:.1f}" height="{alt}" fill="#f3f3f3" stroke="#444"/>']
    x = 0.0
    for comp, marca in sorted(t["cortes"], key=lambda c: -c[0]):
        w = comp * escala
        cor = CORES.get(marca[0], "#ddd")
        o.append(f'<rect x="{x:.1f}" y="0" width="{w:.1f}" height="{alt}" fill="{cor}" stroke="#444"/>')
        if w > 34:
            o.append(f'<text x="{x + w / 2:.1f}" y="{alt / 2 + 4}" font-size="10" text-anchor="middle">{marca} {html.escape(fmt(comp))}</text>')
        else:
            o.append(f'<text x="{x + w / 2:.1f}" y="{alt / 2 + 4}" font-size="9" text-anchor="middle">{marca}</text>')
        x += w + kerf * escala
    sobra = t["comprimento_in"] - sum(c for c, _ in t["cortes"]) - kerf * (len(t["cortes"]) - 1)
    if sobra > 1:
        o.append(f'<text x="{(x + W) / 2:.1f}" y="{alt / 2 + 4}" font-size="9" fill="#777" text-anchor="middle">sobra {html.escape(fmt(sobra))}</text>')
    o.append("</svg>")
    return "".join(o)


def tabela_encaixes(G):
    r = G.g["ripa"]
    fe = r["folga_encaixe"]
    lin = []
    for i, y in enumerate(G.ripas_y):
        a = y - fe / 2 - G.y_rev0
        b = y + r["larg"] + fe / 2 - G.y_rev0
        lin.append((i + 1, a, b))
    return lin


def tabela_entalhes(G):
    """Entalhes de caibro em cada peça de topo (posições a partir da ponta esquerda da peça)."""
    vg, cb = G.g["viga"], G.g["caibro"]
    larg = cb["esp"] + 1 / 16
    pts = [G.x_viga0] + [G.cx[i] for i in G.emendas] + [G.x_viga1]
    out = []
    for j, (a, b) in enumerate(zip(pts, pts[1:])):
        ent = []
        for i, cx in enumerate(G.cx):
            e0, e1 = cx - larg / 2, cx + larg / 2
            if e1 <= a + 1e-6 or e0 >= b - 1e-6:
                continue
            ini, fim = max(e0, a) - a, min(e1, b) - a
            meia = (e0 < a - 1e-6) or (e1 > b + 1e-6)
            ent.append((i + 1, ini, fim, meia))
        out.append((j + 1, b - a, ent))
    return out, vg["entalhe"], larg


def svg_gabarito_caibro(G):
    cb = G.g["caibro"]
    alt, comp = cb["alt"], 9.6
    ponta = ps._ponta(alt, cb["perfil"])
    pts = [(0, alt), (comp, alt), (comp, 0)] + [(dz, y) for dz, y in reversed(ponta)]
    m = 0.2
    W, H = comp + 2 * m, alt + 2 * m
    poly = " ".join(f"{x + m:.4f},{alt - y + m:.4f}" for x, y in pts)
    return (f'<svg width="{W}in" height="{H}in" viewBox="0 0 {W} {H}">'
            f'<polygon points="{poly}" fill="none" stroke="#000" stroke-width="0.02"/>'
            f'<line x1="{comp + m}" y1="{m}" x2="{comp + m}" y2="{alt + m}" stroke="#000" stroke-width="0.01" stroke-dasharray="0.1,0.08"/>'
            ''
            '</svg>')


def svg_gabarito_serrilhado(G):
    """Trecho 1:1: encaixe N inteiro + início do encaixe N+1 (define o passo do gabarito)."""
    r = G.g["ripa"]
    fe = r["folga_encaixe"]
    larg, prof = G.nuc, r["esp"]
    a1 = G.ripas_y[0] - fe / 2 - G.y_rev0
    b1 = a1 + r["larg"] + fe
    a2 = a1 + G.passo
    y0, y1 = a1 - 0.75, a2 + 1.25            # trecho mostrado (medidas a partir da base da tábua)
    H = y1 - y0
    m = 0.25
    W = larg + 2 * m + 3.2
    def Y(y):
        return (y1 - y) + m
    o = [f'<svg width="{W}in" height="{H + 2 * m}in" viewBox="0 0 {W} {H + 2 * m}">',
         f'<polyline points="{m},{Y(y0)} {m},{Y(y1)}" fill="none" stroke="#000" stroke-width="0.02"/>',
         f'<polyline points="{m + larg},{Y(y0)} {m + larg},{Y(a1)} {m + larg - prof},{Y(a1)} {m + larg - prof},{Y(b1)} '
         f'{m + larg},{Y(b1)} {m + larg},{Y(a2)} {m + larg - prof},{Y(a2)} {m + larg - prof},{Y(y1)}" fill="none" stroke="#000" stroke-width="0.02"/>',
         f'<line x1="{m}" y1="{Y(y0)}" x2="{m + larg}" y2="{Y(y0)}" stroke="#000" stroke-width="0.01" stroke-dasharray="0.1,0.08"/>',
         f'<line x1="{m}" y1="{Y(y1)}" x2="{m + larg}" y2="{Y(y1)}" stroke="#000" stroke-width="0.01" stroke-dasharray="0.1,0.08"/>',
         f'<rect x="{m + larg - prof}" y="{Y(b1)}" width="{prof}" height="{b1 - a1}" fill="#e6e6e6" fill-opacity="0.6" stroke="#000" stroke-width="0.02"/>',
         f'<text x="{m + larg + 0.12}" y="{Y((a1 + b1) / 2)}" font-size="0.15">encaixe: {html.escape(fmt(b1 - a1))} x {html.escape(fmt(prof))}</text>',
         f'<text x="{m + larg + 0.12}" y="{Y((a1 + b1) / 2) + 0.22}" font-size="0.13">(1º encaixe começa a {html.escape(fmt(a1))} da base)</text>',
         f'<text x="{m + larg + 0.12}" y="{Y((b1 + a2) / 2) + 0.05}" font-size="0.15">dente: {html.escape(fmt(a2 - b1))}</text>',
         f'<text x="{m + larg + 0.12}" y="{Y(a2) - 0.3}" font-size="0.15">passo: {html.escape(fmt(G.passo))} (início a início)</text>',
         f'<text x="{m + larg + 0.12}" y="{Y(y0) - 0.1}" font-size="0.13">← borda do lado do vizinho (encaixes)</text>',
         f'<text x="{m + 0.05}" y="{Y(y0) + 0.18}" font-size="0.12">↓ para a base da tábua</text>',
         "</svg>"]
    return "".join(o)


def main():
    pasta = sys.argv[1] if len(sys.argv) > 1 else "orcamento-7-postes"
    spec = json.load(open(os.path.join(AQUI, pasta, "spec.json"), encoding="utf-8"))
    G = ps.Geo(ps.mescla(ps.PADRAO, spec["geometria"]))
    p = dict(orc.PARAMS_PADRAO); p.update(spec.get("parametros", {}))
    cat = orc.carregar_precos([os.path.join(orc.REF_DIR, "precos.csv"), os.path.join(AQUI, pasta, spec.get("precos", "precos.csv"))])
    L = pecas(G, spec)
    res = otimizar_por_material(L, cat, p["kerf_in"], p["perda"])

    # lista de compra
    compra = []
    for mat, (tab, extra) in res.items():
        cont = defaultdict(int)
        for t in tab:
            cont[t["comprimento_in"] / 12] += 1
        mais = max(cont, key=lambda k: (cont[k], k))
        for ft in sorted(cont):
            compra.append((cat[mat]["descricao"], ft, cont[ft], cont[ft] + (extra if ft == mais else 0)))
    titulo = spec.get("projeto", "Privacy screen")
    css = """@page{size:Letter;margin:0.5in} body{font-family:'DejaVu Sans',Arial,sans-serif;font-size:8.8pt;color:#222}
h1{font-size:16pt;margin:0} h2{font-size:12pt;border-bottom:2px solid #6a8f3c;margin:12pt 0 5pt;padding-bottom:2pt}
table{border-collapse:collapse;width:100%;page-break-inside:auto} td,th{border:1px solid #bbb;padding:2.5pt 5pt;vertical-align:top}
th{background:#eef3e6;text-align:left} .n{text-align:right} .s{color:#555;font-size:8.5pt} .pb{page-break-before:always}
.tab{margin:3pt 0 6pt} .lbl{font-size:8.5pt;color:#333;margin-bottom:1pt} .chk{width:14pt}
@page land{size:Letter landscape;margin:0.4in} .land{page:land}
.box{display:inline-block;width:10pt;height:10pt;margin-right:4pt;vertical-align:middle;border:1px solid #444}"""
    H = [f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>",
         f"<h1>Plano de corte — oficina</h1><div class='s'>{html.escape(titulo)} · rev. {spec.get('revisao', '')} · "
         f"{G.n} postes · medidas reais (S4S) · serra {fmt(p['kerf_in'])} descontada em cada corte</div>",
         "<h2>1. Peças (lista de corte)</h2><table><tr><th>Marca</th><th>Peça</th><th>Material</th><th class='n'>Compr.</th>"
         "<th class='n'>Qtd</th><th>Operações na oficina</th><th class='chk'>✓</th></tr>"]
    for marca, nome, mat, comp, qtd, op in L:
        H.append(f"<tr><td><span class='box' style='background:{CORES.get(marca[0], '#ddd')}'></span><b>{marca}</b></td>"
                 f"<td>{html.escape(nome)}</td><td>{html.escape(cat[mat]['descricao'])}</td><td class='n'>{html.escape(fmt(comp))}</td>"
                 f"<td class='n'>{qtd}</td><td>{html.escape(op)}</td><td></td></tr>")
    H.append("</table>")
    H.append("<h2>2. Lista de compra</h2><table><tr><th>Material</th><th class='n'>Compr.</th><th class='n'>Tábuas no plano</th>"
             f"<th class='n'>Comprar (c/ {p['perda']:.0%} de sobra)</th></tr>")
    for desc, ft, n0, n1 in compra:
        H.append(f"<tr><td>{html.escape(desc)}</td><td class='n'>{ft:g}'</td><td class='n'>{n0}</td><td class='n'><b>{n1}</b></td></tr>")
    H.append("</table><p class='s'>Escolher tábuas retas, sem rachaduras nas pontas. Pinus tratado: preferir KDAT; guardar empilhado com espaçadores até o corte.</p>")

    H.append("<div class='pb'></div><h2>3. Plano de corte por tábua</h2>"
             "<p class='s'>Cada barra é uma tábua; cortar da esquerda para a direita, das peças maiores para as menores. "
             "Tábuas iguais estão agrupadas (×N).</p>")
    for mat, (tab, extra) in res.items():
        H.append(f"<h3 style='font-size:10.5pt;margin:8pt 0 2pt'>{html.escape(cat[mat]['descricao'])}</h3>")
        grupos = defaultdict(list)
        for t in tab:
            chave = (t["comprimento_in"], tuple(sorted(t["cortes"], key=lambda c: (-c[0], c[1]))))
            grupos[chave].append(t)
        for (comp, cortes), ts in sorted(grupos.items(), key=lambda kv: (-len(kv[1]), -kv[0][0])):
            desc = " + ".join(f"{sum(1 for c in cortes if c == x)}× {x[1]} {fmt(x[0])}" for x in sorted(set(cortes), key=lambda c: -c[0]))
            esc = min(6.0, 7.3 * 96 / comp)
            H.append(f"<div class='tab'><div class='lbl'><b>×{len(ts)}</b> tábua de {comp / 12:g}' — {html.escape(desc)}</div>"
                     f"{svg_tabua(ts[0], p['kerf_in'], escala=esc)}</div>")
        if extra:
            H.append(f"<div class='s'>+ {extra} tábua(s) de sobra para defeitos.</div>")

    enc = tabela_encaixes(G)
    H.append("<div class='pb'></div><h2>4. Tabela 1 — encaixes da lateral serrilhada (S)</h2>"
             f"<p class='s'>Medidas a partir da <b>base</b> da tábua (lado do chão). Encaixe de {fmt(G.g['ripa']['larg'] + G.g['ripa']['folga_encaixe'])} de altura × "
             f"{fmt(G.g['ripa']['esp'])} de profundidade, na borda do <b>lado do vizinho</b>. Passo {fmt(G.passo)}. "
             f"Marcar todas as {2 * (G.n - 1)} tábuas juntas (grampeadas lado a lado) ou usar o gabarito 1:1.</p>"
             "<table><tr><th>Encaixe</th><th class='n'>De</th><th class='n'>Até</th><th>Encaixe</th><th class='n'>De</th><th class='n'>Até</th></tr>")
    meio = math.ceil(len(enc) / 2)
    for k in range(meio):
        a = enc[k]
        b = enc[k + meio] if k + meio < len(enc) else None
        H.append(f"<tr><td>{a[0]}</td><td class='n'>{html.escape(fmt(a[1]))}</td><td class='n'>{html.escape(fmt(a[2]))}</td>"
                 + (f"<td>{b[0]}</td><td class='n'>{html.escape(fmt(b[1]))}</td><td class='n'>{html.escape(fmt(b[2]))}</td>" if b else "<td></td><td></td><td></td>")
                 + "</tr>")
    H.append(f"</table><p class='s'>Acima do último encaixe sobram {fmt(G.comp_rev - enc[-1][2])} de tábua até o topo.</p>")

    ent, prof, larg = tabela_entalhes(G)
    H.append(f"<h2>5. Tabela 2 — entalhes das tábuas de topo (T)</h2><p class='s'>Medidas a partir da <b>ponta esquerda</b> de cada peça "
             f"(olhando a cerca pelo lado do vizinho). Entalhe de {fmt(larg)} de largura × {fmt(prof)} de profundidade na borda de <b>cima</b>. "
             "Fazer cada peça em dobro (uma de cada lado do poste). Nas emendas, o entalhe fica dividido entre as duas peças (½ entalhe em cada).</p>"
             "<table><tr><th>Peça</th><th class='n'>Compr.</th><th>Entalhes (poste: de → até)</th></tr>")
    for j, comp, es in ent:
        txt = "; ".join(f"P{i}: {fmt(a)} → {fmt(b)}" + (" (½)" if meia else "") for i, a, b, meia in es)
        H.append(f"<tr><td>T{j}</td><td class='n'>{html.escape(fmt(comp))}</td><td>{html.escape(txt)}</td></tr>")
    H.append("</table><p class='s'>Furo do parafuso passante 1/2\": no centro de cada poste, a 2 3/4\" da borda de baixo da tábua. "
             "Furar as duas tábuas de cada trecho juntas (grampeadas) para alinhar.</p>")

    H.append("<div class='pb'></div><h2>6. Gabaritos em tamanho real (1:1)</h2>"
             "<p class='s'><b>Imprimir em \"Tamanho real / 100%\"</b> e conferir o quadrado ao lado: deve medir exatamente 1\" x 1\". "
             "Colar em compensado e recortar para fazer o gabarito.</p>"
             "<svg width='1in' height='1in' viewBox='0 0 1 1'><rect x='0.01' y='0.01' width='0.98' height='0.98' fill='none' stroke='#000' stroke-width='0.02'/>"
             "<text x='0.5' y='0.56' font-size='0.2' text-anchor='middle'>1\"</text></svg>"
             f"<h3 style='font-size:10pt;margin:4pt 0'>Lateral serrilhada (S): gabarito do passo</h3>{svg_gabarito_serrilhado(G)}"
             "<div class='land'><div style='font-size:9pt;font-weight:bold;margin-bottom:4pt'>Gabarito 1:1: ponta do caibro (K), usar nas duas pontas. "
             "Caibro 2x6 (5 1/2\" de altura), topo da peça em cima; linha tracejada = a peça continua.</div>"
             f"{svg_gabarito_caibro(G)}</div>"
             "</body></html>")
    out_dir = os.path.join(AQUI, "plano-corte")
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.join(out_dir, f"plano-de-corte-{pasta.replace('orcamento-', '').replace('orcamento', '10-postes')}")
    doc = "\n".join(H)
    open(base + ".html", "w", encoding="utf-8").write(doc)
    with tempfile.TemporaryDirectory() as td:
        hp = os.path.join(td, "p.html")
        open(hp, "w", encoding="utf-8").write(doc)
        subprocess.run([_chromium(), "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={base}.pdf", "file://" + hp], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    print(base + ".pdf")
    for desc, ft, n0, n1 in compra:
        print(f"  {desc} {ft:g}': {n1}")


if __name__ == "__main__":
    main()
