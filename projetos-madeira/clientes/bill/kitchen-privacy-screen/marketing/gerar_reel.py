#!/usr/bin/env python3
"""Reel "Made it with AI. Who's going to build it?" — roteiro em marketing/reel-roteiro.md.

1080x1920, 30 fps, ~60 s, SEM áudio (a música entra no app do Instagram).

Uso (a partir da pasta do projeto):
    node marketing/capturar_fontes.js        # 1x: pranchas/proposta/3D anonimizados -> marketing/build/src
    python3 marketing/gerar_reel.py --previa  # 6 quadros-chave + folha de contato em marketing/build/previa
    python3 marketing/gerar_reel.py           # MP4 final + capa em marketing/

Regras do roteiro aplicadas aqui: cliente anônimo, sem preços, "dramatization" na abertura,
números rotulados como "design check", imagens de IA marcadas como tal, termina em
"build-ready project" (a cerca ainda não foi construída).
"""
import math
import os
import subprocess
import sys
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFilter, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(AQUI)
SRC = os.path.join(AQUI, "build", "src")
W, H, FPS = 1080, 1920, 30
DUR = 60.0
SAFE_TOP, SAFE_BOT = 250, 1570  # fora disso a UI do Reels cobre

BG = (22, 19, 16)
INK = (244, 236, 226)
MUTED = (176, 164, 152)
ACC = (208, 138, 82)
GOOD = (122, 196, 128)
WARN = (236, 118, 78)
PAPER = (250, 248, 244)

FD = "/usr/share/fonts/opentype/inter/"


@lru_cache(None)
def font(size, w="Bold", display=True):
    return ImageFont.truetype(f"{FD}{'InterDisplay' if display else 'Inter'}-{w}.otf", size)


@lru_cache(None)
def emoji(ch, size):
    f = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109)
    im = Image.new("RGBA", (140, 140))
    ImageDraw.Draw(im).text((0, 0), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    return im.resize((size, round(size * im.height / im.width)), Image.LANCZOS)


# ---------------------------------------------------------------- utilidades
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def prog(t, a, b):
    return clamp((t - a) / (b - a))


@lru_cache(None)
def src(name):
    p = os.path.join(SRC, name) if not name.startswith("/") else name
    return Image.open(p).convert("RGBA")


def ref(name):
    return src(os.path.join(PROJ, "referencias", name))


@lru_cache(None)
def sheet_crop(name, box):
    """Recorte de prancha; box em coordenadas da folha 1700x1100 (o PNG é 2x)."""
    x0, y0, x1, y1 = box
    return src(f"{name}.png").crop((x0 * 2, y0 * 2, x1 * 2, y1 * 2))


_FIT = {}


def sized(im, w=None, h=None):
    """Redimensiona mantendo proporção; cache por objeto (as fontes também ficam em cache)."""
    k = (id(im), w, h)
    if k not in _FIT:
        if w and not h:
            h = round(im.height * w / im.width)
        elif h and not w:
            w = round(im.width * h / im.height)
        _FIT[k] = (im, im.resize((w, h), Image.LANCZOS))
    return _FIT[k][1]


def cover(im, w, h, zoom=1.0, fx=0.5, fy=0.5):
    s = max(w / im.width, h / im.height) * zoom
    sw, sh = im.width * s, im.height * s
    x0 = (sw - w) * fx / s
    y0 = (sh - h) * fy / s
    return im.resize((w, h), Image.LANCZOS, box=(x0, y0, x0 + w / s, y0 + h / s))


@lru_cache(None)
def blurred_bg(name_or_ref, dark=0.55):
    im = ref(name_or_ref) if "." in name_or_ref and "/" not in name_or_ref and not name_or_ref.endswith(".png") else src(name_or_ref)
    b = cover(im, W // 4, H // 4).filter(ImageFilter.GaussianBlur(8)).resize((W, H), Image.BILINEAR)
    return Image.blend(b.convert("RGB"), Image.new("RGB", (W, H), BG), dark).convert("RGBA")


def canvas(color=BG):
    return Image.new("RGBA", (W, H), color + (255,))


def paste(dst, im, xy, alpha=1.0):
    if alpha <= 0:
        return
    if alpha < 1:
        im = im.copy()
        a = im.getchannel("A").point(lambda v: int(v * alpha))
        im.putalpha(a)
    dst.alpha_composite(im, (round(xy[0]), round(xy[1])))


def shadowed(im, radius=26, r=22, off=14, op=150):
    """Cartão com cantos arredondados e sombra."""
    w, h = im.size
    pad = radius * 2
    out_ = Image.new("RGBA", (w + pad * 2, h + pad * 2))
    sh = Image.new("RGBA", out_.size)
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + off, pad + w, pad + h + off), r, fill=(0, 0, 0, op))
    out_.alpha_composite(sh.filter(ImageFilter.GaussianBlur(radius)))
    m = Image.new("L", (w, h))
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    card = im.copy()
    card.putalpha(Image.composite(im.getchannel("A"), Image.new("L", (w, h)), m))
    out_.alpha_composite(card, (pad, pad))
    return out_, pad


