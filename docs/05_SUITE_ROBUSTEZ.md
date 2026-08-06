# Suíte de robustez

> Seção própria do projeto, não um parágrafo do relatório. Cada teste abaixo tem um
> **resultado esperado declarado antes de rodar**. Um teste cujo resultado a gente aceita
> qualquer que seja ele não é um teste — é uma ilustração.

> **Estado final após D-075:** H1 passou no portão e teve direção estável em D-066, mas o
> veredito formal da suíte de mecanismo foi NÃO ROBUSTO (cobertura + placebo espacial). H2a
> terminou negativa e a direção acionária original foi falsificada. Na rodada única, H′ passou
> e H5 morreu como previsto, mas H4 falhou; portanto há evidência OOS da estratégia e P&L
> nominal positivo, **não** evidência de alpha climático ou habilidade contra o risk-free.

---

## 1. Hierarquia dos testes

Nem todo teste tem o mesmo poder de destruição. Ordenados por gravidade:

| Nível | Teste | Se falhar... |
|---|---|---|
| 🔴 **Existencial** | **H4 — Spanning regression** | a estratégia é beta de commodity reembalado. O projeto perde a razão de existir como estratégia, e vira um estudo (ainda publicável, mas temos que dizer isso) |
| 🔴 **Existencial** | **H5 — Placebo espacial** | o sinal não vem da agronomia. Estamos capturando outra coisa (ENSO, FX, risco global) e a narrativa está errada |
| 🟡 **Grave** | **Teste primário H′ (D-053)** | se o spread não vier na direção congelada, a reformulação Q-dominante não chega ao equity |
| 🟡 **Grave** | Sensibilidade a hiperparâmetros | resultado é um pico isolado no espaço de parâmetros = garimpado |
| 🟢 **Saudável** | Custos, LOO e grids operacionais D-068 | degradação é esperada e aceitável; colapso não |

Resultados que já pertencem à trilha histórica, e não à suíte futura: H1 passou (D-031), H2a
falhou em seis medidas (D-037–D-041), o Fama–MacBeth foi abandonado por N insuficiente e a
direção original de H3 foi falsificada (D-043). Eles não serão rerodados com novas escolhas
para tentar produzir narrativa melhor.

---

## 2. Os testes existenciais

### 2.1 🔴 H4 — A estratégia é só beta de commodity? (*spanning regression*)

**A pergunta que a banca vai fazer**: *"Isso não é beta de commodities, câmbio ou fatores
reembalado numa carteira de ações?"*

O D-068 elimina uma colinearidade do rascunho antigo: **IBOV e `Rm_minus_Rf` não entram
juntos**, pois ambos representam o fator de mercado brasileiro. O desfecho é o retorno líquido
da estratégia menos `Risk_Free` do NEFIN.

```
r_strat,t − RF_t = α + fatores NEFIN (Mercado, SMB, HML, WML, IML)
                   + USDBRL + soja + milho + açúcar + ONI + ε_t
```

- **Spec core (decomposição):** somente os cinco fatores NEFIN.
- **Spec estendida (veto):** core + FX + soja + milho + açúcar + ONI.
- **Inputs D-069:** calendário NEFIN/B3; DEXBZUS; ETFs futuros SOYB/CORN/CANE em USD;
  último ONI estabilizado disponível. Painel ex post de 1.495 sessões, sem nulos.
- **Inferência:** Newey–West/HAC com 21 lags; `α_H4=0,10`.
- **Resultado esperado sob H′:** `α > 0` e p unilateral ≤0,10 na spec estendida.
- **Critério de falha:** `α ≤ 0`, não-significativo ou controles não materializáveis.
- **Se falhar**: reportamos, com todas as letras, que a estratégia não gera alfa além dos
  fatores conhecidos. Isso é um resultado honesto e ainda rende nota nos critérios "Análise
  dos Resultados" (15%) e "Conclusão" (10%) — mas fingir que não rodamos esse teste seria
  o pior desfecho possível, porque a banca **vai** perguntar.

> Os fatores brasileiros (Mercado, SMB, HML, WML, IML — iliquidez) são publicados
> gratuitamente pelo **NEFIN/FEA-USP**. Usá-los, em vez de improvisar fatores caseiros, é
> o padrão acadêmico brasileiro e é barato de fazer.

### 2.2 🔴 H5 — Placebo espacial

O **veto** continua sendo o placebo geográfico prometido desde o pré-registro: recalcular o
índice com geografia fixa sem produção agrícola relevante, mantendo direção H′, calendário,
universo, score e custos. D-065/D-066 embaralharam UFs para testar o mecanismo H1; isso **não
substitui** este H5 de retorno.

