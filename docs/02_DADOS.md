# Catálogo de dados, latências e regras point-in-time

> Todas as fontes abaixo foram **testadas ao vivo** (requisição real ao endpoint) entre
> 2026-07-13 e 2026-07-17. O que não foi possível confirmar está marcado como **NÃO CONFIRMADO** —
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
escolhidas à mão. O carimbo `avail_date` é **por produto** (`features/shock.py`, D-028):
`prelim` = ref + 7 dias corridos (lag primário congelado); `final` = ref + 60 dias corridos
(conservador vs. a publicação ~1 mês depois). `kind` (prelim/final) permanece como eixo de
vintage — um lag único superestimaria a disponibilidade do `final`.

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
| 🟡 O desfecho CONAB tem granularidade **por UF**, não município | O clima primário é CHIRPS p05 (~5 km), agregado primeiro por município e ponderado pela PAM (D-027/D-028). A regressão H1a continua no nível UF e não localiza fazendas individuais; isso é ruído de medida, não justificativa para usar a grade POWER de ~55 km |
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

**Para peso espacial por município (implementado, D-024)**: IBGE **SIDRA** (PAM, tabela 1612),
API pública sem chave. `ingest/pam.py` consulta nível municipal (`n6`), variável 214
(`Quantidade produzida`, toneladas), soja 2713 e milho total 2711. Cada captura recebe hash e
manifesto; o painel carrega `ref_date=31/12` e a data efetiva de divulgação de
`ingest/pam_calendar.py`. O calendário curado, sem interpolação, é:

```text
PAM ref.  2014       2015       2016       2017       2018       2019
publicada 05/11/2015 23/09/2016 21/09/2017 13/09/2018 05/09/2019 01/10/2020
PAM ref.  2020       2021       2022       2023       2024
publicada 22/09/2021 15/09/2022 14/09/2023 12/09/2024 11/09/2025
```

Em cada data `D`, `pam_weights_asof` usa somente a edição mais recente com
`avail_date ≤ D`. O símbolo SIDRA `-` é zero verdadeiro; `...` é dado não disponível e
permanece `NaN`, com contagem por cultura/UF — nunca é convertido em zero. Na captura integral
2014–2024, 130 de 38.467 linhas vieram como `...`, concentradas em municípios urbanos; os pesos
são normalizados sobre a tonelagem reportada e a incompletude fica visível no painel.

**Geometria**: `ingest/ibge_geometry.py` usa a malha municipal IBGE **edição 2013** como suporte
fixo. Seus artefatos foram gerados em 16/03/2015, antes da primeira janela operacional em
dezembro/2015. Isso evita fronteira futura e mudança mecânica de suporte ao longo do teste. O
arquivo arquivado por UF é lido com PyShp, em SIRGAS 2000, e serializado como GeoJSON compacto.
Município com produção positiva sem polígono provoca erro e exige *crosswalk* explícito.

Dois fatos da malha verificados na regionalização (2026-07-17): (i) a malha do RS traz **dois
polígonos de água não-municipais** — Lagoa Mirim (4300001) e Lagoa dos Patos (4300002), código
de município `0000` — que `features/regionalize.py` exclui do índice de células (nunca têm
produção PAM, mas contaminariam qualquer média não-ponderada); (ii) três municípios reais são
menores que a célula p05 de ~5,5 km e não contêm nenhum centro de célula (Madre de Deus/BA,
Albertina/MG, Esteio/RS) — recebem a célula mais próxima do centroide, com `cell_source`
auditável (D-027).

Limitações residuais: o SIDRA atual reescreve anos antigos, de modo que `avail_date` não
reconstrói os valores originalmente publicados; milho municipal não separa 1ª e 2ª safra; e a
malha fixa ignora refinamentos posteriores de divisa. Captura, hash, sensibilidade com peso
uniforme e declaração desses limites são a defesa — não existe vintage histórico perfeito.

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

**Não existe API "as-of"** — a base serve apenas o vintage mais recente. A tentativa de
reconstrução também falhou: o Wayback não preservou os CSVs anuais consultados nem foram
encontrados snapshots das respostas `POST` da API. Logo, a magnitude histórica da revisão
**não é identificável**.

