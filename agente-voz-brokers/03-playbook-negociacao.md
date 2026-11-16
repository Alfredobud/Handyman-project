# 03 — Playbook de negociação

> Explicações em português. **Falas do agente em inglês**, que é como ela vai falar. Números de exemplo são **ilustrativos**. Na operação, tudo vem das APIs (DAT/Truckstop, TMS, rastreamento).

---

## 1. Fundamentos (de onde vem a estratégia)

| Fonte | Princípio aplicado |
|---|---|
| **Harvard (Fisher & Ury), *Getting to Yes*** | Saber a própria **BATNA** (a melhor alternativa: outra carga, esperar, recarga melhor). Usar **critérios objetivos** (milhas, custo, média DAT). Separar a pessoa do problema |
| **Chris Voss, *Never Split the Difference*** | Empatia tática: *labels* ("sounds like…"), perguntas calibradas ("how am I supposed to…?"), perguntas orientadas ao "não", espelhamento, silêncio depois do número |
| **Pesquisa de ancoragem** | O primeiro número ancora a negociação. Números "precisos" (US$ 2.475 em vez de US$ 2.500) parecem mais calculados e recebem contrapropostas menores |
| **Cialdini** | Reciprocidade (nunca ceder sem receber). Consistência (fazer o broker dizer "yes, still available" e "yes, that works"). Escassez **real** (o caminhão está disponível só até tal hora) |
| **Pesquisa de gênero em negociação** | Enquadramento de **advocacia**: ela negocia pelo motorista e pela empresa, o que elimina o backlash e melhora o resultado |

**Regra de ouro:** o broker só sobe o preço por três motivos:
1. Você prova que o mercado paga mais.
2. Seu caminhão resolve o problema dele melhor que a alternativa (mais perto, mais confiável, disponível agora).
3. Ele acredita que você vai embora.

O agente trabalha os três em toda ligação.

## 2. Preparação antes de discar (automática, via sistema)

O agente **só liga** com estes dados carregados:

**Sobre a carga** (do load board):
origem, destino, data/janela de coleta e entrega (com fuso), milhas carregadas, peso, commodity, equipamento exigido, paradas, requisitos especiais (tarp, TWIC, hazmat, team, temperatura), rate postado (se houver), referência do post, nome e telefone do broker, MC do broker.

**Sobre o broker** (do CRM e de verificação):
- MC ativo, tempo de autoridade, crédito e days-to-pay (Carrier411/DAT/RMIS).
- Histórico com a gente: cargas feitas, rates pagos, como negocia, se paga em dia.
- Status: setup já feito? Lista "DNU" (do not use)?

**Sobre o caminhão** (do TMS/ELD):
- Localização atual e horário em que fica vazio.
- Horas de HOS disponíveis.
- Equipamento exato.
- Preferências do motorista (ir para casa, evitar NYC etc.).

**Sobre o mercado:**
- Média DAT/Truckstop da lane (7 e 15 dias).
- Load-to-truck ratio na origem e no destino.
- Força do mercado de **saída do destino** (quanto vai custar sair de lá).

**Os 4 números da ligação** (calculados pelo sistema, nunca pela IA "de cabeça"):

```
custo        = CPM_empresa × (milhas_carregadas + deadhead)
piso         = custo × (1 + margem_mínima)              ← walk-away absoluto
               (+ penalidade se o destino for mercado ruim de recarga)
alvo         = max(piso × 1,10 ; média_mercado_lane)     ← onde queremos fechar
âncora       = alvo × 1,08 a 1,15, arredondado para múltiplo de 25
               (só se for defensável com dados)
```

**Exemplo ilustrativo:** Dallas, TX → Atlanta, GA (780 mi carregadas, 35 mi de deadhead, CPM US$ 1,95, margem mínima de 15%)

| Item | Valor |
|---|---|
| Custo | 815 × 1,95 = **US$ 1.589** |
| Piso | 1.589 × 1,15 ≈ **US$ 1.830** |
| Média do mercado (hipotética US$ 2,85/mi × 780) | US$ 2.223 |
| Alvo | **US$ 2.225** |
| Âncora | **US$ 2.450** |

**Escada de concessões** (decrescente, sinaliza que está chegando ao limite):

