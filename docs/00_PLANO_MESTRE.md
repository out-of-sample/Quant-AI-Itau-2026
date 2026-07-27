# Plano mestre

Ponto de entrada da documentação do projeto. Leia este primeiro; ele diz o que é o projeto,
como ele está organizado e em que ordem as coisas acontecem.

---

## 1. O projeto em um parágrafo

Choques climáticos nas regiões produtoras brasileiras carregam informação sobre a oferta
futura de commodities agrícolas. O mecanismo físico foi confirmado para soja e milho: o
`Shock` antecipa revisões para baixo da CONAB. A tradução financeira originalmente proposta —
comprar produtores e vender processadores —, porém, **falhou no desenvolvimento**: o canal de
preço não teve suporte e a reação das ações veio no sentido contrário. O projeto foi então
reformulado, com registro completo, para testar a hipótese nova e pré-registrada de que o dano
de volume próprio domina o benefício de preço (`Q>P`). O holdout de retornos 2020–2025 continua
lacrado. A estratégia reformulada foi **congelada antes do holdout** em D-053; ainda não foi
avaliada fora da amostra nem pode ser chamada de aprovada empiricamente. D-072 fechou o pacote
técnico e o preflight, mas a rodada única ainda depende de uma autorização civil posterior.

O elo causal é testado em etapas, não assumido:

```
choque climático  →  revisão CONAB  →  preço da commodity  →  ação
   (CHIRPS)             ✅ H1              ❌ H2              ❌ direção original
                            ↑
             ComexStat corroborou soja ex post
```

---

## 2. Por que a tese não é o óbvio

A leitura ingênua original seria "detectou seca ⇒ vende agro". O desenho econômico postulou
que uma quebra brasileira, como choque de oferta global, elevaria o preço e criaria dois
efeitos opostos no produtor: menos volume e preço maior. Os testes D-037–D-041, porém, **não
deram suporte estatístico ao canal de preço**, e D-043 mostrou que o dano de volume dominou
nos produtores da amostra.

A hipótese reformulada ainda busca **dispersão dentro do setor**, mas não presume ganhadores:
cada canal de cultura precisa primeiro passar sua validação física e depois ser congelado antes
do holdout. O mecanismo plausível não é tratado como evidência já demonstrada.

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

### Fase 3 — Sinal e carteira ✅
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
  teste de ações, **não** inversão post-hoc. Anti-p-hacking: dev queimado para a direção, holdout
  = tiro único, disclosure total. Corroboração independente = a **cadeia lógica** (H1+D-041 ⇒
  receita↓); o teste de fundamentos foi **rebaixado a ilustração** (N≈4, uma empresa, dado sujo).
- 📐 **Análise de poder (D-045)**: expandir compra **conclusividade**, não lucro. Holdout tem 5
  anos-safra fixos ⇒ o único ajuste é nº de nomes. Se o efeito for grande (o do dev), conclusivo
  já com 4 nomes; se moderado, ~8 nomes chegam a ~80-90%; se minúsculo, inconclusivo mesmo
  expandido. `scripts/power_analysis.py`.
- 🌱 **Desenho da expansão (D-046)**: canais de cultura sob H′, direções derivadas do mecanismo.
  Algodão (limpo, reforça AGRO3/SLCE3, +evento, 0 nomes novos); cana (mecanismo **invertido**,
  sub-modelo à parte, +SMTO3/JALL3); café sem veículo (limitação declarada).

