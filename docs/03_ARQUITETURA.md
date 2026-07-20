# Arquitetura do pipeline — especificação e estado

> Este documento **especifica** o contrato de cada camada: o que recebe, o que entrega, e qual
> invariante é obrigada a garantir. Parte do pipeline já está implementada e obedece a este
> contrato — o **estado de implementação** (o que existe hoje em `src/quantagro/`) está na §6.


---

## 0. Princípio arquitetural único

> **Toda camada é uma função pura de (dados disponíveis até `t`) → (saída em `t`).**
> Nenhuma camada pode olhar para frente. Essa é a única invariante que, se quebrada,
> invalida o projeto inteiro — e é por isso que ela está codificada na estrutura do
> pipeline, não só na disciplina de quem escreve o código.

O corolário prático: cada tabela intermediária carrega **duas datas**:

| Coluna | Significado |
|---|---|
| `ref_date` | data a que o dado **se refere** (ex.: choveu no dia 10/01) |
| `avail_date` | data em que o dado **ficou disponível** para nós (ex.: 17/01, após latência da fonte) |

**Nenhuma camada a jusante pode filtrar por `ref_date`. Só por `avail_date`.**
Essa regra sozinha elimina a maior parte dos lookaheads possíveis, e é verificável
mecanicamente (um teste automatizado pode varrer o código atrás de filtros por `ref_date`).

---

## 1. As camadas

Mapeamento direto do esqueleto genérico de `05_Ideacao_Tese/pipeline_e_portfolio.md`,
agora instanciado para a tese Clima + ComexStat.