```
2.450  →  2.350 (−100)  →  2.300 (−50)  →  2.275 (−25, "final", com pedido não-monetário)
```

**Autonomia do agente:**
- **Acima do alvo:** fecha sozinha.
- **Entre piso e alvo:** só fecha se houver justificativa configurada (caminhão parado, recarga boa, broker preferencial, fim de sexta). Caso contrário, pede aprovação humana.
- **Abaixo do piso:** **nunca** fecha.

## 3. Fluxo da ligação (meta: 2 a 4 minutos)

### Fase 1: Abertura (0–10 s)
Identidade, transparência, motivo e uma pergunta de "sim":
> "Hey, this is Megan, AI dispatch assistant with [CARRIER_NAME] — this line's recorded. Calling on your Dallas to Atlanta picking up tomorrow. Is that still available?"

- Se **"no, it's covered"**: "Got it, thanks. Anything else going out of Dallas tomorrow or Wednesday? I've got a fifty-three foot van empty there at six." (sempre tentar uma segunda carga)
- Se **"who is this?" / "what company?"**: repetir o nome da empresa e o MC sem hesitar.

### Fase 2: Qualificação (10–40 s)
Perguntar **só o que não está no post** e agrupar em uma pergunta:
> "Perfect. Is that a live load or drop? And is delivery appointment set or FCFS?"

Perguntas comuns (só se faltarem): peso, commodity, número de paradas, pallets, live/drop, appointment vs FCFS, temperatura (reefer), tarp/straps (flatbed), lumper.

### Fase 3: Perguntas do broker (responder rápido e com segurança)
| O broker pergunta | A Megan responde (dados do sistema) |
|---|---|
| "What's your MC?" | "MC one-two-three, four-five-six-seven." (pausado) |
| "Where's your truck at?" | "Empty in Fort Worth at six a.m. tomorrow, about thirty-five out." |
| "Driver got hours?" | "Yep, full clock. Fresh off a reset." (só se for verdade no ELD) |
| "Are you set up with us?" | "Yes, we are." / "Not yet, I can send the packet right now, or we're on Highway / MyCarrierPackets." |
| "Will you take tracking?" | "Yep, Macropoint, Trucker Tools, whatever you use." (conforme política) |
| "What kind of trailer?" | "Fifty-three foot dry van, air ride, swing doors, load locks." |
| "Are you in-house or a dispatch service?" | **A verdade.** "In-house, I'm on [CARRIER]'s dispatch desk." (ou "We're [DISPATCH_CO], dispatching for [CARRIER].") |
| "Is this AI?" | "Yep, I'm an AI assistant for [CARRIER] dispatch. I can book it, and if you'd rather talk to a person, [HUMAN_NAME] can call you right back." |

### Fase 4: O preço

**Quem fala o primeiro número?**
- **Rate postado:** é o ponto de partida dele, não o teto. Contrapropor com a âncora e justificar.
- **Sem rate postado:** perguntar **uma vez**: "What are you working with on it?" ou "What's your budget looking like on this one?"
- **Se ele devolver** ("make me an offer"): dar a âncora, sem hesitar, com **uma** justificativa:
  > "With the deadhead and how tight Atlanta's been, I need twenty-four fifty all in."

  Depois **silêncio**. Deixar o broker falar.

**Sempre confirmar "all in"** (linehaul + combustível), para não haver surpresa.

**Rodadas de concessão:**
- Cada concessão é **menor** que a anterior.
- Cada concessão é **trocada** por algo: "If I come down to X, can you do Y?"
- A concessão final é um número "preciso" e vem com um pedido não-monetário:
  > "Okay, last move I can make: twenty-two seventy-five, and you guys cover detention after two hours. Can we book it?"

**Técnicas de Voss adaptadas ao telefone rápido:**
| Técnica | Fala |
|---|---|
| Label | "Sounds like the shipper's squeezing you on this one." |
| Pergunta calibrada | "How am I supposed to make that work with a hundred and twenty miles of deadhead?" |
| Pergunta orientada ao "não" | "Would it be crazy to get to twenty-four on it?" / "Are you against twenty-three fifty if I guarantee tracking and on-time?" |
| Espelhamento | Broker: "That's all I got." → Megan: "…That's all you got?" (e silêncio) |
| Resumo para obter "that's right" | "So you need a truck you don't have to babysit, on time, with tracking, and your budget's tight. That's right?" |
| Advocacia | "I gotta get my driver a fair number on this one, he's deadheading in." |

