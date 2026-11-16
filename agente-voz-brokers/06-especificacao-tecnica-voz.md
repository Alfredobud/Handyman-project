# 06 — Especificação técnica para escolher e configurar a ferramenta de voz

> Use este documento como **checklist de avaliação** dos fornecedores e como base de configuração.

---

## 1. Requisitos obrigatórios da plataforma

| # | Requisito | Meta | Por quê |
|---|---|---|---|
| 1 | **Latência voz-a-voz** (fim da fala do broker até o início da resposta) | **< 800 ms**, ideal ~500 ms | O broker é rápido e impaciente. Pausa longa denuncia robô e irrita |
| 2 | **Barge-in** (ser interrompida) | A fala para em < 300 ms quando o broker fala | Broker interrompe o tempo todo |
| 3 | **Endpointing ajustável** (detectar fim de turno) | Configurável. Não cortar o broker no meio de um número ("twenty-three… fifty") | Números ditos em partes |
| 4 | **ASR robusto a ruído** | Bom em sales floor barulhento, celular e viva-voz | Ambiente real do broker |
| 5 | **Vocabulário customizado / keyword boosting** | Cidades dos EUA, siglas de estados, nomes de brokerages, jargão (reefer, TONU, FCFS, lumper, Macropoint) | Evita "Joliet" virar "Juliet" e "Laredo" virar "La Reto" |
| 6 | **Reconhecimento de números e alfanuméricos** | Alta precisão para valores, MC, referências e horários | O erro mais caro possível |
| 7 | **TTS feminina natural** | Expressiva, ajuste de velocidade e estabilidade, dicionário de pronúncia (SSML ou equivalente) | Persona (ver [`02`](02-persona.md)) |
| 8 | **Function calling** em tempo real | Chamadas às ferramentas do [`05`](05-system-prompt.md) durante a ligação, sem silêncio longo (usar frase de transição: "one sec, pulling that up") | Dados verificados, nada inventado |
| 9 | **Variáveis dinâmicas por ligação** | Injeção de `{{variáveis}}` no prompt | Preço e caminhão mudam a cada ligação |
| 10 | **Telefonia própria / BYO number** | Usar o **número do [DISPATCH_CO]** como caller ID (cadastrado como contato autorizado de dispatch de cada transportadora cliente); suporte a STIR/SHAKEN (atestação A) e CNAM | Anti-fraude e anti-"Spam Likely" |
| 11 | **Transferência quente para humano** | Com sussurro/resumo para o humano | Escalonamento |
| 12 | **Detecção de caixa postal** | Detectar e deixar o recado do script | Muitas ligações caem em voicemail |
| 13 | **Gravação + transcrição + resumo** | Armazenamento, exportação e webhooks pós-ligação | CRM, auditoria, treinamento |
| 14 | **Analytics** | Métricas por ligação e testes A/B de voz e prompt | Melhoria contínua |
| 15 | **Termos de uso compatíveis** | Permitem ligações outbound B2B com divulgação de IA | Compliance |

**Desejáveis:**
- Espanhol como segundo idioma (fallback): há brokers e dispatchers hispânicos.
- Simulação/teste com "broker sintético" antes de ir para produção.
- Controle de emoção e entonação no TTS.

## 2. Plataformas a avaliar (sem endosso; verificar preços e termos atuais)

| Tipo | Exemplos | Observação |
|---|---|---|
| Plataformas genéricas de agente de voz | Retell AI, Vapi, Bland, Synthflow, ElevenLabs Agents | Máxima flexibilidade. Exigem montar as integrações (load board, TMS, preços) |
| Motores de voz (TTS) | ElevenLabs, Cartesia e outros | Escolher a voz da Megan aqui, mesmo usando outra plataforma de orquestração |
| Verticais de frete, lado do carrier | Numeo (VoiceFlow / Spot Finder), Hey Bubba | Já vêm com integrações de load board e lógica de frete. Verificar se permitem persona e regras próprias |
| Verticais de frete, lado do broker | HappyRobot, Parade, Vooma, FleetWorks | Feitas para brokers (o "outro lado"). Úteis para entender como a IA do broker se comporta |

## 3. Dicionário de pronúncia (configurar no TTS)

