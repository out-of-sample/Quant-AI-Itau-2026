# Catálogo de dados, latências e regras point-in-time

> Todas as fontes abaixo foram **testadas ao vivo** (requisição real ao endpoint) em
> 2026-07-13/14. O que não foi possível confirmar está marcado como **NÃO CONFIRMADO** —
> nada aqui é assumido por plausibilidade.
>
> Este é o documento mais importante do projeto depois do pré-registro. A maior parte dos
> backtests errados do mundo erra aqui, não no modelo.

---

## 0. A regra que governa tudo

Cada linha de cada tabela carrega duas datas:

| Coluna | Significado |
|---|---|
| `ref_date` | data a que o dado se refere |
| `avail_date` | data em que o dado **ficou publicamente disponível** |

**Nenhuma decisão em `t` pode usar linha com `avail_date > t`.** Sem exceção.

E há um problema mais sutil que a latência, que afeta **quase todas as fontes deste
projeto**:

> ### O problema do *vintage*
>
> Várias fontes **reescrevem o passado**. O número que a API entrega hoje para março de 2021
> não é necessariamente o número que estava disponível em março de 2021. Nesse caso, respeitar
> a `avail_date` **não é suficiente** — o dado em si é uma versão revisada, que embute
> informação do futuro.
>
> Isso não se corrige "tomando cuidado no código". Está na fonte. As opções são: (a) usar
> uma fonte que arquive vintages, (b) medir a magnitude da revisão e declarar a limitação.
> Fizemos as duas coisas, fonte a fonte, abaixo.

---

## 1. Clima

### 1.1 CHIRPS — precipitação — **fonte primária**

| | |
|---|---|
| O que é | Precipitação diária/pêntada, satélite + estações, UCSB |
| Cobertura | `final`: 1981-hoje; `prelim`: arquivos desde 01/01/2015, grade **0.05° (~5 km)** |
| Latência | **~2 dias** (produto *prelim*, publicado nos dias 2/7/12/17/22/27); *final* mensal, ~3ª semana do mês seguinte |
| Acesso | `data.chc.ucsb.edu` — gratuito, sem chave |
| **Vintage** | ✅ **Arquiva prelim e final SEPARADAMENTE** |

**Por que esta é a fonte primária, apesar de só ter chuva**: é a **única fonte testada que
preserva vintage**. O produto preliminar é o que estava disponível na época; o final é a
verdade revisada. Isso nos dá um proxy honesto de point-in-time e permite **medir**
diretamente o quanto a revisão contamina o sinal (`05_SUITE_ROBUSTEZ.md` §2.4) — em vez de
torcer para que não contamine.

Precipitação é, além disso, o canal físico dominante do estresse hídrico em soja e milho.

**Ingestão implementada e verificada ao vivo (2026-07-16, `ingest/chirps.py`, D-018).** Fatos do
produto p05 confirmados no arquivo real: grade **2000×7200** (0.05°), canto superior-esquerdo em
(lon −180, lat +50), `nodata = −9999`; GeoTIFF **sem compressão**, float32, geotransform
auto-descrito nas tags `ModelPixelScale`/`ModelTiepoint` — lido **sem GDAL** (só `tifffile`,
Python puro; cp314 não tem wheel de rasterio). URLs por data são imutáveis (prelim sob
`/prelim/`, final sob `/global_daily/`), ambos `.tif.gz` de ~3 MB. **Prelim e final permanecem
arquivados** (não é produto *rolling*) desde 2015: o timestamp do diretório corrobora a latência
(prelim de 15/01/2024 datado 17/01; final 15/02) e confirma que o vintage é reconstruível nesse
período. A pasta prelim **não existe em 2013**; além disso, janeiro–início de fevereiro de 2015
foi carregado em bloco em 17/02, não em baixa latência. Por isso o primeiro ano-safra completo
admitido no primário é **2015/16** (R16). **A revisão foi
medida**: prelim→final de 15/01/2024 no médio-norte de MT = +0,87 mm/dia (~+23%). A ingestão
aceita **caixas lat/lon nomeadas**; as duas caixas default são somente smoke tests. O sinal
primário usa média por polígono municipal ponderada pela PAM/IBGE (D-023), não regiões
escolhidas à mão. O carimbo `avail_date` = ref + 7 dias corridos preserva `kind`
(prelim/final) como eixo de vintage.

### 1.2 NASA POWER — temperatura e demais variáveis — **fonte secundária**

| | |
|---|---|
| Endpoint | `power.larc.nasa.gov/api/temporal/daily/point` — testado, HTTP 200, sem chave |
| Parâmetros úteis | `PRECTOTCORR`, `T2M`, `T2M_MAX`, `T2M_MIN`, `GWETROOT` (umidade da zona de raízes), `EVPTRNS` |
| Latência **medida** | **3 dias** (meteorologia); 5 dias (solar) |
| Grade | **0.5° × 0.625°** (~55 × 68 km) — grosseiro para município, aceitável para mesorregião |
| Rate limit | NÃO CONFIRMADO numericamente (a doc menciona HTTP 429). Tratar como sem garantia ⇒ **cache local agressivo obrigatório** |
| **Vintage** | 🔴 **NÃO preserva. Sobrescreve o passado.** |

