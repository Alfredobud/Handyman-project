# Dispatcher de voz para motoristas: persona "Laura / Daniel"

> **Status:** v1, 16/11/2026.
> **Escopo:** o agente de IA que **fala com os nossos motoristas**, que são **clientes** (owner-operators). Complementa a Megan ([`../agente-voz-brokers/`](../agente-voz-brokers/README.md)), que fala com os brokers.

## Resumo executivo

1. **Um dispatcher, duas vozes:** **Laura** (feminina) e **Daniel** (masculino).
   - Mesmo "cérebro": mesmas regras, mesma memória do motorista. Só a voz muda.
   - O motorista escolhe ouvindo as duas no onboarding e troca quando quiser.
   - É honesto (ele sabe que é a mesma IA) e mantém o serviço consistente.
2. **A escolha de voz tem base:** o setor recomenda combinar motorista e dispatcher por afinidade, e a preferência por gênero de voz varia de pessoa para pessoa. Escolher também reforça a mensagem central: **aqui quem decide é você**.
3. **Quem é o cliente:**
   - Homem na maioria (~96%), 40–60 anos, experiente.
   - Muitas vezes imigrante e bilíngue.
   - Virou owner-operator **pela liberdade**.
   - Já foi mal tratado por dispatchers e enganado por brokers.
4. **Postura da persona:** *copiloto confiável*, não chefe.
   - Traz opções e uma recomendação honesta; **o motorista decide**.
   - Ela executa: negociação (via Megan), check calls, papelada, cobranças.
5. **Matriz de decisões clara:**
   - O motorista decide carga, preço mínimo, regiões, tempo em casa e segurança.
   - A IA executa e **só veta** broker suspeito ou carga ilegal/insegura.
   - Três níveis de autonomia, escolhidos pelo motorista (padrão: nível 2, negocia e pergunta antes de fechar).
6. **Respeito ao sono e à estrada:**
   - Consulta o ELD antes de ligar e não liga no descanso.
   - Com ele dirigindo, ligação de menos de 60 s, sem pedir para anotar nada; detalhes por mensagem.
7. **Transparência radical:**
   - Rate con original sempre e taxa do serviço sempre visível.
   - Nenhum dinheiro de broker; não passamos pagamento de frete.
8. **Segurança absoluta:** nunca pressiona para violar HOS ou dirigir cansado (coercion rule, 49 CFR 390.6). Há protocolos de acidente (911), crise (988) e escalonamento humano.
9. **Multilíngue:** inglês, português e espanhol, com termos do frete em inglês. Apoio opcional de inglês para inspeções, por causa da fiscalização de proficiência (ELP).
10. **Voz para a cabine:** fala mais lenta que a da Megan e clara nos médios. No Daniel, evitar grave profundo, que some no ronco do motor. Testar com ruído real de cabine.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| [`01-perfil-motoristas.md`](01-perfil-motoristas.md) | Pesquisa: quem é o motorista, preocupações em 2026, relação com dispatchers, rotina na estrada, regulação, idioma |
| [`02-persona-dispatcher.md`](02-persona-dispatcher.md) | Conceito "uma persona, duas vozes", identidade, perfil vocal de Laura e Daniel, personalidade, preferências do motorista, estilo de fala (EN/PT/ES), roteiro de onboarding e de audição |
| [`03-playbook-conversas.md`](03-playbook-conversas.md) | Matriz de decisões, onboarding, quando ligar, como oferecer carga, fechamento, problemas, semana, extrato, fim de dia, vocabulário da estrada |
| [`04-guardrails-seguranca.md`](04-guardrails-seguranca.md) | Regras invioláveis, segurança e emergências, transparência financeira, consentimento, FMCSA (dispatch x broker), escalonamento |
| [`05-system-prompt.md`](05-system-prompt.md) | **System prompt pronto (inglês)**, único para as duas vozes + lista de ferramentas |
| [`persona-config.yaml`](persona-config.yaml) | Configuração estruturada (vozes, idiomas, padrões, segurança) |
| [`fontes.md`](fontes.md) | Fontes da pesquisa |

## Decisões pendentes

| # | Decisão | Recomendação |
|---|---|---|
| 1 | Confirmar o modelo: motoristas com **MC próprio** contratando nosso dispatch (premissa deste documento) ou **leased-on** no nosso MC? | Se for leased-on, a relação muda (nós somos o carrier) e parte da matriz de decisões precisa ser revista |
| 2 | Idiomas no lançamento | EN + PT + ES |
| 3 | Nomes | **Laura** e **Daniel** (alternativas: Julia/Ana, Lucas/Marcos) |
| 4 | Nível de autonomia padrão | **Nível 2** (negocia, pergunta antes de fechar) |
| 5 | Taxa do serviço e exibição | Mostrar em cada oferta por padrão |
| 6 | Canal de mensagens | SMS + **WhatsApp** (muito usado por motoristas imigrantes) e/ou app próprio |
| 7 | Integrações de ELD (Samsara, Motive, etc.) | Essencial para respeitar o descanso e responder check calls |
| 8 | Humano de retaguarda: quem é e em que horários | 24/7 para emergências, mesmo que por plantão |
| 9 | Regra para quando a mesma carga serve a mais de um motorista | **Validar com advogado** (risco de "alocação de tráfego", ver [`04`](04-guardrails-seguranca.md) §5) |

## Impacto nos documentos da Megan (broker desk)

Como os motoristas são clientes com MC próprio, a Megan negocia **em nome de transportadoras diferentes** a cada ligação. Ajustes necessários em `agente-voz-brokers/`:

1. **`[CARRIER_NAME]`, `[MC_NUMBER]` e `[DOT_NUMBER]` viram variáveis por ligação** (`{{carrier_name}}`, `{{mc_number}}`, `{{dot_number}}`) no system prompt e no YAML.
2. **Resposta a "in-house or dispatch service?":** "We're [DISPATCH_CO], dispatching for {{carrier_name}}." (verdade)
3. **Piso de preço** = regras do motorista (rate mínimo dele), não um custo por milha da empresa.
4. **Autoridade para fechar** = nível de autonomia que o motorista escolheu.
5. **Verificação pelo broker:** cadastrar o telefone e o e-mail do nosso dispatch como **contatos autorizados** no cadastro de cada transportadora (Highway, MyCarrierPackets etc.). O broker vai checar o contato contra o FMCSA da transportadora.
6. **Guia da FMCSA sobre dispatch services** (jun/2023): incluir no checklist jurídico da Megan.