def card(dst, im, x, y, alpha=1.0, rot=0.0, r=18):
    c, pad = shadowed(im, r=r)
    if rot:
        cx, cy = x + im.width / 2, y + im.height / 2
        c = c.rotate(rot, resample=Image.BICUBIC, expand=True)
        paste(dst, c, (cx - c.width / 2, cy - c.height / 2), alpha)
    else:
        paste(dst, c, (x - pad, y - pad), alpha)


def wrap(text, f, maxw):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            t = (cur + " " + word).strip()
            if f.getlength(t) <= maxw or not cur:
                cur = t
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def text_block(text, size=58, w="Bold", color=INK, maxw=920, lh=1.18, align="center"):
    f = font(size, w)
    lines = wrap(text, f, maxw)
    lhp = round(size * lh)
    tw = max(f.getlength(l) for l in lines)
    im = Image.new("RGBA", (math.ceil(tw) + 4, lhp * len(lines) + round(size * 0.3)))
    d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        x = (tw - f.getlength(l)) / 2 if align == "center" else 0
        d.text((x, i * lhp), l, font=f, fill=color)
    return im


def caption(dst, text, t, t_in=0.15, cy=1440, size=56, color=INK, box=(14, 12, 10, 225), maxw=900):
    """Legenda em caixa escura, dentro da área segura; entra com fade + leve subida."""
    a = ease(prog(t, t_in, t_in + 0.35))
    if a <= 0:
        return
    tb = text_block(text, size, "Bold", color, maxw)
    bw, bh = tb.width + 76, tb.height + 52
    bx = (W - bw) / 2
    by = min(cy - bh / 2, SAFE_BOT - 8 - bh) + (1 - a) * 30
    layer = Image.new("RGBA", (bw, bh))
    ImageDraw.Draw(layer).rounded_rectangle((0, 0, bw - 1, bh - 1), 30, fill=box)
    layer.alpha_composite(tb, (38, 30))
    paste(dst, layer, (bx, by), a)


def pill(text, size=30, fg=INK, bg=(14, 12, 10, 200), w="SemiBold", padx=20, pady=11):
    f = font(size, w, display=False)
    tw = f.getlength(text)
    asc, desc = f.getmetrics()
    im = Image.new("RGBA", (round(tw + padx * 2), asc + desc + pady * 2))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), im.height // 2, fill=bg)
    d.text((padx, pady), text, font=f, fill=fg)
    return im


def tag(dst, text, x, y, alpha=1.0, anchor="l"):
    p = pill(text, 26, MUTED, (10, 9, 8, 190), "Medium", 16, 8)
    paste(dst, p, (x - p.width if anchor == "r" else x, y), alpha)


def arrow(d, x0, y0, x1, y1, color, w=8, head=26):
    d.line((x0, y0, x1, y1), fill=color, width=w)
    ang = math.atan2(y1 - y0, x1 - x0)
    pts = [(x1, y1)]
    for s in (-1, 1):
        pts.append((x1 - head * math.cos(ang + s * 0.45), y1 - head * math.sin(ang + s * 0.45)))
    d.polygon(pts, fill=color)


