# Suíte de robustez

> Seção própria do projeto, não um parágrafo do relatório. Cada teste abaixo tem um
> **resultado esperado declarado antes de rodar**. Um teste cujo resultado a gente aceita
> qualquer que seja ele não é um teste — é uma ilustração.

> **Estado após D-053/D-054:** H1 passou; a família H2a terminou negativa; a direção acionária
> original foi falsificada; H′ e o substituto de H3 foram congelados em D-053. Esta suíte nasceu
> antes dessa reformulação e será formalmente congelada para H′ na Fase 5, depois que a Fase 4.0
> fechar a mecânica. No desenvolvimento ela serve como diagnóstico e teste do motor — não como
> validação da direção, que foi formulada com esse período. No holdout, roda no mesmo tiro único
> da Fase 6, sem selecionar quais resultados mostrar.

---

## 1. Hierarquia dos testes

Nem todo teste tem o mesmo poder de destruição. Ordenados por gravidade:

| Nível | Teste | Se falhar... |
|---|---|---|
| 🔴 **Existencial** | **H4 — Spanning regression** | a estratégia é beta de commodity reembalado. O projeto perde a razão de existir como estratégia, e vira um estudo (ainda publicável, mas temos que dizer isso) |
| 🔴 **Existencial** | **H5 — Placebo espacial** | o sinal não vem da agronomia. Estamos capturando outra coisa (ENSO, FX, risco global) e a narrativa está errada |
| 🔴 **Existencial** | **Sensibilidade ao lag de publicação** | se o alfa só existe com lag curto e some com lag realista, o alfa era lookahead |
| 🟡 **Grave** | **Teste primário H′ (D-053)** | se o spread não vier na direção congelada, a reformulação Q-dominante não chega ao equity |
| 🟡 **Grave** | Sensibilidade a hiperparâmetros | resultado é um pico isolado no espaço de parâmetros = garimpado |
| 🟢 **Saudável** | Subperíodos, custos dobrados, universo alternativo | degradação é esperada e aceitável; colapso não |

Resultados que já pertencem à trilha histórica, e não à suíte futura: H1 passou (D-031), H2a
falhou em seis medidas (D-037–D-041), o Fama–MacBeth foi abandonado por N insuficiente e a
direção original de H3 foi falsificada (D-043). Eles não serão rerodados com novas escolhas
para tentar produzir narrativa melhor.

---

## 2. Os testes existenciais

### 2.1 🔴 H4 — A estratégia é só beta de commodity? (*spanning regression*)

**A pergunta que a banca vai fazer**: *"Isso não é beta de commodities, câmbio ou fatores
reembalado numa carteira de ações?"*

Regredimos o retorno da estratégia contra tudo o que é barato e óbvio de comprar:

```
r_strat,t = α + b₁·IBOV + b₂·USDBRL + b₃·fut_soja + b₄·fut_milho
            + b₅·fut_açúcar + b₆·fut_café + b₇·ONI(El Niño)
            + fatores NEFIN (Mercado, SMB, HML, WML, IML) + ε
```

- **Resultado esperado sob H′**: `α > 0` e estatisticamente significativo.
- **Critério de falha**: `α ≤ 0` ou não-significativo.
- **Se falhar**: reportamos, com todas as letras, que a estratégia não gera alfa além dos
  fatores conhecidos. Isso é um resultado honesto e ainda rende nota nos critérios "Análise
  dos Resultados" (15%) e "Conclusão" (10%) — mas fingir que não rodamos esse teste seria
  o pior desfecho possível, porque a banca **vai** perguntar.

> Os fatores brasileiros (Mercado, SMB, HML, WML, IML — iliquidez) são publicados
> gratuitamente pelo **NEFIN/FEA-USP**. Usá-los, em vez de improvisar fatores caseiros, é
> o padrão acadêmico brasileiro e é barato de fazer.

### 2.2 🔴 H5 — Placebo espacial

Recalculamos o índice de choque climático usando células de grade em regiões **sem produção
  agrícola relevante** (Amazônia central, litoral, áreas urbanas), mantendo direção H′,
  calendário, universo, score e custos idênticos.
pipeline idêntico.

- **Resultado esperado**: o alfa **desaparece**. Chuva na Amazônia central não tem por que
  prever o resultado da SLC Agrícola.
- **Critério de falha**: o alfa **sobrevive** ao placebo.
- **Se falhar**: é a prova de que o sinal não é agronômico. Provavelmente é um proxy de
  ENSO, de risco global ou de câmbio. A tese, como escrita, está errada.

