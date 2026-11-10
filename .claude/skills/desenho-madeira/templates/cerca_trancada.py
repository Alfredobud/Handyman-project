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
    "painel": {"folga_lateral": 0.25, "moldura_esp": 1.5, "moldura_prof": 3.5,   # 2x4 S4S, 3 1/2" na espessura da cerca
               "rasgo_larg": 2.25, "rasgo_prof": 0.75, "folga_ponta": 0.125,
               "bloco": {"alt": 3.0, "larg": 1.5}},                         # bloco de apoio no poste (sob o painel)
    "rotulos": {"poste": "PT pine 6x6 S4S, ground contact", "tabua": "PT pine 1x6 S4S", "sarrafo": "PT pine 1x2 S4S",
                "batente": "PT pine 1x2 S4S", "moldura": "PT pine 2x4 S4S, grooved", "travessa": "PT pine 2x4 S4S", "capa": "PT pine 2x6 S4S"},
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



# ================================================================== PAINEL PRÉ-FABRICADO (moldura fechada)
class Painel:
    """Geometria do painel trançado montado na oficina (coordenadas do PRÓPRIO painel:
    x = 0 na face externa do montante esquerdo, y = 0 na base da travessa inferior)."""

    def __init__(self, G):
        g = G.g
        pn = g["painel"]
        self.G = G
        self.fl = pn["folga_lateral"]
        self.e, self.pr = pn["moldura_esp"], pn["moldura_prof"]
        self.rl, self.rp, self.fp = pn["rasgo_larg"], pn["rasgo_prof"], pn["folga_ponta"]
        self.W = G.vao - 2 * self.fl                       # largura do painel
        self.Hp = G.h_trama + 2 * self.e                   # altura do painel
        self.Win = self.W - 2 * self.e                     # vão interno da moldura
        self.comp_tabua = self.Win + 2 * (self.rp - self.fp)
        self.comp_sarrafo = G.h_trama + 2 * (self.rp - self.fp)
        self.comp_travessa = self.Win                      # travessa entre os montantes
        self.comp_montante = self.Hp
        self.x0_mod = G.P / 2 + self.fl                    # onde o painel começa no módulo
        self.xs = [x - self.x0_mod for x in G.xs]          # sarrafos no sistema do painel
        self.z0 = (G.P - self.pr) / 2                      # moldura centrada no poste
        self.zr = (G.P / 2 - self.rl / 2, G.P / 2 + self.rl / 2)   # rasgo (= canal do trançado)
        tw = g["tabua"]["larg"]
        self.peso_lb = round(G.fiadas * self.comp_tabua / 12 * 1.4 + 2 * (self.Hp + self.Win) / 12 * 1.6 + 3 * 1.0 * 5.5, 0)


def vista_painel(G, PN, esc=16):
    g, t, e = G.g, G.g["tabua"], PN.e
    v = Vista("PANEL MODULE — SHOP-BUILT (front view)", esc)
    # moldura: montantes inteiros, travessas entre eles
    v.peca(0, 0, e, PN.Hp, "pt")
    v.peca(PN.W - e, 0, e, PN.Hp, "pt")
    v.peca(e, 0, PN.Win, e, "pt")
    v.peca(e, PN.Hp - e, PN.Win, e, "pt")
    for i in range(G.fiadas):
        y = e + i * t["larg"]
        v.peca(e, y, PN.Win, t["larg"], "madeira")
        for j, xs in enumerate(PN.xs):
            if G.frente(i, j):
                v.peca(xs - g["sarrafo"]["larg"] / 2, y, g["sarrafo"]["larg"], t["larg"], "pt")
    for x in (e - PN.rp, PN.W - e + PN.rp):                    # fundo do rasgo dos montantes (oculto)
        v.linha([(x, e), (x, PN.Hp - e)], espessura=0.4, tracejado=True)
    for y in (e - PN.rp, PN.Hp - e + PN.rp):
        v.linha([(e, y), (PN.W - e, y)], espessura=0.4, tracejado=True)
    v.cota((0, PN.Hp), (PN.W, PN.Hp), 9, texto=f"{pes_pol(PN.W)} panel (clear bay {pes_pol(G.vao)} - 2 x {pes_pol(PN.fl)})", tam=6)
    v.cotas_corrente([0, e] + PN.xs + [PN.W - e, PN.W], PN.Hp + 3, 0, tam=5)
    v.cota((PN.W + 3, 0), (PN.W + 3, PN.Hp), 6, tam=6)
    v.cotas_corrente([0, e, PN.Hp - e, PN.Hp], PN.W + 3, 0, horizontal=False, tam=5)
    v.chamada((e / 2, PN.Hp * 0.55), (-10, PN.Hp * 0.55 + 6), f"stile {g['rotulos']['moldura']}\nfull height {pes_pol(PN.comp_montante)}", 5.5)
    v.chamada((PN.W * 0.2, e / 2), (PN.W * 0.2 + 4, -7), f"bottom rail {pes_pol(PN.comp_travessa)} (between stiles)", 5.5)
    v.chamada((PN.W * 0.3, PN.Hp - e / 2), (PN.W * 0.3 + 6, PN.Hp + 13), "top rail (closes the 4th corner)", 5.5)
    v.chamada((PN.W * 0.62, e + 2.5 * t["larg"]), (PN.W * 0.62 + 4, -7), f"{G.fiadas} boards {g['rotulos']['tabua']} x {pes_pol(PN.comp_tabua)}", 5.5)
    v.chamada((PN.xs[2], e + 6.5 * t["larg"]), (PN.W - 30, PN.Hp + 13), f"{len(PN.xs)} weavers {g['rotulos']['sarrafo']} x {pes_pol(PN.comp_sarrafo)}", 5.5)
    for (cx, cy) in ((0, 0), (PN.W, 0), (0, PN.Hp), (PN.W, PN.Hp)):
        v.circulo(cx, cy, 2.2, "vazio", tracejado=True)
    v.texto(PN.W / 2, -16, f"approx. weight {PN.peso_lb:.0f} lb (wet PT) — 2-person lift", 5.5)
    return v