# ---------------------------------------------------------------- cenas
def s_chat(t):
    """0:00–0:04 gancho: mensagem do proprietário com a imagem de IA."""
    im = canvas((14, 13, 12))
    d = ImageDraw.Draw(im)
    px0, py0, px1, py1 = 175, 330, 905, 1560
    d.rounded_rectangle((px0 - 16, py0 - 16, px1 + 16, py1 + 16), 84, fill=(40, 38, 36))
    d.rounded_rectangle((px0, py0, px1, py1), 70, fill=(236, 230, 222))
    # cabeçalho do chat
    d.rounded_rectangle((px0, py0, px1, py0 + 150), 70, fill=(250, 247, 243))
    d.rectangle((px0, py0 + 80, px1, py0 + 150), fill=(250, 247, 243))
    d.line((px0, py0 + 150, px1, py0 + 150), fill=(215, 207, 198), width=2)
    d.ellipse((px0 + 40, py0 + 46, px0 + 120, py0 + 126), fill=(196, 180, 162))
    d.text((px0 + 80, py0 + 86), "H", font=font(40), fill=(250, 247, 243), anchor="mm")
    d.text((px0 + 145, py0 + 52), "Homeowner", font=font(38, "SemiBold", False), fill=(30, 28, 26))
    d.text((px0 + 145, py0 + 98), "online", font=font(26, "Regular", False), fill=(120, 112, 104))
    bx, by = px0 + 36, py0 + 200
    if 0.15 <= t < 0.95:  # digitando…
        d.rounded_rectangle((bx, by, bx + 160, by + 84), 40, fill=(255, 255, 255))
        for i in range(3):
            k = 0.5 + 0.5 * math.sin(t * 12 - i * 0.9)
            d.ellipse((bx + 34 + i * 38 - 9, by + 42 - 9 - 6 * k, bx + 34 + i * 38 + 9, by + 42 + 9 - 6 * k),
                      fill=(150 + int(60 * (1 - k)),) * 3)
    if t >= 0.95:
        a = out(prog(t, 0.95, 1.2))
        tb = text_block("Hey! I need a fence by my kitchen. Look what I made with AI", 40, "Medium",
                        (30, 28, 26), 520, 1.25, "left")
        e = emoji("\U0001F447", 44)
        bub = Image.new("RGBA", (tb.width + 60, tb.height + 40 + 50))
        bd = ImageDraw.Draw(bub)
        bd.rounded_rectangle((0, 0, bub.width - 1, bub.height - 1), 36, fill=(255, 255, 255))
        bub.alpha_composite(tb, (30, 24))
        bub.alpha_composite(e, (30, tb.height + 18))
        paste(im, bub, (bx, by + (1 - a) * 20), a)
        by2 = by + bub.height + 22
        if t >= 1.45:
            a2 = out(prog(t, 1.45, 1.8))
            pic = sized(ref("conceito-000.jpg"), 540)
            fr = Image.new("RGBA", (pic.width + 20, pic.height + 20))
            ImageDraw.Draw(fr).rounded_rectangle((0, 0, fr.width - 1, fr.height - 1), 30, fill=(255, 255, 255))
            m = Image.new("L", pic.size)
            ImageDraw.Draw(m).rounded_rectangle((0, 0, pic.width - 1, pic.height - 1), 22, fill=255)
            p2 = pic.copy()
            p2.putalpha(m)
            fr.alpha_composite(p2, (10, 10))
            sc = 0.85 + 0.15 * a2
            fr = fr.resize((round(fr.width * sc), round(fr.height * sc)), Image.LANCZOS)
            paste(im, fr, (bx, by2), a2)
            d.text((bx + 8, by2 + fr.height + 10), "AI image · 9:41", font=font(24, "Regular", False),
                   fill=(120, 112, 104))
    # o título grande por cima
    if t >= 2.1:
        k = ease(prog(t, 2.1, 2.45))
        scrim = Image.new("RGBA", (W, H), (10, 9, 8, int(185 * k)))
        im.alpha_composite(scrim)
        t1 = text_block("Made it with AI.", 112, "Black", INK, 960)
        paste(im, t1, ((W - t1.width) / 2, 700 + (1 - k) * 40), k)
        if t >= 2.7:
            k2 = ease(prog(t, 2.7, 3.0))
            t2 = text_block("Who's going to build it?", 100, "Black", ACC, 940)
            paste(im, t2, ((W - t2.width) / 2, 880 + (1 - k2) * 40), k2)
    tag(im, "dramatization", W - 40, 268, 1.0, "r")
    return im


def s_concept(t, T=4.0):
    """0:04–0:08 imagem de IA, zoom lento."""
    im = blurred_bg("conceito-000.jpg", 0.5).copy()
    z = 1.0 + 0.10 * (t / T)
    pic = ref("conceito-000.jpg")
    w = round(1080 * z)
    h = round(pic.height * w / pic.width)
    big = pic.resize((w, h), Image.BILINEAR)
    y = 430 - (h - 810) / 2
    paste(im, big, ((W - w) / 2, y))
    tag(im, "homeowner's AI image", 36, 368)
    caption(im, "Beautiful. But can it actually be built?", t, 0.3, cy=1390, size=64)
    return im


