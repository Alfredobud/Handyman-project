#!/usr/bin/env python3
"""Gera os spec.json das propostas do privacy screen a partir da MESMA geometria dos desenhos.

Uso: python3 gerar_propostas.py   (depois rodar orcamento.py e privacy_screen.py em cada pasta)

Variantes:
  orcamento/            10 postes, cedro aparente (núcleo PT)
  orcamento-7-postes/    7 postes, cedro aparente (núcleo PT)
  orcamento-pt/         10 postes, 100% PT (pinus autoclavado) + stain
"""
import json
import math
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))

def _skills_dir(inicio):
    """Sobe a partir desta pasta até achar .claude/skills (funciona em qualquer profundidade)."""
    d = inicio
    while True:
        cand = os.path.join(d, ".claude", "skills")
        if os.path.isdir(cand):
            return cand
        pai = os.path.dirname(d)
        if pai == d:
            raise SystemExit("não achei .claude/skills acima de " + inicio)
        d = pai


SKILLS = _skills_dir(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(SKILLS, "desenho-madeira", "templates"))
import privacy_screen as ps  # noqa: E402

PARAMETROS = {"taxa_hora_usd": 60, "perda": 0.05, "kerf_in": 0.125, "markup_material": 0.0,
              "imposto_material": 0.0825, "contingencia": 0.0, "taxa_fixa_usd": 150, "taxa_fixa_descricao": "Taxa"}

VARIANTES = [
    {"pasta": "orcamento", "n": 10, "mat": "cedro", "pref": "A"},
    {"pasta": "orcamento-7-postes", "n": 7, "mat": "pt", "pref": "B"},
    {"pasta": "orcamento-pt", "n": 10, "mat": "pt", "pref": "C"},
]

MAT = {
    "cedro": {"nome": "cedro", "2x6": "cedro_2x6", "2x4": "cedro_2x4", "2x8": "cedro_2x8", "54": "cedro_5_4x6",
              "rot": {}, "mats": {}},
    "pt": {"nome": "PT", "2x6": "pt_2x6", "2x4": "pt_2x4", "2x8": "pt_2x8", "54": "pt_5_4x6",
           "rot": {"revest": "PT 2x6 S4S", "serrilhado": "PT 5/4 S4S (1\") notched", "lateral_ponta": "PT 5/4 S4S (1\") plain",
                   "ripa": "PT 2x4 S4S (flat)", "viga": "PT 2x8 S4S", "caibro": "PT 2x6 S4S",
                   "especie": "All lumber: Southern Yellow Pine #2, pressure-treated, S4S; posts ground contact (UC4B)."},
           "mats": {"revest": "pt", "serrilhado": "pt", "ripa": "pt", "viga": "pt", "caibro": "pt"}},
}