**Fechamento das subfases da Fase 3:**
- ✅ **3.4 — construir os canais de cultura**: contratos de choque congelados (molde D-023) e
  validação H1 por cultura, sem tocar retorno.
  - ✅ **algodão — contrato congelado** (D-047): MT+BA, janela floração/capulho, fonte ZARC/Embrapa
    (`COTTON_WINDOWS`, travado em teste).
  - ❌ **algodão — não corroborado e excluído (D-048/D-049)**: PAM municipal 2689 e revisão da pluma
    CONAB em 2022/23–2024/25. O β agrupado foi **+0,042**, contrário ao esperado; BA, MT, as
    três safras e as três estimativas *leave-one-safra-out* também foram positivas. O critério
    congelado exigia β<0 e ao menos 2/3 LOO<0; o algodão fica fora do score.
  - ✅ **cana — mecanismo físico corroborado, com ressalva** (D-050/D-051): maturação
    jun–ago→ATR passou a regra direcional (β `+0,0134`, 8/8 LOO e 5/5 UFs positivas), mas sem
    significância (p `0,12`; bootstrap `0,27`). Crescimento→tonelagem veio negativo e fraco.
  - ✅ **cana — auditoria PIT dos veículos (D-052)**: SMTO3 e JALL3 têm geografia dentro do choque
    e cana majoritária/própria; o canal ATR é de quantidade e sobrevive ao hedge de preço.
    **SMTO3 entra no score com haircut** (30% terceiros, hedge, Boa Vista/GO só etanol); **JALL3
    fica fora** por IPO fev/2021 (holdout-only, sem dev). Universo scoreado = **5 nomes** (4 grãos
    + SMTO3). Registro em `data/reference/cane_corporate_audit_v1.json`; ATR≠receita segue como
    ressalva aberta (R24).
- ✅ **3.5 — estratégia reformulada congelada** (D-053, anterior ao holdout): contrato em
  `src/quantagro/backtest/strategy_spec.py`. Universo = 5 nomes; direção H′ (grãos = negativo de
  `E·Shock`; cana = maturação +1). **A1**: teste primário só nos 4 grãos (spread produtor–
  processador) para proteger a força; SMTO3 na carteira negociável capada em 0,15. **B1**: sizing
  proporcional ao sinal, dollar-neutral, cap 0,40 por grão. Pesos CONAB (D-028); execução D+1;
  horizonte 21 pregões. Teste primário = painel `Shock×exposição`, cluster por ano-safra,
  permutação, unilateral α=0,10 (substitui H3/Fama–MacBeth). **R19 resolvido**.

> **Portão da Fase 3: ATRAVESSADO em 2026-07-20 (D-053).** Hipótese H′, universo, direção,
> sizing, caps, execução e teste primário foram congelados antes do holdout. Isso autoriza a
> construção da máquina, não a abertura do holdout.

### Fase 4 — Backtest

Construir e validar a máquina no desenvolvimento, sem usar seu P&L para confirmar H′ ou ajustar
o desenho. O antigo Backtest B amplo deixa de ser promessa; só pode existir como robustez
identificada se surgir exposição direta admissível.

Andamento:
- ✅ **4.0 — contrato operacional fechado sem P&L (D-054/D-055):** grade de blocos não
  sobrepostos de 21 pregões, score multicanal, política sem produtor/processador, permutação
  exata de 32 estados, ADTV/custos/aluguel/capacidade, fronteiras e bloqueio do holdout estão
  executáveis em `backtest/operational_spec.py`. A safra 2019/20 foi excluída para não cruzar o
  lacre civil; o defeito de water-filling da auditoria também foi corrigido e testado.
- ✅ **4.1 — motor vetorizado (D-056):** adaptadores PIT materializam grãos/cana e posições-
  alvo; o ledger mantém quantidades fixas, executa `(X, saída]`, reconcilia P&L bruto/líquido,
  custos e turnover e bloqueia o holdout antes do I/O. Testes sintéticos cobrem transição,
  drift, saída final e custos. **Nenhum P&L de carteira/backtest foi rodado.** R26 limita o smoke test real
  a 2018/19, porque as safras anteriores não têm peso CONAB anterior admissível.