def s_spacing(t):
    """0:08–0:12 diagrama da elevação: postes surgindo, cotas dos vãos."""
    im = canvas((26, 24, 22))
    d = ImageDraw.Draw(im)
    x0, x1, gy = 90, 990, 1010
    ppf = (x1 - x0) / 22.083
    pw, pc = 5.5 / 12 * ppf, 3.604 * ppf
    hh = 8 * ppf
    d.line((40, gy, W - 40, gy), fill=(120, 108, 96), width=4)
    for i in range(30):
        xx = 40 + i * 36
        d.line((xx, gy + 4, xx - 22, gy + 30), fill=(80, 72, 64), width=3)
    xs = [x0 + pw / 2 + i * pc for i in range(7)]
    wood = (214, 150, 96)
    # ripas (24 por vão) entram depois dos postes
    sa = ease(prog(t, 1.35, 1.9))
    if sa > 0:
        for b in range(6):
            for k in range(24):
                if k / 24 > sa:
                    break
                yy = gy - 12 - k * (hh - 40) / 24
                d.rectangle((xs[b] + pw / 2, yy - 5, xs[b + 1] - pw / 2, yy), fill=(190, 130, 82))
    for i, x in enumerate(xs):
        k = out(prog(t, 0.1 + i * 0.13, 0.5 + i * 0.13))
        if k > 0:
            d.rectangle((x - pw / 2, gy - hh * k, x + pw / 2, gy), fill=wood)
    if t > 1.0:  # viga
        k = ease(prog(t, 1.0, 1.4))
        d.rectangle((x0 - 10, gy - hh - 14, x0 - 10 + (x1 - x0 + 20) * k, gy - hh + 6), fill=wood)
    # cotas
    if t > 1.9:
        k = ease(prog(t, 1.9, 2.3))
        yy = gy + 70
        col = tuple(int(c * k + 26 * (1 - k)) for c in ACC)
        for i in range(7):
            d.line((xs[i], yy - 18, xs[i], yy + 18), fill=col, width=3)
        d.line((xs[0], yy, xs[-1], yy), fill=col, width=3)
        lbl = font(30, "SemiBold", False)
        for i in range(6):
            d.text(((xs[i] + xs[i + 1]) / 2, yy + 34), "3'-7¼\"", font=lbl, fill=col, anchor="mm")
    # cartão φ
    if t > 2.2:
        k = ease(prog(t, 2.2, 2.6))
        f1, f2 = font(64, "Black"), font(34, "Medium", False)
        c = Image.new("RGBA", (900, 270))
        cd = ImageDraw.Draw(c)
        cd.rounded_rectangle((0, 0, 899, 269), 28, fill=(40, 36, 32, 255), outline=(70, 62, 54), width=2)
        cd.text((40, 34), "bay : post ≈ φ⁴", font=f1, fill=ACC)
        cd.text((40, 130), "golden ratio (6.86 ≈ 6.85)", font=f2, fill=INK)
        cd.text((40, 182), "clear bay 37¾\"  ·  slat warp limit 48\"", font=f2, fill=MUTED)
        paste(im, c, (90, 360 + (1 - k) * 30), k)
    tag(im, "design check", 40, 268)
    caption(im, "Post spacing: golden-ratio bays, kept under the slat's warp limit.", t, 0.25, size=52)
    return im


def s_wind(t):
    """0:12–0:16 vento no poste + barras de tensão."""
    im = canvas((26, 24, 22))
    d = ImageDraw.Draw(im)
    gy = 860
    d.line((40, gy, W - 40, gy), fill=(120, 108, 96), width=4)
    d.rectangle((640, gy - 470, 700, gy), fill=(214, 150, 96))
    d.rectangle((630, gy, 710, gy + 60), fill=(150, 150, 140))
    d.rectangle((640, gy, 700, gy + 60), fill=(200, 205, 160))
    for i, yy in enumerate((440, 540, 640, 740)):
        ph = (t * 1.6 + i * 0.27) % 1.0
        x_end = 600
        x_start = 120 + ph * 160
        a = int(255 * min(1, (1 - ph) * 2.5, ph * 4 + 0.2))
        col = (140, 190, 230, a)
        lay = Image.new("RGBA", (W, H))
        arrow(ImageDraw.Draw(lay), x_start, yy, x_end - (1 - ph) * 80, yy, col, 10, 34)
        im.alpha_composite(lay)
    d.text((120, 380), "WIND", font=font(36, "Black"), fill=(140, 190, 230))
    # barras
    rows = [("4x4 core", 1740, WARN, "too close to the limit"),
            ("4x6 core", 706, GOOD, "✓ chosen"),
            ("6x6 core", 449, MUTED, "more than needed")]
    d.text((70, 950), "Bending stress in the post core", font=font(46, "Bold"), fill=INK)
    for i, (lbl, v, col, note) in enumerate(rows):
        y = 1030 + i * 104
        k = out(prog(t, 0.4 + i * 0.35, 1.1 + i * 0.35))
        d.text((70, y + 10), lbl, font=font(34, "SemiBold", False), fill=INK)
        bw = 560 * v / 1740 * k
        d.rounded_rectangle((300, y, 300 + max(bw, 4), y + 56), 12, fill=col)
        if k > 0.9:
            d.text((310 + bw + 6, y + 28), f"~{v:,} psi", font=font(32, "Bold", False), fill=col, anchor="lm")
            d.text((300, y + 64), note, font=font(26, "Medium", False), fill=col)
    tag(im, "design check", 40, 268)
    caption(im, "Wind load design check: a 4x4 core is too close to the limit, so we chose 4x6.", t, 1.6, cy=1480, size=48)
    return im