**Placebos adicionais** (mesmo espírito, mais baratos):
- **Placebo temporal**: contar a anomalia climática **fora** da janela fenológica (ex.: chuva
  em julho no MT, quando não há soja no campo). Deveria dar zero.
- **Placebo de exposição**: embaralhar a matriz `E_{i,c}` entre empresas. Deveria destruir
  o alfa — se não destruir, o sinal não vem da exposição, e a tese cross-seccional cai.
- **Placebo de rótulo**: embaralhar as datas do choque. Distribuição nula do Sharpe.

> O placebo de exposição é o mais importante dos três, porque testa se a heterogeneidade
> empresa–cultura realmente ordena H′. O embaralhamento deve respeitar o desenho congelado e
> não pode reintroduzir a direção histórica já falsificada.

### 2.3 🔴 Sensibilidade ao lag de publicação

O caso primário permanece em 7 dias. A Fase 5 congelará uma grade simétrica de lags antes do
holdout; a lista herdada é **0, 3, 7, 14 e 21 dias**, sujeita apenas à verificação de que cada
valor representa uma disponibilidade tecnicamente implementável, não a desempenho.

- **Resultado esperado**: alfa **decai suavemente** com o lag, e ainda existe em 7 dias
  (nosso caso primário).
- **Critério de falha**: alfa **alto em lag 0-3 e desaparece em 7+**.
- **Se falhar**: o alfa vivia de informação que não estaria disponível na hora da decisão.
  Ou seja, era **lookahead**, não alfa.

Este é o teste mais barato de rodar e um dos mais mortais. Deve ser o primeiro.

### 2.4 🔴 Sensibilidade à revisão dos dados climáticos (específico deste projeto)

**Problema confirmado empiricamente** (ver `02_DADOS.md`): NASA POWER e ERA5 **sobrescrevem
retroativamente** os últimos ~2-3 meses de dado. A série que baixamos hoje **não é** a série
que estava disponível na época. Isso é lookahead embutido na fonte, e não é removível
simplesmente "tomando cuidado no código".

**Teste**: comparar o sinal construído com **CHIRPS-prelim** (o que se sabia na época) contra
o construído com **CHIRPS-final** (a verdade revisada). O CHIRPS é a única fonte que arquiva
as duas versões separadamente, o que nos dá um **proxy honesto de vintage**.

- **Resultado esperado**: a diferença é pequena em relação ao tamanho do choque que queremos
  detectar (uma seca severa aparece nas duas versões).
- **Critério de falha**: o alfa existe com o dado final e some com o preliminar.
- **Se falhar**: todo o resultado obtido com POWER/ERA5 está contaminado, e temos que
  reconstruir o sinal apenas com fontes que preservam vintage.

> **Esta magnitude precisa ser medida, não assumida.** É a diferença entre reconhecer uma
> limitação e varrê-la para debaixo do tapete.

---

## 3. Sensibilidade a hiperparâmetros

Padrão Kairos: variar **um parâmetro de cada vez**, em torno da escolha primária, e mostrar
que o resultado não desmorona na vizinhança. Tabela no relatório.

| Parâmetro | Primário | Variações testadas | Falha se... |
|---|---|---|---|
| Janela fenológica | contrato D-023 por cultura × UF | bloco completo em −10 e +10 dias | resultado só existe na janela exata |
| Temperatura (secundária) | fora do primário | soja `T_max>40 °C`; milho `T_max>35 °C` | o ganho depende da fonte POWER sem vintage |
| Mínimo de anos da climatologia | 10 | 5, 15 | idem |
| Horizonte de holding | 21 dias úteis | 5, 10, 42, 63 | alfa só existe num horizonte específico |
| Lag de publicação | 7 dias | 0, 3, 14, 21 | ver §2.3 |
| Método de exposição `E` | fundamentalista (A) | estatístico (B) | os dois discordam completamente |
| Cap por nome | 0,40 por grão; 0,15 SMTO3 (D-053) | vizinhos simétricos pré-registrados na Fase 5 | resultado depende de uma única posição concentrada |
| Filtro de liquidez (ADTV) | valor a congelar na Fase 4.0 | ±50% do valor congelado | alfa só existe nos nomes ilíquidos ⇒ não é operável |