**O problema, confirmado empiricamente.** Lendo o campo `header.sources` da própria resposta
da API, em consultas a períodos diferentes:

| Período consultado (hoje) | Fonte retornada |
|---|---|
| 2020, 2025, jan-mar/2026 | `MERRA2` (definitivo) |
| abr-mai/2026 | `MERRA2` + **`FLASHFLUX`** (solar provisório) |
| jun-jul/2026 | **`GEOSIT`** + `FLASHFLUX` (tudo provisório) |

A documentação confirma: *"o GEOS-IT é anexado ao fim da série MERRA-2 para dar produtos de
baixa latência... os valores MERRA-2 na série resultante são tipicamente atualizados a cada
alguns meses"*. Ou seja: **os últimos ~2 meses de dado são provisórios e serão substituídos.**
A POWER **não oferece vintages** — não há como pedir "o valor como publicado em 15/03".

**Consequência prática**: usar POWER como fonte principal significaria backtest com lookahead
embutido e não removível. Por isso ela é **secundária**, restrita à **temperatura** (estresse
térmico, geada), onde não achamos alternativa gratuita com vintage.

**Limitação declarada**: a componente de temperatura do sinal **permanece contaminada por
revisão**, em magnitude que precisamos medir. Se for material, restringimos o sinal à
precipitação (CHIRPS).

**Ingestão implementada e verificada ao vivo (2026-07-16, `ingest/power.py`, D-019).** Endpoint
`temporal/daily/point`, JSON, HTTP 200, sem chave, ~0,9 s/consulta; `fill_value = -999.0` (→
`NaN`, nunca tratado como temperatura); unidades °C; `header.api.version` versiona a API; a
resposta snapa para a célula da grade e devolve `geometry.coordinates` (`[lon, lat, elev]`).
**A proveniência de vintage é carimbada por resposta** via `header.sources`, confirmado ao vivo:
fetch de 2015 → `['MERRA2', 'POWER']` (definitivo); fetch de jun/2026 → `['GEOSIT', 'POWER']`
(provisório). Como a fonte sobrescreve o passado (não há consulta *as-of*), o módulo baixa por
ponto nomeado — centroides das mesmas regiões do CHIRPS, para casar `region` entre chuva e
temperatura — com **cache por captura datada** (rate limit não garantido) e grava sources +
classificação no manifesto. Escopo restrito à temperatura (`T2M`/`T2M_MAX`/`T2M_MIN`); carimbo
`avail_date` = ref + 3 dias corridos. A limitação de revisão fica declarada e mensurável (a
coluna `source_vintage` no painel permite quantificá-la na suíte de robustez).

### 1.3 ERA5 / ERA5T (Copernicus) — alternativa avaliada e preterida

Latência de 5 dias (ERA5T preliminar), mas **o ERA5T é sobrescrito pelo ERA5 final 2-3 meses
depois**, e o CDS **não guarda vintages**. Mesmo problema da POWER, com o custo adicional de
exigir registro, chave e download assíncrono em fila. **Sem vantagem sobre CHIRPS+POWER.**

### 1.4 INMET — estações de superfície — avaliado e preterido

- A API pública (`apitempo.inmet.gov.br`) **bloqueia requisição sem User-Agent de browser**, e a
  rota de série histórica por estação **retorna HTTP 204 (vazio)** — os dados de estação
  passaram a exigir token. A "API aberta" não serve mais série.
- Caminho gratuito que funciona: ZIPs anuais em `portal.inmet.gov.br/uploads/dadoshistoricos/{ANO}.zip`
  (testados: 2000, 2010, 2019, 2020, 2023, 2026 — todos HTTP 200).
- 🔴 **Problema decisivo — qualidade das estações justamente onde importa**: contagem de
  estações automáticas operantes vs. em pane: **BA 17 operantes / 28 em pane (62% quebradas)**,
  MT 45/17, RS 76/22, PR 17/9. A Bahia — ou seja, o MATOPIBA — é a pior.

> **O trade-off, explicitamente**: estação de superfície não é revisada, mas tem buraco.
> Reanálise não tem buraco, mas é revisada. Não existe fonte gratuita sem um dos dois
> defeitos. Escolhemos conviver com a revisão (medindo-a) em vez de com o buraco, porque
> buraco sistemático justamente na região produtora é pior — e é enviesado, não aleatório.

### 1.5 ONI — El Niño / La Niña — controle obrigatório