**Consequência (D-026):** o dado final pode ser usado como variável dependente de H1b — a
realização física que o choque deveria prever —, mas não como gate histórico de posição com
`avail_date` da primeira divulgação. Isso atribuiria ao passado um vintage revisado que não
existia. Capturas datadas passam a medir revisões prospectivamente; o gate fica fora do
backtest primário.

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

**Decisão**: a camada de confirmação opera em **frequência mensal**. O dado semanal pode ser
mencionado como extensão hipotética de produção, mas está fora do experimento e **não é uma
pendência ativa**. Coletar a partir de hoje renderia ~5 observações até a entrega — inútil.

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

O COTAHIST traz preços **não ajustados por proventos**. O motor D-014, o montador D-015 e a
auditoria D-025 transformam esses preços em retorno total forward-only; R5 está encerrado com
as limitações residuais declaradas abaixo.

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
o montador ignora eventos além do fim da série de preços. Para papel vivo, a StatusInvest só
substitui a B3 se o histórico oficial de caixa vier inteiramente vazio (KLBN11); não se somam
fontes secundárias por padrão. Além disso, linhas idênticas não são deduplicadas: quatro parcelas
iguais da KLBN11 reproduzem o caixa agregado e não têm identificador que autorize colapso.

**Eventos em ações** (split/bonificação/grupamento/subscrição/incorporação): endpoint
`GetListedSupplementCompany` (por código de empresa), campos `approvedOn` (deliberação),
`factor`, `label` e `subscriptions`. Cobre inclusive os **eventos terminais dos deslistados**
(BRFS→incorporação na Marfrig, JBSS incorporação, STBP resgate — todos 2025), úteis para
encerrar a posição short corretamente. 🔴 **Truncamento CONFIRMADO com omissão material**
(2026-07-16): o endpoint **não lista a bonificação de 10% da SLC de 05/2023** (AGO/E de
27/04/2023, ex 09/05/2023) — só o desdobramento de 12/2023 e a bonificação de 12/2025. A
StatusInvest também não a tem (todos os `chartProventsType` testados). O buraco foi pego pelo
cross-check contra o *adjclose* do Yahoo (divergência de 9,1% num dia) e corrigido via registro
curado com proveniência (`ingest/events_manual.py`). A auditoria D-025 dos 19 papéis vivos
encontrou ainda bonificações omitidas de VITT3 e KLBN11 e repetição do mesmo evento KLBN para
ON/PN/UNIT; a normalização agora filtra classe pelo ISIN. Papéis deslistados não têm Yahoo e
ficam com a limitação declarada. O `cashDividends` do supplement é só resumo; o histórico
completo de dinheiro segue no `GetListedCashDividends`.

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

**Como resolvemos**: o backtest **primário** preserva o núcleo histórico de empresas, mas o
`Shock` negociável começa somente na safra **2015/16** (R16), e o
universo é ampliado para **~14 nomes** incluindo os *adjacentes* — empresas que compram
insumo agrícola (MDIA3 compra trigo; KEPL3 vende silos; CAML3 processa arroz) e que, pela
lógica da tese, têm exposição líquida **negativa** bem definida. Isso recupera o lado short
sem depender dos IPOs de 2021. Preços anteriores permanecem úteis para histórico, liquidez e
eventos corporativos, mas não fabricam anos de sinal climático point-in-time.

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

✅ **Acesso histórico confirmado, automação estável não.** O banco oficial permite escolher
produto, especificação, periodicidade e intervalo e gerar uma planilha Excel. A licença
oficial é CC BY-NC 4.0, compatível com o uso acadêmico mediante atribuição. A tentativa de
acesso HTTP direto encontrou proteção JavaScript/Cloudflare; não foi localizada API pública
documentada e reproduzível.

**Decisão:** CEPEA é validação/robustez brasileira obtida por exportação manual com arquivo e
hash preservados, não dependência da ingestão primária. Fonte:
`cepea.org.br/br/consultas-ao-banco-de-dados-do-site.aspx` e
`cepea.org.br/br/licenca-de-uso-de-dados.aspx`.