def vista_perfil(G, PN, esc=2):
    v = Vista("DETAIL 1 — FRAME PROFILE (all 4 members)", esc)
    e, pr, rl, rp = PN.e, PN.pr, PN.rl, PN.rp
    z0 = (pr - rl) / 2
    cont = [(0, 0), (pr, 0), (pr, e), (z0 + rl, e), (z0 + rl, e - rp), (z0, e - rp), (z0, e), (0, e)]
    v.poligono(cont, "pt")
    v.linha([(0, 0), (z0, e - rp)], espessura=0.3)
    v.linha([(pr, 0), (z0 + rl, e - rp)], espessura=0.3)
    t = G.g["tabua"]["esp"]
    v.peca(z0, e - rp + PN.fp, t, rp + 1.2 - PN.fp, "madeira", tracejado=True)
    v.peca(z0 + rl - t, e - rp + PN.fp, t, rp + 1.2 - PN.fp, "madeira", tracejado=True)
    v.cota((0, -0.2), (pr, -0.2), -0.6, tam=5)
    v.cota((z0, e + 1.4), (z0 + rl, e + 1.4), 0.5, tam=5)
    v.cota((pr + 0.2, 0), (pr + 0.2, e), 0.6, tam=5)
    v.cota((pr + 0.2, e - rp), (pr + 0.2, e), 1.4, tam=5)
    v.chamada((z0 + rl / 2, e - rp + 0.1), (pr + 1.0, -0.9), f"groove {pes_pol(rl)} x {pes_pol(rp)}\n(dado blade, 1 pass setup for all)", 5)
    v.chamada((z0 + 0.3, e + 0.6), (-0.6, e + 2.0), "board ends (dashed)\nfront / back of weave", 5)
    v.texto(pr / 2, -1.6, "2x4 S4S: 3 1/2\" = fence thickness", 5)
    return v


def vista_canto(G, PN, esc=4):
    """Canto inferior esquerdo: montante inteiro + travessa entre montantes."""
    v = Vista("DETAIL 2 — CORNER JOINT (typ. 4 corners)", esc)
    e, rp = PN.e, PN.rp
    L = 12
    v.peca(0, 0, e, L, "pt")
    v.peca(e, 0, L, e, "pt")
    v.linha([(e - rp, e), (e - rp, L)], espessura=0.5, tracejado=True)
    v.linha([(e, e - rp), (e + L, e - rp)], espessura=0.5, tracejado=True)
    t = G.g["tabua"]["larg"]
    v.peca(e - rp + PN.fp, e, 6, t, "madeira", tracejado=True)
    xs = 6.0
    v.peca(xs, e - rp + PN.fp, G.g["sarrafo"]["larg"], 8, "pt", tracejado=True)
    for y in (e * 0.35, e * 0.75):
        v.linha([(-1.2, y), (e + 2.2, y)], espessura=1.2, traco="#444")
    v.cota((0, L + 0.5), (e, L + 0.5), 1, tam=5)
    v.cota((-1.5, 0), (-1.5, e), -1, tam=5)
    v.chamada((e + 1.6, e * 0.55), (e + 5, -2.5), "2 structural screws 3 1/2\" + PU glue\nthrough stile into rail end", 5)
    v.chamada((e - rp / 2, 8), (-3, 10), "stile groove", 5)
    v.chamada((xs + 0.7, 4), (xs + 4, 9), "weaver end in rail groove", 5)
    v.chamada((3, e + 2.5), (8, 12.5), "board end in stile groove", 5)
    return v


