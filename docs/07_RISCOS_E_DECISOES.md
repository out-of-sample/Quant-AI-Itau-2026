# Registro de riscos e decisões

Duas coisas neste documento: o **registro de riscos** (o que pode dar errado e o que fazemos
a respeito) e o **log de decisões** (o que decidimos, quando, por quê — e o que mudou de
ideia depois).

O log de decisões é a defesa contra a versão mais insidiosa de overfitting: mudar o desenho
depois de ver o resultado e depois contar a história como se o desenho sempre tivesse sido
aquele. **Toda mudança de desenho posterior ao congelamento entra aqui, com data.**

---

## Parte I — Registro de riscos

Probabilidade × Impacto, com dono e mitigação. Ordenado por severidade.

| # | Risco | Prob. | Impacto | Mitigação | Status |
|---|---|---|---|---|---|
| R1 | **N efetivo pequeno** — a safra é anual, então temos ~12-18 eventos independentes, não 3.000 dias. Sem poder estatístico para efeito pequeno | Alta | Alto | Cruzar culturas com ciclos fenológicos distintos (soja nov-mar, safrinha fev-jun, cana abr-nov, café set-out); agrupar erros por ano-safra; block bootstrap; **reportar N efetivo** | 🔴 **Sem solução. É a limitação nº 1 e vai declarada no relatório** |
| R2 | **A estratégia ser só beta de commodity** (H4) | Média | Existencial | Construção dollar-neutral long/short cancela boa parte da exposição líquida; teste formal de *spanning* pré-registrado | Aberto — decide-se no teste |
| R3 | **Contaminação por revisão dos dados climáticos** — POWER/ERA5 sobrescrevem o passado | **Confirmada** | Alto | CHIRPS (prelim vs. final) como fonte primária de precipitação; medir a magnitude; restringir à precipitação se for material | Mitigado parcialmente. **Temperatura segue exposta** |
| R4 | **Viés de sobrevivência do universo** — JBSS3, BRFS3, MRFG3, STBP3 sumiram em 2025 e o yfinance os apagou | **Confirmada** | Alto | **COTAHIST** (registro de pregão da B3) como fonte de universo e preço — delisting-proof por construção | ✅ Resolvido |
| R5 | **Ajuste de proventos no COTAHIST** — preços não vêm ajustados por dividendos/splits | Alta | Alto | Motor de retorno total (D-014), três fontes de eventos (D-013), **montador** (D-015) e **cross-check obrigatório contra fonte ajustada independente** (D-016) — que já pegou e corrigiu uma bonificação de 10% ausente de todas as fontes. Residual: papéis **deslistados** não têm Yahoo para conferir — declarado | ✅ **Resolvido** (residual: deslistados sem cross-check externo) |
| R6 | **Sinal ser ENSO disfarçado** (H5) | Média | Alto | ONI como controle; placebo espacial | Aberto — decide-se no teste |
| R7 | **Universo agro puro só existe pós-2021** | **Confirmada** | Médio | Backtest primário usa universo ampliado com *adjacentes* (MDIA3, KEPL3, CAML3) para recuperar histórico longo e o lado short | Mitigado |
| R8 | **Short inviável** em small caps agrícolas (sem doador / aluguel caro) | Média | Médio | Reportar variante long-only com hedge de índice em paralelo | Planejado |
| R9 | **Capacidade baixa** — estratégia pode não suportar capital relevante | Alta | Baixo (acadêmico) | Reportar a capacidade estimada explicitamente | Aceito |
| R10 | **Erro de data no calendário CONAB** — o arquivo não traz a data de divulgação dos levantamentos | Média | Alto (contamina o estudo de evento) | Mapa curado ano a ano de fontes primárias, com ≥2 fontes concordando na quase totalidade (D-017); zero interpolação; carimbo falha alto fora do mapa. O risco se materializou na coleta: o próprio site da CONAB exibe datas falsas para 2022/23 | ✅ **Resolvido** (residual: poucas datas com fonte única, anotadas no módulo) |
| R11 | **Bug de sinal invertido** — tratar frigorífico como produtor | Baixa | Existencial (silencioso!) | Teste unitário travando a convenção de sinal; checklist de revisão de PR | Mitigado por automação |
| R12 | **Rate limit / instabilidade das APIs públicas** | Média | Baixo | Cache local agressivo; pipeline nunca depende de rede em tempo de execução | Mitigado |

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
**Custo/limitação**: baixar o histórico completo (prelim+final, ~3 MB/dia × ~18 anos × 2) é
volume real — mitigado pelo cache local (não rebaixa) e por só se materializar quando o backtest
exigir. A grade de ~5 km e a agregação por caixa não resolvem município. NASA POWER (temperatura,
sem vintage) fica para o próximo passo com a limitação de revisão declarada.

---

## Como registrar uma decisão nova

Copie o formato acima: `D-NNN — título`, data, o que foi decidido, **por quê**, e qual o
custo/limitação da escolha. Uma decisão sem custo declarado geralmente é uma decisão mal
examinada.

Se a decisão **reverte** uma anterior, diga qual e por quê. O valor deste log está justamente
em preservar os erros, não em parecer que acertamos de primeira.