- ✅ **4.2 — fricções e investibilidade (D-057/D-058):** retorno total offline dos cinco nomes e
  estado real COTAHIST/ADTV foram materializados; o parser/fetcher das duas tabelas BDI, o
  carimbo PIT e o gate de aluguel por patrimônio corrente estão implementados. O piso congelado
  exclui AGRO3 em todo o dev; SLCE3 preserva o lado produtor nos nove blocos de 2018/19. **Fork
  R27 resolvido pela opção 2 (D-058):** confirmado que não há série histórica pública (só o
  último pregão) e que a opção 1 gratuita é inviável, o custo do short passa a ser **proxy
  conservadora declarada** (piso 5%+tarifas+2×, disponibilidade por ADTV), corroborada pelo único
  snapshot real — não medição de investibilidade histórica. Isso **destrava o smoke** (sujeito a
  R26). Cobertura e nove pontos de decisão congelados em
  `data/reference/market_state_dev_summary_v1.json`; evidência de calibração em
  `data/reference/borrow_rate_calibration_v1.json`.
- ✅ **Smoke de engenharia (D-059, `scripts/run_smoke_dev.py`):** motor rodou ponta a ponta no
  dev 2018/19 com dados reais nos três cenários — dollar-neutral (máx |Σw|=0), caps respeitados,
  custos zero<base<2×, patrimônio finito>0, holdout bloqueado. **Achado:** SMTO3 é holdout-only na
  prática (sem peso CONAB de cana de 2017/18), então o dev é só grãos (SLCE3 short × BRFS3/JBSS3
  long). **O P&L do dev (+36% base) é circular e NÃO valida a estratégia** — a direção H′ foi
  derivada deste mesmo dev; só o holdout (Fase 6) valida.
- ✅ **4.3 — diagnósticos no dev (D-060, `backtest/diagnostics.py`, `scripts/run_diagnostics_dev.py`):**
  descritivos, holdout lacrado. Atribuição por nome: **JBSS3 sozinho responde por 54,6% do P&L
  bruto** e a perna long de proteína (JBS+BRF) por 86,3%; SLCE3 short 13,7%; HHI 0,42 (muito
  concentrado). Decomposição setor-vs-clima: a carteira real (+36,26%) e a carteira **setorial
  ingênua** (short produtor/long processador equal-weight, +36,26%) são idênticas — **incremento
  de clima = +0,00%**; regressão no spread proteína−produtor dá **R²=0,84**. **Conclusão dura:** no
  dev o livro É uma aposta de setor, não um sinal cross-section de clima — o +36% é o rali de
  proteína de 2019 (ASF), não alpha climático. Isso não muda o contrato congelado; alimenta a Fase
  5 (robustez) e o que o relatório precisa declarar sobre exposição setorial.

> **Portão mecânico 4.1: ATRAVESSADO em 2026-07-20 (D-056). Portão 4.2: ATRAVESSADO em 2026-07-20
> (D-058). Smoke de engenharia: ATRAVESSADO em 2026-07-20 (D-059). Diagnósticos 4.3: CONCLUÍDOS em
> 2026-07-20 (D-060).** A infraestrutura mensurável foi concluída e validada ponta a ponta sem abrir
> o holdout. A condição short de D-055 não é reconstruível em 2018/19 com dados públicos; em vez de
> P&L com zeros ou proxies silenciosos, o fork de D-057 foi resolvido por uma proxy conservadora
> **declarada e sinalizada** (reason `proxy`). Os diagnósticos 4.3 mostraram que o P&L do dev é uma
> aposta setorial (incremento de clima ~0), reforçando que só o holdout valida. O holdout segue
> lacrado até a Fase 6, e o P&L do dev nunca é tratado como validação.

### Fase 5 — Robustez

Atualizar e pré-registrar a suíte para H′; executar H4/H5, placebo, lag/vintage, custos,
subperíodos e leave-one-out na ordem de poder de falsificação. O H3 original já foi substituído
pelo teste primário D-053 e H2a já produziu achado negativo.

