# Protocolo de backtest

> Regras de execução do backtest, congeladas antes de rodar. Existem para que o resultado
> seja um teste da tese, e não um retrato do quanto conseguimos ajustar as regras até o
> gráfico ficar bonito.

> **Estado após D-053/D-054:** a hipótese H′, o universo econômico, a direção, o sizing, os
> caps, o lag D+1 e o horizonte de 21 pregões estão congelados em
> `backtest/strategy_spec.py`. A auditoria de transição para a Fase 4 mostrou que a mecânica
> operacional ainda não está completamente especificada. Calendário de decisões, composição
> dos scores, casos de universo incompleto, inferência por permutação, custos e fronteiras
> temporais serão fechados na **Fase 4.0**, sem consultar P&L, antes de implementar o motor.

---

## 1. Universo — construído point-in-time

Uma ação só pode receber posição em `t` se, simultaneamente:

1. pertence ao universo econômico congelado em D-053;
2. estava sendo negociada na B3 segundo o COTAHIST;
3. já completou 60 pregões desde a primeira negociação observada;
4. seu ADTV dos 21 pregões anteriores supera o piso de liquidez ainda a congelar na Fase 4.0;
5. sua exposição e seu score estavam disponíveis em `t`.

O universo econômico é:

| Papel | Canal operacional | Uso |
|---|---|---|
| AGRO3, SLCE3 | grãos, produtor sob H′ (`Q>P`) | teste primário e carteira |
| BRFS3, JBSS3 | grãos, processador/insumo sob H′ | teste primário e carteira |
| SMTO3 | cana, maturação→ATR, evidência mais fraca | somente carteira, satélite capado em 15% |

O **teste estatístico primário** usa apenas os quatro nomes de grãos. A **carteira negociável**
inclui os cinco nomes. O antigo “universo amplo” não é um segundo backtest prometido: só poderá
aparecer como robustez identificada se surgir evidência fundamental direta admissível, nunca
porque nomes adicionais melhoraram o resultado.

**Regra de deslistagem:** a ação permanece no histórico até o último pregão efetivo; não é
apagada retroativamente. A elegibilidade de uma ordem executada em D+1 usa apenas informação
conhecida até D — o volume ou o status final de D+1 não podem decidir retrospectivamente a
ordem.

**Entregável obrigatório:** gráfico da contagem de ativos elegíveis ao longo do tempo, junto
da razão de cada entrada/saída. É a prova visual contra survivorship e backfill.

---

## 2. Timing — a regra que impede lookahead

```
      D                                  primeiro pregão após D
      │                                         │
      ├─ dados com avail_date ≤ D               ├─ EXECUÇÃO no CLOSE
      ├─ elegibilidade medida até D              └─ posição passa a valer
      └─ score e pesos-alvo calculados
```

- “D+1” significa o **primeiro pregão B3 estritamente posterior**, não o dia civil seguinte.
- A execução acontece no close desse pregão; nunca no mesmo fechamento que gerou o sinal.
- O retorno começa depois de incorporado o preço de execução, sem contar o mesmo close duas
  vezes.
- O horizonte primário é de **21 pregões**.

A Fase 4.0 ainda precisa tornar executável o calendário de geração do sinal: datas de decisão,
efeito de nova informação durante uma posição, vencimento e tratamento de posições
sobrepostas. “Mensal” não é especificação suficiente e não pode ser completado depois de ver
o P&L.

---

## 3. Construção da carteira — decisões já congeladas

| Regra | Contrato D-053 | Consequência |
|---|---|---|
| Direção de grãos | negativo de `E·Shock` | estresse reduz score do produtor e eleva score do processador sob H′ |
| Direção da cana | `+Shock_maturação` para SMTO3 | canal separado; não entra no teste estatístico primário |
| Sizing | proporcional ao score demeanado na seção transversal | regra simples, determinística e sem retorno como entrada |
| Estrutura | dollar-neutral | `Σw=0`; isso **não** garante neutralidade a mercado, fatores, FX ou commodities |
| Bruto | 1,0×, alvo 0,5 long + 0,5 short | reduz apenas quando os caps tornam um lado inviável |
| Cap por grão | `|w_i| ≤ 0,40` | resolve R19 sem fingir diversificação inexistente |
| Cap da SMTO3 | `|w_i| ≤ 0,15` | haircut pela evidência fraca e limitações de ATR/hedge |
| Pesos do choque | CONAB da safra anterior disponível | proíbe equal-weight oportunista |
| Execução/horizonte | D+1 / 21 pregões | definidos antes do holdout |

O algoritmo de water-filling e os invariantes acima vivem em `backtest/strategy_spec.py` e
são travados por testes. Exposições residuais a mercado, fatores e commodities são resultados
diagnósticos: não alteram os pesos congelados.

