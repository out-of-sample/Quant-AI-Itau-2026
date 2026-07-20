# Plano mestre

Ponto de entrada da documentação do projeto. Leia este primeiro; ele diz o que é o projeto,
como ele está organizado e em que ordem as coisas acontecem.

---

## 1. O projeto em um parágrafo

Choques climáticos nas regiões produtoras brasileiras carregam informação sobre a oferta
futura de commodities agrícolas. Essa informação chega ao preço das ações da B3 **com
defasagem e de forma heterogênea entre empresas** — porque uma seca pode elevar o preço para
quem vende a commodity, reduzir o volume do produtor atingido e encarecer o insumo de quem a
compra. A
estratégia pretende explorar essa heterogeneidade com uma carteira **dollar-neutral
long/short dentro do próprio setor agro**: comprada em produtores, vendida em processadores,
dimensionada pela exposição líquida de cada empresa a cada commodity. Neutralidade em reais
não implica neutralidade a mercado, fatores ou commodities; essas exposições precisam ser
medidas e testadas explicitamente.

O elo causal é testado em etapas, não assumido:

```
choque climático  →  revisão da estimativa de safra da CONAB  →  preço da commodity  →  ação
   (CHIRPS)            (painel de vintages, data conhecida)        (futuro/CEPEA)      (B3)
                                        ↑
                    confirmação independente: volume exportado (ComexStat)
```

---

## 2. Por que a tese não é o óbvio

A leitura ingênua seria "detectou seca ⇒ vende agro". **Isso está errado.** O Brasil é um dos
maiores exportadores mundiais dessas commodities, então uma quebra de safra brasileira é um
**choque de oferta global** e *empurra o preço para cima*. O produtor tem dois efeitos de
sinais opostos (vende menos, a preço maior); o frigorífico, que compra milho e farelo para
ração, só tem o efeito ruim.

O alfa, portanto, não está em prever a direção do setor — está na **dispersão dentro dele**.
Um índice setorial agregado mistura ganhadores e perdedores e cancela o efeito, que é
justamente por que essa informação pode continuar não-arbitrada.

**A ineficiência explorada é de agregação, não de acesso**: o dado é público e gratuito; caro
é cruzar grade meteorológica × mapa de produção agrícola × composição de receita e custo das
empresas.

Detalhes em `01_TESE_E_PRE_REGISTRO.md` §2.

---

## 3. Mapa da documentação

| Documento | O que responde |
|---|---|
| **`01_TESE_E_PRE_REGISTRO.md`** | Qual é a hipótese, formalizada. **Quais testes a falsificam** — pré-registrados, com critério de falha declarado antes de rodar |
| **`02_DADOS.md`** | Que dados existem, com que latência, e **quais deles reescrevem o passado** (o problema do *vintage*). Tudo testado ao vivo |
| **`03_ARQUITETURA.md`** | Como o pipeline é organizado em camadas e qual invariante cada uma garante |
| **`04_PROTOCOLO_BACKTEST.md`** | Regras de execução, custos, universo dinâmico, disciplina do holdout |
| **`05_SUITE_ROBUSTEZ.md`** | Todos os testes de robustez, **com o resultado esperado declarado antes** |
| **`06_CRITICA_ADVERSARIAL.md`** | O projeto atacado por um avaliador hostil. Onde a defesa é fraca, está escrito que é fraca |
| **`07_RISCOS_E_DECISOES.md`** | Riscos vivos + **log de todas as decisões de desenho, com data** |
| **`08_IDENTIDADE.md`** | Nome e identidade visual da estratégia |
| **`09_FENOLOGIA_E_LIMIARES.md`** | Quando o clima importa, por cultura e estado — janelas e limiares agronômicos |
| **`10_REFERENCIAS.md`** | Referências acadêmicas, métodos e fontes de dados usados, com proveniência e lacunas marcadas |
| **`11_AUDITORIA_FASE1.md`** | Evidências do fechamento da ingestão: cross-check dos preços, decisões sobre preços de commodities e limite de vintage do ComexStat |
| **`12_PENDENCIAS_TRANSVERSAIS.md`** | Fonte única das dívidas legadas/transversais que não pertencem a uma fase futura |
| **`13_MATRIZ_EXPOSICAO.md`** | Regra, fontes e registro point-in-time da matriz fundamentalista empresa × cultura |
| **`14_AUDITORIA_CANAIS_EMPRESARIAIS.md`** | Portão econômico entre a matriz PIT e a carteira: efeito-preço, volume próprio, insumo, geografia, hedge e redesenho de H2/H3 |
| **`DIARIO_GENAI.md`** | Registro contínuo do uso de IA generativa no processo |
| `../CONTRIBUTING.md` | Branches, commits, PRs, checklist de revisão |
| `../05_Ideacao_Tese/` | As 21 teses avaliadas e por que esta foi escolhida |

