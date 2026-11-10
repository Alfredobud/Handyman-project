"""Mini-biblioteca de desenho técnico 2D para projetos em madeira.

Modelo em POLEGADAS (x para a direita, y para cima). Cada `Vista` tem uma escala
(denominador: 24 = 1:24 = 1/2" = 1'-0"). Uma `Prancha` posiciona vistas no papel
(em polegadas de papel) e exporta para SVG, PDF (via Chromium headless) e DXF
(via ezdxf, se instalado; no DXF tudo fica em escala 1:1, cada vista deslocada).

Uso típico (ver templates/privacy_screen.py):

    v = Vista("ELEVAÇÃO", escala=24)
    v.peca(0, 0, 5.5, 96, "pt")                 # retângulo com material
    v.cota((0, 0), (265, 0), -12)              # cota horizontal 12" abaixo
    p = Prancha("Projeto", "Elevação e planta", numero="A-1")
    p.add(v, x=1.0, y=1.0)                     # canto inferior-esquerdo da vista no papel
    exportar([p], "saida/desenhos")            # .svg por prancha + .pdf + .dxf
"""
import html
import math
import os
import shutil
import subprocess
import tempfile
from fractions import Fraction

# ------------------------------------------------------------------ estilos
MATERIAIS = {
    # nome: (preenchimento SVG, traço, cor DXF ACI, camada)
    "pt":       ("#c9cfa3", "#222", 52, "MADEIRA_PT"),
    "cedro":    ("#e2a86f", "#222", 30, "MADEIRA_CEDRO"),
    "madeira":  ("#e8cf9e", "#222", 40, "MADEIRA"),
    "composite": ("#b9b1a6", "#222", 8, "COMPOSITE"),
    "metal":    ("#9aa4ad", "#222", 9, "METAL"),
    "concreto": ("url(#h-concreto)", "#222", 8, "CONCRETO"),
    "brita":    ("url(#h-brita)", "#222", 8, "BRITA"),
    "solo":     ("url(#h-solo)", "none", 34, "SOLO"),
    "vazio":    ("none", "#222", 7, "CONTORNO"),
}
HATCH_DXF = {"concreto": ("AR-CONC", 0.05), "brita": ("GRAVEL", 0.5), "solo": ("EARTH", 0.5)}


