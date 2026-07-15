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

Andamento (2026-07-15), toda peça com teste e CI verde (ver `03_ARQUITETURA.md` §6):
- ✅ Fundação de engenharia (empacotamento, lockfile com hashes, CI, guards de lookahead/segredo).
- ✅ Fontes de proventos verificadas ao vivo e decididas (D-013): B3 oficial + StatusInvest.
- ✅ Motor de **retorno total point-in-time** (D-014), sem *adjusted close* retroativo.
- ✅ Parser + download do **COTAHIST** (offsets validados em arquivo real, delisting-proof).
- ✅ Fetchers de eventos da **B3**: dinheiro (dividendo/JCP) e ações (split/bonificação/
  grupamento, `factor` validado contra preço).
- ⬜ Fetcher da **StatusInvest** (dividendos da cauda deslistada, campo `adj`).
- ⬜ **Montador**: COTAHIST + eventos → série de retorno total por papel, delisting-aware.
- ⬜ Carimbo de `avail_date` (C1) e universo dinâmico com filtro de liquidez.

> **Portão**: se não conseguirmos construir uma série de preços delisting-aware e ajustada
> por proventos, o cross-section não é confiável e nada adiante vale.

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
