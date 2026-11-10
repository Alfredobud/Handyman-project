#!/usr/bin/env python3
"""Specs do orçamento da cerca trançada — solução PAINEL PRÉ-FABRICADO (rev. 2), a partir da
geometria do desenho (cerca_trancada.Geo / Painel).
  orcamento-modulo/   1 painel + 1 poste (unidade; sem locação/mobilização)
  orcamento-completo/ cerca inteira (14 painéis, 15 postes, locação, mobilização)"""
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


def comps(G, PN, npain, npost, completo):
    g = G.g
    d = g["poste"]["furo_diam_in"]
    brita = math.ceil(npost * math.pi * (d / 2) ** 2 * g["poste"]["brita_in"] / 1728 / 0.5)
    a_painel = npain * PN.W * PN.Hp * 2 / 144 * 1.25            # 2 faces; +25% pelo relevo do trançado
    a_obra = (npost * 4 * G.P * G.y_poste + npain * G.oc * (g["capa"]["larg"] + 2 * g["capa"]["esp"])) / 144
    galoes = math.ceil((a_painel + a_obra) / 200)
    nb = npain
    C = [
        # ---- fundação e postes (obra)
        {"tipo": "sapata", "nome": f"Furos Ø{d}\" x {g['poste']['embutimento_in'] + g['poste']['brita_in']}\" — concreto", "qtd": npost,
         "diametro_in": d, "profundidade_in": g["poste"]["embutimento_in"] - 1, "desconto_poste_in2": G.P ** 2,
         "material": "concreto_80lb", "tarefa": "obra_assentar_poste"},
        {"tipo": "item", "nome": "Brita no fundo dos furos", "material": "brita_saco", "qtd": brita},
        {"tipo": "pecas", "nome": "Postes pinus tratado 6x6 ground contact (embutir 24\")", "material": "pt_6x6",
         "comprimento_in": G.comp_poste, "qtd": npost, "perda": 0, "tarefa": "obra_nivelar_topo"},
        # ---- painel (oficina)
        {"tipo": "pecas", "nome": "Moldura: montantes 2x4 PT S4S com rasgo (2/painel)", "material": "pt_2x4",
         "comprimento_in": PN.comp_montante, "qtd": 2 * nb, "tarefa": "oficina_rasgo_moldura"},
        {"tipo": "pecas", "nome": "Moldura: travessas 2x4 PT S4S com rasgo (2/painel)", "material": "pt_2x4",
         "comprimento_in": PN.comp_travessa, "qtd": 2 * nb, "tarefa": "oficina_rasgo_moldura"},
        {"tipo": "pecas", "nome": f"Tábuas trançadas cedro 5/8 x 6 ({G.fiadas}/painel)", "material": "cedro_5_8x6",
         "comprimento_in": PN.comp_tabua, "qtd": G.fiadas * nb, "tarefa": "oficina_corte"},
        {"tipo": "pecas", "nome": f"Sarrafos do trançado 1x2 PT ({len(PN.xs)}/painel)", "material": "pt_1x2",
         "comprimento_in": PN.comp_sarrafo, "qtd": len(PN.xs) * nb, "tarefa": "oficina_corte"},
        {"tipo": "item", "nome": "Montagem do painel (U + sarrafos + trançado com prego pneumático + 4º canto)",
         "material": "prego_pneumatico_inox", "qtd": max(1, math.ceil(nb * 70 / 1000)), "tarefa": "oficina_montar_painel", "tarefa_qtd": nb},
        {"tipo": "item", "nome": "Parafusos estruturais dos cantos da moldura (8/painel) + cola PU", "material": "parafuso_estrutural_caixa",
         "qtd": max(1, math.ceil(nb * 8 / 50))},
        {"tipo": "item", "nome": "Cola PU exterior", "material": "cola_externa", "qtd": max(1, math.ceil(nb / 4))},
        {"tipo": "item", "nome": "Pintura com pistola (painéis na oficina + postes/capa na obra)", "material": "tinta_pistola",
         "qtd": galoes, "tarefa": "oficina_pintura_pistola", "tarefa_qtd": round(a_painel)},
        # ---- instalação (obra)
        {"tipo": "pecas", "nome": "Blocos de apoio 2x4 (2 por painel)", "material": "pt_2x4", "comprimento_in": 3.0,
         "qtd": 2 * nb, "tarefa": "obra_bloco_apoio"},
        {"tipo": "pecas", "nome": "Batentes 1x2 PT nos postes (4 por painel)", "material": "pt_1x2", "comprimento_in": PN.Hp,
         "qtd": 4 * nb, "tarefa": "obra_batente"},
        {"tipo": "pecas", "nome": "Capeamento 2x6 PT contínuo (emenda sobre poste)", "material": "pt_2x6", "comprimento_in": G.oc,
         "qtd": nb, "tarefa": "obra_capa"},
        {"tipo": "item", "nome": "Parafusos trim-head nos postes (batentes, blocos, capa)", "material": "parafuso_deck_trim",
         "qtd": max(1, math.ceil(nb / 5)), "tarefa": "obra_instalar_painel", "tarefa_qtd": nb},
    ]
    X = [{"tarefa": "obra_escavacao_mecanizada", "qtd": npost},
         {"tarefa": "oficina_corte", "qtd": 4 * nb + nb + 2 * nb},       # batentes, capa, blocos pré-cortados
         {"tarefa": "oficina_acabamento_lixa", "qtd": (4 + G.fiadas + len(PN.xs)) * nb},
         {"tarefa": "obra_pintura_pistola", "qtd": round(a_obra)}]
    if completo:
        C += [{"tipo": "item", "nome": "Locação: mini skid steer com auger 12\" (1 dia)", "material": "aluguel_mini_skid_auger", "qtd": 1,
               "tarefa": "obra_transporte_equipamento", "tarefa_qtd": 1},
              {"tipo": "item", "nome": "Entrega/retirada do equipamento", "material": "frete_equipamento", "qtd": 1},
              {"tipo": "item", "nome": "Preservativo nos cortes do PT", "material": "preservativo_corte", "qtd": 1},
              {"tipo": "item", "nome": "Descarte", "material": "descarte", "qtd": 1}]
        X += [{"tarefa": "locacao", "qtd": 1}, {"tarefa": "compras_transporte", "qtd": 1}, {"tarefa": "limpeza", "qtd": 1},
              {"tarefa": "oficina_gabaritos", "qtd": 1},
              {"tarefa": "obra_transporte_paineis", "qtd": math.ceil(nb / 5)},
              {"descricao": "Retorno: pintura dos postes/capa após secagem do PT", "horas": 2}]
    return C, X


