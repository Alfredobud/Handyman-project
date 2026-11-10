#!/usr/bin/env python3
"""Calcula orçamento de projeto em madeira a partir de um spec JSON.

Uso:
    python3 orcamento.py spec.json --saida pasta/orcamento

Gera orcamento.md, orcamento.json e (se openpyxl estiver instalado) orcamento.xlsx.
Formato do spec: ver references/formato-spec.md.
"""
import argparse
import csv
import json
import math
import os
import sys
from collections import defaultdict

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF_DIR = os.path.join(SKILL_DIR, "references")

PARAMS_PADRAO = {
    "taxa_hora_usd": 65.0,
    "perda": 0.05,            # sobra extra sobre o resultado já otimizado (peças com defeito, erro de corte)
    "kerf_in": 0.125,         # espessura da serra
    "markup_material": 0.15,  # margem sobre material
    "imposto_material": 0.0,  # sales tax (ex.: 0.07)
    "contingencia": 0.10,     # aplicada em material e mão de obra
    "comprimento_max_ft": None,  # limita tábuas compradas (ex.: 8 para transporte em carro)
    "taxa_fixa_usd": 0.0,     # taxa fixa do serviço (ex.: no lugar do markup de material)
    "taxa_fixa_descricao": "Taxa de serviço",
}