```
┌──────────────────────────────────────────────────────────────────────────┐
│ C0  INGESTÃO           fontes brutas → parquet local + manifesto         │
│     NASA POWER · CONAB · ComexStat · preços B3 · futuros · ONI · NEFIN   │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ C1  VALIDAÇÃO E CARIMBO PIT     aplica avail_date · valida schema         │
│     buracos · duplicatas · calendário de pregão · quebras de metodologia  │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ C2  FEATURES  (3 blocos, nunca uma lista solta)                          │
│     (a) Shock_{c,t}  — estresse climático ponderado por produção         │
│     (b) E_{i,c}      — matriz de exposição empresa × commodity           │
│     (c) contexto     — IBOV, USDBRL, ONI, vol, ADTV, momentum            │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ C3  TESTE DE SIGNIFICÂNCIA     ← PORTÃO. O sinal só passa se sobreviver. │
│     H1 mecanismo · H2a preço · H2b evento · H5 placebo · BH-FDR          │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ C4  SINAL → POSIÇÃO                                                      │
│     score final condicionado à auditoria P/Q/C · ComexStat = H1b ex post │
│     dollar-neutral · caps de nome e de turnover · filtro de liquidez     │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ C5  EXECUÇÃO (opcional, isolada da tese — só se sobrar tempo)            │
│     ML aqui, e SÓ aqui: nunca decide direção, só refina saída/timing     │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ C6  BACKTEST      universo dinâmico · execução D+1 · custos · benchmark  │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ C7  ROBUSTEZ      sensibilidade · placebo · spanning (H4) · subperíodos  │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ C8  INTERPRETAÇÃO E RELATÓRIO                                            │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Contrato de cada camada

### C0 — Ingestão

**Responsabilidade**: trazer o dado bruto de fora e congelá-lo em disco. Nada mais.
Não limpa, não transforma, não interpreta.

- Cada fonte tem um módulo próprio, com a **mesma interface**: baixa → salva parquet →
  escreve um **manifesto** (`data/manifests/`) com data de download, hash do conteúdo,
  parâmetros da requisição, versão/vintage da fonte.
- **Cache obrigatório**: nunca bater na API duas vezes para o mesmo pedido. As APIs
  públicas brasileiras são lentas e instáveis; um backtest que depende de rede é um
  backtest que não roda.
- **Idempotência**: rodar duas vezes produz o mesmo resultado.

> **Por que o manifesto importa**: fontes de reanálise (NASA POWER) e órgãos públicos
> (CONAB) **revisam o passado**. O manifesto é a única forma de sabermos, depois, qual
> versão do dado usamos e se ela mudou. Sem isso, o backtest não é reproduzível nem por
> nós mesmos daqui a dois meses.

### C1 — Validação e carimbo point-in-time

**Responsabilidade**: transformar dado bruto em dado *confiável e datado corretamente*.
É a camada mais importante do projeto e a mais fácil de subestimar.

Obrigações:
1. **Aplicar `avail_date`** a cada linha, segundo a regra de latência da fonte
   (`02_DADOS.md`). Aqui é onde o lookahead é morto na origem.
2. Validar schema (tipos, faixas plausíveis — precipitação negativa é erro, não dado).
3. Detectar e **registrar** buracos, duplicatas e quebras de metodologia. Nunca imputar
   silenciosamente: toda imputação é uma decisão registrada.
4. Alinhar tudo ao **calendário de pregão da B3** (não ao calendário civil — feriado
   brasileiro não é dia de trade, e o clima não para no feriado).

### C2 — Features

Organizadas em **três blocos com papéis distintos** (a taxonomia é herdada do padrão
Kairos — features em categorias, não lista ad-hoc, é o que dá estrutura ao critério
"Modelagem"):

| Bloco | O que é | Papel |
|---|---|---|
| **(a) Sinal da tese** | `Shock_{c,t}` — anomalia climática ponderada por produção, dentro da janela fenológica | é a tese |
| **(b) Exposição** | matriz empresa × commodity point-in-time | D-033 registra preço/insumo; D-034 bloqueia o score até separar preço, volume próprio, custo, geografia e hedge |
| **(c) Contexto/controle** | IBOV, USDBRL, ONI (El Niño), vol realizada, ADTV, momentum | separa o efeito da tese de movimento de mercado amplo — **sem isso não há como afirmar que é alfa** |

### C3 — Teste de significância (PORTÃO)

**Esta camada tem poder de veto.** Não é decorativa.

Roda as hipóteses `H1` (mecanismo físico), `H2a` (transmissão preditiva ao futuro da
commodity) e `H5` (placebo espacial) **antes** do backtest de retorno de ações. H2b, reação à
publicação CONAB, é diagnóstico complementar; sua nulidade isolada não veta H2a.

- Correção de múltiplas comparações (**Benjamini-Hochberg/FDR**) sobre toda a família de
  testes `(cultura × horizonte × região)` — sem isso, testando dezenas de combinações,
  alguma vai parecer significativa por puro acaso (é o rigor que o KernelNet aplicou e que
  separa um projeto sério de um bonito).
- Inferência robusta a autocorrelação: **Newey-West** + **block bootstrap** (o sinal
  climático é fortemente persistente; t-stat ingênuo mente).

> **Se H1 falhar**, o mecanismo econômico postulado é falso. Nesse caso **não fingimos que
> nada aconteceu**: o achado negativo vai para o relatório e a tese é reformulada
> explicitamente (padrão Kairos, que documentou uma hipótese falsificada e o pivô — e foi
> premiado por isso).

### C4 — Sinal → posição

Converte o score contínuo em uma carteira observável e replicável.

- `S_{i,t} = Σ_c E_{i,c} · Shock_{c,t}` (ver `01_TESE_E_PRE_REGISTRO.md` §3)
- ComexStat **não entra no sizing primário**: valida H1b *ex post*. O gate histórico foi
  removido em D-026 porque a fonte não preserva o vintage da primeira publicação
- **Sizing proporcional à convicção**, não binário
- **Dollar-neutral** long/short — consequência direta da tese (produtores vs. processadores)
- Filtro de liquidez (ADTV mínimo), cap por nome, cap de turnover

### C5 — Execução (opcional)

Existe para deixar claro **onde ML pode entrar sem contaminar a tese**: só para refinar
saída/timing, nunca para escolher direção. É a última prioridade do projeto e pode
simplesmente não existir. Complexidade não pontua por si só.

### C6 — Backtest

Especificado em detalhe em `04_PROTOCOLO_BACKTEST.md`. Invariantes:
universo dinâmico · execução em D+1 · custos explícitos · benchmark declarado a priori.

### C7 — Robustez

Especificado em `05_SUITE_ROBUSTEZ.md`. É **seção própria**, não um parágrafo.
Inclui o teste `H4` (spanning regression) — o que pode matar o projeto.

### C8 — Interpretação

O que funcionou, o que não funcionou, **por quê**, limitações reais e próximos passos
concretos. Alimenta o relatório de 5 páginas.

---

## 3. Estrutura de diretórios

```
.
├── CONTRIBUTING.md              branches, commits, PRs, checklist de revisão
├── README.md
├── docs/
│   ├── 00_PLANO_MESTRE.md       ← ponto de entrada
│   ├── 01_TESE_E_PRE_REGISTRO.md  hipóteses congeladas + critérios de falsificação
│   ├── 02_DADOS.md              catálogo de fontes, latências, regras de PIT
│   ├── 03_ARQUITETURA.md        (este arquivo)
│   ├── 04_PROTOCOLO_BACKTEST.md
│   ├── 05_SUITE_ROBUSTEZ.md
│   ├── 06_CRITICA_ADVERSARIAL.md  crítica hostil do próprio projeto
│   ├── 07_RISCOS_E_DECISOES.md    risk register + log de decisões
│   ├── 08_IDENTIDADE.md           nome + identidade visual (5% da nota)
│   ├── 09_FENOLOGIA_E_LIMIARES.md  janelas e limiares agronômicos por cultura/UF
│   ├── 10_REFERENCIAS.md          referências acadêmicas, métodos e fontes (com proveniência)
│   ├── 11_AUDITORIA_FASE1.md      evidências do fechamento da ingestão
│   ├── 12_PENDENCIAS_TRANSVERSAIS.md  dívidas sem fase proprietária
│   ├── DIARIO_GENAI.md            registro contínuo de uso de IA (15% da nota)
│   └── adr/                       Architecture Decision Records
├── pyproject.toml               empacotamento + config de ruff/pytest
├── requirements.lock            stack pinado com hashes (reprodutível)
├── scripts/                     guards determinísticos (check_lookahead, check_secrets)
├── src/quantagro/
│   ├── ingest/              C0 — preços, eventos, safra, clima, comércio e controles
│   ├── validate/            C1 — schemas e carimbo PIT
│   ├── prices/             C0–C1 — COTAHIST + eventos → retorno total point-in-time
│   ├── features/            C2 — shock, exposure, context
│   ├── stats/               C3 — testes, FDR, bootstrap
│   ├── signal/              C4 — convention (sinal), score → carteira
│   ├── backtest/            C6 — engine, custos, métricas
│   ├── robustness/          C7 — sensibilidade, placebo, spanning
│   └── report/              C8 — tabelas e gráficos do relatório
├── tests/                       espelha src/ — inclui fixtures reais e anti-lookahead
│   └── fixtures/                amostras reais (COTAHIST, respostas da B3)
├── notebooks/                   exploração (nunca fonte de verdade)
├── data/
│   ├── raw/        (gitignored)  como veio da fonte, intocado
│   ├── interim/    (gitignored)  limpo e carimbado com avail_date
│   ├── processed/  (gitignored)  features prontas
│   └── manifests/  (versionado)  hash + data de download + vintage de cada pull
└── outputs/
    ├── figures/                 gráficos do relatório
    └── tables/                  tabelas de resultado e robustez