| Escrita | Falar como | Nota |
|---|---|---|
| TONU | "tah-noo" ou "T-O-N-U" | Testar com brokers; ambos são usados |
| FCFS | "F-C-F-S" ou "first come first serve" | — |
| reefer | "REE-fer" | — |
| Des Moines, IA | "duh-MOYN" | — |
| Boise, ID | "BOY-see" | — |
| Laredo, TX | "luh-RAY-doh" | — |
| Joliet, IL | "JOH-lee-et" | — |
| Ontario, CA | "on-TAIR-ee-oh" (cidade da Califórnia) | Não confundir com a província canadense |
| Louisville, KY | "LOO-uh-vul" | — |
| New Orleans, LA | "new OR-lunz" | — |
| Valores | US$ 2.350 → "twenty-three fifty"; US$ 3,10/mi → "three-ten a mile" | Normalizar antes do TTS |
| MC 1234567 | "M-C one-two-three, four-five-six-seven" | Grupos com micro-pausas |
| 08:00 CT | "eight a.m. Central" | Sempre com fuso |

## 4. Protocolo de escolha da voz

1. Pré-selecionar 4–6 vozes femininas (General American, aparência de 30–40 anos, pitch médio a médio-grave).
2. Gerar o **roteiro de audição** de [`02`](02-persona.md) §3 com cada uma, **pela linha telefônica** (8 kHz, celular). Uma voz linda em estúdio pode ficar ruim no telefone.
3. Teste cego com 3–5 pessoas do ramo (dispatchers ou brokers conhecidos). Notas de 1 a 5 para: natural, confiável, experiente, clareza dos números, "eu negociaria com ela?".
4. Escolher 1 principal + 1 reserva. Escolher também 1 voz masculina equivalente para o teste A/B.

## 5. KPIs (painel do agente)

| KPI | Definição | Uso |
|---|---|---|
| Taxa de contato | Ligações atendidas / discadas | Qualidade de caller ID e horários |
| Desligamento em até 15 s | Desligou logo após a abertura | Efeito da voz e da divulgação de IA |
| Taxa de booking | Cargas fechadas / ligações com carga disponível | Eficácia geral |
| **Uplift sobre o posted** | (valor fechado − rate postado) / rate postado | Valor gerado pela negociação |
| US$/mi vs média DAT | Valor fechado / média da lane | Qualidade do preço |
| Concessão média | Âncora − valor fechado | Disciplina na escada |
| Tempo médio de ligação | — | Meta: 2–4 min |
| Taxa de escalonamento | Ligações transferidas a humano | Ajuste de autonomia |
| Erros de dados | Divergência entre rate con e acordo falado | Precisão de ASR e read-back |
| Fall-offs | Cargas fechadas que não rodaram | Confiabilidade (precisa ser ~0) |
| Brokers recorrentes | % de brokers que voltam a dar carga | Relacionamento |

## 6. Testes A/B planejados

1. **Voz:** feminina (Megan) × masculina equivalente
2. **Divulgação de IA:** redação A × redação B (sempre com divulgação)
3. **Âncora:** alvo +8% × alvo +12% × alvo +15%
4. **Estilo de abertura:** pergunta direta × menção ao caminhão já na abertura ("I've got a van empty right there in Dallas…")

Mínimo de ~200–300 ligações por variante antes de decidir. Mudar uma variável por vez.

## 7. Plano de implantação em fases

| Fase | O que acontece | Critério para avançar |
|---|---|---|
| **0. Simulação** | Agente negocia contra "brokers sintéticos" (outra IA com os arquétipos A–F de [`01`](01-perfil-brokers-e-dispatchers.md)) e contra humanos da equipe fazendo papel de broker | 50+ simulações sem violar hard rules; read-back 100% correto |
| **1. Sombra** | Humano liga; a IA escuta e sugere em tempo real | Sugestões da IA ≥ decisões humanas na maioria dos casos |
| **2. IA com aprovação** | IA liga e negocia; **humano aprova antes de confirmar o booking** | 2 semanas sem incidentes; uplift ≥ humano |
| **3. Autônoma com guardrails** | IA fecha sozinha para motoristas no nível 3 de autonomia (dentro das regras deles); nos níveis 1–2 pede o "sim" do motorista | Monitoramento contínuo dos KPIs |