def vista_corte_painel(G, PN, esc=12):
    g, t = G.g, G.g["tabua"]
    v = Vista("SECTION — PANEL (between weavers)", esc)
    e, pr = PN.e, PN.pr
    v.peca(0, 0, pr, e, "pt", x_corte=True)
    v.peca(0, PN.Hp - e, pr, e, "pt", x_corte=True)
    zc = pr / 2
    zf = (zc - G.g["sarrafo"]["esp"] / 2 - t["esp"], zc - G.g["sarrafo"]["esp"] / 2)
    zb = (zc + G.g["sarrafo"]["esp"] / 2, zc + G.g["sarrafo"]["esp"] / 2 + t["esp"])
    for i in range(G.fiadas):
        z = zf if G.frente(i, 1) else zb
        v.peca(z[0], e + i * t["larg"], t["esp"], t["larg"], "madeira", x_corte=True)
    v.peca(zc - G.g["sarrafo"]["esp"] / 2, e - PN.rp + PN.fp, G.g["sarrafo"]["esp"], PN.comp_sarrafo, "pt", traco="#777")
    v.cota((0, -1), (pr, -1), -2, tam=5)
    v.cota((-1, 0), (-1, PN.Hp), -3, tam=5.5)
    v.chamada((pr, PN.Hp - e / 2), (pr + 3, PN.Hp + 2), "top rail (grooved, down)", 5)
    v.chamada((pr, e / 2), (pr + 3, -3), "bottom rail (grooved, up)", 5)
    v.chamada((zb[1], e + 5.5 * t["larg"]), (pr + 3, e + 6 * t["larg"]), "rows alternate\nfront / back", 5)
    return v


def vista_poste_planta(G, PN, esc=4):
    """Planta na altura de uma tábua: poste + dois painéis + batentes."""
    g = G.g
    v = Vista("DETAIL 3 — PANELS AT POST (plan)", esc)
    P, e, pr, bt = G.P, PN.e, PN.pr, g["batente"]
    v.peca(-P / 2, 0, P, P, "pt", x_corte=True)
    z0 = PN.z0
    for lado in (-1, 1):
        xf = lado * (P / 2 + PN.fl)                       # face do montante
        x0 = xf if lado > 0 else xf - e
        cont_prof = (z0, z0 + pr)
        v.peca(x0, z0, e, pr, "pt", x_corte=True)
        # rasgo
        xr = x0 + (e - PN.rp if lado > 0 else 0)
        xr = x0 + e - PN.rp if lado > 0 else x0
        v.peca(x0 + (e - PN.rp) if lado > 0 else x0, PN.zr[0], PN.rp, PN.rl, "vazio")
        xt = x0 + e - PN.rp + PN.fp if lado > 0 else x0 + PN.rp - PN.fp - 6
        v.peca(xt, PN.zr[0], 6, g["tabua"]["esp"], "madeira")
        # batentes (vizinho = z alto já instalado; casa = z baixo)
        xb = xf if lado > 0 else xf - bt["larg"]
        xb = (P / 2) if lado > 0 else (-P / 2 - bt["larg"])
        v.peca(xb, z0 + pr, bt["larg"], bt["esp"], "pt", x_corte=True)
        v.peca(xb, z0 - bt["esp"], bt["larg"], bt["esp"], "pt", x_corte=True)
    v.cota((P / 2, -2), (P / 2 + PN.fl, -2), -1.5, texto=f"{pes_pol(PN.fl)} gap", tam=4.5)
    v.cota((P / 2 + 2.5, z0), (P / 2 + 2.5, z0 + pr), 0, tam=5)
    v.cota((-P / 2, P + 1), (P / 2, P + 1), 1.0, tam=5)
    v.chamada((P / 2 + bt["larg"] / 2, z0 + pr + bt["esp"] / 2), (P / 2 + 5, P + 3.2), "stop 1x2, neighbor side\n(installed first)", 5)
    v.chamada((-P / 2 - bt["larg"] / 2, z0 - bt["esp"] / 2), (-P / 2 - 6, -3.2), "stop 1x2, house side\n(installed after panel)", 5)
    v.chamada((P / 2 + 0.7, z0 + pr / 2), (P / 2 + 6, -3.2), "panel stile", 5)
    v.texto(-P / 2 - 9, z0 + pr + 1.8, "NEIGHBOR", 5.5, "start", negrito=True)
    v.texto(-P / 2 - 9, z0 - 2.0, "HOUSE", 5.5, "start", negrito=True)
    return v