> **Interpretação correta de uma tabela de sensibilidade**: não estamos procurando o melhor
> valor. Estamos provando que a escolha primária **não foi garimpada**. Se o Sharpe é 1.8 no
> parâmetro escolhido e 0.2 em todos os vizinhos, isso é evidência **contra** nós, não a favor.

---

## 4. Robustez de amostra e de regime

| Teste | O que é | Por quê |
|---|---|---|
| **Subperíodos** | desenvolvimento operacional 2015/16–2019/20; cortes do holdout só serão aplicados no tiro único | ver se o resultado vem de um único episódio sem usar 2020–2025 para redesenhar |
| **Anos de El Niño vs. La Niña** | condicionar por regime ENSO | a estratégia só funciona num regime climático? |
| **Universo alternativo** | Método A direto vs. diagnóstico Método B; universo amplo só se houver evidência admissível | ver D-033 e `01_TESE_E_PRE_REGISTRO.md` §6 |
| **Custos dobrados** | 2× o custo estimado | margem de segurança contra otimismo de execução |
| **Exclusão de um nome por vez** (*leave-one-out*) | remover cada ação e re-rodar | o alfa depende de uma única empresa? |
| **Exclusão da maior janela de retorno** | remover o melhor mês | o resultado é um evento único? |

---

## 5. Teste de generalização em outro mercado (ambicioso, alta recompensa)

Padrão KernelNet — que rodou a metodologia inteira no S&P 500 para checar se o alfa era
artefato do mercado brasileiro.

**Análogo aqui**: aplicar a mesma sequência de método ao mercado americano, mas com direção
econômica derivada e pré-registrada naquele mercado — nunca copiar a direção antiga falsificada:
- Choque climático no **Corn Belt** (mesmas fontes: CHIRPS/ERA5)
- Universo: produtores/processadores agrícolas listados nos EUA (ADM, Bunge, Corteva,
  Mosaic, CF Industries, Tyson, Darling...)
- Mesma disciplina PIT, heterogeneidade produtor/processador e tentativa de falsificação

- **Se funcionar lá também**: a tese é **estrutural**, não um artefato do Brasil. Isso é um
  argumento muito forte e transforma o trabalho.
- **Se não funcionar lá**: ainda é defensável — o mercado americano é mais eficiente e tem
  uma indústria inteira de meteorologia de trading (o dado já está no preço em minutos).
  **A ineficiência existir no Brasil e não nos EUA é exatamente a nossa tese.** Nos dois
  casos aprendemos algo publicável.

> É extensão opcional, posterior ao núcleo e fora do gate da Fase 5. Não será iniciada antes
> do backtest brasileiro estar fechado; complexidade adicional não pontua por si só.

---

## 6. Estatística: como não mentir para nós mesmos


| Problema | Por que é grave aqui | Correção |
|---|---|---|
| **Múltiplas comparações** | culturas × UFs × horizontes × janelas = centenas de testes; alguns "significativos" por puro acaso | **Benjamini-Hochberg (FDR)** sobre toda a família de testes (padrão KernelNet) |
| **Autocorrelação** | o sinal climático é fortemente persistente e usamos retornos sobrepostos; o t-stat ingênuo é inflado | **Newey-West** + **block bootstrap** |
| **N efetivo ≪ N nominal** | soja no MT, GO e MS no mesmo ano de seca não são 3 observações independentes — é 1 evento climático | **cluster por ano-safra**; reportar o número de **eventos independentes**, não de linhas |
| **Poucos eventos** | 1 safra/ano; o sinal começa em 2015/16 e H1a em 2017/18. O N independente é menor que o sugerido pelo painel UF×cultura | computar e reportar o N efetivo **por teste**; é a limitação nº 1 do projeto (ver `06_CRITICA_ADVERSARIAL.md`) |
| **Data-mining do universo** | escolher os tickers depois de ver quais funcionaram | universo definido a priori por critério econômico (exposição declarada), não por retorno |

> **O ponto mais desconfortável e mais importante do projeto**: a natureza sazonal do sinal
> significa que temos **poucas dezenas de eventos verdadeiramente independentes**, não
> milhares. Nenhuma quantidade de dias de backtest muda isso — 3.000 dias úteis de retorno
> derivados de poucos anos-safra continuam sendo poucos eventos, não 3.000. Qualquer intervalo de confiança que
> ignore isso está mentindo. Vamos reportar o **N efetivo** explicitamente. Um avaliador de
> gestora vai reparar nisso na hora, e é melhor sermos nós a levantar a questão.
