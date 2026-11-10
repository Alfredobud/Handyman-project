#!/usr/bin/env python3
"""Opção C (7 postes, 8 ft, 24 ripas 2x2, viga parafusada no núcleo): gera specs para
material {cedro, pt} x núcleo {4x4, 4x6, 6x6} em orcamento-c/<mat>-<nucleo>/ e um resumo.
Uso: python3 gerar_opcao_c.py   (depois rodar orcamento.py em cada pasta; o script já roda)"""
import json, math, os, subprocess, sys
AQUI = os.path.dirname(os.path.abspath(__file__))


def _skills(d):
    while not os.path.isdir(os.path.join(d, ".claude", "skills")):
        d = os.path.dirname(d)
    return os.path.join(d, ".claude", "skills")


SK = _skills(AQUI)
sys.path.insert(0, os.path.join(SK, "desenho-madeira", "templates"))
import privacy_screen as ps  # noqa: E402

BASE = json.load(open(os.path.join(AQUI, "orcamento-c-7-postes", "spec.json"), encoding="utf-8"))
PAR = {"taxa_hora_usd": 60, "perda": 0.05, "kerf_in": 0.125, "markup_material": 0.0, "imposto_material": 0.0825,
       "contingencia": 0.0, "taxa_fixa_usd": 150, "taxa_fixa_descricao": "Taxa"}
# núcleo -> (geometria do poste, material do núcleo, laterais (id, ripar?), faces (id, ripar?))
NUCLEOS = {
    "4x4": ({"nucleo": 3.5, "face_esp": 1.5, "face_larg": 5.5, "serrilhado_esp": 1.0, "lateral_ponta_esp": 1.0},
            "pt_4x4", ("5_4x6", True), ("2x6", False), 12.25),
    "4x6": ({"nucleo": 3.5, "nucleo_prof": 5.5, "face_esp": 1.5, "face_larg": 5.5, "serrilhado_esp": 1.0, "lateral_ponta_esp": 1.0},
            "pt_4x6", ("5_4x6", False), ("2x6", False), 19.25),
    "6x6": ({"nucleo": 5.5, "face_esp": 1.5, "face_larg": 7.0, "serrilhado_esp": 0.75, "lateral_ponta_esp": 0.75},
            "pt_6x6", ("1x6", False), ("2x8", True), 30.25),
}