def s_footing(t):
    """0:16–0:20 corte da fundação (prancha rev9 A-2, detalhe 1)."""
    im = canvas((26, 24, 22))
    box = (505, 420, 790, 1000)
    s = 1010 / (box[3] - box[1])
    dr = sheet_crop("rev9-A-2", box)
    dr = sized(dr, h=1010)
    X0, Y0 = 60, 285
    z = 1.0 + 0.04 * prog(t, 0, 4)
    card(im, dr if z == 1 else dr.resize((round(dr.width * z), round(dr.height * z)), Image.BILINEAR), X0, Y0, r=20)
    d = ImageDraw.Draw(im)

    def P(x, y):
        return X0 + (x - box[0]) * s * z, Y0 + (y - box[1]) * s * z

    chips = [("concrete collar", (690, 582), 0.3), ('36" deep', (600, 740), 0.8),
             ('6" gravel', (690, 915), 1.3), ('16" footing', (700, 975), 1.8)]
    cx = 690
    ys = [470, 760, 1010, 1180]
    for (txt, pt, t0), cy in zip(chips, ys):
        k = out(prog(t, t0, t0 + 0.35))
        if k <= 0:
            continue
        p = pill(txt, 40, (24, 18, 12), ACC + (255,), "Bold", 24, 14)
        px, py = P(*pt)
        lay = Image.new("RGBA", (W, H))
        ld = ImageDraw.Draw(lay)
        ld.line((px, py, cx, cy + p.height / 2), fill=ACC + (255,), width=5)
        ld.ellipse((px - 11, py - 11, px + 11, py + 11), fill=ACC + (255,))
        im.alpha_composite(Image.blend(Image.new("RGBA", (W, H)), lay, k))
        paste(im, p, (cx + (1 - k) * 40, cy), k)
    caption(im, 'Foundation: 36" deep, 16" footing, 6" gravel, concrete collar.', t, 2.2, size=52)
    return im


def s_recs(t):
    """0:20–0:23 recomendações, uma por vez."""
    im = blurred_bg("3d-A-top.png", 0.7).copy()
    items = [("Treated pine below grade", "ground-contact core, set in concrete"),
             ("Planed lumber", "S4S on all four sides, so everything lines up"),
             ("Hidden-head screws", "coated trim-head screws, no visible fasteners")]
    for i, (a, b) in enumerate(items):
        k = out(prog(t, 0.15 + i * 0.7, 0.55 + i * 0.7))
        if k <= 0:
            continue
        c = Image.new("RGBA", (940, 230))
        cd = ImageDraw.Draw(c)
        cd.rounded_rectangle((0, 0, 939, 229), 32, fill=(20, 17, 14, 235), outline=(80, 68, 56), width=2)
        cd.ellipse((40, 60, 150, 170), fill=ACC)
        cd.text((95, 115), str(i + 1), font=font(60, "Black"), fill=(24, 18, 12), anchor="mm")
        cd.text((185, 52), a, font=font(54, "Bold"), fill=INK)
        tb = text_block(b, 32, "Medium", MUTED, 700, 1.2, "left")
        c.alpha_composite(tb, (187, 128))
        paste(im, c, (70 - (1 - k) * 60, 470 + i * 290), k)
    return im


VERS = ["v1", "wrap", "7 posts", "pergola", "top", "A / B"]


def progress(im, idx, frac):
    """Barra 'v1 → final' no topo da seção 3 (logo abaixo da faixa de UI)."""
    d = ImageDraw.Draw(im)
    x0, x1, y = 120, 960, 300
    d.rounded_rectangle((x0, y - 5, x1, y + 5), 5, fill=(70, 62, 54))
    p = (idx + frac) / (len(VERS) - 1)
    d.rounded_rectangle((x0, y - 5, x0 + (x1 - x0) * clamp(p), y + 5), 5, fill=ACC)
    for i, v in enumerate(VERS):
        x = x0 + (x1 - x0) * i / (len(VERS) - 1)
        on = i <= idx
        d.ellipse((x - 14, y - 14, x + 14, y + 14), fill=ACC if on else (70, 62, 54))
        d.text((x, y + 40), v, font=font(26, "SemiBold", False), fill=INK if i == idx else MUTED, anchor="mm")


def s_v1(t):
    """0:23–0:27 prancha antiga + carimbo CHANGED."""
    im = canvas((26, 24, 22))
    sh = sized(src("rev7-A-1.png"), 1000)
    card(im, sh, 40, 520, r=12)
    ImageDraw.Draw(im).text((40, 430), "v1 drawings", font=font(40, "Bold"), fill=MUTED)
    if t > 1.0:
        k = out(prog(t, 1.0, 1.25))
        st = Image.new("RGBA", (560, 170))
        sd = ImageDraw.Draw(st)
        sd.rounded_rectangle((6, 6, 553, 163), 18, outline=(214, 52, 40, 255), width=12)
        sd.text((280, 88), "CHANGED", font=font(108, "Black"), fill=(214, 52, 40, 255), anchor="mm")
        sc = 1.6 - 0.6 * k
        st = st.resize((round(560 * sc), round(170 * sc)), Image.LANCZOS).rotate(12, Image.BICUBIC, expand=True)
        paste(im, st, (540 - st.width / 2, 840 - st.height / 2), 0.92 * k)
    progress(im, 0, prog(t, 0, 4))
    caption(im, "v1: composite base → owner worried it would warp. Switched to all wood.", t, 1.5, size=50)
    return im