def pes_pol(v, frac=16):
    """Formata polegadas como 22'-1 1/2" (>= 24") ou 46 3/8" (< 24")."""
    neg = v < 0
    v = abs(v)
    q = round(v * frac) / frac
    ft = int(q // 12) if q >= 24 else 0
    inch = q - ft * 12
    inteiro = int(inch)
    resto = Fraction(inch - inteiro).limit_denominator(frac)
    s_in = f"{inteiro}" + (f" {resto.numerator}/{resto.denominator}" if resto else "")
    s = f"{ft}'-{s_in}\"" if ft else f"{s_in}\""
    return ("-" if neg else "") + s


# ------------------------------------------------------------------ vista
class Vista:
    def __init__(self, titulo, escala, subtitulo=None):
        self.titulo = titulo
        self.escala = float(escala)
        self.subtitulo = subtitulo or escala_texto(escala)
        self.els = []

    # primitivas ------------------------------------------------------
    def poligono(self, pts, material="vazio", traco=None, espessura=0.8, tracejado=False, camada=None):
        self.els.append({"t": "poly", "pts": list(pts), "fechado": True, "mat": material,
                         "traco": traco, "esp": espessura, "dash": tracejado, "camada": camada})

    def linha(self, pts, traco="#222", espessura=0.6, tracejado=False, camada="CONTORNO"):
        self.els.append({"t": "poly", "pts": list(pts), "fechado": False, "mat": None,
                         "traco": traco, "esp": espessura, "dash": tracejado, "camada": camada})

    def peca(self, x, y, w, h, material="madeira", x_corte=False, **kw):
        """Retângulo de peça. x_corte=True desenha o X de peça cortada (seção)."""
        pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        self.poligono(pts, material, **kw)
        if x_corte:
            self.linha([(x, y), (x + w, y + h)], espessura=0.3, camada="CORTE")
            self.linha([(x + w, y), (x, y + h)], espessura=0.3, camada="CORTE")

    def circulo(self, cx, cy, r, material="vazio", tracejado=False):
        self.els.append({"t": "circ", "c": (cx, cy), "r": r, "mat": material, "dash": tracejado})

    def texto(self, x, y, s, tam=7, ancora="middle", negrito=False, rot=0, camada="TEXTO"):
        """tam em pontos no PAPEL (independe da escala)."""
        self.els.append({"t": "txt", "p": (x, y), "s": s, "tam": tam, "anc": ancora, "b": negrito,
                         "rot": rot, "camada": camada})

    def eixo(self, p1, p2, rotulo=None):
        self.linha([p1, p2], traco="#c33", espessura=0.3, tracejado="eixo", camada="EIXO")
        if rotulo:
            self.els.append({"t": "bolha", "p": p2, "s": rotulo})

    def cota(self, p1, p2, deslocamento, texto=None, tam=6.5):
        """Cota horizontal (p1.y==p2.y referência) ou vertical, conforme a maior diferença.
        deslocamento: distância em polegadas de MODELO, perpendicular (sinal = lado)."""
        (x1, y1), (x2, y2) = p1, p2
        horiz = abs(x2 - x1) >= abs(y2 - y1)
        self.els.append({"t": "cota", "p1": p1, "p2": p2, "d": deslocamento, "h": horiz,
                         "s": texto, "tam": tam})

    def cotas_corrente(self, pontos, y_ou_x, deslocamento, horizontal=True, tam=6):
        """Cadeia de cotas entre pontos consecutivos (lista de x se horizontal, de y se vertical)."""
        for a, b in zip(pontos, pontos[1:]):
            if horizontal:
                self.cota((a, y_ou_x), (b, y_ou_x), deslocamento, tam=tam)
            else:
                self.cota((y_ou_x, a), (y_ou_x, b), deslocamento, tam=tam)

    def chamada(self, p_alvo, p_texto, s, tam=6.5):
        """Seta de chamada (leader) com texto."""
        self.els.append({"t": "leader", "a": p_alvo, "b": p_texto, "s": s, "tam": tam})

    def marca_corte(self, p1, p2, rotulo):
        """Linha de corte com setas e letra (ex.: A)."""
        self.els.append({"t": "mcorte", "p1": p1, "p2": p2, "s": rotulo})

    # extensão ---------------------------------------------------------
    def limites(self):
        xs, ys = [], []
        for e in self.els:
            if e["t"] == "poly":
                xs += [p[0] for p in e["pts"]]; ys += [p[1] for p in e["pts"]]
            elif e["t"] == "circ":
                xs += [e["c"][0] - e["r"], e["c"][0] + e["r"]]; ys += [e["c"][1] - e["r"], e["c"][1] + e["r"]]
            elif e["t"] in ("txt", "bolha"):
                xs.append(e["p"][0]); ys.append(e["p"][1])
            elif e["t"] == "cota":
                for p in (e["p1"], e["p2"]):
                    xs.append(p[0] + (0 if e["h"] else e["d"])); ys.append(p[1] + (e["d"] if e["h"] else 0))
                    xs.append(p[0]); ys.append(p[1])
            elif e["t"] in ("leader", "mcorte"):
                for p in (e.get("a") or e["p1"], e.get("b") or e["p2"]):
                    xs.append(p[0]); ys.append(p[1])
        return min(xs), min(ys), max(xs), max(ys)


def escala_texto(den):
    den = float(den)
    nomes = {96: '1/8" = 1\'-0"', 48: '1/4" = 1\'-0"', 32: '3/8" = 1\'-0"', 24: '1/2" = 1\'-0"',
             16: '3/4" = 1\'-0"', 12: '1" = 1\'-0"', 8: '1 1/2" = 1\'-0"', 4: '3" = 1\'-0"', 2: '6" = 1\'-0"', 1: "1:1"}
    return f"ESCALA 1:{den:g}" + (f"  ({nomes[den]})" if den in nomes else "")


# ------------------------------------------------------------------ prancha
class Prancha:
    def __init__(self, projeto, titulo, numero="A-1", largura=17.0, altura=11.0, cliente="", autor="",
                 data="", notas=None, revisao="0"):
        self.projeto, self.titulo, self.numero = projeto, titulo, numero
        self.W, self.H = largura, altura
        self.cliente, self.autor, self.data, self.revisao = cliente, autor, data, revisao
        self.notas = notas or []
        self.vistas = []   # (vista, x, y, ancora_modelo)
        self.tabelas = []  # (x, y, colunas, linhas, larguras, titulo)

    def add(self, vista, x, y, origem=None):
        """Posiciona a vista: o ponto `origem` do modelo (padrão = canto inferior-esquerdo dos limites)
        vai para (x, y) em polegadas de papel, medido do canto inferior-esquerdo da folha."""
        if origem is None:
            x0, y0, _, _ = vista.limites()
            origem = (x0, y0)
        self.vistas.append((vista, x, y, origem))

    def tabela(self, x, y_topo, colunas, linhas, larguras, titulo=None, tam=6):
        self.tabelas.append((x, y_topo, colunas, linhas, larguras, titulo, tam))


# ------------------------------------------------------------------ SVG
PX = 100.0  # unidades SVG por polegada de papel

DEFS = """<defs>
<pattern id="h-solo" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
  <line x1="0" y1="0" x2="0" y2="14" stroke="#8a6d4b" stroke-width="1"/>
  <line x1="5" y1="0" x2="5" y2="14" stroke="#8a6d4b" stroke-width="0.5"/></pattern>
<pattern id="h-concreto" width="18" height="18" patternUnits="userSpaceOnUse">
  <rect width="18" height="18" fill="#e4e4e4"/>
  <circle cx="4" cy="5" r="1" fill="#777"/><circle cx="12" cy="12" r="1.3" fill="#777"/>
  <path d="M13 3 l3 4 h-5z" fill="none" stroke="#777" stroke-width="0.6"/>
  <path d="M3 13 l2.5 3.5 h-4z" fill="none" stroke="#777" stroke-width="0.6"/></pattern>
<pattern id="h-brita" width="16" height="12" patternUnits="userSpaceOnUse">
  <rect width="16" height="12" fill="#ececec"/>
  <ellipse cx="4" cy="4" rx="3" ry="2" fill="none" stroke="#666" stroke-width="0.6"/>
  <ellipse cx="12" cy="9" rx="3" ry="2" fill="none" stroke="#666" stroke-width="0.6"/></pattern>
<marker id="seta" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
  <path d="M0,0 L10,5 L0,10 z" fill="#222"/></marker>
</defs>"""


def _svg_prancha(p):
    W, H = p.W * PX, p.H * PX
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{p.W}in" height="{p.H}in" viewBox="0 0 {W:g} {H:g}" '
           f'font-family="DejaVu Sans, Arial, sans-serif">', DEFS,
           f'<rect width="{W:g}" height="{H:g}" fill="#fff"/>']
    m = 0.35 * PX
    out.append(f'<rect x="{m}" y="{m}" width="{W-2*m}" height="{H-2*m}" fill="none" stroke="#222" stroke-width="2"/>')

    for vista, x, y, (ox, oy) in p.vistas:
        k = PX / vista.escala

        def T(pt, x=x, y=y, ox=ox, oy=oy, k=k):
            return (x * PX + (pt[0] - ox) * k, H - (y * PX + (pt[1] - oy) * k))

        out.append(_svg_vista(vista, T, k))
        # título da vista
        x0, y0, x1, _ = vista.limites()
        cx = (T((x0, y0))[0] + T((x1, y0))[0]) / 2
        ty = T((x0, y0))[1] + 0.32 * PX
        out.append(f'<text x="{cx:.1f}" y="{ty:.1f}" font-size="{11/72*PX:.1f}" font-weight="bold" '
                   f'text-anchor="middle" text-decoration="underline">{html.escape(vista.titulo)}</text>')
        out.append(f'<text x="{cx:.1f}" y="{ty+0.16*PX:.1f}" font-size="{7/72*PX:.1f}" text-anchor="middle">'
                   f'{html.escape(vista.subtitulo)}</text>')

    for (tx, ty_top, cols, linhas, larg, titulo, tam) in p.tabelas:
        out.append(_svg_tabela(tx, ty_top, cols, linhas, larg, titulo, tam, H))
    out.append(_svg_carimbo(p, W, H, m))
    out.append("</svg>")
    return "\n".join(out)