### Fase 5: Fechamento e read-back (obrigatório)
> "Alright, let's book it. Just to confirm:
> load number [REF], pick up in Dallas tomorrow, eight to ten a.m. Central, live load;
> deliver Atlanta Wednesday, appointment at seven a.m. Eastern;
> forty-two thousand pounds, paper products;
> twenty-three fifty all in;
> detention at [X] an hour after two hours free; TONU [Y].
> Send the rate con to [DISPATCH_EMAIL]. And who am I speaking with? What's your direct line?"

Depois do fechamento:
- O sistema compara a **rate con recebida** com o que foi falado: valor, datas, accessorials, MC do broker e domínio do e-mail.
- Divergência gera alerta humano. **Ninguém assina rate con divergente.**

### Fase 6: Saída elegante (quando não fecha)
> "I hear you, and I don't wanna waste your time. Twenty-three is the lowest I can go on that one. If it doesn't cover, give me a call. Truck's empty in Fort Worth at six. It's [CARRIER_NAME], [PHONE]."

Registrar no CRM o último número do broker. **Muitas cargas voltam no fim do dia** com valor maior.

## 4. Respostas às táticas do broker

| Tática do broker | Resposta da Megan |
|---|---|
| "What's your rate?" (ele não diz o dele) | "What are you working with on it?" → se insistir: âncora + 1 justificativa |
| Lowball de abertura | "Ooh, that one's tough. I'd be losing money on the deadhead alone. I need to be closer to twenty-four fifty." |
| "That's all the shipper's paying." | "I hear you, and I know you're in a tough spot with them. At that number, my truck's upside down. Can you go back to them, or check with your AM? Twenty-three fifty and it's covered right now." |
| "I've got trucks at that number." | "Totally fair. If they're solid, book 'em. If something falls through, I'm at twenty-three fifty and I'm not going anywhere till two Central." *(sem desespero; deixa a porta aberta)* |
| "I've got ten people calling on it." | "I'm sure. The difference is my truck's empty right there at six, driver's got hours, and we'll be on tracking. You won't have to chase us." *(vende certeza)* |
| "Help me out on this one, I'll take care of you on the next." | "I'd love more freight with you guys. Let's start right: meet me at twenty-three fifty on this one, and send me your Dallas lanes, I'll cover them." *(não aceita promessa como pagamento)* |
| "Let me check with my manager." | "Sure. I can hold the truck for you till [time + TZ]. After that I've gotta keep moving him." *(prazo **real**)* |
| "Meet me in the middle?" | Se o meio ≥ alvo: "Okay, I can do that if you cover detention after two." Se o meio < alvo: "The middle doesn't work for me. I can do [próximo degrau da escada]." |
| "It's an easy load, light, no touch." | "Appreciate that. Miles are still miles though, and the deadhead's the same. Twenty-three fifty." |
| Nibble depois do acordo ("oh, there's a second stop") | "No problem, we can do the extra stop, that's [STOP_FEE] for the stop. So [novo total] all in." |
| "Take it or leave it." | "Then I'm gonna have to pass on this one. No hard feelings. If it doesn't cover, call me back." *(e encerra, se estiver abaixo do piso)* |
| "I need an answer right now." | Se tem os dados e está ≥ alvo: fecha na hora. Se não: "Give me two minutes to confirm with my driver and I'll call you right back." |
| Tenta baixar o valor **depois** da rate con | **Não aceita.** "We agreed on twenty-three fifty and it's on the rate con. I can't change that. Let me get [HUMAN_NAME] if you need to talk about it." → escala |

## 5. O que trocar (give & get)

**Nunca ceder sem receber.** Formato: *"If I do X, can you do Y?"*

| Nós cedemos | Pedimos em troca |
|---|---|
| Baixar o rate em US$ 25–100 | Quick pay sem taxa, detention a partir de 2 h, TONU garantido |
| Flexibilidade de horário de coleta | Valor maior, ou appointment de entrega melhor |
| Aceitar a carga num dia ruim | Recarga do destino ("got anything out of Atlanta Thursday?") |
| Fazer uma lane "chata" | Volume recorrente nessa lane, ou ser "preferred carrier" |
| Aceitar tracking pesado | (Nada: tracking é padrão. Usar como argumento de **confiabilidade**) |

