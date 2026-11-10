#!/usr/bin/env python3
"""Pranchas de um privacy screen / cerca de ripas horizontais com topo pergolado.

Uso:  python3 privacy_screen.py spec.json --saida pasta/desenhos [--png]

Lê o bloco "geometria" do spec (o mesmo spec.json da skill orcamento-madeira).
Convenções do modelo (polegadas): x ao longo da cerca (0 = face externa do 1º poste),
y vertical (0 = terreno acabado), z na espessura (0 = face do LADO DA CASA,
positivo em direção ao vizinho).

Tipos de poste ("poste.tipo"):
  "composto": núcleo PT (ex.: 4x4) enterrado + revestimento acima do chão: tábuas nas
              2 faces (casa/vizinho) e, nas laterais voltadas para o vão, uma tábua
              SERRILHADA com encaixes onde entram as pontas das ripas (dá o espaçamento
              e trava as ripas). Laterais externas dos postes de ponta: tábua lisa.
  "macico":   poste maciço (ex.: 6x6) e ripas presas entre sarrafos nas 2 faces.
Perfil do caibro ("caibro.perfil"): "nuvem" (vários recortes) | "concavo".
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from cad import Vista, Prancha, exportar, pes_pol  # noqa: E402

PADRAO = {
    "comprimento_total_in": 265, "n_postes": 11,
    "poste": {"tipo": "composto", "nucleo": 3.5, "revest": 1.5, "face_larg": 5.5, "macico": 5.5},
    "embutimento_in": 36, "brita_in": 6, "sapata_diam_in": 12,
    "colar_concreto": {"altura": 2.0, "largura": 8.0},
    "altura_topo_in": 96,
    "y_primeira_ripa": 4.0,
    "ripa": {"larg": 3.5, "esp": 1.5, "espaco_min": 1.5, "folga_ponta": 0.125, "folga_encaixe": 0.0625},
    "cleat": {"esp": 1.5, "larg": 1.5},
    "viga": {"esp": 1.5, "alt": 7.25, "balanco": 6.0},
    "caibro": {"esp": 1.5, "alt": 5.5, "comprimento": 36, "posicao": "postes", "qtd": 11, "perfil": "nuvem"},
    "paisagismo": {"canteiro_in": 24, "pedra_in": 14, "lado": "vizinho", "trepadeiras": True},
    "materiais": {"nucleo": "pt", "revest": "cedro", "serrilhado": "cedro", "cleat": "cedro",
                  "ripa": "cedro", "viga": "cedro", "caibro": "cedro"},
    "rotulos": {"nucleo": "PT 4x4 ground contact (UC4B)", "revest": "Cedro 2x6", "serrilhado": "Cedro 2x6 serrilhado",
                "cleat": "Cedro 2x2", "ripa": "Cedro 2x4 (deitado)", "viga": "Cedro 2x8", "caibro": "Cedro 2x6"},
}


def mescla(a, b):
    out = dict(a)
    for k, v in (b or {}).items():
        out[k] = mescla(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


class Geo:
    def __init__(self, g):
        self.g = g
        po, r, c, v = g["poste"], g["ripa"], g["caibro"], g["viga"]
        self.composto = po["tipo"] == "composto"
        if self.composto:
            self.nuc, self.rev = po["nucleo"], po["revest"]
            self.P = self.nuc + 2 * self.rev
        else:
            self.nuc, self.rev = po["macico"], 0.0
            self.P = po["macico"]
        P, n, L = self.P, g["n_postes"], g["comprimento_total_in"]
        self.n, self.L = n, L
        self.vao = (L - n * P) / (n - 1)
        self.xp = [i * (self.vao + P) for i in range(n)]
        self.y_topo = g["altura_topo_in"]
        self.y_poste = self.y_topo - c["alt"]
        self.y_viga0 = self.y_poste - v["alt"]
        self.y_rev0 = g["colar_concreto"]["altura"] + 0.5
        self.y_r0 = g["y_primeira_ripa"]
        self.y_r1 = self.y_viga0 + 1.0
        H = self.y_r1 - self.y_r0
        e = r["espaco_min"]
        self.fiadas = int(math.floor((H + e) / (r["larg"] + e) + 1e-9))
        self.espaco = (H - self.fiadas * r["larg"]) / (self.fiadas - 1)
        self.passo = r["larg"] + self.espaco
        self.ripas_y = [self.y_r0 + i * self.passo for i in range(self.fiadas)]
        if self.composto:
            self.z_r0 = self.rev
            self.comp_ripa = self.vao + 2 * (self.rev - r["folga_ponta"])
        else:
            self.z_r0 = (P - r["esp"]) / 2
            self.comp_ripa = self.vao
        self.z_r1 = self.z_r0 + r["esp"]
        self.y_base = -g["embutimento_in"]
        self.x_viga0 = -v["balanco"]; self.x_viga1 = L + v["balanco"]
        if c["posicao"] == "postes":
            self.xc = [x + P / 2 - c["esp"] / 2 for x in self.xp]
        else:
            nc = c["qtd"]
            passo = (self.x_viga1 - self.x_viga0 - 4.0 - c["esp"]) / (nc - 1)
            self.xc = [self.x_viga0 + 2.0 + i * passo for i in range(nc)]
        self.passo_caibro = self.xc[1] - self.xc[0]
        self.zc0 = P / 2 - c["comprimento"] / 2
        self.zc1 = self.zc0 + c["comprimento"]
        self.i_emenda = (n - 1) // 2
        self.comp_nucleo = self.y_poste - self.y_base
        self.comp_rev = self.y_poste - self.y_rev0

    def bay_centro(self, i):
        return self.xp[i] + self.P + self.vao / 2


def _ponta(alt, perfil):
    if perfil == "nuvem":
        topo, Lp, lobos, prof, n = 2.0, 9.0, 3, 0.85, 30
        pts = [(0, alt - topo)]
        for i in range(1, n + 1):
            z = Lp * i / n
            base = (alt - topo) * (1 - z / Lp)
            k = int(min(z / (Lp / lobos), lobos - 1))
            zl = z - k * Lp / lobos
            pts.append((z, max(base + prof * math.sin(math.pi * zl / (Lp / lobos)), 0)))
        return pts
    rec, ext, n = 1.75, 5.0, 10
    pts = [(0, alt - rec)]
    for i in range(1, n + 1):
        a = i / n * math.pi / 2
        pts.append((ext * (1 - math.cos(a)), (alt - rec) * (1 - math.sin(a))))
    return pts


def perfil_caibro(z0, comp, y0, alt, perfil="nuvem"):
    ponta = _ponta(alt, perfil)
    pts = [(z0, y0 + alt), (z0 + comp, y0 + alt)]
    pts += [(z0 + comp - dz, y0 + y) for dz, y in ponta]
    pts += [(z0 + dz, y0 + y) for dz, y in reversed(ponta)]
    return pts


def _terreno(v, x0, x1, prof=10):
    v.poligono([(x0, -prof), (x1, -prof), (x1, 0), (x0, 0)], "solo")
    v.linha([(x0, 0), (x1, 0)], espessura=1.2)


def _colar(v, cx, col):
    w = col["largura"] / 2
    v.poligono([(cx - w, 0), (cx + w, 0), (cx + w - 1, col["altura"]), (cx - w + 1, col["altura"])], "concreto")


def _poste_planta(v, G, x, M):
    g, P, rev, nuc = G.g, G.P, G.rev, G.nuc
    if not G.composto:
        v.peca(x, 0, P, P, M["nucleo"], x_corte=True)
        return
    fl = g["poste"]["face_larg"]
    m = (P - fl) / 2
    v.peca(x + rev, rev, nuc, nuc, M["nucleo"], x_corte=True)
    v.peca(x + m, 0, fl, rev, M["revest"], x_corte=True)
    v.peca(x + m, rev + nuc, fl, rev, M["revest"], x_corte=True)
    for i_lado, xs in enumerate((x, x + rev + nuc)):
        externo = (x == G.xp[0] and i_lado == 0) or (x == G.xp[-1] and i_lado == 1)
        if externo:
            v.peca(xs, rev, rev, nuc, M["revest"], x_corte=True)
        else:
            v.peca(xs, G.z_r1, rev, rev + nuc - G.z_r1, M["serrilhado"], x_corte=True)


# ------------------------------------------------------------------ vistas
def vista_elevacao(G, esc=32):
    g, M, P = G.g, G.g["materiais"], G.P
    v = Vista("ELEVAÇÃO — LADO DO VIZINHO", esc)
    _terreno(v, G.x_viga0 - 8, G.x_viga1 + 8)
    d, col = g["sapata_diam_in"], g["colar_concreto"]
    for x in G.xp:
        cx = x + P / 2
        v.poligono([(cx - d / 2, G.y_base), (cx + d / 2, G.y_base), (cx + d / 2, 0), (cx - d / 2, 0)], "concreto", tracejado=True)
        v.poligono([(cx - d / 2, G.y_base - g["brita_in"]), (cx + d / 2, G.y_base - g["brita_in"]),
                    (cx + d / 2, G.y_base), (cx - d / 2, G.y_base)], "brita", tracejado=True)
        v.peca(x + G.rev, G.y_base, G.nuc, G.y_rev0 - G.y_base, M["nucleo"], tracejado=True)
    for i in range(G.n - 1):
        for yr in G.ripas_y:
            v.peca(G.xp[i] + P, yr, G.vao, g["ripa"]["larg"], M["ripa"])
    for x in G.xp:
        if G.composto:
            fl = g["poste"]["face_larg"]; m = (P - fl) / 2
            v.peca(x, G.y_rev0, P, G.comp_rev, M["serrilhado"])
            v.peca(x + m, G.y_rev0, fl, G.comp_rev, M["revest"])
        else:
            v.peca(x, 0, P, G.y_poste, M["nucleo"])
        _colar(v, x + P / 2, col)
    vg, cb = g["viga"], g["caibro"]
    v.poligono([(G.x_viga0, G.y_poste), (G.x_viga1, G.y_poste), (G.x_viga1, G.y_viga0 + 3.0),
                (G.x_viga1 - 3, G.y_viga0), (G.x_viga0 + 3, G.y_viga0), (G.x_viga0, G.y_viga0 + 3.0)], M["viga"])
    xe = G.xp[G.i_emenda] + P / 2
    v.linha([(xe, G.y_viga0), (xe, G.y_poste)], espessura=0.8)
    for xc in G.xc:
        v.peca(xc, G.y_poste, cb["esp"], cb["alt"], M["caibro"])
    for i, x in enumerate(G.xp, 1):
        v.eixo((x + P / 2, G.y_base - g["brita_in"] - 4), (x + P / 2, G.y_topo + 12), str(i))
    yb = G.y_base - 10
    v.cota((0, yb), (G.L, yb), -9, tam=7)
    v.cotas_corrente([x + P / 2 for x in G.xp], yb, 0, tam=5)
    v.cota((G.x_viga0, G.y_topo), (G.x_viga1, G.y_topo), 24, tam=6.5)
    xr = G.x_viga1 + 10
    v.cotas_corrente([G.y_base - g["brita_in"], G.y_base, 0, G.y_r0, G.y_viga0, G.y_topo], xr, 0, horizontal=False, tam=5.5)
    v.cota((xr, 0), (xr, G.y_topo), 18, tam=6.5)
    v.texto(G.x_viga0 - 6, 1.5, "TERRENO", 5.5, "end")
    v.chamada((G.xc[1] + 0.75, G.y_topo - 1), (G.xc[1] + 3, G.y_topo + 40),
              f"{len(G.xc)} caibros {g['rotulos']['caibro']} (1 por poste), ponta recortada", 6)
    v.chamada((G.bay_centro(2), G.ripas_y[-4] + 1.7), (G.bay_centro(2) + 2, G.y_topo + 30),
              f"{G.fiadas} ripas {g['rotulos']['ripa']} por vão, espaço {pes_pol(G.espaco)}", 6)
    v.chamada((xe, G.y_viga0 + 3), (xe + 30, G.y_topo + 20), "emenda da viga sobre o poste", 6)
    if G.composto:
        xq = G.xp[-3]
        v.chamada((xq + P / 2, 50), (xq + 30, -24), "poste composto (det. 2 e 3)", 5.5)
    v.marca_corte((G.bay_centro(0), G.y_topo + 8), (G.bay_centro(0), G.y_base - 2), "A")
    v.marca_corte((G.x_viga0 - 4, 40), (G.xp[1] + P + 6, 40), "B")
    return v


def vista_planta(G, esc=32):
    g, M, P = G.g, G.g["materiais"], G.P
    pa = g.get("paisagismo") or {}
    v = Vista("PLANTA — VISTA SUPERIOR", esc)
    if pa:
        viz = pa.get("lado") == "vizinho"
        zc = (P, P + pa["canteiro_in"]) if viz else (-pa["canteiro_in"], 0)
        zp = (zc[1], zc[1] + pa["pedra_in"]) if viz else (zc[0] - pa["pedra_in"], zc[0])
        v.poligono([(G.x_viga0, zc[0]), (G.x_viga1, zc[0]), (G.x_viga1, zc[1]), (G.x_viga0, zc[1])], "solo")
        v.poligono([(G.x_viga0, zp[0]), (G.x_viga1, zp[0]), (G.x_viga1, zp[1]), (G.x_viga0, zp[1])], "brita")
        if pa.get("trepadeiras"):
            for i in range(G.n - 1):
                v.circulo(G.bay_centro(i), zc[0] + 6, 3, "vazio")
    d = g["sapata_diam_in"]
    for x in G.xp:
        v.circulo(x + P / 2, P / 2, d / 2, "vazio", tracejado=True)
    for i in range(G.n - 1):
        v.peca(G.xp[i] + P, G.z_r0, G.vao, G.z_r1 - G.z_r0, M["ripa"])
    for x in G.xp:
        _poste_planta(v, G, x, M)
    vg, cb = g["viga"], g["caibro"]
    v.peca(G.x_viga0, -vg["esp"], G.x_viga1 - G.x_viga0, vg["esp"], M["viga"])
    v.peca(G.x_viga0, P, G.x_viga1 - G.x_viga0, vg["esp"], M["viga"])
    for xc in G.xc:
        v.peca(xc, G.zc0, cb["esp"], cb["comprimento"], M["caibro"])
    v.texto(G.L / 2, G.zc0 - 9, "LADO DA CASA (cozinha)", 6.5, negrito=True)
    v.texto(G.L / 2, max(G.zc1, P + (pa.get("canteiro_in", 0) + pa.get("pedra_in", 0) if pa else 0)) + 4,
            "LADO DO VIZINHO", 6.5, negrito=True)
    v.cota((G.x_viga0, G.zc0), (G.x_viga0, G.zc1), -8, tam=5.5)
    v.cota((G.xp[0] + P / 2, G.zc0 - 2), (G.xp[1] + P / 2, G.zc0 - 2), -4, texto=f"{pes_pol(G.vao + P)} entre eixos", tam=5.5)
    if pa:
        v.chamada((G.bay_centro(G.n - 2), zc[0] + 6), (G.x_viga1 + 6, zc[0] + 4), "canteiro c/ trepadeira\n(1 por vão)", 5.5)
        v.chamada((G.x_viga1 - 4, (zp[0] + zp[1]) / 2), (G.x_viga1 + 6, zp[1] + 4), "borda de pedra de rio", 5.5)
    v.chamada((G.xp[2] + P / 2 + d / 2 * 0.7, P / 2 - d / 2 * 0.7), (G.xp[2] + 20, G.zc0 - 4), f"sapata Ø{pes_pol(d)}", 5.5)
    return v


def vista_lateral(G, esc=24):
    g, M, P = G.g, G.g["materiais"], G.P
    vg, cb = g["viga"], g["caibro"]
    v = Vista("ELEVAÇÃO LATERAL (extremidade)", esc)
    _terreno(v, G.zc0 - 4, G.zc1 + 4, prof=6)
    if G.composto:
        v.peca(0, G.y_rev0, G.rev, G.comp_rev, M["revest"])
        v.peca(G.rev, G.y_rev0, G.nuc, G.comp_rev, M["revest"])
        v.peca(G.rev + G.nuc, G.y_rev0, G.rev, G.comp_rev, M["revest"])
    else:
        v.peca(0, 0, P, G.y_poste, M["nucleo"])
    _colar(v, P / 2, g["colar_concreto"])
    v.peca(-vg["esp"], G.y_viga0, vg["esp"], vg["alt"], M["viga"])
    v.peca(P, G.y_viga0, vg["esp"], vg["alt"], M["viga"])
    v.poligono(perfil_caibro(G.zc0, cb["comprimento"], G.y_poste, cb["alt"], cb["perfil"]), M["caibro"])
    v.cota((G.zc0, G.y_topo), (G.zc1, G.y_topo), 6, tam=5.5)
    v.cota((G.zc1 + 2, 0), (G.zc1 + 2, G.y_topo), 4, tam=5.5)
    v.texto(G.zc0, -10, "CASA", 6, "start", negrito=True)
    v.texto(G.zc1, -10, "VIZINHO", 6, "end", negrito=True)
    return v


def vista_corte_A(G, esc=16):
    g, M, P = G.g, G.g["materiais"], G.P
    r, vg, cb = g["ripa"], g["viga"], g["caibro"]
    v = Vista("CORTE A-A (meio do vão, olhando o poste 1)", esc)
    zmin, zmax = G.zc0 - 3, G.zc1 + 3
    _terreno(v, zmin, zmax)
    if G.composto:
        v.peca(0, G.y_rev0, G.rev, G.comp_rev, M["revest"], traco="#555")
        v.peca(G.rev + G.nuc, G.y_rev0, G.rev, G.comp_rev, M["revest"], traco="#555")
        v.peca(G.rev, G.y_rev0, G.nuc, G.comp_rev, M["serrilhado"], traco="#555")
    else:
        v.peca(0, 0, P, G.y_poste, M["nucleo"], traco="#666")
    _colar(v, P / 2, g["colar_concreto"])
    for yr in G.ripas_y:
        v.peca(G.z_r0, yr, r["esp"], r["larg"], M["ripa"], x_corte=True)
    v.peca(-vg["esp"], G.y_viga0, vg["esp"], vg["alt"], M["viga"], x_corte=True)
    v.peca(P, G.y_viga0, vg["esp"], vg["alt"], M["viga"], x_corte=True)
    v.poligono(perfil_caibro(G.zc0, cb["comprimento"], G.y_poste, cb["alt"], cb["perfil"]), M["caibro"])
    yb = G.y_viga0 + vg["alt"] / 2
    v.linha([(-vg["esp"] - 0.8, yb), (P + vg["esp"] + 0.8, yb)], espessura=1.2, traco="#333")
    zl = zmin - 2
    v.cotas_corrente([0, G.y_r0, G.y_viga0, G.y_topo], zl, 0, horizontal=False, tam=5.5)
    v.cota((zl, 0), (zl, G.y_topo), -9, tam=6)
    v.cota((G.z_r0, G.ripas_y[3]), (G.z_r0, G.ripas_y[3] + r["larg"]), -4, tam=5)
    v.cota((G.z_r0, G.ripas_y[3] + r["larg"]), (G.z_r0, G.ripas_y[4]), -8, tam=5)
    v.cota((-vg["esp"], G.y_topo + 2), (P + vg["esp"], G.y_topo + 2), 4, tam=5.5)
    v.cota((G.zc0, G.y_topo + 2), (G.zc1, G.y_topo + 2), 10, tam=5.5)
    v.cota((0, -2), (P, -2), -4, tam=5.5)
    zt = zmax + 2

    def ch(p, y, s):
        v.chamada(p, (zt, y), s, 5.5)
    ch((G.zc1 - 3, G.y_topo - 0.5), G.y_topo + 6, f"caibro {g['rotulos']['caibro']}\nponta recortada (det. 4)")
    ch((P + vg["esp"], G.y_viga0 + 5), G.y_viga0 + 1, f"viga dupla {g['rotulos']['viga']}\nparafuso passante 1/2\"")
    if G.composto:
        ch((G.rev + G.nuc - 0.3, G.ripas_y[11] + r["larg"] + G.espaco / 2), G.ripas_y[11] + 2,
           f"dente do serrilhado\n(além do corte, det. 3)")
        ch((P - 0.3, G.ripas_y[7]), G.ripas_y[7], f"face {g['rotulos']['revest']}")
    ch((G.z_r1, G.ripas_y[2] + 2), G.ripas_y[2] - 2, f"ripa {g['rotulos']['ripa']}\nencaixada no serrilhado")
    v.texto(-vg["esp"] - 1, G.y_topo + 16, "CASA", 6, "end", negrito=True)
    v.texto(P + vg["esp"] + 1, G.y_topo + 16, "VIZINHO", 6, "start", negrito=True)
    return v


def vista_fundacao(G, esc=12):
    g, M, P = G.g, G.g["materiais"], G.P
    d, E, B, col = g["sapata_diam_in"], g["embutimento_in"], g["brita_in"], g["colar_concreto"]
    v = Vista("DETALHE 1 — FUNDAÇÃO DO POSTE", esc)
    c = P / 2
    a0, a1 = c - G.nuc / 2, c + G.nuc / 2
    z0, z1 = c - d / 2 - 8, c + d / 2 + 8
    v.poligono([(z0, -E - B - 6), (z1, -E - B - 6), (z1, 0), (c + d / 2, 0), (c + d / 2, -E - B),
                (c - d / 2, -E - B), (c - d / 2, 0), (z0, 0)], "solo")
    v.linha([(z0, 0), (z1, 0)], espessura=1.2)
    v.poligono([(c - d / 2, -E - B), (c + d / 2, -E - B), (c + d / 2, -E), (c - d / 2, -E)], "brita")
    w = col["largura"] / 2
    v.poligono([(c - d / 2, -E), (a0, -E), (a0, col["altura"]), (c - w + 1, col["altura"]), (c - w, 0), (c - d / 2, 0)], "concreto")
    v.poligono([(a1, -E), (c + d / 2, -E), (c + d / 2, 0), (c + w, 0), (c + w - 1, col["altura"]), (a1, col["altura"])], "concreto")
    topo = G.y_rev0 + 12
    v.peca(a0, -E, G.nuc, E + topo, M["nucleo"])
    if G.composto:
        v.peca(0, G.y_rev0, G.rev, topo - G.y_rev0, M["revest"])
        v.peca(P - G.rev, G.y_rev0, G.rev, topo - G.y_rev0, M["revest"])
    v.linha([(-1, topo), (P + 1, topo)], espessura=0.6, tracejado=True)
    v.cota((c - d / 2, -E - B - 3), (c + d / 2, -E - B - 3), -3, tam=5.5)
    v.cotas_corrente([-E - B, -E, 0], z0 - 1, 0, horizontal=False, tam=5.5)
    v.cota((a0, topo + 1), (a1, topo + 1), 3, tam=5.5)
    v.cota((z1 - 2, 0), (z1 - 2, G.y_rev0), 2, tam=5)
    v.chamada((a1 - 0.5, -10), (z1 + 4, -6), f"núcleo {g['rotulos']['nucleo']}\nembutido {pes_pol(E)} (mín. 2 ft)", 5.5)
    v.chamada((c + d / 2 - 1.5, -22), (z1 + 4, -22), f"concreto em volta do núcleo\nfuro Ø{pes_pol(d)}", 5.5)
    v.chamada((c + d / 2 - 2, -E - B / 2), (z1 + 4, -E - B / 2 - 2), f"brita {pes_pol(B)} (drenagem)\npé do poste sobre a brita", 5.5)
    v.chamada((c + w - 1.5, col["altura"] * 0.6), (z1 + 4, 4), "colar de concreto aparente\ncom caimento p/ fora", 5.5)
    if G.composto:
        v.chamada((P - G.rev / 2, G.y_rev0 + 6), (z1 + 4, 14),
                  f"revestimento começa {pes_pol(G.y_rev0 - col['altura'])}\nacima do colar (não toca o concreto)", 5.5)
    return v


def vista_poste(G, esc=3):
    g, M, P = G.g, G.g["materiais"], G.P
    r = g["ripa"]
    v = Vista("DETALHE 2 — POSTE COMPOSTO, CORTE B-B", esc)
    ext = 5.0
    v.peca(-ext, G.z_r0, ext + G.rev - r["folga_ponta"], r["esp"], M["ripa"])
    v.peca(G.rev + G.nuc + r["folga_ponta"], G.z_r0, ext + G.rev - r["folga_ponta"], r["esp"], M["ripa"])
    for xs in (0, G.rev + G.nuc):
        v.peca(xs, G.rev, G.rev, G.nuc, "vazio", tracejado=True)
    fl = g["poste"]["face_larg"]; m = (P - fl) / 2
    v.peca(G.rev, G.rev, G.nuc, G.nuc, M["nucleo"], x_corte=True)
    v.peca(m, 0, fl, G.rev, M["revest"], x_corte=True)
    v.peca(m, G.rev + G.nuc, fl, G.rev, M["revest"], x_corte=True)
    for xs in (0, G.rev + G.nuc):
        v.peca(xs, G.z_r1, G.rev, G.rev + G.nuc - G.z_r1, M["serrilhado"], x_corte=True)
    v.cota((0, P), (P, P), 2.2, tam=5.5)
    v.cota((0, P), (G.rev, P), 1.0, tam=5)
    v.cota((G.rev, P), (G.rev + G.nuc, P), 1.0, tam=5)
    v.cota((P + ext, 0), (P + ext, P), 2.4, tam=5.5)
    v.cota((P + ext, G.z_r0), (P + ext, G.z_r1), 1.0, tam=5)
    v.cota((m, 0), (m + fl, 0), -1.0, tam=5)
    v.chamada((G.rev + 1.0, G.rev + 1.0), (-1.5, P + 3.4), f"núcleo {g['rotulos']['nucleo']}", 5.5)
    v.chamada((m + 0.8, G.rev + G.nuc + 0.7), (-3.0, P + 2.2), f"face {g['rotulos']['revest']} (vizinho)", 5.5)
    v.chamada((m + 0.8, 0.5), (-3.0, -2.6), f"face {g['rotulos']['revest']} (casa)", 5.5)
    v.chamada((G.rev + G.nuc + 0.7, G.rev + G.nuc - 0.6), (P + 1.5, P + 3.4), "lateral serrilhada (det. 3)", 5.5)
    v.chamada((P + 3.5, G.z_r0 + 0.7), (P + 2.5, -2.6), f"ripa entra no encaixe\nfolga {pes_pol(r['folga_ponta'])} na ponta", 5.5)
    v.texto(-ext, -0.7, "CASA", 6, "start", negrito=True)
    v.texto(-ext, P - 0.6, "VIZINHO", 6, "start", negrito=True)
    return v


def vista_serrilhado(G, esc=4, n=3):
    g, M = G.g, G.g["materiais"]
    r = g["ripa"]
    v = Vista("DETALHE 3 — SERRILHADO (vista do vão)", esc)
    z0, z1 = G.rev, G.rev + G.nuc
    y0 = G.ripas_y[0] - 2.5
    y1 = G.ripas_y[n - 1] + r["larg"] + G.espaco
    fe = r["folga_encaixe"]
    cont = [(z1, y0), (z1, y1), (z0, y1)]
    for i in reversed(range(n)):
        ya, yb = G.ripas_y[i] - fe / 2, G.ripas_y[i] + r["larg"] + fe / 2
        cont += [(z0, yb), (G.z_r1, yb), (G.z_r1, ya), (z0, ya)]
    cont.append((z0, y0))
    v.poligono(cont, M["serrilhado"])
    v.linha([(z0 - 0.4, y1 + 0.3), (z1 + 0.4, y1 - 0.3)], espessura=0.6)
    for i in range(n):
        v.peca(z0, G.ripas_y[i], r["esp"], r["larg"], "vazio", tracejado=True)
    v.cota((z0, y0), (z1, y0), -1.5, tam=5)
    v.cota((z0, y1), (G.z_r1, y1), 1.4, texto=f"{pes_pol(r['esp'])} prof.", tam=5)
    ya, yb = G.ripas_y[1] - fe / 2, G.ripas_y[1] + r["larg"] + fe / 2
    v.cota((z1, ya), (z1, yb), 1.5, texto=f"{pes_pol(yb - ya)} encaixe", tam=5)
    v.cota((z1, yb), (z1, G.ripas_y[2] - fe / 2), 1.5, texto=f"{pes_pol(G.espaco - fe)} dente", tam=5)
    v.cota((z1, G.ripas_y[0]), (z1, G.ripas_y[1]), 6.5, texto=f"{pes_pol(G.passo)} passo", tam=5)
    v.cota((z0 - 0.5, 0), (z0 - 0.5, G.ripas_y[0]), -1.5, texto=f"{pes_pol(G.ripas_y[0])} do chão", tam=5)
    v.linha([(z0 - 2.5, 0), (z1 + 1, 0)], espessura=1.0)
    v.chamada((z0 + 0.7, G.ripas_y[0] + 1.5), (z0 - 3.0, G.ripas_y[0] + 6), "ponta da ripa\nencaixada", 5)
    return v


def vista_caibro(G, esc=4):
    g, M = G.g, G.g["materiais"]
    cb = g["caibro"]
    v = Vista("DETALHE 4 — PONTA DO CAIBRO", esc)
    comp, alt = 14, cb["alt"]
    ponta = _ponta(alt, cb["perfil"])
    pts = [(0, alt), (comp, alt), (comp, 0)] + [(dz, y) for dz, y in reversed(ponta)]
    v.poligono(pts, M["caibro"])
    v.linha([(comp - 0.4, -0.6), (comp + 0.4, alt + 0.6)], espessura=0.6)
    v.cota((0, alt), (ponta[-1][0], alt), 1.5, tam=5)
    v.cota((-1, 0), (-1, alt), -1.5, tam=5)
    v.cota((-1, ponta[0][1]), (-1, alt), -4.5, tam=5)
    k = len(ponta) // 2
    v.chamada((ponta[k][0], ponta[k][1] + 0.1), (ponta[k][0] + 6, -2.6), "traçar com gabarito, tico-tico, lixar", 5)
    return v


def lista_pecas(G):
    g, nb, R = G.g, G.n - 1, G.g["rotulos"]
    if G.composto:
        linhas = [
            ["N", "Núcleo do poste", R["nucleo"], G.n, pes_pol(G.comp_nucleo), f"embutir {pes_pol(g['embutimento_in'])}"],
            ["F", "Face do poste", R["revest"], 2 * G.n, pes_pol(G.comp_rev), "casa + vizinho"],
            ["S", "Lateral serrilhada", R["serrilhado"], 2 * nb, pes_pol(G.comp_rev), f"{G.fiadas} encaixes; ripar p/ {pes_pol(G.nuc)}"],
            ["L", "Lateral lisa", R["revest"], 2, pes_pol(G.comp_rev), f"postes 1 e {G.n}, lado externo"],
        ]
    else:
        linhas = [["P", "Poste", R["nucleo"], G.n, pes_pol(G.comp_nucleo), f"embutir {pes_pol(g['embutimento_in'])}"],
                  ["S", "Sarrafo", R["cleat"], 4 * nb, pes_pol(G.y_r1 - G.y_r0), "2 faces, junto aos postes"]]
    xe = G.xp[G.i_emenda] + G.P / 2
    linhas += [
        ["R", "Ripa", R["ripa"], G.fiadas * nb, pes_pol(G.comp_ripa), f"{G.fiadas}/vão, espaço {pes_pol(G.espaco)}"],
        ["V", "Viga (2 linhas x 2)", R["viga"], 4, f"{pes_pol(xe - G.x_viga0)} + {pes_pol(G.x_viga1 - xe)}", "emenda sobre poste"],
        ["K", "Caibro decorativo", R["caibro"], len(G.xc), pes_pol(g["caibro"]["comprimento"]), "pontas recortadas"],
    ]
    return ["Marca", "Peça", "Material", "Qtd", "Compr.", "Obs."], linhas


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
    notas = [
        f"Comprimento {pes_pol(G.L)}; {G.n} postes a {pes_pol(G.vao + G.P)} entre eixos; vão livre {pes_pol(G.vao)}.",
        f"Núcleo dos postes embutido {pes_pol(g['embutimento_in'])} em concreto sobre {pes_pol(g['brita_in'])} de brita.",
        "Ligar para NC811 antes de escavar. Conferir divisa, recuo e HOA.",
        "Fixadores: inox no cedro; galvanizado a fogo/inox no PT.",
        f"Ripas: {G.fiadas} por vão, espaço {pes_pol(G.espaco)} dado pelo serrilhado." if G.composto
        else f"Ripas: {G.fiadas} por vão, espaço {pes_pol(G.espaco)}; usar espaçador.",
        "Serrilhados: marcar todos juntos com gabarito; conferir o nível da 1ª fiada." if G.composto else "",
    ]
    p1 = Prancha(proj, "Elevação e planta", "A-1", notas=[n for n in notas if n], **meta)
    p1.add(vista_planta(G), 1.5, 0.95)
    p1.add(vista_elevacao(G), 1.0, 4.4)
    p1.add(vista_lateral(G), 13.4, 5.0)

    p2 = Prancha(proj, "Cortes e detalhes", "A-2", **meta)
    p2.add(vista_corte_A(G), 0.9, 1.1)
    p2.add(vista_fundacao(G), 5.0, 1.1)
    p2.add(vista_caibro(G), 5.9, 8.1)
    cols, linhas = lista_pecas(G)
    p2.tabela(9.95, 4.3, cols, linhas, [0.42, 1.3, 1.7, 0.35, 1.25, 1.6], "LISTA DE PEÇAS", 6)
    pranchas = [p1, p2]

    if G.composto:
        p3 = Prancha(proj, "Poste composto com serrilhado", "A-3", **meta)
        p3.add(vista_poste(G, esc=2), 1.6, 3.45)
        p3.add(vista_serrilhado(G, esc=3), 12.3, 2.5)
        passos = [
            [1, f"Locar os {G.n} eixos a {pes_pol(G.vao + G.P)}; furos Ø{pes_pol(g['sapata_diam_in'])} x {pes_pol(g['embutimento_in'] + g['brita_in'])}; {pes_pol(g['brita_in'])} de brita no fundo."],
            [2, "Prumar e alinhar os núcleos 4x4 com escoras e linha; concretar; colar com caimento. Curar 48 h."],
            [3, f"Cortar todos os núcleos na mesma altura ({pes_pol(G.y_poste)} acima do terreno), com nível laser ou mangueira."],
            [4, f"Fabricar os {2 * (G.n - 1)} serrilhados juntos, com gabarito: {G.fiadas} encaixes de {pes_pol(g['ripa']['larg'] + g['ripa']['folga_encaixe'])} x {pes_pol(g['ripa']['esp'])}, passo {pes_pol(G.passo)}."],
            [5, "Fixar as faces 2x6 do LADO DO VIZINHO nos núcleos (parafuso inox, cola PU)."],
            [6, "Fixar os serrilhados nas laterais dos núcleos, com os encaixes voltados para o lado da casa."],
            [7, "Encaixar as ripas pelo lado da casa, de baixo para cima; 1 parafuso inox por ponta no serrilhado."],
            [8, "Fechar com as faces 2x6 do LADO DA CASA: elas travam as ripas nos encaixes."],
            [9, "Vigas duplas 2x8 com parafuso passante 1/2\" por poste (emenda sobre o poste do meio)."],
            [10, "Caibros com ponta recortada sobre as vigas, 1 por poste; parafuso estrutural."],
        ]
        p3.tabela(1.0, 2.55, ["#", "SEQUÊNCIA DE MONTAGEM"], passos, [0.3, 10.4], None, 6.5)
        pranchas.append(p3)

    res = exportar(pranchas, base, png=a.png)
    print(f"P={G.P} vão livre {G.vao:.2f} | {G.fiadas} fiadas, espaço {G.espaco:.3f}, passo {G.passo:.3f} | ripa {G.comp_ripa:.2f} | "
          f"núcleo {G.comp_nucleo:.1f} | revest {G.comp_rev:.2f} | caibros {len(G.xc)} | vigas "
          f"{G.xp[G.i_emenda] + G.P / 2 - G.x_viga0:.2f} + {G.x_viga1 - G.xp[G.i_emenda] - G.P / 2:.2f}")
    for k, v in res.items():
        if v:
            print(k, v)


if __name__ == "__main__":
    main()