def main():
    p = os.path.join(AQUI, "orcamento-modulo", "spec.json")
    base = json.load(open(p, encoding="utf-8"))
    G = ct.Geo(ct.mescla(ct.PADRAO, base.get("geometria", {})))
    PN = ct.Painel(G)
    for pasta, npain, npost, comp in [("orcamento-modulo", 1, 1, False), ("orcamento-completo", G.n_mod, G.n_postes, True)]:
        C, X = comps(G, PN, npain, npost, comp)
        s = dict(base)
        s.update({"parametros": PAR, "precos": "precos.csv" if pasta == "orcamento-modulo" else "../orcamento-modulo/precos.csv",
                  "componentes": C, "tarefas_extra": X,
                  "premissas": [
                      f"Solução PAINEL PRÉ-FABRICADO: moldura fechada nos 4 cantos ({ct.pes_pol(PN.W)} x {ct.pes_pol(PN.Hp)}), 2x4 PT S4S com rasgo de "
                      f"{ct.pes_pol(PN.rl)} x {ct.pes_pol(PN.rp)}; montada e pintada na oficina; ~{PN.peso_lb:.0f} lb por painel.",
                      f"Trançado: {G.fiadas} tábuas de CEDRO 5/8\" x 6 ({ct.pes_pol(PN.comp_tabua)}) e {len(PN.xs)} sarrafos 1x2 PT; tábuas fixadas com prego "
                      "pneumático inox anelado em cada cruzamento com os sarrafos.",
                      f"Módulo de 10'-0\" entre eixos: 40'/60'/40' = {G.modulos} → {G.n_mod} painéis iguais e {G.n_postes} postes 6x6 PT ground contact de 8', "
                      "embutidos 24\" em concreto sobre 6\" de brita (furos com mini skid steer + auger alugado).",
                      f"Altura total {ct.pes_pol(G.y_topo)} (módulo/altura = {G.razao:.3f} ≈ φ); folga de {ct.pes_pol(G.gap)} do terreno, definida pelos blocos de apoio.",
                      "Instalação: blocos de apoio → batentes 1x2 do lado do vizinho → painel → batentes do lado da casa → capeamento 2x6. "
                      "Nos postes, tudo com PARAFUSO (batentes, blocos e capa).",
                      "Pintura com PISTOLA: painéis na oficina (2 faces, +25% pelo relevo do trançado); postes e capa na obra, numa visita de retorno "
                      "depois da secagem do PT. Rendimento adotado de ~200 sqft/gal na pistola.",
                      "Estrutura (moldura, sarrafos, batentes, capa, postes) em pinus tratado S4S; usar KDAT na moldura para poder pintar logo.",
                      "PRELIMINAR: preços de cedro 5/8 em 10', 1x2, 6x6, pregos e tinta são estimados.",
                      "Orçamento de 1 módulo = 1 painel + 1 poste, sem locação/mobilização." if pasta == "orcamento-modulo" else
                      "Inclui locação do equipamento, transporte dos painéis (reboque), mobilização, compras, limpeza e retorno da pintura.",
                  ],
                  "perguntas": ["Cedro 5/8\" em 10': confirmar disponibilidade (madeireira) e preço.",
                                "Cor/produto da pintura (stain transparente, semi ou sólido)?",
                                "Altura 6'-1 1/2\": confirmar limite de HOA/código.", "LED, portões, desnível do terreno."]})
        os.makedirs(os.path.join(AQUI, pasta), exist_ok=True)
        json.dump(s, open(os.path.join(AQUI, pasta, "spec.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(pasta, "ok", f"painel {PN.W}x{PN.Hp} {PN.peso_lb} lb")


if __name__ == "__main__":
    main()