def _fill(mat):
    return MATERIAIS.get(mat or "vazio", MATERIAIS["vazio"])


def _svg_vista(v, T, k):
    o = []
    for e in v.els:
        t = e["t"]
        if t == "poly":
            pts = " ".join(f"{a:.2f},{b:.2f}" for a, b in (T(q) for q in e["pts"]))
            fill, stroke = ("none", e["traco"] or "#222") if e["mat"] is None else _fill(e["mat"])[:2]
            if e.get("traco"):
                stroke = e["traco"]
            dash = ' stroke-dasharray="24,6,4,6"' if e["dash"] == "eixo" else (' stroke-dasharray="6,4"' if e["dash"] else "")
            tag = "polygon" if e["fechado"] else "polyline"
            fill = fill if e["fechado"] else "none"
            o.append(f'<{tag} points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{e["esp"]*1.6:.2f}"{dash}/>')
        elif t == "circ":
            (cx, cy), r = T(e["c"]), e["r"] * k
            fill, stroke = _fill(e["mat"])[:2]
            dash = ' stroke-dasharray="6,4"' if e["dash"] else ""
            o.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="{fill}" stroke="{stroke if stroke!="none" else "#222"}" stroke-width="1"{dash}/>')
        elif t == "txt":
            a, b = T(e["p"])
            rot = f' transform="rotate({-e["rot"]} {a:.1f} {b:.1f})"' if e["rot"] else ""
            o.append(_svg_text(a, b, e["s"], e["tam"], e["anc"], e["b"], rot))
        elif t == "bolha":
            a, b = T(e["p"])
            o.append(f'<circle cx="{a:.1f}" cy="{b-9:.1f}" r="9" fill="#fff" stroke="#c33" stroke-width="1"/>'
                     f'<text x="{a:.1f}" y="{b-5.5:.1f}" font-size="10" text-anchor="middle" fill="#c33">{html.escape(e["s"])}</text>')
        elif t == "cota":
            o.append(_svg_cota(e, T))
        elif t == "leader":
            (ax, ay), (bx, by) = T(e["a"]), T(e["b"])
            o.append(f'<polyline points="{bx:.1f},{by:.1f} {ax:.1f},{ay:.1f}" fill="none" stroke="#222" stroke-width="0.7" marker-end="url(#seta)"/>')
            anc = "start" if bx >= ax else "end"
            dx = 3 if anc == "start" else -3
            for i, ln in enumerate(e["s"].split("\n")):
                o.append(_svg_text(bx + dx, by + 3 + i * e["tam"] / 72 * PX * 1.15, ln, e["tam"], anc))
        elif t == "mcorte":
            (ax, ay), (bx, by) = T(e["p1"]), T(e["p2"])
            o.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="#222" stroke-width="1.4" stroke-dasharray="20,5,4,5"/>')
            for (px_, py_) in ((ax, ay), (bx, by)):
                o.append(f'<circle cx="{px_:.1f}" cy="{py_:.1f}" r="10" fill="#fff" stroke="#222" stroke-width="1.2"/>'
                         f'<text x="{px_:.1f}" y="{py_+4:.1f}" font-size="12" font-weight="bold" text-anchor="middle">{html.escape(e["s"])}</text>')
    return "\n".join(o)