def s_wrap(t):
    """0:27–0:31 poste revestido: núcleo + 2x6 + serrilhado (rev9 A-3, det. 2a)."""
    im = canvas((26, 24, 22))
    dr = sized(sheet_crop("rev9-A-3", (90, 240, 700, 745)), 860)
    z = 1.0 + 0.05 * prog(t, 0, 4)
    dz = dr.resize((round(dr.width * z), round(dr.height * z)), Image.BILINEAR)
    card(im, dz, 110 - (dz.width - dr.width) / 2, 400, r=18)
    d = ImageDraw.Draw(im)
    leg = [((200, 207, 160), "treated-pine core"), ((228, 168, 112), "cedar wrap: 2x6 faces + notched sides")]
    for i, (c, txt) in enumerate(leg):
        k = ease(prog(t, 0.6 + i * 0.5, 0.9 + i * 0.5))
        if k <= 0:
            continue
        lay = Image.new("RGBA", (W, 70))
        ld = ImageDraw.Draw(lay)
        ld.rounded_rectangle((0, 8, 54, 62), 10, fill=c)
        ld.text((76, 35), txt, font=font(36, "SemiBold", False), fill=INK, anchor="lm")
        paste(im, lay, (110, 1160 + i * 76), k)
    progress(im, 1, prog(t, 0, 4))
    caption(im, "Owner's idea: wrap the post, notch the sides. We detailed it.", t, 1.4, cy=1500, size=50)
    return im


def s_posts(t):
    """0:31–0:35 10 postes vs 7."""
    im = canvas((26, 24, 22))
    d = ImageDraw.Draw(im)
    box = (80, 150, 1070, 680)
    a = sized(sheet_crop("rev7-10-A-1", box), 840)
    b = sized(sheet_crop("rev7-A-1", box), 840)
    ka = ease(prog(t, 0.0, 0.3))
    kb = ease(prog(t, 0.6, 0.9))
    d.text((120, 385), "10 posts", font=font(46, "Bold"), fill=INK)
    card(im, a, 120, 445, ka)
    if t > 1.6:
        k = ease(prog(t, 1.6, 1.9))
        dim = Image.new("RGBA", (a.width, a.height), (26, 24, 22, int(150 * k)))
        paste(im, dim, (120, 445))
    if kb > 0:
        d.text((120, 905), "7 posts", font=font(46, "Bold"), fill=INK)
        card(im, b, 120, 965, kb)
    if t > 1.6:
        k = out(prog(t, 1.6, 1.9))
        p = pill("✓ kept", 40, (16, 30, 16), GOOD + (255,), "Bold", 24, 12)
        paste(im, p, (330, 900), k)
    progress(im, 2, prog(t, 0, 4))
    caption(im, "10 posts vs 7: kept 7.", t, 1.9, cy=1495, size=56)
    return im


def s_pergola(t):
    """0:35–0:39 nova referência (IA) + prancha rev9."""
    im = canvas((26, 24, 22))
    r = sized(ref("referencia-rev8-6-postes.webp"), 900)
    sh = sized(src("rev9-A-1.png"), 900)
    k1 = ease(prog(t, 0, 0.3))
    card(im, r, 90, 360, k1)
    tag(im, "new AI reference", 110, 360 + r.height - 56, k1)
    k2 = out(prog(t, 0.5, 1.0))
    card(im, sh, 90 + (1 - k2) * 300, 990, k2, r=12)
    progress(im, 3, prog(t, 0, 4))
    caption(im, "New reference: pergola top. Redesigned with 24 slats per bay.", t, 1.1, cy=960, size=50)
    return im


def s_top(t):
    """0:39–0:43 detalhe do topo antes/depois."""
    im = canvas((26, 24, 22))
    d = ImageDraw.Draw(im)
    a = sized(sheet_crop("rev7-A-1", (1320, 105, 1560, 335)), 440)
    b = sized(sheet_crop("rev9-A-2", (1030, 40, 1300, 460)), h=640)
    if b.width > 440:
        b = sized(b, 440)
    ka = ease(prog(t, 0, 0.3))
    kb = out(prog(t, 0.9, 1.3))
    d.text((70, 400), "BEFORE", font=font(44, "Black"), fill=WARN)
    d.text((70, 455), "end cap on top", font=font(30, "Medium", False), fill=MUTED)
    card(im, a, 70, 520, ka)
    if kb > 0:
        lay = Image.new("RGBA", (W, H))
        ld = ImageDraw.Draw(lay)
        ld.text((570, 400), "AFTER", font=font(44, "Black"), fill=GOOD)
        ld.text((570, 455), "no cap, beam bolted\nstraight to the core", font=font(30, "Medium", False), fill=MUTED,
                spacing=6)
        paste(im, lay, (0, 0), kb)
        card(im, b, 570, 560 + (1 - kb) * 40, kb)
    progress(im, 4, prog(t, 0, 4))
    caption(im, "Top detail: no end cap, beam bolted straight to the core.", t, 1.6, size=52)
    return im