### 3.1 Graus de liberdade que a Fase 4.0 precisa fechar

| Tema | Decisão ainda necessária — sempre sem P&L |
|---|---|
| Calendário | datas de decisão, encerramento, nova informação e sobreposição de horizontes |
| Score | combinação soja+milho; escala comum com cana; ausências; conjunto usado no demean |
| Universo incompleto | zerar, reduzir bruto ou manter posição relativa quando falta um lado econômico |
| Liquidez | piso numérico de ADTV e convenção de janela, escolhidos por operabilidade observável |
| Custos | patrimônio de referência, taxas, slippage, aluguel e capacidade, com fontes/cenários |
| Inferência | estatística, unidade permutada, enumeração/semente, p-valor e dados ausentes |
| Partição temporal | datas exatas de dev/holdout e eventos que cruzam a fronteira |
| Segurança | motor nega o holdout por padrão; somente a Fase 6 pode liberá-lo deliberadamente |

Esses itens pertencem à Fase 4, não ao registro de pendências transversais. Nenhuma escolha
pode ser feita para aumentar Sharpe, significância ou retorno.

---

## 4. Custos de transação e capacidade

Custos são parte do resultado, não um desconto decorativo aplicado no fim. O modelo deve
separar:

| Componente | Tratamento exigido |
|---|---|
| Corretagem, emolumentos e demais taxas | taxa por notional negociado, com valor e fonte congelados na Fase 4.0 |
| Slippage | função explícita da participação da ordem no ADTV; patrimônio/notional declarado |
| Aluguel da ponta short | cenário histórico quando houver fonte válida; na ausência, cenários conservadores declarados, nunca taxa atual retroaplicada como se fosse PIT |
| Indisponibilidade de aluguel | política determinística congelada antes do P&L; não remover apenas operações perdedoras |
| Robustez | caso-base, custo zero como decomposição e custo 2× como stress |
| Capacidade | capital máximo compatível com o limite pré-fixado de participação no ADTV |

A antiga proposta de uma carteira long-only com hedge de índice **não é substituto automático**:
é uma estratégia diferente e não pode ser promovida depois de observar que o short foi ruim.
Se for mantida, será apenas análise operacional identificada e pré-registrada antes do holdout.

---

## 5. Métricas reportadas — inclusive as ruins

| Categoria | Métricas |
|---|---|
| Retorno | acumulado e anualizado, sempre bruto e líquido de custos |
| Risco | volatilidade, max drawdown, tempo de recuperação, VaR/CVaR |
| Ajustado a risco | Sharpe, Sortino e Calmar |
| Qualidade do sinal | estatística primária D-053, hit rate e IC apenas quando identificáveis |
| Operacional | turnover, custo total, participação no ADTV e capacidade |
| Atribuição | long/short, nome, cultura/canal e ano-safra; SMTO3 separada |
| Exposições | beta de mercado, FX, commodities e fatores NEFIN, sem chamá-las de neutralizadas |
| Benchmarks | Ibovespa e CDI, ambos declarados a priori |

O N efetivo é o número de anos-safra/clusters relevante para a inferência, não a quantidade
de retornos diários. Retornos sobrepostos não fabricam novas observações independentes.

---

## 6. Reprodutibilidade e testes obrigatórios do motor

1. semente fixa em bootstrap e permutações;
2. dependências pinadas e manifestos de dados versionados;
3. um comando reproduz cada artefato a partir das entradas locais;
4. teste-canário de D+1, inclusive feriado e fim de semana;
5. teste de fronteira para não duplicar o close de execução;
6. teste de elegibilidade usando informação somente até D;
7. teste de caps, bruto, dollar-neutralidade e redução de bruto quando um lado é inviável;
8. teste de custo zero, custo conhecido e turnover por mudança de pesos;
9. teste de deslistagem, ausência de preço e evento que cruza a fronteira temporal;
10. bloqueio técnico do holdout por padrão.

---

## 7. Disciplina do desenvolvimento e do holdout

O desenvolvimento termina em 2019 e está **queimado para a direção** por D-043. Na Fase 4,
ele serve para validar mecânica, invariantes, custos, turnover e atribuição — seu P&L não
confirma H′ nem autoriza alterar direção, score ou parâmetros.

O holdout de retornos 2020–2025 permanece lacrado mesmo após D-053. “Desenho econômico
congelado” não significa “permissão para olhar”: a abertura só ocorre na Fase 6, depois de
fechar a Fase 4.0, implementar e testar o motor e pré-registrar a suíte de robustez.

O motor deve falhar alto ao receber datas do holdout sem uma autorização explícita e exclusiva
da Fase 6. A rodada ocorre **uma vez** e o resultado, qualquer que seja, vai para o relatório.