def _svg_text(x, y, s, tam, anc="middle", bold=False, extra=""):
    fw = ' font-weight="bold"' if bold else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{tam/72*PX:.1f}" text-anchor="{anc}"{fw}{extra}>'
            f'{html.escape(s)}</text>')


def _svg_cota(e, T):
    (x1, y1), (x2, y2), d = e["p1"], e["p2"], e["d"]
    if e["h"]:
        yy = y1 + d
        a, b = (x1, yy), (x2, yy)
        ext = [((x1, y1), (x1, yy)), ((x2, y2), (x2, yy))]
        val = abs(x2 - x1)
    else:
        xx = x1 + d
        a, b = (xx, y1), (xx, y2)
        ext = [((x1, y1), (xx, y1)), ((x2, y2), (xx, y2))]
        val = abs(y2 - y1)
    s = e["s"] or pes_pol(val)
    o = []
    for p, q in ext:
        (px_, py_), (qx, qy) = T(p), T(q)
        # pequena folga na origem da linha de chamada
        L = math.hypot(qx - px_, qy - py_) or 1
        ux, uy = (qx - px_) / L, (qy - py_) / L
        o.append(f'<line x1="{px_+ux*3:.1f}" y1="{py_+uy*3:.1f}" x2="{qx+ux*4:.1f}" y2="{qy+uy*4:.1f}" stroke="#555" stroke-width="0.5"/>')
    (ax, ay), (bx, by) = T(a), T(b)
    o.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="#222" stroke-width="0.6"/>')
    for (cx, cy) in ((ax, ay), (bx, by)):  # tique arquitetônico
        o.append(f'<line x1="{cx-4:.1f}" y1="{cy+4:.1f}" x2="{cx+4:.1f}" y2="{cy-4:.1f}" stroke="#222" stroke-width="1.1"/>')
    mx, my = (ax + bx) / 2, (ay + by) / 2
    if e["h"]:
        o.append(_svg_text(mx, my - 3, s, e["tam"]))
    else:
        o.append(_svg_text(mx - 3, my, s, e["tam"], extra=f' transform="rotate(-90 {mx-3:.1f} {my:.1f})"'))
    return "\n".join(o)