Andamento:
- ✅ **Reconstrução da matriz de exposição sob H′ (D-061, 2026-07-24)**: uma investigação
  return-agnóstica (choques sintéticos, sem retorno) achou que a matriz de **preço** D-033 dava
  exposição **idêntica** aos dois processadores ⇒ a carteira colapsava em **dois estados**
  dependentes só do sinal do choque, um bit-idêntico à setorial ingênua (a identidade que zerou o
  `climate_increment` de D-060). `E` nunca fora re-derivada para H′ (D-053 herdou a de preço). D-061
  re-deriva a materialidade sob o critério de quantidade/geografia, das fontes primárias já
  auditadas em D-035 (AGRO3 1,0→0,50; JBSS3 0,50→0,25), em `data/reference/exposure_hprime_v1.json`
  (v1 preservado). A carteira passa a **8 estados** com inclinação long entre processadores conforme
  a cultura estressada. Não muda o contrato de estratégia/operacional, só o artefato de exposição.
  Limites declarados em D-061: magnitude do choque ainda descartada, produtor ainda fino no dev,
  canal do processador ainda de preço.
- ✅ **Auditoria das estruturas de monetização de H1 (D-062, 2026-07-24)**: avaliou, return-agnóstico e
  com base acadêmica, se um veículo melhor-casado com o nowcast de produção existiria — logística de
  grão (Rumo) e spread soja–milho. **Rumo rejeitada**: apesar de ~75% grão e 42% de MT, é
  **limitada por capacidade** ⇒ volume insensível à revisão marginal (dilui o sinal). **Spread
  rejeitado**: canal de preço morto (H2a + Silveira 2025 JFM), mercado CBOT eficiente (contradiz a
  tese de ineficiência brasileira), trade clássico, motor do zero. **Decisão: reter a estratégia de
  ações do D-061**; nenhum veículo novo entra; a divergência soja–milho vira evidência de apoio no
  relatório; a auditoria inteira vira ativo de rigor. Verdade estrutural declarada: não há veículo
  brasileiro líquido com sensibilidade limpa a um nowcast de produção marginal (confirma R1/R7).
- ✅ **Correção do canal Rumo e enumeração estruturada (D-063, 2026-07-26)**: em resposta à cobrança
  de exaustividade, (1) afiou a rejeição da Rumo — sob capacidade travada o sinal migra do volume para
  o **frete/margem**, canal abafado por take-or-pay, de sinal ambíguo/perverso, regulado e não-estabelecido
  (conclusão inalterada, motivo mais preciso); (2) **mapeou** o espaço inteiro de veículos (ferrovia,
  porto STBP3, hidrovia HBSA3, caminhão, spread, basis Brasil−Chicago, crush, insumos) contra os cinco
  filtros — todo transporte herda o gargalo de capacidade exceto a hidrovia, que é holdout-only; todo
  veículo de preço esbarra no canal morto/CBOT; (3) abriu o **hedge de setor** como o thread de "arrumar
  o que temos" (isolar o resíduo climático do beta de setor confirmado no D-060), a ser pré-registrado
  return-agnóstico (futuro D-064). Busca por veículo alternativo **encerrada e mapeada**.
- 🟡 **Pré-registro da suíte de robustez do sinal H1 (D-065, 2026-07-26)**: congela em
  `stats/robustness_spec.py`, **antes de rodar**, o grid single-knob (climatologia ±2 anos, fonte
  final×prelim, lag +14d, janela crítica ±15d) e dois placebos (espacial e temporal), com critérios
  executáveis (banda |β|/|β_base| ∈ [0,4; 2,5]; placebo morre se |β|<0,5× e p>0,10) e veredito global.
  Return-agnóstico (mecanismo H1a, não retornos); mede **estabilidade de desenho**, não poder. Só
  informativo agora porque o D-061 desfez a degeneração da carteira. Runner e números vêm no próximo
  passo. Testes 497→508.
