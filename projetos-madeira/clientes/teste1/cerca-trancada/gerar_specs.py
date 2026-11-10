#!/usr/bin/env python3
"""Gera os specs do orçamento a partir da geometria do desenho (cerca_trancada.Geo).
  orcamento-modulo/   1 módulo + 1 poste (unidade de repetição, sem locação/mobilização)
  orcamento-completo/ cerca inteira (módulos x N, postes N+1, locação, mobilização, stain)"""
import json, math, os, sys
AQUI = os.path.dirname(os.path.abspath(__file__))


def _skills_dir(d):
    while not os.path.isdir(os.path.join(d, ".claude", "skills")):
        if os.path.dirname(d) == d:
            raise SystemExit("sem .claude/skills")
        d = os.path.dirname(d)
    return os.path.join(d, ".claude", "skills")


sys.path.insert(0, os.path.join(_skills_dir(AQUI), "desenho-madeira", "templates"))
import cerca_trancada as ct  # noqa: E402

PAR = {"taxa_hora_usd": 60, "perda": 0.05, "kerf_in": 0.125, "markup_material": 0.0, "imposto_material": 0.0825,
       "contingencia": 0.0, "taxa_fixa_usd": 150, "taxa_fixa_descricao": "Taxa"}


def comps(G, nmod, npost, completo):
    g = G.g
    d = g["poste"]["furo_diam_in"]
    brita = math.ceil(npost * math.pi * (d / 2) ** 2 * g["poste"]["brita_in"] / 1728 / 0.5)
    area = nmod * (G.vao * G.y_topo * 2 + 4 * G.P * G.y_poste) / 144          # 2 faces + postes, 1 demão
    C = [
        {"tipo": "sapata", "nome": f"Furos Ø{d}\" x {g['poste']['embutimento_in'] + g['poste']['brita_in']}\" — concreto", "qtd": npost,
         "diametro_in": d, "profundidade_in": g["poste"]["embutimento_in"] - 1, "desconto_poste_in2": G.P ** 2,
         "material": "concreto_80lb", "tarefa": "obra_assentar_poste"},
        {"tipo": "item", "nome": "Brita no fundo dos furos", "material": "brita_saco", "qtd": brita},
        {"tipo": "pecas", "nome": f"Postes pinus tratado 6x6 ground contact (embutir {g['poste']['embutimento_in']}\")", "material": "pt_6x6",
         "comprimento_in": G.comp_poste, "qtd": npost, "perda": 0, "tarefa": "obra_nivelar_topo"},
        {"tipo": "pecas", "nome": f"Tábuas trançadas 1x6 ({G.fiadas}/módulo)", "material": "pt_1x6", "comprimento_in": G.comp_tabua,
         "qtd": G.fiadas * nmod, "tarefa": "obra_tabua_trancada"},
        {"tipo": "pecas", "nome": f"Sarrafos verticais do trançado 1x2 ({len(G.xs)}/módulo)", "material": "pt_1x2",
         "comprimento_in": G.comp_vertical, "qtd": len(G.xs) * nmod, "tarefa": "obra_sarrafo_trama"},
        {"tipo": "pecas", "nome": "Batentes do canal nos postes 1x2 (4/módulo)", "material": "pt_1x2", "comprimento_in": G.comp_vertical,
         "qtd": 4 * nmod, "tarefa": "obra_batente"},
        {"tipo": "pecas", "nome": "Travessas 2x4 (inferior + superior)", "material": "pt_2x4", "comprimento_in": G.vao,
         "qtd": 2 * nmod, "tarefa": "obra_travessa_cerca"},
        {"tipo": "pecas", "nome": "Capeamento 2x6 (emenda sobre poste)", "material": "pt_2x6", "comprimento_in": G.oc,
         "qtd": nmod, "tarefa": "obra_capa"},
        {"tipo": "item", "nome": "Parafusos deck trim-head (ocultos)", "material": "parafuso_deck_trim", "qtd": max(1, math.ceil(nmod / 4))},
        {"tipo": "item", "nome": "Stain semi-transparente (2 faces, 1 demão após secagem)", "material": "stain_galao",
         "qtd": max(1, math.ceil(area / 250)), "tarefa": "acabamento_stain", "tarefa_qtd": round(area)},
    ]
    if completo:
        C += [{"tipo": "item", "nome": "Locação: mini skid steer com auger 12\" (1 dia)", "material": "aluguel_mini_skid_auger", "qtd": 1,
               "tarefa": "obra_transporte_equipamento", "tarefa_qtd": 1},
              {"tipo": "item", "nome": "Entrega/retirada do equipamento", "material": "frete_equipamento", "qtd": 1},
              {"tipo": "item", "nome": "Preservativo nos cortes do PT", "material": "preservativo_corte", "qtd": 1},
              {"tipo": "item", "nome": "Descarte", "material": "descarte", "qtd": 1}]
    pecas = G.fiadas * nmod + len(G.xs) * nmod + 4 * nmod + 2 * nmod + nmod
    X = [{"tarefa": "obra_escavacao_mecanizada", "qtd": npost}, {"tarefa": "oficina_corte", "qtd": pecas},
         {"tarefa": "oficina_acabamento_lixa", "qtd": pecas}]
    if completo:
        X += [{"tarefa": "locacao", "qtd": 1}, {"tarefa": "compras_transporte", "qtd": 1}, {"tarefa": "limpeza", "qtd": 1},
              {"descricao": "Visita de retorno para stain após secagem", "horas": 2}]
    return C, X