def _svg_tabela(x, y_topo, cols, linhas, larg, titulo, tam, H):
    o = []
    lh = tam / 72 * PX * 1.55
    X0, Y = x * PX, H - y_topo * PX
    if titulo:
        o.append(_svg_text(X0, Y - 4, titulo, tam + 2, "start", True))
    total = sum(larg) * PX
    for i, row in enumerate([cols] + linhas):
        yy = Y + i * lh
        if i == 0:
            o.append(f'<rect x="{X0:.1f}" y="{yy:.1f}" width="{total:.1f}" height="{lh:.1f}" fill="#eee" stroke="#222" stroke-width="0.6"/>')
        else:
            o.append(f'<rect x="{X0:.1f}" y="{yy:.1f}" width="{total:.1f}" height="{lh:.1f}" fill="none" stroke="#999" stroke-width="0.4"/>')
        cx = X0
        for c, w in zip(row, larg):
            o.append(_svg_text(cx + 3, yy + lh * 0.7, str(c), tam, "start", i == 0))
            cx += w * PX
    return "\n".join(o)


def _quebra(s, n, max_linhas):
    palavras, linhas, atual = s.split(), [], ""
    for w in palavras:
        if len(atual) + len(w) + 1 > n and atual:
            linhas.append(atual); atual = w
        else:
            atual = (atual + " " + w).strip()
    linhas.append(atual)
    if len(linhas) > max_linhas:
        linhas = linhas[:max_linhas]; linhas[-1] = linhas[-1][: n - 1] + "…"
    return linhas


def _svg_carimbo(p, W, H, m):
    w, h = 4.6 * PX, 1.45 * PX
    x, y = W - m - w, H - m - h
    o = [f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="#fff" stroke="#222" stroke-width="1.5"/>',
         f'<line x1="{x:.1f}" y1="{y+0.42*PX:.1f}" x2="{x+w:.1f}" y2="{y+0.42*PX:.1f}" stroke="#222" stroke-width="0.8"/>',
         f'<line x1="{x+w-0.9*PX:.1f}" y1="{y+0.42*PX:.1f}" x2="{x+w-0.9*PX:.1f}" y2="{y+h:.1f}" stroke="#222" stroke-width="0.8"/>',
         *[_svg_text(x + 6, y + (0.14 + 0.13 * i) * PX, ln, 7.5, "start", True)
           for i, ln in enumerate(_quebra(p.projeto + (f" — {p.cliente}" if p.cliente else ""), 64, 2))],
         _svg_text(x + 6, y + 0.62 * PX, p.titulo[:60], 10, "start", True),
         _svg_text(x + 6, y + 0.85 * PX, f"Data: {p.data}   Rev.: {p.revisao}   Por: {p.autor}"[:80], 6.5, "start"),
         _svg_text(x + 6, y + 1.05 * PX, "Medidas em polegadas/pés. Madeira: medidas reais (6x6 = 5 1/2\").", 6, "start"),
         _svg_text(x + 6, y + 1.22 * PX, "Conferir no campo antes de cortar. Não é projeto estrutural.", 6, "start"),
         _svg_text(x + w - 0.45 * PX, y + 0.95 * PX, p.numero, 20, "middle", True)]
    if p.notas:
        nx, ny = x, y - 0.12 * PX
        lh = 6.5 / 72 * PX * 1.35
        top = ny - lh * (len(p.notas) + 1)
        o.append(f'<rect x="{nx:.1f}" y="{top-6:.1f}" width="{w:.1f}" height="{ny-top+8:.1f}" fill="#fff" stroke="#222" stroke-width="0.8"/>')
        o.append(_svg_text(nx + 6, top + lh * 0.6, "NOTAS", 7.5, "start", True))
        for i, n in enumerate(p.notas, 1):
            o.append(_svg_text(nx + 6, top + lh * (i + 0.6), f"{i}. {n}", 6.5, "start"))
    return "\n".join(o)


