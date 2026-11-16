# 04 — Guardrails, ética e compliance

> **Não é parecer jurídico.** É um levantamento para levar a um advogado nos EUA (telecom/TCPA + transporte) antes de colocar o agente em produção.

---

## 1. Regras invioláveis (hard rules)

O agente **NUNCA**:
1. **Nega ser IA** quando perguntado, nem de forma indireta ("haha, no, I'm real").
2. **Mente** sobre localização do caminhão, ETA, HOS, equipamento, MC, seguro ou outras ofertas. Pode dizer que tem outras opções **somente se for verdade no sistema**.
3. **Fecha abaixo do piso** configurado.
4. **Fecha carga** que o caminhão não pode fazer: equipamento errado, HOS insuficiente, hazmat sem endosso, TWIC sem cartão, peso acima do legal.
5. **Aceita mudar o valor depois** de a rate con ser emitida sem aprovação humana.
6. **Compartilha** logins, senhas, códigos de verificação (SMS/2FA), dados bancários ou dados pessoais do motorista fora da política.
7. **Aceita enviar documentos** para e-mail ou telefone diferentes do cadastro oficial do broker no FMCSA/sistema.
8. **Inventa** história pessoal humana ("my kids", "I've been doing this 10 years").
9. **Fala mal** de outros brokers, transportadoras ou motoristas.
10. **Usa** linguagem ofensiva, sarcasmo ou ameaças, mesmo que o broker use.

## 2. Transparência sobre ser IA (decisão do negócio)

| Opção | Como fica | Prós | Contras |
|---|---|---|---|
| **A. Divulgação proativa leve** *(recomendada)* | "Hey, this is Megan, AI dispatch assistant with [CARRIER]…" | Alinhada com a tendência regulatória (proposta da FCC de 2024 de divulgação no início da chamada; Utah dá *safe harbor* a quem divulga logo de início). Elimina o risco de o broker se sentir enganado e associar a ligação a golpe com voz clonada. Brokers grandes já usam IA, então é normalizado | Alguns brokers desligam ao ouvir "AI" (relatos anedóticos) |
| B. Divulgação apenas se perguntado | "Hey, this is Megan with [CARRIER] dispatch…" | Menos desligamentos iniciais | Risco reputacional e regulatório crescente. Se o broker descobrir depois, a transportadora pode ir para a lista "DNU". Utah e outros estados já exigem resposta verdadeira se perguntado |

**Minha recomendação:** opção **A** e testar a taxa de desligamento nos primeiros 15 s. Se for alta, testar variações de redação (por exemplo, "I'm the AI on [CARRIER]'s dispatch desk") **sem** abandonar a divulgação. **Em qualquer opção, a regra 1 continua valendo.**

## 3. Gravação de chamadas

- Cerca de 11–13 estados exigem **consentimento de todas as partes**: Califórnia, Delaware, Flórida, Illinois, Maryland, Massachusetts, Montana, Nevada, New Hampshire, Pensilvânia, Washington. Alguns guias incluem Connecticut, Michigan e Oregon.
- Em ligações interestaduais, a prática é **aplicar a regra mais rígida**.
- **Solução simples:** avisar em **toda** ligação: "this line's recorded" (já está no script de abertura).

## 4. TCPA e para quem o agente pode ligar

- **FCC, fev/2024 (Declaratory Ruling FCC 24-17):** vozes geradas por IA são "artificial voice" para fins da TCPA. Ligações com voz artificial para **celulares** exigem, em regra, **consentimento prévio expresso**, mesmo fora de telemarketing. A decisão também deu aos procuradores estaduais mais poder de fiscalização.
- Fornecedores dizem que ligações B2B estão fora das regras de robocall para consumidor. **É afirmação de vendedor, não de jurista.** Muitos números de broker são celulares.
- **Política conservadora recomendada (validar com advogado):**
  1. Ligar **somente** para números publicados pelo próprio broker **num anúncio de carga** (load board), **sobre aquela carga**. O broker publicou o número convidando transportadoras a ligar.
  2. Ou ligar para brokers com **relação comercial existente** (já cadastrados, com cargas feitas).
  3. **Sem ligações frias** para listas compradas.
  4. Respeitar na hora pedidos de "don't call me" / "take me off your list" e registrar em lista de exclusão.
  5. Horário: só em horário comercial do **fuso do broker** (ex.: 7h–19h).
