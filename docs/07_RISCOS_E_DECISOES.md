# Registro de riscos e decisões

Duas coisas neste documento: o **registro de riscos** (o que pode dar errado e o que fazemos
a respeito) e o **log de decisões** (o que decidimos, quando, por quê — e o que mudou de
ideia depois).

Pendências executáveis que atravessam fases, mas não são riscos nem entregáveis de uma camada
futura, ficam em `12_PENDENCIAS_TRANSVERSAIS.md`. Os dois registros se referenciam sem duplicar
responsabilidade: risco descreve incerteza/impacto; pendência descreve ação e critério de
encerramento.

O log de decisões é a defesa contra a versão mais insidiosa de overfitting: mudar o desenho
depois de ver o resultado e depois contar a história como se o desenho sempre tivesse sido
aquele. **Toda mudança de desenho posterior ao congelamento entra aqui, com data.**

---

## Parte I — Registro de riscos

Probabilidade × Impacto, com dono e mitigação. Ordenado por severidade.

| # | Risco | Prob. | Impacto | Mitigação | Status |
|---|---|---|---|---|---|
| R1 | **N efetivo pequeno** — o sinal operacional começa em 2015/16 e H1a depende do painel iniciado em 2017/18; linhas UF×cultura não viram eventos independentes. Sem poder estatístico para efeito pequeno | Alta | Alto | Primário combina soja e milho 2ª em painel de UFs, mas inferência continua agrupada por ano-safra; block bootstrap; **reportar N efetivo por teste**. Outras culturas não são adicionadas só para fabricar N | 🔴 **Sem solução. É a limitação nº 1 e vai declarada no relatório** |
| R2 | **A estratégia ser só beta de commodity** (H4) | Média | Existencial | Dollar-neutral não garante cancelamento; medir betas residuais e executar o *spanning* pré-registrado | Aberto — decide-se no teste |
| R3 | **Contaminação por revisão dos dados climáticos** — POWER/ERA5 sobrescrevem o passado | **Confirmada** | Alto | CHIRPS prelim arquivado é o único canal primário (D-023); comparar prelim/final. POWER só em robustez térmica | ✅ Mitigado no primário. **Temperatura secundária segue exposta** |
| R4 | **Viés de sobrevivência do universo** — JBSS3, BRFS3, MRFG3, STBP3 sumiram em 2025 e o yfinance os apagou | **Confirmada** | Alto | **COTAHIST** (registro de pregão da B3) como fonte de universo e preço — delisting-proof por construção | ✅ Resolvido |
| R5 | **Ajuste de proventos no COTAHIST** — preços não vêm ajustados por dividendos/splits | Alta | Alto | Motor PIT, três fontes, montador e auditoria dos 19 papéis vivos (D-014–D-016/D-025). Cross-check encontrou bonificações SLC/VITT/KLABIN, repetição de classes e parcelas iguais legítimas. Residual: deslistados sem Yahoo e defeitos do próprio Yahoo | ✅ **Resolvido**, residual declarado |
| R6 | **Sinal ser ENSO disfarçado** (H5) | Média | Alto | ONI como controle; placebo espacial | Aberto — decide-se no teste |
| R7 | **Universo fundamental direto é estreito** — quatro nomes de grãos no teste primário e SMTO3 como satélite de evidência inferior | **Confirmada** | Alto | Não fabricar exposição; teste primário restrito aos quatro grãos; caps 0,40/0,15 e redução de bruto quando necessário (D-053). Método B só como robustez identificada | 🟡 Estrutura resolvida; poder e concentração seguem como limitações |
| R8 | **Short inviável** em small caps agrícolas (sem doador / aluguel caro) | Média | Médio | D-055 exige evidência B3 PIT em 5 pregões, posição ≤1% do estoque alugado e custo com piso de 5% a.a.; se qualquer short falhar, o bloco inteiro não abre. Long-only não resgata o primário | 🟡 Regra e código resolvidos; custo histórico via proxy conservadora declarada (D-058), não medição |
| R9 | **Capacidade baixa** — estratégia pode não suportar capital relevante | Alta | Baixo (acadêmico) | D-055 fixa AUM de R$500 mil, ADTV21 ≥R$8 mi, ordem ≤5% do ADTV e short ≤1% do estoque alugado; reportar mínimo/P10/mediana | 🟡 ADTV real medido (AGRO3 sempre abaixo do piso no dev); custo do short via proxy declarada (D-058) |
| R10 | **Erro de data no calendário CONAB** — o arquivo não traz a data de divulgação dos levantamentos | Média | Alto (contamina o estudo de evento) | Mapa curado ano a ano de fontes primárias, com ≥2 fontes concordando na quase totalidade (D-017); zero interpolação; carimbo falha alto fora do mapa. O risco se materializou na coleta: o próprio site da CONAB exibe datas falsas para 2022/23 | ✅ **Resolvido operacionalmente**; reforço das poucas datas com fonte única em PT-005 |
| R11 | **Bug de sinal invertido** — tratar frigorífico como produtor | Baixa | Existencial (silencioso!) | Teste unitário travando a convenção de sinal; checklist de revisão de PR | Mitigado por automação |
| R12 | **Rate limit / instabilidade das APIs públicas** | Média | Baixo | Cache local agressivo; pipeline nunca depende de rede em tempo de execução | Mitigado |
| R13 | **ONI histórico contaminado por revisão** — a NOAA sobrescreve valores recentes e atualiza a base centrada a cada cinco anos | Confirmada | Médio | Captura datada + hash; caso primário espera a janela declarada de 2 meses; sensibilidade com publicação inicial e RONI | Mitigado parcialmente. **Vintage histórico não é reconstruível** |
| R14 | **NEFIN reescreve fatores históricos** — HML mudou materialmente entre dois snapshots oficiais | Confirmada | Alto para H4 | URL presa ao SHA, manifesto e comparação de vintages; fatores restritos à atribuição ex post | Mitigado. **Não usar NEFIN para gerar posição** |
| R15 | **Peso espacial PAM não é vintage perfeito** — SIDRA revisa anos antigos; milho municipal não separa 1ª/2ª safra; `...` é indisponível | Confirmada | Médio | Calendário efetivo 2014–2024; captura + manifesto; somente `avail_date≤t`; ausentes ficam `NaN` e contados; sensibilidade uniforme | 🟡 Mitigado, residual irremovível (D-024) |
| R16 | **CHIRPS prelim começa em 2015** — não há vintage operacional para 2013-14; jan/início de fev de 2015 foi backfill | Confirmada | Alto para poder estatístico | Primeiro ano-safra primário = 2015/16; ausência antes disso, nunca substituir silenciosamente por `final`; reportar redução do desenvolvimento | Aceito — limitação irremovível da fonte |
| R17 | **Fronteiras municipais mudam** — usar malha atual no passado cria suporte espacial futuro; trocar malha por ano muda mecanicamente o sinal | Confirmada | Médio | Malha IBGE 2013 fixa, pré-amostra; geocódigo PAM positivo sem polígono falha e exige crosswalk versionado | 🟡 Mitigado; refinamentos posteriores são ignorados (D-024) |
| R18 | **ComexStat histórico não preserva o vintage da primeira publicação** — usar hoje a base final como confirmação mensal passada cria lookahead | Confirmada | Alto | Retirar o gate do sizing primário; usar volume final apenas como desfecho H1b *ex post*; manter snapshots para revisões prospectivas (D-026) | ✅ Eliminado do sinal; revisão histórica segue irrecuperável |
| R19 | **Cap de 20% incompatível com a matriz PIT** — único produtor até 03/2018 exige 50% do bruto; depois, dois exigem 25% cada | Resolvida (D-053) | Baixo | Artefato da estrutura antiga (long produtor). Sob H′ a carteira é balanceada nos dois sentidos e o holdout (2020/21+) tem os 5 nomes vivos ⇒ concentração de "um nome só" não ocorre; cap 0,40 declara o teto | 🟢 Resolvido — sizing dollar-neutral congelado em `strategy_spec.py` |
| R20 | **Sinal líquido do produtor estava subespecificado** — preço maior (+) e quebra na própria lavoura (−) foram colapsados em direção positiva | Confirmada | Existencial | D-043 falsificou a direção antiga; D-044 pré-registrou H′ (`Q>P`) com disclosure de que o dev está queimado; D-053 congelou a camada operacional sem apagar o sinal histórico | 🟡 Reformulado; validação de H′ existe somente no holdout |
| R21 | **Exposição corporativa temporalmente esparsa** — cinco vintages não representam automaticamente geografia, hedge, aquisições e mix de uma década | Confirmada | Alto | Auditoria PIT feita nas fontes primárias (20-F AGRO3/BRF, 10-K Pilgrim's); mix/geografia/perímetro extraídos; área-por-UF e % de hedge **declarados como lacuna**, não preenchidos (D-035) | 🟡 Mitigado com lacunas declaradas |
| R22 | **H3/Fama–MacBeth incompatível com N cross-sectional de 3–4 ações** | Confirmada | Alto | Fama–MacBeth suspenso e substituído em D-053 por spread/painel nos quatro grãos, cluster por ano-safra e permutação unilateral | 🟢 Desenho substituto congelado; poder continua limitado por R1 |
| R23 | **Dollar-neutral foi chamado de market-neutral** — notional zero não neutraliza beta, tamanho, liquidez, FX ou commodity | Confirmada | Alto | Corrigir linguagem; medir/neutralizar fatores explicitamente e manter H4 como teste existencial | 🟡 Conceito corrigido; exposição fatorial ainda aberta |
| R24 | **Canal de cana passa por estabilidade direcional, mas sem significância** — ATR maior não implica receita total maior | Confirmada | Alto | Submodelo separado; SMTO3 entra só na carteira, cap 0,15, e fica fora do teste primário; JALL3 excluída. Reportar p=0,12/bootstrap p=0,27 (D-052/D-053) | 🟡 Tratamento congelado; ATR≠receita permanece ressalva aberta |
| R25 | **D-053 não fechou toda a mecânica do backtest** — calendário, score multicanal, universo incompleto, permutação, custos e fronteiras ainda permitiam escolhas | Confirmada | Existencial | D-055 tornou a grade de blocos executável em `operational_spec.py`, com tripwires e holdout negado por padrão | 🟢 **Resolvido — Fase 4.0 encerrada sem P&L** |
| R26 | **Desenvolvimento operacional parcialmente não materializável** — D-055 declara 2015/16–2018/19, mas o peso nacional exige a safra CONAB anterior e o painel de vintages começa em 2017/18 | Confirmada | Médio | Não usar equal-weight, peso futuro ou backfill. Validar a mecânica com testes sintéticos; a única safra real de dev computável pelo contrato nacional é 2018/19. Tratar a cobertura como limitação, não selecionar regra alternativa por P&L (D-056) | 🟡 Motor resolvido; cobertura real restrita e declarada |
| R27 | **Histórico público de aluguel não cobre o experimento** — negócios, taxa e estoque por ticker de D-055 não são recuperáveis em 2018/19 e cobrem apenas parte do holdout | Confirmada | **Existencial para investibilidade** | Parser/gate permanecem estritos; não usar taxa atual, zero por ausência nem backfill. **Fork resolvido pela opção 2 (D-058)**: custo de aluguel via proxy conservadora declarada (piso 5%+tarifas+2×, disponibilidade por ADTV), corroborada pelo único snapshot real; custo é premissa, não medição de investibilidade histórica | 🟡 **Mitigado por D-058**: smoke destravado; limitação (custo não medido do short) declarada no relatório |

> **Sobre R1 e R2**: são os dois riscos que não conseguimos eliminar por engenharia. R1 é
> uma propriedade do fenômeno (safra é anual, ponto). R2 só se resolve rodando o teste. A
> postura do projeto é **medir e declarar**, não contornar.

---

## Parte II — Log de decisões

### D-001 — Tese escolhida: choque climático + confirmação por comércio exterior
**Data**: 2026-07-13
Escolhida entre 21 teses candidatas avaliadas (`05_Ideacao_Tese/teses_candidatas.md`), por
critérios definidos antes da escolha (base teórica, novidade no Brasil, custo/acesso ao dado,
densidade de observações, clareza da decisão de investimento, defensabilidade).
**Decisão tomada antes de qualquer backtest.** As 20 alternativas descartadas ficam
documentadas — não escolhemos a tese que "funcionou".

### D-002 — Reformulação: a tese não é direcional, é cross-seccional
**Data**: 2026-07-14
A formulação ingênua ("seca ⇒ vende agro") está **economicamente errada**: uma quebra de
safra brasileira é um choque de oferta *global* e **eleva** o preço da commodity — o que
beneficia o produtor e prejudica quem compra o grão como insumo (frigoríficos). A estratégia
passa a ser **long produtores / short processadores**, market-neutral por construção.
**Impacto**: é o principal ativo intelectual do projeto e a base do critério "Conceito" (20%).

### D-003 — CHIRPS como fonte climática primária, NASA POWER rebaixada a secundária
**Data**: 2026-07-14
Confirmamos empiricamente que a NASA POWER **sobrescreve retroativamente** os últimos ~2
meses (campo `sources` da API: `GEOSIT` provisório → `MERRA2` definitivo). Ela **não oferece
vintages**, o que embute lookahead não removível. O CHIRPS é a única fonte testada que
**arquiva prelim e final separadamente**.
**Custo da decisão**: CHIRPS só tem precipitação. A temperatura (estresse térmico, geada)
continua vindo da POWER, e continua exposta ao problema — limitação declarada.

### D-004 — COTAHIST (B3) como fonte de preços e de universo, não yfinance
**Data**: 2026-07-14
Descoberto que JBSS3, BRFS3, MRFG3 e STBP3 **deixaram de existir em 2025** e que o Yahoo
apaga tickers deslistados — tornando impossível baixar seu histórico por yfinance. Como esses
eram justamente o lado *processador* (short) da tese, o viés de sobrevivência seria fatal.
O COTAHIST é um registro do pregão e inclui todo papel negociado em cada ano.
**Consequência**: abre a pendência R5 (ajuste de proventos).

### D-005 — A revisão da CONAB vira elo causal explícito da tese
**Data**: 2026-07-14
Descoberto que o `LevantamentoGraos.txt` da CONAB é um **painel de vintages verdadeiro**
(guarda as 12 estimativas de cada safra, com revisões de −15% a +20%). Isso insere um elo
intermediário **observável e datável** entre o clima e o preço, e transforma a hipótese
central em algo diretamente falsificável: *o choque climático prevê a revisão que a CONAB vai
publicar?* Permite ainda um **estudo de evento** em torno das datas de divulgação.
**Limitação**: o painel só começa em 2017/18 (~9 safras).

### D-006 — Camada de confirmação opera em frequência mensal; ANTAQ e dado semanal descartados
**Data**: 2026-07-14
- O **dado semanal** do MDIC teria latência de ~1 dia, mas o órgão **sobrescreve a mesma URL
  toda semana e declara que não armazena histórico**. Não há série para backtestar. Vai para
  o relatório como "o que coletaríamos em produção" (próximo passo).
- A **ANTAQ** tem latência de ~40 dias, e o ComexStat já entrega porto de embarque (URF) por
  NCM em 3-5 dias úteis. **A ANTAQ é estritamente pior e não adiciona nada** — descartada
  como camada de granularidade (revertendo a expectativa inicial).

### D-007 — Método fundamentalista (A) é o primário para a matriz de exposição
**Data**: 2026-07-14
A exposição `E_{i,c}` estimada por regressão dos próprios retornos (Método B) cria
dependência circular entre sinal e alvo, enfraquecendo a interpretação causal. O Método A
(composição de receita/custo divulgada) é auditável e defensável. **B entra como robustez**,
e a **discordância entre os dois é reportada como achado**, não escondida.

### D-008 — Split temporal e holdout lacrado
**Data**: 2026-07-14
Desenvolvimento restrito a 2013-2019. Holdout 2020-2025 lacrado, rodado **uma única vez**.
Resposta direta ao viés de "escolha oportunista de período" citado nominalmente pelo edital.

**Ponto fechado (D-029)**: D-008 não explicitava se o lacre alcança também os desfechos
físicos sem retornos. Resolvido em **D-029** (encerra PT-001): o lacre veda a estratégia e seus
parâmetros, não os testes de mecanismo H1a/H1b, que rodam no span cheio com sub-amostras
dev/holdout reportadas em separado.

### D-010 — O sinal climático é condicional à cultura e à fase, não linear
**Data**: 2026-07-14
A verificação da literatura agronômica derrubou a premissa implícita de que "menos chuva ⇒
preço sobe" vale uniformemente. Três exceções confirmadas (`09_FENOLOGIA_E_LIMIARES.md`):
- **Cana**: seca no verão reduz tonelagem (ruim), mas seca na maturação (inverno) **aumenta o
  ATR** (boa). Confirmado na safra 24/25: produtividade caiu e o **ATR subiu 1,33%**. Um
  z-score linear teria o **sinal trocado metade do tempo**.
- **Café**: a florada exige seca *seguida de* chuva — o gatilho é a sequência, não o nível.
- **Milho safrinha**: déficit no embonecamento custa −40/−50%; depois, −10/−20%.

**Impacto**: `Shock` passa a ser definido **por cultura × fase**, com direção declarada. Este
é o tipo de erro que geraria um backtest ruim e inexplicável, praticamente impossível de
diagnosticar depois.

### D-011 — NDVI é camada de validação, não de sinal
**Data**: 2026-07-14
O INPE Brazil Data Cube (WTSS) entrega MODIS NDVI de graça, sem token, desde 2000 — e a
qualidade foi verificada (a curva de dupla safra do MT é legível). **Mas a latência real é de
~4 meses**, não os 16 dias anunciados (testado em 4 pontos; requisições além de 06/03/2026
retornam erro).
**Consequência**: o NDVI **não pode gerar posição**. Fica como camada de **validação ex-post**
do mecanismo (o choque climático de fato reduziu o vigor vegetativo?), reforçando H1.
Isso reverte a expectativa inicial de usá-lo como sinal antecedente.
*(SATVeg da Embrapa foi avaliado e descartado: é pago — R$ 250/mês — e entrega o mesmo produto
MODIS que o INPE dá de graça.)*

### D-009 — Python 3.14 / pandas 3.x
**Data**: 2026-07-14
Única versão de Python disponível no ambiente. Verificado que pandas 3.0.3, numpy 2.5.1,
scipy 1.18 e statsmodels 0.14.6 têm wheels e funcionam.
⚠️ **pandas 3.x tem breaking changes vs. 2.x** (Copy-on-Write por padrão): tutoriais e
respostas antigas podem não funcionar. Fixar versões no lockfile.

### D-012 — Fundação de engenharia: lock com hashes, um formatador, guards determinísticos
**Data**: 2026-07-15
Antes de escrever qualquer ingestão, montamos o esqueleto de engenharia do repositório, para
que nenhum commit posterior consiga introduzir lookahead, segredo ou lint quebrado sem a CI
barrar. Escolhas e seus custos:
- **Reprodutibilidade por lockfile com hashes** (`requirements.lock`, via `pip-compile
  --generate-hashes --allow-unsafe`), não `pip freeze`. Custo: quem mexe em dependência
  precisa regenerar o lock (documentado no `CONTRIBUTING.md` §5). O `--allow-unsafe` foi
  **necessário**, não opcional: sem pinar `setuptools`/`wheel`, a instalação em modo
  `--require-hashes` falha — bug pego numa validação de instalação limpa, não em teoria.
- **Um único formatador (`ruff format`)**, removendo o `black`. Ter os dois é um footgun
  conhecido (podem discordar e oscilar). Custo: contraria a menção a "ruff/black" no guia
  local, mas `ruff format` reimplementa o estilo do black, então a intenção é preservada.
- **Guards de lookahead e de segredo como scripts determinísticos** (`scripts/check_*.py`),
  não como checagem de IA. São *tripwires* baratos, não prova de ausência — a defesa real
  continua sendo a revisão de PR (`CONTRIBUTING.md` §4) e os testes. Reforçam R11 e a regra
  dura de point-in-time.
- **Teste-canário `tests/test_signal_sign.py` antes do sinal existir**, travando a convenção
  produtor(+)/frigorífico(−) de `01_TESE` §3. Mitigação ativa de R11.
- **Versões verificadas ao vivo com wheels cp314**: pandas 3.0.3, numpy 2.5.1, scipy 1.18.0,
  statsmodels 0.14.6 (confirma D-009). Nota py3.14: `except A, B:` sem parênteses é sintaxe
  **válida** agora (PEP 758) e o `ruff format` a adota — não é erro.

### D-013 — Proventos: B3 oficial primária, StatusInvest para a cauda deslistada
**Data**: 2026-07-15
Verificação ao vivo de duas fontes gratuitas de proventos (detalhes em `02_DADOS.md` §4.2.1):
- A **API oficial da B3** (`GetListedCashDividends`) é a melhor onde cobre — traz a data de
  deliberação (`dateApproval` = nosso `avail_date`, **vintage-safe**) e o preço de referência
  pré-ex, que é o que se precisa para o fator de ajuste. Mas **não cobre deslistados**: BRF e
  Santos Brasil retornam 0 registros e JBS congela em 2019. O problema de survivorship (R4)
  reaparece na dimensão de proventos.
- A **StatusInvest** guarda a cauda deslistada (JBSS3 com eventos até 05/2025), mas é agregador
  derivado: só tem data-com e pagamento (sem deliberação) e **reescreve** valores por ação para
  splits posteriores (campo `adj`).

**Decisão**: B3 oficial como **primária** para todo nome que ela cobre; StatusInvest como
**preenchedor da cauda deslistada** (BRF, Santos Brasil, JBS pós-2019). Legitimado por um
**cross-check** onde as duas se sobrepõem — em SLC os valores batem e o `ed` da StatusInvest é
exatamente a data-com da B3 (o preço ajusta no pregão seguinte).
**Custo/limitação**: parte do lado short depende de um agregador não-oficial. Mitiga-se tratando
o campo `adj` explicitamente (nunca misturar valor ajustado e nominal) e reportando qualquer
divergência entre as fontes como achado.
Eventos **em ações** (split/bonificação/incorporação/subscrição) vêm do endpoint
`GetListedSupplementCompany` da B3 (com data de deliberação e fator), que cobre até os eventos
terminais dos deslistados — mas parece truncar as listas, o que precisa ser conferido ao
construir os fatores.

### D-014 — Série de retorno total point-in-time, não "adjusted close" retroativo
**Data**: 2026-07-15
O motor de preços (`quantagro.prices.adjust`) devolve **retorno total diário**, não um nível de
preço ajustado. Motivo: o ajuste retroativo clássico reescala todo o passado a cada novo
provento, então o nível ajustado numa data `t` passaria a embutir dividendos pagos **depois** de
`t` — lookahead puro para qualquer sinal que olhe nível. O retorno total é calculado só para
frente, aplicando cada evento a partir da sua data-ex (= 1º pregão após a data-com). A
propriedade está **travada em teste** (`tests/test_price_adjust.py::TestPointInTime`): o retorno
até `t` não muda quando se acrescenta um evento posterior a `t`.
**Custo/limitação**: quem precisar de nível (ex.: filtro de preço mínimo) terá de reconstruir um
índice a partir do retorno, ciente de que só é válido para frente. A normalização específica de
cada fonte (fator da B3, campo `adj` da StatusInvest) fica na ingestão, fora do motor.

### D-015 — Montador: merge de fontes com tolerância, corte na deslistagem e tripwire de split
**Data**: 2026-07-16
O montador (`quantagro.prices.assemble`) junta COTAHIST + as três fontes de eventos numa série
de retorno total por papel. Três regras de desenho:
- **Merge B3 × StatusInvest sem dupla contagem**: a B3 entra inteira; da StatusInvest entra só
  o que não casa 1-para-1 com um evento B3 na mesma data-com e valor dentro de **5e-4 relativo**
  (a tolerância medida no cross-check). O casamento é 1-para-1 de propósito: dividendo e JCP na
  mesma data-com (caso real em SLC 12/12/2025) não podem se fundir.
- **A série termina onde o pregão terminou**: evento com data-com no último pregão ou depois
  (caso real: BRFS3 tem provento datado após a incorporação pela Marfrig) não tem data-ex e é
  descartado. Travado em teste.
- **Tripwire de split perdido** (`flag_suspect_returns`): dias com |retorno| ≥ 30% são listados
  para inspeção humana — é o sintoma de um split ausente (truncamento conhecido do supplement da
  B3). O limiar pega splits ≥ 1,5:1.
**Validação**: contra dados reais, ponta a ponta — no dia ex do desdobramento 2:1 da SLC
(14/12/2023) o retorno cru é −51,8% e o montado −3,7% (= movimento real do papel); na JBS o
dividendo da StatusInvest é absorvido no ex e a série termina na deslistagem (06/06/2025).
Manifestos dos COTAHIST usados em `data/manifests/`.
**Custo/limitação**: (i) bonificações pequenas (ex.: 12,5%) ficam **abaixo de qualquer limiar
útil** do tripwire — a completude do supplement só é verificável por cross-check contra uma
fonte ajustada independente (yfinance, nos papéis vivos), pendência levada para a validação
C1; (ii) um evento de fallback na mesma data-com com valor fora da tolerância é tratado como
lacuna da primária e mantido — se for na verdade divergência de valor, entraria duplicado
(mitigado pelo cross-check em teste e pelo tripwire).

### D-016 — Cross-check contra fonte ajustada independente é obrigatório por papel vivo; correções entram por registro curado com proveniência
**Data**: 2026-07-16
O cross-check da série montada contra o *adjclose* do Yahoo (SLCE3 e AGRO3, 2023-2025, 748
pregões cada) encontrou **uma divergência real de 9,1% num único dia** (09/05/2023): uma
**bonificação de 10%** da SLC (AGO/E de 27/04/2023, data-base 08/05, ex 09/05) que está
ausente de **todas** as fontes automáticas do projeto — o `GetListedSupplementCompany` da B3
(que lista o desdobramento de 12/2023 e a bonificação de 12/2025, mas não a de 05/2023) e a
StatusInvest (todos os `chartProventsType` testados). Com isso, o truncamento do supplement
deixa de ser ressalva ("parece truncar", D-013) e vira **fato confirmado com omissão material**.
Decisões:
- **Todo papel vivo do universo passa pelo cross-check** (`scripts/crosscheck_yahoo.py`)
  antes de o dataset de preços ser congelado. Feito até agora: SLCE3 ✅ (limpo após correção),
  AGRO3 ✅ (limpo). Os demais nomes do universo são pendência aberta.
- Eventos ausentes das APIs entram por **registro curado manualmente**
  (`ingest/events_manual.py`), sempre com fonte primária citada (documento societário/RI) e
  nascidos de divergência concreta — nunca de memória. O git é a trilha de auditoria.
- **Divergência de convenção não é bug**: em dividendo grande, o Yahoo usa fator
  multiplicativo `P_ex/(P_cum−div)`, que se afasta do retorno verdadeiro do acionista
  `(P_ex+div)/P_cum` (nossa convenção, CRSP) — no dividendo de 10,6% da AGRO3 (25/10/2023),
Yahoo −9,00% vs nosso −8,04%. Mantemos a nossa; o script documenta a leitura.

**Status posterior**: D-025 concluiu o cross-check dos 19 papéis vivos e encerrou a pendência
aberta acima. O texto original é preservado para mostrar a sequência da auditoria.
**Custo/limitação**: papéis **deslistados não existem no Yahoo** — a cauda short (JBSS3,
BRFS3, STBP3) fica sem cross-check externo de eventos em ações; mitigação parcial: o tripwire
de D-015 e o fato de a B3 cobrir os eventos terminais. Limitação declarada, sem solução
gratuita conhecida.

### D-017 — Calendário CONAB (R10): curadoria multi-fonte com data efetiva > planejada; na dúvida, a mais tardia
**Data**: 2026-07-16
O `Levantamento*.txt` não traz a data de divulgação de cada levantamento, e a verificação
ano a ano provou que o problema era real e pior do que o previsto: **o listing atual do site
da CONAB (gov.br) exibe datas falsas para toda a safra 2022/23 de grãos** — datas nominais
"dia 10" (incluindo sábados), artefato da migração de site de nov/2023, com erro de até 6
dias contra as datas verdadeiras. Um mapa ingênuo lido do site oficial contaminaria o estudo
de evento em silêncio.

O mapa foi curado em `ingest/conab_calendar.py` (grãos 2017/18→2025/26 completo, café
2017→2026, cana 2017/18→2026/27), com fontes primárias trianguladas: PDFs oficiais do
Calendário de Divulgação (Wayback), a página antiga da CONAB com data de publicação por item
(snapshots 2018-2023), o espelho same-day da AMPA (timestamp no nome do arquivo, validado
7/7 contra datas conhecidas), timestamps de upload do site antigo e notícias datadas do dia.
Decisões:
- **Data efetiva vence planejada** (foram observados 3 adiamentos reais de 5-20 dias:
  grãos 4º/2023-24, cana 1º/2021-22 e 3º/2022-23); divergência irresolvida → vale a **mais
  tardia** (atrasar sinal nunca cria lookahead; adiantar cria).
- **Entrada nova só com fonte primária citada** no comentário da safra — mesma disciplina do
  registro de eventos societários (D-016). O git é a trilha de auditoria.
- **O carimbo falha alto** para qualquer `(ano_agricola, id_levantamento)` fora do mapa —
  cobre o resíduo legado `lev 99`, as culturas de inverno (alinhamento de boletim ambíguo,
  não usadas pela tese) e safras futuras ainda não curadas.
**Custo/limitação**: poucas datas seguem com fonte única (anotadas no módulo): café e cana
2017 só têm o calendário planejado; 9º lev de grãos 2017/18 só tem a página antiga. O painel
de café de 2020 não tem 2º levantamento (suspenso na pandemia) — buraco da fonte, declarado.

---

### D-018 — Ingestão CHIRPS: GeoTIFF sem GDAL (`tifffile`), agregação por caixas, vintage prelim/final preservado
**Data**: 2026-07-16
O CHIRPS é a fonte climática **primária** (`02_DADOS §1.1`) porque é a única testada que
preserva vintage. A verificação ao vivo confirmou o mecanismo e fixou o desenho da ingestão:
- **Prelim e final são arquivados separadamente e permanecem no servidor** (não é produto
  *rolling*): o prelim de 15/01/2024 segue lá em 2026, datado 17/01 no diretório (latência
  ~2 dias); o final, datado 15/02. O vintage é reconstruível retroativamente — ao contrário do
  ComexStat semanal (`02_DADOS §3.4`) e da reanálise. **A revisão é material**: prelim→final de 15/01/2024
  no médio-norte de MT = +0,87 mm/dia (~+23%); no oeste da BA, −0,33 mm. É exatamente essa
  contaminação que a fonte com vintage nos deixa **medir** em vez de supor ausente.
- **GeoTIFF lido sem GDAL**. O ambiente cp314 não tem wheel de rasterio/GDAL, mas o tif do
  CHIRPS é **sem compressão**, float32, com geotransform auto-descrito nas tags
  `ModelPixelScale`/`ModelTiepoint` — `tifffile` (Python puro sobre numpy) basta. Nova
  dependência de runtime travada em `pyproject.toml`/`requirements.lock`. `imagecodecs` foi
  avaliado e **descartado** (nenhuma compressão a decodificar).
- **Agregação por caixas lat/lon nomeadas** (decisão escolhida sobre máscara por polígono):
  média de precipitação numa bounding-box por região produtora, ignorando `nodata`, sem
  dependência de geometria/shapefile. A grade de ~5 km agregada não justifica recorte por
  polígono de UF; a *escolha* das caixas fica na camada de sinal, não na ingestão (entram como
  argumento explícito). Uma caixa sem célula válida devolve `nan` — nunca zero espúrio de chuva.
- **Carimbo `avail_date` = ref + 7 dias corridos** (lag congelado em `01_TESE §5`), aplicado a
  jusante por `validate.pit`, com `kind` (prelim/final) preservado como o eixo de vintage. Os
  7 dias cobrem com folga a latência real observada do prelim (2 dias).
- **Fixture de teste**: recorte real do grid global (Brasil central, 160×320), com as tags geo
  do recorte — exercita o mesmo caminho de leitura auto-descrita e reproduz **exatamente** os
  valores extraídos do raster global (prova cruzada rodada ao vivo). O leitor lê as tags direto
  da página (não de `geotiff_metadata`, que o `tifffile` só popula com `GeoKeyDirectoryTag`).
**Correção factual posterior (D-023/R16)**: o `final` cobre desde 1981, mas a pasta `prelim`
começa em 01/01/2015; consultas a 2008/2013 retornam 404. Os arquivos de janeiro e início de
fevereiro de 2015 foram carregados em bloco em 17/02, logo não representam baixa latência na
origem. A afirmação inicial de “~18 anos × 2” superestimava a cobertura operacional.

**Custo/limitação**: baixar o histórico completo disponível (prelim desde 2015 + final) é
volume real — mitigado pelo cache local (não rebaixa) e por só se materializar quando o backtest
exigir. A grade de ~5 km e a agregação por caixa não resolvem município. NASA POWER (temperatura,
sem vintage) fica para o próximo passo com a limitação de revisão declarada.

**Status posterior**: D-019 implementou POWER e D-023/D-024/D-027 substituíram as caixas pela
regionalização municipal do sinal primário.

---

### D-019 — Ingestão NASA POWER: só temperatura, proveniência de vintage carimbada, limitação declarada
**Data**: 2026-07-16
O POWER é o clima **secundário** (`02_DADOS §1.2`). Diferente do CHIRPS, ele **não preserva
vintage** — a série é MERRA-2 com uma cauda de baixa latência (GEOS-IT/FLASHFLUX), e os últimos
~2 meses são provisórios e sobrescritos; mesmo o MERRA-2 é reprocessado a cada alguns meses.
Respeitar `avail_date` não conserta o problema (o valor em si é revisado). O desenho da ingestão
foi fixado por verificação ao vivo:
- **Escopo restrito à temperatura** (`T2M`/`T2M_MAX`/`T2M_MIN`). A precipitação, canal físico
  dominante, vem do CHIRPS (que tem vintage). O POWER só entra onde não há alternativa gratuita
  com vintage — estresse térmico e geada.
- **Proveniência de vintage carimbada por resposta** via `header.sources` — mecanismo confirmado
  ao vivo: fetch de 2015 → `MERRA2` (definitivo); fetch de jun/2026 → `GEOSIT` (provisório). A
  classificação (`classify_vintage`) e a lista de sources vão para o manifesto e para a coluna
  `source_vintage` do painel. A API não expõe a fonte por data, então a classificação é
  **por resposta** — declarado como tal, não fingido mais fino do que é.
- **Cache por captura datada** (como a CONAB): a fonte sobrescreve no lugar, então o nome do
  arquivo leva a data de captura (um vintage por captura) e não rebaixa. O rate limit não é
  garantido (a doc menciona HTTP 429), o que reforça o cache agressivo.
- **Pontos = centroides das caixas do CHIRPS** (`DEFAULT_POINTS` espelha `DEFAULT_BOXES`), para
  que chuva e temperatura casem pela coluna `region` na camada de sinal. Grade ~0.5° (grosseira
  para município, aceitável para mesorregião). Carimbo `avail_date` = ref + 3 dias corridos.
- **Fill −999 → `NaN`** sempre — o fill nunca pode ser tratado como temperatura real.
**Custo/limitação**: a componente de temperatura do sinal permanece **contaminada por revisão**,
irremovível na fonte. A mitigação é medir a magnitude (a suíte de robustez usa `source_vintage`,
e capturas datadas a partir de agora permitem comparar provisório × definitivo no futuro); se for
material, o sinal se restringe à precipitação (CHIRPS). Grade grosseira não resolve município.

---

### D-020 — Ingestão ComexStat: guardrail do NCM, proveniência de vintage, camada mensal
**Data**: 2026-07-16
O ComexStat é a **camada de confirmação por comércio exterior** (H1b): o volume exportado das
commodities é a contraparte comercial do choque de oferta. Duas propriedades da fonte, ambas
reconfirmadas ao vivo, fixaram o desenho:
- **Guardrail do NCM (a decisão central)**: a API exige o código NCM como **string de 8 dígitos**;
  passá-lo como int (perdendo o zero à esquerda) retorna **lista vazia com `success:true`** — erro
  silencioso que corromperia café (0901) e carnes (02xx), metade das NCMs da tese. Verificado:
  café `"09011110"` = 2 linhas, `9011110` (int) = 0. `_validate_ncms` **falha alto** para qualquer
  valor que não seja string de 8 dígitos, antes de tocar a rede — e um meta-teste garante que a
  própria constante `THESIS_NCMS` passa no guardrail.
- **Não preserva vintage**: a fonte revisa todos os meses do ano corrente até fevereiro do ano
  seguinte, e não há consulta *as-of*. O manifesto grava o `general/dates/updated` (mês mais
  recente + data de atualização) como prova de qual versão foi capturada; o arquivo é datado por
  captura (um vintage por captura, como CONAB/POWER). A fonte entra como confirmação **mensal**,
  nunca como gatilho de alta frequência.
- **`ref_date` = fim do mês de referência**; carimbo `avail_date` a jusante (divulgação nos
  primeiros dias úteis do mês seguinte, latência ~3-5 dias úteis). Métricas string→int.
- **Rate limit confirmado**: a verificação ao vivo bateu em **HTTP 429**, confirmando o limite
  que a doc marcava como não caracterizado. Reforça o cache agressivo (não rebaixa).
**Custo/limitação**: a contaminação por revisão é irremovível na fonte (mitigada pela captura
datada + `dates/updated`, que permitem comparar snapshots no futuro). O dado semanal do MDIC
continua inutilizável para backtest (não arquiva — `02_DADOS §3.4`), então a confirmação opera em
frequência mensal, com ~poucas dezenas de observações — coerente com o N efetivo já pequeno da tese.

---

### D-021 — ONI: controle pré-registrado, disponibilidade após estabilização e RONI só como robustez
**Data**: 2026-07-16
O ONI é controle de ENSO para R6/H5, não componente direcional do sinal. A verificação da
fonte oficial fixou quatro escolhas:
- `ref_date` é o fim do **mês central** da temporada de três meses (`DJF 2025` → 31/01/2025),
  evitando fingir que o rótulo sazonal é um mês de publicação;
- `initial_avail_date` é o dia 5 dois meses depois do mês central: a janela precisa terminar
  e a NOAA atualiza a página até o dia 5;
- o caso primário usa `avail_date` **dois meses depois da primeira publicação**, pois a própria
  NOAA avisa que os valores recentes podem mudar nesse intervalo. O caso sem espera existe
  apenas como sensibilidade explícita;
- a mudança operacional da NOAA para RONI em 2026 não altera retrospectivamente o
  pré-registro. ONI permanece primário; RONI é uma futura robustez declarada.

O arquivo oficial é sobrescrito e não oferece consulta *as-of*. `ingest/oni.py` salva uma
captura por dia e manifesto com hash, última temporada e metodologia. Validação ao vivo em
16/07/2026: 917 temporadas, de DJF/1950 a AMJ/2026; último ONI = 0,98, publicação inicial
05/07/2026 e disponibilidade conservadora 05/09/2026.

**Custo/limitação**: esperar estabilização reduz a atualidade do controle e não desfaz
revisões históricas causadas pela atualização quinquenal dos períodos-base. A defesa é
transparência + sensibilidade; não existe engenharia capaz de reconstruir um arquivo que a
fonte não arquivou.

---

### D-022 — NEFIN: snapshot preso ao commit e uso exclusivamente ex post em H4
**Data**: 2026-07-16
Os fatores NEFIN são observações diárias, mas a fonte publica o CSV inteiro em lotes. A
frequência do dado não autoriza supor disponibilidade D+1. O repositório oficial GitHub Pages
permite prender cada captura ao commit que publicou o arquivo; esse SHA, e não a branch
mutável, é a unidade de vintage de `ingest/nefin.py`.

A comparação empírica dos dois commits disponíveis desde a migração do site derrubou a
hipótese de atualização apenas por *append*. Entre os snapshots de 01/06 e 19/06/2026:
- ambos têm 6.218 datas sobrepostas; o novo acrescenta observações até 02/06;
- HML mudou em 4.484 datas acima de `1e-10`, sendo 3.889 por mais de 1 bp;
- a maior revisão do HML foi 2,759 p.p.; WML teve 21 mudanças acima de 1 bp;
- `Risk_Free` ficou idêntico.

Todas as linhas do painel recebem `avail_date` igual à data do commit do snapshot. Não se
inventa um calendário histórico por linha. Essa aparente perda de granularidade não prejudica
o desenho porque NEFIN entra somente na regressão de *spanning* H4, executada **ex post** para
atribuir os retornos já realizados; os fatores nunca alimentam sinal, *sizing* ou execução.

Validação ao vivo: snapshot `e12ab2b324cbd0d26e300477949349711598bccc`, publicado em
19/06/2026, com 6.299 pregões de 02/01/2001 a 02/06/2026.

**Custo/limitação**: o histórico de commits do site atual começa em junho de 2026; vintages
anteriores não são reconstruíveis por esse canal. H4 descreve a atribuição segundo a
metodologia e o snapshot registrados, não o fator que teria sido baixado em cada data passada.

---

### D-023 — O `Shock` primário é soja + milho 2ª, chuva CHIRPS e geografia PAM/IBGE
**Data**: 2026-07-16

Antes de observar qualquer retorno, a especificação fenológica e regional foi reduzida e
transformada em contrato executável (`features/shock_spec.py`). O caso primário ficou:

- **culturas**: soja e milho 2ª safra — mecanismos hídricos lineares, exportação observável e
  painel CONAB com 12 levantamentos anuais desde 2017/18;
- **suporte fixo**: soja em MT/GO/PR/RS/MS/MG/BA (82,2% da produção 2024/25) e milho 2ª em
  MT/PR/GO/MS (86,2%). Regra: menor conjunto acima de 80%, decidida por produção física, não
  por retorno;
- **canal**: déficit de precipitação CHIRPS prelim, padronizado contra climatologia expanding
  do mesmo trecho da janela, com mínimo de dez safras. `Shock=-z(chuva)`;
- **janelas**: fixas por cultura × UF, derivadas de CONAB/ZARC/Embrapa e travadas por teste;
- **geografia**: média CHIRPS por polígono municipal, ponderada pela PAM mais recente já
  publicada dentro da UF; agregação nacional pelos pesos CONAB da **safra anterior encerrada**.

Isto rebaixa a temperatura POWER, algodão, café, cana, caixas retangulares e deslocamentos de
janela a especificações secundárias com pergunta própria. Também esclarece D-018: as caixas
continuam válidas para testar a ingestão, mas não definem o sinal final.

**Custo/limitação**: o primário abre mão de culturas que poderiam aumentar o N aparente e pode
perder choques térmicos reais. A PAM tem atraso anual, revisa o passado e não separa milho 1ª/2ª
safra municipalmente (R15). Implementar PAM + polígonos IBGE torna-se bloqueio da C2. O custo é
aceito porque reduz graus de liberdade, evita a fonte térmica sem vintage e elimina regiões
escolhidas à mão.

**Status posterior**: o bloqueio descrito acima foi encerrado por D-024 (PAM/malha), D-027
(raster→município) e D-028 (agregação as-of e cálculo do `Shock`).

Durante a validação, confirmou-se ainda que o CHIRPS prelim só começa em 2015 e que os primeiros
arquivos foram backfill. O primeiro ano-safra completo foi fixado em 2015/16 (R16); isso reduz o
desenvolvimento efetivo, custo aceito em vez de preencher 2013-14 com dado final revisado.

---

### D-024 — PAM usa calendário efetivo e a geografia é fixa na malha IBGE 2013
**Data**: 2026-07-16

A regionalização de D-023 foi implementada sem consultar retornos. A tabela SIDRA 1612 fornece
quantidade municipal de soja (2713) e milho total (2711); o segundo continua sendo proxy
declarado para a localização do milho 2ª safra. As datas efetivas de divulgação de cada PAM
2014–2024 foram verificadas em calendários/releases do IBGE e codificadas sem interpolação.
Em `D`, entra apenas a edição com maior ano de referência e `avail_date≤D`.

A malha municipal foi fixada na edição IBGE 2013. Os arquivos internos foram gerados em
16/03/2015, antes da primeira janela operacional (dezembro/2015). A alternativa de pedir o
`periodo` correspondente a cada ano na API foi rejeitada: ao vivo, a API entregou 2019–2022,
mas devolveu erro 500 para 2014–2018 e 2023–2024. Misturar versões disponíveis com *fallbacks*
atuais criaria uma quebra de suporte difícil de distinguir de choque climático.

Validação integral: 38.467 linhas PAM (2014–2024), 25.208 observadas, 13.129 zeros SIDRA e 130
`...` (dado indisponível). `...` permanece `NaN`; os pesos normalizam somente tonelagem
reportada e carregam a contagem ausente. As sete malhas têm 141 (MT), 246 (GO), 399 (PR), 499
(RS), 79 (MS), 853 (MG) e 417 (BA) municípios. A cobertura foi completa para toda produção
positiva nos *snapshots as-of* de 01/12/2015, 01/12/2020 e 01/12/2025.

**Custo/limitação**: a captura atual do SIDRA não recupera valores anteriores às revisões; a
malha fixa ignora refinamentos posteriores; e milho total é proxy para safrinha. Esses custos
são preferíveis a fabricar vintage, converter ausente em zero ou deixar a fronteira variar.
Peso municipal uniforme permanece robustez pré-registrada.

---

### D-025 — Auditoria integral fecha o lado de preços com correções curadas
**Data**: 2026-07-16

Antes de congelar o dataset, os 19 papéis vivos do universo foram confrontados, em 2023–2025,
com o `adjclose` do Yahoo. O exercício validou somente integridade de preço/evento; não calculou
retorno de estratégia, sinal, exposição ou métrica do holdout.

Três classes de achado exigiram tratamento diferente:

- **lacunas nossas**: bonificações de 10% de VITT3 (04/2024) e KLBN11 (05/2024) estavam
  ausentes do endpoint atual da B3, como já ocorrera com SLC (05/2023). Entraram no registro
  manual somente após confirmação em documento CVM/B3, com data-com e proveniência;
- **normalização**: a B3 repetia eventos da KLBN para ON, PN e UNIT; agora a classe é filtrada
  pelo marcador do ISIN. Já a StatusInvest traz quatro parcelas legítimas de KLBN11 com mesmo
  dia e valor; deduplicá-las apagava caixa real, portanto linhas sem ID não são colapsadas;
- **falhas do comparador**: BEEF3, RAIZ4, SUZB3, HBSA3 e KEPL3 têm barras isoladas ou
  reescaladas no Yahoo que revertem depois; AGRO3 expõe a diferença conhecida entre o fator
  multiplicativo do Yahoo e o retorno total verdadeiro. COTAHIST continua autoritativo.

A fonte secundária não é somada indiscriminadamente à B3. Nos papéis vivos, StatusInvest só
substitui o histórico de caixa quando a B3 devolve zero registros (caso KLBN11); lacunas
pontuais exigem fonte primária e registro curado. Resultado detalhado em
`11_AUDITORIA_FASE1.md`.

**Custo/limitação**: Yahoo não é padrão-ouro e não cobre deslistados. A auditoria detecta
inconsistências, mas sua conclusão depende da classificação manual contra COTAHIST e documentos
societários. Esse custo é preferível a ajustar a fonte oficial para imitar barras defeituosas.

---

### D-026 — ComexStat confirma H1b ex post; CEPEA e futuros B3 são robustez
**Data**: 2026-07-16

A auditoria das três pendências de `02_DADOS.md §7` alterou o desenho antes de qualquer retorno
de estratégia:

1. **ComexStat**: a Secex reprocessa semanalmente o mês corrente, mensalmente todo o ano e,
   em fevereiro, o ano anterior. A API e os CSVs anuais só expõem o vintage mais recente; o
   Wayback não preservou os arquivos consultados nem foram encontrados snapshots das respostas
   `POST`. Não é possível saber
   qual volume estava publicado em cada mês histórico. O gate 1.0/0.5/0.0 sairia contaminado
   por vintage futuro e foi removido do sizing primário. ComexStat permanece como desfecho
   físico de H1b *ex post* e os snapshots atuais medirão revisões prospectivamente.
2. **CEPEA**: séries históricas e licença CC BY-NC foram confirmadas, mas a exportação é
   interativa e não há API pública estável. Entra como robustez brasileira, com planilha e hash.
3. **Futuros B3**: ajustes diários por vencimento são públicos. Não há série contínua pronta;
   construí-la exige regra de rolagem e preços de ajuste podem ser calculados pela metodologia
   da bolsa quando não há negócio suficiente. Entra como robustez. H2 usa futuros internacionais
   em janelas de evento, excluindo datas de rolagem.

Esta decisão **restringe** D-001/D-006/D-020: a combinação Clima + ComexStat continua sendo a
tese causal — antecipação meteorológica e confirmação física —, mas só a primeira gera o sinal
histórico. A segunda testa se a história econômica é verdadeira.

**Custo/limitação**: o backtest perde uma camada narrativa atraente de confirmação e H2 usa
proxy internacional no primário. Em troca, elimina-se um lookahead irremovível e separa-se
claramente sinal negociável de validação causal.

---

### D-027 — Regionalização raster→município: centro de célula, fallback e exclusão de água
**Data**: 2026-07-17

Primeira metade do C2 `Shock` (`features/regionalize.py`), implementada sem consultar retornos.
A "média climática por polígono municipal" de D-023 foi materializada como **média das células
p05 cujo centro cai dentro do polígono** (regra even-odd, numpy puro, sem GDAL — mesma decisão
de stack de D-018/D-024). O índice município→células é função apenas da malha 2013 e da grade
CHIRPS, ambas congeladas: calcula-se uma vez, carrega as constantes da grade e **recusa** um
raster de grade diferente.

Três escolhas de implementação com efeito observável:

1. **Município sub-célula**: Madre de Deus/BA, Albertina/MG e Esteio/RS não contêm nenhum
   centro de célula (~5,5 km). Descartá-los distorceria o peso PAM; falhar alto bloquearia o
   pipeline por geometria conhecida. Eles recebem a célula cujo centro é o mais próximo do
   centroide do polígono, com `cell_source="nearest_centroid"` auditável.
2. **Polígonos de água não-municipais** (RS: Lagoas Mirim e dos Patos, código de município
   `0000`) ficam fora do índice — nunca têm produção PAM, mas contaminariam médias
   não-ponderadas.
3. **Seleção por centro de célula** ignora frações de célula na divisa municipal; o efeito
   máximo é de meia célula por borda e desaparece na agregação UF ponderada por produção.

Validação por execução (raster global real de 15/01/2024 + 7 malhas UF completas): 2.634/2.634
municípios cobertos com 110.489 células (~12 s, uma vez); painel municipal em 0,12 s/raster;
contagem de células coerente com a área municipal oficial (Cuiabá ~3.500 km² → 118 células de
~30,25 km²); a revisão prelim→final aparece no nível municipal (Cuiabá 15/01/2024:
2,67 → 3,05 mm).

**Custo/limitação**: o clima do município minúsculo é o da célula do centroide (aceitável —
peso PAM ínfimo e erro espacial < 1 célula); a fronteira municipal é tratada como corte duro
de células, não como máscara de área fracionária. Refinar isso não muda a UF agregada de forma
material e abriria uma dependência de rasterização fracionária que o stack não tem.

---

### D-028 — Implementação do `Shock` as-of: mesmo trecho por deslocamento, pesos em `t` e carimbo por produto
**Data**: 2026-07-17

Segunda metade do C2 (`features/shock.py`), implementada sem consultar retornos. O contrato de
D-023 deixava quatro pontos em aberto que precisavam de decisão explícita:

1. **"Mesmo trecho" da climatologia = deslocamento em dias.** O acumulado parcial até `d`
   dias após o início da janela é comparado com o acumulado dos mesmos `d` dias nas safras
   anteriores — trechos de comprimento idêntico, sempre. A alternativa (casar por dia do
   calendário) criaria trechos de comprimentos diferentes em ano bissexto e complicaria a
   comparação sem ganho agronômico.
2. **Pesos espaciais únicos, *as-of* `t`.** A PAM disponível em `t` pondera tanto o trecho
   corrente quanto todos os anos da climatologia. Antes de 2015 não existe PAM com
   `avail_date` reconstruído, então pesos por época são impossíveis para a climatologia
   longa; usar o mesmo vetor de pesos nos dois lados mantém a comparação espacialmente
   idêntica e só usa informação disponível em `t`.
3. **Carimbo por produto CHIRPS.** `prelim` mantém o lag congelado de 7 dias corridos
   (`01_TESE` §5); `final` recebe lag conservador de **60 dias** (a fonte publica ~1 mês
   depois; 15/01/2024 saiu em 15/02). Um lag único de 7 dias superestimaria a disponibilidade
   do `final`. Na prática o `final` só alimenta climatologia de safras ≥ 1 ano no passado, mas
   a regra fica correta por construção, não por sorte.
4. **Nacional renormalizado sobre janelas já iniciadas.** Antes de todas as UFs entrarem na
   janela (soja RS/BA começa um mês depois de MT/GO/PR/MS/MG), o índice usa as que já
   entraram e reporta `uf_coverage_weight` — a composição é visível para o rodador de H1a,
   nunca imputada. O peso entre UFs é a produção da safra CONAB **anterior** já divulgada
   (último levantamento disponível em `t`), nunca a corrente, cuja revisão é o que se quer
   prever.

Guardas que falham alto (todas testadas): buraco de cobertura diária no trecho, município com
peso PAM ausente do painel municipal, menos de 10 safras de climatologia, climatologia
degenerada (desvio zero), UF do suporte sem produção CONAB e painel sem `avail_date`.

Validação: álgebra sintética conferível no papel (climatologia 1..10 mm ⇒ média 5,5, desvio
3,0277; z e sinal verificados nos dois lados) e execução de ponta a ponta com dados 100%
reais (soja/MT, trecho 1–10/dez, `t`=20/12/2024, 110 rasters CHIRPS baixados com manifesto):
acumulado 71,1 mm vs. climatologia 96,3 ± 25,7 mm (safras 2014–2023) ⇒ `z = −0,98`,
`Shock = +0,98` — início de dezembro mais seco que o normal, estresse positivo, convenção
correta. A PAM *as-of* escolheu sozinha a edição 2023 (a última com `avail_date ≤ t`) e os
três maiores pesos municipais são Sorriso, Diamantino e Campo Novo do Parecis — exatamente a
geografia real da soja de MT. O peso nacional veio do 12º levantamento CONAB 2023/24.

**Custo/limitação**: o proxy espacial do milho 2ª continua sendo o milho total da PAM (R15);
os pesos *as-of* únicos significam que o `Shock` recalculado em `t'` > `t` pode diferir do
calculado em `t` se uma edição PAM entrou no meio — é o comportamento correto de um sinal
point-in-time, mas exige que H1a fixe `t` nos cortes dos levantamentos, não recicle valores.

---

### D-029 — Perímetro do holdout: lacra a estratégia, não os testes de mecanismo (encerra PT-001)
**Data**: 2026-07-17

**Decisão.** O holdout 2020–2025 (D-008) veda os **retornos da estratégia e todo parâmetro de
desenho** — matriz de exposição `E`, score, *position sizing* e o backtest, que só é rodado
uma vez na Fase 6. Ele **não** veda os testes físicos de mecanismo H1a (revisão CONAB ~ Shock)
e H1b (Δlog exportação ~ Shock). Estes rodam no **span cheio operacional 2015/16–2024/25** e
são reportados com as sub-amostras **desenvolvimento (2015/16–2019/20)** e **holdout
(2020/21–2024/25)** exibidas separadamente, além do estimador agrupado. Esta decisão é tomada
**antes de qualquer resultado de H1**, cumprindo o critério de encerramento de PT-001.

**N efetivo por perímetro** (contagem de anos-safra = clusters de inferência, sem olhar
resultado; H1a é limitado pelo painel de vintages CONAB, que começa em 2017/18; H1b é limitado
pelo Shock prelim, que começa em 2015/16):

| Perímetro | H1a (revisão CONAB) | H1b (exportação) |
|---|---|---|
| Lacre físico também (dev ≤ 2019/20) | ~2–3 anos-safra | ~4 anos-safra |
| **Lacre só a estratégia (escolhido)** | **~8 anos-safra** (2017/18–2024/25) | **~9 anos-safra** (2015/16–2024/25) |

**Por quê.** Três razões, na ordem em que pesam:
1. **H1a/H1b não contêm retorno de ação nem parâmetro da estratégia.** Testam um fato do mundo
   — déficit de chuva na janela fenológica prevê a revisão para baixo da safra CONAB e a queda
   da exportação física? — não a performance da carteira. O viés de "escolha oportunista de
   período" que o edital cita nominalmente mira o **backtest**; usar todos os anos disponíveis
   num teste de mecanismo é o oposto de *cherry-picking* — maximiza a amostra e reduz a chance
   de uma janela de sorte.
2. **O Shock já está congelado (D-023), antes de qualquer retorno.** Culturas, UFs, janelas
   cultura×fase e regra de climatologia estão travadas em `features/shock_spec.py`. Nenhum
   parâmetro é ajustado a 2020–2025; as regressões consomem um sinal pré-registrado.
3. **Lacrar os desfechos físicos torna H1a intestável.** Restrito ao desenvolvimento, o portão
   mais importante do projeto ficaria com ~2–3 anos-safra — cluster-bootstrap e Newey-West
   inviáveis. Lacrar o mecanismo mataria justamente o teste que deveria proteger a tese antes
   do backtest.

**Custo/limitação declarado.** A decisão de go/no-go do portão da Fase 2 é informada por
comportamento do mecanismo que **inclui anos do holdout** — é um uso brando da janela lacrada.
Aceitamos o custo e o mitigamos por **transparência**: H1a/H1b são reportados com a sub-amostra
de holdout separada da de desenvolvimento, de modo que a banca veja se o mecanismo está
presente nos anos lacrados em vez de diluído no agrupado. O lacre dos **retornos** da
estratégia (Fase 6, rodada única) permanece absoluto: nenhum retorno, exposição, peso de score
ou parâmetro de sizing é calculado sobre 2020–2025 antes do portão do holdout. Esta decisão
**não reverte** D-008; ela explicita o ponto que D-008 havia deixado em aberto.

---

### D-030 — Pré-registro das regressões de H1a e H1b (congelado antes de qualquer ajuste)
**Data**: 2026-07-17

Esta decisão **congela a especificação exata** dos dois testes do portão da Fase 2 **antes de
observar qualquer coeficiente**. É a âncora anti-*p-hacking*: o que estiver aqui é o que roda,
uma vez; qualquer variante posterior é robustez sob BH-FDR, nunca o resultado principal
re-escolhido. O commit desta seção precede na história do git a geração dos resultados.

**Parâmetros compartilhados (herdados e agora fechados).**
- `Shock` = contrato primário congelado (D-023/D-028): soja + milho 2ª, sinal CHIRPS `prelim`,
  climatologia expanding `final` (mín. 10 safras), `Shock = −z(chuva)`.
- **`climatology_first_year = 2000`** — último parâmetro livre do `Shock`, fixado aqui. A
  densidade de estações do CHIRPS no Brasil melhora a partir de ~2000 (antes é mais
  satélite-only); a âncora dá à safra 2015/16 uma base de 15 anos, folga sobre o mínimo de 10.
  Justificativa de **qualidade de dado**, não de resultado.
- Perímetro do holdout: **D-029** — H1a/H1b rodam no span cheio, com sub-amostras
  desenvolvimento (safras ≤ 2019/20) e holdout (2020/21–2024/25) reportadas em separado. A
  decisão do portão usa o span cheio.
- Inferência: erros agrupados por ano-safra (H1a); Newey–West HAC (H1b); *block bootstrap* como
  robustez; **BH-FDR sobre a família primária** de 11 testes (abaixo).

**H1a — o choque prevê a revisão da estimativa de safra da CONAB.**
- Dado: painel de *vintages* `LevantamentoGraos` (safras **2017/18+**), soja (SOJA/UNICA) nas
  UFs {MT,GO,PR,RS,MS,MG,BA} e milho 2ª (MILHO/2ª SAFRA) em {MT,PR,GO,MS}.
- Observação: `(cultura c, UF u, safra s, levantamento n)`, com `n ≥ 2`.
- **Variável dependente** (revisão): `y = log(prod_{s,u,n} / prod_{s,u,base})`, com `base` = o
  primeiro levantamento presente de `(c,u,s)` (normalmente o 1º). Revisão log acumulada.
- **Regressor**: `Shock_{c,u}` avaliado em `t = avail_date(lev n)` — o `Shock` da UF acumulado
  até a publicação do levantamento (`uf_shock_asof`; linhas com `status ≠ ok`, i.e. janela não
  iniciada, são descartadas). `t` fixo no corte de cada levantamento (D-028).
- **Modelo**: OLS agrupado `y ~ α + β·Shock`, erros agrupados por safra; também por cultura.
- **Sinal esperado: `β < 0`** (estresse ⇒ revisão para baixo). Este é o **motor do veto**.
- **Falsificação**: `β ≥ 0` **ou** não-significativo após BH-FDR.

**H1b — o choque prevê a exportação física (ex post, D-026; corroboração).**
- Dado: ComexStat mensal, kg líquido (`metricKG`). Soja = NCM `12019000` (grão; farelo/óleo só
  robustez); milho = `10059010`. Base **final**, ex post — sem *vintage*, por isso apenas
  corrobora, nunca dimensiona (R18/D-026).
- **Regressor**: `Shock_{c,s}` **nacional** da safra (janela plenamente decorrida,
  `avail_date` do último levantamento).
- **Desfecho**: variação log ano-contra-ano do volume exportado no `h`-ésimo mês após o fim da
  janela fenológica da cultura, `h ∈ {3,4,5,6}`:
  `Δ_h = log(kg_{mês(fim)+h, ano}) − log(kg_{mesmo mês, ano−1})`. Uma observação por
  `(cultura, safra, h)`.
- **Modelo**: por cultura e por `h`: `Δ_h ~ α + β·Shock`, erros Newey–West. Sinal esperado
  `β < 0`.
- **Adaptação declarada**: o `Shock` congelado (D-023) é por **ano-safra**, não uma série
  mensal; a forma `h ∈ {3,4,5,6}` de `01_TESE` §4 é aplicada como o deslocamento do **mês de
  exportação** em relação à colheita. Registrado aqui como parte de D-030.
- **Papel**: corroboração física. Poder baixo (~8–9 safras); H1a é o motor do veto.

**Família primária sob BH-FDR** (11 testes): H1a {agrupado, soja, milho} (3) + H1b {soja, milho}
× `h∈{3,4,5,6}` (8).

**Regra do portão (pré-registrada).** O portão **passa** se o `β` agrupado de H1a for `< 0` e
significativo após BH-FDR sobre a família; H1b corrobora fisicamente. Se H1a falhar (sinal
errado ou não-significativo), **paramos e reformulamos** — o achado negativo vai para o
relatório, não é escondido. As sub-amostras dev/holdout são reportadas para transparência; a
decisão usa o span cheio (D-029).

**Custo/limitação**: N efetivo pequeno por construção (H1a ~8 safras-cluster; H1b ~8–9). O
teste tem pouco poder para efeito pequeno — declarado desde já (`00_PLANO_MESTRE` §6, limitação
nº 1). A revisão log acumulada e o `Shock` acumulado crescem ambos ao longo da safra; o
agrupamento por safra trata a dependência serial intra-safra, mas o sinal não é mero
co-tendência (o `z` de déficit sobe e desce conforme a chuva). Robustez à forma incremental
(Δ entre levantamentos consecutivos) fica para a suíte, não para o primário.

---

### D-031 — Resultado do portão da Fase 2: mecanismo confirmado, seguimos para a Fase 3
**Data**: 2026-07-17

Rodada **única** dos rodadores pré-registrados em D-030, sobre o painel municipal CHIRPS
completo (6.197 rasters, 2015/16–2024/25 prelim + 2000–2023 final; manifesto
`chirps_h1_bulk`). Artefatos em `data/processed/` (`h1a_results.csv`, `h1b_results.csv`,
`gate_family_fdr.csv`).

**H1a — o choque prevê a revisão da CONAB. CONFIRMADO.** 729 observações
`(cultura×UF×safra×levantamento)`, 8 safras (2017/18–2024/25):

| Escopo | β (revisão log por unidade de `Shock`) | t (cluster) | N | clusters |
|---|---|---|---|---|
| Agrupado (span cheio) | **−0,0672** | −5,96 | 729 | 8 |
| Desenvolvimento (≤2019/20) | −0,0567 | −6,02 | 276 | 3 |
| Holdout (2020/21–2024/25) | −0,0715 | −4,21 | 453 | 5 |
| Só soja | −0,0674 | −4,50 | 539 | 8 |
| Só milho 2ª | −0,0664 | −3,76 | 190 | 8 |

Sinal **negativo** como pré-registrado (estresse ⇒ safra revisada para baixo). Magnitude
econômica material: +1 unidade de `Shock` (≈1 desvio mais seco que a climatologia) ⇒ ~6,7% de
revisão para baixo da estimativa — coerente com as revisões de ~15% (≈2σ) observadas em anos de
seca. **O efeito aparece igual no desenvolvimento e no holdout, e nas duas culturas** — não é
artefato do período lacrado (o reporte separado de D-029 serviu exatamente para checar isso).

**Inferência honesta com poucos clusters**: o p-valor assintótico normal (2,6e-9) é otimista
com apenas 8 clusters. O honesto é `t(G−1=7)` **p ≈ 5,7e-4**, e o **pairs cluster bootstrap dá
p ≈ 0** com IC [−0,084; −0,050] inteiramente negativo. As três formas de H1a (agrupado, soja,
milho) sobrevivem ao BH-FDR da família de 11 testes com folga.

**H1b — exportação física (ex post, corroboração, 7 safras).** Soja responde ao choque no 3º e
no 6º mês após a colheita (β=−0,32 e −0,35; ambos sobrevivem ao BH-FDR); milho 2ª tem todos os
coeficientes no sinal esperado exceto um, nenhum significativo. Corroboração **parcial**,
coerente com o poder baixíssimo (N=7) e com o ruído de exportação — H1b nunca foi o motor do
veto (D-030).

**Veredito (regra de D-030): PORTÃO ATRAVESSADO.** A cadeia causal postulada — choque climático
→ revisão da safra CONAB — existe e é forte, dentro e fora da amostra. **Seguimos para a Fase
3** (matriz de exposição e construção da carteira). Isto **não** é um retorno de estratégia:
nenhum preço de ação foi tocado; o holdout de retornos (Fase 6) permanece lacrado.

**Custo/limitação declarado**: N efetivo pequeno (8 safras-cluster) — o poder vem da magnitude
grande e da consistência dev/holdout, não de N. A revisão e o `Shock` acumulam ambos na safra;
o bootstrap por cluster e a consistência entre sub-amostras endereçam o risco de co-tendência,
mas a robustez à forma incremental e ao lag do `Shock` fica para a Fase 5. H1b permanece ex
post e nunca dimensiona (R18/D-026).

---

### D-032 — Operacionalização point-in-time da matriz fundamentalista antes da classificação
**Data**: 2026-07-17

O Método A de D-007 passa a ter uma regra mecânica, registrada **antes de materializar a
matriz** e sem consultar retornos:

```text
E(i,c) = direction(i) * materiality(i) * crop_weight(i,c)
```

- `direction` vale `+1` para venda direta recorrente do grão e `-1` para compra direta como
  insumo produtivo; canais indiretos ou de direção líquida ambígua são inelegíveis;
- `materiality` é ordinal: `1` para canal ≥50% do consolidado, `0,5` para 10%–50%, `0,25`
  para canal direto <10% ou sem percentual separável, e `0` para indireto/ambíguo;
- `crop_weight` usa abertura por receita/custo, depois volume/área; cesta soja+milho sem
  abertura recebe divisão igual marcada e vai à sensibilidade.

Cada vintage carrega `ref_date`, `avail_date` e fonte. O último vintage integral disponível em
`t` é usado; não existe preenchimento para trás. A matriz e a auditoria de candidatos ficam em
`13_MATRIZ_EXPOSICAO.md` e no registro versionado consumido pelo código.

**Por quê.** Percentuais contábeis de empresas diferentes não são diretamente comparáveis:
receita de cultura para produtor e custo de ração para processador medem objetos distintos. A
faixa ordinal preserva materialidade sem fabricar precisão; a composição dentro da empresa
mantém a informação de soja versus milho. A exclusão conservadora impede que logística,
sementes ou insumos recebam sinal só para aumentar o número de ações.

**Custo/limitação.** Os degraus 0,25/0,50/1 e a divisão igual de cesta agregada são hipóteses
de modelagem. Serão submetidos a sensibilidade, mas não escolhidos por retorno. A regra pode
reduzir o núcleo histórico abaixo dos ~14 nomes imaginados na ideação e expor concentração
maior que a prevista; se isso ocorrer, o protocolo de carteira será ajustado antes de qualquer
backtest, com nova decisão explícita — nunca com inclusão oportunista de nomes indiretos.

---

### D-033 — Resultado da matriz fundamentalista: quatro nomes diretos e concentração material
**Data**: 2026-07-17

A regra D-032 foi aplicada depois de sua pré-especificação no histórico e sem consultar
retornos. O registro versionado contém cinco vintages para quatro empresas:

- produtores: AGRO3 (`E>0`, desde 31/10/2014) e SLCE3 (`E>0`, desde 07/03/2018);
- processadores: BRFS3 (`E<0`, desde 31/03/2014; magnitude atualizada em 27/04/2018) e
  JBSS3 (`E<0`, desde limite conservador de 01/07/2015).

Todos os demais 17 candidatos foram recusados no primário por cultura fora do escopo, canal
indireto, direção líquida ambígua ou ausência de evidência admissível. A auditoria completa e
as fontes estão em `13_MATRIZ_EXPOSICAO.md`; o registro consumido pelo código está em
`data/reference/exposure_fundamental_v1.json`.

**Consequência.** A mitigação anterior de R7 — ampliar o núcleo para cerca de 14 adjacentes —
era incompatível com o critério causal que acabamos de congelar e foi retirada. Com
neutralidade 0,5/0,5, o único produtor até março de 2018 exige 50% do bruto; depois, dois
produtores exigem ao menos 25% cada. O cap de 20% não fecha a carteira em nenhum trecho e
reduzir o bruto não resolve um limite expresso como porcentagem do próprio bruto. R19 passa a
bloquear o próximo passo de construção até uma decisão separada, ainda sem retornos.

**Custo/limitação.** O Método A ganha auditabilidade e perde diversificação. JBSS3 usa a
participação do segmento JBS Foods como limite de materialidade e uma data conservadora de
disponibilidade; as cestas agregadas de BRFS3/JBSS3 usam 50%/50% e exigem sensibilidade. O
Método B poderá medir discordâncias, mas não corrigirá retroativamente o Método A.

---

### D-034 — Fase 3.1 audita canais empresariais antes de score e carteira
**Data**: 2026-07-17

A matriz D-033 é point-in-time e auditável, mas ainda representa exposição ao encarecimento do
grão, não o efeito líquido completo sobre lucro. Para produtores, o benefício de preço e a
perda de volume próprio têm sinais opostos; geografia e hedge podem decidir qual domina. Além
disso, quatro ações não sustentam o H3/Fama–MacBeth originalmente descrito, e dollar-neutral
não equivale a market-neutral.

Por isso, uma **Fase 3.1** passa a bloquear score, carteira e qualquer retorno de ação. Seu
protocolo está em `14_AUDITORIA_CANAIS_EMPRESARIAIS.md` e exige:

1. auditoria PIT de mix, geografia produtiva, canal de preço/insumo, hedge e perímetro;
2. decomposição candidata entre benefício de preço (`P`), dano de volume próprio regional
   (`Q`) e custo de insumo (`C`), sem fabricar granularidade ausente;
3. H2a preditivo em futuros como portão econômico, executado apenas no desenvolvimento;
4. H2b de reação à divulgação da CONAB como diagnóstico, não veto isolado;
5. substituição do H3/Fama–MacBeth por desenho compatível com três a quatro ações;
6. resolução de R19 e correção da linguagem de neutralidade antes de construir a carteira.

**Custo/limitação.** A Fase 3 fica mais longa e pode concluir que o canal líquido do produtor
é indeterminado ou que o universo não comporta uma estratégia investível. Esse é um custo
menor do que transformar uma matriz auditável, porém economicamente incompleta, em um Sharpe
sem interpretação causal. A matriz D-033 não é reescrita: permanece como registro do canal de
preço/insumo e só será promovida ou decomposta após o novo portão.

---

### D-035 — Resultado da auditoria dos canais empresariais: manter D-033, long condicionado a H2a
**Data**: 2026-07-18

A auditoria PIT dos quatro nomes (protocolo `14_AUDITORIA_CANAIS_EMPRESARIAIS.md`) foi
concluída **sem consultar nenhum retorno de ação**. Registro estruturado por nome/vintage/
fonte/localizador/lacuna em `data/reference/corporate_audit_v1.json`; resultado narrado em
`14` §9. Fontes primárias lidas: 20-F BrasilAgro FY2014/FY2019 (SEC CIK 1499849), 20-F BRF
FY2017 (CIK 1122491), 10-K Pilgrim's Pride FY2018 (CIK 802481); SLCE3 e a JBS consolidada
sobre a âncora datada de D-033 + geografia pública, com números finos declarados como lacuna.

**O que foi decidido.**
1. As **direções de D-033 são defensáveis** (produtores +, processadores −).
2. **`P` e `Q` não são PIT-separáveis**: área plantada por cultura×UF×vintage e % de hedge são
   lacunas declaradas. Por `14` §3 e `13` §7, a ausência é limite de identificação, não
   preenchida ⇒ **mantém-se a matriz D-033 (opção 1)**, sem termo `Q` separado nem score
   `P/Q/C` explícito.
3. A **materialidade efetiva é atenuada** em todos (cana na AGRO3 subiu a 48% da receita
   operacional em FY2019; algodão na SLC; bovino + insumo US/Europa na JBS; hedge; geografia
   fora do Shock — PI/Paraguai, MA/PI/PA). Entra como **haircut candidato e eixo de
   sensibilidade** no congelamento do score (só no desenvolvimento), **sem reescrever** o
   registro congelado D-033.
4. O **lado long fica condicionado a H2a**: `Q` parcialmente fora do Shock faz `P` tender a
   dominar, mas o líquido do produtor não é resolvível só pelo fundamento. Se H2a falhar, o
   long é reformulado.
5. **Nenhum novo nome direto**: os vetos de D-033 se mantêm; a concentração não é diluível por
   nomes diretos.

**Por quê.** O objetivo do portão (D-034) era impedir que uma direção econômica ambígua
virasse posição por uma fórmula simples demais. A auditoria mostrou que a ambiguidade do
produtor se resolve **por evidência de geografia (Q parcial) + dependência de H2a**, não por
presunção — e que a granularidade para um `Q` próprio não existe de forma PIT-reproduzível.
Manter D-033 com essas ressalvas é mais honesto que fabricar um `Q` sem fonte.

**Custo/limitação.** Não decompor `P/Q` é assumir um limite de identificação: o sinal segue
sendo o canal de preço/insumo de D-033, com a ponta long dependente de H2a e a materialidade
real abaixo da participação de receita. R20 passa a **endereçado** (por evidência, condicionado
a H2a), R21 a **mitigado com lacunas declaradas**; R19 (concentração) permanece **aberto** —
a auditoria confirma que não há como diluí-lo adicionando nomes diretos.

---

### D-036 — Pré-registro de H2a: transmissão do Shock ao preço mundial (portão do lado long)
**Data**: 2026-07-19

Especificação **congelada antes de qualquer resultado** (a ordem é provada no histórico do
git: este commit precede o commit do resultado). Implementação em `stats/h2a.py`,
`ingest/fred_prices.py`, `scripts/run_h2a.py`, testes em `tests/test_h2a.py`.

**Hipótese.** O `Shock` brasileiro já disponível em `t` antecipa a valorização do preço mundial
da commodity, no sinal esperado `β>0` (estresse ⇒ menos oferta ⇒ preço sobe — oposto de
H1a/H1b). Sustenta o canal de preço `P` do lado long; se falhar, o long é reformulado.

**Fonte do desfecho.** Preço-referência mundial (FRED/IMF Primary Commodity Prices), USD/t,
mensal: soja `PSOYBUSDM`, milho `PMAIZMTUSDM`. Escolha justificada economicamente: o produtor
é *price-taker* desse preço (o 20-F da BrasilAgro declara a soja precificada na CBOT; D-035).
Preço é vintage-estável (não reescrito como CONAB/NEFIN); captura datada + manifesto por
disciplina. Não gera posição/sizing — só desfecho de H2a.

**Regressor.** `Shock` **nacional** as-of `t` (contrato D-028, pesos da safra CONAB anterior),
computado em **cada fim de mês dentro da janela** fenológica — por isso só de 2018/19 em diante.

**Desfecho e timing PIT.** Para observação no fim do mês `m`, retorno forward
`r = log(P[m+h]/P[m])`, inteiramente posterior a `t`. Ressalva declarada: o IMF publica `P[m]`
~3 semanas depois ⇒ lag de **execução**, não look-ahead (o `Shock` usa só chuva ≤ `t`; o
retorno é todo futuro). Horizonte primário `h=3`; `h∈{1,2,3}` como robustez.

**Perímetro (aplica o princípio de D-029/PT-001).** H2a é teste de **mecanismo** físico-
econômico, como H1: roda no **span cheio 2018/19–2024/25** com sub-amostras dev (≤2019/20) e
holdout reportadas em separado. O veredito do portão olha o agregado; o desenho da carteira
permanece calibrado só no desenvolvimento. Isto **reconcilia** `14` §5, que originalmente
restringia H2a a dev — mudança de desenho registrada aqui, com custo declarado.

**Inferência.** OLS com erros agrupados por `ano-safra × cultura`; pooled com efeito fixo de
cultura (demeaning intra-cultura); *pairs cluster bootstrap*. N efetivo reportado. Span cheio
≈ 14 clusters; dev ≈ 4 (consistência, não motor).

**Regra do portão (direcional + ressalva; ratificada com o usuário).** No `h` primário, span
cheio, pooled: `β>0` e p unilateral (bootstrap) < 0,10 ⇒ **PASSA**; `β>0` sem significância ⇒
**INCONCLUSIVO** (o long segue com ressalva explícita, a confirmar no holdout); `β<0`
significativo ⇒ **REPROVA** (reformula o lado long).

**Custo/limitação.** Poder baixo por N pequeno (safra é anual): um `β>0` fraco não distingue
"efeito ausente" de "amostra curta" — por isso a regra é direcional, não veto por significância.
Usar span cheio dá poder mas deixa o comportamento de preço do período de holdout informar a
decisão do portão; aceito porque é mecanismo físico, não retorno da estratégia, e o desenho da
carteira segue lacrado ao holdout. FRED mensal ≠ preço diário; o lag de execução é declarado.

---

### D-037 — Resultado de H2a: transmissão ao preço mundial NÃO confirmada (inconclusivo-negativo)
**Data**: 2026-07-19

Rodada única do spec pré-registrado D-036, sem mudar nada após ver o número. Artefatos em
`data/processed/h2a_{panel.parquet,results.csv}`. 147 obs, 7 safras, 14 clusters (dev 42 obs /
4 clusters; holdout 105 / 10).

**Resultado primário (h=3, span cheio, pooled): β = −0,0166; INCONCLUSIVO.** p unilateral do
lado esperado (β>0, bootstrap por cluster) = 0,887; p do lado negativo = 0,113 — negativo, mas
não significativo ao nível pré-registrado de 0,10. Pela regra congelada (β<0 **não**
significativo ⇒ inconclusivo), o portão **não reprova**, mas também **não confirma** o canal de
preço.

**O ponto estimado é do sinal ERRADO.** Esperávamos β>0 (estresse ⇒ preço sobe). Quase todas as
especificações dão β<0: full pooled h1 = −0,0136 (lado negativo p≈0,002, **significativo**),
h2 = −0,0149, h3 = −0,0166; soja full h3 = −0,041; milho full h3 = −0,010. A exceção é soja
**dev** (β>0), mas com N=8 e 2 clusters o bootstrap é não confiável e não sobrevive ao span
cheio.

**Duas leituras não excludentes (declaradas, não resolvidas):**
1. a transmissão do choque brasileiro ao preço **mundial em USD** é fraca/ausente — o preço
   global responde a oferta/demanda mundial, câmbio e safra dos EUA, e o Brasil é um driver
   entre muitos;
2. o preço reage de forma **contemporânea/antecipada** ao choque e depois reverte à média, o
   que torna um teste **forward** (a partir da data do choque) cego a um efeito real já
   incorporado ao nível de preço em `t`. Isto foi antecipado no custo/limitação de D-036.

Distinguir (1) de (2) exige um diagnóstico **contemporâneo** (variação do preço **dentro** da
janela vs. Shock), que **não foi rodado** para não virar um resgate post-hoc do resultado.

**Limitação da fonte (não é resgate).** O preço mundial em USD ≠ receita do produtor em BRL
(câmbio + base brasileira). Um teste com preço brasileiro (CEPEA/B3, BRL) pode mostrar
transmissão que o USD esconde, mas **só como robustez pré-registrada** (D-025), com sua própria
justificativa — nunca substituindo o primário depois de ver que o primário não deu o esperado.

**Consequência.** O canal de preço `P` do lado long **não recebeu suporte empírico** do teste
pré-registrado; o estimador aponta para o lado contrário. Pela regra, o long só poderia seguir
com ressalva forte e confirmação obrigatória no holdout — mas um ponto de sinal errado é um
alerta, não um sinal verde. A decisão de reformular o lado long, pré-registrar os diagnósticos
contemporâneo/BRL, ou reduzir a tese ao lado processador fica para o próximo passo, com novo
go-ahead. **R20 volta a preocupar**: sem transmissão forward comprovada, a dominância de `P`
sobre `Q` no produtor não está sustentada.

**Custo/honestidade.** Este é o resultado que o pré-registro existe para proteger: a fonte,
o horizonte e a regra foram fixados antes; o número veio contrário à tese e é reportado como
veio. Nenhuma troca de fonte ou horizonte foi feita para melhorá-lo.

---

### D-038 — Pré-registro dos diagnósticos de H2a: contemporâneo e BRL (não-veto)
**Data**: 2026-07-20

Especificação **congelada antes do resultado** (ordem provada no git). Implementação em
`stats/h2a.py` (`build_h2a_diag_panel`, `run_h2a_diag`), `ingest/fred_prices.py` (câmbio),
`scripts/run_h2a_diag.py`. Motivação: D-037 deu forward-negativo ao preço mundial USD, com duas
leituras não distinguíveis (transmissão fraca ao USD vs. reação contemporânea + reversão
invisível a um teste forward). Estes diagnósticos separam as leituras **sem** trocar o primário
de H2a (isso seria resgate post-hoc); são diagnósticos, **sem poder de veto próprio**.

**Fonte adicional.** Câmbio BRL/USD mensal FRED `EXBZUS` (vintage-estável, sem chave). Preço em
BRL = preço mundial USD × câmbio — proxy da receita do produtor pelo canal de câmbio.

**Testes (todos com sinal esperado `β>0`), regressor = Shock nacional as-of `t`:**
- `contemp_usd` / `contemp_brl`: `log(P[m]/P[base])`, base = mês anterior ao início da janela —
  mede se o preço JÁ se moveu com o choque **dentro** da janela. É **contemporâneo**, não
  preditivo ⇒ diagnóstico explicativo, **nunca vira sinal negociável**;
- `fwd_usd` / `fwd_brl`: `log(P[m+3]/P[m])` no horizonte primário — compara com D-037 e isola o
  canal de câmbio (BRL vs USD).

**Inferência e perímetro.** Iguais a H2a: cluster por ano-safra × cultura + bootstrap; pooled
com efeito fixo de cultura; span cheio com dev/holdout separados. Diagnóstico, não portão.

**Regra de leitura (pré-registrada).**
1. se `contemp_*` `β>0` significativo (USD ou BRL) ⇒ o preço reage **contemporaneamente** ao
   choque (leitura 2); o forward-negativo de D-037 é reversão, não ausência de transmissão ⇒ o
   canal de preço `P` é plausível e o long pode seguir com ressalva e confirmação no holdout;
2. se `fwd_brl` `β>0` enquanto `fwd_usd` ~0/negativo ⇒ a transmissão está no **câmbio/base** ⇒
   canal `P` via BRL;
3. se todos forem nulos/negativos ⇒ leitura 1 (sem transmissão) confirmada ⇒ reduzir a tese ao
   lado processador (canal `C`, D-035) ou reformular o long.

**Custo/limitação.** O contemporâneo não é preditivo — informa a economia, não gera posição.
BRL via (mundial × câmbio) é proxy: falta a **base local** brasileira (CEPEA), declarada como
robustez futura, não reconstruída aqui. N pequeno (safra anual) ⇒ leitura direcional, não veto.

---

### D-039 — Resultado dos diagnósticos: canal de preço mundial NÃO resgatado; resta o local (CEPEA)
**Data**: 2026-07-20

Rodada única do spec pré-registrado D-038, sem alterar nada após ver o número. Artefatos em
`data/processed/h2a_diag_{panel.parquet,results.csv}`. 49 obs, 14 clusters.

**Leitura confiável (pooled, span cheio, 14 clusters):**

| Desfecho | β (esperado >0) | p unilateral (bootstrap) |
|---|---|---|
| contemporâneo USD | −0,0013 | 0,54 |
| contemporâneo BRL | +0,0045 | 0,39 |
| forward USD (= D-037) | −0,0166 | 0,89 |
| forward BRL | +0,0041 | 0,43 |

**Nenhum é significativo.** Aplicando a regra de leitura de D-038:
1. o **contemporâneo** deu ≈ zero (não positivo significativo) ⇒ a leitura "o preço reage
   dentro da janela e reverte" **não se sustenta**; o forward-negativo de D-037 não é artefato de
   reversão de um efeito contemporâneo — o efeito contemporâneo também está ausente;
2. a conversão para **BRL** vira o forward de −0,017 (USD) para +0,004, direção coerente com um
   canal de **câmbio**, mas não significativo ⇒ sinal fraco, não conclusivo;
3. no nível do preço **mundial** (USD) e do proxy **mundial×câmbio** (BRL), o quadro é de
   **nulo generalizado**.

**Conclusão honesta.** O canal de preço `P` do produtor, medido no preço mundial e no proxy
BRL, **não tem suporte empírico**. A ponta long "comprar produtor porque o choque eleva o preço
que ele recebe" não se confirmou em quatro medidas (forward/contemporâneo × USD/BRL).

**A porta que resta é distinta, não é insistência.** O proxy BRL = mundial × câmbio **não** tem
a **base local** brasileira (CEPEA/ESALQ), e é justamente o preço **local** que um choque
doméstico moveria primeiro (oferta/logística/basis interno). Além disso, o preço local é o preço
**economicamente certo para o lado processador** (a BRF compra milho **brasileiro**, D-035),
que estes diagnósticos **não** testaram e **não** derrubam. Um pequeno indício positivo aparece
só no milho contemporâneo (holdout significativo, N pequeno), não na soja.

**Consequência.** Evidência forte contra o long de produtor pelo **preço mundial**. O teste
decisivo restante é o **preço local CEPEA** (pré-registrado como robustez em D-038/D-025), que
resolve tanto o preço realizado do produtor quanto o custo do processador. Recomenda-se como o
**último** teste de preço antes de decidir o rumo: se o CEPEA também for nulo, o mecanismo de
preço está morto e a tese precisa ser reformulada ou reduzida; se o CEPEA local transmitir, o
lado **processador** (canal `C`) é o sobrevivente natural. R20 permanece 🔴; o passo do preço na
cadeia clima→safra→**preço**→ação está sob dúvida direta, o que aproxima R2 (estratégia ser só
beta de commodity) do centro da discussão.

**Custo/honestidade.** Quatro medidas de preço pré-registradas deram nulo e foram reportadas
como vieram. Nenhuma foi trocada ou re-especificada para melhorar. O CEPEA é uma fonte
economicamente distinta (base local), não uma quinta tentativa da mesma coisa — mas será o
último teste de preço, para não virar busca por especificação.

---

### D-040 — Pré-registro do último teste de preço: transmissão ao preço LOCAL brasileiro
**Data**: 2026-07-20

Especificação **congelada antes do resultado** (ordem provada no git). Implementação em
`ingest/ipea_prices.py`, `stats/h2a_local.py`, `scripts/run_h2a_local.py`. É o **último** teste
de preço da tese (regra de parada declarada), não uma quinta tentativa da mesma medida: o preço
**local** brasileiro é economicamente distinto do mundial (embute a base doméstica) e é o preço
que o produtor de fato recebe e o processador de fato paga.

**Fonte e substituição declarada.** A referência de preço local (CEPEA/ESALQ) está atrás de
Cloudflare, sem acesso programático reproduzível (D-025) — confirmado nesta sessão. Uso, no lugar,
o **IPEADATA** (IPEA, governo federal), que espelha com API OData aberta e sem chave a série da
**Seab-PR/DERAL** do **preço recebido pelo agricultor** (soja `DERAL12_PRSO12`, milho
`DERAL12_PRMI12`, R$/60kg, mensal). Para o lado produtor é ainda mais direto que o CEPEA: é a
receita realizada, não o FOB porto. A escolha foi feita e commitada **antes** de ver o resultado.

**Desenho.** Idêntico a H2a/D-038 mudando só a fonte de preço: regressor = `Shock` nacional
as-of fim de mês na janela; desfechos = contemporâneo `log(P[m]/P[base])` (base = mês anterior à
janela) e forward `log(P[m+3]/P[m])`; sinal esperado `β>0`. Inferência cluster por ano-safra ×
cultura + bootstrap; pooled com efeito fixo de cultura; span cheio com dev/holdout separados.

**Regra de leitura (regra de parada).** Se algum desfecho pooled span-cheio tiver `β>0` com p
unilateral < 0,10 ⇒ o choque **transmite ao preço local** ⇒ o canal de preço vive no mercado
brasileiro (favorece o lado **processador**, canal `C`, e valida a receita realizada do
produtor); a estratégia segue com esse canal. Se **todos** forem nulos/negativos ⇒ soma-se aos
quatro nulos de D-037/D-039 e o **mecanismo de preço da tese está morto** ⇒ reformular o gatilho
(ex.: usar o corte da CONAB como sinal direto) ou reduzir/abandonar. **Nenhum outro teste de
preço será rodado depois deste**, para não virar busca por especificação.

**Custo/limitação.** É preço do **Paraná** (Seab-PR), não nacional — mas PR é UF primária e o
mercado brasileiro é integrado por arbitragem/exportação. Pode sofrer revisão modesta (captura
datada + manifesto; `avail_date` = fim de mês + 30 dias). N pequeno ⇒ leitura direcional.

---

### D-041 — Resultado do teste local: sinal CERTO mas sem poder; mecanismo de preço não provado
**Data**: 2026-07-20

Rodada única do spec pré-registrado D-040. Artefatos em `data/processed/h2a_local_*`. 49 obs,
14 clusters. Preço local recebido pelo agricultor (IPEADATA/DERAL-Seab-PR, R$/60kg).

**Leitura confiável (pooled, span cheio, 14 clusters):**

| Desfecho | β (esperado >0) | p unilateral (bootstrap) |
|---|---|---|
| contemporâneo local | +0,0071 | 0,33 |
| forward local | +0,0310 | 0,21 |

**Veredito pré-registrado: NÃO transmite** ao nível de 0,10 — nenhum dos dois cruza o limiar.

**Mas é qualitativamente diferente do preço mundial.** Ao contrário de D-037/D-039 (forward
mundial negativo, contemporâneo ≈ zero), aqui **os dois desfechos têm o sinal CERTO (positivo)**,
e o `forward local` (+0,031) é a **maior estimativa positiva** de todas as seis medidas de preço;
o holdout confirma o sinal (`fwd_local` +0,040). O milho contribui positivo no contemporâneo; a
soja é a ponta fraca. É o padrão de um efeito **direcionalmente real, porém sem poder** — com
~7 anos-safra, o intervalo não exclui zero.

**Conclusão (fecha a família de testes de preço).** Em **seis** medidas pré-registradas (4
mundiais + 2 locais), **nenhuma** atinge significância. O elo produção→preço→retorno **não está
estatisticamente estabelecido** como preditor. O preço **local** aponta na direção certa, o que
é consistente com uma transmissão **local/base** real mas fraca; o preço **mundial** não. A
limitação é de fundo: o sinal só existe desde 2015/16, ~7–10 anos-safra — pouco para provar um
elo mensal ruidoso. **Nenhum teste de preço adicional será rodado** (regra de parada de D-040).

**Consequência para a tese.** A força **testada** da tese é o elo clima→revisão de safra
(H1/D-031, forte e robusto), não o elo produção→preço→ação (fraco/subdimensionado). Decisão do
próximo passo (novo go-ahead): reformular o sinal para se apoiar no elo provado (usar o
corte/revisão da CONAB como gatilho direto, tratando o preço como racional econômico e não como
preditor testado), reduzir o escopo, ou aceitar com ressalva explícita. R20 permanece 🔴; R2
(ser só beta de commodity) segue no centro. O sinal local positivo **atenua** — não elimina — a
leitura de "sem transmissão".

**Custo/honestidade.** Seis medidas de preço pré-registradas, todas reportadas como vieram;
nenhuma trocada ou re-especificada. A regra de parada foi respeitada: o teste local era o último.

---

### D-042 — Roteiro pós-preço e pré-registro do teste de reação das ações (Fase 3.2)
**Data**: 2026-07-20

**Contexto.** A família de testes de preço (D-036–D-041) fechou sem transmissão significativa; a
força testada da tese é clima→revisão CONAB (H1). Antes de reformular ou expandir, falta testar o
elo que nunca foi tocado: **as ações expostas reagem?** Decisão de roteiro acordada:

1. **agora (barato)**: testar a reação das ações na versão soja+milho / 4 nomes, **só no
   desenvolvimento** — retorno de ação é o que o holdout protege;
2. **expandir por cultura** (algodão, cana) **só se** o teste mostrar sinal de vida — cada
   cultura é um canal independente pré-registrado (janela, sinal, UFs, nomes), motor reaproveitado;
3. **congelar uma vez** e rodar o **holdout uma vez**. Adiar a decisão de expandir é permitido;
   adiar para **depois** do holdout, não (seria segundo olhar no holdout). R7/R19/R22 (N pequeno)
   permanecem; a expansão por cultura é a única forma *de princípio* de crescer (não afrouxar a
   régua de nomes nem minerar betas — isso seria seleção pelo resultado).

**Pré-registro do teste (congelado antes do resultado; ordem provada no git).** Implementação em
`scripts/build_equity_returns.py`, `stats/equity_reaction.py`, `scripts/run_equity_reaction.py`.

- **Universo**: os 4 nomes diretos, com entrada PIT pelos vintages da matriz (`exposure_asof`).
- **Sinal**: score `S_i(t) = Σ_c E_i,c(t) · Shock_c(t)` — matriz de exposição as-of `t` × Shock
  nacional as-of `t` (cultura com janela não iniciada contribui 0). Observado em fins de mês
  dentro das janelas das culturas, nas safras de desenvolvimento (2015/16–2019/20). O Shock
  nacional aqui é **equal-weighted** entre as UFs primárias (não a ponderação D-028 por safra
  CONAB anterior, que só existe de 2017/18 e reduziria o dev a 2 safras): simplificação
  **declarada** para o diagnóstico cobrir o desenvolvimento inteiro (5 safras); a ponderação de
  produção D-028 fica para o backtest congelado.
- **Desfecho**: retorno total forward do nome sobre os próximos `H=21` pregões, com execução em
  **D+1** (motor de retorno total PIT, D-014).
- **Teste primário**: painel pooled com retorno **demeanado na seção transversal por data**
  (remove o componente comum/mercado) regredido no score demeanado; OLS agrupado por ano-safra +
  bootstrap. Sinal esperado `β>0` (nome com score maior rende mais que os pares na mesma data).
  Neutro a mercado por construção.
- **Secundário**: retorno médio forward da carteira dollar-neutral ponderada pelo score (o P&L) e
  por nome.
- **Perímetro**: **desenvolvimento apenas** (≤2019/20); holdout 2020-2025 lacrado.
- **Regra de leitura (direcional, amostra pequena)**: `β>0` com p unilateral < 0,10 ⇒ o sinal
  ordena os nomes ⇒ o mecanismo chega ao equity ⇒ vale congelar e considerar a expansão por
  cultura. Nulo/negativo ⇒ a reação não aparece nem no desenvolvimento ⇒ reconsiderar antes de
  gastar o holdout.

**Custo/limitação.** Dev tem ~2-5 safras e 4 nomes (SLCE3 só a partir de 2018) ⇒ baixo poder; é
diagnóstico direcional, não veredito de lucro. Eventos B3 vêm de endpoint frágil (retentativa no
build). Nenhuma medida será trocada após ver o resultado.

---

### D-043 — Resultado da reação das ações: sinal ANTI-preditivo no dev; a estratégia não traduz
**Data**: 2026-07-20

Rodada única do spec pré-registrado D-042. Artefato em `data/processed/equity_reaction_panel.parquet`.
81 obs (data×nome), 24 datas, **4 safras** (2015/16–2018/19; 2019/20 sai por falta de retorno
forward — os preços de dev terminam em 12/2019), 4 clusters.

**Resultado primário (painel demeanado, β>0 esperado):**

| Métrica | Valor |
|---|---|
| β (score→retorno) | **−0,091** |
| t | −3,60 |
| IC 90% | [−0,141, −0,042] — **exclui zero pelo lado negativo** |
| p unilateral (esperado) | 1,000 |
| P&L carteira dollar-neutral | **−3,97%/período**, hit-rate **12%** |
| corr score×retorno por nome | AGRO3 −0,27 · BRFS3 −0,16 · JBSS3 −0,46 · SLCE3 −0,82 (**todas negativas**) |

**Veredito: reage=False — e pior, o sinal é significativamente ANTI-preditivo no desenvolvimento.**
A carteira long-produtor/short-processador com o sinal do choque climático **perde** (ganha em só
12% dos períodos) e a relação score→retorno é **do sinal contrário** ao pré-registrado, consistente
nos quatro nomes.

**Leitura econômica (coerente com tudo).** O sinal negativo é economicamente plausível e bate com
a auditoria (D-035) e com a família de preço (D-041): para o **produtor**, o dano de volume próprio
`Q` (a seca corta a colheita dele) **domina** o benefício de preço `P` — que mostramos ser fraco.
Logo a seca **prejudica** o produtor, e a ponta long perde. R20 se resolve empiricamente: o líquido
do produtor é **negativo**, não positivo.

**Disciplina — o que NÃO se faz.** Inverter o sinal ("então short produtor / long processador,
que aí ganha") depois de ver o resultado do dev é **exatamente** o p-hacking discutido: um sinal
escolhido pela amostra de dev pareceria ótimo em dev por construção e provavelmente falharia fora
dela. O resultado é reportado como veio. "A seca prejudica o produtor (Q>P)" vira uma **hipótese
nova a pré-registrar e testar de forma independente** (idealmente confirmada em dado não usado),
nunca um gatilho para inverter e backtestar.

**Consequência.** A estratégia, como desenhada (long/short pelo choque climático), **não se traduz
em retorno de ação** no desenvolvimento — o mecanismo clima→revisão CONAB é real (H1), mas não
produz o payoff acionário previsto. Por D-042, **não** se congela nem se gasta o holdout com este
sinal. Ponto de decisão do projeto: reformular a tese com hipótese nova pré-registrada (ex.: a
direção Q-dominante, testada de forma limpa), reduzir o escopo, ou reportar o achado negativo com
rigor. A expansão por cultura **não** deve ser paga sobre um sinal que perde no dev. R2 sai do
centro para a periferia: não é "só beta de commodity" — é que a ponta long tem o sinal invertido.

**Custo/honestidade.** Amostra pequena (4 clusters) ⇒ sem p-valor preciso, mas a direção, a
magnitude (t=−3,6) e a consistência nos 4 nomes rejeitam decisivamente o "reage positivamente"
pré-registrado. Nenhuma medida trocada após ver o número; o sinal não foi invertido.

---

### D-044 — Reformulação Q-dominante: hipótese derivada, não invertida; protocolo anti-p-hacking
**Data**: 2026-07-20

D-043 mostrou que a estratégia original (long produtor / short processador pelo choque) é
**anti-preditiva** no desenvolvimento. Esta decisão reformula a tese para a direção oposta —
**mas por derivação econômica, não por inversão do sinal olhando o dev.** O que se segue é o
registro que separa as duas coisas e trava o protocolo que impede o p-hacking.

#### 1. A hipótese reformulada (H′)
> Um choque climático adverso **reduz** o retorno das produtoras agrícolas expostas em relação
> aos processadores, porque o dano de volume próprio (`Q`) domina o benefício de preço (`P`).

#### 2. Derivação econômica — H′ era formulável ANTES do teste de ações
Três resultados **anteriores e independentes do retorno de ação** implicam H′:
- **H1 (D-031)**: o choque prevê a **revisão para baixo** da produção CONAB, β=−0,067 por σ de
  estresse (a colheita cai). Medido em estimativa de safra, não em cotação.
- **D-041 (preço)**: o choque **quase não move** o preço recebido pelo produtor (local, +0,031 sem
  significância; mundial nulo/negativo). O produtor **não é compensado** pela quebra.
- **D-035 (auditoria)**: as produtoras têm **volume próprio real** exposto ao choque (fazendas
  atingidas), lido de balanço, não de retorno.

Composição: receita do produtor ≈ **volume × preço**. Se o volume cai (H1) e o preço não sobe
(D-041), a receita cai — e a produtora, cujo `Q` é material (D-035), é prejudicada. **H′ é uma
consequência lógica de três achados que precedem e não usam o β acionário.** O β=−0,09 de D-043 é
**consistente** com H′, não a sua fonte: poderíamos ter previsto o sinal negativo antes de rodar
o teste de ações. Este é o teste-chave de legitimidade — hipótese derivável a priori não é
padrão pescado no resultado.

#### 3. Por que isto NÃO é p-hacking (e o resíduo que assumimos)
- **A direção vem do mecanismo**, não do dado acionário (§2). Não invertemos um sinal; derivamos
  uma hipótese.
- **Resíduo honesto**: nós **vimos** o β<0 do dev. Não dá para des-ver. Consequência inegociável:
  **o desenvolvimento está QUEIMADO para a escolha de direção** — o desempenho de H′ no dev deixa
  de valer como evidência (seria circular), e **não se afina H′ no dev**.
- **O holdout 2020-2025 é a ÚNICA prova de retorno restante** — nunca informou a direção. H′ e a
  estratégia serão **congeladas por inteiro num commit anterior** ao primeiro contato com o
  holdout; roda **uma vez**; reporta-se o que der.
- **Disclosure total no relatório**: a sequência real (apostamos +, preço fraco, `Q` domina,
  reformulamos para −, testamos uma vez no holdout) entra explícita. A transparência é o rigor.

Seria p-hacking se: usássemos o desempenho no **dev** como prova; **iterássemos** H′ no dev;
inventássemos a economia **só** para justificar (não é o caso — D-035/D-041 vieram antes); ou
rodássemos o holdout, não gostássemos, e mexêssemos.

#### 4. Corroboração independente ANTES do holdout (para o holdout não ser o único tiro)
- **(a) Cadeia lógica** — já estabelecida por H1 (volume↓) + D-041 (preço≈flat) ⇒ receita↓. Não
  usa dado novo nem o retorno acionário.
- **(b) Teste de fundamentos** (a construir, pré-registrado aqui): a **receita/margem de grão
  reportada** das produtoras (AGRO3 via 20-F; SLCE3 se obtível) **cai** em anos de choque alto?
  Fonte = demonstração financeira, **independente do retorno de ação e do holdout**. Sinal
  esperado: β<0 (receita/margem de grão vs. Shock da safra). N pequeno ⇒ direcional; corrobora,
  não prova sozinho.

#### 5. O que é congelado agora e o que fica para depois
- **Congelado agora**: H′, a derivação (§2) e o protocolo anti-p-hacking (§3).
- **Depois, em decisão própria, antes do holdout**: a especificação exata da estratégia
  reformulada (universo, direção operacional, sizing, execução) — só então o holdout roda uma vez.
  **Não se paga a expansão por cultura** enquanto H′ não for corroborada.

**Custo/limitação declarado.** O dev está gasto para a direção; vimos o resultado primeiro (e
dizemos isso). O holdout é um tiro único. A corroboração por fundamentos tem N pequeno e, para
SLCE3, dado difícil (pode virar lacuna declarada). Se o holdout desmentir H′, reporta-se o
negativo — a tese vira um achado honesto, não uma curva forçada.

---

### D-045 — Análise de poder: expandir o universo compra conclusividade, não lucro
**Data**: 2026-07-20

Antes de investir na obra da expansão, quantificamos o que de fato importa: a probabilidade de o
teste no holdout dar um **veredito CLARO** (rejeitar na direção certa, α=0,10 unilateral) — não
"dar lucro". Monte Carlo do teste efetivo (demeaning na seção transversal + SE agrupado por
ano-safra), em `scripts/power_analysis.py`. Calibração: |β|≈0,09 é o efeito observado no
desenvolvimento (D-043); ruído idiossincrático do retorno de ~21 pregões varrido em [0,10; 0,16].

**Gargalo estrutural.** O holdout tem **5 anos-safra fixos** (2020/21–2024/25) — não se cria
evento novo ali. O único ajuste operável é o **nº de nomes** (expansão).

**Poder por tamanho do efeito × nº de nomes (holdout, 5 anos, faixa de ruído):**

| β real | 4 nomes (hoje) | 8 nomes (expandido) |
|---|---|---|
| 0,09 (o do dev — grande) | 82–95% | 93–98% |
| 0,05 (metade — moderado) | 56–77% | 72–90% |
| 0,03 (um terço — pequeno) | 37–53% | 51–71% |

IC 90% do β aperta de ±0,028 (4 nomes) para ±0,020 (8 nomes).

**Leitura.**
1. **Não estamos condenados ao inconclusivo.** Se o efeito for do tamanho que o dev mostrou
   (β≈0,09), o holdout é conclusivo com 82–95% já com 4 nomes. Não vamos cegos — o dev
   *detectou* esse efeito (t=−3,6), evidência direta de que ele é grande.
2. O risco de inconclusivo mora só no cenário de **efeito bem menor que o do dev** (β≈0,03–0,05,
   se o t=−3,6 foi parte sorte). Aí a expansão para **~8 nomes** sobe o poder de ~64–77% para
   ~72–90% (moderado) — de "cara ou coroa" para "provavelmente conclusivo".
3. Efeito **minúsculo** (β≈0,03) é inconclusivo mesmo expandido: precisaria de ~15–20 anos-safra,
   que não existem. Limite irredutível — mas um inconclusivo **depois** de um dev fortíssimo é
   ele próprio informativo (indica que o sinal do dev não era robusto).

**Decisão.** **Expandir o universo para ~8 nomes** (algodão nos nomes existentes + cana
SMTO3/JALL3) como **seguro de conclusividade** antes do holdout — não para caçar lucro, mas para
garantir um sim/não limpo se o efeito for pelo menos moderado. Desenho da expansão em D-046.

**Custo/limitação.** A calibração assume que a estrutura do dev vale no holdout; a regressão à
média sugere que β no holdout tende a ser ≤ o do dev, então o caso de planejamento honesto é o
**moderado** (β≈0,05), onde 8 nomes são justificados. Nenhuma expansão salva um efeito minúsculo.

#### Nota de re-análise (2026-07-20) — o universo de ~8 nomes não se materializou

A decisão original assumia chegar a ~8 nomes via algodão (nos nomes existentes) + cana
(SMTO3/JALL3). Depois de executar os dois canais, essa premissa caiu:

- **algodão (D-049)**: não corroborado (β agrupado +0,0421, 0/3 LOO na direção certa). Adiciona
  **0 nome** e não entrega o evento adicional prometido;
- **cana (D-051)**: corroborada só pelo critério direcional, com evidência fraca (p=0,12). Adiciona
  **no máximo 2 nomes** (SMTO3/JALL3), ainda **condicionados** à auditoria PIT do R24.

Universo real, portanto: **4 nomes (core de grãos)**, ou **6 se a auditoria da cana passar** — não
8. Re-rodamos o mesmo simulador de D-045 (`scripts/power_analysis.py::power`, reusado sem
alteração) nessas células, σ=0,13 (caso central), holdout de 5 anos-safra:

| β real | 4 nomes (core grãos) | 6 nomes (+cana, se audit passar) |
|---|---|---|
| 0,09 (o do dev — grande) | 89% | 93% |
| 0,05 (metade — moderado) | 65% | 73% |
| 0,03 (um terço — pequeno) | 45% | 51% |

**Leitura atualizada.**
1. A conclusão qualitativa de D-045 se mantém: com efeito grande (β≈0,09) o holdout é conclusivo
   (~89%) já com 4 nomes; o risco de inconclusivo mora no cenário de efeito moderado/pequeno.
2. **A alavanca "expansão de universo" ficou fraca.** Ir de 4→6 nomes vale só **~+8pp** — não
   muda o regime. A alavanca que moveria o poder de verdade é o nº de anos-safra (5→10 levaria o
   caso moderado de 65%→84%), e ela está **travada em 5**. Não há como comprá-la.
3. Consequência prática: a proteção contra o inconclusivo **não é mais a expansão** (ela entregou
   menos que o assumido em D-045) — é o **tamanho do efeito sobreviver fora da amostra**. O dev
   sugere que sobrevive (t=−3,6), mas isso só se confirma gastando o holdout, tiro único.

Isto **não reabre** nenhum desenho congelado: o universo permanece o de D-046 (com cana ainda sob
R24). A nota apenas corrige a expectativa de poder ao valor realista pós-canais e move o peso da
aposta do "quantos nomes" para o "quão grande é o efeito". Re-análise determinística; execução em
`scripts/power_analysis.py` (N_SIM=4000, seed fixa).

---

### D-046 — Desenho da expansão de universo: canais de cultura sob H′ (algodão, cana)
**Data**: 2026-07-20

Pré-registro do **desenho** da expansão que D-045 justifica (comprar conclusividade). A obra
(contratos de choque congelados por cultura, no molde de D-023) vem depois; aqui travamos os
**princípios e as direções**, cada uma **derivada do mecanismo**, não do retorno — mesma
disciplina anti-p-hacking de D-044.

#### Princípio de direção (para nenhum canal ser "invertido olhando o dev")
Para cada cultura, define-se o **estresse climático adverso ao rendimento/qualidade daquela
cultura** e a direção do retorno do produtor é **derivada da agronomia + do achado Q>P**, e
**congelada antes de qualquer retorno**. A validação é só no holdout.

#### Canal 1 — Algodão (extensão limpa de H′; recomendado)
- Mecanismo: algodão é preço global (como soja) e sensível à seca. Estresse = déficit de chuva na
  janela crítica. Sob H′ (Q>P): seca → queda de volume do produtor, preço global não compensa →
  **produtor de algodão prejudicado** (mesma direção do produtor de grão).
- Nomes: **0 novos** — AGRO3 e SLCE3 já são grandes produtores de algodão (já no universo).
- Ganho: reforça o sinal do produtor com um **evento semi-independente** (seca do algodão no
  Cerrado/BA difere parcialmente da soja em timing/geografia). Barato: só um contrato de choque
  novo (UFs do algodão: MT/BA/GO/MS; janela fenológica própria).

#### Canal 2 — Cana (mecanismo INVERTIDO; opcional, sub-modelo à parte)
- Mecanismo **diferente**: para cana, **inverno seco é BOM** (mais sacarose/ATR) e o preço é de
  energia (açúcar/etanol, CONSECANA), não grão. Logo o "estresse" da cana é o adverso próprio
  (excesso de chuva / seca extrema), e a direção do produtor **não** é a mesma do grão.
- Direção derivada: evento **favorável à cana** (inverno seco) → maior ATR/receita → **produtor
  de cana beneficiado**. Sinal próprio, congelado.
- Nomes: **+2** (SMTO3, JALL3; RAIZ4 é diversificada/energia, fica de robustez).
- Tratamento: canal **separado**, testado standalone **e** combinado — **não** jogado na mesma
  regressão de H′ (misturar mecanismos sujaria o teste primário). Custo: um contrato de choque de
  cana (fenologia, sinal invertido/não-linear, regiões SP/Centro-Sul) — obra maior que o algodão.

#### Não entram (com motivo)
- **Café**: o **melhor sinal climático** do Brasil (geada/seca), mas **sem produtor listado** —
  limitação declarada, boa para o relatório ("mecanismo forte sem veículo de equity").
- **Proteína bovina** (MRFG3, BEEF3): canal de grão fraco (boi é pasto); só entra se for preciso
  empurrar para ~8 nomes, e explicitamente rotulada como fraca.
- **Trigo/arroz/celulose**: fora do mecanismo (importado / ambíguo / árvore).

#### O que a expansão realmente entrega (honesto)
Núcleo H′ limpo (grão+algodão): AGRO3, SLCE3 (produtores) + BRFS3, JBSS3 (processadores) = **4
nomes, +1 evento (algodão)**. Com cana: **6 nomes, +1 canal independente**. Com proteína: ~8,
mais sujo. Por D-045, isso põe o poder na faixa "**conclusivo se o efeito for ≥ moderado**" — não
vira um universo de dezenas de ações. É o teto do listado brasileiro, e a gente o assume.

> **Resultado posterior:** D-049 rejeitou o canal do algodão; portanto ele não fornece o
> evento adicional projetado neste desenho. O texto acima é preservado como expectativa
> anterior ao teste, não como descrição do estado atual.

**Congelado agora**: os princípios e as direções (algodão = produtor prejudicado por seca; cana =
produtor beneficiado por inverno seco, à parte). **Depois, antes do holdout**: os contratos de
choque por cultura (D-023-like) e a especificação final da estratégia (D-044 §5).

---

### D-047 — Contrato congelado do canal do algodão (Fase 3.4)
**Data**: 2026-07-20

Materializa o algodão de D-046 num contrato de choque congelado, no molde de D-023, **antes de
computar qualquer choque ou retorno**. Em `features/shock_spec.py::COTTON_WINDOWS` (à parte do
`PRIMARY_WINDOWS` de grãos) e travado por `tests/test_shock_spec.py::test_contrato_algodao_congelado`.

- **UFs (suporte mínimo >80%)**: **MT + BA** (MT ~68%, BA ~17% da produção CONAB 2023/24; as
  demais somam <15%). Ambas já no painel CHIRPS municipal (são UFs de soja) — regionalização
  reaproveitada.
- **Fase crítica hídrica = floração + formação do capulho** (`flowering_boll`): 50–60% da
  necessidade hídrica e ~80% das estruturas produtivas emitidas 60–100 dias após a emergência.
  Fonte: ZARC/MAPA (portarias de algodão herbáceo MT/BA) e fisiologia Embrapa.
- **Janelas** (ano base+1): **MT 15/03–31/05** (plantio jan–fev após a soja ⇒ floração/capulho
  mar–mai); **BA 01/02–30/04** (plantio dez–jan ⇒ fev–abr).
- **Canal climático e sinal**: idênticos ao grão — déficit CHIRPS, `Shock = −z(chuva acumulada)`
  na janela. Mesmo mecanismo, mesma convenção (seca = estresse); sob H′, seca prejudica o
  produtor de algodão como o de grão.
- **CONAB**: produto `ALGODAO EM PLUMA`, safra `UNICA` (rótulo de MT e BA no painel), disponível
  de 2017/18 em diante.

**Próximo (3.4, parte 2)**: buscar a PAM municipal do algodão (SIDRA, produto próprio) para o
peso intra-UF e **validar** o canal — o choque do algodão prevê a **revisão CONAB da pluma**?
(H1 por cultura, sem tocar retorno de ação). Só depois o algodão entra no score.

**Custo/limitação.** A CONAB da pluma começa em 2017/18 (~4 safras com ≥2 levantamentos por UF)
⇒ a validação será de **baixo poder/direcional** (como H1b), não um veto forte. Reforça, não
sozinha decide. MT concentra ~68% ⇒ o canal é quase MT+BA; a diversificação de evento vem do
timing/geografia parcialmente distintos da soja, não de muitas UFs.

---

### D-048 — Pré-registro da validação H1 do algodão: três safras e critério direcional
**Data**: 2026-07-20

Antes de calcular o primeiro `Shock` de algodão, fica congelado o teste que decide se o canal
D-047 pode entrar na estratégia reformulada H′. Ele testa somente o mecanismo físico
clima→revisão de safra; não consulta retorno de ação.

**Correção de cobertura descoberta antes do teste.** O painel CONAB traz `ALGODAO EM PLUMA`
desde 2017/18, mas 2017/18 possui apenas o 12º levantamento e 2018/19–2021/22 usam o código
legado 99, sem data recuperável. As únicas safras encerradas com vintages 1–12 datáveis são
**2022/23, 2023/24 e 2024/25**. A safra 2025/26 está em andamento e não entra. Logo o N efetivo
é três anos-safra, não quatro ou nove; a estimativa anterior em D-047 fica corrigida por esta
decisão posterior.

**Desenho congelado:**

1. peso intra-UF: PAM/SIDRA 1612, variável 214, produto 2689 (`Algodão herbáceo (em caroço)`),
   última edição disponível em cada data; o produto em caroço localiza a lavoura, enquanto o
   desfecho CONAB é produção de pluma;
2. UFs e janelas: MT e BA, exatamente `COTTON_WINDOWS` de D-047;
3. desfecho: revisão log acumulada de `ALGODAO EM PLUMA/UNICA` desde o 1º levantamento;
4. regressor: `Shock` da UF observável na data de cada levantamento, com CHIRPS prelim e
   climatologia expanding desde 2000; levantamentos anteriores ao início da janela não são
   imputados;
5. estimativa primária: painel MT+BA, `logrev ~ Shock`, erros agrupados por ano-safra;
6. diagnósticos: MT e BA separados, coeficientes por safra e três estimativas
   *leave-one-safra-out*; bootstrap por cluster e p-valores são reportados, mas não decidem
   aprovação com apenas três clusters.

**Critério direcional pré-registrado.** O canal é corroborado se `(a)` o β agrupado for
negativo — estresse antecipa revisão para baixo — e `(b)` pelo menos duas das três estimativas
*leave-one-safra-out* também forem negativas. Caso contrário, o algodão não entra no score.
Significância não é exigida nem alegada. Se o sinal for correto, mas a estabilidade falhar, o
resultado é inconclusivo e o canal também fica fora do primário.

**Custo/limitação.** Levantamentos mensais dentro da mesma safra não são eventos independentes;
o teste mede direção com três clusters e não compra o poder prometido para retorno pela D-045.
Seu papel é controle de qualidade do ingrediente climático. A contribuição de poder do algodão
ao holdout só existe se este teste direcional passar.

---

### D-049 — Resultado H1 do algodão: critério não corroborado; canal excluído
**Data**: 2026-07-20

O teste D-048 foi executado uma vez, sem retorno de ação. O painel contém 42 observações em
MT e BA e apenas **três anos-safra independentes** (2022/23–2024/25). O resultado agrupado foi
`β=+0,0421` (erro-padrão agrupado `0,0089`; `t=+4,76`, apenas diagnóstico). O sinal é o
**oposto** do mecanismo pré-registrado, segundo o qual estresse deveria antecipar revisão para
baixo da produção de pluma.

A estabilidade também veio no sentido contrário:

- BA: `β=+0,0299`; MT: `β=+0,1431`;
- por safra: `+0,0185`, `+0,0820` e `+0,0458`;
- *leave-one-safra-out*: `+0,0502`, `+0,0466` e `+0,0376` — portanto **0/3 negativas**.

O critério D-048 falhou nos dois componentes. **O algodão não entra no score H′, não recebe
peso próprio e não conta como evento adicional na análise de poder D-045.** A expansão segue
para o canal independente da cana; o holdout de ações permanece intocado.

Um diagnóstico posterior, rotulado como explicativo e incapaz de resgatar o teste, decompôs a
produção em área e produtividade. O coeficiente da área plantada foi positivo (`+0,0375`),
enquanto o de produtividade foi próximo de zero (`−0,0018`). Assim, a revisão positiva da
produção parece refletir revisão de área, não evidência de que déficit hídrico eleve rendimento.
Trocar o desfecho primário para produtividade depois de observar esse resultado seria uma
mudança *post-hoc* e não foi feita.

**Custo/limitação.** Três clusters não permitem uma alegação forte de significância, e os
diagnósticos não são evidências independentes entre si. A formulação precisa é: o ingrediente
**não foi corroborado pelo critério pré-registrado**, com sinal positivo em todos os
diagnósticos desta amostra. Isso não é prova geral sobre a fisiologia do algodão. A sensibilidade
com pesos municipais uniformes pode quantificar R15, mas, por ser secundária, não pode reverter
o veto do teste primário nem promover o canal.

O registro imutável `data/reference/cotton_h1_result_v1.json` preserva commit de pré-registro,
parâmetros, hashes das entradas e hashes dos artefatos da primeira execução. O diagnóstico
área/produtividade foi incorporado ao rodador depois do veredito, com rótulo pós-hoc explícito.

---

### D-050 — Contrato e validação H1 da cana: maturação/ATR é o portão
**Data**: 2026-07-20

Antes de calcular qualquer choque de cana, separam-se os dois mecanismos que um índice anual
misturaria com sinais opostos:

1. **maturação (primário)**: déficit de chuva em **junho–agosto** reduz crescimento vegetativo e
   pode favorecer concentração de sacarose. O regressor é `dryness = −z(precipitação)` e o
   desfecho é a revisão log de `producao_atr_kg_t` desde o 1º levantamento. Sinal esperado:
   **β > 0**;
2. **crescimento (diagnóstico pré-declarado)**: déficit de chuva em **dezembro–fevereiro** que
   precede a safra reduz biomassa/tonelagem. O mesmo `dryness` é comparado à revisão log de
   `producao_mil_t`. Sinal esperado: **β < 0**. Este resultado não pode promover nem resgatar o
   canal se o teste primário de ATR falhar.

**Suporte espacial congelado.** SP, MG, GO, MS e PR — o menor conjunto acima de 85% da produção
CONAB 2024/25 (87,8%; SP sozinho = 51,5%). Dentro da UF, PAM/SIDRA 1612, variável 214, produto
2696 (`Cana-de-açúcar`), com a última edição disponível em cada data. Não omitir SP para
reaproveitar um painel pronto: isso eliminaria metade do fenômeno.

**Amostra congelada.** Safras **2018/19–2025/26**, oito anos com quatro levantamentos datáveis.
2017/18 é excluída porque só contém 1º, 2º e o resíduo legado 99; 2026/27 está incompleta. Cada
levantamento posterior ao primeiro gera uma revisão; a inferência é agrupada por ano-safra.
P-valores e bootstrap são diagnósticos com oito clusters, não regra de aprovação.

**Clima e vintage.** CHIRPS mensal arquivado, preservando `prelim` para o trecho corrente e
`final` somente na climatologia expanding desde 2000, com os mesmos lags conservadores de 7 e
60 dias. Os arquivos mensais são somas oficiais dos dias e as janelas usam meses civis
completos; a troca de frequência reduz a captura de milhares para centenas de rasters sem
alterar a quantidade física acumulada. Em cada data entram somente meses cujo
`avail_date ≤ t`; a climatologia compara o mesmo número de meses da fase em safras anteriores.

**Critério direcional pré-registrado.** O canal de cana é corroborado somente se os três itens
forem verdadeiros no teste de maturação/ATR: `(a)` β agrupado **positivo**; `(b)` pelo menos
**6/8** estimativas *leave-one-safra-out* positivas; e `(c)` pelo menos **3/5** coeficientes por
UF positivos. Significância não é exigida nem alegada. Falha em qualquer item exclui cana do
score e impede a entrada de SMTO3/JALL3 por este mecanismo. O teste de crescimento é publicado
em qualquer resultado, mas nunca substitui o portão.

**Racional agronômico anterior ao resultado.** A Embrapa descreve água e calor favorecendo o
crescimento vegetativo, enquanto menor disponibilidade hídrica e temperaturas mais amenas
favorecem maturação e acúmulo de sacarose. A CONAB documenta que chuva excessiva/baixa
luminosidade pode ampliar crescimento e atrasar maturação, enquanto baixa chuva/alta
temperatura no desenvolvimento reduz produtividade. Fontes e períodos estão registrados em
`09_FENOLOGIA_E_LIMIARES.md`.

**Custo/limitação.** ATR é qualidade por tonelada, não receita total: ATR maior pode coexistir
com tonelagem menor. O portão valida somente o ingrediente físico favorável da maturação; não
prova retorno da ação nem benefício líquido da usina. A janela fixa Centro-Sul simplifica
diferenças locais de plantio/corte, e os vintages mensais continuam sujeitos às limitações
documentadas do produto CHIRPS.

---

### D-051 — Resultado H1 da cana: canal físico corroborado, evidência fraca
**Data**: 2026-07-20

O portão D-050 foi executado uma vez, sem carregar retorno de ação. A captura contém 198 meses
CHIRPS (150 `final`, 48 `prelim`), 439.956 agregações município×mês nas cinco UFs, zero valor
de precipitação ausente e pesos PAM 2014–2024 para cana. O painel de regressão tem 120 linhas
em oito anos-safra (2018/19–2025/26).

**Teste primário — maturação/ATR.** O β agrupado foi **+0,0134**, com erro-padrão por safra
`0,0086`, `t=1,55`, p bilateral `0,121` e p do bootstrap por cluster `0,273`. A estabilidade
direcional, que era a regra de aprovação congelada, passou integralmente:

- **8/8** estimativas *leave-one-safra-out* positivas (`+0,0055` a `+0,0187`);
- **5/5** UFs positivas (GO `+0,0029`, MG `+0,0207`, MS `+0,0066`, PR `+0,0185`,
  SP `+0,0272`).

Logo, o mecanismo **inverno seco → revisão positiva de ATR** é **corroborado pelo critério
direcional pré-registrado**. A formulação não é “comprovado”: os p-valores não rejeitam zero e
o efeito é pequeno. A estabilidade entre UFs e exclusões anuais é evidência de sinal coerente,
não substituto de poder estatístico.

**Diagnóstico pré-declarado — crescimento/produção.** O β foi `−0,0061`, no sinal esperado,
mas fraco (`t=−0,59`, p `0,556`, bootstrap p `0,615`) e com instabilidade anual. Como D-050
determinava, este diagnóstico não participou do veredito e não melhora a qualificação do
primário.

**Consequência.** A cana pode prosseguir como **submodelo independente** para a próxima etapa,
mas ainda não autoriza posição em SMTO3/JALL3. Antes de qualquer retorno é preciso auditar,
point-in-time, se a exposição econômica dessas empresas traduz ATR favorável em receita/margem
líquida (tonelagem, mix açúcar/etanol, cana própria/terceiros, hedge e geografia) e então
congelar direção, sizing e regra de combinação. R24 impede transformar o passe físico em
alegação financeira automática.

O registro imutável `data/reference/cane_h1_result_v1.json` preserva os commits anteriores ao
resultado, hashes das entradas/saídas e a leitura limitada. O manifesto consolidado
`data/manifests/chirps_cane_monthly_bulk.parquet` preserva URL e hash dos 198 rasters.

**Custo/limitação.** Há apenas oito clusters; as três observações por UF×safra são revisões
acumuladas, não eventos independentes. ATR mede kg de açúcar recuperável por tonelada, e não
receita total. O passo seguinte pode matar o canal mesmo com D-051 positivo — isso é uma
barreira metodológica, não uma formalidade.

---

### D-052 — Auditoria PIT dos veículos de cana: SMTO3 entra, JALL3 fica fora do score
**Data**: 2026-07-20

Auditoria conduzida sem tocar retorno de ação, respondendo ao R24: o ATR favorável de D-051
se traduz em exposição econômica assinável? Registro estruturado por nome, fonte e lacuna
declarada em `data/reference/cane_corporate_audit_v1.json`. Direção do submodelo: produtor de
cana com ATR favorável = **+1** (D-051).

**Achados que decidem (ambos os nomes têm geografia dentro do choque SP/MG/GO/MS/PR e cana
majoritária/totalmente própria):**

| | **SMTO3 — São Martinho** | **JALL3 — Jalles Machado** |
|---|---|---|
| Geografia usinas | 3 SP + Boa Vista/GO (dentro) | 2 GO + 1 MG/2022 (dentro) |
| Cana própria | ~70% (30% terceiros/CONSECANA) | 100% (exposição mais limpa) |
| Mix | ~47% açúcar; Boa Vista/GO só etanol | ~50–60% açúcar, >⅓ orgânico premium |
| Hedge | ~96% do preço 1 safra à frente | preço até 2 anos à frente |
| **Histórico PIT** | **IPO 2007 → dev + holdout** | **IPO 08/02/2021 → só holdout, zero dev** |

**Racional econômico central.** O canal da cana é de **quantidade** (ATR = açúcar recuperável
por tonelada), não de preço: mais ATR = mais açúcar **e** etanol da mesma cana. Por isso ele
**sobrevive ao hedge de preço** (que travou ~96% na SMTO3) — diferentemente do canal de preço
de grãos que falhou em D-037/D-041. Esse é o motivo de manter cana como submodelo. Ressalva
dura: ATR ≠ receita total, e o canal de tonelagem (crescimento) veio fraco/negativo em D-051 —
o sinal físico líquido de receita **não está provado** (R24).

**Decisão (opção 1, decidida pelo time).**
1. **SMTO3 entra no universo scoreado, com haircut declarado** (30% terceiros → offset
   CONSECANA; hedge intenso de preço; Boa Vista/GO só etanol). É o único veículo **testável no
   dev e negociável no holdout**. Direção +1 sob o submodelo; peso definido no congelamento do
   score (Fase 3.5).
2. **JALL3 fica fora do score.** Economicamente é a exposição mais limpa, mas o **IPO de
   fev/2021** a deixa sem dev, só no holdout lacrado. Incluí-la seria pôr no teste de tiro único
   um nome que **nunca poderíamos ter validado** — exatamente o risco de descoberta falsa que o
   projeto blinda. O mecanismo clima→ATR já está validado por D-051 no CONAB, **independe do
   IPO**; excluir a JALL3 não enfraquece o canal.
3. **Universo scoreado passa a 5 nomes** (4 grãos + SMTO3). O ganho de poder de 5→6 nomes é
   marginal (~+4–8pp, re-análise D-045) e não justifica o risco metodológico.

**Custo/limitação declarado.** Tier de evidência **inferior ao de D-035**: as fontes primárias
CVM (formulário de referência) não foram baixadas diretamente — WebFetch retornou 403 em
XP/NovaCana e a SEC não cobre nomes só da B3. Os números finos (% cana própria por safra, mix
por vintage, % de hedge) vêm de síntese de imprensa setorial/RI e ficam como **lacuna
declarada**. A decisão, porém, **não depende deles**: apoia-se na data de IPO (fato público
robusto) e na geografia/cana-própria (corroboradas em múltiplas fontes). O timing do
surpreendimento de ATR vs. o momento do hedge não é PIT-separável — lacuna de identificação.

---

### D-053 — Congelamento da estratégia reformulada (Fase 3.5), anterior ao holdout
**Data**: 2026-07-20

Especificação executável e imutável da estratégia sob H′ (D-044), **num commit anterior ao
primeiro contato com o holdout**. Contrato em `src/quantagro/backtest/strategy_spec.py`
(return-agnóstico; travado em `tests/test_strategy_spec.py`). O objetivo é que a rodada única do
holdout 2020/21–2024/25 não tenha **nenhum grau de liberdade ajustável**.

**Prioridades declaradas pelo time**: (1) força estatística, (2) resultado (lucro), sob a trava
de rigor. O desenho foi escolhido sob a verdade dura de que a força é **limitada pelos 5
anos-safra** do holdout (re-análise D-045) e nenhuma escolha aqui levanta esse teto — só evita
desperdiçá-lo.

**Camadas de sinal (não confundir).** `signal/convention.py::raw_signal=E·Shock` é o mecanismo
(canal de preço, produtor sobe sob estresse), **falsificado em D-043** e **intacto** (segue
travado em `test_signal_sign.py`). A estratégia H′ é uma camada operacional por cima: para
grãos, toma o **negativo** de `E·Shock` (a seca prejudica o produtor, `Q>P`); para a cana
(SMTO3), um canal próprio de maturação com direção +1 (seca→ATR↑→long). `test_strategy_spec.py`
trava a garantia cruzada de que H′ não altera a convenção de mecanismo.

**Forks resolvidos com o time:**
- **A1 — cana satélite**: o **teste estatístico primário usa só os 4 grãos** (spread
  produtor–processador), para o mecanismo fraco da cana (p=0,12) não diluir o sinal forte e
  baixar o t-stat — é a escolha que **protege a força** (prioridade 1). A **carteira negociável**
  inclui a SMTO3 mas com `|peso| ≤ 0,15` (D-052 põe a SMTO3 "no score"); a contribuição dela é
  reportada à parte.
- **B1 — sizing proporcional ao sinal, dollar-neutral (Σw=0, Σ|w|=1), cap 0,40 por grão**. Água
  por lado (long e short recebem o mesmo bruto ⇒ neutralidade e caps por construção). O sizing
  **não afeta o teste primário** (regressão não-ponderada); é uma escolha de P&L/Sharpe
  (prioridade 2), onde o mais simples e robusto vence sob a trava de rigor.
- **Pesos do choque nacional = contrato CONAB da safra anterior (D-028)**, não o equal-weight que
  foi simplificação de diagnóstico no dev.
- **Teste primário (substitui H3/Fama–MacBeth)**: painel/spread `Shock×exposição` demeanado na
  seção transversal, cluster por ano-safra, **inferência por permutação** (melhor com 5 clusters)
  e **unilateral** α=0,10 (direção dada por H′). Fecha o item de docs/14 §6.
- **Execução D+1; horizonte forward de 21 pregões.**

**R19 resolvido.** A concentração que definia o R19 era artefato da estrutura antiga (long
produtor forçava 50% do bruto num nome antes de 03/2018). Sob H′ não há long-produtor forçado
(carteira balanceada nos dois sentidos) e o **holdout começa em 2020/21 com os 5 nomes vivos** —
a concentração de "um nome só" não ocorre no período de teste. O cap de 0,40 declara o teto e no
holdout raramente ativa. R19 passa a **resolvido**.

**Custo/limitação declarado.** (a) A força continua limitada pelos 5 anos-safra — este
congelamento não a aumenta, só a preserva; o holdout pode voltar inconclusivo e isso será
reportado. (b) A cana é satélite de mecanismo fraco: pode não somar nada ao P&L. (c) Dollar-
neutral **não é market-neutral**: exposições residuais a fatores/beta/commodity não são
neutralizadas — declaradas, não presumidas. (d) O dev está queimado para a direção; o desempenho
de H′ no dev **não** vale como evidência (Fase 4 é return-agnóstica). O holdout roda **uma vez**.

---

### D-054 — Auditoria de transição e gate operacional da Fase 4.0
**Data**: 2026-07-20

D-053 congelou corretamente a **estratégia econômica** — universo, direção H′, sizing, caps,
execução D+1, horizonte e teste primário —, mas a auditoria anterior à máquina encontrou graus
de liberdade operacionais que ainda poderiam alterar materialmente o resultado:

1. calendário das decisões, encerramento e sobreposição de posições;
2. combinação soja+milho e escala da cana, ausências e conjunto usado no demean;
3. comportamento quando elegibilidade/liquidez elimina um dos lados econômicos;
4. estatística e unidade exatas da permutação, semente/enumerabilidade e fórmula do p-valor;
5. piso de ADTV, patrimônio de referência, taxas, slippage, aluguel e capacidade;
6. datas diárias exatas de dev/holdout e eventos que atravessam a fronteira.

**Decisão.** A Fase 4 começa por uma subfase **4.0 return-agnóstica** que fecha e torna
executáveis esses itens sem consultar P&L. O motor não será implementado sobre placeholders e
deve negar o holdout por padrão; a liberação deliberada pertence somente à Fase 6. As escolhas
de Fase 4.0 serão registradas em decisão própria antes do primeiro resultado de carteira.

**Defeito de implementação encontrado.** O water-filling de `strategy_spec.py` recalculava o
conjunto livre a cada iteração e podia recolocar um nome já capado, violando o teto em mapas de
caps admissíveis pela API. O algoritmo passou a manter caps ativos permanentemente, usar
`GROSS/2` em vez de `0.5` literal e rejeitar score/cap inválido; um caso de regressão trava o
erro. Também foram adicionados tripwires para lag, horizonte, bruto e inferência já declarados
em D-053. Isso corrige a implementação do contrato, sem alterar nenhuma decisão econômica.

**Custo/limitação.** A expressão “estratégia congelada” em D-053 precisava ser qualificada:
ela não autorizava calcular o backtest nem garantia que cada detalhe operacional estivesse
fechado. A Fase 4 ganha um gate adicional e pode levar mais tempo, mas elimina escolhas pós-P&L
e torna a rodada do holdout auditável.

---

### D-055 — Contrato operacional completo da Fase 4.0, anterior ao P&L
**Data**: 2026-07-20

Os sete graus de liberdade de D-054 foram fechados sem carregar retorno nem calcular P&L. O
contrato executável está em `src/quantagro/backtest/operational_spec.py` e seus invariantes em
`tests/test_operational_spec.py`.

**Calendário.** Cada safra usa blocos contíguos e não sobrepostos de 21 pregões. A primeira
decisão é o primeiro pregão em ou após 7/jan do segundo ano da safra; executa-se no close do
pregão seguinte. O close de saída após 21 intervalos é também o close de entrada do bloco
seguinte. O primeiro ponto da grade em ou após 7/set é a última decisão; ao fim desse bloco, a
carteira fica zerada. Informação entre decisão e execução não altera a ordem.

**Score.** Grãos usam `−(E_soja·Shock_soja + E_milho·Shock_milho)`. Janela ainda não iniciada
contribui zero sem renormalizar `E`; dado ausente/indefinido falha alto. A cana agrega GO, MG,
MS, PR e SP com pesos CONAB anteriores, em escala z 1:1. O cap de 15% é seu único *haircut*;
SMTO3 fica fora do *demean* antes do primeiro prefixo de maturação. Teste primário usa somente
grãos; carteira acrescenta SMTO3 quando ativa.

**Universo incompleto.** Exigem-se ao menos um produtor e um processador de grãos válidos e
elegíveis. Sem qualquer lado, o bloco inteiro é zerado; SMTO3 não substitui o núcleo. Ausência
de close de execução/saída sem evento terminal auditado bloqueia o bloco, em vez de trocar o
preço ou descartar o nome.

**Inferência.** Em cada ano-safra calcula-se a inclinação do painel transversal demeanado nos
quatro grãos; a estatística é a média com peso igual dos cinco anos do holdout. O teste
unilateral enumera os `2⁵=32` *sign flips* dos clusters inteiros. Não há semente nem aproximação;
`p=#(T_perm≥T_obs)/32`. H′ passa se `T_obs>0` e `p≤0,10`. As cinco safras e todos os blocos
pré-declarados são obrigatórios.

**Investibilidade.** Patrimônio de referência = R$500 mil; ADTV21 encerrado em D ≥R$8 milhões;
ordem ≤5% do ADTV. Custo-base à vista, em bps do notional, é
`3,5 B3 + 2 corretagem + 5 execução + 10·sqrt(participação/1%)`. O short exige negócio B3 nos
cinco pregões anteriores, posição ≤1% do estoque alugado e taxa
`max(taxa PIT,5%)+tarifa B3+1%` a.a. Sem evidência para qualquer short, o bloco não abre.
Cenários zero/base/2× mantêm a mesma investibilidade; zero remove só custo monetário. Não há
cap de turnover. Capacidade é o mínimo entre limites do à vista e do aluguel.

**Partição e segurança.** Dev = safras 2015/16–2018/19 com saída até 31/12/2019. A safra
2019/20 é excluída integralmente. Holdout = somente 2020/21–2024/25, com saída até 31/12/2025,
e permanece negado por padrão até a Fase 6. Bloco de fronteira não é truncado.

**Por quê.** Blocos de 21 pregões preservam literalmente o horizonte congelado sem cohorts
sobrepostos; peso igual por safra respeita o N efetivo; o piso de ADTV fecha algebricamente a
pior reversão de peso permitida (`0,80×R$500 mil/R$8 mi=5%`); a política de aluguel impede que
um cenário monetário transforme short inexistente em operação possível.

**Custo/limitação.** A escolha abre mão da atualização diária e pode ficar zerada quando um
lado ou aluguel falha. Tarifas históricas, corretagem, spread e profundidade não são
reconstruídos perfeitamente; a regra usa hipóteses uniformes conservadoras. Estoque negociado
é proxy, não garantia de doador. A safra 2019/20 é perdida para preservar simultaneamente o
lacre civil e os cinco clusters pré-registrados. R25 fica resolvido; R8/R9 passam a riscos
mensuráveis, não eliminados.

---

### D-056 — Contabilidade diária do motor e cobertura efetiva do desenvolvimento
**Data**: 2026-07-20

Antes de consultar qualquer P&L observado, a implementação da Fase 4.1 encontrou que “posição
por 21 pregões” ainda admitia duas contabilidades diferentes: manter quantidades ou reaplicar o
peso-alvo todos os dias. A segunda opção criaria rebalanceamento diário, turnover e custos não
declarados. A auditoria também mostrou que o peso nacional CONAB da safra anterior não existe
para as três primeiras safras do desenvolvimento operacional.

**Posições e sequência diária.** O motor mantém quantidades de um **índice de retorno total**
fixas dentro de cada bloco. Uma ordem executada no close de `X` recebe os retornos em
`(X, saída]`. No close compartilhado entre blocos, aplica-se primeiro o último retorno e o
aluguel da posição antiga, marca-se seu drift e depois se faz uma única ordem líquida contra o
novo alvo. A nova posição começa a receber retorno apenas no intervalo seguinte. A saída final
negocia contra zero. Dividendos e splits já estão no retorno total; não há segunda cobrança.

**Patrimônio e custos.** A simulação começa com R$500 mil e é autofinanciada: ordens usam o
patrimônio corrente, não um reset de R$500 mil a cada bloco. Como o alvo é peso sobre o
patrimônio **pós-custo**, o motor resolve por bisseção a identidade
`A⁺ = A⁻ − Σ|ordem_i(A⁺)|·c_i`, instalando os pesos exatamente depois do custo. Participação e
custo usam a ordem efetiva contra a posição marcada, nunca apenas a diferença entre dois alvos.
Entrada, transição e liquidação são cobradas. No cenário zero o custo monetário some, mas os
gates de participação e aluguel permanecem.

O ADTV de entrada/transição é o disponível em `D`; na liquidação final programada, usa-se o
ADTV encerrado no pregão imediatamente anterior à saída. A taxa de aluguel observada em `D`
fica fixa pelos 21 intervalos e acumula linearmente em `taxa all-in/252` por pregão, incidindo
sobre o short marcado no início de cada intervalo. O intervalo que termina numa transição paga
o short antigo; o novo começa depois do close. Indisponibilidade de qualquer short zera somente
aquele bloco inteiro, sem redistribuição.

**Turnover e reconciliação.** O livro reporta simultaneamente notional bruto negociado
`Σ|ordem|/A⁻` e turnover one-way convencional, metade desse valor. Custos de transição ficam em
rubrica própria no dia da ordem, sem serem atribuídos oportunisticamente ao bloco que entra ou
sai. A soma diária da atribuição por nome fecha com P&L bruto, e
`ΔA = P&L bruto − aluguel − custo spot` é um invariante testado.

**Cobertura do dev.** O contrato nacional usa a safra CONAB anterior encerrada. Como os painéis
de vintages começam em 2017/18, 2015/16–2017/18 não possuem pesos anteriores admissíveis;
2018/19 é a única safra real de desenvolvimento materializável sem alterar D-053/D-055. A
Fase 4.1 não substitui isso por equal-weight, PAM, primeiro peso futuro nem reconstrução atual.
Testes sintéticos cobrem toda a álgebra; o smoke test observado fica restrito a 2018/19 quando
os dados de investibilidade da Fase 4.2 estiverem prontos.

**Custo/limitação.** A contabilidade autofinanciada torna custos levemente dependentes do
caminho do patrimônio e o uso de um índice de retorno total equivale a reinvestimento sintético
dos proventos. A convenção linear de aluguel ignora dias corridos. A validação real do dev tem
apenas uma safra e serve exclusivamente para detectar defeitos mecânicos, nunca para validar H′
ou escolher parâmetros. Nenhum retorno observado foi consultado ao tomar esta decisão.

---

### D-057 — Materialização das fricções e bloqueio histórico do aluguel
**Data**: 2026-07-20

A Fase 4.2 materializou tudo que pode ser reconstruído sem alterar D-055. Os eventos
corporativos dos cinco nomes até 2019 foram congelados num snapshot versionado por fonte; o
build de retorno total passou a ser offline e ganhou SMTO3. O split 3:1 de 12/2016 foi
confirmado no evento B3 e no COTAHIST. O único retorno absoluto ≥30% restante, JBSS3 em
22/05/2017, foi auditado como movimento real ligado aos fatos de maio/2017 e registrado com
fonte CVM — não foi “ajustado”.

O estado COTAHIST 2014–2019 confirmou um calendário de 1.482 pregões; quatro papéis negociaram
em todos eles e JBSS3 em 1.451. Aplicando literalmente ADTV21 ≥R$8 milhões, **AGRO3 não passa
o piso em nenhum pregão do dev**; em todos
os nove pontos de decisão de 2018/19, SLCE3, BRFS3, JBSS3 e SMTO3 passam, preservando o núcleo
produtor/processador sem relaxar o piso. Isso é um resultado de investibilidade, não motivo para
recalibrar o parâmetro. Cobertura, parâmetros, hashes dos seis COTAHIST e os nove pontos ficam
em `data/reference/market_state_dev_summary_v1.json`.

**Aluguel implementado.** As exportações `BTBLoanBalance` e `BTBLendingOpenPosition` do BDI
referentes a 17/07/2026 foram baixadas e parseadas ao vivo em 20/07/2026, com manifestos. O
primeiro painel distingue taxa repetida de negócio real exigindo contratos e quantidade
positivos; o segundo reconcilia modalidades com a linha `Total`. Uma data só entra na cobertura
após atestar CSV e manifesto por tabela, data interna, bytes, SHA-256 e contagem. A decisão no
close D só usa arquivos disponíveis até D, taxa doadora ponderada do último negócio nos cinco
pregões anteriores e estoque Total de D−1 marcado pelo close D. Arquivo/manifesto faltante ou
divergente falha alto. O motor passou a verificar 1% do estoque contra o **patrimônio corrente
pré-ordem**; testes cobrem igualdade exata, drift entre blocos, falta de arquivo e falha de um
único short inclusive no cenário zero. O motor também zera a entrada se um alvo não negociou no
close de execução, falha se uma posição aberta não negociou no close de saída e rejeita retorno
total menor que −100%.

**Fato que bloqueia o experimento.** A fonte pública antiga da B3, iniciada em 14/11/2019,
preservava apenas dez dias. A centralização atual das duas tabelas foi anunciada em 25/09/2023,
com exclusividade a partir de 01/12/2023, e a interface limita o acesso recente. A busca oficial,
probes de PDFs e endpoints antigos não recuperaram taxa/negócio/estoque por ticker para 2018/19;
o NEFIN disponível também não fornece esse contrato. Assim, o smoke real de 2018/19 **não foi
rodado**. Ausência de arquivo não virou ausência de doador, taxa atual não foi retroagida e o
gate não foi removido.

**Fork que exige decisão do time antes de qualquer P&L:**

1. obter uma fonte histórica contratada que entregue negócios, taxas e estoque por ticker;
2. revisar formalmente D-055 para um backtest econômico com proxy declarada, aceitando que não
   demonstrará investibilidade histórica;
3. reformular a estratégia para não depender de short, reconhecendo que isso muda H′ e exige
   novo congelamento antes do holdout.

Até essa escolha, R27 bloqueia a conclusão da Fase 4.2 e também impede usar o holdout como
estratégia “investível”. A infraestrutura não é descartada: ela mede corretamente datas cobertas
e torna explícito o que antes seria uma suposição invisível.

### D-058 — Proxy conservadora declarada de aluguel (resolve o fork R27), anterior ao P&L

**Data:** 2026-07-20. **Decisão:** resolver o fork de D-057/R27 pela **opção 2** — custo de
aluguel do short via **proxy econômica declarada**, não medição histórica —, depois de confirmar
que a **opção 1 (fonte gratuita) é inviável** e que a calibração pretendida não tem dado de
origem.

**Por que a opção 1 caiu.** Sondagem ao vivo do endpoint de exportação da B3
(`arquivos.b3.com.br/bdi/table/export/csv`): datas de 2024, jan/2025, jul/2025 e jan–jun/2026
retornam “Nenhum resultado”; **somente o último pregão (2026-07-17)** traz dado completo. A
própria B3 documenta que o histórico livre no site é dos “últimos 21 dias”. Terceiros
(StatusInvest, investsite, ADVFN) mostram taxa atual/recente, não são vintage-safe/PIT e não
cobrem BRFS3/JBSS3 — os dois processadores, ausentes do snapshot (aparentemente fora da B3 até
2026). Não existe série histórica pública por ativo para 2018/19 nem para parte do holdout.

**O que a calibração virou.** Do único snapshot real, as taxas doadoras dos nomes observáveis são
AGRO3 0,08%, SLCE3 0,19% e SMTO3 4,65% ponderada — **todas abaixo do piso de 5% a.a. já congelado
em D-055**. Para BRFS3/JBSS3, sem observação, o piso é conservador pela classe de liquidez. Logo,
a premissa congelada **domina** o custo real observável, e a série faltante **não mudaria** o
custo assumido. A calibração, na prática, **corrobora** o piso em vez de alterar um número.
Evidência imutável em `data/reference/borrow_rate_calibration_v1.json`.

**A proxy (return-agnóstica).** `validate/borrow.py::build_proxy_borrow_state` produz, para datas
sem BDI real, um `BorrowState` que codifica: taxa 0 → `borrow_all_in_rate` aplica piso 5% + tarifa
B3 + 1% de intermediação (all-in base 6,7% a.a. ≈ 0,56%/bloco; cenário 2× ≈ 1,12%/bloco);
disponibilidade = **elegibilidade por ADTV**; profundidade de 1% do estoque **não modelada** ao
AUM de referência de R$500 mil (imaterial para nomes que passam o piso de R$8 mi), via sentinela
finito; completude declarada. **Todo bloco carrega reason `proxy`**, para que nenhum resultado
seja confundido com aluguel medido. O motor congelado não muda — apenas consome o estado.

**Custo/limitação declarados.** Isto **não** demonstra investibilidade histórica medida do lado
short: o custo é premissa, não observação. A honestidade está em (a) o piso ser superestimado
vs. o real observável, (b) o estresse 2× e (c) a cauda da SMTO3 (máx 25% numa modalidade) poder
furar até o 2× — por isso ela é satélite capado em 0,15. O relatório deve dizer isto sem rodeio.
A força estatística do teste primário **não é afetada** (o custo simétrico não entra na
permutação de sinal). Com D-058, o smoke de 2018/19 fica **destravado** (sujeito a R26); o holdout
segue lacrado até a Fase 6.

### D-059 — Smoke de engenharia do motor no dev 2018/19 (validação, não estratégia)

**Data:** 2026-07-20. **O que foi feito:** `scripts/run_smoke_dev.py` montou os inputs reais do
dev (retorno total dos cinco nomes, ADTV/traded/elegibilidade COTAHIST, scores de grãos via
CHIRPS/PAM/CONAB, proxy de aluguel D-058) e rodou o motor ponta a ponta nos três cenários de
custo. **Objetivo: validar engenharia, não avaliar a estratégia.**

**Resultado de engenharia (aprovado):** motor rodou os nove blocos sem erro em zero/base/double;
pesos dollar-neutral (máx |Σw|=0), caps respeitados, custos escalam zero<base<2× (aluguel
≈R$11,7 mil base / R$23,1 mil no 2×; spot ≈R$1,9 mil/R$3,8 mil), patrimônio final finito e
positivo, identidade diária de P&L fechando, e `require_backtest_scope` mantendo o holdout
bloqueado. A proxy de aluguel foi consumida sem incidente (todos os blocos `planned`).

**Achado 1 — SMTO3 é holdout-only na prática.** No dev 2018/19 o satélite de cana **não é
scoreável**: o bloco exige o peso CONAB de cana do ano anterior (2017/18), mas a série de
vintages datáveis da cana só começa em 2018/19 (D-050). Logo, a carteira do dev é **só de
grãos** — SLCE3 (produtor) short contra BRFS3+JBSS3 (processadores) long, bruto 0,8 porque
AGRO3 é excluído por ADTV e o lado produtor tem um único nome no cap de 0,40. A cana só entra a
partir do holdout. Registrado para não sobre-vender o papel da cana na tese.

**Achado 2 (metodológico, o que mais importa) — o P&L do dev é circular.** O motor devolveu
retorno **positivo** no dev (base ≈ +36%), mas isso **não é evidência de que a estratégia
funciona**: a direção H′ foi *derivada* deste mesmo dev depois de D-043 falsificar a original. O
dev está queimado; o P&L é in-sample e descritivo. **Só o holdout lacrado (Fase 6) valida.** Tratar
o +36% como sucesso seria exatamente o teatro estatístico que o projeto recusa. Artefatos de
engenharia em `data/processed/smoke_dev_*` (gitignored); o runner é versionado.

---

### D-060 — Diagnósticos descritivos da Fase 4.3 no dev (setor-vs-clima)

**Data:** 2026-07-20. **O que foi feito:** `backtest/diagnostics.py` e
`scripts/run_diagnostics_dev.py` produziram, sobre o dev 2018/19 e sem abrir o holdout, três
blocos descritivos: (A) invariantes do motor; (B) atribuição do P&L por nome; (C) decomposição do
retorno em aposta de SETOR versus sinal cross-section de clima. **Objetivo: entender o que o motor
faz, não avaliar a estratégia.** O P&L do dev continua circular (direção H′ derivada do próprio
dev, D-059); nada aqui é validação.

**Bloco A — invariantes (ok):** alvo dollar-neutral (máx |Σw|=0), bruto-alvo máx 0,800 (o lado
produtor tem um único nome no cap 0,40 porque AGRO3 sai por ADTV), custo monótono
zero≥base≥double (697,0 ≥ 681,3 ≥ 665,9 mil).

**Bloco B — atribuição por nome (base):** o P&L bruto vem esmagadoramente da perna long de
proteína. JBSS3 **54,6%** (long, +R$106,4 mil), BRFS3 31,7% (long, +R$61,8 mil), SLCE3 13,7%
(short, +R$26,6 mil); AGRO3/SMTO3 fora. A perna long (JBS+BRF) = **86,3%** do bruto; HHI 0,42.
Custos: bruto 194,9 − aluguel 11,7 − spot 1,9 = líquido 181,3 mil (+36,26% sobre R$500 mil).

**Bloco C — decomposição setor-vs-clima (o que mais importa):** construiu-se uma **carteira
setorial ingênua** que só expressa short produtor / long processador com pesos iguais por perna,
ignorando o score de clima — reusando a máquina de pesos congelada com um `E·Shock` constante
(produtor +1, processador −1). Resultado: a carteira real (+36,26%) e a ingênua (+36,26%) são
**idênticas** — **incremento atribuível ao clima = +0,00%**. A regressão do retorno diário do
livro no spread proteína−produtor dá **R²=0,84**. Ou seja: no dev, com apenas três nomes ativos, o
livro **É uma aposta de setor**; o score cross-section de clima não diferencia nada. O +36% é o
rali de proteína de 2019 (peste suína africana) entrando pela perna long, não alpha climático.

**Por quê / consequência:** isto converte os gargalos conhecidos (concentração e exposição
setorial não neutralizada) de suspeita em fato medido. **Não muda o contrato congelado (D-053/
D-055)** — os diagnósticos são descritivos e a inferência mora só no holdout. Alimenta duas coisas:
(1) a Fase 5 deve incluir uma leitura de retorno **líquida de setor/beta**, separando quanto é
spread proteína×produtor de quanto é o sinal climático; (2) o relatório precisa **declarar a
exposição setorial** e jamais vender o P&L do dev como sinal de clima. Se o time decidir
neutralizar setor na própria estratégia, isso vira decisão pré-registrada ANTES do holdout,
separada de D-060.

**Custo/limitação:** o incremento de clima exatamente nulo é, em parte, artefato do dev ter só 3
nomes ativos (a atribuição de perna determina quase toda a estrutura); no holdout, com 5 nomes e
variação cross-section real, o score de clima tem mais espaço para diferenciar — mas isso é
justamente o que o holdout, e só ele, vai medir. Artefatos em `data/processed/diag_dev_*`
(gitignored); módulo e runner versionados.

> **Correção posterior (ver D-061):** a leitura de "artefato de 3 nomes" acima está **superada**. O
> D-061 provou que o incremento nulo era uma **identidade algébrica** (processadores com exposição
> idêntica ⇒ carteira degenerada em 2 estados), que valeria também no holdout — não um efeito de
> amostra pequena. A reconstrução de `E` sob H′ (D-061) quebrou a degeneração (1→8 estados). Este
> registro fica intacto como estava; a correção vive no D-061.

---

### D-061 — Reconstrução da matriz de exposição sob o critério H′ de quantidade (Fase 5), anterior ao holdout

**Data**: 2026-07-24

**Achado que motiva a decisão (return-agnóstico).** Investigando a carteira congelada com choques
**sintéticos** — sem consultar nenhum retorno —, verificou-se que a matriz `E` de D-033 dava aos
dois processadores (BRFS3 e JBSS3) vetores de exposição **idênticos** (direção −1, materialidade
0,50, cesta soja/milho 50/50). Com o único produtor líquido no dev (AGRO3 reprova ADTV) e dois
processadores indistinguíveis, a função de pesos (`dollar_neutral_weights`, demean + water-filling
+ caps + bruto fixo) tem **apenas dois estados de carteira alcançáveis**, e qual deles ocorre
depende só do **sinal** do choque nacional; a magnitude é integralmente descartada pela
normalização. Um dos dois estados é **bit-idêntico** à carteira setorial ingênua de D-060 — por
isso o `climate_increment` de D-060 deu **exatamente** `0,0` (dez casas), não "aproximadamente
zero". **Isto corrige a leitura de custo/limitação de D-060**: o incremento nulo não é artefato de
"só 3 nomes no dev", é uma **identidade algébrica** que valeria também no holdout enquanto os
processadores forem gêmeos. Uma estratégia cuja informação climática efetiva na seção transversal
é **um bit por bloco** não expressa a própria tese cross-section.

**Por que reabrir um input congelado é legítimo aqui.** (i) O achado é **return-agnóstico**:
derivado de choques sintéticos na função de pesos, não de P&L; o dev permanece queimado e o
holdout lacrado. (ii) A degeneração é **estrutural**, não um resultado ruim: consertar um mecanismo
que matematicamente não consegue expressar a hipótese ≠ ajustar desenho para melhorar um número.
(iii) A matriz `E` foi construída em D-032/D-033 para o **canal de preço**; H′ (D-044) trocou a
hipótese econômica para **quantidade dominante**, mas `E` **nunca foi re-derivada** para H′ — D-053
herdou a matriz de preço e apenas aplicou o sinal negativo. (iv) A auditoria D-035 **já havia
deixado explícito** que a atenuação de materialidade "entra como haircut candidato … no
congelamento do score"; D-053 congelou a estratégia (universo, direção, sizing, teste) mas
**não executou** essa re-derivação. D-061 executa a decisão que D-035 pré-sinalizou, sob o critério
correto de H′.

**O que foi decidido.** Re-derivar a materialidade de cada nome de grão sob o **critério H′ de
quantidade**: *share da economia da firma dirigido por volume físico de soja/milho DENTRO da
geografia do Shock*. Direção e pesos de cultura inalterados; apenas a materialidade é reavaliada
sob quantidade/geografia (não preço), a partir das **fontes primárias já documentadas** em
`data/reference/corporate_audit_v1.json` (auditoria D-035), sem baixar dado novo nem olhar retorno.
Resultado (`data/reference/exposure_hprime_v1.json`, artefato imutável novo; o v1 fica congelado
como registro do canal de preço):

| Nome | D-033 (preço) | H′ (quantidade) | Base primária (auditoria D-035) |
|---|---|---|---|
| SLCE3 | +1, 0,50 | **+1, 0,50** (mantém) | produtor direto; volume próprio dentro do Shock |
| AGRO3 | +1, **1,00** | **+1, 0,50** (↓) | grão 70,6%→51,7% e caindo; soja própria em PI+Paraguai, fora do Shock |
| BRFS3 | −1, 0,50 | **−1, 0,50** (mantém) | 28,5% do custo, grão brasileiro físico, dentro do Shock (mais limpo) |
| JBSS3 | −1, 0,50 | **−1, 0,25** (↓) | mais diluído: só Seara/BR no Shock; Pilgrim's (EUA) e Moy Park (EU) fora |

As duas mudanças são **descidas** em direção aos candidatos que a própria auditoria D-035 já havia
registrado, sob o critério de geografia/quantidade. Nenhum nome direto novo entrou; o universo de
D-052/D-053 (cinco nomes) permanece.

**O que isto conserta e o que NÃO conserta.** Verificado no pipeline real (loader validado, não
função sintética): a carteira passa de **1 para 8 estados** e o **incremento de clima deixa de ser
nulo** — o lado long agora inclina entre BRFS3 e JBSS3 conforme **qual cultura** (soja vs milho)
está mais estressada, um sinal cross-section climático genuíno que não existia. **NÃO** conserta:
(a) a magnitude total do choque continua descartada (comportamento correto de uma carteira
dollar-neutral — não se dimensiona por z-score sem evidência de que z maior ⇒ retorno maior);
(b) o lado produtor no dev continua sendo um único nome no cap (a cross-section de produtor exige
AGRO3 passar ADTV, o que só o holdout dirá); (c) o canal econômico do processador continua sendo o
custo de insumo, que passa pelo **preço** — e o preço foi empiricamente fraco (D-037/D-041); a
estratégia honesta segue sendo um **spread produtor–processador com uma inclinação climática**, não
uma cross-section climática pura.

**Custo/limitação declarado.** (a) É uma mudança num artefato herdado do congelamento D-053, feita
**depois** de observar a degeneração no dev; a defesa é que o achado é return-agnóstico e a mudança
é estrutural e pré-sinalizada por D-035 — mas é uma defesa que exige do avaliador seguir esse
argumento, e isso é declarado, não escondido. (b) A materialidade ordinal tem latitude (0,25 vs
0,35 para a JBSS3); a escolha usa o degrau ordinal já existente e a evidência da auditoria, sem
sintonia fina por resultado. (c) A estratégia continua fina e limitada pelos cinco anos-safra
(R1); D-061 a torna **não-degenerada**, não a torna poderosa. (d) O contrato de estratégia
(`strategy_spec.py`) e o operacional (`operational_spec.py`) **não mudam**; muda apenas o artefato
de exposição consumido. O holdout permanece lacrado e roda **uma vez** na Fase 6.

---

### D-062 — Auditoria das estruturas de monetização de H1; retenção da estratégia de ações (Fase 5)

**Data**: 2026-07-24

**Pergunta que motivou a decisão.** Depois do D-061, o time levantou a questão estrutural certa:
*a estrutura de ações (long/short produtor–processador) é a certa, dado que só o H1 é sólido?* O
único resultado não-circular do projeto é o H1 — o choque climático prevê a revisão de produção da
CONAB (nowcast de **quantidade nacional marginal**). O canal de preço morreu (H2a, 6×), e a tradução
em ações é fina e no dev virou aposta de setor (D-060). A estrutura atual foi desenhada no D-002 para
a **tese de preço**, que foi falsificada — ela é órfã da hipótese que a justificava. Antes de gastar
o holdout, avaliou-se, **return-agnóstico**, se um veículo melhor-casado existiria.

**Reframe.** O que se monetiza é um *nowcast da surpresa da CONAB*. O veículo ideal maximiza a
sensibilidade ao que prevemos (produção nacional marginal) por unidade de ruído próprio. Dois
candidatos foram auditados a fundo, com múltiplas personas e base acadêmica.

**Candidato (b) — Rumo / logística de grão (canal de quantidade).** Reviravolta parcial: a Rumo **não**
é a "ferrovia diversificada" do veto original — **~75% do volume é soja/milho/farelo e ela detém ~42%
do transporte de grão de Mato Grosso** (epicentro do Shock). Veículo mais líquido do tabuleiro
(R$108M/dia), reuso altíssimo do motor de ações (D-055/D-056), e âncora acadêmica forte (família
"alt-data → throughput físico → surpresa de receita": Katona, Painter, Patatoukas & Zeng, JFQA 2025,
satélite de estacionamento → earnings; Jegadeesh & Livnat, JAE 2006). **Mas a auditoria de
investibilidade achou a pegadinha decisiva, e ela é fatal para o nosso sinal: a Rumo é limitada por
CAPACIDADE, não por demanda.** A demanda por ferrovia no Brasil é historicamente maior que a
capacidade; a Rumo carrega 42% e o resto transborda para caminhão; o volume dela cresce puxado por
capex (60,1B TKU em 2019 → 64B em 2021), não pela safra. Como sempre sobra mais grão do que ela
consegue levar, uma **revisão marginal** da safra (o que nosso sinal prevê) **não move o volume anual**
— muda só o transbordo para caminhão e o *timing* trimestral. Só uma quebra **catastrófica** apareceria.
Pela lógica de poder (D-045/A1), adicionar um nome líquido de **baixa sensibilidade ao sinal dilui** o
sinal — mesma vala dos frigoríficos de boi, por outro motivo. **A Rumo não entra na estratégia.**

**Candidato (d) — spread soja–milho (canal de preço diferencial).** A triagem return-agnóstica de
divergência passou com folga (corr soja×milho2ª = −0,33; mesmo sinal em 43% dos anos; desvio do
diferencial 2,7× o do nível comum) — há sinal diferencial real. Vantagens: macro-neutro por
construção, atribuição limpa, o mais "modelo quantitativo" dos dois. **Mas três rachaduras
estruturais:** (1) é uma aposta de **preço**, e o canal de preço morreu — confirmado também na
literatura (Silveira, *J. Futures Markets*, 2025: a reação de preço à CONAB é mais fraca que à WASDE);
(2) o instrumento natural é **CBOT** — o mercado que os próprios docs (H5/`06`) chamam de eficiente
demais para esse edge, contradizendo a tese de ineficiência **brasileira**; (3) é um **trade clássico**
(spread soja–milho é o hedge de clima mais batido do agro), perdendo ponto de originalidade, e exige
um **motor de futuros do zero** (baixo reuso). Rejeitado como estratégia primária.

**Decisão.** (i) **Reter a estratégia de ações do D-061** — não porque é ótima (é fina, R1/R7), mas
porque nenhuma alternativa a supera de fato, ela reaproveita todo o maquinário e expressa o canal mais
direto (dano de volume próprio sob H′). (ii) **Nenhum veículo novo entra**: Rumo rejeitada por
capacidade; spread rejeitado por canal morto/eficiência/reuso. (iii) A **divergência soja–milho de (d)**
é retida como **evidência de apoio** no relatório (o sinal distingue soja de milho ⇒ é agronômico, não
macro), sem virar backtest — um motor, sem custo de N nem de comparações múltiplas. (iv) A **auditoria
inteira vira ativo de rigor**: demonstra, com fonte primária e paper, que avaliamos veículos
alternativos e por que cada um é amortecido — rigor que pontua em Backtest (15%) e Análise (15%).

**Por quê (a verdade estrutural).** Não existe veículo brasileiro líquido com sensibilidade limpa e
alta a um nowcast de produção **marginal**: produtores são idiossincráticos + preço morto + ilíquidos;
a Rumo é capacidade-limitada; o spread é preço-morto em mercado eficiente. O gargalo é do elo
**sinal→ativo**, não do ativo — por isso trocar de veículo não resolve. Isso confirma, com evidência,
a limitação nº 1 (R1) e a estreiteza do universo (R7).

**Custo/limitação declarado.** (a) A estratégia continua fina e de baixo poder — a decisão a torna
**a mais defensável disponível**, não poderosa. (b) A rejeição da Rumo apoia-se em evidência econômica
de investibilidade (capacidade), não num teste de retorno da RAIL3 (que seria dev-limitado e queimaria
teste) — é return-agnóstica e declarada como tal. (c) As referências acadêmicas (Silveira 2025 JFM
DOI 10.1002/fut.22601; Katona et al. JFQA 2025; Jegadeesh & Livnat 2006) precisam ser **conferidas na
fonte primária** antes de qualquer citação no relatório (regra do `10_REFERENCIAS.md`). (d) O contrato
congelado (`strategy_spec.py`/`operational_spec.py`) e o artefato H′ (D-061) **não mudam**; o holdout
segue lacrado.

> **Refinamento posterior (2026-07-26, ver D-063):** a rejeição da Rumo aqui apoia-se em "volume
> anual insensível", o que é verdadeiro mas incompleto. Sob capacidade travada o sinal **não some —
> migra do volume para o frete/margem**, e é esse canal, de sinal ambíguo e abafado por take-or-pay,
> que sustenta a rejeição. O D-063 corrige a formulação e enumera o espaço completo de veículos.

---

### D-063 — Correção do canal Rumo e enumeração estruturada do espaço de monetização de H1 (Fase 5)

**Data**: 2026-07-26

**Pergunta que motivou a decisão.** Ao revisar o D-062, o time cobrou **exaustividade**: *e outros
canais de transporte (portos, hidrovias)? e outras variantes de spread? e outros jeitos de arrumar a
estratégia que já temos?* O D-062 auditou dois candidatos a fundo, mas não mapeou o espaço inteiro
nem julgou o canal da Rumo com a precisão devida. Esta decisão fecha as duas lacunas, **return-agnóstica**.

**Correção do canal da Rumo (dívida de honestidade do D-062).** O D-062 rejeitou a Rumo por "volume
anual insensível à revisão marginal". Isso é verdadeiro mas trata o amortecimento como total, e não é.
Sob **capacidade estruturalmente travada** (demanda por logística > oferta no Brasil), uma safra marginal
não desaparece do sinal — **ela migra do canal de volume para o canal de frete/margem**: mais grão
disputando trilho/porto escassos pressiona o frete para cima. O que mata a Rumo como veículo do *nosso*
sinal não é a ausência de canal, e sim que esse canal remanescente é **quádruplo-amortecido**: (i)
**abafado por take-or-pay** — boa parte da receita é contratada e não responde ao spot; (ii) **de sinal
ambíguo, possivelmente perverso** — safra cheia → congestão → frete/margem *sobem*, o que teria o sinal
**oposto** ao do produtor sob H′ (a Rumo *ganharia* com a fartura que prejudica o produtor); (iii)
**regulado** (tarifas de ferrovia/porto têm tetos), o que trunca a transmissão; (iv) o elo
**margem→lucro→retorno** nunca foi estabelecido para a RAIL3 — seria um segundo H2a a provar, com o
mesmo N de 5 anos-safra. Conclusão inalterada, motivo afiado: **a Rumo não entra**, agora porque seu
canal vivo (margem) é abafado, ambíguo no sinal e não-estabelecido — não porque o veículo seja inerte.

**Enumeração estruturada (a moldura "nenhuma pedra sem virar").** Cada veículo/estrutura julgado pelos
cinco filtros do reframe do D-062 (sensibilidade **limpa** ao nowcast de produção **marginal
brasileira**; liquidez B3; expressão da ineficiência **brasileira**; validável no **dev** — não
holdout-only; reuso do motor). `Sens.` = sensibilidade ao sinal; `Val.` = validável no dev.

| Veículo / estrutura | Canal econômico | Sens. | Líquido BR | Inefic. BR | Val. dev | Veredito |
|---|---|---|---|---|---|---|
| **Ações produtor×processador (atual, D-061)** | dano de volume próprio (H′/Q) | fraca mas limpa | não (produtor ilíquido) | sim | sim | **retido** (mais defensável) |
| Ferrovia — Rumo/RAIL3 | volume→frete/margem | ambígua, abafada | sim (R$108M/d) | parcial | sim | rejeitado (canal abafado/perverso) |
| Porto grão — Santos Brasil/STBP3 | throughput | ~nula p/ grão | sim | parcial | sim | rejeitado (Tecon = contêiner, não bulk de grão; mesma capacidade) |
| Hidrovia — Hidrovias do Brasil/HBSA3 | volume de barcaça (grão-pesado) | melhor-casada dos transportes | médio | sim | **não** (IPO set/2020 → holdout-only) | fora (não-validável, como JALL3) |
| Caminhão / rodoviário | frete rodoviário | sinal certo (transbordo) | **sem pure-play B3** | — | — | inexistente como veículo |
| Spread soja–milho (D-062/d) | preço diferencial | real (corr −0,33) | via CBOT | **contradiz** (CBOT eficiente) | sim | rejeitado (canal de preço morto + trade clássico + motor do zero) |
| Basis Brasil−Chicago (local − CBOT) | prêmio local de oferta | **a mais limpa** teoricamente | **não** (sem instrumento líquido acessível) | sim | não | ideal no papel, inacessível na prática |
| Crush spread (soja→farelo+óleo) | margem de esmagamento | de processamento, não de produção | via CBOT | não | sim | fora do escopo (não é surpresa de quantidade) |
| Insumos / fertilizante (montante) | custo de insumo (canal C) | global, não BR | não-BR | não | — | fora (é o `C` global inseparável do D-034) |

Padrão que emerge: **todo veículo de transporte herda o mesmo gargalo de capacidade** (o sinal migra
para margem, de sinal ambíguo) exceto a hidrovia — que seria a melhor-casada, mas é **holdout-only**
por IPO em 2020, logo não-validável no dev pela mesma regra que barrou JALL3 (D-052). E **todo veículo
de preço** (spread, basis, crush) esbarra no canal de preço morto (H2a, 6×) e/ou na eficiência do CBOT.
Confirma a verdade estrutural do D-062 com o espaço **mapeado**, não só amostrado: o gargalo é do elo
**sinal→ativo**.

**"Outros jeitos de arrumar o que temos" — o thread retido.** A cobrança tem uma terceira frente que
**não** é troca de veículo: melhorar a estrutura atual. As alavancas de re-ponderação (materialidade,
não-linearidade) já foram usadas no D-061 (colapso 1→8 estados); a expansão de universo foi varrida
(nenhum nome líquido faltando). Resta a alavanca com maior lastro empírico: o D-060 provou que o P&L do
dev é **aposta de setor** (spread proteína×produtor, R²=0,84), não alfa de clima. Logo o jeito
substantivo de "arrumar" é **isolar o resíduo climático do beta de setor** — um **hedge de setor
pré-registrado** sobre o livro atual. Isso ataca o problema confirmado (contaminação de setor), é
return-agnóstico, reusa o maquinário e materializa o "market-neutral feito direito" que o R23 exige.
**Aberto como thread próprio (será D-064 quando implementado)**; não altera o contrato congelado.

**Decisão.** (i) Corrigir a formulação do canal Rumo no registro (feito acima e como nota no D-062).
(ii) Registrar a enumeração como ativo de rigor do relatório — a busca por veículo alternativo está
**encerrada e mapeada**, não reabrir sem fato novo. (iii) Abrir o hedge de setor como o thread de
"arrumar o que temos", a ser pré-registrado e testado **return-agnóstico** antes do holdout.

**Por quê.** A cobrança de exaustividade é legítima e a resposta honesta não é "já olhei" e sim o mapa
completo com o critério explícito de rejeição de cada célula — isso *é* o entregável de rigor. E a
correção da Rumo paga uma dívida de honestidade: uma decisão recém-tomada estava certa na conclusão e
imprecisa no argumento; consertar o argumento vale mais que defender a redação.

**Custo/limitação declarado.** (a) A enumeração é qualitativa/return-agnóstica — não roda RAIL3/STBP3/
HBSA3 (queimaria teste com N mínimo e alguns são holdout-only). (b) O basis Brasil−Chicago é declarado
"ideal no papel" sem instrumento — é uma admissão de limite, não um plano. (c) O hedge de setor ainda
é uma **abertura**, não um resultado; seu valor depende de o resíduo climático sobreviver à
neutralização — o que pode falhar, e falhar seria um achado válido. (d) Contrato congelado e holdout
seguem intocados.

---

### D-064 — Decomposição setor×clima pré-registrada como leitura do holdout (Fase 5)

**Data**: 2026-07-26

**Pergunta que motivou a decisão.** O D-060 provou que, no dev, o P&L é dominado por uma **aposta de
setor** (produtor×processador), não pela dispersão cross-section de clima. O D-063 abriu o "hedge de
setor" como o jeito de "arrumar o que temos". A pergunta operacional: *como o hedge de setor entra sem
comprometer a disciplina do holdout?* Três formas foram postas ao time (2026-07-26): (1) decomposição
do primário; (2) segunda estratégia negociada com inferência própria; (3) substituir o contrato
congelado. **O time escolheu (1).**

**Decisão.** O hedge de setor entra como uma **regra de decomposição pré-registrada**, não como mudança
da estratégia negociada. `backtest/diagnostics.py::sector_orthogonal_decomposition` congela, antes do
holdout, uma separação **aditiva e exata** do retorno bruto do livro em (i) a parte alinhada à aposta
de setor e (ii) o resíduo ortogonal a ela. A cada pregão projeta os pesos reais `w` sobre os pesos da
carteira setorial ingênua `s` (mesma máquina, mesmos caps/elegibilidade):

```
c = ⟨w,s⟩/⟨s,s⟩ ;  w_setor = c·s ;  w_clima = w − c·s  (⟨w_clima, s⟩ = 0)
g_setor + g_clima = Σ w·r = g_livro   (linearidade exata)
```

A separação usa **só `w` e `s`, nunca retornos** — logo é return-agnóstica e congelável agora. Na
Fase 6 esta mesma regra é aplicada ao resultado do holdout: reporta-se o retorno do livro congelado
**e** sua fatia climática (resíduo) vs. de setor (projeção). No dev roda como demonstração descritiva
e **circular** (Bloco C′ do `run_diagnostics_dev.py`); a inferência mora só no holdout.

**Por quê (1) e não (2)/(3).** (2) transformaria o resíduo num segundo livro com inferência própria,
**multiplicando a família de testes** num holdout de apenas 5 anos-safra (N mínimo) — dividiria o α e
enfraqueceria os dois testes por pouco retorno marginal. (3) redesenharia o contrato **congelado**
reagindo a um diagnóstico visto no **dev** — exatamente o "design no dev" que o congelamento existe
para impedir. (1) entrega o essencial — **medir e mostrar** quanto do retorno do holdout é clima vs
setor — sem gasto extra de α, sem tocar no que está congelado e sem reagir ao dev de forma que invalide.
É a resposta madura à fraqueza que nós mesmos encontramos (D-060): a estratégia não muda; ela aprende a
se explicar. Se a decomposição do holdout mostrar um resíduo climático forte, aí sim (2) pode ser
pré-registrado como passo seguinte — mas com fato novo, não sobre o dev.

**Distinção do D-060.** `sector_climate_decomposition` (D-060) — incremento sobre a ingênua +
regressão ex-post no spread — permanece como descritivo do dev. O `sector_orthogonal_decomposition`
(D-064) é a decomposição **aditiva/exata/return-agnóstica** que vai ao holdout. As duas coexistem; a
segunda é a pré-registrada.

**Custo/limitação declarado.** (a) A decomposição é **aritmética** (soma de contribuições diárias
brutas), não composta, e é feita **antes de custos** — custos não são lineares na projeção e são
reportados à parte; declarar isso ao ler o holdout. (b) A "direção de setor" é a carteira ingênua
produtor+/processador− ponderada igual; é uma escolha de eixo (defensável porque é exatamente o viés
que o D-060 achou), não a única projeção possível — beta de mercado é um segundo eixo deixado como
robustez futura, não pré-registrado aqui. (c) Não é hedge negociado: o livro continua carregando a
aposta de setor; a decomposição a **mede**, não a remove da execução. (d) O número do dev é circular e
não vale como validação; contrato congelado e holdout seguem intactos.

---

### D-065 — Pré-registro da suíte de robustez do sinal H1 (Fase 5), anterior aos resultados

**Data**: 2026-07-26

**O que foi decidido.** Congelar, **antes de rodar**, o grid de perturbações e os critérios de aprovação
da suíte de robustez do mecanismo H1 (clima→revisão CONAB), em `stats/robustness_spec.py`. É
**return-agnóstico**: testa o mecanismo H1a, não retornos; o holdout de retornos segue lacrado e a
leitura por sub-amostra respeita a separação dev/holdout de D-029 (reportada, não usada para escolher).

**Grid (single-knob a partir do baseline congelado de D-030).** Cada perturbação mexe em **exatamente
um botão** (travado no `__post_init__`): (real) climatologia ±2 anos; fonte `final` vs `prelim` (com
ressalva de vintage R15/R16); lag de disponibilidade +14 dias; janela crítica ±15 dias. (placebo)
espacial — `Shock` embaralhado entre UFs no mesmo ano-safra; temporal — `Shock` do ano-safra anterior.

**Critérios (congelados).** Perturbação **real** passa se o β agrupado no span cheio mantém o sinal
esperado (β<0, estresse ⇒ revisão para baixo) **e** |β|/|β_base| ∈ [0,4; 2,5]. **Placebo** comporta-se
bem se |β| < 0,5×|β_base| **e** bootstrap p > 0,10 — um placebo significativo e de mesmo sinal é
**bandeira vermelha** (sinal possivelmente mecânico). Veredito global "robusto" = todas as reais
preservam o sinal, ≥5/6 na banda, e os dois placebos morrem. β_base é o baseline pooled de H1a
(D-030/D-031, β≈−0,067). O dev é reportado como descritivo (N minúsculo), nunca gate.

**Por quê separar pré-registro de execução.** A honestidade científica está em declarar o grid e os
limiares **antes** de ver os números, para não poder escolher a posteriori quais perturbações reportar
ou onde traçar a banda. Este commit é anterior à materialização — mesmo padrão do projeto que colocou a
regra da matriz `E` num commit anterior aos dados (D-032). A suíte só é informativa **agora** porque o
D-061 desfez a degeneração da carteira (1→8 estados): antes, robustez de um livro de 2 estados era vazia.

**Custo/limitação declarado.** (a) A banda [0,4; 2,5] e o teto de placebo 0,5 são escolhas de
julgamento — congeladas aqui para não serem ajustadas depois, mas são convenções, não verdades. (b) A
fonte `final` carrega o alerta de vintage (R15/R16): entra como sensibilidade, não como fonte primária.
(c) O N de anos-safra é pequeno; a suíte mede **estabilidade de desenho**, não adiciona poder
estatístico. (d) Ainda não rodou — este passo é só o pré-registro; a execução e os números vêm a seguir.

---

### D-066 — Resultado da suíte de robustez do sinal H1 (Fase 5)

**Data**: 2026-07-26

**O que foi feito.** Executou-se, uma vez, o grid congelado de D-065 (`scripts/run_robustness_h1.py`,
`stats/robustness.py`), com o motor de Shock **intocado** — cada perturbação constrói inputs
modificados para o `build_h1a_panel`. Baseline bit-idêntico ao portão: β=**−0,0672**, bootstrap
p<0,001, N=729, 8 anos-safra. Return-agnóstico; holdout de retornos lacrado.

**Robustez direcional — forte.** As quatro perturbações reais que rodaram **preservaram o sinal
(β<0) e a ordem de grandeza** (|β|/|β_base| na banda [0,4; 2,5]): climatologia +2 anos **0,97×**;
lag de disponibilidade +14d **1,02×**; janela +15d **0,76×**; e a **fonte `final` fortalece** o sinal
(β=−0,092, **1,37×**) — o mecanismo não depende do botão específico. O **placebo temporal morreu
limpo** (β=+0,011, p=0,42, sinal invertido): o sinal não é artefato de tendência temporal.

**O achado central — componente nacional-comum (placebo espacial).** O placebo espacial (choque
embaralhado entre UFs no mesmo ano-safra) **não morreu por completo**: embaralhar a geografia destrói
~69% do β (β cai de −0,067 para −0,021), confirmando que **a maioria do sinal é regional**, mas sobra
um resíduo de ~31% **significativo** (p=0,019, mesmo sinal). Leitura: existe um **componente
nacional-comum forte** — um ano seco desloca choque e revisão de todas as UFs juntas, então o choque de
uma UF trocada ainda prevê a revisão de outra. Isto **caracteriza**, não falsifica, H1: o sinal é real
e majoritariamente regional, mas parte relevante da sua força é um **nowcast nacional**, não
discriminação regional fina. Coerente com D-060/D-061 (cross-section fino) e com a auditoria de veículos
D-062/D-063 (o que se monetiza é uma surpresa de produção **nacional**).

**Dois botões não rodaram — piso de dado, declarado (não fragilidade).** Climatologia −2 anos exige a
série `final` antes de 2000-12 (início da cobertura) ⇒ falha de cobertura em 1998. Janela −15d exige
`prelim` em meados de novembro, fora da janela crítica (Dez–Mai) para a qual o painel municipal foi
materializado. Ambas são limites de **cobertura de dado**; uma materialização futura mais ampla poderia
rodá-las — não se ajustou a magnitude pós-hoc para forçar execução.

**Veredito global pré-registrado: NÃO ROBUSTO — reportado fielmente.** O gate de D-065 reprovou por
**dois** motivos, e por honestidade os dois ficam registrados: (i) só 4<5 perturbações reais foram
executáveis (pisos de dado); (ii) o placebo espacial ficou significativo. **Nenhum dos dois é
fragilidade direcional do sinal** — que foi, ao contrário, notavelmente estável. O gate estrito falhar e
ser reportado assim mesmo *é* o entregável de rigor: fixamos a régua antes dos números e não a afrouxamos.

**Consequência para o relatório.** (a) Apresentar a tabela de robustez direcional como força (sinal e
magnitude estáveis, `final` inclusive fortalece). (b) Declarar o componente nacional-comum como
limitação honesta — não vender o β agrupado como identificação regional limpa. (c) Amarrar a narrativa:
H1 é um nowcast nacional robusto de direção, o que explica por que a tradução cross-section em ações é
fina (D-060) e por que nenhum veículo isola o sinal de forma limpa (D-063).

**Custo/limitação declarado.** (a) O componente nacional-comum limita a identificação regional — é o
principal achado a comunicar. (b) Dois botões pré-registrados não rodaram por cobertura; a robustez a
esses eixos fica **não testada**, não aprovada. (c) N pequeno de anos-safra: mede estabilidade, não
adiciona poder. (d) Mecanismo, não retorno; holdout intacto.

---

### D-067 — Pré-registro do ramo AGRO3×ADTV e da profundidade da perna produtora

**Data:** 2026-07-26

**Pergunta que motivou a decisão.** A AGRO3 nunca superou ADTV21 de R$8 milhões no dev 2018/19;
por isso a perna produtora ficou reduzida à SLCE3 e ao cap de 0,40. No holdout a AGRO3 pode nunca,
às vezes ou sempre passar o piso. Deixar para decidir depois dos retornos como tratar esses estados
abriria um ramo oportunista exatamente antes da rodada única.

**Decisão operacional, anterior ao holdout.** Não existem carteiras alternativas a escolher. A regra
primária de D-055 permanece: em cada decisão `D`, a AGRO3 entra somente se cumprir os gates PIT,
inclusive ADTV21 ≥R$8 milhões, e possuir score válido; sai somente daquele bloco quando falha, sem
*carry-forward*, classificação retroativa da safra ou alteração do piso. O teste primário e a carteira
consomem os grãos válidos/elegíveis do mesmo bloco e continuam exigindo ao menos um produtor e um
processador. As cinco safras permanecem no único teste exato; o ramo não cria família inferencial.

**Auditoria executável.** `build_target_schedule` passa a registrar, por decisão,
`agro3_eligible`, `agro3_active`, quantidade de produtores ativos e quantidade de processadores
ativos. `diagnostics.audit_agro3_liquidity`, sem preços ou retornos, classifica a trajetória como
`never_eligible`, `intermittent` ou `always_eligible` e conta blocos com zero/um/dois produtores e
com núcleo econômico disponível. O bloqueio técnico do holdout permanece: a classificação real só
será materializada dentro do tiro deliberado da Fase 6.

**Interpretação congelada.**

1. `never_eligible`: a perna produtora tem no máximo a SLCE3. Mesmo com P&L/teste positivo, não se
   alega dispersão cross-sectional entre produtores; o livro é descrito como spread
   produtor–processador com produtor concentrado.
2. `intermittent`: resultados com/sem AGRO3 e atribuição por profundidade são descritivos, sem
   p-valores ou conclusões por subgrupo. Todos os blocos válidos permanecem no teste único.
3. `always_eligible`: dois produtores só contam quando AGRO3 e SLCE3 estão simultaneamente ativos.
   A profundidade melhora, mas não transforma P&L positivo em alpha climático sem D-064/H4/H5.

As sensibilidades de liquidez R$4 milhões/R$12 milhões já previstas em `docs/05` rodam depois do
primário no mesmo pacote, com AUM, participação máxima, custos e gates inalterados. São diagnóstico;
não podem substituir R$8 milhões nem mudar o veredito primário.

**Custo/limitação declarado.** (a) A composição do painel varia endogenamente com liquidez, portanto
o N cross-sectional por bloco deve ser mostrado. (b) Se a AGRO3 continuar fora, o projeto aceita a
concentração em vez de baixar o piso. (c) Uma comparação descritiva entre blocos com/sem AGRO3 mistura
tempo e regimes; não identifica efeito causal da liquidez. (d) O passo fecha a interpretação, mas não
adiciona poder, nomes ou evidência de retorno. Holdout intacto; suíte 519→523 testes.

### D-068 — Congelamento do pacote indivisível e preflight da rodada única

**Data:** 2026-07-26

**Problema que motivou a decisão.** A estratégia econômica e a mecânica primária estavam congeladas,
mas “rodar o holdout uma vez” ainda não era uma operação indivisível. A suíte histórica continha
promessas que se tornaram incompatíveis com decisões e dados posteriores: climatologias fora do grid
D-065, dev 2015/16–2019/20 apesar de R26 e da zona de transição, Method B/universo alternativo já
suspensos, e H5 geográfico ainda sem materialização. Também duplicava o fator de mercado ao propor
IBOV junto de `Rm_minus_Rf`. Sem correção anterior aos retornos, haveria espaço para escolher o que
rodar, como interpretar e quando parar.

**Decisão inferencial.** `backtest/holdout_spec.py` congela a ordem dos 12 blocos e proíbe pausa ou
exibição intermediária. O teste exato H′ de cinco anos-safra, unilateral a 10%, é a **única hipótese
confirmatória**. Todos os demais blocos rodam mesmo que ele falhe:

1. custos zero/base/2×, AGRO3×ADTV e setor×clima D-064;
2. H4 e H5 como vetos adversariais à expressão “alpha climático”;
3. leave-one-name-out, leave-one-crop-year-out e grids single-knob como sensibilidades descritivas;
4. métricas, atribuição e selo final.

H4 usa `r_estratégia líquida − Risk_Free` como desfecho. A especificação core contém os cinco
fatores NEFIN (`Rm_minus_Rf`, SMB, HML, WML, IML); a estendida adiciona USDBRL, soja, milho 2ª,
açúcar e ONI. Não entra IBOV, evitando duplicação de mercado. A inferência é HAC/Newey–West com
21 lags e α=0,10; somente a estendida é veto.

H5 mantém como veto o placebo geográfico de área não produtora, com a mesma estratégia, calendário,
score e custos: sobre o retorno líquido base médio dos cinco anos-safra, com sign-flip exato dos
clusters, ele deve reter menos de 50% da estatística do sinal real em módulo e ter p unilateral
acima de 0,10. A permutação de exposições dentro de cada lado econômico é obrigatória, porém
descritiva: com dois produtores e dois processadores há apenas `2!×2!=4` permutações, insuficientes
para outro teste a 10%. O embaralhamento de UFs de D-065/D-066 testa H1 e **não substitui** H5.

**Grids mantidos.** Além de custo zero/base/2×: ADTV R$4 mi/R$12 mi em torno do piso primário de
R$8 mi; horizonte 10/42 em torno de 21 pregões; lag total 14/21 em torno de 7 dias; cap de grãos
0,30/0,50 em torno de 0,40; cap de cana 0,10/0,20 em torno de 0,15; exclusão individual dos cinco
nomes e das cinco safras. Variações de climatologia/janela/fonte final já pertencem a D-066, no
mecanismo, e não geram novos P&Ls de holdout. Temperatura, Method B, matriz `E` alternativa e
universo alternativo ficam fora.

**Níveis de afirmação congelados.**

- retorno líquido base positivo permite dizer apenas “P&L OOS positivo”;
- evidência OOS da estratégia exige também aprovação do primário H′;
- evidência de alpha climático exige os dois anteriores, componente climático D-064 positivo,
  passagem de H4 estendida e morte do placebo geográfico H5.

**Implementação segura e bloqueios.** `backtest/holdout.py` e `scripts/run_holdout_once.py` implementam
somente o preflight: validam o payload lógico, atestam os fontes por SHA-256 e listam presença dos
sete inputs sem parsear parquets. `--execute` falha antes do I/O porque
`EXECUTOR_IMPLEMENTED=False`. O payload lógico está travado pelo hash civil
`cefa5f60b78e373e07060f68dcc65412c4e832663deac980f62b43cd7b202900`; qualquer divergência
falha já no import. A rodada continua bloqueada até três entregas anteriores ao unlock:
(i) controles diários confiáveis e manifestados de H4; (ii) geografia não produtiva e score H5;
(iii) executor indivisível, registro civil e emissão atômica dos 12 artefatos. Os caminhos dos
inputs são fixos em `data/interim/holdout/`; arquivos de dev, downloads atuais e substituições ad hoc
não são aceitos.

**Custo/limitação declarado.** (a) O escopo de robustez ficou menor que a promessa histórica, mas
agora cada item é executável e compatível com as decisões congeladas. (b) H4 depende de futuros
contínuos cuja regra de rolagem ainda precisa ser definida; confirmação de ticker não é dado pronto.
(c) H5 continua existencial e ainda não existe: sua ausência veta a alegação climática e a execução.
(d) O pacote não aumenta os cinco eventos independentes nem transforma sensibilidades em poder.
(e) Este passo congela o plano e prova que a porta está fechada; não lê retorno, score ou peso do
holdout. Suíte 523→530 testes.

### D-069 — Controles diários H4: proxies negociáveis e snapshot ex post

**Data:** 2026-07-26

**Problema.** D-068 congelou as colunas de H4, mas não suas fontes e transformações. Usar os
tickers contínuos front-month do Yahoo introduziria saltos de rolagem sem uma regra por contrato;
inventar essa regra agora abriria novos graus de liberdade. Dados mensais FRED/IMF não conseguem
explicar retorno diário. H4 também precisava respeitar calendários distintos (B3, NYSE e Federal
Reserve) sem puxar uma observação futura para um pregão brasileiro.

**Decisão de fonte.**

- fatores e taxa livre de risco: snapshot NEFIN D-022;
- câmbio: **DEXBZUS**, nível diário BRL por USD do FRED/Federal Reserve;
- commodities: adjusted close, em USD, dos ETFs futuros Teucrium **SOYB**, **CORN** e **CANE**;
- regime climático: ONI D-021 em nível, usando a última temporada cuja `avail_date`
  conservadora já ocorreu.

Os três ETFs têm benchmarks públicos baseados em três vencimentos. A rolagem passa a ser a regra
pré-existente de um veículo negociável, não uma série construída pelo time. Isso resolve a lacuna
de rolagem declarada em D-068 sem trocar as commodities congeladas.

**Transformação.** O calendário-mestre é o NEFIN/B3. Cada nível externo é carregado somente para
a frente até a sessão brasileira, com staleness máxima de quatro dias corridos, e vira retorno
simples entre sessões B3 consecutivas. Feriado americano pode produzir retorno zero numa sessão
brasileira; o movimento acumulado aparece na próxima observação disponível. Não há backfill.
Retornos dos ETFs permanecem em USD e a variação BRL/USD entra separadamente, evitando converter
o mesmo risco cambial duas vezes.

O painel inteiro é um **snapshot ex post** com `avail_date=27/07/2026`, a captura mais tardia.
Yahoo, FRED e NOAA podem reescrever o histórico; não se finge disponibilidade D+1. H4 nunca alimenta
sinal, score, universo ou ordem. Sua regressão ainda não foi executada porque o desfecho são os
retornos lacrados da estratégia.

**Materialização e auditoria.** `ingest/h4_market.py` baixa e valida quatro fontes de mercado;
`robustness/h4_controls.py` alinha e valida o painel; `scripts/build_h4_controls.py` prende a
primeira seleção de capturas e recusa substituição silenciosa. Resultado:

- 1.495 sessões, 02/01/2020–30/12/2025;
- 13 colunas, zero células ausentes e zero datas duplicadas;
- parquet `data/interim/holdout/h4_controls.parquet`, SHA-256
  `07811b9ec22b8914c9081e46bee8858446e4f098f54c2159c8b20a0ce6b3e666`;
- seis fontes e transformações registradas em `h4_controls_summary_v1.json`;
- rebuild bit-a-bit; cache sem manifesto/hash falha alto; rebuild divergente não sobrescreve
  o arquivo congelado.

O hash lógico do pacote muda de `cefa5f60…2900` para
`9ffa0fbfff81f7ccab1aee09093af2b2167e4b01add2e61a5c342f7919a08df6`, mudança
pré-holdout que apenas inclui os novos fontes/registro H4 em `SPEC_FILES`. Estratégia, teste,
grids, claims e executor bloqueado permanecem iguais. O preflight agora mostra `h4_controls`
presente e seis inputs ainda ausentes.

**Custo/limitação declarado.** (a) ETF é proxy: inclui collateral yield, despesas, tracking
error e curva de futuros; não é spot brasileiro. (b) Yahoo adjusted close e ONI não preservam
vintage, mitigado por captura/hash e `avail_date` única de snapshot, não eliminado. (c) Fechar
o input não é passar H4: o alpha só será estimado na rodada única. (d) A coincidência imperfeita
de closes NYSE/B3 pode gerar não-sincronicidade; H4 é atribuição contemporânea ex post, não regra
de negociação. (e) Nenhum retorno de ação ou estratégia foi lido. Suíte 530→540 testes.

### D-070 — Geografia placebo H5 congelada antes da materialização

**Data:** 2026-07-26

**Problema.** O pré-registro prometia recalcular o `Shock` em células sem produção agrícola
relevante, citando Amazônia central ou litoral, mas não fixava polígonos, pesos ou a prova de
não produção. Escolher coordenadas depois de observar o choque placebo criaria o mesmo grau de
liberdade que o H5 deve combater. Rebaixar milhares de rasters globais para uma caixa nova
também seria redundante: o painel CHIRPS D-027 já contém todos os municípios das UFs cobertas
pela malha fixa.

**Decisão anterior ao choque placebo.** H5 usa as 91 células CHIRPS cujos centros caem nos
polígonos IBGE 2013 de **Canavieiras, Maraú e Salinas da Margarida (BA), Matinhos e Pontal do Paraná
(PR)**. São duas faixas do litoral atlântico, uma das geografias não produtoras explicitamente
previstas em H5. A média de precipitação é ponderada pelo número fixo de células de cada
município — equivalente a peso igual por célula, sem PAM no sinal placebo.

O snapshot PAM/SIDRA foi auditado **antes** de calcular qualquer série climática: nos cinco
municípios, a quantidade produzida é exatamente zero para soja e milho total em cada ano de
2014–2024 (110 observações). O milho/BA exigiu uma captura adicional oficial, presa pelo
manifesto `pam_1612_corn_total_2014-2024_ba_20260727.json`. A seleção completa e os hashes
ficam em `h5_geography_spec_v1.json`; o contrato executável vive em
`robustness/h5_geography_spec.py`.

**Tudo que não muda.** O placebo reutiliza integralmente as janelas `PRIMARY_WINDOWS`, a
climatologia expanding do mesmo trecho, o mínimo de dez safras, os pesos CONAB da safra
anterior encerrada, as exposições H′, o calendário, direção, sizing e custos. Só o suporte
espacial da chuva muda. O score e o retorno do H5 continuam não calculados neste commit.
O hash lógico pré-holdout muda de `9ffa0fbf…df6` para
`fbcaa5d02d35c9364fb093fd3df21fc0833ff6712fb6958b6f826d516534964f`, incluindo
somente o contrato, o registro e o manifesto de auditoria H5 em `SPEC_FILES`.

**Custo/limitação declarado.** (a) O suporte costeiro não representa toda geografia não
produtora do Brasil e não inclui a alternativa amazônica citada como exemplo. (b) Zero
soja/milho não significa ausência de outros cultivos, atividade urbana ou risco macro; isso é
intencional, pois H5 tenta preservar confundidores amplos e retirar o canal agronômico de
grãos. (c) PAM reescreve o passado: a prova vale para o snapshot capturado, não para vintages
históricos reconstruídos. (d) A materialização posterior deve falhar se qualquer uma das 91
células, dos 6.197 raster-dias ou das identidades municipais divergir. (e) Nenhum `Shock`
placebo e nenhum retorno foi calculado.

### D-071 — Scores geográficos H5 materializados; veto de retorno segue lacrado

**Data:** 2026-07-26

**Pré-condição verificável.** O commit `1522ae6` congelou D-070 antes desta materialização.
Logo, municípios, células, regra de zero PAM, agregação, janelas e pesos já estavam no histórico
antes de qualquer valor do `Shock` placebo ser calculado.

**Implementação.** `robustness/h5_geography.py` agrega o painel municipal por número de células,
carimba prelim/final com os mesmos lags do sinal real e calcula uma climatologia expanding do
mesmo trecho para cada janela `PRIMARY_WINDOWS`. As janelas observáveis são agregadas com os
mesmos pesos CONAB da safra anterior; `E·Shock_placebo` usa os mesmos vintages H′ por data.
`scripts/build_h5_geographic_scores.py` usa o calendário NEFIN/B3 para os blocos congelados,
autoriza apenas a materialização de feature holdout sem retornos e escreve por arquivo
temporário.

**Resultado de engenharia, não do veto.**

- 91 células em cinco municípios e 6.197 raster-dias CHIRPS completos;
- 46 datas de decisão entre 07/01/2021 e 08/09/2025, quatro nomes de grãos;
- zero score ausente/duplicado/infinito;
- output `h5_geographic_grain_scores.parquet`, SHA-256
  `936bee66b580ad26d6b55ab4f0f004c511489243bd4cb69a9d31c87f864832e1`;
- 27 partes municipais e todas as demais fontes presas por SHA-256 em
  `h5_geographic_scores_summary_v1.json`; rebuild bit-a-bit;
- preflight reconhece `h4_controls` e `h5_geographic_scores`, mas `--execute` permanece
  bloqueado antes do I/O.

O hash lógico pré-holdout muda de `fbcaa5d0…964f` para
`cb125fea931b616e2c62ec22a2821d3899c5a84643fa28d6f02ab9060a04912b`, apenas para
incluir implementação, script e registro H5 em `SPEC_FILES`. Estratégia, H5 estatístico,
limiar de 50%, p unilateral, custos, claims e executor falso não mudam.

**Custo/limitação declarado.** (a) O score placebo usa dados do período lacrado, mas não
preços, retornos, P&L nem elegibilidade; isso é a preparação obrigatória definida em D-068.
(b) O output não diz se H5 morreu: essa comparação exige o retorno líquido real e só ocorre na
rodada única. (c) A média costeira pode carregar regime regional BA/PR e não isola causalmente
ENSO; é um falsificador severo da narrativa, não instrumento causal. (d) Os parquets municipais
foram produzidos antes sem hashes individuais; D-071 prende o estado atual de cada parte, mas
não recria 6.197 rasters brutos já descartados. O manifesto original preserva URL/hash de cada
raster. (e) O único bloqueio técnico restante é o executor/registro civil atômico. Suíte
540→549 testes.

---

## Como registrar uma decisão nova

Copie o formato acima: `D-NNN — título`, data, o que foi decidido, **por quê**, e qual o
custo/limitação da escolha. Uma decisão sem custo declarado geralmente é uma decisão mal
examinada.

Se a decisão **reverte** uma anterior, diga qual e por quê. O valor deste log está justamente
em preservar os erros, não em parecer que acertamos de primeira.