# ------------------------------------------------------------------ DXF
def _dxf(pranchas, caminho):
    try:
        import ezdxf
        from ezdxf.enums import TextEntityAlignment
    except ImportError:
        return False
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.IN
    msp = doc.modelspace()
    for nome, (_, _, aci, camada) in MATERIAIS.items():
        if camada not in doc.layers:
            doc.layers.add(camada, color=aci)
    for c, aci in (("COTA", 1), ("TEXTO", 7), ("EIXO", 1), ("CORTE", 8), ("CONTORNO", 7), ("TITULO", 7)):
        if c not in doc.layers:
            doc.layers.add(c, color=aci)

    oy_prancha = 0.0
    for p in pranchas:
        ox_v = 0.0
        alt_max = 0.0
        for vista, _, _, _ in p.vistas:
            x0, y0, x1, y1 = vista.limites()
            dx, dy = ox_v - x0, oy_prancha - y0
            off = lambda q: (q[0] + dx, q[1] + dy)
            s = vista.escala  # texto: tamanho de papel * escala = altura no modelo
            for e in vista.els:
                t = e["t"]
                if t == "poly":
                    mat = e["mat"]
                    camada = e.get("camada") or (_fill(mat)[3] if mat else "CONTORNO")
                    pts = [off(q) for q in e["pts"]]
                    msp.add_lwpolyline(pts, close=e["fechado"], dxfattribs={"layer": camada,
                                       "linetype": "CENTER" if e["dash"] == "eixo" else ("DASHED" if e["dash"] else "BYLAYER")})
                    if e["fechado"] and mat in HATCH_DXF:
                        pat, sc = HATCH_DXF[mat]
                        h = msp.add_hatch(dxfattribs={"layer": _fill(mat)[3]})
                        h.set_pattern_fill(pat, scale=sc)
                        h.paths.add_polyline_path(pts, is_closed=True)
                elif t == "circ":
                    msp.add_circle(off(e["c"]), e["r"], dxfattribs={"layer": _fill(e["mat"])[3]})
                elif t == "txt":
                    al = {"middle": TextEntityAlignment.BOTTOM_CENTER, "start": TextEntityAlignment.BOTTOM_LEFT,
                          "end": TextEntityAlignment.BOTTOM_RIGHT}[e["anc"]]
                    msp.add_text(e["s"], height=e["tam"] / 72 * s, rotation=e["rot"],
                                 dxfattribs={"layer": "TEXTO"}).set_placement(off(e["p"]), align=al)
                elif t == "cota":
                    (x1_, y1_), (x2_, y2_) = off(e["p1"]), off(e["p2"])
                    if e["h"]:
                        base = (x1_, y1_ + e["d"]); ang = 0
                    else:
                        base = (x1_ + e["d"], y1_); ang = 90
                    d = msp.add_linear_dim(base=base, p1=(x1_, y1_), p2=(x2_, y2_), angle=ang,
                                           text=e["s"] or pes_pol(abs((x2_ - x1_) if e["h"] else (y2_ - y1_))),
                                           dimstyle="EZ_INCH_2" if "EZ_INCH_2" in doc.dimstyles else "Standard",
                                           override={"dimtxt": e["tam"] / 72 * s, "dimasz": 0.08 * s, "dimtsz": 0.06 * s,
                                                     "dimexo": 0.04 * s, "dimexe": 0.06 * s},
                                           dxfattribs={"layer": "COTA"})
                    d.render()
                elif t == "leader":
                    a, b = off(e["a"]), off(e["b"])
                    msp.add_line(b, a, dxfattribs={"layer": "COTA"})
                    for i, ln in enumerate(e["s"].split("\n")):
                        msp.add_text(ln, height=e["tam"] / 72 * s, dxfattribs={"layer": "TEXTO"}).set_placement(
                            (b[0], b[1] - i * e["tam"] / 72 * s * 1.3))
                elif t == "mcorte":
                    msp.add_line(off(e["p1"]), off(e["p2"]), dxfattribs={"layer": "CORTE", "linetype": "PHANTOM"})
                    for q in (e["p1"], e["p2"]):
                        msp.add_text(e["s"], height=0.15 * s, dxfattribs={"layer": "TEXTO"}).set_placement(off(q))
                elif t == "bolha":
                    msp.add_circle(off(e["p"]), 0.1 * s, dxfattribs={"layer": "EIXO"})
                    msp.add_text(e["s"], height=0.1 * s, dxfattribs={"layer": "EIXO"}).set_placement(
                        off(e["p"]), align=TextEntityAlignment.MIDDLE_CENTER)
            msp.add_text(f"{p.numero} - {vista.titulo} ({vista.subtitulo})", height=0.15 * s,
                         dxfattribs={"layer": "TITULO"}).set_placement((ox_v, oy_prancha - 0.6 * s))
            ox_v += (x1 - x0) + 60
            alt_max = max(alt_max, y1 - y0)
        oy_prancha -= alt_max + 120
    doc.saveas(caminho)
    return True