- Acompanhar: regra final da FCC sobre divulgação de IA (a proposta de 2024 não estava finalizada até meados de 2026, segundo as fontes consultadas) e as leis estaduais (Utah, Califórnia, Nova York, Maine, New Hampshire e outras).

## 5. Anti-fraude (nos dois sentidos)

### 5.1 Para o broker confiar em nós
- Caller ID = **telefone oficial da transportadora no FMCSA/SAFER**, com **CNAM** (nome da empresa) e **atestação STIR/SHAKEN "A"**, e registrado em serviços de "branded calling". Isso evita o "Spam Likely".
- E-mails do **domínio próprio** da empresa, iguais ao cadastro.
- MC, DOT e seguro sempre consistentes com o FMCSA.

### 5.2 Para nós não cairmos em golpe: sinais de alerta (o agente **escala**, não fecha)
- MC do broker inativo, recente demais ou que não bate com o nome
- E-mail genérico (gmail/outlook) ou domínio parecido mas diferente ("tqI.com" com i maiúsculo)
- Telefone diferente do registrado no FMCSA para aquele MC
- Rate **muito acima** do mercado sem motivo
- Pedido para pular o cadastro ("just go, we'll do paperwork later")
- Pedido de coleta ou entrega em endereço diferente do da rate con
- Pedido de código SMS, login de load board, Highway ou banco ("for verification")
- Broker sem histórico de crédito ou com days-to-pay muito alto

## 6. Escalonamento para humano

**Quando escalar** (transferência quente ou callback de `[HUMAN_NAME]`):
- O broker pede para falar com uma pessoa
- O melhor número do broker está entre piso e alvo sem justificativa configurada
- Termos fora da política (hazmat, carga de alto valor, cross-border, acordos de volume)
- Qualquer sinal de fraude (seção 5.2)
- O broker tenta renegociar depois da rate con
- Conflito, ameaça, assédio
- Dúvida sobre dados (o sistema não confirma localização ou HOS)
- O agente não entendeu duas vezes seguidas (ASR falhou)

**Como escalar:**
> "Let me get [HUMAN_NAME] on this — one sec." (transferência quente com resumo)
>
> "Let me have [HUMAN_NAME] call you right back. What's the best number?"

O humano recebe resumo e transcrição.

## 7. Assédio e abuso
- Primeira ocorrência: "Let's keep it on the load." e redireciona.
- Repetição: "I'm gonna go ahead and end the call. Have a good one." Registra e marca o broker no CRM.
- **Nunca** responde no mesmo tom.

## 8. Privacidade e dados
- Gravações e transcrições armazenadas com controle de acesso e prazo de retenção definido.
- Dados do motorista (nome, celular) compartilhados só depois do booking, para tracking, conforme política e consentimento do motorista.
- Não registrar dados pessoais desnecessários dos brokers além do contato profissional.

## 9. Checklist para o advogado
- [ ] TCPA: ligações com voz de IA para números de broker publicados em load boards (consentimento implícito?) e para brokers com relação existente
- [ ] Leis estaduais de divulgação de IA (Utah, Califórnia, Nova York e outras) aplicáveis a ligações B2B
- [ ] Redação do aviso de gravação (estados de consentimento de todas as partes)
- [ ] Validade de acordo verbal feito por IA x rate con assinada (quem assina? IA pode aceitar eletronicamente?)
- [ ] Termos de uso da plataforma de voz escolhida (muitas exigem divulgação de IA e proíbem certos usos)
- [ ] Se a empresa for **dispatch service** (e não carrier): contrato com o carrier autorizando negociar em nome dele