Índice sazonal público da NOAA/CPC, atualizado mensalmente. É a média móvel de três meses
da anomalia ERSST.v5 na região Niño 3.4, com períodos-base centrados de 30 anos atualizados a
cada cinco anos. Entra como **controle** nas regressões e na *spanning regression*, porque é o
confundidor macro mais óbvio da tese (`06_CRITICA_ADVERSARIAL.md` §4).

**Fonte oficial**: `https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt`. O arquivo traz
`SEAS`, `YR`, temperatura total e anomalia. A temporada é datada pelo mês central: `DJF 2025`
vira `ref_date = 31/01/2025`. A página oficial é atualizada até o dia 5; como DJF só termina
em fevereiro, sua primeira publicação é 05/03.

🔴 **Não preserva vintage.** A NOAA avisa que o filtro de alta frequência pode alterar os
valores por até dois meses depois da primeira publicação; a atualização quinquenal do
período-base pode reescrever o histórico mais antigo. Não existe consulta *as-of*. D-021 adota
captura datada + hash e, no caso primário, `avail_date` no dia 5 quatro meses após o mês
central: primeira publicação (dois meses) + janela declarada de estabilização (dois meses).
Isso reduz a revisão recente, mas não recria o vintage histórico — limitação mantida.

Em 2026 a NOAA passou a usar o **RONI** no monitoramento operacional, mas continua atualizando
o ONI. Como o pré-registro nomeia ONI, ele permanece como controle primário; RONI poderá entrar
como robustez, nunca como substituição silenciosa.

---

## 2. Safra — CONAB

**O achado mais valioso do levantamento de dados.** Arquivos CSV diretos (sem scraping, sem
API), delimitados por `;`, encoding latin-1, em `portaldeinformacoes.conab.gov.br/downloads/arquivos/`:

| Arquivo | Conteúdo |
|---|---|
| `SerieHistoricaGraos.txt` | Série longa **desde 1976/77**, por UF/produto/safra. **Só o valor final** |
| `LevantamentoGraos.txt` | 🔑 **Painel de vintages** — traz `id_levantamento` (1º ao 12º) |
| `LevantamentoCafe.txt`, `LevantamentoCana.txt` | idem, café e cana (cana traz ATR, açúcar, etanol) |

### 2.1 Por que o painel de vintages muda o projeto

`LevantamentoGraos.txt` guarda **cada uma das 12 estimativas** que a CONAB publicou ao longo
da safra. Isso é um vintage **verdadeiro**, com data de publicação conhecida — coisa que
nenhuma das fontes climáticas oferece.

Soja, Mato Grosso (mil t):

| Safra | 1º Lev. | 4º | 6º | 12º | Revisão |
|---|---|---|---|---|---|
| **2023/24** (seca) | 44.348 | 40.200 | 37.568 | 40.420 | **−15% do 1º ao 6º** |
| **2022/23** (boa) | 41.146 | 42.534 | 43.903 | 46.906 | **+14%** |

Milho 2ª safra MT 2024/25: 4º Lev. = 45.487 → 12º = 54.493 (**+20%**).

Revisões dessa magnitude são materiais. E dão à tese um **elo intermediário datável**
(ver `01_TESE_E_PRE_REGISTRO.md` §3.3): *o choque climático prevê a revisão que a CONAB vai
publicar?*

### 2.2 Limitações da CONAB, declaradas

| Limitação | Impacto |
|---|---|
| 🔴 **O painel de vintages só começa em 2017/18** (~9 safras) | Limita severamente o poder estatístico desta camada. A série longa (1976/77) só tem o número final |
| ✅ **O arquivo NÃO traz a data de publicação de cada levantamento** — só o número (1-12) | **Resolvido (R10, D-017)**: mapa `(ano_agricola, id_levantamento) → data` curado ano a ano de fontes primárias em `ingest/conab_calendar.py` — grãos 2017/18→2025/26 completo, café 2017→2026, cana 2017/18→2026/27. Ver §2.3 |
| 🟡 Granularidade **por UF**, não município | Aceitável: a grade meteorológica (~55 km) também não sustenta resolução municipal |
| 🟡 **O TXT do portal atrasa dias em relação ao boletim** | Verificado ao vivo: 10º lev de grãos 2025/26 divulgado em 14/07/2026, mas em 16/07 o `LevantamentoGraos.txt` ainda só continha até o 9º. O número é público na data do boletim (é ela o `avail_date`); o TXT é só o canal de captura, e o manifesto prova qual vintage baixamos |

### 2.3 Fatos do arquivo e do calendário (verificados em 2026-07-16)

- **Formatos de `ano_agricola` em grãos**: "2017/18" (safra de verão) e "2018" (ano civil —
  culturas de inverno: trigo, aveia, cevada...). O alinhamento dos levantamentos de inverno
  com o calendário de boletins é **ambíguo** (as revisões de trigo não casam com um único
  ano-boletim) ⇒ inverno fica **fora do calendário** e o carimbo falha alto se aparecer.
  A tese não usa culturas de inverno.