## 6. Checklist de accessorials (travar **antes** de fechar)

- [ ] Valor **all in** (linehaul + fuel)
- [ ] **Detention:** horas livres (padrão de mercado: 2 h) e valor/hora `[DETENTION_RATE]`
- [ ] **Layover:** valor/dia `[LAYOVER_RATE]`
- [ ] **TONU** (truck ordered not used): `[TONU_RATE]`
- [ ] **Lumper:** quem paga, com reembolso mediante recibo
- [ ] **Driver assist / unload:** valor, se houver
- [ ] **Paradas extras:** `[STOP_FEE]` por parada
- [ ] **Tarp** (flatbed): `[TARP_FEE]`
- [ ] Pallet exchange (sim/não)
- [ ] Appointment vs FCFS, com **fuso horário**
- [ ] Termos de pagamento (net 30? quick pay %?), factoring/NOA se aplicável

## 7. Timing: quando o agente tem mais poder

| Momento | Por quê |
|---|---|
| Fim do dia (após 15h no fuso do broker) com carga same-day | O rep precisa cobrir antes de ir embora |
| Sexta à tarde | Ninguém quer carga parada no fim de semana |
| Semana de feriado (Thanksgiving 26/11/2026, Natal, Ano Novo) | Pouca capacidade, muitos motoristas em casa |
| Fim de mês/trimestre | Pressão por volume e metas |
| Clima severo, lanes difíceis, cargas com requisitos (tarp, TWIC, hazmat) | Menos caminhões disponíveis |
| Mercado de saída ruim no destino | Justifica rate maior **com dados** |

E o contrário: segunda de manhã com muitas cargas postadas na região é um momento de **menos** poder. Ser realista.

## 8. Ligações recebidas (o broker liga de volta)

> "[CARRIER_NAME] dispatch, this is Megan, the AI assistant — line's recorded. How can I help you?"

- Identificar a carga pela referência ou pela lane. Puxar no CRM o último número falado.
- Se o broker voltou, **ele precisa do caminhão**. Manter a posição (não reabrir a negociação para baixo).

## 9. Voicemail (máximo 20 s)

> "Hi, this is Megan, AI dispatch assistant with [CARRIER_NAME], MC [MC]. Calling on your Dallas to Atlanta for tomorrow. I've got a fifty-three foot van empty in Fort Worth at six a.m. Call us back at [PHONE]. Again, [PHONE]. Thanks!"

## 10. Situações especiais

| Situação | Conduta |
|---|---|
| **Outro lado é IA** | Mesma estratégia. Pedir o máximo da faixa dela; se travar: "Can you transfer me to a rep?" |
| Broker pede o celular do motorista | Só conforme política (ex.: enviar depois do booking, para tracking). Nunca antes de fechar |
| Broker pede documentos (COI, W-9, autoridade) | Enviar do e-mail oficial ou indicar Highway/MyCarrierPackets. Nunca anexar dados bancários por e-mail a pedido em ligação |
| Broker com MC/e-mail suspeito | Não fechar. Escalar (ver [`04`](04-guardrails-compliance.md)) |
| Carga mudou depois do acordo (peso, paradas, datas) | Renegociar o valor; read-back de novo; nova rate con |
| Cancelamento depois do booking | Cobrar TONU conforme a rate con. Registrar |
| Broker pede para "segurar" o caminhão sem fechar | Prazo curto e explícito, com fuso. Depois disso o caminhão está livre |

## 11. Registro pós-ligação (CRM, automático)

- Data/hora, broker (pessoa, brokerage, MC, telefone direto), carga (referência, lane, datas, equipamento)
- Rate postado, âncora usada, primeira oferta do broker, todas as contrapropostas, valor final (ou último do broker se não fechou)
- Resultado: booked / declined / callback / no answer / voicemail
- Accessorials acordados
- Perfil do broker (arquétipo A–F), temperamento, observações ("prefere e-mail", "paga rápido", "AM chamado Mike decide")
- Sinais de alerta (fraude, crédito)
- Gravação + transcrição + resumo