**Geografia congelada antes da materialização (D-070):** 91 células CHIRPS contidas nos
polígonos IBGE 2013 de Canavieiras, Maraú e Salinas da Margarida (BA), Matinhos e Pontal do Paraná
(PR). Os cinco municípios têm produção PAM observada exatamente zero para soja e milho total
em todos os anos de 2014–2024. A média é ponderada pelo número fixo de células, sem peso de
produção. Janelas por cultura/UF, climatologia expanding, pesos CONAB da safra anterior e
todo o restante da estratégia real são reutilizados sem alteração. A escolha cobre duas
faixas costeiras — uma das geografias não produtoras prometidas no pré-registro — e não tenta
representar toda área não produtora do país.

**Input materializado (D-071):** 46 decisões × quatro nomes de grãos, de 07/01/2021 a
08/09/2025, sem ausências. O cálculo consumiu 6.197 raster-dias e foi reproduzido com o
mesmo SHA-256 `936bee66…32e1`. Isso fecha o input, não o teste: `T_placebo`, sua razão contra
`T_real` e o p-valor continuam lacrados até a rodada única.

- **Resultado esperado**: o alfa **desaparece**. Chuva nesses municípios costeiros sem
  soja/milho não tem por que prever o resultado da SLC Agrícola.
- **Critério executável D-068**: sobre o retorno líquido base médio dos cinco anos-safra,
  com sign-flip exato dos clusters, `|T_placebo| < 0,5·|T_real|` e p unilateral >0,10.
- **Critério de falha**: o placebo retém ≥50% do efeito ou permanece significativo.
- **Se falhar**: é a prova de que o sinal não é agronômico. Provavelmente é um proxy de
  ENSO, de risco global ou de câmbio. A tese, como escrita, está errada.

O placebo de exposição também permanece obrigatório, permutando materialidades **dentro do lado
econômico** para não reintroduzir a direção histórica falsificada. Como há apenas
`2!×2!=4` estados que preservam produtor/processador, ele é **descritivo**, não um segundo
teste a 10%. O veto formal é o geográfico.

Os placebos temporal e de rótulo já foram absorvidos pela suíte de mecanismo D-066; não
ganham novos P&Ls de holdout.

### 2.3 Sensibilidade ao lag de publicação

O caso primário permanece em 7 dias. D-066 já atrasou o mecanismo em mais 14 dias e preservou
o β em 1,02×. Para o retorno, D-068 permite apenas lags totais **14 e 21 dias** como
sensibilidades conservadoras. Os antigos 0/3 dias são removidos: são otimistas em relação à
disponibilidade congelada e não devem ganhar um P&L no holdout.

- **Resultado esperado**: alfa **decai suavemente** com o lag, e ainda existe em 7 dias
  (nosso caso primário).
- **Bandeira de fragilidade**: o caso de 7 dias funciona, mas há colapso abrupto nos dois
  atrasos conservadores.
- **Se falhar**: o alfa vivia de informação que não estaria disponível na hora da decisão.
  Ou seja, era **lookahead**, não alfa.

Os lags alternativos rodam depois do primário, no mesmo tiro, e nunca o substituem.

### 2.4 🔴 Sensibilidade à revisão dos dados climáticos (específico deste projeto)

**Problema confirmado empiricamente** (ver `02_DADOS.md`): NASA POWER e ERA5 **sobrescrevem
retroativamente** os últimos ~2-3 meses de dado. A série que baixamos hoje **não é** a série
que estava disponível na época. Isso é lookahead embutido na fonte, e não é removível
simplesmente "tomando cuidado no código".

**Executado em D-066**: comparar CHIRPS-prelim com CHIRPS-final dentro da suíte do mecanismo.
O produto final fortaleceu o β em 1,37×; não será transformado em novo P&L no holdout, pois
isso repetiria a família de escolhas sobre retornos.

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
| Janela/climatologia/fonte | contrato D-023 | **já testados em D-066**, sem novo P&L | veredito de mecanismo já registrado |
| Horizonte de holding | 21 dias úteis | **10, 42** | alfa só existe no horizonte exato |
| Lag total de publicação | 7 dias | **14, 21** | resultado some com atraso conservador |
| Cap por nome | 0,40 grão; 0,15 cana | grão **0,30/0,50**; cana **0,10/0,20**, single-knob | resultado depende do cap exato |
| Filtro de liquidez (ADTV) | R$ 8 milhões, 21 pregões (D-055) | R$ 4 mi e R$ 12 mi | alfa só existe nos nomes ilíquidos ⇒ não é operável |

Temperatura, Método B/universo amplo e troca de `E` ficam fora: foram rejeitados/suspensos por
vintage ou falta de identificação fundamental, e não podem reaparecer como tentativas de salvar
o holdout.