# ---------------------------------------------------------------- catálogos
def carregar_precos(caminhos):
    """Retorna {id: {"descricao", "unidade", "comprimentos": {ft: preco}, "preco": p, "fonte", "data"}}.
    Arquivos posteriores sobrescrevem os anteriores (preço do projeto > catálogo base)."""
    cat = {}
    for caminho in caminhos:
        if not caminho or not os.path.exists(caminho):
            continue
        with open(caminho, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                mid = row["id"].strip()
                ent = cat.setdefault(mid, {"comprimentos": {}, "preco": None, "fontes": {}})
                ent["descricao"] = row.get("descricao", mid)
                ent["unidade"] = row.get("unidade", "un")
                ent["fonte"] = row.get("fonte", "")
                ent["data"] = row.get("data", "")
                preco = float(row["preco_usd"])
                comp = (row.get("comprimento_ft") or "").strip()
                if comp:
                    ent["comprimentos"][float(comp)] = preco
                    ent["fontes"][float(comp)] = row.get("fonte", "")
                else:
                    ent["preco"] = preco
    return cat


def carregar_produtividade(caminho):
    prod = {}
    with open(caminho, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            prod[row["tarefa"]] = {
                "unidade": row["unidade"],
                "horas": float(row["horas_por_unidade"]),
                "descricao": row["descricao"],
            }
    return prod


# ---------------------------------------------------------------- otimização de cortes
def _ffd(cortes, comprimentos_in, kerf, reducao_in=None):
    """First-fit decreasing (best fit). cortes: lista de (consumo_in, rotulo).
    comprimentos_in: comprimentos de estoque disponíveis. Abre tábua no maior comprimento
    e no final reduz cada tábua ao menor comprimento que ainda comporta os cortes."""
    maior = max(comprimentos_in)
    tabuas = []  # {"usado": x, "cortes": [...]}
    for consumo, rotulo in sorted(cortes, key=lambda c: -c[0]):
        precisa = consumo + kerf
        melhor = None
        for t in tabuas:
            livre = maior - t["usado"]
            if livre + 1e-9 >= precisa and (melhor is None or livre < maior - melhor["usado"]):
                melhor = t
        if melhor is None:
            melhor = {"usado": 0.0, "cortes": []}
            tabuas.append(melhor)
        melhor["usado"] += precisa
        melhor["cortes"].append((consumo, rotulo))
    for t in tabuas:
        # o último corte não precisa de kerf
        necessario = t["usado"] - kerf
        t["comprimento_in"] = min(c for c in (reducao_in or comprimentos_in) if c + 1e-9 >= necessario)
    return tabuas


def otimizar(cortes, tabela_ft, kerf):
    """Testa estoque misto e cada comprimento isolado; retorna a opção mais barata."""
    comprimentos = {ft * 12: p for ft, p in tabela_ft.items()}
    opcoes = [list(comprimentos)] + [[c] for c in comprimentos]
    melhor, melhor_custo = None, None
    for disponiveis in opcoes:
        if max(c for c, _ in cortes) > max(disponiveis) + 1e-9:
            continue
        tabuas = _ffd(cortes, disponiveis, kerf, reducao_in=list(comprimentos))
        custo = sum(comprimentos[t["comprimento_in"]] for t in tabuas)
        if melhor_custo is None or custo < melhor_custo - 1e-9:
            melhor, melhor_custo = tabuas, custo
    return melhor


# ---------------------------------------------------------------- expansão dos componentes
def expandir(spec, avisos):
    """Converte componentes em: cortes lineares por material, itens unitários e tarefas."""
    cortes = defaultdict(list)       # material -> [(consumo_in, rotulo)]
    perdas = defaultdict(float)      # material -> perda (máxima entre componentes)
    tabuas_diretas = defaultdict(lambda: defaultdict(int))  # material -> {ft: qtd}
    itens = defaultdict(float)       # material -> qtd
    itens_nomes = defaultdict(list)  # material -> nomes dos componentes
    tarefas = defaultdict(float)     # tarefa -> qtd
    detalhes = []                    # linhas para relatório de cortes
    perda_padrao = spec["parametros"]["perda"]

    for comp in spec.get("componentes", []):
        tipo = comp["tipo"]
        nome = comp.get("nome", tipo)
        mat = comp.get("material")
        perda = comp.get("perda", perda_padrao)
        qtd_mo = None

        if tipo == "pecas":
            n = int(comp["qtd"])
            comprimento = float(comp["comprimento_in"])
            por_largura = int(comp.get("por_largura", 1))
            # consumo_in: comprimento de tábua realmente ocupado por grupo (ex.: pernas em ângulo encaixadas)
            consumo = float(comp.get("consumo_in", comprimento))
            grupos = math.ceil(n / por_largura)
            for i in range(grupos):
                cortes[mat].append((consumo, nome))
            perdas[mat] = max(perdas[mat], perda)
            extra = f" ({por_largura} por largura, {grupos} trechos)" if por_largura > 1 else ""
            if consumo != comprimento:
                extra += f" (consome {consumo:g}\" de tábua por trecho)"
            detalhes.append((nome, mat, n, comprimento, extra.strip()))
            qtd_mo = n

        elif tipo == "ripado":
            vaos = comp.get("vaos_in") or [float(comp["vao_in"])] * int(comp["n_vaos"])
            altura = float(comp["altura_in"])
            larg = float(comp["largura_peca_in"])
            lados = int(comp.get("lados", 1))
            if "espaco_min_in" in comp:
                # máximo de fiadas respeitando o espaço mínimo; o espaço real é redistribuído para preencher a altura
                esp_min = float(comp["espaco_min_in"])
                fiadas = int(math.floor((altura + esp_min) / (larg + esp_min) + 1e-9))
                esp_real = (altura - fiadas * larg) / (fiadas - 1) if fiadas > 1 else 0.0
                if "espaco_max_in" in comp and esp_real > float(comp["espaco_max_in"]) + 1e-9:
                    avisos.append(f"Ripado '{nome}': espaço real {esp_real:.2f}\" passa do máximo {comp['espaco_max_in']}\".")
            else:
                esp = float(comp["espaco_in"])
                fiadas = int(math.floor((altura + esp) / (larg + esp) + 1e-9))
                esp_real = esp
            n_total = 0
            por_vao = defaultdict(int)
            for v in vaos:
                n = fiadas * lados
                for _ in range(n):
                    cortes[mat].append((float(v), nome))
                n_total += n
                por_vao[float(v)] += 1
            for v, nv in por_vao.items():
                detalhes.append((nome, mat, nv * fiadas * lados, v, f"{nv} vão(s) x {fiadas} fiadas x {lados} lado(s)"))
            perdas[mat] = max(perdas[mat], perda)
            altura_real = fiadas * larg + (fiadas - 1) * esp_real
            comp["_calc"] = {"fiadas": fiadas, "espaco_real_in": round(esp_real, 2),
                             "altura_coberta_in": round(altura_real, 2), "pecas": n_total}
            qtd_mo = n_total

        elif tipo == "tabuas":
            tabuas_diretas[mat][float(comp["comprimento_ft"])] += int(comp["qtd"])
            qtd_mo = int(comp["qtd"])

        elif tipo == "sapata":
            n = int(comp["qtd"])
            d_ft = float(comp["diametro_in"]) / 12
            h_ft = float(comp["profundidade_in"]) / 12
            vol = math.pi * (d_ft / 2) ** 2 * h_ft * n
            desconto = float(comp.get("desconto_poste_in2", 0)) / 144 * h_ft * n  # volume ocupado pelo poste
            vol_liq = max(vol - desconto, 0) * (1 + comp.get("perda", 0.10))
            rend = float(comp.get("rendimento_cf", 0.60))
            sacos = math.ceil(vol_liq / rend)
            itens[mat or "concreto_80lb"] += sacos
            itens_nomes[mat or "concreto_80lb"].append(nome)
            comp["_calc"] = {"volume_cf": round(vol_liq, 2), "sacos": sacos}
            qtd_mo = n

        elif tipo == "item":
            itens[mat] += float(comp["qtd"])
            itens_nomes[mat].append(nome)
            qtd_mo = comp.get("qtd")

        else:
            avisos.append(f"Componente '{nome}': tipo desconhecido '{tipo}' — ignorado.")
            continue

        if comp.get("tarefa"):
            tarefas[comp["tarefa"]] += float(comp.get("tarefa_qtd", qtd_mo or 0))

    for t in spec.get("tarefas_extra", []):
        if "horas" in t:
            tarefas[("__horas__", t.get("descricao", "Horas avulsas"))] += float(t["horas"])
        else:
            tarefas[t["tarefa"]] += float(t.get("qtd", 1))

    return cortes, perdas, tabuas_diretas, itens, itens_nomes, tarefas, detalhes


# ---------------------------------------------------------------- cálculo principal
def calcular(spec, base_dir):
    p = dict(PARAMS_PADRAO)
    p.update(spec.get("parametros", {}))
    spec["parametros"] = p
    avisos = []

    caminhos = [os.path.join(REF_DIR, "precos.csv")]
    if spec.get("precos"):
        caminhos.append(os.path.join(base_dir, spec["precos"]))
    cat = carregar_precos(caminhos)
    prod = carregar_produtividade(os.path.join(REF_DIR, "produtividade.csv"))

    cortes, perdas, tabuas_diretas, itens, itens_nomes, tarefas, detalhes = expandir(spec, avisos)

    compra = []        # linhas da lista de compra
    plano_cortes = []  # tábua a tábua

    for mat, lista in cortes.items():
        ent = cat.get(mat)
        if not ent or not ent["comprimentos"]:
            avisos.append(f"Material '{mat}' sem preço por comprimento no catálogo — custo 0, adicione ao precos.csv.")
            total_in = sum(c for c, _ in lista)
            compra.append({"material": mat, "descricao": mat, "comprimento_ft": "", "qtd": 0,
                           "preco_unit": 0.0, "subtotal": 0.0, "fonte": "",
                           "obs": f"SEM PREÇO — {len(lista)} cortes, {total_in/12:.1f} ft lineares"})
            continue
        maior_in = max(ent["comprimentos"]) * 12
        longos = [c for c in lista if c[0] > maior_in + 1e-9]
        if longos:
            avisos.append(f"Material '{mat}': {len(longos)} corte(s) de até {max(c for c,_ in longos):g}\" maiores que a "
                          f"maior peça comercial ({maior_in:g}\") — precisa de emenda sobre apoio; dividir no spec.")
            lista = [c for c in lista if c[0] <= maior_in + 1e-9]
            if not lista:
                continue
        tabela = ent["comprimentos"]
        if p.get("comprimento_max_ft"):
            limitada = {ft: pr for ft, pr in tabela.items() if ft <= p["comprimento_max_ft"]}
            if limitada and max(c for c, _ in lista) <= max(limitada) * 12 + 1e-9:
                tabela = limitada
            else:
                avisos.append(f"Material '{mat}': limite de {p['comprimento_max_ft']}' ignorado (há corte maior ou não há tábua nesse tamanho).")
        tabuas = otimizar(lista, tabela, p["kerf_in"])
        cont = defaultdict(int)
        padroes = {}
        for t in tabuas:
            cont[t["comprimento_in"] / 12] += 1
            usado = sum(c for c, _ in t["cortes"])
            agrup = defaultdict(int)
            for c, r in t["cortes"]:
                agrup[(c, r)] += 1
            desc = " + ".join(f'{n}x {c:g}" {r}' for (c, r), n in agrup.items())
            chave = (t["comprimento_in"], desc)
            if chave not in padroes:
                padroes[chave] = {
                    "material": mat, "qtd_tabuas": 0, "comprimento_ft": t["comprimento_in"] / 12, "cortes": desc,
                    "sobra_in": round(t["comprimento_in"] - usado - p["kerf_in"] * (len(t["cortes"]) - 1), 2),
                }
            padroes[chave]["qtd_tabuas"] += 1
        plano_cortes.extend(padroes.values())
        # sobra para defeitos/erros: aplicada na bitola mais usada
        n_tab = len(tabuas)
        extra = math.ceil(n_tab * perdas[mat]) if perdas[mat] > 0 else 0
        if extra:
            mais_usada = max(cont, key=lambda k: (cont[k], k))
            cont[mais_usada] += extra
        for ft in sorted(cont):
            preco = ent["comprimentos"][ft]
            compra.append({"material": mat, "descricao": ent["descricao"], "comprimento_ft": ft, "qtd": cont[ft],
                           "preco_unit": preco, "subtotal": preco * cont[ft], "fonte": ent["fontes"].get(ft, ""),
                           "obs": f"inclui {extra} de sobra ({perdas[mat]:.0%})" if extra and ft == mais_usada else ""})

    for mat, por_ft in tabuas_diretas.items():
        ent = cat.get(mat, {"descricao": mat, "comprimentos": {}})
        for ft, q in sorted(por_ft.items()):
            preco = ent["comprimentos"].get(ft)
            if preco is None:
                avisos.append(f"Material '{mat}' {ft:g}' sem preço no catálogo — custo 0.")
                preco = 0.0
            compra.append({"material": mat, "descricao": ent["descricao"], "comprimento_ft": ft, "qtd": q,
                           "preco_unit": preco, "subtotal": preco * q, "obs": "quantidade informada",
                           "fonte": ent.get("fontes", {}).get(ft, "")})

    for mat, q in itens.items():
        ent = cat.get(mat)
        if not ent or ent.get("preco") is None:
            avisos.append(f"Item '{mat}' sem preço unitário no catálogo — custo 0.")
            ent = {"descricao": mat, "preco": 0.0, "unidade": "un"}
        q_compra = math.ceil(q - 1e-9)
        compra.append({"material": mat, "descricao": ent["descricao"], "comprimento_ft": "", "qtd": q_compra,
                       "preco_unit": ent["preco"], "subtotal": ent["preco"] * q_compra, "fonte": ent.get("fonte", ""),
                       "obs": f'{ent.get("unidade", "")} — ' + "; ".join(dict.fromkeys(itens_nomes[mat]))})

    # mão de obra
    mo = []
    for tarefa, qtd in tarefas.items():
        if isinstance(tarefa, tuple):
            mo.append({"tarefa": tarefa[1], "qtd": qtd, "unidade": "h", "h_unit": 1.0, "horas": qtd})
            continue
        info = prod.get(tarefa)
        if not info:
            avisos.append(f"Tarefa '{tarefa}' não está em produtividade.csv — 0 h.")
            info = {"unidade": "?", "horas": 0.0, "descricao": tarefa}
        mo.append({"tarefa": tarefa, "descricao": info["descricao"], "qtd": qtd, "unidade": info["unidade"],
                   "h_unit": info["horas"], "horas": qtd * info["horas"]})

    mat_sub = sum(c["subtotal"] for c in compra)
    mat_imp = mat_sub * p["imposto_material"]
    mat_mk = (mat_sub + mat_imp) * p["markup_material"]
    mat_cont = (mat_sub + mat_imp + mat_mk) * p["contingencia"]
    mat_total = mat_sub + mat_imp + mat_mk + mat_cont
    horas = sum(m["horas"] for m in mo)
    mo_sub = horas * p["taxa_hora_usd"]
    mo_cont = mo_sub * p["contingencia"]
    mo_total = mo_sub + mo_cont
    taxa = float(p.get("taxa_fixa_usd") or 0)

    return {
        "projeto": spec.get("projeto", ""),
        "cliente": spec.get("cliente", ""),
        "parametros": p,
        "componentes": spec.get("componentes", []),
        "detalhes_cortes": detalhes,
        "compra": compra,
        "plano_cortes": plano_cortes,
        "mao_de_obra": mo,
        "totais": {
            "material_subtotal": round(mat_sub, 2), "material_imposto": round(mat_imp, 2),
            "material_markup": round(mat_mk, 2), "material_contingencia": round(mat_cont, 2),
            "material_total": round(mat_total, 2),
            "horas": round(horas, 1), "mao_de_obra_subtotal": round(mo_sub, 2),
            "mao_de_obra_contingencia": round(mo_cont, 2), "mao_de_obra_total": round(mo_total, 2),
            "taxa_fixa": round(taxa, 2),
            "total_geral": round(mat_total + mo_total + taxa, 2),
        },
        "premissas": spec.get("premissas", []),
        "perguntas": spec.get("perguntas", []),
        "avisos": avisos,
        "fontes_preco": sorted({f'{v.get("fonte","")} ({v.get("data","")})' for v in cat.values()}),
    }


# ---------------------------------------------------------------- saídas
def usd(v):
    return f"${v:,.2f}"


def gerar_md(r):
    t, p = r["totais"], r["parametros"]
    L = [f"# Orçamento — {r['projeto']}", ""]
    if r["cliente"]:
        L += [f"**Cliente:** {r['cliente']}", ""]
    L += ["## Resumo", "",
          "| | Valor |", "|---|---:|",
          f"| Materiais (subtotal loja) | {usd(t['material_subtotal'])} |"]
    if t["material_imposto"]:
        L.append(f"| Imposto sobre material ({p['imposto_material']:.2%}) | {usd(t['material_imposto'])} |")
    if t["material_markup"]:
        L.append(f"| Markup material ({p['markup_material']:.0%}) | {usd(t['material_markup'])} |")
    if t["material_contingencia"]:
        L.append(f"| Contingência material ({p['contingencia']:.0%}) | {usd(t['material_contingencia'])} |")
    L += [f"| **Total materiais** | **{usd(t['material_total'])}** |",
          f"| Mão de obra ({t['horas']:g} h × {usd(p['taxa_hora_usd'])}/h) | {usd(t['mao_de_obra_subtotal'])} |"]
    if t["mao_de_obra_contingencia"]:
        L.append(f"| Contingência mão de obra ({p['contingencia']:.0%}) | {usd(t['mao_de_obra_contingencia'])} |")
    L.append(f"| **Total mão de obra** | **{usd(t['mao_de_obra_total'])}** |")
    if t["taxa_fixa"]:
        L.append(f"| **{p.get('taxa_fixa_descricao') or 'Taxa'}** | **{usd(t['taxa_fixa'])}** |")
    L += [f"| **TOTAL** | **{usd(t['total_geral'])}** |", ""]

    if r["avisos"]:
        L += ["## ⚠️ Avisos", ""] + [f"- {a}" for a in r["avisos"]] + [""]

    L += ["## Lista de compra", "", "| Material | Compr. | Qtd | Unit. | Subtotal | Obs. | Fonte do preço |", "|---|---:|---:|---:|---:|---|---|"]
    for c in r["compra"]:
        comp = f"{c['comprimento_ft']:g}'" if c["comprimento_ft"] != "" else ""
        L.append(f"| {c['descricao']} | {comp} | {c['qtd']} | {usd(c['preco_unit'])} | {usd(c['subtotal'])} | {c['obs']} | {c.get('fonte', '')} |")
    L.append("")

    calc = [c for c in r["componentes"] if c.get("_calc")]
    if calc:
        L += ["## Cálculos derivados", ""]
        for c in calc:
            L.append(f"- **{c.get('nome', c['tipo'])}**: " + ", ".join(f"{k} = {v}" for k, v in c["_calc"].items()))
        L.append("")

    L += ["## Peças (lista de corte)", "", "| Peça | Material | Qtd | Compr. (in) | Obs. |", "|---|---|---:|---:|---|"]
    for nome, mat, n, comp, obs in r["detalhes_cortes"]:
        L.append(f"| {nome} | {mat} | {n} | {comp:g} | {obs} |")
    L.append("")

    L += ["## Plano de corte (sem a sobra de perda)", "", "| Material | Tábuas | Compr. | Cortes por tábua | Sobra/tábua (in) |", "|---|---:|---:|---|---:|"]
    for pc in r["plano_cortes"]:
        L.append(f"| {pc['material']} | {pc['qtd_tabuas']} | {pc['comprimento_ft']:g}' | {pc['cortes']} | {pc['sobra_in']:g} |")
    L.append("")

    L += ["## Mão de obra", "", "| Tarefa | Qtd | Unid. | h/unid. | Horas |", "|---|---:|---|---:|---:|"]
    for m in r["mao_de_obra"]:
        L.append(f"| {m['tarefa']} | {m['qtd']:g} | {m['unidade']} | {m['h_unit']:g} | {m['horas']:.1f} |")
    L += [f"| **Total** | | | | **{t['horas']:.1f}** |", ""]

    if r["premissas"]:
        L += ["## Premissas", ""] + [f"- {x}" for x in r["premissas"]] + [""]
    if r["perguntas"]:
        L += ["## Perguntas / verificações de campo", ""] + [f"- [ ] {x}" for x in r["perguntas"]] + [""]
    L += ["## Fontes de preço", ""] + [f"- {f}" for f in r["fontes_preco"]] + [
        "", "_Preços de referência devem ser confirmados na loja/região antes da proposta final. "
        "Dimensionamento estrutural, licença/HOA, utilidades subterrâneas (811) e especificações do "
        "fabricante devem ser verificados antes da obra._", ""]
    return "\n".join(L)


def gerar_xlsx(r, caminho):
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font
    except ImportError:
        return False
    wb = Workbook()
    ws = wb.active
    ws.title = "Resumo"
    ws.append(["Projeto", r["projeto"]])
    ws.append(["Cliente", r["cliente"]])
    ws.append([])
    for k, v in r["totais"].items():
        ws.append([k, v])
    for row in ws.iter_rows(min_row=1, max_row=2):
        row[0].font = Font(bold=True)

    def aba(nome, cab, linhas):
        w = wb.create_sheet(nome)
        w.append(cab)
        for c in w[1]:
            c.font = Font(bold=True)
        for l in linhas:
            w.append(l)
        for col in w.columns:
            w.column_dimensions[col[0].column_letter].width = max(10, min(60, max(len(str(c.value or "")) for c in col) + 2))

    aba("Compra", ["Material", "Descrição", "Compr. (ft)", "Qtd", "Unit. USD", "Subtotal USD", "Obs.", "Fonte"],
        [[c["material"], c["descricao"], c["comprimento_ft"], c["qtd"], c["preco_unit"], c["subtotal"], c["obs"], c.get("fonte", "")] for c in r["compra"]])
    aba("Cortes", ["Material", "Qtd tábuas", "Compr. (ft)", "Cortes por tábua", "Sobra/tábua (in)"],
        [[p["material"], p["qtd_tabuas"], p["comprimento_ft"], p["cortes"], p["sobra_in"]] for p in r["plano_cortes"]])
    aba("Mão de obra", ["Tarefa", "Qtd", "Unid.", "h/unid.", "Horas"],
        [[m["tarefa"], m["qtd"], m["unidade"], m["h_unit"], m["horas"]] for m in r["mao_de_obra"]])
    aba("Premissas", ["Premissas e perguntas"], [[x] for x in r["premissas"]] + [[""]] + [["PERGUNTA: " + x] for x in r["perguntas"]] + [[""]] + [["AVISO: " + x] for x in r["avisos"]])
    wb.save(caminho)
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--saida", default=None, help="pasta de saída (padrão: <pasta do spec>/orcamento)")
    a = ap.parse_args()

    with open(a.spec, encoding="utf-8") as f:
        spec = json.load(f)
    base = os.path.dirname(os.path.abspath(a.spec))
    saida = a.saida or os.path.join(base, "orcamento")
    os.makedirs(saida, exist_ok=True)

    r = calcular(spec, base)
    with open(os.path.join(saida, "orcamento.md"), "w", encoding="utf-8") as f:
        f.write(gerar_md(r))
    with open(os.path.join(saida, "orcamento.json"), "w", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2, default=str)
    xlsx = gerar_xlsx(r, os.path.join(saida, "orcamento.xlsx"))

    t = r["totais"]
    print(f"Materiais: {usd(t['material_total'])} | Mão de obra: {usd(t['mao_de_obra_total'])} ({t['horas']:g} h) | "
          f"Taxa: {usd(t['taxa_fixa'])} | Total: {usd(t['total_geral'])}")
    print(f"Arquivos em {saida}: orcamento.md, orcamento.json" + (", orcamento.xlsx" if xlsx else " (sem xlsx: instale openpyxl)"))
    for av in r["avisos"]:
        print("AVISO:", av, file=sys.stderr)


if __name__ == "__main__":
    main()