```

**Por que `data/manifests/` é versionado e o resto não**: o dado bruto é grande e
regenerável pelo código. O manifesto é pequeno e é a **prova** de qual vintage usamos —
é ele que torna o resultado auditável.

---

## 4. Decisões de engenharia já tomadas

| Decisão | Escolha | Motivo |
|---|---|---|
| Linguagem | Python | única razoável para o stack e é o que o time domina |
| Interpretador | **3.14** (única versão na máquina) | verificado: pandas 3.0.3 / numpy 2.5.1 / scipy 1.18 / statsmodels 0.14.6 têm wheels e funcionam |
| pandas | **3.x** | consequência do 3.14 — pandas 2.x não tem wheel para cp314. **Atenção: pandas 3 tem breaking changes vs. 2.x** (Copy-on-Write por padrão); tutoriais antigos podem não funcionar. Registrado em ADR |
| Formato intermediário | Parquet | tipado, comprimido, rápido; CSV perde tipo e é fonte de bug silencioso |
| Loops | vetorizar com pandas/numpy | reduz custo e evita estados implícitos em séries/painéis |
| Reprodutibilidade | dependências pinadas + lockfile + seed fixa | um backtest que não roda igual duas vezes não é evidência de nada |

---

## 5. Automação de qualidade (o que a máquina garante, não a disciplina humana)


Hooks e CI existem para tornar impossível o erro que mais custa neste projeto.

| Guardião | O que faz | Onde (implementado) |
|---|---|---|
| **Lint + formatador** | `ruff check` + `ruff format` a cada commit e na CI | `.pre-commit-config.yaml` + `.github/workflows/ci.yml` |
| **Bloqueio de segredo** | impede commit com chave/token/credencial | `scripts/check_secrets.py` (pre-commit + CI) |
| **Varredura anti-lookahead** | tripwire contra `.shift(-N)` sem justificativa | `scripts/check_lookahead.py` (pre-commit + CI) |
| **CI** | lint + guards + testes a cada PR; `main` só recebe merge com CI verde | GitHub Actions |
| **Teste de sinal invertido** | trava a convenção `estresse ⇒ produtor sobe, frigorífico cai` | `tests/test_signal_sign.py` |
| **Reprodutibilidade** | stack pinado com hashes; instalação idêntica à da CI | `requirements.lock` (ver D-012) |

> Os dois tripwires (lookahead e segredo) são *baratos e determinísticos*, não prova de
> ausência — a defesa real continua sendo a revisão de PR e os testes (ver D-012). O formatador
> é só o `ruff format` (o `black` foi removido para evitar dois formatadores em conflito).

> O bug de **sinal invertido** e o bug de **lookahead** são os dois que destroem um projeto
> quant, e ambos são silenciosos: o backtest roda, produz um número bonito, e está errado.
> Por isso os dois têm guardião automatizado, não confiam em revisão humana.

---

## 6. Estado de implementação (atualizado em 2026-07-20)

O que já existe em `src/quantagro/` e obedece ao contrato acima. O restante permanece
especificação (§2) até ser construído — e cada peça construída entra com teste e CI verde.

| Camada | Módulo | Estado | Notas |
|---|---|---|---|
| Fundação | `pyproject.toml`, `requirements.lock`, CI, guards | ✅ | D-012; stack cp314 pinado com hashes |
| C0 preço | `ingest/cotahist.py` | ✅ | parser de largura fixa (offsets validados em arquivo real), download com cache + manifesto de vintage; delisting-proof (R4/D-004) |
| C0 eventos | `ingest/events_b3.py`, `ingest/events_statusinvest.py`, `ingest/events_manual.py` | ✅ | B3: dinheiro paginado e ações filtradas por classe/ISIN. StatusInvest: cauda deslistada ou B3 inteiramente vazia, nominal via `sov`, sem apagar parcelas iguais legítimas. Manual: bonificações SLC/VITT/KLABIN com fonte primária (D-025) |
| C0–C1 preço | `prices/adjust.py`, `prices/assemble.py` | ✅ | **retorno total point-in-time** (D-014) + **montador** (D-015): merge B3×StatusInvest sem dupla contagem, corte na deslistagem, tripwire de split perdido; validado contra o split real da SLC |
| C0 safra | `ingest/conab.py`, `ingest/conab_calendar.py` | ✅ | painéis de vintages (grãos/café/cana) com manifesto por captura datada (a fonte reescreve o arquivo no lugar); **calendário R10 curado** (D-017): `(ano_agricola, id_levantamento) → data de divulgação` de fontes primárias, carimbo `avail_date` que falha alto fora do mapa |
| C0 clima | `ingest/chirps.py` | ✅ | precipitação CHIRPS com **vintage real** (prelim/final arquivados separadamente); download diário e mensal + manifesto (hash), GeoTIFF lido sem GDAL (`tifffile`), agregação ignorando `nodata`; tripwire de grade global; revisão prelim→final medida ao vivo (D-018/D-050) |
| C0 clima | `ingest/power.py` | ✅ | temperatura NASA POWER (secundária) por ponto — centroides das regiões do CHIRPS. Fonte **não** preserva vintage: classifica proveniência (`MERRA2`=definitivo / `GEOSIT`/`FLASHFLUX`=provisório) por resposta e grava no manifesto; fill −999→`NaN`; cache por captura datada (D-019) |
| C0 comércio | `ingest/comexstat.py` | ✅ | H1b *ex post* (`POST /general`). Guardrail do NCM string de 8 dígitos; métricas string→int; captura datada e `dates/updated`. Vintages históricos não são recuperáveis, portanto a fonte **não entra no sizing primário** (D-020/D-026) |
| C0 controle | `ingest/oni.py` | ✅ | ONI NOAA/CPC sazonal: parser da temporada centrada, captura datada + manifesto; fonte sobrescreve o histórico e revisa os valores recentes. `initial_avail_date` no dia 5 após o fim da janela; caso primário espera mais 2 meses para estabilização (D-021). RONI fica para robustez, sem troca silenciosa do pré-registro |
| C0 controle | `ingest/nefin.py` | ✅ | fatores brasileiros para H4, em decimal. Download preso ao SHA do commit oficial + manifesto; snapshot inteiro recebe a data do commit. Revisão HML material comprovada entre dois vintages; uso exclusivamente ex post, nunca no sinal (D-022) |
| C0 geografia | `ingest/pam.py`, `ingest/pam_calendar.py`, `ingest/ibge_geometry.py` | ✅ | PAM/SIDRA 1612 municipal com calendário efetivo 2014–2024, captura datada e pesos *as-of*; inclui soja 2713, milho 2711, algodão 2689 e cana 2696. Malha IBGE 2013 fixa pré-amostra, agora incluindo SP. Cobertura positiva sem polígono falha alto (D-024/D-048/D-050) |
| C4 sinal | `signal/convention.py` | 🟡 | a convenção algébrica histórica `S = E·Shock` permanece travada contra inversão acidental, mas foi rejeitada economicamente em D-043. Algodão foi excluído e cana passou apenas o mecanismo físico; direção reformulada e carteira seguem sem congelamento até a auditoria empresarial da cana (D-044–D-051/R24) |
| C1 validação | `validate/pit.py`, `validate/universe.py` | ✅ | carimbo `avail_date` + filtro as-of; universo dinâmico validado nas 4 deslistagens reais de 2025. Cross-check dos 19 papéis vivos concluído, com divergências classificadas contra COTAHIST oficial (`scripts/crosscheck_yahoo.py`, D-025) |
| C2 features | `features/shock_spec.py` | ✅ | contrato do `Shock` primário congelado e testado (D-023): soja + milho 2ª, UFs/janelas, chuva CHIRPS, mínimo 10 safras e geografia PAM/IBGE→UF→CONAB. Extensões ficam separadas: `COTTON_WINDOWS` foi rejeitado (D-047–D-049); cana tem contratos distintos de crescimento e maturação (D-050/D-051) |
| C2 features | `features/shock.py` | ✅ | cálculo do `Shock` as-of `t` (D-028): acumulado `prelim` até a data de corte, climatologia expanding do mesmo trecho (produto `final`, ≥10 safras, cobertura diária obrigatória), `Shock = −z`; UF pondera municípios pela PAM as-of e o nacional pondera UFs pela safra CONAB anterior encerrada (nunca a corrente), renormalizando sobre janelas já iniciadas com `uf_coverage_weight` visível. Carimbo por produto: `prelim` +7d, `final` +60d |
| C2 features | `features/regionalize.py` | ✅ | raster CHIRPS → município IBGE 2013 (D-027): ponto-em-polígono even-odd sobre centros de célula p05 (numpy puro), índice município→células cacheável que valida a grade, painéis diário e mensal ignorando `nodata`. Fallback auditável para município sub-célula; polígonos de água não-municipais excluídos. Validado ao vivo nas 7 UFs dos grãos e nas 5 UFs da cana |
| C2 features | `features/panel.py` + `scripts/build_municipal_panel.py` | ✅ | painel municipal diário CHIRPS por **streaming** (baixa em memória → regionaliza → descarta), índice de células cacheável, manifesto consolidado `chirps_h1_bulk` (url+sha256/raster) como prova de vintage; enumera exatamente as janelas primárias (prelim 2015/16–2024/25 + climatologia final 2000–2023) |
| C2 features | `features/exposure.py` + `data/reference/exposure_fundamental_v1.json` | 🟡 | matriz fundamentalista PIT do canal preço/insumo (D-032/D-033), sem retornos: valida fonte, datas, direção, materialidade e composição. Quatro nomes diretos; teste-canário prova que divulgação futura não reescreve o passado. O artefato é válido, mas não está promovido a score até concluir D-034 |
| C3 stats | `stats/inference.py` | ✅ | OLS **cluster-robust** e **HAC/Newey–West** (statsmodels), **pairs cluster bootstrap**, **moving-block bootstrap** e **BH-FDR** (conferido contra statsmodels). Pensado para N efetivo pequeno |
| C3 stats | `stats/h1a.py`, `stats/h1b.py`, `stats/gate.py` | ✅ | rodadores de H1a (revisão CONAB ~ `Shock` de UF, memoizado por corte) e H1b (Δlog exportação ~ `Shock` nacional, Newey–West); orquestrador aplica BH-FDR na família de 11 testes e emite o veredito. **Portão da Fase 2 atravessado (D-031)** |
| C3 stats | `stats/cotton_h1.py`, `scripts/run_cotton_h1.py`, `data/reference/cotton_h1_result_v1.json` | ✅ | validação isolada do algodão, sem retornos: painel de 3 safras, OLS agrupado, UFs/anos/LOO e veredito literal de D-048. Critério não corroborado, com sinal positivo em todos os diagnósticos desta amostra; registro imutável contém hashes das entradas e da primeira execução (D-049) |
| C2/C3 cana | `features/cane_panel.py`, `features/cane_shock.py`, `stats/cane_h1.py`, scripts e `data/reference/cane_h1_result_v1.json` | ✅ | submodelo mensal separado: crescimento/produção e maturação/ATR nunca se misturam. 198 rasters com manifesto, painel SP+MG+GO+MS+PR e portão direcional reproduzível. Maturação passou D-050 (8/8 LOO, 5/5 UFs), mas sem significância; R24 bloqueia tradução automática em ação (D-051) |
| C4 estratégia | `backtest/strategy_spec.py` | ✅ | contrato congelado da estratégia reformulada (D-053), anterior ao holdout e return-agnóstico: universo de 5 nomes, direção H′ (grãos = negativo de `E·Shock`; cana +1), sizing dollar-neutral proporcional ao sinal com cap 0,40/0,15 (B1, resolve R19), execução D+1, pesos CONAB, e o teste primário spread produtor–processador só nos grãos (A1). Travado em `tests/test_strategy_spec.py` |
| C6 backtest · C7 robustez · C8 report | idem | ⬜ | especificados nos docs `04`/`05`; a máquina de backtest (Fase 4) consome `strategy_spec.py` |

> A camada **`prices/`** não estava no esqueleto original de 8 camadas: ela nasceu na Fase 1
> como o passo que transforma preço bruto + eventos corporativos em retorno total antes das
> features. Fica entre C0 (ingestão) e C1 (validação). Registrá-la aqui, em vez de encaixá-la
> à força numa caixa existente, é a escolha honesta — a arquitetura real tem essa peça.

Ver o andamento por fase em `00_PLANO_MESTRE.md` §4 e as decisões em `07_RISCOS_E_DECISOES.md`.