---

## 4. Fases do projeto

O projeto é sequencial de propósito: **cada fase tem um portão que a seguinte não pode
atravessar sem passar.** A ideia é falhar cedo e barato, não descobrir no fim que a premissa
era falsa.

### Fase 0 — Planejamento e pré-registro ✅
Tese formalizada, hipóteses e critérios de falsificação congelados, dados verificados ao
vivo, arquitetura especificada, riscos mapeados. **Nada disso depende de escrever código.**

### Fase 1 — Ingestão e point-in-time ✅
Trazer as fontes, carimbar `avail_date`, montar o universo dinâmico via COTAHIST.
Resolver as pendências de `02_DADOS.md` §7 (ajuste de proventos, calendário CONAB).

Andamento (2026-07-16), toda peça com teste e CI verde (ver `03_ARQUITETURA.md` §6):
- ✅ Fundação de engenharia (empacotamento, lockfile com hashes, CI, guards de lookahead/segredo).
- ✅ Fontes de proventos verificadas ao vivo e decididas (D-013): B3 oficial + StatusInvest.
- ✅ Motor de **retorno total point-in-time** (D-014), sem *adjusted close* retroativo.
- ✅ Parser + download do **COTAHIST** (offsets validados em arquivo real, delisting-proof).
- ✅ Fetchers de eventos da **B3**: dinheiro (dividendo/JCP) e ações (split/bonificação/
  grupamento, `factor` validado contra preço).
- ✅ Fetcher da **StatusInvest** (cauda deslistada ou histórico B3 vazio; nominal via campo
  `sov`, cross-check 8/8 contra a B3 na sobreposição; parcelas iguais legítimas preservadas).
- ✅ **Montador** (D-015): COTAHIST + eventos → retorno total por papel, delisting-aware;
  validado contra o split real da SLC e a deslistagem da JBS; tripwire de split perdido.
- ✅ Carimbo de `avail_date` (C1, `validate/pit.py`) e **universo dinâmico** com filtro de
  liquidez (`validate/universe.py`) — validado em 2025 real: JBSS3 sai em 06/06, BRFS3/MRFG3
  em 22/09 (fusão), STBP3 em 02/10, e MBRF3 *entra* em dezembro ao completar o seasoning.
- ✅ **Cross-check contra fonte ajustada independente** (D-016): pegou uma bonificação de 10%
  da SLC (05/2023) ausente de **todas** as fontes automáticas — corrigida via registro curado
  com proveniência (`ingest/events_manual.py`); validação repetível em
  `scripts/crosscheck_yahoo.py`, obrigatória por papel vivo antes de congelar o dataset.
- ✅ **Ingestão CONAB** (`ingest/conab.py`): download com manifesto de vintage (a fonte
  reescreve o arquivo no lugar ⇒ captura datada + hash), parser dos painéis de grãos, café e
  cana, validado ao vivo contra os números conhecidos (soja/MT 2023/24: 44.348 → 37.568).
- ✅ **Calendário CONAB (R10, D-017)**: mapa curado `(ano_agricola, id_levantamento) → data de
  divulgação` em `ingest/conab_calendar.py`, ano a ano de fontes primárias, sem interpolação;
  carimbo `avail_date` integrado ao contrato PIT (`attach_avail_date` + `available_asof`).
  A verificação pegou o site oficial exibindo datas falsas para 2022/23 — ver D-017.
- ✅ **Ingestão CHIRPS (clima primário, D-018)** (`ingest/chirps.py`): precipitação diária com
  vintage real — `prelim` e `final` arquivados separadamente pela fonte, baixados com manifesto
  (hash) e agregados em caixas lat/lon nomeadas por região produtora. GeoTIFF lido sem GDAL
  (`tifffile`, Python puro). Verificado ao vivo: a revisão prelim→final de 15/01/2024 no
  médio-norte de MT foi +0,87 mm/dia (~+23%) — a contaminação que a fonte com vintage existe
  para medir. Carimbo `avail_date` = ref + 7 dias corridos (lag congelado, `01_TESE §5`).