- 🟡 **Suíte de robustez do sinal H1 executada (D-066, 2026-07-26)**: baseline reproduz o portão
  (β=−0,0672, p<0,001, N=729, 8 safras). **Robustez direcional forte**: as 4 perturbações reais
  rodáveis preservaram sinal e magnitude (climatologia +2 = 0,97×; lag +14d = 1,02×; janela +15d =
  0,76×; **fonte `final` fortalece** = 1,37×); placebo **temporal morreu limpo** (p=0,42). **Achado
  central**: o placebo **espacial não morreu de todo** — embaralhar UFs destrói ~69% do β (maioria é
  regional) mas sobra ~31% significativo (p=0,019) ⇒ **componente nacional-comum forte** (caracteriza,
  não falsifica H1; casa com D-060/D-061/D-063). Dois botões não rodaram por piso de dado (climatologia
  −2 = série final começa em 2000; janela −15 = painel só cobre Dez–Mai), declarados. **Veredito global
  pré-registrado = NÃO ROBUSTO**, reportado fielmente (reprova por 4<5 reais rodáveis + placebo espacial
  significativo; **nenhum é fragilidade direcional**). O gate estrito falhar e ser reportado é o próprio
  entregável de rigor. Motor de Shock intocado; `signal_lag_days` só na chave de cache. Testes 508→519.
- ✅ **Ramo AGRO3×ADTV pré-registrado (D-067, 2026-07-26)**: o piso primário permanece
  ADTV21 ≥R$8 milhões e a elegibilidade é resolvida separadamente em cada decisão `D`, sem
  classificação retroativa da safra e sem escolher carteira pelo P&L. O motor agora expõe
  elegibilidade/atividade da AGRO3 e profundidade ativa de produtores/processadores; a auditoria
  return-agnóstica congela os estados `never_eligible`/`intermittent`/`always_eligible`. Se a
  perna produtora continuar com um nome, nenhum resultado positivo autoriza alegar dispersão
  cross-sectional entre produtores. Subgrupos são descritivos; não criam novos testes. O
  holdout continua lacrado. Testes 519→523.
- ✅ **Pacote indivisível do holdout congelado até o preflight (D-068, 2026-07-26)**:
  `backtest/holdout_spec.py` fixa a ordem dos 12 blocos, o único teste confirmatório H′,
  H4/H5 como vetos, grids descritivos, níveis de afirmação e caminhos dos sete inputs.
  `backtest/holdout.py` e `scripts/run_holdout_once.py` atestam fontes por SHA-256 e listam
  ausências **sem abrir os parquets**. A execução permanece desabilitada e falha antes do
  I/O: ainda faltam controles diários confiáveis de H4, o sinal geográfico não produtor de
  H5 e o executor atômico/registro civil. A auditoria também retirou promessas antigas
  incompatíveis com D-053–D-067. Holdout intocado; testes 523→530.
- ✅ **Painel diário H4 materializado e congelado (D-069, 2026-07-26)**:
  `ingest/h4_market.py` captura câmbio diário DEXBZUS e os ETFs futuros SOYB/CORN/CANE;
  `robustness/h4_controls.py` alinha tudo ao calendário NEFIN/B3 sem backfill e carrega o
  último ONI estabilizado disponível. São **1.495 sessões** (02/01/2020–30/12/2025), zero
  ausências/duplicatas, snapshot 27/07/2026 e parquet reproduzido com o mesmo SHA-256.
  Manifestos e `h4_controls_summary_v1.json` prendem as seis fontes e as transformações.
  O preflight agora reconhece `h4_controls`; H4 **ainda não foi estimado**, pois o desfecho
  são os retornos lacrados. Hash lógico atualizado de forma pré-holdout em D-069; testes
  530→540.
- ✅ **Geografia e scores placebo H5 congelados (D-070/D-071, 2026-07-26)**:
  um primeiro commit fixou, antes do cálculo climático, 91 células em cinco municípios
  costeiros BA/PR com **110 observações PAM completas e produção zero** de soja/milho em
  2014–2024. O segundo materializou 46 decisões H5 nos cinco anos-safra, usando os mesmos
  6.197 raster-dias CHIRPS, janelas, climatologia, pesos CONAB e exposições do sinal real.
  Fontes/partes/output estão presos por hash; rebuild reproduziu SHA-256
  `936bee66…32e1`. O preflight reconhece H4 e H5, mas o veto H5 **não foi estimado** porque
  exige retornos lacrados. Hash lógico daquela etapa `cb125fea…912b`; testes 540→549.