def vista_poste_elev(G, PN, esc=16):
    """Elevação junto ao poste: bloco de apoio, painel, capeamento."""
    g = G.g
    v = Vista("DETAIL 4 — PANEL SUPPORT AND CAP (at post)", esc)
    P, cp, bl = G.P, g["capa"], g["painel"]["bloco"]
    _terreno(v, -P / 2 - 14, P / 2 + 14, prof=4)
    v.peca(-P / 2, 0, P, G.y_poste, "pt")
    for lado in (-1, 1):
        x0 = P / 2 + PN.fl if lado > 0 else -P / 2 - PN.fl - 12
        v.peca(x0, G.gap, 12, PN.Hp, "madeira", tracejado=True)
        xb = P / 2 if lado > 0 else -P / 2 - bl["larg"]
        v.peca(xb, G.gap - bl["alt"], bl["larg"], bl["alt"], "pt", x_corte=True)
    v.peca(-P / 2 - 14, G.y_poste, P + 28, cp["esp"], "pt")
    v.cotas_corrente([0, G.gap, G.gap + PN.Hp, G.y_topo], P / 2 + 16, 0, horizontal=False, tam=5)
    v.chamada((P / 2 + bl["larg"] / 2, G.gap - bl["alt"] / 2), (P / 2 + 5, -6), f"support block 2x4\n(sets the {pes_pol(G.gap)} gap, shim to level)", 5)
    v.chamada((0, G.y_topo - 0.5), (6, G.y_topo + 5), "continuous 2x6 cap: screws into posts and top rails", 5)
    v.chamada((-P / 2 - 6, G.gap + PN.Hp / 2), (-P / 2 - 16, G.gap + PN.Hp / 2 + 10), "panel (dashed)", 5)
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
    PN = Painel(G)
    p1 = Prancha(proj, "Panel module (shop-built)", "P-1", notas=[
        f"Panel {pes_pol(PN.W)} x {pes_pol(PN.Hp)}: closed frame (4 corners) of grooved 2x4 S4S, built in the shop.",
        f"Groove {pes_pol(PN.rl)} x {pes_pol(PN.rp)} on all frame members = weave thickness; boards and weavers sit in it.",
        f"{G.fiadas} boards x {pes_pol(PN.comp_tabua)}; {len(PN.xs)} weavers x {pes_pol(PN.comp_sarrafo)}; stiles {pes_pol(PN.comp_montante)}, rails {pes_pol(PN.comp_travessa)}.",
        "Shop: groove members > U-frame > weavers > weave boards > top rail.",
        f"Check diagonals before closing the 4th corner. Approx. {PN.peso_lb:.0f} lb (wet PT).",
        "PRELIMINARY — solution study; quantities and costs to follow.",
    ], **meta)
    p1.add(vista_painel(G, PN), 1.9, 4.5)
    p1.add(vista_corte_painel(G, PN), 10.2, 3.4)
    p1.add(vista_perfil(G, PN), 12.6, 6.4)
    p1.add(vista_canto(G, PN), 1.3, 0.9)
    p2 = Prancha(proj, "Installation between posts", "P-2", **meta)
    p2.add(vista_poste_planta(G, PN), 1.2, 6.2)
    p2.add(vista_poste_elev(G, PN), 9.0, 4.4)
    passos = [
        [1, f"Set {G.n_postes} posts at {pes_pol(G.oc)} o.c. (±1/8\"), embedded {pes_pol(g['poste']['embutimento_in'])}; level all tops."],
        [2, f"Support blocks on both posts of each bay at {pes_pol(G.gap)} above grade (laser), shim to level."],
        [3, "Neighbor-side 1x2 stops on the post faces."],
        [4, f"Set panel on the blocks from the house side, against the stops ({pes_pol(PN.fl)} gap each side)."],
        [5, "House-side 1x2 stops: panel locked between stops (removable for repair)."],
        [6, "Continuous 2x6 cap screwed into posts and panel top rails (splices over posts)."],
    ]
    p2.tabela(1.0, 3.0, ["#", "FIELD INSTALLATION"], passos, [0.3, 9.6], None, 6.5)
    p3 = Prancha(proj, "Site layout", "P-3", notas=notas, **meta)
    p3.add(vista_implantacao(G), 3.0, 2.5)
    res = exportar([p1, p2, p3], base, png=a.png or a.previa, pdf=not a.previa, dxf=not a.previa)
    print(f"painel {PN.W} x {PN.Hp} | vão interno {PN.Win} | tábua {PN.comp_tabua} | sarrafo {PN.comp_sarrafo} | peso ~{PN.peso_lb} lb")
    print(f"módulo {G.oc} | vão {G.vao} | fiadas {G.fiadas} | trama {G.h_trama} | topo {G.y_topo} (alvo {G.alvo:.2f}) | razão {G.razao:.3f} | "
          f"sarrafos {[round(x, 2) for x in G.xs]} | tábua {G.comp_tabua} | poste {G.comp_poste} | módulos {G.modulos} | postes {G.n_postes}")
    for k, vv in res.items():
        if vv:
            print(k, vv)


if __name__ == "__main__":
    main()