- ✅ **Ingestão NASA POWER (clima secundário, D-019)** (`ingest/power.py`): temperatura
  (`T2M`/`T2M_MAX`/`T2M_MIN`) por ponto nomeado — centroides das mesmas regiões do CHIRPS, para
  casar `region`. A fonte **não preserva vintage**, então o módulo classifica a proveniência de
  cada captura via `header.sources` (`MERRA2` = definitivo; `GEOSIT`/`FLASHFLUX` = provisório,
  verificado ao vivo) e grava no manifesto — a limitação é declarada e mensurável, não ignorada.
  Carimbo `avail_date` = ref + 3 dias corridos (latência meteorológica medida).
- ✅ **Ingestão ComexStat (confirmação por comércio exterior, D-020)** (`ingest/comexstat.py`):
  `POST /general` por NCM, com o **guardrail obrigatório** contra o gotcha do NCM — a API exige
  string de 8 dígitos; int (que perde o zero à esquerda) retorna vazio com `success:true`, e
  `_validate_ncms` falha alto antes da rede. Não preserva vintage (revisa até fev do ano seguinte)
  ⇒ o manifesto grava o `dates/updated` como prova de vintage; uso como confirmação mensal.
  Carimbo `avail_date` = ref (fim do mês) + lag (divulgação no início do mês seguinte).
- ✅ **Ingestão ONI (controle ENSO, D-021)** (`ingest/oni.py`): arquivo oficial NOAA/CPC,
  parser da temporada trimestral centrada, captura datada + manifesto e carimbo conservador.
  A NOAA publica até o dia 5 e pode revisar os dois valores mensais seguintes; o caso primário
  só disponibiliza o valor após essa janela. A fonte não arquiva vintages, limitação declarada.
- ✅ **Ingestão NEFIN (fatores de risco de H4, D-022)** (`ingest/nefin.py`): fatores diários
  presos ao SHA do commit oficial, manifesto e carimbo pelo snapshot. A comparação de dois
  vintages provou revisão histórica material do HML; por isso os fatores são controles de
  atribuição **ex post**, nunca informação para gerar posição.
- ✅ **Especificação fenológica/regional congelada (D-023)** (`features/shock_spec.py`): sem
  consultar retornos, o primário foi limitado a soja + milho 2ª safra, chuva CHIRPS, UFs que
  cobrem mais de 80% da produção, janelas cultura × UF e climatologia expanding. As caixas
  climáticas de ingestão ficaram como smoke tests; a geografia final usa PAM/IBGE→UF→CONAB.
  A auditoria de cobertura fixou o início em 2015/16: o CHIRPS prelim não existe antes (R16).
- ✅ **Ingestão PIT da PAM/IBGE e geometrias municipais (D-024)**
  (`ingest/pam.py`, `pam_calendar.py`, `ibge_geometry.py`): tabela SIDRA 1612 com calendário
  efetivo 2014–2024, captura datada e pesos *as-of*; malha IBGE 2013 fixa e pré-amostra, sem
  fronteiras futuras. Símbolos `...` permanecem ausentes e são contabilizados, nunca viram
  zero. A cobertura foi validada nas 7 UFs e nos vintages usados em 2015, 2020 e 2025.
- ✅ **Auditoria de fechamento (D-025/D-026)**: os 19 papéis vivos do universo foram
  confrontados com fonte ajustada independente em 2023–2025, sem consultar retorno da
  estratégia. O teste encontrou e corrigiu bonificações ausentes de VITT3/KLBN11, repetição
  ON/PN/UNIT no endpoint B3 e parcelas legítimas iguais da KLBN11. CEPEA e futuros B3 foram
  classificados como robustez; a ausência de vintages históricos do ComexStat retirou o
  gate 1.0/0.5/0.0 do sizing primário, preservando H1b como validação física *ex post*.

> **PORTÃO DA FASE 1: ATRAVESSADO em 2026-07-16.** Preços, safra, clima, exportação,
> controles ONI/NEFIN e regionalização PAM/IBGE têm ingestão reproduzível e contrato PIT;
> as pendências metodológicas foram decididas em D-025/D-026 e auditadas em
> `11_AUDITORIA_FASE1.md`. C2 `Shock` foi concluído em D-027/D-028; o próximo artefato são
> os rodadores H1a/H1b, não um backtest.

