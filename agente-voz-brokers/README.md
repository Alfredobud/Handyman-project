# Agente de voz para negociação com brokers (EUA): persona "Megan"

> **Status:** definição de persona concluída (v1, 16/11/2026). Próximo passo: preencher as decisões pendentes e escolher a plataforma de voz.
> **Escopo:** agente de IA por voz que liga para freight brokers nos EUA, em nome de uma transportadora, e negocia o valor das cargas.

## Resumo executivo

1. **Contraparte:** o *carrier sales rep* do broker.
   - Maioria homens (~60–65%). Nas brokerages grandes, jovens e com metas agressivas; nas pequenas, mais experientes e relacionais.
   - Faz de 25 a 100 ligações por dia e ganha comissão sobre a **margem**: cada dólar que conseguimos sai do bolso dele.
   - Tem um teto ("max buy") e pouca autonomia acima dele.
2. **O broker quer certeza:** caminhão confiável, sem "fall-off", com tracking. **Paga um pouco mais por isso.** Vender confiabilidade é tão importante quanto negociar preço.
3. **O broker tem medo de fraude.** O agente precisa ligar do **telefone oficial no FMCSA** (com nome e STIR/SHAKEN), usar e-mail do domínio da empresa e **ser transparente sobre ser IA**.
4. **IA já é rotina no frete.** Brokers grandes usam IA de voz (HappyRobot, Parade etc.). O diferencial não é ser IA: é ser **rápida, competente e honesta**.
5. **Persona:** **Megan**, "AI dispatch assistant" da transportadora.
   - Voz feminina de 30–40 anos, General American, calma, confiante e firme sem ser agressiva.
   - Fala curta, domina o jargão e os números.
6. **Voz feminina: concordo**, com três cuidados que vêm da pesquisa:
   - Negociar sempre **em nome do motorista e da empresa** (enquadramento de advocacia, que elimina o backlash contra mulheres assertivas).
   - Âncoras **justificadas com dados**.
   - Entonação **descendente** nos números (sem "uptalk").
   - Confirmar com teste A/B contra uma voz masculina.
7. **Mercado agora (nov/2026):** apertado, favorável ao carrier.
   - Spot rates nos maiores níveis desde 2010; Thanksgiving em 26/11.
   - Preços sempre vêm de API em tempo real, nunca fixos no prompt.
8. **Negociação:** quem calcula piso, alvo, âncora e escada de concessões é o **sistema**, não a IA. A IA conduz a conversa:
   - âncora justificada, concessões decrescentes e sempre trocadas por algo;
   - read-back obrigatório;
   - saída elegante quando não fecha.
9. **Hard rules:** nunca negar ser IA, nunca mentir sobre caminhão ou ofertas, nunca fechar abaixo do piso, nunca aceitar renegociação depois da rate con, escalar diante de qualquer sinal de fraude.
10. **Implantação em fases:** simulação → sombra → IA com aprovação humana → autônoma com guardrails.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| [`01-perfil-brokers-e-dispatchers.md`](01-perfil-brokers-e-dispatchers.md) | Pesquisa: quem é o broker e o dispatcher, demografia, remuneração, rotina, psicografia, arquétipos, táticas, fraude, atitude em relação a IA, mercado atual |
| [`02-persona.md`](02-persona.md) | Identidade da Megan, análise da voz feminina, perfil vocal, personalidade, princípios, estilo de fala, postura em situações difíceis, roteiro de audição |
| [`03-playbook-negociacao.md`](03-playbook-negociacao.md) | Estratégia, cálculo de piso/alvo/âncora, fluxo da ligação com falas em inglês, respostas às táticas do broker, accessorials, timing, voicemail, registro no CRM |
| [`04-guardrails-compliance.md`](04-guardrails-compliance.md) | Regras invioláveis, divulgação de IA, gravação, TCPA, anti-fraude, escalonamento, checklist para o advogado |
| [`05-system-prompt.md`](05-system-prompt.md) | **System prompt pronto (inglês)** com variáveis dinâmicas + lista de ferramentas (functions) |
| [`06-especificacao-tecnica-voz.md`](06-especificacao-tecnica-voz.md) | Requisitos para escolher a plataforma, dicionário de pronúncia, protocolo de escolha da voz, KPIs, testes A/B, fases de implantação |
| [`07-glossario.md`](07-glossario.md) | Jargão do frete nos EUA + frases típicas do broker |
| [`persona-config.yaml`](persona-config.yaml) | Configuração estruturada (para importar ou copiar na plataforma) |
| [`fontes.md`](fontes.md) | Todas as fontes da pesquisa |

## Decisões pendentes (do negócio)

| # | Decisão | Recomendação | Impacto |
|---|---|---|---|
| 1 | A empresa é **carrier** (tem caminhões/MC próprio) ou **dispatch service** (atende carriers de terceiros)? | — | Muda a resposta a "in-house or dispatch service?" e exige contrato com o carrier |
| 2 | Equipamentos: dry van, reefer, flatbed, box truck, hotshot, power only? | — | Jargão, accessorials (tarp, temperatura) e lanes |
| 3 | Divulgação de IA proativa ou só se perguntado | **Proativa** ([`04`](04-guardrails-compliance.md) §2) | Compliance e confiança |
| 4 | Autonomia: a IA fecha sozinha ou com aprovação humana? | Começar **com aprovação** (fase 2) | Risco operacional |
| 5 | CPM (custo por milha), margem mínima e regras de piso/alvo | Definir com dados reais da operação | Base de todo o preço |
| 6 | Valores de accessorials (detention, layover, TONU, stop, tarp) | Padrão de mercado: detention após 2 h | Read-back e rate con |
| 7 | Nome final da persona | **Megan** (alternativas: Lauren, Rachel) | Marca |
| 8 | Quem é o humano de escalonamento e em que horários | — | Transferências |
| 9 | Load boards e sistemas a integrar (DAT, Truckstop, 123Loadboard; TMS; ELD) | — | Escolha da plataforma |

## Premissas usadas

- O agente atua **do lado da transportadora** (carrier/dispatch), ligando para brokers sobre cargas publicadas em load boards e recebendo ligações de retorno.
- Todas as ligações são em inglês (espanhol como opcional futuro).
- Dados de caminhão, preço e broker chegam via integrações. A IA não inventa nem calcula números.
