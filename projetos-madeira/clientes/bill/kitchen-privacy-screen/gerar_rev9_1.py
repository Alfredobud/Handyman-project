#!/usr/bin/env python3
"""Rev 9.1 — Opção A (cedro) da rev 9 + stain/selador em TODO o cedro exposto, dos dois lados,
incluindo o topo do pergolado. Base: orcamento-rev9-1/rev9-cedro-4x6-base.json (spec da rev 9, commit 08a716d).
Produto: Ready Seal Natural Cedar (óleo, semi-transparente). Aplicação: pistola na oficina, 4 faces de
cada peça antes da montagem (protege também as faces ocultas), + retoque na obra (cortes, entalhes, parafusos)."""
import json, os, subprocess, sys, math
AQUI = os.path.dirname(os.path.abspath(__file__))
d = AQUI
while not os.path.isdir(os.path.join(d, ".claude", "skills")):
    d = os.path.dirname(d)
ORC = os.path.join(d, ".claude", "skills", "orcamento-madeira", "scripts", "orcamento.py")

REAL = {"cedro_5_4x6": (1.0, 5.5), "cedro_2x6": (1.5, 5.5), "cedro_2x2": (1.5, 1.5), "cedro_2x8": (1.5, 7.25)}
COBERTURA = 125.0      # sqft/gal em cedro (Ready Seal; conservador)
s = json.load(open(os.path.join(AQUI, "orcamento-rev9-1", "rev9-cedro-4x6-base.json"), encoding="utf-8"))
area = 0.0
det = []
for c in s["componentes"]:
    if c["tipo"] == "pecas" and c["material"] in REAL:
        t, w = REAL[c["material"]]
        a = c["qtd"] * (2 * (t + w) * c["comprimento_in"] + 2 * t * w) / 144
        if "serrilhad" in c["nome"]:
            a *= 1.10                                   # faces dos encaixes do serrilhado
        if "nuvem" in c["nome"]:
            a *= 1.05                                   # recorte da ponta
        det.append((c["nome"], round(a, 1)))
        area += a
area = math.ceil(area)
gal = area / COBERTURA
s["revisao"] = "9.1"
s["data"] = "2026-11-10"
s["projeto"] += " — rev 9.1 com stain/selador"
s["componentes"] += [
    {"tipo": "item", "nome": f"Stain/selador Ready Seal Natural Cedar — 5 gal ({area} sqft de cedro, 4 faces)", "material": "stain_readyseal_natural_cedar_5gal", "qtd": 1,
     "tarefa": "oficina_pintura_pistola", "tarefa_qtd": area},
    {"tipo": "item", "nome": "Stain/selador Ready Seal Natural Cedar — 1 gal (retoques + reserva)", "material": "stain_readyseal_natural_cedar_1gal", "qtd": 1},
    {"tipo": "item", "nome": "Suprimentos de acabamento", "material": "acabamento_suprimentos", "qtd": 1},
]
s["tarefas_extra"] += [
    {"descricao": "Oficina: montar cavaletes/racks de secagem, virar peças, limpar pistola", "horas": 2.0},
    {"descricao": "Obra: retoque de stain em cortes, entalhes, pontas e cabeças de parafuso", "horas": 2.0},
]
s["premissas"] = s.get("premissas", []) + [
    f"Stain: Ready Seal Natural Cedar, 1 demão saturada (úmido sobre úmido) nas 4 faces de cada peça de cedro, na oficina; área {area} sqft ≈ {gal:.1f} gal a {COBERTURA:.0f} sqft/gal.",
    "Núcleo PT não recebe stain (fica oculto); manutenção: reaplicar a cada 2–3 anos.",
]
pasta = os.path.join(AQUI, "orcamento-rev9-1", "opcao-a-cedro-stain")
os.makedirs(pasta, exist_ok=True)
json.dump(s, open(os.path.join(pasta, "spec.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
subprocess.run([sys.executable, ORC, os.path.join(pasta, "spec.json"), "--saida", pasta], check=True, stdout=subprocess.DEVNULL)
r = json.load(open(os.path.join(pasta, "orcamento.json")))
for n, a in det:
    print(f"  {a:7.1f} sqft  {n}")
print(f"área total {area} sqft, {gal:.2f} gal")
print(json.dumps(r["totais"], indent=1))