- **`id_levantamento == 99` ("LEVANT")**: resíduo legado sem número (algodão 2017/18–2021/22,
  café 2017, cana ≤2020/21). Não é datável; o parser preserva, o calendário não cobre.
- **Café 2020 não tem 2º levantamento** (suspenso na pandemia) — ausente do painel e da
  página da CONAB da época. Buraco real da fonte, não do mapa.
- **Armadilha de vintage no próprio site da CONAB**: o listing atual (gov.br) mostra, para a
  safra 2022/23 de grãos, datas nominais falsas (todas "dia 10", incluindo sábados) — artefato
  da migração de site de nov/2023. As datas verdadeiras (K2 da página antiga + calendário
  oficial, 12/12 concordantes) diferem em até 6 dias. **Nunca confiar num "Publicado em" sem
  checar se o item é nativo da era do site.**
- **Fontes do mapa** (detalhe em `ingest/conab_calendar.py`): PDFs oficiais do "Calendário de
  Divulgação de Safras" 2017 e 2021-2023 (Wayback); página Joomla antiga com data de publicação
  por item (snapshots 2018-2023); espelho same-day da AMPA (timestamp no nome do arquivo,
  validado 7/7 contra datas conhecidas); timestamps de upload do site antigo da CONAB; notícias
  datadas do dia (Agência Brasil, MAPA, novacana, udop, Cecafé, ConabCast). Regra: data efetiva
  > planejada; irresolvido → a mais tardia (atrasar sinal nunca cria lookahead).
- **Divergências reais planejado × efetivo já observadas** (por que "nunca interpolar"):
  4º lev grãos 2023/24 (04→10/jan), 1º lev cana 2021/22 (29/abr→18/mai), 3º lev cana 2022/23
  (22→27/dez). O calendário planejado sozinho **não** é confiável.

**Para peso espacial por município**: IBGE **SIDRA** (PAM, tabela 1612), API pública sem
chave, testada e funcional. É anual e divulgada no ano seguinte, portanto não gera o choque;
entra apenas como máscara/peso espacial point-in-time (D-023). A implementação deve usar o ano
mais recente cuja data oficial de divulgação seja conhecida em `t`, salvar captura + manifesto
e reconhecer que a PAM revisa anos antigos. Para milho, a PAM municipal não separa 1ª e 2ª
safra — limitação explícita do peso espacial.

---

## 3. Comércio exterior — ComexStat / Secex-MDIC

### 3.1 API — confirmada e funcional

`POST https://api-comexstat.mdic.gov.br/general` (JSON). Retorna `metricFOB` (US$) e
`metricKG` (kg líquido). Aceita `details`: `ncm`, `country`, `state`, `via`, **`urf` (porto de
embarque)** — testado, retorna `PORTO DE SANTOS`, `PORTO DE PARANAGUÁ` etc.

> ⚠️ **Bug silencioso confirmado**: NCM com zero à esquerda precisa ser passado **como
> string**. `"values":[9011110]` (int) retorna lista **vazia com `success: true`** — falha sem
> erro. `"values":["09011110"]` funciona. Isso afeta café (0901) e carnes (0201/0202/0207) —
> metade das NCMs da tese. **Guardrail obrigatório na camada de ingestão.**

**Endpoint de vintage**: `GET /general/dates/updated` informa o último mês disponível.

**Ingestão implementada e verificada ao vivo (2026-07-16, `ingest/comexstat.py`, D-020).** Schema
do `POST /general` confirmado: corpo JSON (`flow`, `period.from/to` em "AAAA-MM", `filters` por
`ncm`, `details`, `metrics`), resposta `{"data":{"list":[...]},"success":true}` com `coNcm`,
`year`, `monthNumber`, `metricFOB` (US$) e `metricKG` (kg) — **as métricas vêm como string**,
convertidas para int na ingestão. O **gotcha do NCM foi reconfirmado**: café `"09011110"` (string)
= 2 linhas; `9011110` (int) = 0 linhas com `success:true`. O guardrail `_validate_ncms` (string de
8 dígitos, senão erro alto) bloqueia isso antes da rede. O `dates/updated` (verificado:
`updated=2026-07-03`, último mês `2026-06`) vai para o manifesto como prova de vintage — a fonte
sobrescreve o passado, então cada captura é datada no nome (um vintage por captura). 🔴 **Rate
limit observado ao vivo**: consultas seguidas retornaram **HTTP 429 Too Many Requests** — o
ComexStat também limita requisição, o que reforça a decisão de cache local agressivo (não rebaixa
se o arquivo do dia já existe).

### 3.2 Calendário de publicação — confirmado

Divulgação consolidada nos **primeiros dias úteis do mês seguinte** (dia 3 a 7). A leitura ao
vivo da API bateu exatamente com o cronograma oficial. **Latência: ~3-5 dias úteis.**

