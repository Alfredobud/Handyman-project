#!/usr/bin/env python3
"""Tabela de horas por etapa de instalação (opções A e B), a partir de orcamento*/orcamento.json.
Uso: python3 gerar_tempo_etapas.py  -> tempo-por-etapa.md"""
import json
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
OPC = [("orcamento", "A — 10 postes"), ("orcamento-7-postes", "B — 7 postes")]
ETAPAS = [
    ("Oficina", "Pré-corte (antes da obra)", lambda t: t.startswith("oficina")),
    ("1", "Furos (marcação + escavação mecanizada + retirar/devolver equipamento)",
     lambda t: t in ("locacao", "obra_escavacao_mecanizada", "obra_transporte_equipamento")),
    ("2", "Postes (brita, prumo, escora, concreto, colar)", lambda t: t == "obra_assentar_poste"),
    ("3", "Nivelar topos", lambda t: t == "obra_nivelar_topo"),
    ("4", "Serrilhados (lado do vizinho)", lambda t: t == "obra_instalar_serrilhado"),
    ("5", "Ripas", lambda t: t == "obra_instalar_ripa"),
    ("6", "Fechamento frontal (faces 2x6)", lambda t: t == "obra_instalar_face"),
    ("7", "Fechamento lateral (postes de ponta)", lambda t: t == "obra_instalar_lateral"),
    ("8", "Tábuas de topo", lambda t: t == "obra_instalar_tabua_topo"),
    ("9", "Fechamento das pontas", lambda t: t == "obra_instalar_fechamento"),
    ("10", "Caibros do pergolado", lambda t: t == "obra_instalar_caibro"),
    ("Outros", "Compras/transporte e limpeza", lambda t: True),
]


def main():
    R = {d: json.load(open(os.path.join(AQUI, d, "orcamento.json"), encoding="utf-8")) for d, _ in OPC}
    taxa = R[OPC[0][0]]["parametros"]["taxa_hora_usd"]
    usadas = {d: set() for d in R}
    linhas = []
    for cod, nome, f in ETAPAS:
        hs, det = {}, {}
        for d, r in R.items():
            ms = [m for i, m in enumerate(r["mao_de_obra"]) if i not in usadas[d] and f(str(m["tarefa"]))]
            usadas[d] |= {i for i, m in enumerate(r["mao_de_obra"]) if m in ms}
            hs[d] = sum(m["horas"] for m in ms)
            det[d] = ms
        linhas.append((cod, nome, hs, det))
    tot = {d: sum(l[2][d] for l in linhas) for d in R}
    for d in R:
        assert abs(tot[d] - R[d]["totais"]["horas"]) < 0.05
    of = {d: linhas[0][2][d] for d in R}
    a, b = OPC[0][0], OPC[1][0]
    out = ["# Tempo de mão de obra por etapa — Kitchen Privacy Screen", "",
           f"Horas do orçamento atual, a ${taxa:g}/h. Dia = 8 h. Paisagismo é extra e não está incluído.", "",
           f"| Etapa | Descrição | {OPC[0][1]} (h) | ($) | {OPC[1][1]} (h) | ($) |", "|---|---|---:|---:|---:|---:|"]
    for cod, nome, hs, _ in linhas:
        out.append(f"| {cod} | {nome} | {hs[a]:.1f} | ${hs[a] * taxa:,.0f} | {hs[b]:.1f} | ${hs[b] * taxa:,.0f} |")
    ob = {d: tot[d] - of[d] for d in R}
    out += [f"| | **Subtotal oficina** | **{of[a]:.1f}** | **${of[a] * taxa:,.0f}** | **{of[b]:.1f}** | **${of[b] * taxa:,.0f}** |",
            f"| | **Subtotal obra** | **{ob[a]:.1f}** | **${ob[a] * taxa:,.0f}** | **{ob[b]:.1f}** | **${ob[b] * taxa:,.0f}** |",
            f"| | **TOTAL** | **{tot[a]:.1f}** | **${tot[a] * taxa:,.0f}** | **{tot[b]:.1f}** | **${tot[b] * taxa:,.0f}** |",
            f"| | Dias de 8 h (oficina / obra) | {of[a] / 8:.1f} / {ob[a] / 8:.1f} | | {of[b] / 8:.1f} / {ob[b] / 8:.1f} | |", "",
            "## Como cada etapa foi calculada", "",
            "| Etapa | Tarefa | Unid. | Qtd A | Qtd B | h/unid. |", "|---|---|---|---:|---:|---:|"]
    for cod, _, _, det in linhas:
        tar = {}
        for d in R:
            for m in det[d]:
                tar.setdefault(m["tarefa"], {"desc": m.get("descricao", m["tarefa"]), "un": m["unidade"], "h": m["h_unit"]})[d] = m["qtd"]
        for v in tar.values():
            out.append(f"| {cod} | {v['desc']} | {v['un']} | {v.get(a, 0):g} | {v.get(b, 0):g} | {v['h']:g} |")
    out += ["", "_Etapa 2: cura de 48 h do concreto antes das etapas 3–10 (espera, não cobrada). Taxas em "
            "`.claude/skills/orcamento-madeira/references/produtividade.csv`._"]
    open(os.path.join(AQUI, "tempo-por-etapa.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\n".join(out[4:22]))


if __name__ == "__main__":
    main()