def gerar(var):
    m = MAT[var["mat"]]
    geo = {"comprimento_total_in": 265, "n_postes": var["n"], "embutimento_in": 24, "brita_in": 6,
           "sapata_diam_in": 12, "altura_topo_in": 96, "lado_ripas": "vizinho"}
    if m["rot"]:
        geo["rotulos"] = m["rot"]
        geo["materiais"] = m["mats"]
    G = ps.Geo(ps.mescla(ps.PADRAO, geo))
    n, nb = G.n, G.n - 1
    g = G.g
    brita = math.ceil(n * math.pi * (g["sapata_diam_in"] / 2) ** 2 * g["brita_in"] / 1728 / 0.5)
    pv = {}
    for c in G.pecas_viga:
        pv[round(c, 3)] = pv.get(round(c, 3), 0) + 2
    nome = m["nome"]
    C = [
        # fundação (obra, com equipamento alugado)
        {"tipo": "sapata", "nome": f"Furos Ø{g['sapata_diam_in']}\" x {g['embutimento_in'] + g['brita_in']}\" — concreto em volta do núcleo",
         "qtd": n, "diametro_in": g["sapata_diam_in"], "profundidade_in": g["embutimento_in"] - 1,
         "desconto_poste_in2": 12.25, "material": "concreto_80lb", "tarefa": "obra_assentar_poste"},
        {"tipo": "item", "nome": f"Brita {g['brita_in']}\" no fundo dos furos", "material": "brita_saco", "qtd": brita},
        {"tipo": "item", "nome": "Locação: mini skid steer com auger 12\" (1 dia)", "material": "aluguel_mini_skid_auger", "qtd": 1,
         "tarefa": "obra_transporte_equipamento", "tarefa_qtd": 1},
        {"tipo": "item", "nome": "Entrega/retirada do equipamento", "material": "frete_equipamento", "qtd": 1},
        {"tipo": "item", "nome": "Preservativo nos cortes do PT", "material": "preservativo_corte", "qtd": 1},
        {"tipo": "pecas", "nome": f"Núcleo PT 4x4 ground contact (embutir {g['embutimento_in']}\", nivelar topo na obra)",
         "material": "pt_4x4", "comprimento_in": round(G.comp_nucleo + 1.5, 2), "qtd": n, "perda": 0,
         "tarefa": "obra_nivelar_topo"},
        # peças pré-cortadas na oficina
        {"tipo": "pecas", "nome": f"Laterais serrilhadas {nome} 5/4x6 (1\", ripar p/ 3 1/2\", {G.fiadas} encaixes)",
         "material": m["54"], "comprimento_in": G.comp_rev, "qtd": 2 * nb, "tarefa": "oficina_serrilhado"},
        {"tipo": "pecas", "nome": f"Ripas {nome} 2x4 deitado ({G.fiadas}/vão x {nb} vãos)", "material": m["2x4"],
         "comprimento_in": round(G.comp_ripa, 3), "qtd": G.fiadas * nb, "tarefa": "oficina_corte"},
        {"tipo": "pecas", "nome": f"Faces do poste {nome} 2x6 (casa + vizinho)", "material": m["2x6"],
         "comprimento_in": G.comp_rev, "qtd": 2 * n, "tarefa": "oficina_corte"},
        {"tipo": "pecas", "nome": f"Laterais lisas {nome} 5/4x6 (1\", ripar p/ 3 1/2\") — postes 1 e {n}",
         "material": m["54"], "comprimento_in": G.comp_rev, "qtd": 2, "tarefa": "oficina_ripar"},
    ]
    for comp, q in sorted(pv.items()):
        C.append({"tipo": "pecas", "nome": f"Tábuas de topo {nome} 2x8 de {ps.pes_pol(comp)}, entalhadas p/ caibros (emendas sobre postes "
                  + ", ".join(str(i + 1) for i in G.emendas) + ")", "material": m["2x8"], "comprimento_in": comp, "qtd": q,
                  "tarefa": "oficina_tabua_topo"})
    C += [
        {"tipo": "pecas", "nome": f"Fechamento das pontas das tábuas de topo {nome} 2x8", "material": m["2x8"],
         "comprimento_in": G.fech_larg, "qtd": 2, "tarefa": "oficina_fechamento"},
        {"tipo": "pecas", "nome": f"Caibros do pergolado {nome} 2x6 com ponta tipo nuvem (1 por poste)", "material": m["2x6"],
         "comprimento_in": g["caibro"]["comprimento"], "qtd": len(G.xc), "tarefa": "oficina_caibro_nuvem"},
        # fixação
        {"tipo": "item", "nome": "Parafusos passantes 1/2\"x10\" (tábuas de topo/núcleo)", "material": "parafuso_passante", "qtd": n},
        {"tipo": "item", "nome": "Parafusos de deck trim-head (cabeça pequena, oculta), revestidos p/ PT", "material": "parafuso_deck_trim",
         "qtd": 3 if n <= 8 else 4},
        {"tipo": "item", "nome": "Cola PU/exterior", "material": "cola_externa", "qtd": 3},
        {"tipo": "item", "nome": "Descarte", "material": "descarte", "qtd": 1},
    ]
    if var["mat"] == "pt":
        C.append({"tipo": "item", "nome": "Stain semi-transparente (tudo, 1 demão após secagem)", "material": "stain_galao",
                  "qtd": 3, "tarefa": "acabamento_stain", "tarefa_qtd": 450})
    pecas_visiveis = 2 * nb + G.fiadas * nb + 2 * n + 2 + len(G.pecas_viga) * 2 + 2 + len(G.xc)
    extras = [
        {"tarefa": "locacao", "qtd": 1},
        {"tarefa": "obra_escavacao_mecanizada", "qtd": n},
        {"tarefa": "compras_transporte", "qtd": 1},
        {"tarefa": "oficina_gabaritos", "qtd": 1},
        {"tarefa": "oficina_ripar", "qtd": 2 * nb},                       # ripar os serrilhados (5/4x6 -> 3 1/2)
        {"tarefa": "oficina_acabamento_lixa", "qtd": pecas_visiveis},
        {"tarefa": "obra_instalar_serrilhado", "qtd": 2 * nb},
        {"tarefa": "obra_instalar_ripa", "qtd": G.fiadas * nb},
        {"tarefa": "obra_instalar_face", "qtd": 2 * n},
        {"tarefa": "obra_instalar_lateral", "qtd": 2},
        {"tarefa": "obra_instalar_tabua_topo", "qtd": 2 * len(G.pecas_viga)},
        {"tarefa": "obra_instalar_fechamento", "qtd": 2},
        {"tarefa": "obra_instalar_caibro", "qtd": len(G.xc)},
        {"tarefa": "limpeza", "qtd": 1},
    ]
    if var["mat"] == "pt":
        extras.append({"descricao": "Visita de retorno para stain após secagem da madeira", "horas": 2})
    titulo_mat = "cedro aparente (núcleo PT)" if var["mat"] == "cedro" else "100% pinus autoclavado (PT)"
    empeno = ("bem abaixo do limite de empeno (≤ 36\" conservador)" if G.vao <= 36
              else f"acima do limite conservador de 36\" (ainda abaixo do máximo de 48\"): ripa 2x4 deitada aguenta, mas tem mais chance de arquear do que com 10 postes")
    prem = [
        f"Material: {titulo_mat}." + (" Stain em 2ª visita após a secagem." if var["mat"] == "pt" else " Cedro natural, sem stain."),
        f"{n} postes a {ps.pes_pol(G.entre_eixos)} entre eixos; vão livre {ps.pes_pol(G.vao)}; vão/poste = {G.vao / 5.5:.2f} "
        + ("≈ φ³ (55/13 de Fibonacci)" if n == 10 else "≈ φ⁴ (89/13 de Fibonacci)" if n == 7 else "") + f"; {empeno}.",
        f"Poste composto: núcleo PT 4x4 ground contact embutido {g['embutimento_in']}\" em concreto (furo Ø{g['sapata_diam_in']}\" x {g['embutimento_in'] + g['brita_in']}\", "
        f"{g['brita_in']}\" de brita), furos com mini skid steer + auger alugado. Revestimento acima do colar: faces 2x6 e laterais de 1\" "
        f"(serrilhadas nos vãos, lisas nas pontas); todos os postes com 5 1/2\", faces alinhadas.",
        f"Ripas 2x4 deitadas: {G.fiadas} por vão, espaço {ps.pes_pol(G.espaco)}, ripa de {ps.pes_pol(G.comp_ripa)}; instaladas pelo lado do vizinho.",
        f"Topo: tábuas 2x8 dos dois lados dos postes, entalhadas 1 1/2\" para os caibros, {len(G.pecas_viga)} peças por lado ("
        + " + ".join(ps.pes_pol(c) for c in G.pecas_viga) + ") com emendas sobre os postes " + ", ".join(str(i + 1) for i in G.emendas)
        + f"; fechamento de {ps.pes_pol(G.fech_larg)} nas pontas (aparência de viga maciça); {len(G.xc)} caibros 2x6 de 36\" com ponta tipo nuvem.",
        "Acabamento da madeira: todo cedro aparente Western Red Cedar seco em estufa (KD), APLAINADO S4S (medidas reais 2x4 = 1 1/2 x 3 1/2, 2x6 = 1 1/2 x 5 1/2, 2x8 = 1 1/2 x 7 1/4, 5/4x6 = 1 x 5 1/2). "
        "Na Lowe's o cedro 2x6/2x8 costuma ser BRUTO/green (~1 11/16 x 5 3/4 e 7 5/8): comprar S4S em madeireira ou aplainar na oficina; os núcleos dos postes são pinus tratado (PT SYP) ground contact.",
        "Fixação: parafusos de deck trim-head (cabeça pequena, fica oculta), revestidos para PT/ACQ (não inox); parafuso passante de 1/2\" nas tábuas de topo.",
        "Mão de obra separada em OFICINA (pré-corte: serrilhados, ripas, faces, laterais, tábuas de topo, fechamentos, caibros, gabaritos, lixa) e OBRA (furos, postes, nivelamento, montagem).",
        "Sequência de instalação (A-3): 1 furos, 2 postes, 3 nivelar topos, 4 serrilhados pelo lado do vizinho, 5 ripas, 6 fechamento frontal, 7 fechamento lateral, 8 tábuas de topo, 9 fechamento das pontas, 10 caibros do pergolado.",
        "Preços: Lowe's/Home Depot online (nov/2026) e estimativas marcadas na coluna de fonte (PT 4x4x12, cedro 2x6/2x8, locação do equipamento, parafuso trim-head); confirmar em Cornelius.",
        "Imposto de Mecklenburg de 8.25% sobre o material; sem markup e sem contingência; taxa fixa de $150.",
        "Paisagismo (manta, borda e pedra de rio) NÃO incluído: é extra opcional, cotado à parte na proposta; trepadeiras não incluídas.",
        "Produtividade revisada com o ritmo real da equipe: furos + postes em 1 dia; serrilhados, ripas e faces chegam prontos e só encaixam.",
    ]
    perg = [
        "Confirmar preço e disponibilidade do mini skid steer com auger (Home Depot Rental / Sunbelt / United Rentals na região).",
        "Confirmar na loja os preços do cedro 2x6, 2x8 e 5/4x6 e do PT 4x4.",
        "NC811 antes de escavar; licença/HOA de Cornelius; posição da divisa.",
        "Trepadeiras e canteiro: o cliente fornece ou incluímos?",
    ]
    spec = {
        "projeto": f"Kitchen Privacy Screen — {n} postes, {titulo_mat}, topo pergolado (Cornelius, NC)",
        "projeto_en": f"Kitchen Privacy Screen — {n} posts, " + ("cedar" if var["mat"] == "cedro" else "pressure-treated pine")
                      + " with pergola top (Cornelius, NC)",
        "cliente": "Bill", "data": "2026-11-10", "revisao": "7", "idioma_desenho": "en", "prefixo_prancha": var["pref"],
        "precos": "../orcamento/precos.csv",
        "parametros": PARAMETROS, "geometria": geo, "componentes": C, "tarefas_extra": extras,
        "premissas": prem, "perguntas": perg,
    }
    pasta = os.path.join(AQUI, var["pasta"])
    os.makedirs(pasta, exist_ok=True)
    if var["pasta"] == "orcamento":
        spec["precos"] = "precos.csv"
    with open(os.path.join(pasta, "spec.json"), "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)
    print(var["pasta"], "ok")


if __name__ == "__main__":
    for v in VARIANTES:
        gerar(v)