# ------------------------------------------------------------------ exportar
def _chromium():
    for c in ("/opt/pw-browsers/chromium", shutil.which("chromium") or "", shutil.which("google-chrome") or "",
              shutil.which("chromium-browser") or ""):
        if c and os.path.exists(c):
            return c
    return None


def exportar(pranchas, base, pdf=True, dxf=True, png=False):
    """Gera <base>-<numero>.svg, <base>.pdf (todas as pranchas) e <base>.dxf. Retorna dict com caminhos."""
    os.makedirs(os.path.dirname(os.path.abspath(base)), exist_ok=True)
    res = {"svg": [], "pdf": None, "dxf": None, "png": []}
    svgs = []
    for p in pranchas:
        s = _svg_prancha(p)
        cam = f"{base}-{p.numero}.svg"
        with open(cam, "w", encoding="utf-8") as f:
            f.write(s)
        res["svg"].append(cam)
        svgs.append((p, s))
    nav = _chromium()
    if (pdf or png) and nav:
        W, H = pranchas[0].W, pranchas[0].H
        pag = "".join(f'<div class="pg">{s}</div>' for _, s in svgs)
        doc = (f"<!doctype html><html><head><meta charset='utf-8'><style>@page{{size:{W}in {H}in;margin:0}}"
               f"html,body{{margin:0}} .pg{{width:{W}in;height:{H}in;page-break-after:always;overflow:hidden}}"
               f".pg:last-child{{page-break-after:auto}}</style></head><body>{pag}</body></html>")
        with tempfile.TemporaryDirectory() as td:
            hp = os.path.join(td, "p.html")
            with open(hp, "w", encoding="utf-8") as f:
                f.write(doc)
            if pdf:
                out = os.path.abspath(base + ".pdf")
                subprocess.run([nav, "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                                f"--print-to-pdf={out}", "file://" + hp], check=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
                res["pdf"] = out
            if png:
                for p, s in svgs:
                    sp = os.path.join(td, f"{p.numero}.html")
                    with open(sp, "w", encoding="utf-8") as f:
                        f.write(f"<!doctype html><html><body style='margin:0'>{s}</body></html>")
                    out = os.path.abspath(f"{base}-{p.numero}.png")
                    subprocess.run([nav, "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                                    f"--window-size={int(p.W*96)},{int(p.H*96)}", "--force-device-scale-factor=1.5",
                                    f"--screenshot={out}", "file://" + sp], check=True,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
                    res["png"].append(out)
    if dxf:
        cam = base + ".dxf"
        if _dxf(pranchas, cam):
            res["dxf"] = cam
    return res
