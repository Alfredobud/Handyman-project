#!/usr/bin/env python3
"""Pranchas de um privacy screen / cerca de ripas horizontais com topo pergolado.

Uso:  python3 privacy_screen.py spec.json --saida pasta/desenhos [--png]

Lê o bloco "geometria" do spec (o mesmo spec.json da skill orcamento-madeira).
Convenções do modelo (polegadas): x ao longo da cerca (0 = face externa do 1º poste),
y vertical (0 = terreno acabado), z na espessura (0 = face do poste do LADO DA CASA,
positivo em direção ao vizinho).
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from cad import Vista, Prancha, exportar, pes_pol  # noqa: E402

PADRAO = {
    "comprimento_total_in": 265, "n_postes": 6, "poste_in": 5.5,
    "embutimento_in": 36, "brita_in": 6, "sapata_diam_in": 16, "coroa_concreto_in": 1,
    "altura_topo_in": 96,
    "travessa": {"esp": 1.5, "larg": 5.5, "y_inferior": 2.5},
    "cleat": {"esp": 1.5, "larg": 3.5},
    "montante_central": True,
    "ripa": {"larg": 5.5, "esp": 1.0, "z": 1.0, "espaco_min": 1.5},
    "viga": {"esp": 1.5, "alt": 7.25, "balanco": 11.5},
    "caibro": {"esp": 1.5, "alt": 3.5, "comprimento": 30, "qtd": 14},
    "materiais": {"poste": "pt", "travessa": "pt", "cleat": "pt", "montante": "pt",
                  "ripa": "cedro", "viga": "cedro", "caibro": "cedro"},
    "rotulos": {"poste": "PT 6x6 ground contact (UC4B)", "travessa": "PT 2x6", "cleat": "PT 2x4",
                "montante": "PT 2x4", "ripa": "Cedro 5/4x6", "viga": "Cedro 2x8", "caibro": "Cedro 2x4"},
}


def mescla(a, b):
    out = dict(a)
    for k, v in (b or {}).items():
        out[k] = mescla(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


class Geo:
    """Calcula todas as posições a partir dos parâmetros."""

    def __init__(self, g):
        self.g = g
        P, n, L = g["poste_in"], g["n_postes"], g["comprimento_total_in"]
        self.P, self.n, self.L = P, n, L
        self.vao = (L - n * P) / (n - 1)
        self.xp = [i * (self.vao + P) for i in range(n)]            # face esquerda de cada poste
        c, v, t, r = g["caibro"], g["viga"], g["travessa"], g["ripa"]
        self.y_topo = g["altura_topo_in"]
        self.y_poste = self.y_topo - c["alt"]                        # topo do poste = base dos caibros
        self.y_viga0 = self.y_poste - v["alt"]
        self.y_ti0 = t["y_inferior"]; self.y_ti1 = self.y_ti0 + t["esp"]
        # travessa superior escondida atrás das vigas
        self.y_ts1 = self.y_viga0 + 3.25
        self.y_ts0 = self.y_ts1 - t["esp"]
        self.y_r0, self.y_r1 = self.y_ti1, self.y_ts0                # zona das ripas
        H = self.y_r1 - self.y_r0
        e = r["espaco_min"]
        self.fiadas = int(math.floor((H + e) / (r["larg"] + e) + 1e-9))
        self.espaco = (H - self.fiadas * r["larg"]) / (self.fiadas - 1)
        self.ripas_y = [self.y_r0 + i * (r["larg"] + self.espaco) for i in range(self.fiadas)]
        self.z_cleat0 = r["z"] + r["esp"]
        self.y_base = -g["embutimento_in"]
        self.x_viga0 = -v["balanco"]; self.x_viga1 = L + v["balanco"]
        nc = c["qtd"]
        passo = (self.x_viga1 - self.x_viga0 - 2 * 2.0 - c["esp"]) / (nc - 1)
        self.xc = [self.x_viga0 + 2.0 + i * passo for i in range(nc)]
        self.passo_caibro = passo
        self.zc0 = P / 2 - c["comprimento"] / 2

    def bay_centro(self, i):
        return self.xp[i] + self.P + self.vao / 2


def perfil_caibro(z0, comp, y0, alt, recorte=1.75, extensao=5.0, passos=8):
    """Caibro de perfil com ponta decorativa côncava nas duas extremidades."""
    pts = [(z0, y0 + alt), (z0 + comp, y0 + alt)]
    # ponta direita: desce de (z1, topo-recorte...) curva até a base
    z1 = z0 + comp
    pts.append((z1, y0 + alt - recorte))
    for i in range(1, passos + 1):
        a = i / passos * math.pi / 2
        pts.append((z1 - extensao * (1 - math.cos(a)), y0 + (alt - recorte) * (1 - math.sin(a))))
    pts.append((z0 + extensao, y0))
    for i in range(passos + 1):
        a = (passos - i) / passos * math.pi / 2
        pts.append((z0 + extensao * (1 - math.cos(a)), y0 + (alt - recorte) * (1 - math.sin(a))))
    pts.append((z0, y0 + alt - recorte))
    return pts


# ------------------------------------------------------------------ vistas
def vista_elevacao(G, esc=32):
    g, M, P = G.g, G.g["materiais"], G.P
    v = Vista("ELEVAÇÃO — LADO DA CASA", esc)
    # terreno
    v.poligono([(G.x_viga0 - 6, -10), (G.x_viga1 + 6, -10), (G.x_viga1 + 6, 0), (G.x_viga0 - 6, 0)], "solo")
    v.linha([(G.x_viga0 - 6, 0), (G.x_viga1 + 6, 0)], espessura=1.2)
    # sapatas e postes enterrados (tracejado)
    d = g["sapata_diam_in"]
    for x in G.xp:
        cx = x + P / 2
        v.poligono([(cx - d / 2, G.y_base), (cx + d / 2, G.y_base), (cx + d / 2, -g["coroa_concreto_in"]),
                    (cx - d / 2, -g["coroa_concreto_in"])], "concreto", tracejado=True)
        v.poligono([(cx - d / 2, G.y_base - g["brita_in"]), (cx + d / 2, G.y_base - g["brita_in"]),
                    (cx + d / 2, G.y_base), (cx - d / 2, G.y_base)], "brita", tracejado=True)
        v.peca(x, G.y_base, P, -G.y_base, M["poste"], tracejado=True)
    # travessa inferior (borda visível)
    for i in range(G.n - 1):
        x0 = G.xp[i] + P
        v.peca(x0, G.y_ti0, G.vao, G.y_ti1 - G.y_ti0, M["travessa"])
        for yr in G.ripas_y:
            v.peca(x0, yr, G.vao, g["ripa"]["larg"], M["ripa"])
        if g["montante_central"]:  # oculto atrás das ripas
            xm = G.bay_centro(i) - g["cleat"]["esp"] / 2
            v.peca(xm, G.y_r0, g["cleat"]["esp"], G.y_r1 - G.y_r0, "vazio", tracejado=True)
    for x in G.xp:
        v.peca(x, 0, P, G.y_poste, M["poste"])
    # viga (lado da casa) com pontas decorativas
    vg = g["viga"]
    v.poligono([(G.x_viga0, G.y_poste), (G.x_viga1, G.y_poste), (G.x_viga1, G.y_viga0 + 3.0),
                (G.x_viga1 - 4, G.y_viga0), (G.x_viga0 + 4, G.y_viga0), (G.x_viga0, G.y_viga0 + 3.0)], M["viga"])
    xm_emenda = G.xp[G.n // 2] + P / 2 if G.n % 2 else G.xp[G.n // 2 - 1] + P / 2
    v.linha([(xm_emenda, G.y_viga0), (xm_emenda, G.y_poste)], espessura=0.8)
    # caibros vistos de topo (extremidade)
    cb = g["caibro"]
    for xc in G.xc:
        v.peca(xc, G.y_poste, cb["esp"], cb["alt"], M["caibro"])
    # eixos dos postes
    for i, x in enumerate(G.xp, 1):
        v.eixo((x + P / 2, G.y_base - g["brita_in"] - 4), (x + P / 2, G.y_topo + 14), str(i))
    # cotas horizontais
    v.cota((0, G.y_base - 10), (G.L, G.y_base - 10), -8, tam=7)
    pts = []
    for x in G.xp:
        pts += [x, x + P]
    v.cotas_corrente(pts, G.y_base - 10, 0, tam=5.5)
    v.cota((G.x_viga0, G.y_topo), (G.x_viga1, G.y_topo), 22, tam=6.5)
    v.cota((G.x_viga0, G.y_topo), (0, G.y_topo), 12, tam=5.5)
    # cotas verticais à direita
    xr = G.x_viga1 + 10
    niveis = [G.y_base - g["brita_in"], G.y_base, 0, G.y_r0, G.y_r1, G.y_topo]
    v.cotas_corrente(niveis, xr, 0, horizontal=False, tam=5.5)
    v.cota((xr, 0), (xr, G.y_topo), 18, tam=6.5)
    v.texto(G.x_viga0 - 4, 1.5, "TERRENO ACABADO", 5.5, "end")
    # chamadas
    b0 = G.xp[0] + P
    v.chamada((G.xc[1] + 0.75, G.y_topo - 0.5), (G.xc[1] + 3, G.y_topo + 40),
              f"{cb['qtd']} caibros {G.g['rotulos']['caibro']} @ ~{pes_pol(G.passo_caibro)}", 6)
    v.chamada((G.bay_centro(1) - 8, G.ripas_y[-3] + 2.7), (G.bay_centro(1) - 6, G.y_topo + 30),
              f"{G.fiadas} ripas {G.g['rotulos']['ripa']} por vão, espaço {pes_pol(G.espaco)}", 6)
    v.chamada((xm_emenda, G.y_viga0 + 3), (xm_emenda + 40, G.y_topo + 34), "emenda da viga sobre o poste", 6)
    v.chamada((G.bay_centro(0) + 0.75, G.y_r0 + 20), (G.bay_centro(0) + 4, -18), "montante oculto", 5.5)
    v.marca_corte((G.xp[0] + P + 10, G.y_topo + 8), (G.xp[0] + P + 10, G.y_base - 2), "A")
    return v


def vista_planta(G, esc=32):
    g, M, P = G.g, G.g["materiais"], G.P
    v = Vista("PLANTA — VISTA SUPERIOR", esc)
    d = g["sapata_diam_in"]
    for x in G.xp:
        v.circulo(x + P / 2, P / 2, d / 2, "vazio", tracejado=True)
    for i in range(G.n - 1):
        v.peca(G.xp[i] + P, 0, G.vao, P, M["travessa"])
    for x in G.xp:
        v.peca(x, 0, P, P, M["poste"])
    vg, cb = g["viga"], g["caibro"]
    v.peca(G.x_viga0, -vg["esp"], G.x_viga1 - G.x_viga0, vg["esp"], M["viga"])
    v.peca(G.x_viga0, P, G.x_viga1 - G.x_viga0, vg["esp"], M["viga"])
    for xc in G.xc:
        v.peca(xc, G.zc0, cb["esp"], cb["comprimento"], M["caibro"])
    for i, x in enumerate(G.xp, 1):
        v.eixo((x + P / 2, G.zc0 - 6), (x + P / 2, G.zc0 + cb["comprimento"] + 6), str(i))
    v.texto(G.L / 2, G.zc0 - 9, "LADO DA CASA (cozinha)", 6.5, negrito=True)
    v.texto(G.L / 2, G.zc0 + cb["comprimento"] + 4, "LADO DO VIZINHO", 6.5, negrito=True)
    v.cotas_corrente([x + P / 2 for x in G.xp], G.zc0 + cb["comprimento"], 12, tam=5.5)
    v.cota((G.x_viga1, G.zc0), (G.x_viga1, G.zc0 + cb["comprimento"]), 10, tam=5.5)
    v.chamada((G.xp[1] + P / 2 + d / 2 * 0.7, P / 2 - d / 2 * 0.7), (G.xp[1] + 30, G.zc0 - 4),
              f"sapata Ø{pes_pol(d)}", 5.5)
    return v


def vista_corte_A(G, esc=16):
    g, M, P = G.g, G.g["materiais"], G.P
    r, t, cl, vg, cb = g["ripa"], g["travessa"], g["cleat"], g["viga"], g["caibro"]
    v = Vista("CORTE A-A (no vão, olhando para o poste 1)", esc)
    zmin, zmax = G.zc0 - 4, G.zc0 + cb["comprimento"] + 4
    v.poligono([(zmin, -10), (zmax, -10), (zmax, 0), (zmin, 0)], "solo")
    v.linha([(zmin, 0), (zmax, 0)], espessura=1.2)
    # poste além do corte (vista) e cleat
    v.peca(0, 0, P, G.y_poste, M["poste"], traco="#666")
    v.peca(G.z_cleat0, G.y_r0, cl["larg"], G.y_r1 - G.y_r0, M["cleat"])
    # peças cortadas
    v.peca(0, G.y_ti0, P, t["esp"], M["travessa"], x_corte=True)
    v.peca(0, G.y_ts0, P, t["esp"], M["travessa"], x_corte=True)
    for yr in G.ripas_y:
        v.peca(r["z"], yr, r["esp"], r["larg"], M["ripa"], x_corte=True)
    v.peca(-vg["esp"], G.y_viga0, vg["esp"], vg["alt"], M["viga"], x_corte=True)
    v.peca(P, G.y_viga0, vg["esp"], vg["alt"], M["viga"], x_corte=True)
    v.poligono(perfil_caibro(G.zc0, cb["comprimento"], G.y_poste, cb["alt"]), M["caibro"])
    yb = G.y_viga0 + vg["alt"] / 2
    v.linha([(-vg["esp"] - 0.8, yb), (P + vg["esp"] + 0.8, yb)], espessura=1.2, traco="#333")
    # cotas
    zl = zmin - 2
    v.cotas_corrente([0, G.y_r0, G.y_r1, G.y_topo], zl, 0, horizontal=False, tam=5.5)
    v.cota((zl, 0), (zl, G.y_topo), -9, tam=6)
    v.cota((r["z"], G.ripas_y[2]), (r["z"], G.ripas_y[2] + r["larg"]), -5, tam=5)
    v.cota((r["z"], G.ripas_y[2] + r["larg"]), (r["z"], G.ripas_y[3]), -9, tam=5)
    v.cota((-vg["esp"], G.y_topo + 2), (P + vg["esp"], G.y_topo + 2), 4, tam=5.5)
    v.cota((G.zc0, G.y_topo + 2), (G.zc0 + cb["comprimento"], G.y_topo + 2), 10, tam=5.5)
    v.cota((0, -2), (P, -2), -4, tam=5.5)
    # chamadas
    zt = zmax + 2
    def ch(p, y, s):
        v.chamada(p, (zt, y), s, 5.5)
    ch((G.zc0 + cb["comprimento"] - 2, G.y_topo - 1), G.y_topo + 6, f"caibro {g['rotulos']['caibro']}")
    ch((P + vg["esp"], G.y_viga0 + 5), G.y_viga0 + 6, f"viga dupla {g['rotulos']['viga']}\nparafuso passante 1/2\"")
    ch((P - 0.5, G.y_ts0 + 0.7), G.y_ts0 - 6, f"travessa sup. {g['rotulos']['travessa']} (deitada)")
    ch((G.z_cleat0 + cl["larg"], G.y_r0 + 50), G.y_r0 + 52, f"cleat {g['rotulos']['cleat']}\nparafusado no poste")
    ch((r["z"] + r["esp"], G.ripas_y[5] + 2.5), G.ripas_y[5], f"ripa {g['rotulos']['ripa']}\n2 parafusos inox por apoio")
    ch((P - 0.5, G.y_ti0 + 0.7), G.y_ti0 + 10, f"travessa inf. {g['rotulos']['travessa']}\nfolga do chão {pes_pol(G.y_ti0)}")
    v.texto(-vg["esp"] - 1, G.y_topo + 16, "CASA", 6, "end", negrito=True)
    v.texto(P + vg["esp"] + 1, G.y_topo + 16, "VIZINHO", 6, "start", negrito=True)
    return v


def vista_fundacao(G, esc=12):
    g, M, P = G.g, G.g["materiais"], G.P
    d, E, B, cr = g["sapata_diam_in"], g["embutimento_in"], g["brita_in"], g["coroa_concreto_in"]
    v = Vista("DETALHE 1 — FUNDAÇÃO DO POSTE", esc)
    c = P / 2
    z0, z1 = c - d / 2 - 8, c + d / 2 + 8
    v.poligono([(z0, -E - B - 6), (z1, -E - B - 6), (z1, 0), (c + d / 2, 0), (c + d / 2, -E - B),
                (c - d / 2, -E - B), (c - d / 2, 0), (z0, 0)], "solo")
    v.linha([(z0, 0), (z1, 0)], espessura=1.2)
    v.poligono([(c - d / 2, -E - B), (c + d / 2, -E - B), (c + d / 2, -E), (c - d / 2, -E)], "brita")
    v.poligono([(c - d / 2, -E), (0, -E), (0, cr), (c - d / 2, -cr)], "concreto")
    v.poligono([(P, -E), (c + d / 2, -E), (c + d / 2, -cr), (P, cr)], "concreto")
    v.peca(0, -E, P, E + 14, M["poste"], x_corte=False)
    v.linha([(-1, 14), (P + 1, 14)], espessura=0.6, tracejado=True)
    v.cota((c - d / 2, -E - B - 3), (c + d / 2, -E - B - 3), -3, tam=5.5)
    v.cotas_corrente([-E - B, -E, 0], z0 - 1, 0, horizontal=False, tam=5.5)
    v.cota((0, 8), (P, 8), 3, tam=5.5)
    v.chamada((P + 0.5, -10), (z1 + 3, -6), f"poste {g['rotulos']['poste']}\nembutido {pes_pol(E)} (mín. 2 ft)", 5.5)
    v.chamada((c + d / 2 - 2, -20), (z1 + 3, -22), f"concreto em volta do poste\nfuro Ø{pes_pol(d)}", 5.5)
    v.chamada((c + d / 2 - 2, -E - B / 2), (z1 + 3, -E - B / 2 - 2), f"brita {pes_pol(B)} (drenagem)\npé do poste sobre a brita", 5.5)
    v.chamada((P + 1, cr * 0.4), (z1 + 3, 8), "coroa de concreto\ncom caimento p/ fora", 5.5)
    return v


def vista_corte_B(G, esc=6):
    g, M, P = G.g, G.g["materiais"], G.P
    r, cl = g["ripa"], g["cleat"]
    v = Vista("DETALHE 2 — CORTE HORIZONTAL B-B (pela ripa)", esc)
    x_fim = G.bay_centro(0) + 7
    v.peca(-3, 0, 3 + P, P, M["poste"], x_corte=True)
    v.linha([(-3, -0.8), (-3, P + 0.8)], espessura=0.5, tracejado=True)
    v.peca(P, G.z_cleat0, cl["esp"], cl["larg"], M["cleat"], x_corte=True)
    xm = G.bay_centro(0) - cl["esp"] / 2
    if g["montante_central"]:
        v.peca(xm, G.z_cleat0, cl["esp"], cl["larg"], M["montante"], x_corte=True)
    v.peca(P, r["z"], x_fim - P, r["esp"], M["ripa"])
    for xs in (P + cl["esp"] / 2, xm + cl["esp"] / 2):
        v.linha([(xs, r["z"] - 0.2), (xs, G.z_cleat0 + 2.2)], espessura=1.0, traco="#555")
    v.cota((P, -1), (P + G.vao / 2, -1), -2.5, texto=f"{pes_pol(G.vao / 2)} (vão livre / 2)", tam=5.5)
    v.cota((P, P), (P + cl["esp"], P), 2.5, tam=5)
    v.cota((x_fim + 1, r["z"]), (x_fim + 1, r["z"] + r["esp"]), 2, tam=5)
    v.cota((x_fim + 1, G.z_cleat0), (x_fim + 1, G.z_cleat0 + cl["larg"]), 2, tam=5)
    v.chamada((P + 8, r["z"] + 0.5), (P + 10, -6), f"ripa {g['rotulos']['ripa']}", 5.5)
    v.chamada((P + 0.7, G.z_cleat0 + 2), (P - 1, P + 4.5), f"cleat {g['rotulos']['cleat']}", 5.5)
    if g["montante_central"]:
        v.chamada((xm + 0.7, G.z_cleat0 + 2.5), (xm + 3, P + 4.5), "montante central (apoio a cada ~2 ft)", 5.5)
    v.chamada((xm + cl["esp"] / 2, r["z"] - 0.1), (xm + 4, -6), "parafuso inox", 5.5)
    v.texto(x_fim + 6, -0.5, "CASA", 6, "start", negrito=True)
    v.texto(x_fim + 6, P - 0.5, "VIZINHO", 6, "start", negrito=True)
    return v


def vista_caibro(G, esc=4):
    g, M = G.g, G.g["materiais"]
    cb = g["caibro"]
    v = Vista("DETALHE 3 — PONTA DO CAIBRO / VIGA", esc)
    comp, alt, rec, ext, n = 13, cb["alt"], 1.75, 5.0, 10
    pts = [(0, alt), (comp, alt), (comp, 0), (ext, 0)]
    for i in range(n + 1):
        a = (n - i) / n * math.pi / 2
        pts.append((ext * (1 - math.cos(a)), (alt - rec) * (1 - math.sin(a))))
    pts.append((0, alt - rec))
    v.poligono(pts, M["caibro"])
    v.linha([(comp - 0.4, -0.6), (comp + 0.4, alt + 0.6)], espessura=0.6)  # linha de quebra
    v.cota((0, cb["alt"]), (5, cb["alt"]), 1.5, tam=5)
    v.cota((-1, 0), (-1, cb["alt"]), -1.5, tam=5)
    v.cota((-1, cb["alt"] - 1.75), (-1, cb["alt"]), -4.5, tam=5)
    v.chamada((3, 0.9), (8, -2.5), "curva côncava: traçar com gabarito,\ncortar com tico-tico, lixar", 5.5)
    return v


def lista_pecas(G):
    g, P = G.g, G.g["poste_in"]
    R, nb = g["rotulos"], G.n - 1
    comp_poste = G.y_poste + g["embutimento_in"]
    linhas = [
        ["P", "Poste", R["poste"], G.n, pes_pol(comp_poste), f"embutir {pes_pol(g['embutimento_in'])}"],
        ["TI", "Travessa inferior", R["travessa"], nb, pes_pol(G.vao), "deitada"],
        ["TS", "Travessa superior", R["travessa"], nb, pes_pol(G.vao), "deitada, atrás das vigas"],
        ["C", "Cleat", R["cleat"], 2 * nb, pes_pol(G.y_r1 - G.y_r0), "nas faces dos postes"],
    ]
    if g["montante_central"]:
        linhas.append(["M", "Montante central", R["montante"], nb, pes_pol(G.y_r1 - G.y_r0), "meio do vão"])
    linhas += [
        ["R", "Ripa", R["ripa"], G.fiadas * nb, pes_pol(G.vao), f"{G.fiadas}/vão, espaço {pes_pol(G.espaco)}"],
        ["V", "Viga (2 linhas x 2 peças)", R["viga"], 4, pes_pol((G.x_viga1 - G.x_viga0) / 2), "emenda sobre poste"],
        ["K", "Caibro decorativo", R["caibro"], g["caibro"]["qtd"], pes_pol(g["caibro"]["comprimento"]), "pontas recortadas"],
    ]
    return ["Marca", "Peça", "Material", "Qtd", "Compr.", "Obs."], linhas


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--saida", default=None)
    ap.add_argument("--png", action="store_true")
    a = ap.parse_args()
    spec = json.load(open(a.spec, encoding="utf-8"))
    g = mescla(PADRAO, spec.get("geometria", {}))
    G = Geo(g)
    base_dir = a.saida or os.path.join(os.path.dirname(os.path.abspath(a.spec)), "..", "desenhos")
    base = os.path.join(base_dir, "privacy-screen")
    proj = spec.get("projeto", "Privacy screen")
    meta = dict(cliente=spec.get("cliente", ""), autor=spec.get("autor", ""), data=spec.get("data", ""),
                revisao=str(spec.get("revisao", "0")))

    p1 = Prancha(proj, "Elevação e planta", "A-1", notas=[
        f"Comprimento total {pes_pol(G.L)}; {G.n} postes; vão livre {pes_pol(G.vao)}.",
        f"Postes embutidos {pes_pol(g['embutimento_in'])} em concreto sobre {pes_pol(g['brita_in'])} de brita.",
        "Ligar para NC811 antes de escavar. Conferir divisa, recuo e HOA.",
        "Fixadores: inox no cedro; galvanizado a fogo/inox no PT.",
        f"Ripas: {G.fiadas} por vão, espaço {pes_pol(G.espaco)}; usar espaçador.",
    ], **meta)
    elev = vista_elevacao(G)
    plan = vista_planta(G)
    p1.add(plan, 1.6, 1.25)
    p1.add(elev, 1.0, 3.55)

    p2 = Prancha(proj, "Cortes e detalhes", "A-2", **meta)
    p2.add(vista_corte_A(G), 0.9, 1.1)
    p2.add(vista_fundacao(G), 5.0, 1.1)
    p2.add(vista_caibro(G), 11.4, 5.4)
    p2.add(vista_corte_B(G), 5.0, 7.75)
    cols, linhas = lista_pecas(G)
    p2.tabela(9.95, 4.3, cols, linhas, [0.42, 1.35, 1.75, 0.35, 0.7, 2.05], "LISTA DE PEÇAS", 6)

    res = exportar([p1, p2], base, png=a.png)
    print(f"vão livre {G.vao:.2f} in | {G.fiadas} fiadas, espaço {G.espaco:.3f} in | poste {G.y_poste + g['embutimento_in']:.1f} in | "
          f"caibros @ {G.passo_caibro:.2f} in")
    for k, v in res.items():
        if v:
            print(k, v)


if __name__ == "__main__":
    main()