def s_options(t, T=3.0):
    """0:43–0:46 cedro vs pinho tratado (renders 3D), cortina divisória."""
    im = canvas()
    A = cover(src("3d-A-overall.png"), W, H)
    B = cover(src("3d-B-overall.png"), W, H)
    im.alpha_composite(A)
    split = W - (W / 2) * out(prog(t, 0.3, 1.1))
    if split < W:
        im.alpha_composite(B.crop((round(split), 0, W, H)), (round(split), 0))
        ImageDraw.Draw(im).rectangle((split - 3, 0, split + 3, H), fill=INK)
    pa = pill("A · Cedar", 38, INK, (14, 12, 10, 210), "Bold")
    paste(im, pa, (40, 380))
    kb = ease(prog(t, 0.8, 1.1))
    pb = pill("B · Treated pine", 38, INK, (14, 12, 10, 210), "Bold")
    paste(im, pb, (W - 40 - pb.width, 380), kb)
    progress(im, 5, prog(t, 0, T))
    caption(im, "Two options: cedar or treated pine.", t, 1.0, size=58)
    return im


def s_final(t):
    """0:46–0:50 proposta (sem preços) + pranchas rev9 deslizando."""
    im = canvas((26, 24, 22))
    p = sized(src("proposta-p1.png").crop((0, 0, 1632, 1500)), 660)
    k = ease(prog(t, 0, 0.35))
    card(im, p, 70, 330, k, rot=3, r=10)
    for i, n in enumerate(["rev9-A-1", "rev9-A-2", "rev9-A-3"]):
        ks = out(prog(t, 0.5 + i * 0.45, 1.0 + i * 0.45))
        if ks <= 0:
            continue
        sh = sized(src(f"{n}.png"), 720)
        card(im, sh, 300 + (1 - ks) * 700 + i * 20, 760 + i * 130, 1.0, rot=-2 + i * 1.5, r=8)
    caption(im, "Final: proposal + shop drawings.", t, 0.3, cy=1470, size=58)
    return im


PHONE_SEQ = [  # (início, imagem, toque em (x,y) no screenshot 780x1560)
    (0.0, "phone-1-overall.png", None),
    (0.55, None, (302, 1191)),  # toque "Top detail"
    (0.8, "phone-2-top.png", None),
    (1.5, None, (553, 195)),  # toque "B · Treated pine"
    (1.75, "phone-3-top-B.png", None),
    (2.4, None, (166, 1191)),  # toque "Overall"
]


def s_phone(t):
    """0:50–0:54 celular com o visualizador 3D."""
    im = blurred_bg("phone-3-top-B.png", 0.75).copy()
    sw = 540
    sh = round(sw * 1560 / 780)
    sx, sy = (W - sw) / 2, 285
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((sx - 22, sy - 22, sx + sw + 22, sy + sh + 22), 70, fill=(18, 18, 20))
    shot = "phone-1-overall.png"
    for t0, name, _ in PHONE_SEQ:
        if name and t >= t0:
            shot = name
    if t >= 2.65:
        i = min(23, int((t - 2.65) / 1.35 * 24))
        shot = f"phone-spin-{i:02d}.png"
    scr = sized(src(shot), sw)
    m = Image.new("L", scr.size)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, sw - 1, sh - 1), 52, fill=255)
    scr = scr.copy()
    scr.putalpha(m)
    paste(im, scr, (sx, sy))
    for t0, _, pt in PHONE_SEQ:
        if pt and t0 <= t < t0 + 0.4:
            k = prog(t, t0, t0 + 0.4)
            x, y = sx + pt[0] * sw / 780, sy + pt[1] * sw / 780
            rr = 26 + 30 * k
            lay = Image.new("RGBA", (W, H))
            ImageDraw.Draw(lay).ellipse((x - rr, y - rr, x + rr, y + rr), fill=(255, 255, 255, int(150 * (1 - k))),
                                        outline=(255, 255, 255, int(230 * (1 - k))), width=4)
            im.alpha_composite(lay)
    caption(im, "Then the owner explored it in 3D, on their phone.", t, 0.2, cy=1480, size=50)
    return im


def s_end(t):
    """0:54–1:00 imagem de referência → marca."""
    if t < 3.0:
        im = blurred_bg("referencia-rev8-6-postes.webp", 0.5).copy()
        pic = ref("referencia-rev8-6-postes.webp")
        z = 1.0 + 0.08 * (t / 3)
        w = round(1080 * z)
        h = round(pic.height * w / pic.width)
        paste(im, pic.resize((w, h), Image.BILINEAR), ((W - w) / 2, 430 - (h - 720) / 2))
        tag(im, "AI reference image", 36, 368)
        caption(im, "From AI picture to a build-ready project.", t, 0.2, cy=1330, size=64)
        return im
    k = ease(prog(t, 3.0, 3.5))
    im = canvas((16, 14, 12))
    lay = Image.new("RGBA", (W, H))
    ld = ImageDraw.Draw(lay)
    ld.text((W / 2, 800), "REAL SPECIAL", font=font(104, "Black"), fill=INK, anchor="mm")
    ld.text((W / 2, 915), "PROJECTS", font=font(104, "Black"), fill=INK, anchor="mm")
    ld.line((W / 2 - 120, 1010, W / 2 + 120, 1010), fill=ACC, width=6)
    ld.text((W / 2, 1075), "When AI meets the real world", font=ImageFont.truetype(f"{FD}Inter-MediumItalic.otf", 46),
            fill=MUTED, anchor="mm")
    paste(im, lay, (0, (1 - k) * 30), k)
    k2 = out(prog(t, 3.6, 4.0))
    p = pill('Lake Norman area  ·  DM "DESIGN"', 42, (24, 18, 12), ACC + (255,), "Bold", 34, 18)
    paste(im, p, ((W - p.width) / 2, 1200), k2)
    return im