### 3.3 🔴 Revisão retroativa — confirmada no manual oficial

> *"nas divulgações consolidadas, todos os meses do ano corrente podem sofrer alterações em
> valores e volumes já divulgados"* — congelamento definitivo só em **fevereiro do ano
> seguinte**.

**Não existe API "as-of"** — a base serve apenas o vintage mais recente. Mesma classe de
problema da reanálise climática. Mitigação: usar o dado como **confirmação de baixa
frequência** (não como gatilho de alta frequência), e quantificar a magnitude da revisão
comparando um snapshot antigo (Wayback) contra o atual.

### 3.4 🔴 Balança semanal — existe, mas é **inutilizável** para backtest

Havia a expectativa de que o dado semanal do MDIC desse frequência semanal ao sinal
(latência de ~1 dia, com produto detalhado: soja, café, milho, açúcar, celulose, carnes).
**Ele existe, mas não serve**, e é importante registrar por quê:

- O arquivo fica numa **URL fixa, sobrescrita toda semana**. Não há arquivo histórico.
- O manual do MDIC declara: *"dados semanais **não são armazenados**"* e *"os dados
  consolidados mensais **não podem ser obtidos pela simples soma** dos relatórios semanais"*.
- O Wayback Machine tem **~9 snapshots** desde 2022 — não reconstrói série alguma.
- Os dados são **acumulados month-to-date** (não semana isolada) e fortemente revisados
  semana a semana.

**Decisão**: a camada de confirmação opera em **frequência mensal**. O dado semanal entra no
relatório como *"o que passaríamos a coletar em produção"* (próximo passo), não como base do
backtest. Coletar a partir de hoje renderia ~5 observações até a entrega — inútil.

### 3.5 NCMs verificados (contra a tabela oficial)

A API exige **8 dígitos**. Códigos de 4 dígitos não funcionam como filtro.

| Produto | NCM |
|---|---|
| Soja em grão | `12019000` |
| Farelo de soja | `23040010` + `23040090` |
| Óleo de soja | `15071000` (bruto), `15079011` |
| Milho | `10059010` |
| Açúcar | `17011400` (VHP — o grande) + `17019900` |
| Café | `09011110` + `09011190` |
| Carne bovina | `02013000` + `02023000` |
| Frango | `02071200` + `02071400` |
| Celulose | `47032900` (eucalipto) |
| Algodão | `52010010` + `52010020` |

### 3.6 Bases brutas (alternativa à API)

CSVs anuais **1997-2026**: `balanca.economia.gov.br/balanca/bd/comexstat-bd/ncm/EXP_{ANO}.csv`
(EXP_2025 = 113 MB). Colunas incluem `CO_NCM`, `CO_URF` (porto), `CO_VIA`, `KG_LIQUIDO`, `VL_FOB`.

⚠️ O arquivo por **município** (`EXP_{ANO}_MUN.csv`) só tem **SH4 (4 dígitos)** e **não tem
porto**. Não dá para cruzar e obter município × NCM × porto simultaneamente.

### 3.7 ANTAQ — avaliada e **despriorizada**

Mensal, **latência ~40 dias**. O ComexStat já entrega porto (URF) por NCM com latência de
3-5 dias úteis. **A ANTAQ é estritamente pior e não adiciona informação ao sinal.**
(Isso reverte a expectativa inicial de usá-la como camada de granularidade — a camada de
confirmação portuária já vem de graça no ComexStat.)

---

## 4. Preços de ações — o problema mais grave, e sua solução

### 4.1 🔴 O universo agro da B3 mudou radicalmente em 2025

| Ticker | Status |
|---|---|
| **JBSS3** | ❌ Deslistado em 06/06/2025. Virou BDR `JBSS32`; JBS N.V. agora lista na NYSE |
| **BRFS3** + **MRFG3** | ❌ Deixaram de existir — fusão BRF+Marfrig → **`MBRF3`** |
| **STBP3** | ❌ Deslistado em 03/10/2025 (OPA da CMA CGM) |

**Isso não é viés de sobrevivência hipotético — já está mordendo.** Hoje, via yfinance, você
**literalmente não consegue baixar** o histórico de JBSS3, BRFS3, MRFG3 e STBP3: o Yahoo apaga
tickers deslistados. E esses eram justamente **o lado "processador" da tese** — o lado short
do par.

Um backtest montado com a lista de tickers de hoje excluiria automaticamente as empresas que
morreram, num setor em que **três dos maiores nomes sumiram nos últimos 12 meses**.

### 4.2 ✅ A solução: COTAHIST (série histórica oficial da B3)

Arquivos anuais com **todos os papéis negociados naquele ano** — incluindo os que deslistaram
depois. Delisting-proof **por construção**, porque é um registro do pregão, não uma lista de
empresas vivas.

```
https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_A{ANO}.ZIP
```
Testado: 2015 (14 MB), 2021 (50 MB), 2025 (89 MB) — todos HTTP 200, gratuitos, sem chave.

