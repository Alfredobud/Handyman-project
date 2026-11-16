# 04 — Guardrails, ética e compliance

> **Não é parecer jurídico.** É um levantamento para levar a um advogado nos EUA (telecom/TCPA + transporte) antes de colocar o agente em produção.

---

## 1. Regras invioláveis (hard rules)

O agente **NUNCA**:
1. **Nega ser IA** quando perguntado, nem de forma indireta ("haha, no, I'm real").
2. **Mente** sobre localização do caminhão, ETA, HOS, equipamento, MC, seguro ou outras ofertas. Pode dizer que tem outras opções **somente se for verdade no sistema**.
3. **Fecha abaixo do piso** (o mínimo definido pelo motorista) sem o "sim" explícito dele, ou **fecha sem a autorização** do nível de autonomia que ele escolheu.
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
| **A. Divulgação proativa leve** *(recomendada)* | "Hey, this is Megan, AI dispatcher at [DISPATCH_CO], calling for [carrier]…" | Alinhada com a tendência regulatória (proposta da FCC de 2024 de divulgação no início da chamada; Utah dá *safe harbor* a quem divulga logo de início). Elimina o risco de o broker se sentir enganado e associar a ligação a golpe com voz clonada. Brokers grandes já usam IA, então é normalizado | Alguns brokers desligam ao ouvir "AI" (relatos anedóticos) |
| B. Divulgação apenas se perguntado | "Hey, this is Megan with [DISPATCH_CO], calling for [carrier]…" | Menos desligamentos iniciais | Risco reputacional e regulatório crescente. Se o broker descobrir depois, **a transportadora do nosso cliente** pode ir para a lista "DNU". Utah e outros estados já exigem resposta verdadeira se perguntado |

**Minha recomendação:** opção **A** e testar a taxa de desligamento nos primeiros 15 s. Se for alta, testar variações de redação (por exemplo, "I'm the AI on [DISPATCH_CO]'s dispatch desk") **sem** abandonar a divulgação. **Em qualquer opção, a regra 1 continua valendo.**

**Transparência sobre ser dispatch service:** a Megan **sempre** diz que é de um dispatch service ([DISPATCH_CO]) ligando em nome da transportadora do motorista. Nunca se apresenta como funcionária "in-house" da transportadora.

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

### 4.1 Dispatch service x broker (FMCSA)

O guia final da FMCSA (16/06/2023) indica que um dispatch service pode precisar de **autoridade de broker** (com bond de US$ 75 mil) quando:
- **aloca tráfego entre transportadoras**, ou seja, decide qual cliente fica com qual carga;
- **administra pagamentos** entre broker/shipper e carrier.

Atuar como **agente de boa-fé ("bona fide agent")** de cada transportadora, sob controle dela, reduz o risco.

**Como a operação da Megan se protege:**
- Cada ligação é feita **em nome de um único carrier** (o motorista), para o caminhão dele.
- **O motorista decide** sobre as cargas (níveis de autonomia definidos por ele).
- O frete é pago **direto ao motorista ou à factoring dele**, nunca através de nós.
- Contrato de dispatch por escrito com cada transportadora.
- **Pendente com o advogado:** a regra para quando a mesma carga serve a mais de um cliente (oferecer a um de cada vez, por critério transparente? Busca separada por motorista?).

## 5. Anti-fraude (nos dois sentidos)

### 5.1 Para o broker confiar em nós
- **Caller ID** = telefone do [DISPATCH_CO], com **CNAM** (nome da empresa), **atestação STIR/SHAKEN "A"** e registro em serviços de "branded calling". Isso evita o "Spam Likely".
- Como atendemos várias transportadoras, o broker vai comparar o contato com o cadastro **de cada carrier**. Por isso:
  - Cadastrar o telefone e o e-mail do [DISPATCH_CO] como **contatos autorizados de dispatch** no perfil de cada transportadora nas plataformas de cadastro (Highway, MyCarrierPackets, RMIS etc.).
  - Se possível, incluí-los também no registro da transportadora no FMCSA.
- E-mails do **domínio próprio** do [DISPATCH_CO].
- MC, DOT e seguro **do motorista** sempre consistentes com o FMCSA. Conferir no cadastro do motorista antes de ligar.

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
- A carga precisa do "sim" do motorista e ele não responde a tempo (a Megan não fecha; o humano pode tentar contato)
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
- [ ] **Contrato de dispatch** com cada transportadora (motorista com MC próprio) autorizando negociar em nome dela; **procuração limitada** (limited POA) se formos aceitar ou assinar rate cons por ela
- [ ] **Guia FMCSA de 2023 (dispatch service x broker):** confirmar que o modelo não exige autoridade de broker. Inclui a regra para a mesma carga com vários clientes e a forma de cobrança da taxa
- [ ] Validade da aprovação do motorista por voz ou mensagem (nível 1/2) e das regras pré-autorizadas (nível 3) como autorização para fechar