> **Portão (lado preços): ATRAVESSADO em 2026-07-16.** A série de preços delisting-aware e
> ajustada por proventos existe, é testada e foi validada contra fonte independente. A
> auditoria integral e suas correções estão em D-025 e `11_AUDITORIA_FASE1.md`.

### Fase 2 — Validação do mecanismo (o portão mais importante)
Testar **H1a**: o choque climático prevê a revisão da CONAB? E **H1b**: prevê o volume
exportado? Com BH-FDR e erros agrupados por ano-safra.

Pré-requisito da fase: construir o C2 `Shock` (é ele que entra nas regressões) — **cumprido**.
Andamento:
- ✅ **Regionalização raster→município (D-027)** (`features/regionalize.py`): média de
  precipitação CHIRPS por polígono municipal da malha IBGE 2013, sem GDAL (ponto-em-polígono
  numpy sobre centros de célula p05). Índice município→células validado ao vivo nas 7 UFs
  (2.634/2.634 municípios); fallback auditável para os 3 municípios menores que a célula;
  polígonos de água não-municipais da malha (lagoas do RS) excluídos.
- ✅ **Cálculo do `Shock` as-of (D-028)** (`features/shock.py`): acumulado `prelim` da janela
  fenológica até a data de corte, climatologia expanding do **mesmo trecho** (produto `final`,
  ≥10 safras, cobertura diária obrigatória — buraco falha alto), `Shock = −z`; agregação
  UF (peso municipal PAM *as-of* `t`) → nacional (peso CONAB da safra **anterior** encerrada,
  nunca a corrente), renormalizada sobre janelas já iniciadas com composição visível.
  Validado com álgebra sintética conferível no papel e de ponta a ponta com dados reais.
- ✅ **Perímetro do holdout para H1 fixado (D-029, encerra PT-001)**: o lacre 2020–2025 veda a
  estratégia e seus parâmetros, não os testes de mecanismo. H1a/H1b rodam no span cheio
  2015/16–2024/25 (N efetivo ~8 e ~9 anos-safra) com sub-amostras dev/holdout reportadas em
  separado. Decidido antes de qualquer resultado de H1.
- ✅ **Pré-registro das regressões (D-030)**: variável dependente, regressor, sinal esperado,
  `climatology_first_year=2000` e família BH-FDR congelados antes de olhar qualquer coeficiente.
- ✅ **Rodadores de H1a/H1b executados uma vez (D-031)** (`stats/h1a.py`, `stats/h1b.py`,
  `stats/gate.py`, `scripts/run_gate.py`): H1a agrupado **β=−0,067**, `t(7)` p≈6e-4, bootstrap
  por cluster p≈0, sobrevive ao BH-FDR; efeito consistente no desenvolvimento (−0,057) e no
  holdout (−0,072) e nas duas culturas. H1b corrobora a soja ex post. **Portão ATRAVESSADO.**

> **Portão: ATRAVESSADO em 2026-07-17 (D-031).** O choque climático prevê a revisão da safra
> CONAB, com o sinal certo e força dentro e fora da amostra — a cadeia causal postulada existe.
> Seguimos para a Fase 3. (A regra permanece registrada: se o clima **não** previsse a revisão,
> **pararíamos e reformularíamos** em vez de caçar um alfa que seria coincidência. O achado —
> qualquer que fosse — iria para o relatório.)

### Fase 3 — Sinal e carteira
Matriz de exposição `E`, score e construção da carteira. O ComexStat valida H1b *ex post* e
não dimensiona o experimento primário (D-026). Calibração
**exclusivamente** no desenvolvimento até 2019; o `Shock` operacional começa em 2015/16
(R16), embora preços e universo preservem o recorte anterior como histórico auxiliar.

- ✅ método fundamentalista point-in-time pré-registrado antes da classificação (D-032;
  `13_MATRIZ_EXPOSICAO.md`)
- ✅ regra aplicada ao universo, matriz `E` versionada e validada (D-033; quatro nomes
  diretos, entrada PIT gradual)
- ✅ inserido o portão **Fase 3.1 — auditoria dos canais empresariais** antes de score e
  carteira (D-034; `14_AUDITORIA_CANAIS_EMPRESARIAIS.md`)
- ✅ auditoria PIT de mix, geografia, preço/insumo, hedge e perímetro dos quatro nomes
  concluída, com lacunas declaradas (D-035; `14` §9; `data/reference/corporate_audit_v1.json`)