SCENES = [  # (início, fim, função)
    (0, 4, s_chat), (4, 8, s_concept), (8, 12, s_spacing), (12, 16, s_wind), (16, 20, s_footing),
    (20, 23, s_recs), (23, 27, s_v1), (27, 31, s_wrap), (31, 35, s_posts), (35, 39, s_pergola),
    (39, 43, s_top), (43, 46, s_options), (46, 50, s_final), (50, 54, s_phone), (54, 60, s_end),
]
XF = 0.2  # transição cruzada (s)


def frame(t):
    for i, (a, b, f) in enumerate(SCENES):
        if a <= t < b or (i == len(SCENES) - 1 and t >= a):
            im = f(t - a)
            if i > 0 and t - a < XF:
                pa, pb, pf = SCENES[i - 1]
                prev = pf(t - pa)
                im = Image.blend(prev, im, ease((t - a) / XF))
            return im.convert("RGB")
    raise ValueError(t)


def capa():
    im = blurred_bg("conceito-000.jpg", 0.35).copy()
    pic = sized(ref("conceito-000.jpg"), 1080)
    paste(im, pic, (0, 380))
    paste(im, Image.new("RGBA", (W, H), (10, 9, 8, 120)), (0, 0))
    t1 = text_block("Made it with AI.", 116, "Black", INK, 980)
    t2 = text_block("Who builds it?", 116, "Black", ACC, 980)
    paste(im, t1, ((W - t1.width) / 2, 760))
    paste(im, t2, ((W - t2.width) / 2, 900))
    f = font(40, "Bold")
    ImageDraw.Draw(im).text((W / 2, 1110), "REAL SPECIAL PROJECTS", font=f, fill=INK, anchor="mm")
    return im.convert("RGB")


PREVIA = [(3.4, "hook"), (14.6, "wind check"), (19.5, "foundation"), (25.6, "v1 changed"),
          (52.2, "3D on phone"), (59.0, "end card")]


def previa():
    out_ = os.path.join(AQUI, "build", "previa")
    os.makedirs(out_, exist_ok=True)
    thumbs = []
    for i, (t, nome) in enumerate(PREVIA, 1):
        im = frame(t)
        p = os.path.join(out_, f"quadro-{i}-{int(t // 60)}m{t % 60:04.1f}s.png")
        im.save(p)
        thumbs.append((im, f"{i} · {int(t // 60)}:{t % 60:04.1f} · {nome}"))
        print(p)
    tw, th = 360, 640
    sheet = Image.new("RGB", (tw * 3 + 80, (th + 70) * 2 + 40), (40, 38, 36))
    d = ImageDraw.Draw(sheet)
    for i, (im, lbl) in enumerate(thumbs):
        x, y = 20 + (i % 3) * (tw + 20), 20 + (i // 3) * (th + 70)
        sheet.paste(im.resize((tw, th), Image.LANCZOS), (x, y))
        # faixas de UI do Reels (topo 250 / base 350) em vermelho translúcido para conferir a área segura
        ov = Image.new("RGBA", (tw, th))
        od = ImageDraw.Draw(ov)
        od.rectangle((0, 0, tw, 250 * th / H), fill=(255, 0, 0, 50))
        od.rectangle((0, th - 350 * th / H, tw, th), fill=(255, 0, 0, 50))
        sheet.paste(ov, (x, y), ov)
        d.text((x, y + th + 12), lbl, font=font(28, "SemiBold", False), fill=INK)
    p = os.path.join(out_, "previa-6-quadros.png")
    sheet.save(p)
    capa().save(os.path.join(out_, "capa.png"))
    print(p)


def video():
    dst = os.path.join(AQUI, "reel-made-it-with-ai.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "18",
           "-pix_fmt", "yuv420p", "-profile:v", "high", "-movflags", "+faststart", dst]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = int(DUR * FPS)
    for i in range(n):
        pr.stdin.write(frame(i / FPS).tobytes())
        if i % 150 == 0:
            print(f"{i}/{n}", flush=True)
    pr.stdin.close()
    if pr.wait():
        sys.exit("ffmpeg falhou")
    capa().save(os.path.join(AQUI, "reel-capa.jpg"), quality=92)
    print(dst)


if __name__ == "__main__":
    if not os.path.exists(os.path.join(SRC, "phone-spin-23.png")):
        sys.exit("rode antes: node marketing/capturar_fontes.js")
    previa() if "--previa" in sys.argv else video()