def main():
    base = json.load(open(os.path.join(AQUI, "orcamento-modulo", "spec.json"), encoding="utf-8"))
    G = ct.Geo(ct.mescla(ct.PADRAO, base.get("geometria", {})))
    for pasta, nmod, npost, comp in [("orcamento-modulo", 1, 1, False), ("orcamento-completo", G.n_mod, G.n_postes, True)]:
        C, X = comps(G, nmod, npost, comp)
        s = dict(base)
        s.update({"parametros": PAR, "precos": "../orcamento-modulo/precos.csv" if pasta != "orcamento-modulo" else "precos.csv",
                  "componentes": C, "tarefas_extra": X,
                  "premissas": [
                      f"Módulo {G.oc}\" (10'-0\" = 3.05 m) entre eixos: trechos 40'/60'/40' = {G.modulos} módulos idênticos, {G.n_postes} postes.",
                      f"Altura total {ct.pes_pol(G.y_topo)}: módulo/altura = {G.razao:.3f} (φ = 1.618). {G.fiadas} tábuas 1x6 por módulo.",
                      f"Folga de {ct.pes_pol(G.gap)} entre a travessa inferior e o terreno.",
                      "Tudo em pinus tratado aplainado S4S; postes 6x6 ground contact embutidos 24\" em concreto sobre 6\" de brita.",
                      "Trançado montado na obra: travessa inferior + sarrafos, tábuas descem pelo canal dos postes alternando frente/trás; peças pré-cortadas na oficina.",
                      "Stain semi-transparente nas 2 faces em visita após secagem (pinus tratado chega úmido).",
                      "PRELIMINAR: estudo de módulo; preços de 1x6, 1x2 e 6x6 estimados.",
                      "Orçamento de 1 módulo = módulo + 1 poste, sem locação/mobilização (essas entram só no completo)." if pasta == "orcamento-modulo" else
                      "Inclui locação do equipamento, mobilização, compras, limpeza e visita do stain.",
                  ],
                  "perguntas": ["Altura: 6'-1 1/2\" (proporção áurea). HOA/código de Cornelius costuma limitar cerca lateral/fundo a 6'-0\"?",
                                "Iluminação LED atrás das tábuas (como na foto): incluir?", "Portão(ões): quantos e onde?",
                                "Terreno plano ou com desnível (degraus nos módulos)?"]})
        os.makedirs(os.path.join(AQUI, pasta), exist_ok=True)
        json.dump(s, open(os.path.join(AQUI, pasta, "spec.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(pasta, "ok")


if __name__ == "__main__":
    main()