- ✅ decisão do fork `P/Q/C`: `P`/`Q` **não são PIT-separáveis** ⇒ mantém-se a matriz D-033
  (opção 1), materialidade atenuada como sensibilidade, **long condicionado a H2a** (D-035)
- ⚠️ Família de testes de preço FECHADA (D-036–D-041, 6 medidas): transmissão do `Shock` ao
  preço não atinge significância em nenhuma (mundial nulo/errado; local BRL sinal certo mas sem
  poder). A força testada é clima→revisão CONAB (H1).
- 🛑 **Reação das ações testada (D-042/D-043, Fase 3.2): ANTI-preditiva no dev** — β=−0,09
  (t=−3,6), P&L −4%/período, correlações por nome todas negativas. A estratégia long/short pelo
  choque **perde** e o sinal é invertido: a seca **prejudica** o produtor (`Q>P`).
- 🔬 **Reformulação Q-dominante pré-registrada (D-044)**: a hipótese "a seca prejudica o produtor"
  é **derivada** de H1 (volume↓) + D-041 (preço flat) + D-035 (`Q` real) — formulável antes do
  teste de ações, **não** uma inversão post-hoc. Protocolo anti-p-hacking: dev queimado para a
  direção, holdout = tiro único, disclosure total. Corroboração independente antes do holdout:
  cadeia lógica + teste de **fundamentos** (receita/margem de grão das produtoras vs Shock).
  Próximo: construir a corroboração por fundamentos; depois congelar a estratégia; só então holdout
- ⬜ substituir o H3/Fama–MacBeth por teste compatível com apenas três a quatro ações
- ⬜ resolver R19 sem consultar retornos e construir carteira dollar-neutral, sem presumir
  neutralidade a beta, fatores ou commodities

### Fase 4 — Backtest
Backtest A (núcleo histórico, primário); B amplo permanece condicionado a evidência direta
admissível (D-033). Custos, capacidade, atribuição.

### Fase 5 — Robustez
Suíte completa. **Os três testes existenciais primeiro** (spanning, placebo, sensibilidade ao
lag), antes dos cosméticos — porque são os que podem tornar o resto irrelevante.

### Fase 6 — Holdout
Rodar em 2020-2025. **Uma vez.** O resultado vai para o relatório, qualquer que seja.

### Fase 7 — Relatório
5 páginas, 16:9, 100% anônimo. É o único entregável avaliado.

---

## 5. Como os critérios de avaliação estão endereçados

| Critério | Peso | Onde o projeto responde |
|---|---|---|
| Conceito da estratégia | 20% | A reformulação produtor-vs-processador (`01` §2): ineficiência de **agregação**, não de acesso. Economicamente correta e não-óbvia |
| Modelagem | 20% | Pipeline em 8 camadas com contrato explícito (`03`); features em 3 blocos; exposição estimada por dois métodos independentes que se cruzam |
| Backtest | 15% | Pré-registro + holdout lacrado + universo point-in-time via COTAHIST + `avail_date` em toda linha (`02`, `04`) |
| Análise dos resultados | 15% | Suíte de robustez com resultado esperado declarado antes (`05`); crítica adversarial (`06`); achados negativos reportados |
| Uso de IA generativa | 15% | `DIARIO_GENAI.md` — registro contínuo, com o que a IA acertou **e errou** |
| Conclusão e próximos passos | 10% | Limitações reais em `06`; riscos sem solução declarados como tal em `07` |
| Apresentação do robô | 5% | `08_IDENTIDADE.md` |

---

## 6. As três coisas que podem matar o projeto

Estão escritas aqui, no documento de entrada, de propósito. Um projeto que esconde os
próprios pontos de ruptura não está sendo honesto sobre o que é.

1. **N efetivo pequeno.** A safra é anual: temos poucas dezenas de eventos independentes, não
   milhares de dias. Sem poder estatístico para detectar efeito pequeno. **Não tem solução.**
2. **A estratégia pode ser só beta de commodity** (H4). Se o alfa não sobreviver à *spanning
   regression*, a estratégia é uma forma cara de comprar o futuro da soja.
3. **O sinal pode ser El Niño disfarçado** (H5). Se o alfa sobreviver ao placebo espacial, a
   narrativa agronômica está errada.

Se qualquer uma se confirmar, **reportamos**. Um trabalho que testa a própria tese com rigor e
conclui que ela não se sustenta pontua nos critérios de Backtest, Análise e Conclusão — e é
mais defensável do que um resultado bonito que não sobrevive à primeira pergunta da banca.
