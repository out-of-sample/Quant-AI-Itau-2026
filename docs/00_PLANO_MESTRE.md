# Plano mestre

Ponto de entrada da documentação do projeto. Leia este primeiro; ele diz o que é o projeto,
como ele está organizado e em que ordem as coisas acontecem.

---

## 1. O projeto em um parágrafo

Choques climáticos nas regiões produtoras brasileiras carregam informação sobre a oferta
futura de commodities agrícolas. Essa informação chega ao preço das ações da B3 **com
defasagem e de forma heterogênea entre empresas** — porque uma seca é *boa* para quem vende
a commodity (o preço sobe) e *ruim* para quem a compra como insumo (a margem cai). A
estratégia explora essa heterogeneidade com uma carteira **market-neutral long/short dentro
do próprio setor agro**: comprada em produtores, vendida em processadores, dimensionada pela
exposição líquida de cada empresa a cada commodity.

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

### Fase 1 — Ingestão e point-in-time (em andamento)
Trazer as fontes, carimbar `avail_date`, montar o universo dinâmico via COTAHIST.
Resolver as pendências de `02_DADOS.md` §7 (ajuste de proventos, calendário CONAB).

Andamento (2026-07-16), toda peça com teste e CI verde (ver `03_ARQUITETURA.md` §6):
- ✅ Fundação de engenharia (empacotamento, lockfile com hashes, CI, guards de lookahead/segredo).
- ✅ Fontes de proventos verificadas ao vivo e decididas (D-013): B3 oficial + StatusInvest.
- ✅ Motor de **retorno total point-in-time** (D-014), sem *adjusted close* retroativo.
- ✅ Parser + download do **COTAHIST** (offsets validados em arquivo real, delisting-proof).
- ✅ Fetchers de eventos da **B3**: dinheiro (dividendo/JCP) e ações (split/bonificação/
  grupamento, `factor` validado contra preço).
- ✅ Fetcher da **StatusInvest** (dividendos da cauda deslistada; nominal via campo `sov`,
  cross-check 8/8 contra a B3 na sobreposição).
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
- ⬜ Ingestão das demais fontes da tese: ComexStat, ONI, NEFIN — cada uma com carimbo de
  `avail_date` na entrada.

> **Portão (lado preços): ATRAVESSADO em 2026-07-16.** A série de preços delisting-aware e
> ajustada por proventos existe, é testada e foi validada contra fonte independente. O
> restante da Fase 1 é a ingestão das fontes de sinal (clima/safra/exportação).

### Fase 2 — Validação do mecanismo (o portão mais importante)
Testar **H1a**: o choque climático prevê a revisão da CONAB? E **H1b**: prevê o volume
exportado? Com BH-FDR e erros agrupados por ano-safra.

> **Portão**: se o clima **não** prevê a revisão de safra nem a exportação, o mecanismo
> econômico postulado é falso. Nesse caso **paramos e reformulamos**, em vez de seguir para o
> backtest e descobrir um alfa que seria coincidência. Um achado negativo aqui, documentado
> com honestidade, ainda é um bom trabalho — e é infinitamente melhor do que um Sharpe bonito
> construído sobre um mecanismo inexistente.

### Fase 3 — Sinal e carteira
Matriz de exposição `E`, score, gate de confirmação, construção da carteira. Calibração
**exclusivamente** em 2013-2019.

### Fase 4 — Backtest
Backtest A (núcleo histórico, primário) e B (universo amplo, secundário). Custos, capacidade,
atribuição.

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