| Papel | Fonte |
|---|---|
| **Universo point-in-time** (quem existia e era líquido em `t`) | **COTAHIST** — obrigatório |
| **Liquidez (ADTV)** para o filtro | COTAHIST (volume por papel/dia) |
| Preços de empresas vivas | COTAHIST; yfinance como conferência cruzada |
| Preços de empresas **mortas** | **Só COTAHIST** — não há alternativa gratuita |

⚠️ **Pendência conhecida**: o COTAHIST traz preços **não ajustados por proventos** (dividendos,
splits, bonificações). Construir a série de retorno total exige aplicar fatores de ajuste.
É trabalho real e é o principal item técnico em aberto da camada de ingestão (risco R5).

#### 4.2.1 Fonte de proventos — verificada ao vivo (2026-07-15)

Duas fontes gratuitas testadas ao vivo. Nenhuma sozinha resolve; a decisão (D-013) é usar as
duas com papéis distintos.

| Critério | **B3 oficial** (`GetListedCashDividends`) | **StatusInvest** (`companytickerprovents`) |
|---|---|---|
| Acesso | API JSON (payload base64, por `tradingName`) | API JSON, por ticker |
| `avail_date` (deliberação) | ✅ `dateApproval` — **vintage-safe** | ❌ só data-com (`ed`) e pagamento (`pd`) |
| Preço de referência pré-ex | ✅ `closingPricePriorExDate` + `lastDatePriorEx` | ❌ |
| Cobre **deslistados** | ❌ **BRF e Santos Brasil = 0 registros; JBS congela em 2019** | ✅ JBSS3 com eventos até 05/2025 |
| Tipos cobertos | só **dinheiro** (dividendo/JCP) | só **dinheiro** (Dividendo/JCP/Amortização — confirmado na resposta) |

**Cross-check (o que legitima usar a StatusInvest na cauda deslistada):** onde as duas se
sobrepõem (SLC), os **valores batem** e o `ed` da StatusInvest **é exatamente** o
`lastDatePriorEx` (data-com) da B3 — logo o preço ajusta no **pregão seguinte** ao `ed`.

**Gotcha de vintage confirmado — e resolvido na própria fonte:** em evento pré-split, a
StatusInvest **reescreve** o valor por ação para a base pós-split (campo `adj`), enquanto a B3
mantém o nominal da época (ex.: dividendo SLC de 04/05/2023 — B3 `2,596`, StatusInvest `1,299` =
metade, por um desdobramento posterior). Misturar valores ajustados e nominais corromperia o
fator. A calibração ao vivo (2026-07-16) encontrou porém um campo não documentado, **`sov`**,
que preserva o **valor nominal original**: quando `adj=True`, o nominal está em `sov`; quando
`adj=False`, `sov` vem como `"-"` e `v` já é nominal. A regra `nominal = sov se adj senão v`
está implementada em `ingest/events_statusinvest.py` e travada por teste, inclusive um
**cross-check contra a B3** na sobreposição (SLC): 8/8 registros batem, 7 exatos e 1 com desvio
de 3,9e-4 (a StatusInvest reconstrói o nominal multiplicando o valor ajustado pelo fator do
split, com arredondamento — tolerância de comparação: 5e-4).

**Cobertura da cauda deslistada, confirmada ao vivo (2026-07-16)**: JBSS3 = 22 eventos (11 deles
pós-2019, exatamente o trecho que a B3 congela); BRFS3 = 22 (até 09/2025); STBP3 = 50 (até
03/2025). JCP vem **bruto**, consistente com o `valueCash` da B3 — as fontes podem ser somadas
sem ajuste de base. ⚠️ BRFS3 traz evento com data-com **posterior** à incorporação pela Marfrig;
o motor de retorno já ignora eventos além do fim da série de preços, mas o montador deve conferir
que a data de deslistagem via COTAHIST corta esses resíduos.

**Eventos em ações** (split/bonificação/grupamento/subscrição/incorporação): endpoint
`GetListedSupplementCompany` (por código de empresa), campos `approvedOn` (deliberação),
`factor`, `label` e `subscriptions`. Cobre inclusive os **eventos terminais dos deslistados**
(BRFS→incorporação na Marfrig, JBSS incorporação, STBP resgate — todos 2025), úteis para
encerrar a posição short corretamente. 🔴 **Truncamento CONFIRMADO com omissão material**
(2026-07-16): o endpoint **não lista a bonificação de 10% da SLC de 05/2023** (AGO/E de
27/04/2023, ex 09/05/2023) — só o desdobramento de 12/2023 e a bonificação de 12/2025. A
StatusInvest também não a tem (todos os `chartProventsType` testados). O buraco foi pego pelo
cross-check contra o *adjclose* do Yahoo (divergência de 9,1% num dia) e corrigido via registro
curado com proveniência (`ingest/events_manual.py`) — processo formalizado em **D-016**: todo
papel vivo passa por `scripts/crosscheck_yahoo.py` antes de o dataset ser congelado; papéis
deslistados não têm Yahoo e ficam com a limitação declarada. O `cashDividends` dele é só um
resumo; o histórico completo de dinheiro segue no `GetListedCashDividends`.