- ✅ **Executor e inputs da rodada única fechados (D-072, 2026-07-26)**:
  os seis parquets derivados cobrem 1.495 sessões e todas as agendas/lags congelados; manifesto
  local e resumo versionado prendem inputs e fontes por SHA-256. O executor cria o registro
  irreversível antes de abrir parquets, calcula obrigatoriamente os blocos 0–10, faz `fsync` e
  publica os 12 artefatos por rename atômico. Qualquer falha consome a tentativa; alteração em
  fonte/input bloqueia o preflight. O gate seguro está `ready=true`, mas `--execute` sem a frase
  civil exata falha antes do I/O. **Nenhum P&L, H′, H4 ou H5 foi calculado.** Hash lógico vigente
  `f97093b9…3f9e`; manifesto de fontes `cb73c893…090d`; manifesto de inputs
  `d31091cb…b43d`; suíte 549→564 testes. A auditoria return-agnóstica também detectou dois blocos que cruzam
  deslistagens em 2025; a regra PIT agora liquida o bloco inteiro no último close oficial,
  sem seguir JBSS32/MBRF3 nem trocar o universo.
- ✅ **Hedge de setor como decomposição pré-registrada (D-064, 2026-07-26)**: dado que o D-060 mostrou
  o P&L do dev dominado por aposta de setor, o time escolheu (entre 3 formas) que o hedge entra como
  **regra de decomposição do primário**, não como estratégia nova nem mudança do contrato congelado.
  `diagnostics.py::sector_orthogonal_decomposition` congela uma separação aditiva/exata do bruto do
  livro em parte de setor (projeção nos pesos setoriais ingênuos) e resíduo climático ortogonal — **só
  pesos, sem retornos** (return-agnóstica). Na Fase 6 explica o resultado do holdout (quanto é clima ×
  setor) sem gastar α extra nem multiplicar a família de testes; no dev roda descritiva/circular
  (Bloco C′). Não muda a estratégia negociada. Testes 492→497.

- ✅ **Benchmark das edições anteriores (D-073, 2026-07-27)**: comparação return-agnóstica com 8
  relatórios, 11 repositórios e as fontes oficiais de 2020–2025, em
  `docs/15_BENCHMARK_ANOS_ANTERIORES.md`. Nenhuma alteração de contrato, estratégia ou input.
  Confirmou que estamos acima de todo o acervo em point-in-time, holdout lacrado, pré-registro,
  custo de aluguel, CI e placebos — nenhum dos 11 repositórios tem integração contínua e só um
  tem testes. Identificou **seis lacunas técnicas reais**, das quais quatro exigem pré-registro
  anterior à rodada: métricas por ano-safra, estatísticas descritivas de risco, benchmark de
  performance declarado e correção pelo número de especificações testadas. A quinta (validar o
  mecanismo contra um segundo estimador oficial de safra) atacaria o componente nacional-comum
  de D-066, mas depende de fonte ainda não validada. Limitação declarada: nenhum relatório do
  acervo é de projeto campeão.

### Fase 6 — Holdout

O bloqueio técnico foi fechado em D-072. Antes da autorização, D-073 abriu quatro pré-registros
pendentes (`docs/15_BENCHMARK_ANOS_ANTERIORES.md` §8, itens 2–5) que perdem valor se escritos
depois de vermos o resultado. O passo seguinte é uma decisão humana exclusiva:
autorizar deliberadamente e rodar a especificação congelada em 2020–2025 **uma vez**. Nenhuma
correção posterior; todos os blocos rodam sem pausa e o resultado vai para o relatório,
qualquer que seja. `ready=true` não equivale a autorização civil.

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