def specs(mat, nuc):
    pg, mnuc, (lat, lat_rip), (face, face_rip), area_nuc = NUCLEOS[nuc]
    pre = "cedro" if mat == "cedro" else "pt"
    g = json.loads(json.dumps(BASE["geometria"]))
    g["poste"] = {k: v for k, v in pg.items() if k != "nucleo_prof"}
    G = ps.Geo(ps.mescla(ps.PADRAO, g))
    n, nb = G.n, G.n - 1
    d = g["sapata_diam_in"]
    brita = math.ceil(n * math.pi * (d / 2) ** 2 * g["brita_in"] / 1728 / 0.5)
    vg = g["viga"]
    C = [
        {"tipo": "sapata", "nome": f"Furos Ø{d}\" x {g['embutimento_in'] + g['brita_in']}\" — concreto", "qtd": n, "diametro_in": d,
         "profundidade_in": g["embutimento_in"] - 1, "desconto_poste_in2": area_nuc, "material": "concreto_80lb", "tarefa": "obra_assentar_poste"},
        {"tipo": "item", "nome": "Brita", "material": "brita_saco", "qtd": brita},
        {"tipo": "item", "nome": "Locação mini skid steer + auger (1 dia)", "material": "aluguel_mini_skid_auger", "qtd": 1,
         "tarefa": "obra_transporte_equipamento", "tarefa_qtd": 1},
        {"tipo": "item", "nome": "Frete do equipamento", "material": "frete_equipamento", "qtd": 1},
        {"tipo": "item", "nome": "Preservativo nos cortes do PT", "material": "preservativo_corte", "qtd": 1},
        {"tipo": "pecas", "nome": f"Núcleo {nuc} PT ground contact (embutir {g['embutimento_in']}\")", "material": mnuc,
         "comprimento_in": round(G.comp_nucleo + 1.5, 2), "qtd": n, "perda": 0, "tarefa": "obra_nivelar_topo"},
        {"tipo": "pecas", "nome": f"Laterais serrilhadas {pre} {lat}", "material": f"{pre}_{lat}", "comprimento_in": G.comp_rev,
         "qtd": 2 * nb, "tarefa": "oficina_serrilhado"},
        {"tipo": "pecas", "nome": f"Laterais lisas {pre} {lat} (pontas)", "material": f"{pre}_{lat}", "comprimento_in": G.comp_rev, "qtd": 2},
        {"tipo": "pecas", "nome": f"Faces {pre} {face}" + (" ripado" if face_rip else ""), "material": f"{pre}_{face}",
         "comprimento_in": G.comp_face, "qtd": 2 * n, "tarefa": "oficina_corte"},
        {"tipo": "pecas", "nome": f"Ripas {pre} 2x2 ({G.fiadas}/vão)", "material": f"{pre}_2x2", "comprimento_in": round(G.comp_ripa, 3),
         "qtd": G.fiadas * nb, "tarefa": "oficina_corte"},
    ]
    pv = {}
    for c in G.pecas_viga:
        pv[round(c, 3)] = pv.get(round(c, 3), 0) + 2
    for comp, q in pv.items():
        C.append({"tipo": "pecas", "nome": f"Vigas {pre} 2x8 {ps.pes_pol(comp)} (entalhadas, parafusadas no núcleo)", "material": f"{pre}_2x8",
                  "comprimento_in": comp, "qtd": q, "tarefa": "oficina_tabua_topo"})
    C += [
        {"tipo": "pecas", "nome": f"Caibros {pre} 2x6 ponta nuvem ({len(G.xc)})", "material": f"{pre}_2x6", "comprimento_in": 36,
         "qtd": len(G.xc), "tarefa": "oficina_caibro_nuvem"},
        {"tipo": "item", "nome": "Parafusos passantes 1/2\" (4 por poste)", "material": "parafuso_passante", "qtd": 4 * n},
        {"tipo": "item", "nome": "Parafusos deck trim-head", "material": "parafuso_deck_trim", "qtd": 4},
        {"tipo": "item", "nome": "Cola PU/exterior", "material": "cola_externa", "qtd": 3},
        {"tipo": "item", "nome": "Descarte", "material": "descarte", "qtd": 1},
    ]
    if pre == "pt":
        C.append({"tipo": "item", "nome": "Stain (tudo, 1 demão após secagem)", "material": "stain_galao", "qtd": 3,
                  "tarefa": "acabamento_stain", "tarefa_qtd": 450})
    ripar = (2 * nb + 2 if lat_rip else 0) + (2 * n if face_rip else 0)
    pecas = 2 * nb + G.fiadas * nb + 2 * n + 2 + 2 * len(G.pecas_viga) + len(G.xc)
    X = [{"tarefa": "locacao", "qtd": 1}, {"tarefa": "obra_escavacao_mecanizada", "qtd": n}, {"tarefa": "compras_transporte", "qtd": 1},
         {"tarefa": "oficina_gabaritos", "qtd": 1}, {"tarefa": "oficina_acabamento_lixa", "qtd": pecas},
         {"tarefa": "obra_instalar_serrilhado", "qtd": 2 * nb}, {"tarefa": "obra_instalar_ripa", "qtd": G.fiadas * nb},
         {"tarefa": "obra_instalar_face", "qtd": 2 * n}, {"tarefa": "obra_instalar_lateral", "qtd": 2},
         {"tarefa": "obra_instalar_tabua_topo", "qtd": 2 * len(G.pecas_viga)}, {"tarefa": "obra_instalar_caibro", "qtd": len(G.xc)},
         {"tarefa": "limpeza", "qtd": 1}]
    if ripar:
        X.append({"tarefa": "oficina_ripar", "qtd": ripar})
    if pre == "pt":
        X.append({"descricao": "Retorno para stain após secagem", "horas": 2})
    s = {"projeto": f"Kitchen Privacy Screen — opção C, {n} postes, {'cedro' if pre == 'cedro' else '100% pinus'}, núcleo {nuc}",
         "cliente": "Bill", "precos": "../../orcamento/precos.csv", "parametros": PAR, "geometria": g,
         "componentes": C, "tarefas_extra": X, "premissas": [f"Comparativo de núcleo {nuc}; vão livre {ps.pes_pol(G.vao)}; poste {ps.pes_pol(G.W[1])}."]}
    return s, G


def main():
    orc = os.path.join(SK, "orcamento-madeira", "scripts", "orcamento.py")
    linhas = []
    for mat in ("cedro", "pt"):
        for nuc in NUCLEOS:
            s, G = specs(mat, nuc)
            pasta = os.path.join(AQUI, "orcamento-c", f"{mat}-{nuc}")
            os.makedirs(pasta, exist_ok=True)
            json.dump(s, open(os.path.join(pasta, "spec.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            subprocess.run([sys.executable, orc, os.path.join(pasta, "spec.json"), "--saida", pasta], check=True, stdout=subprocess.DEVNULL)
            r = json.load(open(os.path.join(pasta, "orcamento.json")))
            t = r["totais"]
            nucleo = sum(c["subtotal"] for c in r["compra"] if c["material"].startswith(("pt_4x4", "pt_4x6", "pt_6x6")))
            linhas.append((mat, nuc, G.vao, G.W[1], nucleo, t["material_total"], t["mao_de_obra_total"], t["horas"], t["total_geral"]))
    out = ["| Material | Núcleo | Vão livre | Poste | Núcleos (loja) | Materiais | Mão de obra | Total |", "|---|---|---:|---:|---:|---:|---:|---:|"]
    for mat, nuc, vao, W, nucleo, m, mo, h, tot in linhas:
        out.append(f"| {'Cedro (núcleo PT)' if mat == 'cedro' else '100% pinus'} | {nuc} | {ps.pes_pol(vao)} | {ps.pes_pol(W)} | ${nucleo:,.0f} | ${m:,.0f} | ${mo:,.0f} ({h:.0f} h) | **${tot:,.0f}** |")
    open(os.path.join(AQUI, "orcamento-c", "comparativo-nucleo.md"), "w", encoding="utf-8").write(
        "# Opção C — comparativo de núcleo (7 postes, 8 ft, embutimento 36\")\n\n" + "\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
