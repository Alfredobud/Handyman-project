#!/usr/bin/env python3
"""Cerca trançada (woven fence): tábuas horizontais que passam alternadamente na frente e
atrás de sarrafos verticais, entre postes com canal (batentes) — UM MÓDULO + implantação.

Uso: python3 cerca_trancada.py spec.json --saida pasta [--previa]

Eixos: x ao longo da cerca (0 = eixo do poste esquerdo), y vertical (0 = terreno),
z na espessura (0 = face do LADO DA CASA). Medidas reais em polegadas.
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import cad  # noqa: E402
from cad import Vista, Prancha, exportar, pes_pol  # noqa: E402

PHI = (1 + 5 ** 0.5) / 2

PADRAO = {
    "modulo_oc_in": 120, "trechos_ft": [40, 60, 40],
    "poste": {"larg": 5.5, "embutimento_in": 24, "brita_in": 6, "furo_diam_in": 12},
    "folga_terreno_in": 3.0,
    "tabua": {"esp": 0.75, "larg": 5.5, "fiadas": None},          # None = calcula pela proporção áurea
    "sarrafo": {"esp": 0.75, "larg": 1.5, "qtd": 3},              # sarrafos verticais do trançado
    "batente": {"esp": 0.75, "larg": 1.5},                        # canal nos postes (2 por lado)
    "travessa": {"esp": 1.5, "larg": 3.5},                        # 2x4 deitado embaixo e em cima
    "capa": {"esp": 1.5, "larg": 5.5, "beiral": 0.0},             # 2x6 de capeamento contínuo
    "rotulos": {"poste": "PT pine 6x6 S4S, ground contact", "tabua": "PT pine 1x6 S4S", "sarrafo": "PT pine 1x2 S4S",
                "batente": "PT pine 1x2 S4S", "travessa": "PT pine 2x4 S4S", "capa": "PT pine 2x6 S4S"},
}


def mescla(a, b):
    out = dict(a)
    for k, v in (b or {}).items():
        out[k] = mescla(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


class Geo:
    def __init__(self, g):
        self.g = g
        P, t, s, tr, cp = g["poste"]["larg"], g["tabua"], g["sarrafo"], g["travessa"], g["capa"]
        self.P, self.oc = P, g["modulo_oc_in"]
        self.vao = self.oc - P
        self.gap = g["folga_terreno_in"]
        # profundidade do trançado: sarrafo no meio, tábua passa na frente ou atrás
        self.zs0 = P / 2 - s["esp"] / 2
        self.zs1 = self.zs0 + s["esp"]
        self.zf = (self.zs0 - t["esp"], self.zs0)                 # tábua na frente (lado casa)
        self.zb = (self.zs1, self.zs1 + t["esp"])                 # tábua atrás (lado vizinho)
        self.canal = (self.zf[0], self.zb[1])
        # altura pela proporção áurea: altura total = módulo / φ
        alvo = self.oc / PHI
        fixo = self.gap + 2 * tr["esp"] + cp["esp"]
        self.fiadas = t["fiadas"] or max(1, int(math.floor((alvo - fixo) / t["larg"] + 1e-9)))
        self.h_trama = self.fiadas * t["larg"]
        self.y_tr0 = self.gap
        self.y_t0 = self.y_tr0 + tr["esp"]
        self.y_t1 = self.y_t0 + self.h_trama
        self.y_tr1 = self.y_t1 + tr["esp"]
        self.y_poste = self.y_tr1
        self.y_topo = self.y_poste + cp["esp"]
        self.razao = self.oc / self.y_topo
        self.alvo = alvo
        n = s["qtd"]
        self.xs = [P / 2 + self.vao * (j + 1) / (n + 1) for j in range(n)]   # centros dos sarrafos
        self.comp_tabua = self.vao + 2 * 0.75 - 0.25                          # entra 5/8" em cada canal
        self.comp_vertical = self.h_trama
        self.y_base = -g["poste"]["embutimento_in"]
        self.comp_poste = self.y_poste - self.y_base
        trechos = g["trechos_ft"]
        self.modulos = [round(L * 12 / self.oc) for L in trechos]
        self.n_mod = sum(self.modulos)
        self.n_postes = self.n_mod + 1                                       # trechos em "U", cantos compartilhados

    def frente(self, fiada, j):
        """True se a tábua da fiada passa na FRENTE do sarrafo j."""
        return (fiada + j) % 2 == 0


def _terreno(v, x0, x1, prof=8):
    v.poligono([(x0, -prof), (x1, -prof), (x1, 0), (x0, 0)], "solo")
    v.linha([(x0, 0), (x1, 0)], espessura=1.2)


def vista_modulo(G, esc=24):
    g = G.g
    t, tr, cp = g["tabua"], g["travessa"], g["capa"]
    v = Vista("MODULE ELEVATION — NEIGHBOR SIDE", esc)
    P = G.P
    _terreno(v, -P, G.oc + P)
    for xc in (0, G.oc):
        v.peca(xc - P / 2, 0, P, G.y_poste, "pt")
        v.peca(xc - P / 2, G.y_base, P, -G.y_base, "pt", tracejado=True)
        d = g["poste"]["furo_diam_in"]
        v.poligono([(xc - d / 2, G.y_base), (xc + d / 2, G.y_base), (xc + d / 2, 0), (xc - d / 2, 0)], "concreto", tracejado=True)
    x0, x1 = P / 2, G.oc - P / 2
    v.peca(x0, G.y_tr0, G.vao, tr["esp"], "pt")
    v.peca(x0, G.y_t1, G.vao, tr["esp"], "pt")
    for i in range(G.fiadas):
        y = G.y_t0 + i * t["larg"]
        v.peca(x0, y, G.vao, t["larg"], "madeira")
        # sombra do trançado: onde a tábua passa atrás do sarrafo (visto do vizinho = z alto), o sarrafo aparece
        for j, xs in enumerate(G.xs):
            if G.frente(i, j):        # tábua na frente (lado casa) -> do vizinho vê-se o sarrafo por cima
                v.peca(xs - g["sarrafo"]["larg"] / 2, y, g["sarrafo"]["larg"], t["larg"], "pt")
    v.peca(-P / 2 - cp["beiral"], G.y_poste, G.oc + P + 2 * cp["beiral"], cp["esp"], "pt")
    v.cota((0, -12), (G.oc, -12), -4, texto=f"{pes_pol(G.oc)} o.c. (module)", tam=6.5)
    v.cota((x0, G.y_topo), (x1, G.y_topo), 5, texto=f"{pes_pol(G.vao)} clear", tam=6)
    v.cotas_corrente([0] + G.xs + [G.oc], G.y_topo + 9, 0, tam=5)
    xr = G.oc + P + 4
    v.cotas_corrente([0, G.y_t0, G.y_t1, G.y_topo], xr, 0, horizontal=False, tam=5.5)
    v.cota((xr, 0), (xr, G.y_topo), 10, tam=6.5)
    v.cota((xr, G.y_base), (xr, 0), 0, tam=5.5)
    v.chamada((G.xs[0], G.y_t0 + 2.5 * t["larg"]), (G.xs[0] + 8, G.y_topo + 22),
              f"{G.fiadas} woven boards {g['rotulos']['tabua']}", 6)
    v.chamada((G.xs[1] + 0.5, G.y_t0 + 5.5 * t["larg"] + 2), (G.xs[1] + 10, G.y_topo + 16),
              f"{len(G.xs)} vertical weavers {g['rotulos']['sarrafo']}", 6)
    v.chamada((G.oc / 2, G.y_topo - 0.5), (G.oc / 2 + 28, G.y_topo + 22), f"top cap {g['rotulos']['capa']}", 6)
    v.chamada((G.oc - P / 2 + 1, G.y_poste * 0.6), (G.oc + 8, G.y_topo + 16), f"post {g['rotulos']['poste']}", 6)
    v.marca_corte((G.oc * 0.62, G.y_topo + 6), (G.oc * 0.62, -6), "A")
    v.marca_corte((-P, G.y_t0 + 2.5 * t["larg"]), (G.oc + P, G.y_t0 + 2.5 * t["larg"]), "B")
    return v


def vista_corte_A(G, esc=12):
    """Corte vertical entre sarrafos: fiadas alternam frente/trás."""
    g = G.g
    t, tr, cp = g["tabua"], g["travessa"], g["capa"]
    v = Vista("SECTION A-A (between weavers)", esc)
    P = G.P
    _terreno(v, -6, P + 6, prof=6)
    v.peca(0, 0, P, G.y_poste, "pt", traco="#777")
    v.peca(P / 2 - tr["larg"] / 2, G.y_tr0, tr["larg"], tr["esp"], "pt", x_corte=True)
    v.peca(P / 2 - tr["larg"] / 2, G.y_t1, tr["larg"], tr["esp"], "pt", x_corte=True)
    for i in range(G.fiadas):
        y = G.y_t0 + i * t["larg"]
        # entre sarrafos j e j+1 a tábua cruza o plano; mostramos a posição junto ao sarrafo 1 (j=1)
        z = G.zf if G.frente(i, 1) else G.zb
        v.peca(z[0], y, t["esp"], t["larg"], "madeira", x_corte=True)
    v.peca(G.zs0, G.y_t0, g["sarrafo"]["esp"], G.h_trama, "pt", traco="#777")
    v.peca(-cp["beiral"], G.y_poste, P + 2 * cp["beiral"], cp["esp"], "pt", x_corte=True)
    v.cotas_corrente([0, G.y_tr0, G.y_t0, G.y_t1, G.y_poste, G.y_topo], -3, 0, horizontal=False, tam=5)
    v.cota((G.zf[0], G.y_t0 + 3 * t["larg"]), (G.zb[1], G.y_t0 + 3 * t["larg"]), 0, texto=f"{pes_pol(G.zb[1] - G.zf[0])} weave", tam=5)
    v.cota((0, -2), (P, -2), -2, tam=5)
    v.chamada((G.zb[1], G.y_t0 + 7.5 * t["larg"]), (P + 4, G.y_t0 + 8 * t["larg"]), "boards alternate\nfront / back each row", 5.5)
    v.chamada((P / 2 + tr["larg"] / 2, G.y_tr0 + 0.7), (P + 4, G.y_tr0 + 6), f"bottom rail {g['rotulos']['travessa']}\n{pes_pol(G.gap)} above grade", 5.5)
    v.chamada((P / 2 + 1, G.y_topo - 0.5), (P + 4, G.y_topo + 3), f"cap {g['rotulos']['capa']}", 5.5)
    v.texto(-1, G.y_topo + 7, "HOUSE", 6, "end", negrito=True)
    v.texto(P + 1, G.y_topo + 7, "NEIGHBOR", 6, "start", negrito=True)
    return v


def _tabua_planta(G, fiada, x0, x1):
    """Polígono da tábua em planta (x, z) passando frente/trás dos sarrafos."""
    t, sl = G.g["tabua"]["esp"], G.g["sarrafo"]["larg"]
    xs = [x for x in G.xs if x < x1]
    pts_f, cur = [], None
    nodes = [(x0, None)] + [(x, j) for j, x in enumerate(xs)] + [(x1, None)]
    path = []
    for k, (x, j) in enumerate(nodes):
        if j is None:
            # ponta: mesma posição da tábua no sarrafo mais próximo
            jj = 0 if k == 0 else len(xs) - 1
            z = G.zf[0] if G.frente(fiada, jj) else G.zb[0]
            path.append((x, z))
        else:
            z = G.zf[0] if G.frente(fiada, j) else G.zb[0]
            path.append((x - sl / 2, z))
            path.append((x + sl / 2, z))
    baixo = path
    cima = [(x, z + t) for x, z in path]
    return baixo + list(reversed(cima))


def vista_planta_B(G, esc=10):
    g = G.g
    v = Vista("SECTION B-B (plan through one board row, half module)", esc)
    P, bt = G.P, g["batente"]
    xc = 0
    v.peca(xc - P / 2, 0, P, P, "pt", x_corte=True)
    for z0 in (G.canal[0] - bt["esp"], G.canal[1]):
        v.peca(xc + P / 2, z0, bt["larg"], bt["esp"], "pt", x_corte=True)
    x0, x1 = P / 2 - 0.625, G.xs[1] + 3
    v.linha([(x1, -1), (x1, P + 1)], espessura=0.6)
    v.poligono(_tabua_planta(G, 0, x0, x1), "madeira")
    v.poligono(_tabua_planta(G, 1, x0, x1), "vazio", tracejado=True)
    for xs in G.xs[:2]:
        v.peca(xs - g["sarrafo"]["larg"] / 2, G.zs0, g["sarrafo"]["larg"], g["sarrafo"]["esp"], "pt", x_corte=True)
    v.cotas_corrente([0] + G.xs[:2], P + 3, 0, tam=5)
    v.texto(x1 + 1, P / 2, "(symmetric)", 5.5, "start")
    v.chamada((G.xs[0] + 10, G.zf[0] + 0.5), (G.xs[0] + 16, -5), "board (this row)", 5.5)
    v.chamada((G.xs[0] + 6, G.zb[1] - 0.6), (G.xs[0] + 14, P + 7), "row above (dashed): opposite weave", 5.5)
    v.chamada((P / 2 + 0.7, G.canal[0] - 0.4), (P / 2 + 4, -5), f"channel: 1x2 stops on post, {pes_pol(G.canal[1] - G.canal[0])} wide", 5.5)
    v.texto(-P, -1.2, "HOUSE", 6, "start", negrito=True)
    v.texto(-P, P + 0.5, "NEIGHBOR", 6, "start", negrito=True)
    return v


def vista_implantacao(G, esc=96):
    g = G.g
    v = Vista("SITE LAYOUT — 40' + 60' + 40'", esc)
    L = [x * 12 for x in g["trechos_ft"]]
    # U: lado esquerdo sobe (x=0), fundo (y=L1), lado direito desce
    pts = [(0, 0), (0, L[0]), (L[1], L[0]), (L[1], 0)]
    v.linha(pts, espessura=2.0, traco="#8a5a2b")
    k = 1
    marcas = []
    for (a, b), m in zip(zip(pts, pts[1:]), G.modulos):
        for i in range(m + (1 if k == 1 else 0)):
            f = i / m if k == 1 else (i + 1) / m
            x = a[0] + (b[0] - a[0]) * f
            y = a[1] + (b[1] - a[1]) * f
            marcas.append((x, y))
        k += 1
    for i, (x, y) in enumerate(marcas, 1):
        v.peca(x - 6, y - 6, 12, 12, "pt")
    v.cota((0, L[0]), (L[1], L[0]), 30, texto=f"{g['trechos_ft'][1]}'-0\" ({G.modulos[1]} modules)", tam=6)
    v.cota((0, 0), (0, L[0]), -30, texto=f"{g['trechos_ft'][0]}'-0\" ({G.modulos[0]} modules)", tam=6)
    v.cota((L[1], 0), (L[1], L[2]), 30, texto=f"{g['trechos_ft'][2]}'-0\" ({G.modulos[2]} modules)", tam=6)
    v.texto(L[1] / 2, -40, "HOUSE / OPEN SIDE", 6.5, negrito=True)
    v.texto(L[1] / 2, L[0] / 2, f"{G.n_mod} modules @ {pes_pol(G.oc)} o.c. · {G.n_postes} posts", 7, negrito=True)
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--saida", default=None)
    ap.add_argument("--png", action="store_true")
    ap.add_argument("--previa", action="store_true")
    a = ap.parse_args()
    spec = json.load(open(a.spec, encoding="utf-8"))
    cad.set_idioma(spec.get("idioma_desenho", "en"))
    g = mescla(PADRAO, spec.get("geometria", {}))
    G = Geo(g)
    base = os.path.join(a.saida or os.path.join(os.path.dirname(os.path.abspath(a.spec)), "..", "desenhos"), "cerca-trancada-modulo")
    meta = dict(cliente=spec.get("cliente", ""), autor="", data=spec.get("data", ""), revisao=str(spec.get("revisao", "0")))
    proj = spec.get("projeto_en") or spec.get("projeto", "Woven fence")
    notas = [
        f"Module {pes_pol(G.oc)} o.c. (3.05 m): runs 40'/60'/40' = {G.modulos[0]}+{G.modulos[1]}+{G.modulos[2]} identical modules, {G.n_postes} posts.",
        f"Height {pes_pol(G.y_topo)}: module/height = {G.razao:.3f} (golden ratio φ = 1.618).",
        f"{pes_pol(G.gap)} clearance between bottom rail and grade.",
        f"Posts embedded {pes_pol(g['poste']['embutimento_in'])} in concrete over {pes_pol(g['poste']['brita_in'])} gravel (Ø{pes_pol(g['poste']['furo_diam_in'])} holes).",
        f"{G.fiadas} boards per module, woven over {len(G.xs)} vertical weavers ({pes_pol(G.xs[1] - G.xs[0])} spacing).",
        "PRELIMINARY — module study for client review; not for construction.",
    ]
    p1 = Prancha(proj, "Module study", "M-1", notas=notas, **meta)
    p1.add(vista_modulo(G), 0.9, 4.0)
    p1.add(vista_corte_A(G), 9.9, 2.2)
    p1.add(vista_planta_B(G), 0.9, 0.9)
    p2 = Prancha(proj, "Site layout", "M-2", **meta)
    p2.add(vista_implantacao(G), 3.0, 2.5)
    res = exportar([p1, p2], base, png=a.png or a.previa, pdf=not a.previa, dxf=not a.previa)
    print(f"módulo {G.oc} | vão {G.vao} | fiadas {G.fiadas} | trama {G.h_trama} | topo {G.y_topo} (alvo {G.alvo:.2f}) | razão {G.razao:.3f} | "
          f"sarrafos {[round(x, 2) for x in G.xs]} | tábua {G.comp_tabua} | poste {G.comp_poste} | módulos {G.modulos} | postes {G.n_postes}")
    for k, vv in res.items():
        if vv:
            print(k, vv)


if __name__ == "__main__":
    main()
