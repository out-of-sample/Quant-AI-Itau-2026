# Protocolo de backtest

> Regras de execução do backtest, congeladas antes de rodar. Existem para que o resultado
> seja um teste da tese, e não um retrato do quanto conseguimos ajustar as regras até o
> gráfico ficar bonito.

---

## 1. Universo — construído point-in-time

O universo **não** é uma lista de tickers. É uma **função de `t`**:

> Uma ação está no universo em `t` se, e somente se: (i) estava sendo negociada na B3 em `t`
> segundo o COTAHIST; (ii) já se passaram 60 pregões do IPO; (iii) o ADTV dos últimos 21
> pregões supera o piso de liquidez; e (iv) ela tem exposição fundamentalista definida a
> pelo menos uma commodity do escopo.

**Por que 60 pregões pós-IPO**: os primeiros meses de um papel recém-listado têm dinâmica
distorcida (estabilização, lock-up, poeira do bookbuilding). Incluir esse período adiciona
ruído que nada tem a ver com a tese.

**Regra de deslistagem**: a ação **permanece** no backtest até a data efetiva de deslistagem,
com o último preço negociado. Não é apagada retroativamente — apagar é exatamente o viés de
sobrevivência que estamos combatendo (JBSS3, BRFS3, MRFG3 e STBP3 sumiram em 2025; ver
`02_DADOS.md` §4.1).

**Entregável obrigatório**: gráfico da **contagem de ativos elegíveis ao longo do tempo**.
Vai no relatório. É a prova visual de que o universo é dinâmico.

### Os dois backtests declarados

| | **A — Núcleo histórico** (primário) | **B — Universo amplo** (secundário) |
|---|---|---|
| Período | sinal 2015/16–2025; preços anteriores só como histórico auxiliar | 2021-2025 (~5 anos) |
| Universo | Método A PIT: AGRO3, BRFS3 e JBSS3 em 2015; SLCE3 entra em 2018 (D-033) | não materializado no Método A; nomes indiretos/pós-2021 só entram se fonte primária futura provar canal direto |
| Papel | **resultado principal** — tem histórico para sustentar afirmação | diagnóstico condicionado à existência de evidência direta; **não calibra nada** |
| Limitação | só dois nomes por ponta a partir de 2018; concentração é risco central | está **inteiramente dentro do holdout** e pode não existir sob o critério fundamentalista conservador |

---

## 2. Timing — a regra que impede lookahead

```
      D                    D+1
      │                    │
      ├─ dado com          ├─ EXECUÇÃO no CLOSE
      │  avail_date ≤ D    │  (preço de fechamento de D+1)
      │                    │
      └─ sinal calculado   └─ posição passa a valer
```

- O sinal de `D` usa **apenas** linhas com `avail_date ≤ D`.
- A execução acontece no **close de D+1**, nunca no close de `D`.

**Por que não executar no close de `D`**: o sinal foi calculado *com* a informação do dia `D`.
Executar no fechamento do mesmo dia assume que a decisão foi tomada e executada
instantaneamente no último instante do pregão. É a fonte de lookahead mais comum e mais
inocente-parecendo que existe. O custo de ser conservador aqui é baixo; o custo de estar
errado é o projeto inteiro.

---

## 3. Construção da carteira

| Regra | Valor | Motivo |
|---|---|---|
| Estrutura | **dollar-neutral long/short** | consequência direta da tese: produtores e processadores se movem em direções opostas sob o mesmo choque |
| Peso | proporcional ao score `S_{i,t}`, normalizado | sizing ∝ convicção, não binário |
| Cap por nome | 20% do bruto, **pendente de ratificação antes da carteira** | incompatível: um único long até 03/2018 exige 50% do bruto; depois, dois longs exigem 25% cada (D-033) |
| Rebalanceamento | mensal, com holding de 21 pregões | compatível com a hipótese pré-registrada de difusão lenta; ComexStat é apenas H1b *ex post* (D-026) |
| Cap de turnover | a definir na calibração (in-sample) | turnover alto come o alfa em nomes ilíquidos |
| Alavancagem | 1.0× bruto (0.5 long + 0.5 short) | sem alavancagem — não é onde está a contribuição |

---

## 4. Custos de transação

Modelados explicitamente. Custo subestimado é a forma mais fácil de inventar alfa.

| Componente | Tratamento |
|---|---|
| Corretagem + emolumentos B3 | taxa fixa por notional (ordem de ~0,03%) |
| **Slippage** | **proporcional à participação no ADTV** — quanto maior a ordem em relação ao volume diário do papel, maior o impacto |
| Aluguel (ponta short) | custo de aluguel do papel; **nomes sem lastro de aluguel são inelegíveis para short** |
| Robustez | rodar tudo de novo com **custo 2×** |

> ⚠️ **A ponta short é o ponto mais frágil da execução.** Vender a descoberto small caps
> agrícolas na B3 pode ser caro ou simplesmente impossível por falta de doador. Se a
> viabilidade do short não se sustentar, a alternativa é uma versão **long-only com hedge de
> índice** (long produtores, short futuro de Ibovespa), que é menos elegante mas operável.
> Essa variante deve ser reportada em paralelo, não escondida.

---

## 5. Métricas reportadas (todas, sempre — não só as boas)

| Categoria | Métricas |
|---|---|
| Retorno | retorno anualizado, retorno acumulado |
| Risco | volatilidade, **max drawdown**, tempo até recuperação, VaR/CVaR |
| Ajustado a risco | **Sharpe**, Sortino, Calmar |
| Qualidade do sinal | *hit rate*, *information coefficient* (IC), IC por cultura |
| Operacional | **turnover**, custo total pago, **capacidade estimada** |
| Atribuição | contribuição da ponta long × short, por commodity, por ano |
| Contra benchmark | vs. **Ibovespa** e vs. **CDI** — ambos declarados a priori |

> **Capacidade** (quanto capital a estratégia suporta antes de o alfa desaparecer) é a
> métrica que uma gestora de verdade olha primeiro e que trabalhos acadêmicos costumam
> omitir. Vamos reportá-la, mesmo que o número seja desconfortavelmente baixo.

---

## 6. O que torna este backtest reprodutível

1. **Semente aleatória fixa** em tudo que tem aleatoriedade (bootstrap, embaralhamentos).
2. **Dependências pinadas** com lockfile.
3. **Manifesto de dados** (`data/manifests/`): data de download, hash e vintage de cada
   pull — versionado no git, ao contrário dos dados brutos.
4. **Um comando** roda o pipeline inteiro, do dado bruto ao número final. Se o resultado do
   relatório não puder ser regenerado por um comando, ele não é um resultado — é uma
   anedota.

---

## 7. Disciplina do holdout

O período **2020-2025 é lacrado**. Enquanto o desenho não estiver congelado, ninguém do time
roda backtest nele — nem "só para dar uma olhada".

Rodamos **uma vez**. O resultado, qualquer que seja, vai para o relatório.

> Olhar o holdout e depois "ajustar um detalhezinho" o transforma em in-sample, e o projeto
> perde a única defesa forte que tem contra a acusação de overfitting. Não existe meio-termo:
> ou o holdout está lacrado, ou ele não existe.