### 4.3 🔴 O trade-off que define o escopo do projeto: histórico × universo

**Primeira barra disponível**, por grupo econômico:

| Papel na tese | Ticker | 1ª barra |
|---|---|---|
| **Produtor** | SLCE3 | 2007-06 |
| | AGRO3 | 2006-05 |
| | SOJA3 | 🔴 **2021-04** |
| **Processador** (lado short) | BEEF3 | 2007-07 |
| | MRFG3 / BRFS3 / JBSS3 | 2007 — **hoje deslistados** |
| **Sucroenergético** | SMTO3 | 2007-02 |
| | CSAN3 | 2005-12 |
| | JALL3 / RAIZ4 | 🔴 **2021** |
| **Insumos** | TTEN3 / VITT3 / AGXY3 | 🔴 **2021** |
| **Celulose** | SUZB3 | 2004-08 |
| | KLBN11 | 2014-01 |
| **Logística** | RAIL3 | 2015-04 |
| | HBSA3 | 🔴 2020-09 |
| **Adjacentes** (compram insumo agrícola) | KEPL3 | 2000-11 |
| | MDIA3 | 2006-11 |
| | CAML3 | 2017-09 |

> 🔴 **Todos os "agros puros" (SOJA3, TTEN3, VITT3, JALL3, RAIZ4, AGXY3) são pós-2021.**
> Um cross-section rico de agro puro dá **~5 anos / ~60 observações mensais** — e essa janela
> contém COVID, o pico de commodities de 21/22 e o bear market de grãos de 23/24. Um Sharpe
> bonito aí é quase certamente sorte.

**Como resolvemos**: o backtest **primário** é o de **histórico longo** (2008-2025), e o
universo é ampliado para **~14 nomes** incluindo os *adjacentes* — empresas que compram
insumo agrícola (MDIA3 compra trigo; KEPL3 vende silos; CAML3 processa arroz) e que, pela
lógica da tese, têm exposição líquida **negativa** bem definida. Isso recupera o lado short
sem depender dos IPOs de 2021, e dá 18 anos de histórico.

O universo amplo pós-2021 vira o **backtest secundário**, com a limitação declarada.

---

## 5. Preços de commodities

### 5.1 Futuros internacionais (yfinance) — confirmados

`ZS=F` soja (2000-11), `ZM=F` farelo, `ZL=F` óleo, `ZC=F` milho, `SB=F` açúcar, `KC=F` café,
`CT=F` algodão, `LE=F` boi (CME), `BRL=X` USDBRL (2003-12). Todos testados.

⚠️ **Três armadilhas confirmadas**:
1. São séries **contínuas de front-month, NÃO ajustadas por roll** ⇒ retorno acumulado tem
   saltos artificiais no roll. Usar com cuidado (nível/momentum sim; retorno composto não).
2. **Unidades misturadas**: a maioria é **USX (cents)**, mas `ZM=F` é **USD**. Misturar sem
   normalizar gera erro silencioso.
3. `LE=F` é boi gordo **do CME (EUA)** — **não** é o boi brasileiro. Para a tese, o análogo
   correto é o indicador CEPEA/B3.

### 5.2 CEPEA/ESALQ — indicadores spot brasileiros

É a fonte-padrão gratuita de preço **brasileiro** (soja, milho, boi, café, açúcar, algodão),
diária, histórico longo, licença CC BY-NC. Conceitualmente **melhor que o futuro de Chicago**
para esta tese, porque é o preço que a empresa brasileira efetivamente realiza.

⚠️ **NÃO CONFIRMADO**: endpoint programático estável. A consulta é via web/planilha por
produto. **Item pendente de verificação** — se não houver acesso automatizável, usamos os
futuros internacionais e declaramos a aproximação.

### 5.3 Futuros da B3 (BGI boi, CCM milho, ICF café, SJC soja)

🔴 **NÃO CONFIRMADO.** As "Séries Históricas" gratuitas da B3 (COTAHIST) cobrem o **segmento
de ações**; os derivativos BM&F não estão lá. Não foi possível confirmar download histórico
longo e gratuito. **Item em aberto.**

### 5.4 Fatores de risco brasileiros — NEFIN/FEA-USP

Fatores Mercado, SMB, HML, WML, IML (iliquidez), públicos e gratuitos. Usados na *spanning
regression* (H4) — é o padrão acadêmico brasileiro, e evita improvisar fatores caseiros.

