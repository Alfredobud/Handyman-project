#!/usr/bin/env python3
"""Pranchas de um privacy screen / cerca de ripas horizontais com topo pergolado.

Uso:  python3 privacy_screen.py spec.json --saida pasta/desenhos [--png | --previa]

Lê o bloco "geometria" do spec (o mesmo spec.json da skill orcamento-madeira).
Os textos das pranchas saem em inglês (cliente nos EUA); o carimbo usa cad.set_idioma("en").
Convenções do modelo (polegadas): x ao longo da cerca (0 = face externa do 1º poste),
y vertical (0 = terreno acabado), z na espessura (0 = face do LADO DA CASA,
positivo em direção ao vizinho).

Poste "composto": núcleo PT (4x4) enterrado + revestimento acima do chão: tábuas 2x6
nas duas faces e, nas laterais voltadas para o vão, tábua SERRILHADA (1") com encaixes
onde entram as pontas das ripas. Lateral externa dos postes de ponta: tábua lisa (1").
Todos os postes com 5 1/2", faces alinhadas. "lado_ripas": "vizinho" | "casa" define
de que lado ficam os encaixes (e por onde as ripas são instaladas).
Topo: tábuas 2x8 dos dois lados dos postes, entalhadas para receber os caibros, com
fechamento nas pontas (aparência de viga maciça). Caibros com ponta tipo nuvem.
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import cad  # noqa: E402
from cad import Vista, Prancha, exportar, pes_pol  # noqa: E402

PADRAO = {
    "comprimento_total_in": 265, "n_postes": 10,
    "poste": {"tipo": "composto", "nucleo": 3.5, "face_esp": 1.5, "face_larg": 5.5,
              "serrilhado_esp": 1.0, "lateral_ponta_esp": 1.0},
    "lado_ripas": "vizinho",
    "embutimento_in": 24, "brita_in": 6, "sapata_diam_in": 12,
    "colar_concreto": {"altura": 2.0, "largura": 8.0},
    "altura_topo_in": 96,
    "y_primeira_ripa": 4.0,
    "ripa": {"larg": 3.5, "esp": 1.5, "espaco_min": 1.5, "folga_ponta": 0.125, "folga_encaixe": 0.0625},
    "viga": {"esp": 1.5, "alt": 7.25, "balanco": 6.0, "peca_max": 96, "entalhe": 1.5, "fechamento_esp": 1.5},
    "caibro": {"esp": 1.5, "alt": 5.5, "comprimento": 36, "perfil": "nuvem"},
    "paisagismo": {"canteiro_in": 24, "pedra_in": 14, "lado": "vizinho", "trepadeiras": True},
    "materiais": {"nucleo": "pt", "revest": "cedro", "serrilhado": "cedro", "ripa": "cedro", "viga": "cedro", "caibro": "cedro"},
    "rotulos": {"nucleo": "PT pine 4x4 S4S, ground contact (UC4B)", "revest": "Cedar 2x6 S4S",
                "serrilhado": "Cedar 5/4 S4S (1\") notched", "lateral_ponta": "Cedar 5/4 S4S (1\") plain",
                "ripa": "Cedar 2x4 S4S (flat)", "viga": "Cedar 2x8 S4S", "caibro": "Cedar 2x6 S4S",
                "parafuso": "coated trim-head deck screws (ACQ-rated), countersunk",
                "especie": "Cedar = Western Red Cedar, kiln-dried, S4S (planed 4 sides). PT = Southern Yellow Pine #2, ground contact."},
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
        n, L = g["n_postes"], g["comprimento_total_in"]
        self.n, self.L = n, L
        self.nuc, self.fe, self.fl = po["nucleo"], po["face_esp"], po["face_larg"]
        self.s, self.lp = po["serrilhado_esp"], po["lateral_ponta_esp"]
        self.D = self.nuc + 2 * self.fe
        self.tl = [self.lp if i == 0 else self.s for i in range(n)]
        self.tr = [self.lp if i == n - 1 else self.s for i in range(n)]
        self.W = [self.tl[i] + self.nuc + self.tr[i] for i in range(n)]
        self.vao = (L - sum(self.W)) / (n - 1)
        self.xp, x = [], 0.0
        for i in range(n):
            self.xp.append(x)
            x += self.W[i] + self.vao
        self.xn = [self.xp[i] + self.tl[i] for i in range(n)]
        self.mf = []
        for i in range(n):
            f = self.W[i] - self.fl
            self.mf.append(0.0 if i == 0 else (f if i == n - 1 else f / 2))
        self.cx = [self.xn[i] + self.nuc / 2 for i in range(n)]
        self.entre_eixos = self.cx[2] - self.cx[1] if n > 2 else self.cx[1] - self.cx[0]
        # alturas: caibro entalhado nas vigas
        self.y_topo = g["altura_topo_in"]
        self.y_vtopo = self.y_topo - c["alt"] + v["entalhe"]          # topo das vigas = topo do núcleo
        self.y_cb0 = self.y_vtopo - v["entalhe"]                       # base do caibro
        self.y_poste = self.y_vtopo
        self.y_viga0 = self.y_vtopo - v["alt"]
        self.y_rev0 = g["colar_concreto"]["altura"] + 0.5
        self.y_r0 = g["y_primeira_ripa"]
        self.y_r1 = self.y_viga0 + 1.0
        H = self.y_r1 - self.y_r0
        e = r["espaco_min"]
        self.fiadas = int(r["fiadas"]) if r.get("fiadas") else int(math.floor((H + e) / (r["larg"] + e) + 1e-9))
        self.espaco = (H - self.fiadas * r["larg"]) / (self.fiadas - 1)
        self.passo = r["larg"] + self.espaco
        self.ripas_y = [self.y_r0 + i * self.passo for i in range(self.fiadas)]
        self.viz = g["lado_ripas"] == "vizinho"
        self.z_r0 = (self.fe + self.nuc - r["esp"]) if self.viz else self.fe
        self.z_r1 = self.z_r0 + r["esp"]
        self.comp_ripa = self.vao + 2 * (self.s - r["folga_ponta"])
        self.y_base = -g["embutimento_in"]
        self.x_viga0 = -v["balanco"]; self.x_viga1 = L + v["balanco"]
        if c.get("posicao") == "postes_e_meio":            # 1 caibro por poste + 1 no meio de cada vão
            xs = sorted(self.cx + [self.bay_centro(i) for i in range(n - 1)])
        else:
            xs = list(self.cx)
        self.xc = [x - c["esp"] / 2 for x in xs]
        self.zc0 = self.D / 2 - c["comprimento"] / 2
        self.zc1 = self.zc0 + c["comprimento"]
        Lv = self.x_viga1 - self.x_viga0
        k = 1
        while True:
            alvo = [self.x_viga0 + Lv * j / k for j in range(1, k)]
            em = sorted({min(range(n), key=lambda i: abs(self.cx[i] - t)) for t in alvo})
            pts = [self.x_viga0] + [self.cx[i] for i in em] + [self.x_viga1]
            pecas = [b - a for a, b in zip(pts, pts[1:])]
            if max(pecas) <= v["peca_max"] + 1e-6 or k > n:
                break
            k += 1
        self.emendas, self.pecas_viga = em, pecas
        self.comp_nucleo = self.y_poste - self.y_base
        self.comp_rev = self.y_poste - self.y_rev0
        self.fech_larg = self.D + 2 * v["esp"]

    def bay_ini(self, i):
        return self.xp[i] + self.W[i]

    def bay_centro(self, i):
        return self.bay_ini(i) + self.vao / 2


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


def _serr_z(G):
    """Faixa z do serrilhado que sobra atrás da ripa (corte na altura de uma ripa)."""
    return (G.fe, G.z_r0) if G.viz else (G.z_r1, G.fe + G.nuc)


def _poste_planta(v, G, i, M, x0=None):
    dx = (x0 - G.xp[i]) if x0 is not None else 0.0
    xp, xn, fe, nuc = G.xp[i] + dx, G.xn[i] + dx, G.fe, G.nuc
    v.peca(xn, fe, nuc, nuc, M["nucleo"], x_corte=True)
    v.peca(xp + G.mf[i], 0, G.fl, fe, M["revest"], x_corte=True)
    v.peca(xp + G.mf[i], fe + nuc, G.fl, fe, M["revest"], x_corte=True)
    za, zb = _serr_z(G)
    for xs, t, externo in ((xp, G.tl[i], i == 0), (xn + nuc, G.tr[i], i == G.n - 1)):
        if externo:
            v.peca(xs, fe, t, nuc, M["revest"], x_corte=True)
        else:
            v.peca(xs, fe, t, nuc, "vazio", tracejado=True)
            v.peca(xs, za, t, zb - za, M["serrilhado"], x_corte=True)


def _vigas_elev(v, G, M):
    vg = G.g["viga"]
    v.peca(G.x_viga0, G.y_viga0, G.x_viga1 - G.x_viga0, vg["alt"], M["viga"])
    for ie in G.emendas:
        v.linha([(G.cx[ie], G.y_viga0), (G.cx[ie], G.y_vtopo)], espessura=0.8)
    for xe in (G.x_viga0 - vg["fechamento_esp"], G.x_viga1):
        v.peca(xe, G.y_viga0, vg["fechamento_esp"], vg["alt"], M["viga"])


# ------------------------------------------------------------------ views
def vista_elevacao(G, esc=32):
    g, M = G.g, G.g["materiais"]
    v = Vista("ELEVATION — NEIGHBOR SIDE", esc)
    _terreno(v, G.x_viga0 - 10, G.x_viga1 + 10)
    d, col = g["sapata_diam_in"], g["colar_concreto"]
    for i in range(G.n):
        cx = G.cx[i]
        v.poligono([(cx - d / 2, G.y_base), (cx + d / 2, G.y_base), (cx + d / 2, 0), (cx - d / 2, 0)], "concreto", tracejado=True)
        v.poligono([(cx - d / 2, G.y_base - g["brita_in"]), (cx + d / 2, G.y_base - g["brita_in"]),
                    (cx + d / 2, G.y_base), (cx - d / 2, G.y_base)], "brita", tracejado=True)
        v.peca(G.xn[i], G.y_base, G.nuc, G.y_rev0 - G.y_base, M["nucleo"], tracejado=True)
    for i in range(G.n - 1):
        for yr in G.ripas_y:
            v.peca(G.bay_ini(i), yr, G.vao, g["ripa"]["larg"], M["ripa"])
    for i in range(G.n):
        v.peca(G.xp[i], G.y_rev0, G.W[i], G.comp_rev, M["serrilhado"])
        v.peca(G.xp[i] + G.mf[i], G.y_rev0, G.fl, G.comp_rev, M["revest"])
        _colar(v, G.cx[i], col)
    _vigas_elev(v, G, M)
    cb = g["caibro"]
    for xc in G.xc:
        v.peca(xc, G.y_cb0, cb["esp"], cb["alt"], M["caibro"])
    for i in range(G.n):
        v.eixo((G.cx[i], G.y_base - g["brita_in"] - 4), (G.cx[i], G.y_topo + 12), str(i + 1))
    yb = G.y_base - 10
    v.cota((0, yb), (G.L, yb), -9, tam=7)
    v.cotas_corrente(G.cx, yb, 0, tam=5)
    v.cota((G.x_viga0 - g["viga"]["fechamento_esp"], G.y_topo), (G.x_viga1 + g["viga"]["fechamento_esp"], G.y_topo), 24, tam=6.5)
    xr = G.x_viga1 + 12
    v.cotas_corrente([G.y_base - g["brita_in"], G.y_base, 0, G.y_r0, G.y_viga0, G.y_topo], xr, 0, horizontal=False, tam=5.5)
    v.cota((xr, 0), (xr, G.y_topo), 18, tam=6.5)
    v.texto(G.x_viga0 - 8, 1.5, "GRADE", 5.5, "end")
    v.chamada((G.xc[1] + 0.75, G.y_topo - 1), (G.xc[1] + 3, G.y_topo + 40),
              f"{len(G.xc)} rafters {g['rotulos']['caibro']} ({'at posts + mid-bay' if len(G.xc) > G.n else '1 per post'}), cloud-lift ends", 6)
    v.chamada((G.bay_centro(2), G.ripas_y[-4] + 1.7), (G.bay_centro(2) + 2, G.y_topo + 30),
              f"{G.fiadas} slats {g['rotulos']['ripa']} per bay, {pes_pol(G.espaco)} gap", 6)
    xe = G.cx[G.emendas[0]] if G.emendas else G.cx[G.n // 2]
    v.chamada((xe, G.y_viga0 + 3), (xe + 30, G.y_topo + 20),
              "top-board splices over posts " + ", ".join(str(i + 1) for i in G.emendas), 6)
    v.chamada((G.x_viga1 + 0.7, G.y_viga0 + 5), (G.x_viga1 + 4, G.y_topo + 8), "end cap", 5.5)
    v.chamada((G.cx[-3], 50), (G.cx[-3] + 26, -16), f"composite post ({G.g.get('_pref', 'A')}-3)", 5.5)
    v.marca_corte((G.bay_centro(0), G.y_topo + 8), (G.bay_centro(0), G.y_base - 2), "A")
    v.marca_corte((G.x_viga0 - 6, 40), (G.bay_ini(1) + 6, 40), "B")
    return v


def vista_planta(G, esc=32):
    g, M, D = G.g, G.g["materiais"], G.D
    pa = g.get("paisagismo") or {}
    v = Vista("PLAN — TOP VIEW", esc)
    if pa:
        viz = pa.get("lado") == "vizinho"
        zc = (D, D + pa["canteiro_in"]) if viz else (-pa["canteiro_in"], 0)
        zp = (zc[1], zc[1] + pa["pedra_in"]) if viz else (zc[0] - pa["pedra_in"], zc[0])
        v.poligono([(G.x_viga0, zc[0]), (G.x_viga1, zc[0]), (G.x_viga1, zc[1]), (G.x_viga0, zc[1])], "solo")
        v.poligono([(G.x_viga0, zp[0]), (G.x_viga1, zp[0]), (G.x_viga1, zp[1]), (G.x_viga0, zp[1])], "brita")
        if pa.get("trepadeiras"):
            for i in range(G.n - 1):
                v.circulo(G.bay_centro(i), zc[0] + 6, 3, "vazio")
    d = g["sapata_diam_in"]
    for i in range(G.n):
        v.circulo(G.cx[i], D / 2, d / 2, "vazio", tracejado=True)
    for i in range(G.n - 1):
        v.peca(G.bay_ini(i), G.z_r0, G.vao, G.z_r1 - G.z_r0, M["ripa"])
    for i in range(G.n):
        _poste_planta(v, G, i, M)
    vg, cb = g["viga"], g["caibro"]
    v.peca(G.x_viga0, -vg["esp"], G.x_viga1 - G.x_viga0, vg["esp"], M["viga"])
    v.peca(G.x_viga0, D, G.x_viga1 - G.x_viga0, vg["esp"], M["viga"])
    for xe in (G.x_viga0 - vg["fechamento_esp"], G.x_viga1):
        v.peca(xe, -vg["esp"], vg["fechamento_esp"], G.fech_larg, M["viga"])
    for xc in G.xc:
        v.peca(xc, G.zc0, cb["esp"], cb["comprimento"], M["caibro"])
    v.texto(G.L / 2, G.zc0 - 9, "HOUSE SIDE (kitchen)", 6.5, negrito=True)
    v.texto(G.L / 2, max(G.zc1, D + (pa.get("canteiro_in", 0) + pa.get("pedra_in", 0) if pa else 0)) + 4,
            "NEIGHBOR SIDE", 6.5, negrito=True)
    v.cota((G.x_viga0 - 2, G.zc0), (G.x_viga0 - 2, G.zc1), -8, tam=5.5)
    v.cota((G.cx[1], G.zc0 - 2), (G.cx[2], G.zc0 - 2), -4, texto=f"{pes_pol(G.entre_eixos)} o.c.", tam=5.5)
    if pa:
        v.chamada((G.bay_centro(G.n - 2), zc[0] + 6), (G.x_viga1 + 6, zc[0] + 4), "planting bed, 1 vine\nper bay", 5.5)
        v.chamada((G.x_viga1 - 4, (zp[0] + zp[1]) / 2), (G.x_viga1 + 6, zp[1] + 4), "river rock border", 5.5)
    v.chamada((G.cx[3] + d / 2 * 0.7, D / 2 - d / 2 * 0.7), (G.cx[3] + 18, G.zc0 - 4), f"Ø{pes_pol(d)} footing", 5.5)
    return v


def vista_lateral(G, esc=24):
    g, M, D = G.g, G.g["materiais"], G.D
    vg, cb = g["viga"], g["caibro"]
    v = Vista("SIDE ELEVATION (end view)", esc)
    _terreno(v, G.zc0 - 4, G.zc1 + 4, prof=6)
    v.peca(0, G.y_rev0, G.fe, G.comp_rev, M["revest"])
    v.peca(G.fe, G.y_rev0, G.nuc, G.comp_rev, M["revest"])
    v.peca(G.fe + G.nuc, G.y_rev0, G.fe, G.comp_rev, M["revest"])
    _colar(v, D / 2, g["colar_concreto"])
    v.peca(-vg["esp"], G.y_viga0, G.fech_larg, vg["alt"], M["viga"])          # fechamento da ponta
    v.poligono(perfil_caibro(G.zc0, cb["comprimento"], G.y_cb0, cb["alt"], cb["perfil"]), M["caibro"])
    v.cota((G.zc0, G.y_topo), (G.zc1, G.y_topo), 6, tam=5.5)
    v.cota((G.zc1 + 2, 0), (G.zc1 + 2, G.y_topo), 4, tam=5.5)
    v.chamada((D / 2 + 3, G.y_viga0 + 2), (G.zc1 - 2, G.y_viga0 - 10), "end cap", 5.5)
    v.texto(G.zc0, -10, "HOUSE", 6, "start", negrito=True)
    v.texto(G.zc1, -10, "NEIGHBOR", 6, "end", negrito=True)
    return v


def vista_corte_A(G, esc=16):
    g, M, D = G.g, G.g["materiais"], G.D
    r, vg, cb = g["ripa"], g["viga"], g["caibro"]
    v = Vista("SECTION A-A (mid-bay, looking at post 1)", esc)
    zmin, zmax = G.zc0 - 3, G.zc1 + 3
    _terreno(v, zmin, zmax)
    v.peca(0, G.y_rev0, G.fe, G.comp_rev, M["revest"], traco="#555")
    v.peca(G.fe + G.nuc, G.y_rev0, G.fe, G.comp_rev, M["revest"], traco="#555")
    v.peca(G.fe, G.y_rev0, G.nuc, G.comp_rev, M["serrilhado"], traco="#555")
    _colar(v, D / 2, g["colar_concreto"])
    for yr in G.ripas_y:
        v.peca(G.z_r0, yr, r["esp"], r["larg"], M["ripa"], x_corte=True)
    v.peca(-vg["esp"], G.y_viga0, vg["esp"], vg["alt"], M["viga"], x_corte=True)
    v.peca(D, G.y_viga0, vg["esp"], vg["alt"], M["viga"], x_corte=True)
    v.poligono(perfil_caibro(G.zc0, cb["comprimento"], G.y_cb0, cb["alt"], cb["perfil"]), M["caibro"])
    yb = G.y_viga0 + vg["alt"] / 2 - 1
    v.linha([(-vg["esp"] - 0.8, yb), (D + vg["esp"] + 0.8, yb)], espessura=1.2, traco="#333")
    zl = zmin - 2
    v.cotas_corrente([0, G.y_r0, G.y_viga0, G.y_topo], zl, 0, horizontal=False, tam=5.5)
    v.cota((zl, 0), (zl, G.y_topo), -9, tam=6)
    v.cota((G.z_r1, G.ripas_y[3]), (G.z_r1, G.ripas_y[3] + r["larg"]), 4, tam=5)
    v.cota((G.z_r1, G.ripas_y[3] + r["larg"]), (G.z_r1, G.ripas_y[4]), 8, tam=5)
    v.cota((-vg["esp"], G.y_topo + 2), (D + vg["esp"], G.y_topo + 2), 4, tam=5.5)
    v.cota((G.zc0, G.y_topo + 2), (G.zc1, G.y_topo + 2), 10, tam=5.5)
    v.cota((0, -2), (D, -2), -4, tam=5.5)
    zt = zmax + 2

    def ch(p, y, s):
        v.chamada(p, (zt, y), s, 5.5)
    ch((G.zc1 - 3, G.y_topo - 0.5), G.y_topo + 6, f"rafter {g['rotulos']['caibro']}\ncloud-lift end (det. 4)")
    ch((D + vg["esp"], G.y_viga0 + 4), G.y_viga0 + 1, f"top board {g['rotulos']['viga']} each side\nnotched {pes_pol(vg['entalhe'])} for rafters, 1/2\" thru-bolt")
    ch((G.fe + 0.3, G.ripas_y[11] + r["larg"] + G.espaco / 2), G.ripas_y[11] + 2, "notched side board tooth\n(beyond, det. 3)")
    ch((D - 0.3, G.ripas_y[7]), G.ripas_y[7], f"face {g['rotulos']['revest']}")
    ch((G.z_r1, G.ripas_y[2] + 2), G.ripas_y[2] - 2, f"slat {g['rotulos']['ripa']}\nset in notches")
    v.texto(-vg["esp"] - 1, G.y_topo + 16, "HOUSE", 6, "end", negrito=True)
    v.texto(D + vg["esp"] + 1, G.y_topo + 16, "NEIGHBOR", 6, "start", negrito=True)
    return v


def vista_fundacao(G, esc=12):
    g, M, D = G.g, G.g["materiais"], G.D
    d, E, B, col = g["sapata_diam_in"], g["embutimento_in"], g["brita_in"], g["colar_concreto"]
    v = Vista("DETAIL 1 — POST FOOTING", esc)
    c = D / 2
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
    v.peca(0, G.y_rev0, G.fe, topo - G.y_rev0, M["revest"])
    v.peca(D - G.fe, G.y_rev0, G.fe, topo - G.y_rev0, M["revest"])
    v.linha([(-1, topo), (D + 1, topo)], espessura=0.6, tracejado=True)
    v.cota((c - d / 2, -E - B - 3), (c + d / 2, -E - B - 3), -3, tam=5.5)
    v.cotas_corrente([-E - B, -E, 0], z0 - 1, 0, horizontal=False, tam=5.5)
    v.cota((a0, topo + 1), (a1, topo + 1), 3, tam=5.5)
    v.cota((z1 - 2, 0), (z1 - 2, G.y_rev0), 2, tam=5)
    v.chamada((a1 - 0.5, -8), (z1 + 4, -4), f"core {g['rotulos']['nucleo']}\nembedded {pes_pol(E)}", 5.5)
    v.chamada((c + d / 2 - 1.5, -16), (z1 + 4, -15), f"concrete around core\nØ{pes_pol(d)} hole (machine auger)", 5.5)
    v.chamada((c + d / 2 - 2, -E - B / 2), (z1 + 4, -E - B / 2 - 2), f"{pes_pol(B)} gravel (drainage)\ncore bears on gravel", 5.5)
    v.chamada((c + w - 1.5, col["altura"] * 0.6), (z1 + 4, 5), "exposed concrete collar\nsloped away from post", 5.5)
    v.chamada((D - G.fe / 2, G.y_rev0 + 6), (z1 + 4, 14),
              f"cladding starts {pes_pol(G.y_rev0 - col['altura'])} above collar\n(no wood-to-concrete contact)", 5.5)
    return v


def vista_poste(G, i, titulo, esc=3, ext=5.0):
    g, M, D = G.g, G.g["materiais"], G.D
    r = g["ripa"]
    v = Vista(titulo, esc)
    W, tl, tr = G.W[i], G.tl[i], G.tr[i]
    if i != 0:
        v.peca(-ext, G.z_r0, ext + tl - r["folga_ponta"], r["esp"], M["ripa"])
    if i != G.n - 1:
        v.peca(tl + G.nuc + r["folga_ponta"], G.z_r0, ext + tr - r["folga_ponta"], r["esp"], M["ripa"])
    _poste_planta(v, G, i, M, x0=0.0)
    m = G.mf[i]
    v.cota((0, D), (W, D), 2.2, tam=5.5)
    v.cota((0, D), (tl, D), 1.0, tam=5)
    v.cota((tl, D), (tl + G.nuc, D), 1.0, tam=5)
    v.cota((tl + G.nuc, D), (W, D), 1.0, tam=5)
    v.cota((m, 0), (m + G.fl, 0), -1.0, tam=5)
    xr = W + (ext if i != G.n - 1 else 1.0)
    v.cota((xr, 0), (xr, D), 2.4, tam=5.5)
    v.cota((xr, G.z_r0), (xr, G.z_r1), 1.0, tam=5)
    v.chamada((tl + 1.0, G.fe + 1.0), (-1.0, D + 3.6), f"core {g['rotulos']['nucleo']}", 5.5)
    v.chamada((m + 0.8, G.fe + G.nuc + 0.7), (-2.5, D + 2.4), f"face {g['rotulos']['revest']} (neighbor)", 5.5)
    v.chamada((m + 0.8, 0.5), (-2.5, -2.4), f"face {g['rotulos']['revest']} (house)", 5.5)
    if i == 0:
        v.chamada((tl / 2, G.fe + 0.6), (-2.5, D + 1.2), f"side {g['rotulos']['lateral_ponta']}", 5.5)
    v.chamada((tl + G.nuc + tr / 2, G.fe + 0.6), (W + 1.5, D + 3.6), f"side {g['rotulos']['serrilhado']}", 5.5)
    if i != G.n - 1:
        v.chamada((W + 3.0, G.z_r0 + 0.7), (W + 2.0, -2.4), f"slat goes {pes_pol(G.s - r['folga_ponta'])} into notch", 5.5)
    lx, an = (-ext, "start") if i != 0 else (-1.0, "end")
    v.texto(lx, -0.7, "HOUSE", 6, an, negrito=True)
    v.texto(lx, D - 0.6, "NEIGHBOR", 6, an, negrito=True)
    return v


def vista_serrilhado(G, esc=4, n=3):
    g, M = G.g, G.g["materiais"]
    r = g["ripa"]
    v = Vista("DETAIL 3 — NOTCHED SIDE BOARD (from bay)", esc)
    z0, z1 = G.fe, G.fe + G.nuc
    y0 = G.ripas_y[0] - 2.5
    y1 = G.ripas_y[n - 1] + r["larg"] + G.espaco
    fe = r["folga_encaixe"]
    if G.viz:   # encaixes na borda do lado do vizinho (z1)
        cont = [(z0, y0), (z0, y1), (z1, y1)]
        for i in reversed(range(n)):
            ya, yb = G.ripas_y[i] - fe / 2, G.ripas_y[i] + r["larg"] + fe / 2
            cont += [(z1, yb), (G.z_r0, yb), (G.z_r0, ya), (z1, ya)]
        cont.append((z1, y0))
        zn, zd = z1, G.z_r0
    else:
        cont = [(z1, y0), (z1, y1), (z0, y1)]
        for i in reversed(range(n)):
            ya, yb = G.ripas_y[i] - fe / 2, G.ripas_y[i] + r["larg"] + fe / 2
            cont += [(z0, yb), (G.z_r1, yb), (G.z_r1, ya), (z0, ya)]
        cont.append((z0, y0))
        zn, zd = z0, G.z_r1
    v.poligono(cont, M["serrilhado"])
    v.linha([(z0 - 0.4, y1 + 0.3), (z1 + 0.4, y1 - 0.3)], espessura=0.6)
    for i in range(n):
        v.peca(G.z_r0, G.ripas_y[i], r["esp"], r["larg"], "vazio", tracejado=True)
    v.cota((z0, y0), (z1, y0), -1.5, tam=5)
    v.cota((min(zn, zd), y1), (max(zn, zd), y1), 1.4, texto=f"{pes_pol(r['esp'])} deep", tam=5)
    zdim = z0 if G.viz else z1
    s = -1 if G.viz else 1
    ya, yb = G.ripas_y[1] - fe / 2, G.ripas_y[1] + r["larg"] + fe / 2
    v.cota((zdim, ya), (zdim, yb), 1.5 * s, texto=f"{pes_pol(yb - ya)} notch", tam=5)
    v.cota((zdim, yb), (zdim, G.ripas_y[2] - fe / 2), 1.5 * s, texto=f"{pes_pol(G.espaco - fe)} tooth", tam=5)
    v.cota((zdim, G.ripas_y[0]), (zdim, G.ripas_y[1]), 4.0 * s, texto=f"{pes_pol(G.passo)} pitch", tam=5)
    v.cota((z1 + 0.5, 0), (z1 + 0.5, G.ripas_y[0]), 1.5, texto=f"{pes_pol(G.ripas_y[0])} above grade", tam=5)
    v.linha([(z0 - 1, 0), (z1 + 2.5, 0)], espessura=1.0)
    v.texto(z0, y1 + 3.2, "HOUSE", 5.5, "middle", negrito=True)
    v.texto(z1, y1 + 3.2, "NEIGHBOR", 5.5, "middle", negrito=True)
    v.chamada((G.z_r0 + 0.7, G.ripas_y[0] + 1.5), (z1 + 3.0, G.ripas_y[0] + 6),
              f"slat end in notch\n(board {pes_pol(G.s)} thick)", 5)
    return v


def vista_caibro(G, esc=4):
    g, M = G.g, G.g["materiais"]
    cb = g["caibro"]
    v = Vista("DETAIL 4 — RAFTER END", esc)
    comp, alt = 14, cb["alt"]
    ponta = _ponta(alt, cb["perfil"])
    pts = [(0, alt), (comp, alt), (comp, 0)] + [(dz, y) for dz, y in reversed(ponta)]
    v.poligono(pts, M["caibro"])
    v.linha([(comp - 0.4, -0.6), (comp + 0.4, alt + 0.6)], espessura=0.6)
    v.cota((0, alt), (ponta[-1][0], alt), 1.5, tam=5)
    v.cota((-1, 0), (-1, alt), -1.5, tam=5)
    v.cota((-1, ponta[0][1]), (-1, alt), -4.5, tam=5)
    k = len(ponta) // 2
    v.chamada((ponta[k][0], ponta[k][1] + 0.1), (ponta[k][0] - 1, -2.6), "pre-cut in shop with template + jigsaw", 5)
    return v


def vista_topo(G, esc=8):
    """Detalhe 5: ponta das tábuas de topo (entalhe do caibro + fechamento)."""
    g, M = G.g, G.g["materiais"]
    vg, cb = g["viga"], g["caibro"]
    v = Vista("DETAIL 5 — TOP BOARD END: NOTCH + END CAP", esc)
    x0, x1 = G.x_viga0 - vg["fechamento_esp"], G.cx[0] + 9
    W0 = G.W[0]
    v.peca(0, G.y_viga0 - 8, W0, 8 + vg["alt"], M["revest"], tracejado=True)
    cont = [(G.x_viga0, G.y_viga0), (x1, G.y_viga0), (x1, G.y_vtopo)]
    for xc in reversed([xc for xc in G.xc if xc < x1 - 2]):
        cont += [(xc + cb["esp"] + 1 / 32, G.y_vtopo), (xc + cb["esp"] + 1 / 32, G.y_vtopo - vg["entalhe"]),
                 (xc - 1 / 32, G.y_vtopo - vg["entalhe"]), (xc - 1 / 32, G.y_vtopo)]
    cont.append((G.x_viga0, G.y_vtopo))
    v.poligono(cont, M["viga"])
    v.peca(x0, G.y_viga0, vg["fechamento_esp"], vg["alt"], M["viga"])
    for xc in G.xc:
        if xc < x1 - 2:
            v.peca(xc, G.y_cb0, cb["esp"], cb["alt"], M["caibro"])
    v.linha([(x1 - 0.5, G.y_viga0 - 1), (x1 + 0.5, G.y_topo + 1)], espessura=0.6)
    v.cota((G.xc[0], G.y_topo + 1), (G.xc[0] + cb["esp"], G.y_topo + 1), 2, tam=5)
    v.cota((x1 + 1, G.y_vtopo - vg["entalhe"]), (x1 + 1, G.y_vtopo), 2, texto=f"{pes_pol(vg['entalhe'])} notch", tam=5)
    v.cota((x0, G.y_viga0 - 1), (G.x_viga0, G.y_viga0 - 1), -2, tam=5)
    v.cota((G.x_viga0, G.y_viga0 - 1), (0, G.y_viga0 - 1), -2, tam=5)
    v.chamada((x0 + 0.7, G.y_viga0 + 2), (x0 - 4, G.y_viga0 - 6), f"end cap {g['rotulos']['viga']}\n{pes_pol(G.fech_larg)} wide", 5)
    v.chamada((G.cx[0] + 5, G.y_viga0 + 2), (G.cx[0] + 3, G.y_viga0 - 9), "top boards pre-notched\nin shop", 5)
    return v


def lista_pecas(G):
    g, nb, R = G.g, G.n - 1, G.g["rotulos"]
    pv = ", ".join(pes_pol(c) for c in sorted(set(round(c, 3) for c in G.pecas_viga), reverse=True))
    return (["Mark", "Part", "Material", "Qty", "Length", "Shop pre-cut / notes"], [
        ["N", "Post core", R["nucleo"], G.n, pes_pol(G.comp_nucleo), f"embed {pes_pol(g['embutimento_in'])}; trim tops on site"],
        ["S", "Notched side board", R["serrilhado"], 2 * nb, pes_pol(G.comp_rev), (f"YES: {G.fiadas} notches" if abs(G.nuc - 5.5) < 1e-6 else f"YES: rip to {pes_pol(G.nuc)}, {G.fiadas} notches")],
        ["R", "Slat", R["ripa"], G.fiadas * nb, pes_pol(G.comp_ripa), "YES: cut to length (stop block)"],
        ["F", "Post face", R["revest"], 2 * G.n, pes_pol(G.comp_rev), "YES: cut to length"],
        ["L", "Plain side (end posts)", R["lateral_ponta"], 2, pes_pol(G.comp_rev), "YES: cut to length" if abs(G.nuc - 5.5) < 1e-6 else f"YES: rip to {pes_pol(G.nuc)}"],
        ["T", f"Top board ({len(G.pecas_viga)} per side)", R["viga"], 2 * len(G.pecas_viga), pv, "YES: notches for rafters"],
        ["E", "Top board end cap", R["viga"], 2, pes_pol(G.fech_larg), "YES"],
        ["K", "Pergola rafter", R["caibro"], len(G.xc), pes_pol(g["caibro"]["comprimento"]), "YES: cloud-lift ends"],
    ])


def _nota_fib(G):
    phi = (1 + 5 ** 0.5) / 2
    r = G.vao / G.W[1]
    k = round(math.log(r, phi))
    fib = {2: "34/13", 3: "55/13", 4: "89/13", 5: "144/13"}.get(k, "")
    erro = (r / phi ** k - 1) * 100
    prop = f"Bay/post = {r:.2f} ≈ φ^{k}" + (f" (Fibonacci {fib})" if abs(erro) < 3 else f" ({erro:+.0f}% off)")
    if G.vao <= 36:
        emp = f"; span {pes_pol(G.vao)} < 36\" (low warping risk)."
    else:
        emp = f"; span {pes_pol(G.vao)} > 36\" limit (< 48\" max)."
    return prop + emp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--saida", default=None)
    ap.add_argument("--png", action="store_true")
    ap.add_argument("--previa", action="store_true", help="só PNG (sem PDF/DXF), para revisão antes de emitir")
    a = ap.parse_args()
    spec = json.load(open(a.spec, encoding="utf-8"))
    cad.set_idioma(spec.get("idioma_desenho", "en"))
    g = mescla(PADRAO, spec.get("geometria", {}))
    g["_pref"] = spec.get("prefixo_prancha", "A")
    G = Geo(g)
    base_dir = a.saida or os.path.join(os.path.dirname(os.path.abspath(a.spec)), "..", "desenhos")
    base = os.path.join(base_dir, "privacy-screen")
    proj = spec.get("projeto_en") or spec.get("projeto", "Privacy screen")
    meta = dict(cliente=spec.get("cliente", ""), autor=spec.get("autor", ""), data=spec.get("data", ""),
                revisao=str(spec.get("revisao", "0")))
    R = g["rotulos"]
    notas = [
        f"Overall length {pes_pol(G.L)}; {G.n} posts at {pes_pol(G.entre_eixos)} o.c.; clear bay {pes_pol(G.vao)}.",
        _nota_fib(G),
        f"Post cores embedded {pes_pol(g['embutimento_in'])} in concrete over {pes_pol(g['brita_in'])} gravel; holes by machine auger.",
        "Call NC811 before digging. Verify property line, setbacks and HOA.",
        f"Fasteners: {R['parafuso']}.",
        f"{G.fiadas} slats per bay, {pes_pol(G.espaco)} gap set by the notched side boards.",
        f"All posts {pes_pol(G.W[1])} wide, faces flush. Parts marked YES are pre-cut in the shop.",
        *[x.strip().rstrip(".") + "." for x in R["especie"].split(". ") if x.strip()],
    ]
    p1 = Prancha(proj, "Elevation and plan", f"{g['_pref']}-1", notas=notas, **meta)
    p1.add(vista_planta(G), 1.5, 0.95)
    p1.add(vista_elevacao(G), 1.0, 4.4)
    p1.add(vista_lateral(G), 13.4, 5.0)

    p2 = Prancha(proj, "Sections and details", f"{g['_pref']}-2", **meta)
    p2.add(vista_corte_A(G), 0.9, 1.1)
    p2.add(vista_fundacao(G), 5.0, 1.1)
    p2.add(vista_caibro(G), 5.9, 8.1)
    p2.add(vista_topo(G), 9.9, 6.6)
    p2.add(vista_serrilhado(G, esc=5), 13.7, 5.0)
    cols, linhas = lista_pecas(G)
    p2.tabela(9.95, 4.3, cols, linhas, [0.4, 1.45, 1.6, 0.33, 1.3, 1.6], "PARTS LIST", 5.8)

    p3 = Prancha(proj, "Composite post and installation", f"{g['_pref']}-3", **meta)
    p3.add(vista_poste(G, 1, "DETAIL 2a — INTERMEDIATE POST, SECTION B-B", esc=3), 1.4, 4.2)
    p3.add(vista_poste(G, 0, f"DETAIL 2b — END POST (1 and {G.n})", esc=3), 9.4, 4.2)
    side = "neighbor" if G.viz else "house"
    passos = [
        [1, f"HOLES: lay out {G.n} post centers at {pes_pol(G.entre_eixos)} o.c.; dig Ø{pes_pol(g['sapata_diam_in'])} x {pes_pol(g['embutimento_in'] + g['brita_in'])} with rented machine auger; {pes_pol(g['brita_in'])} gravel."],
        [2, f"POSTS: set {g['rotulos']['nucleo']} cores {pes_pol(g['embutimento_in'])} deep, plumb and brace, concrete with sloped collar. Cure 48 h."],
        [3, f"LEVEL TOPS: cut all cores to {pes_pol(G.y_poste)} above grade (laser level)."],
        [4, f"NOTCHED SIDE BOARDS (pre-cut): fasten to core sides from the {side} side, notches facing {side}."],
        [5, f"SLATS (pre-cut): drop into notches from the {side} side, bottom to top; 1 screw per end."],
        [6, f"FRONT CLOSURE: {g['rotulos']['revest']} face boards on both faces (closes the notches and locks the slats)."],
        [7, f"SIDE CLOSURE: {g['rotulos']['lateral_ponta']} on the outer side of end posts 1 and {G.n}."],
        [8, "TOP BOARDS (pre-notched): 2x8 each side of the posts, 1/2\" thru-bolt per post; splices over posts "
            + ", ".join(str(i + 1) for i in G.emendas) + "."],
        [9, "END CAPS (pre-cut): close the ends of the top boards for a solid-beam look."],
        [10, f"PERGOLA RAFTERS (pre-cut): {len(G.xc)} into top-board notches ({'posts + mid-bay' if len(G.xc) > G.n else '1 per post'}); hidden trim-head screws."],
    ]
    p3.tabela(1.0, 2.75, ["#", "INSTALLATION SEQUENCE"], passos, [0.3, 10.4], None, 6.2)
    pranchas = [p1, p2, p3]

    res = exportar(pranchas, base, png=a.png or a.previa, pdf=not a.previa, dxf=not a.previa)
    print(f"W {G.W[1]} | vão {G.vao:.3f} | o.c. {G.entre_eixos:.3f} | {G.fiadas} fiadas, espaço {G.espaco:.3f} | ripa {G.comp_ripa:.3f} | "
          f"núcleo {G.comp_nucleo:.1f} | revest {G.comp_rev:.2f} | vigas {[round(c, 2) for c in G.pecas_viga]} emendas "
          f"{[i + 1 for i in G.emendas]} | fechamento {G.fech_larg}")
    for k, v in res.items():
        if v:
            print(k, v)


if __name__ == "__main__":
    main()
