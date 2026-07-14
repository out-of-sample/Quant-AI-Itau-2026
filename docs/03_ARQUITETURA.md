# Arquitetura do pipeline — especificação

> Este documento **especifica**, não implementa. Descreve o que cada camada recebe, o que
> entrega, e qual invariante ela é obrigada a garantir. O código vem depois e tem que
> obedecer a este contrato.


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
│     H1 mecanismo · H2 preço · H5 placebo · BH-FDR · block bootstrap      │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ C4  SINAL → POSIÇÃO                                                      │
│     S = E·Shock · gate de confirmação ComexStat · sizing ∝ convicção     │
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
| **(b) Exposição** | `E_{i,c}` — matriz empresa × commodity, de `[-1,+1]` | traduz o choque agregado em cross-section |
| **(c) Contexto/controle** | IBOV, USDBRL, ONI (El Niño), vol realizada, ADTV, momentum | separa o efeito da tese de movimento de mercado amplo — **sem isso não há como afirmar que é alfa** |

### C3 — Teste de significância (PORTÃO)

**Esta camada tem poder de veto.** Não é decorativa.

Roda as hipóteses `H1` (o choque prevê a exportação física?), `H2` (prevê o futuro da
commodity?) e `H5` (placebo espacial) **antes** de qualquer backtest de retorno de ações.

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
- **Gate de confirmação** ComexStat: peso 1.0 (confirma) / 0.5 (sem dado) / 0.0 (contradiz)
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
├── CLAUDE.md                    convenções técnicas do repositório
├── CONTRIBUTING.md              branches, commits, PRs, checklist de revisão
├── README.md
├── docs/
│   ├── 00_PLANO_MESTRE.md       ← ponto de entrada
│   ├── 01_TESE_E_PRE_REGISTRO.md  hipóteses congeladas + critérios de falsificação
│   ├── 02_DADOS.md              catálogo de fontes, latências, regras de PIT
│   ├── 03_ARQUITETURA.md        (este arquivo)
│   ├── 04_PROTOCOLO_BACKTEST.md
│   ├── 05_SUITE_ROBUSTEZ.md
│   ├── 06_CRITICA_ADVERSARIAL.md  o projeto atacado pelas personas céticas
│   ├── 07_RISCOS_E_DECISOES.md    risk register + log de decisões
│   ├── 08_IDENTIDADE_ROBO.md      nome + identidade visual (5% da nota)
│   ├── DIARIO_GENAI.md            registro contínuo de uso de IA (15% da nota)
│   └── adr/                       Architecture Decision Records
├── src/                         (código — fase seguinte)
│   └── <pacote>/
│       ├── ingest/              C0 — um módulo por fonte
│       ├── validate/            C1 — schemas e carimbo PIT
│       ├── features/            C2 — shock, exposure, context
│       ├── stats/               C3 — testes, FDR, bootstrap
│       ├── signal/              C4 — score → carteira
│       ├── backtest/            C6 — engine, custos, métricas
│       ├── robustness/          C7 — sensibilidade, placebo, spanning
│       └── report/              C8 — tabelas e gráficos do relatório
├── tests/                       espelha src/ — inclui testes de anti-lookahead
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
| Loops | vetorizar com pandas/numpy | já é convenção do `CLAUDE.md` |
| Reprodutibilidade | dependências pinadas + lockfile + seed fixa | um backtest que não roda igual duas vezes não é evidência de nada |

---

## 5. Automação de qualidade (o que a máquina garante, não a disciplina humana)


Hooks e CI existem para tornar impossível o erro que mais custa neste projeto.

| Guardião | O que faz | Onde |
|---|---|---|
| **Formatador automático** | roda o linter/formatador a cada arquivo salvo | hook local |
| **Bloqueio de segredo** | impede commit que contenha chave/token | git hook (`.githooks/pre-commit`) |
| **Varredura anti-lookahead** | procura padrões suspeitos: `.shift(-1)`, filtro por `ref_date` a jusante da C1, estatística calculada sobre o período inteiro | git hook + CI |
| **CI** | lint + testes a cada PR; `main` só recebe merge com CI verde | GitHub Actions |
| **Teste de sinal invertido** | trava a convenção de sinal (`estresse ⇒ produtor sobe, frigorífico cai`) | teste unitário |

> O bug de **sinal invertido** e o bug de **lookahead** são os dois que destroem um projeto
> quant, e ambos são silenciosos: o backtest roda, produz um número bonito, e está errado.
> Por isso os dois têm guardião automatizado, não confiam em revisão humana.