**Fonte oficial**: `https://nefin.com.br/resources/risk_factors/nefin_factors.csv`, servida
pelo repositório público `nefin/nefin.github.io`. O arquivo tem retornos **diários em decimal**
desde 02/01/2001, nas colunas `Rm_minus_Rf`, `SMB`, `HML`, `WML`, `IML` e `Risk_Free`.

🔴 **Frequência do dado ≠ frequência de publicação.** O site informa atualizações
periódicas, mas publica o histórico inteiro em lote. Na captura de 16/07/2026, o último pregão
era 02/06 e o commit que publicou o snapshot era de 19/06. Não existe evidência para assumir
`avail_date = ref_date + 1`.

🔴 **Revisão retroativa material, medida.** O repositório oficial preserva dois commits do
CSV desde a migração do site. Comparando 01/06/2026 (6.218 linhas até 02/02) com 19/06/2026
(6.299 linhas até 02/06), na sobreposição:
- HML mudou acima de `1e-10` em **4.484/6.218** datas e mais de 1 bp em **3.889**;
- maior revisão absoluta do HML: **2,759 p.p.** (05/11/2001);
- WML mudou mais de 1 bp em 21 datas; `Risk_Free` não mudou.

D-022 baixa o arquivo pela URL *raw* presa ao SHA do commit, não pela branch mutável, e
grava SHA, timestamp, hash e cobertura no manifesto. Todas as linhas recebem `avail_date`
igual à data do snapshot. Isso é conservador e coerente com seu papel: NEFIN entra na H4 como
**atribuição ex post**, depois que os retornos ocorreram; nunca alimenta o sinal ou a carteira.

---

## 6. Resumo: latência e vintage por fonte

| Fonte | Latência | Preserva vintage? | Papel |
|---|---|---|---|
| **CHIRPS** | ~2 dias | ✅ **sim** (prelim + final) | 🥇 clima primário (precipitação) |
| NASA POWER | 3 dias | 🔴 não (sobrescreve ~2 meses) | clima secundário (temperatura) |
| ERA5/ERA5T | 5 dias | 🔴 não | preterida |
| INMET | ~1 dia | ~ (não revisa, mas tem buracos) | preterida (62% das estações da BA em pane) |
| **CONAB levantamentos** | mensal, ~dia 15 | ✅ **sim** (painel 1º-12º lev.) | 🥇 elo causal intermediário |
| **ComexStat** | 3-5 dias úteis | 🔴 não (revisa até fev do ano seguinte) | camada de confirmação (mensal) |
| ComexStat semanal | ~1 dia | 🔴 **não arquiva** | ❌ inutilizável para backtest |
| ANTAQ | ~40 dias | — | ❌ despriorizada (pior que ComexStat) |
| **COTAHIST (B3)** | D+1 | ✅ (registro de pregão) | 🥇 preços + universo point-in-time |
| yfinance | D+1 | 🔴 **apaga deslistados** | só conferência cruzada |
| Futuros (yfinance) | D+1 | ✅ | preço de commodity |
| ONI (NOAA) | até dia 5; caso primário espera +2 meses | 🔴 não (revisão recente + base quinquenal) | controle (El Niño) |
| NEFIN | diário, publicado em lotes irregulares | parcial (commits desde jun/2026; revisão histórica material) | fatores ex post (H4) |

---

## 7. Itens em aberto (a resolver antes de codar a ingestão)

1. ✅ **Ajuste de proventos no COTAHIST** — **resolvido** (R5). Três fontes de eventos + motor
   de retorno total + **montador** (`prices/assemble`, D-015) + **cross-check contra o Yahoo
   por papel vivo** (D-016) — que já pegou e corrigiu uma bonificação de 10% ausente de todas
   as fontes (§4.2.1). Pendência aberta: rodar o cross-check nos demais nomes vivos do universo
   antes de congelar o dataset; deslistados ficam com a limitação declarada em D-016.
2. ✅ **Mapa `(safra, nº do levantamento) → data de divulgação` da CONAB** — **resolvido**
   (R10, D-017): curado ano a ano de fontes primárias em `ingest/conab_calendar.py`, com a
   proveniência de cada safra anotada no módulo. Ver §2.3 — inclusive a armadilha encontrada
   (o site oficial exibe datas falsas para 2022/23).
3. **Acesso programático ao CEPEA** — se não existir, usar futuros internacionais e declarar.
4. **Futuros agro da B3** — confirmar se há histórico gratuito, ou abandonar.
5. **Magnitude da revisão do ComexStat** nas NCMs agro — quantificar via snapshot do Wayback
   vs. dado atual.
6. ✅ **Especificação fenológica e regional do `Shock`** — **congelada** em D-023, sem
   consultar retornos: soja + milho 2ª, UFs fixas, chuva CHIRPS, janelas por cultura × UF e
   geografia PAM/IBGE. O CSV oficial do ZARC foi testado. Falta implementar a ingestão PIT da
   PAM e as geometrias municipais antes de calcular C2.