### 5.3 Futuros da B3 (BGI boi, CCM milho, ICF café, SJC soja)

✅ **Dados diários por vencimento confirmados, série contínua pronta não.** A área oficial
`Market Data > Histórico > Derivativos` publica ajustes do pregão e resumos estatísticos; as
fichas dos contratos confirmam código, unidade e vencimentos. O preço de ajuste é específico
por contrato e, em sessões sem negócio suficiente, pode ser calculado por regras de
apreçamento/interpolação da B3.

Transformar esses arquivos em retorno contínuo exige regra de rolagem declarada, controle de
vencimento e validação dos ajustes — uma camada de modelagem adicional. **Decisão:** futuros
internacionais são a fonte primária reproduzível de H2, em janelas de evento com datas de
rolagem excluídas; contratos B3 e CEPEA entram como robustez brasileira. Fonte:
`b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/`.

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
| **ComexStat** | 3-5 dias úteis | 🔴 não (revisa até fev do ano seguinte; vintages históricos irrecuperáveis) | H1b *ex post*; não entra no sizing primário |
| ComexStat semanal | ~1 dia | 🔴 **não arquiva** | ❌ inutilizável para backtest |
| ANTAQ | ~40 dias | — | ❌ despriorizada (pior que ComexStat) |
| **COTAHIST (B3)** | D+1 | ✅ (registro de pregão) | 🥇 preços + universo point-in-time |
| yfinance | D+1 | 🔴 **apaga deslistados** | só conferência cruzada |
| Futuros (yfinance) | D+1 | ✅ | preço de commodity |
| ONI (NOAA) | até dia 5; caso primário espera +2 meses | 🔴 não (revisão recente + base quinquenal) | controle (El Niño) |
| NEFIN | diário, publicado em lotes irregulares | parcial (commits desde jun/2026; revisão histórica material) | fatores ex post (H4) |

---

## 7. Checklist de fechamento da Fase 1

1. ✅ **Ajuste de proventos no COTAHIST** — **resolvido** (R5/D-025). Três fontes de eventos +
   motor de retorno total + montador + auditoria dos **19 papéis vivos** em 2023–2025. Foram
   corrigidas bonificações ausentes de SLC, VITT3 e KLBN11, repetição de classes da KLBN11 e
   preservação de parcelas de caixa legítimas. Deslistados seguem sem cross-check Yahoo.
2. ✅ **Mapa `(safra, nº do levantamento) → data de divulgação` da CONAB** — **resolvido**
   (R10, D-017): curado ano a ano de fontes primárias em `ingest/conab_calendar.py`, com a
   proveniência de cada safra anotada no módulo. Ver §2.3 — inclusive a armadilha encontrada
   (o site oficial exibe datas falsas para 2022/23).
3. ✅ **CEPEA** — planilha histórica e licença acadêmica confirmadas; sem API estável.
   Classificado como robustez manual, não dependência do pipeline (D-026).
4. ✅ **Futuros agro da B3** — ajustes diários por vencimento confirmados; exigem construção
   e validação de rolagem. Robustez, não fonte primária de H2 (D-026).
5. ✅ **Revisão do ComexStat** — magnitude histórica não reconstruível: API/CSVs só expõem o
   vintage atual e o Wayback não preservou os artefatos consultados. O gate sai do sizing;
   ComexStat fica em H1b *ex post* e os snapshots medem revisões futuras (D-026/R18).
6. ✅ **Especificação e cálculo do `Shock`** — contrato congelado em D-023, ingestão PIT da
   PAM/malha municipal em D-024, regionalização raster→município em D-027 e cálculo as-of
   município→UF→nacional em D-028, todos sem consultar retornos. A auditoria da Fase 1 foi
   fechada em D-025/D-026; os rodadores H1a/H1b são o portão da Fase 2.

Pendências que atravessam fases e não pertencem a uma camada futura são controladas em
`12_PENDENCIAS_TRANSVERSAIS.md`.
