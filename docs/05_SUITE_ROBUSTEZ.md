# Suíte de robustez

> Seção própria do projeto, não um parágrafo do relatório. Cada teste abaixo tem um
> **resultado esperado declarado antes de rodar**. Um teste cujo resultado a gente aceita
> qualquer que seja ele não é um teste — é uma ilustração.

> **Estado após D-034:** H2 foi separado em H2a preditivo, que funciona como portão econômico
> antes da carteira, e H2b de evento, que é diagnóstico. O H3/Fama–MacBeth está suspenso até
> ser substituído por desenho compatível com o N de três a quatro ações. Nenhum teste de
> robustez abaixo autoriza pular a Fase 3.1.

---

## 1. Hierarquia dos testes

Nem todo teste tem o mesmo poder de destruição. Ordenados por gravidade:

| Nível | Teste | Se falhar... |
|---|---|---|
| 🔴 **Existencial** | **H4 — Spanning regression** | a estratégia é beta de commodity reembalado. O projeto perde a razão de existir como estratégia, e vira um estudo (ainda publicável, mas temos que dizer isso) |
| 🔴 **Existencial** | **H5 — Placebo espacial** | o sinal não vem da agronomia. Estamos capturando outra coisa (ENSO, FX, risco global) e a narrativa está errada |
| 🔴 **Existencial** | **Sensibilidade ao lag de publicação** | se o alfa só existe com lag curto e some com lag realista, o alfa era lookahead |
| 🔴 **Existencial** | **H2a — transmissão preditiva ao preço** | se o choque não antecipa o futuro da commodity no desenvolvimento, o canal de preço usado para assinar `P` não se sustenta |
| 🟡 **Grave** | H1 — mecanismo físico (clima → safra/exportação) | o elo causal postulado não existe; qualquer alfa seria coincidência |
| 🟡 **Grave** | **H3 — desenho compatível com N** | se a inferência depender de uma cross-section inexistente, a evidência acionária não é identificada |
| 🟡 **Grave** | Sensibilidade a hiperparâmetros | resultado é um pico isolado no espaço de parâmetros = garimpado |
| 🟢 **Saudável** | Subperíodos, custos dobrados, universo alternativo | degradação é esperada e aceitável; colapso não |

---

## 2. Os testes existenciais

### 2.1 🔴 H4 — A estratégia é só beta de commodity? (*spanning regression*)

**A pergunta que a banca vai fazer**: *"Isso não é uma forma cara e complicada de ficar
comprado no futuro da soja?"*

Regredimos o retorno da estratégia contra tudo o que é barato e óbvio de comprar:

```
r_strat,t = α + b₁·IBOV + b₂·USDBRL + b₃·fut_soja + b₄·fut_milho
            + b₅·fut_açúcar + b₆·fut_café + b₇·ONI(El Niño)
            + fatores NEFIN (Mercado, SMB, HML, WML, IML) + ε
```

- **Resultado esperado**: `α > 0` e estatisticamente significativo.
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
agrícola relevante** (Amazônia central, litoral, áreas urbanas), mantendo todo o resto do
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

> O placebo de exposição é o mais importante dos três, porque testa justamente a parte
> **original** da tese: que o alfa vem da heterogeneidade produtor-vs-processador, e não de
> um efeito setorial médio. É o teste que confirma que a contribuição do trabalho é real.

### 2.3 🔴 Sensibilidade ao lag de publicação

Rodamos a estratégia com lag de publicação do dado climático de **0, 3, 7, 14 e 21 dias**.

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
| Cap por nome | a ratificar antes da carteira (R19/D-033) | vizinhos simétricos do valor escolhido | resultado depende de uma única posição concentrada |
| Filtro de liquidez (ADTV) | a definir | ±50% | alfa só existe nos nomes ilíquidos ⇒ não é operável |

> **Interpretação correta de uma tabela de sensibilidade**: não estamos procurando o melhor
> valor. Estamos provando que a escolha primária **não foi garimpada**. Se o Sharpe é 1.8 no
> parâmetro escolhido e 0.2 em todos os vizinhos, isso é evidência **contra** nós, não a favor.

---

## 4. Robustez de amostra e de regime

| Teste | O que é | Por quê |
|---|---|---|
| **Subperíodos** | quebrar o backtest em blocos (pré-2016, 2016-2019, 2020-2022, 2023-2025) | ver se o alfa vem de um único episódio (ex.: a seca de 2021) |
| **Anos de El Niño vs. La Niña** | condicionar por regime ENSO | a estratégia só funciona num regime climático? |
| **Universo alternativo** | Método A direto vs. diagnóstico Método B; universo amplo só se houver evidência admissível | ver D-033 e `01_TESE_E_PRE_REGISTRO.md` §6 |
| **Custos dobrados** | 2× o custo estimado | margem de segurança contra otimismo de execução |
| **Exclusão de um nome por vez** (*leave-one-out*) | remover cada ação e re-rodar | o alfa depende de uma única empresa? |
| **Exclusão da maior janela de retorno** | remover o melhor mês | o resultado é um evento único? |

---

## 5. Teste de generalização em outro mercado (ambicioso, alta recompensa)

Padrão KernelNet — que rodou a metodologia inteira no S&P 500 para checar se o alfa era
artefato do mercado brasileiro.

**Análogo aqui**: aplicar a **mesma metodologia** (choque climático ponderado por produção →
exposição líquida → long/short) ao mercado americano:
- Choque climático no **Corn Belt** (mesmas fontes: CHIRPS/ERA5)
- Universo: produtores/processadores agrícolas listados nos EUA (ADM, Bunge, Corteva,
  Mosaic, CF Industries, Tyson, Darling...)
- Mesma estrutura produtor (+) vs. processador (−)

- **Se funcionar lá também**: a tese é **estrutural**, não um artefato do Brasil. Isso é um
  argumento muito forte e transforma o trabalho.
- **Se não funcionar lá**: ainda é defensável — o mercado americano é mais eficiente e tem
  uma indústria inteira de meteorologia de trading (o dado já está no preço em minutos).
  **A ineficiência existir no Brasil e não nos EUA é exatamente a nossa tese.** Nos dois
  casos aprendemos algo publicável.

> Este é um teste em que **os dois resultados possíveis são bons para nós** — o que é raro
> e vale o esforço. Prioridade: alta, mas depois que o núcleo estiver fechado.

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