> **Interpretação correta de uma tabela de sensibilidade**: não estamos procurando o melhor
> valor. Estamos provando que a escolha primária **não foi garimpada**. Se o Sharpe é 1.8 no
> parâmetro escolhido e 0.2 em todos os vizinhos, isso é evidência **contra** nós, não a favor.

---

## 4. Robustez de amostra e de regime

| Teste | O que é | Por quê |
|---|---|---|
| **LOO de ano-safra** | excluir cada uma das cinco safras, uma por vez | resultado vem de um único episódio? |
| **Regime ENSO** | atribuição por ONI, descritiva, sem p-valor de subgrupo | resultado coincide com um regime climático? |
| **Custos dobrados** | 2× o custo estimado | margem de segurança contra otimismo de execução |
| **LOO de nome** | remover cada uma das cinco ações e re-rodar | resultado depende de uma única empresa? |

Não se usa o dev 2015/16–2019/20: R26 impede materializar três safras e 2019/20 é transição
excluída. Não se cria universo alternativo sem exposição fundamental admissível.

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

---

## 7. Pacote indivisível da rodada única (D-068–D-072)

O contrato executável vive em `backtest/holdout_spec.py`. O hash inicial D-068
`cefa5f60…2900` foi substituído em D-069 ao incluir os fontes H4; o hash D-069
`9ffa0fbf…df6` foi substituído em D-070 ao congelar a geografia H5 antes da materialização.
O hash D-070 `fbcaa5d0…964f` foi substituído em D-071 ao incluir o materializador e seu
registro. D-072 incorporou executor, inputs, fontes de preço e emissão; o payload vigente está
travado pelo SHA-256
`f97093b9e493d0370428f1948f54cdbc29d6ef57587cce06ab7f4de37c393f9e`. A rodada não
pausa após ver o primário: mesmo se H′ falhar, todos os passos são calculados e emitidos.

| Ordem | Bloco | Papel |
|---:|---|---|
| 0 | preflight + hashes | gate |
| 1 | teste primário H′ | **único confirmatório**, α=0,10 |
| 2 | carteira zero/base/2× | decisão; base é o resultado principal |
| 3–4 | AGRO3×ADTV D-067; setor×clima D-064 | diagnóstico obrigatório |
| 5–6 | H4; H5 geográfico + exposição | vetos adversariais |
| 7–9 | LOO nome, LOO safra, grids single-knob | sensibilidades descritivas |
| 10–11 | métricas/atribuição; selo final | relatório + integridade |

Não há impressão de métricas intermediárias nem escolha humana entre blocos. Os resultados
ganham níveis de afirmação distintos:

- **P&L OOS positivo:** retorno líquido base >0 — afirma somente o fato histórico;
- **evidência OOS da estratégia:** P&L base >0 **e** primário H′ aprovado;
- **evidência de alpha climático:** anterior + componente D-064 positivo + H4 estendida
  aprovada + H5 geográfico morto.

Falha ou ausência de H4/H5 impede usar “alpha climático”, mesmo com curva positiva.

### 7.1 Portão concluído e resultado selado

`scripts/run_holdout_once.py` sem argumentos executa apenas o preflight, que compara código e
inputs com manifestos SHA-256 sem abrir parquets. D-072 encerrou os três requisitos técnicos:

1. ~~materializar controles diários confiáveis de H4~~ **feito em D-069**;
2. ~~congelar e materializar a geografia não produtiva de H5~~ **feito em D-070/D-071**;
3. ~~implementar o executor indivisível, registro civil e emissão atômica dos 12 artefatos~~
   **feito em D-072**.

Os sete inputs derivados têm caminhos fixos em `data/interim/holdout/`; não podem ser
substituídos por arquivos de desenvolvimento, dados atuais ou download ad hoc. O manifesto
versionado de fontes cobre exatamente `SPEC_FILES`; qualquer diferença de bytes bloqueia o
preflight. Após autorização humana exclusiva, a rodada foi executada em 27/07/2026 e selada:

| Condição pré-declarada | Resultado | Consequência |
|---|---:|---|
| H′, permutação exata unilateral | `p=0,0625` | passou |
| retorno líquido nominal base | `+16,97%` | P&L OOS positivo |
| componente climático D-064 | positivo | condição necessária, não suficiente |
| H4 estendida | falhou; `t=−1,03` | veta “alpha climático” |
| H5 geográfico | morreu; `p=0,5625` | não acionou o veto espacial |
| Sharpe de excesso ao risk-free | `−0,50` | sem evidência de habilidade |

O registro existente impede nova execução do pacote `v1`. Os valores canônicos e hashes dos
doze artefatos estão em
[`../data/reference/holdout_result_v1.json`](../data/reference/holdout_result_v1.json).
