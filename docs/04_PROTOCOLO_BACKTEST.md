# Protocolo de backtest

> Regras de execução do backtest, congeladas antes de rodar. Existem para que o resultado
> seja um teste da tese, e não um retrato do quanto conseguimos ajustar as regras até o
> gráfico ficar bonito.

> **Estado após D-056:** a especificação econômica de D-053, a mecânica operacional de D-055
> e a contabilidade diária de D-056 foram congeladas sem consultar P&L. O motor em
> `backtest/engine.py` executa esses contratos sem rebalanceamento diário implícito e bloqueia
> o holdout antes do I/O. Nenhum parâmetro pode ser completado olhando resultados.

---

## 1. Universo — construído point-in-time

Uma ação só pode receber posição em `t` se, simultaneamente:

1. pertence ao universo econômico congelado em D-053;
2. estava sendo negociada na B3 segundo o COTAHIST;
3. já completou 60 pregões desde a primeira negociação observada;
4. seu ADTV da janela de 21 pregões encerrada em D é de ao menos **R$ 8 milhões**, com dia sem
   negócio contado como zero;
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
ordem. Se faltar close de execução ou saída sem evento terminal auditado, o bloco falha; não se
usa o próximo preço nem se descarta o nome silenciosamente.

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
- O horizonte primário é de **21 intervalos de pregão close-to-close**.

### 2.1 Grade operacional congelada em D-055

Para cada safra `Y/Y+1`:

1. a âncora é **7 de janeiro de `Y+1`**, quando dezembro completo já venceu o lag climático de
   sete dias;
2. `D₀` é o primeiro pregão B3 em ou após a âncora; `X₀`, o pregão seguinte, é a execução;
3. `Xₖ₊₁` é o 21º pregão posterior a `Xₖ`; `Dₖ₊₁` é o pregão imediatamente anterior;
4. o close de `Xₖ₊₁` encerra o bloco anterior e inicia o próximo. O retorno dessa transição é
   contado uma única vez; não há *cohorts* sobrepostos;
5. o primeiro `Dₖ` da grade em ou após **7 de setembro** é a última decisão da safra. Seu bloco
   termina 21 pregões depois e a carteira fica zerada até janeiro seguinte;
6. informação publicada entre D e X não altera a ordem já formada.

A grade cobre, em sequência única, soja, milho safrinha e a maturação da cana. Ela não depende
de retorno, fechamento de mês de mercado ou data de divulgação da CONAB. O painel estatístico
de 21 pregões e a carteira negociável usam os mesmos blocos; isso impede que sobreposição
fabrique observações ou alavancagem.

### 2.2 Contabilidade diária congelada em D-056

- os pesos-alvo são instalados no close da execução e viram quantidades de um índice de
  retorno total; essas quantidades permanecem fixas até o próximo rebalanceamento;
- o drift intrabloco é econômico e **não** dispara ordem. Repetir os pesos diariamente seria
  uma estratégia diferente, com turnover oculto;
- em `(t−1,t]`, calcula-se primeiro o P&L por nome e o aluguel da posição antiga; no close `t`,
  marca-se a posição e só então se negocia contra o novo alvo;
- o alvo é peso sobre o patrimônio pós-custo. O motor resolve a equação implícita do custo para
  que os pesos efetivos depois da ordem coincidam com os alvos;
- a simulação é autofinanciada a partir de R$500 mil. Ordens e participação usam o patrimônio
  corrente; não há reset do AUM por bloco;
- a soma da atribuição por nome fecha com o P&L bruto, e a identidade diária obrigatória é
  `Δpatrimônio = P&L bruto − aluguel − custo spot`.

O livro separa `gross_traded = Σ|ordem|/patrimônio pré-trade` de
`turnover_one_way = gross_traded/2`. Na transição existe uma única ordem líquida contra a
posição marcada; não se cobra uma saída e uma entrada artificiais sobre o mesmo notional.

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

### 3.1 Composição executável do score

Para cada grão e nome elegível em D:

`G_i(D) = −[E_i,soja(D)·Shock_soja(D) + E_i,milho(D)·Shock_milho(D)]`.

- cultura cuja janela ainda não começou contribui zero, **sem renormalizar** `E`;
- depois do fim da janela, usa-se o choque final da safra;
- `NaN`, buraco de cobertura, vintage ausente ou erro técnico nunca vira zero: falha alto;
- o choque nacional usa pesos CONAB da safra anterior disponível, como em D-028.

Para a SMTO3, o choque de maturação é a média das cinco UFs de D-050 ponderada pelos mesmos
pesos CONAB anteriores. Exigem-se GO, MG, MS, PR e SP válidos. A escala é **1:1 em z-score**, sem
normalização por volatilidade ou coeficiente estimado. O cap de 15% é o único *haircut*: não há
multiplicador adicional. Antes do primeiro prefixo junho–agosto disponível, SMTO3 fica fora do
score e do *demean*; não recebe zero artificial.

O teste primário faz *demean* somente nos quatro grãos válidos/elegíveis. A carteira usa esses
grãos e acrescenta SMTO3 quando seu canal está ativo. Em ambos os casos, é obrigatório haver ao
menos um produtor (AGRO3/SLCE3) e um processador (BRFS3/JBSS3). Se faltar qualquer lado, o bloco
inteiro fica zerado; SMTO3 não substitui o núcleo. Caps insuficientes reduzem o bruto dos dois
lados simetricamente pelo *water-filling* já testado.

### 3.2 Inferência primária exata

Em cada bloco, score e retorno forward são demeanados na seção transversal dos quatro grãos.
Para cada ano-safra `k`, calcula-se uma inclinação:

`β_k = Σ(x·y) / Σ(x²)`, usando todos os blocos válidos daquele ano.

A estatística é a média com **peso igual** dos cinco `β_k` de 2020/21–2024/25. Sob a nula,
enumeram-se exatamente os `2⁵ = 32` *sign flips* dos clusters ano-safra. O p-valor unilateral é
a fração de estatísticas permutadas maiores ou iguais à observada; não há semente, aproximação
assintótica nem “+1” de Monte Carlo. H′ passa somente se média `>0` e `p≤0,10`.

As cinco safras são obrigatórias e todo bloco pré-declarado precisa de score e preços válidos.
Falta não é descartada: bloqueia o veredito até a fonte ou evento terminal ser auditado. A
dependência dentro da safra, inclusive por sinais persistentes, é preservada ao inverter o
cluster inteiro.

---

## 4. Custos de transação e capacidade

O patrimônio de referência é **R$ 500 mil** e a exposição bruta, 1,0×. O piso de ADTV de R$ 8
milhões não veio de retorno: ele garante que a pior reversão permitida de um grão, de +40% para
−40% (`|Δw|=0,80`), negocie no máximo 5% do ADTV (`400 mil / 8 milhões`).

O custo à vista por ordem no cenário-base, em bps do notional, é:

`c(p) = 3,5 + 2 + 5 + 10·sqrt(p/1%)`, para `0 < p ≤ 5%`,

onde `p=|Δw|·AUM/ADTV21`. Os 3,5 bps arredondam para cima a tarifa vigente de ações da B3
(3,0 bps em operação regular de baixo volume; 3,2 no leilão de fechamento); 2 bps são hipótese
conservadora de corretagem histórica; 5 bps representam spread/execução e a raiz quadrada é a
hipótese de impacto. O COTAHIST não traz livro de ofertas, logo slippage é modelo declarado,
não dado observado. Fontes: [tarifas de ações B3](https://www.b3.com.br/pt_br/produtos-e-servicos/tarifas/listados-a-vista-e-derivativos/renda-variavel/tarifas-de-acoes-e-fundos-de-investimento/a-vista/)
e [cotações históricas B3](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/).

### 4.1 Ponta short

Em D, usa-se somente o Boletim Diário da B3 já público. Cada short precisa ter:

1. contrato/negócio positivo em alguma modalidade nos cinco pregões anteriores;
2. posição limitada a 1% do estoque total alugado observado;
3. taxa-base igual a `max(taxa PIT observada, 5% a.a.)`, acrescida da tarifa B3
   `clip(20%·taxa, 2,5 bps, 70 bps a.a.)` e de 1% a.a. de intermediação.

Sem evidência PIT para qualquer short necessário, **não se abre o bloco inteiro**. Não se
redistribui para outro short nem se transforma o cenário de custo zero em operação possível.
O estoque é proxy de profundidade, não prova de oferta na corretora; recalls e garantias seguem
como limitação. Fontes: [regras do empréstimo B3](https://www.b3.com.br/pt_br/produtos-e-servicos/emprestimo-de-ativos/informacoes.htm)
e [tarifas do empréstimo B3](https://www.b3.com.br/pt_br/produtos-e-servicos/tarifas/tarifas-de-emprestimo-de-ativos/).

Na contabilidade D-056, a taxa observada em D permanece fixa no bloco e acumula
`taxa all-in/252` em cada um dos 21 intervalos. O aluguel incide sobre o short marcado no início
do intervalo. No close de transição, o último accrual pertence à posição antiga; a nova começa
no intervalo seguinte. A liquidação final usa o ADTV conhecido no pregão imediatamente
anterior; entradas e transições usam o ADTV encerrado em D.

**Contrato de dados implementado em D-057.** A tabela de negócios registrados mantém
`ref_date`, `avail_date`, ticker/ISIN/modalidade, contratos, quantidade, notional e taxas
doadora/tomadora; somente contratos **e** quantidade positivos provam negociação. A posição em
aberto mantém modalidades e linha `Total`, cuja soma é reconciliada. Para decisão no close D:

1. os cinco boletins de negócios de D−5 a D−1 precisam estar disponíveis e atestados por
   CSV + manifesto (tabela, data, bytes, SHA-256 e contagem);
2. a posição Total de D−1 precisa ter a mesma atestação;
3. usa-se a taxa **doadora média ponderada** do dia mais recente com negócio;
4. `estoque_brl = quantidade_total(D−1) × close_COTAHIST(D)`;
5. o gate de 1% usa `|peso_short| × patrimônio_real_pré-ordem`, inclusive em transições.

Arquivo/manifesto ausente ou divergente é erro de dado e falha alto; ticker ausente num arquivo
atestado equivale a zero. Ausência de negócio recente ou capacidade insuficiente zera o bloco
inteiro, com reason code. A distinção impede que taxa antiga repetida pela B3 vire falsa
disponibilidade e impede que o gate use R$500 mil depois de o patrimônio ter derivado.

O painel COTAHIST fornece também o indicador explícito de negociação. Se um alvo novo não
negociou no close de execução, o bloco inteiro fica zerado; se uma posição já aberta não
negociou no close de saída/transição, o motor falha alto em vez de simular liquidação. Retorno
total observado menor que −100% também falha alto, pois inverteria o sinal econômico da
posição e denuncia erro de ajuste ou de dado.

**Bloqueio empírico e sua resolução (D-058).** A infraestrutura acima está validada em arquivos
BDI reais de 2026, mas a B3 pública não preserva esses dois painéis para 2018/19 (R27): o
histórico gratuito antigo retinha 10 dias e o export atual serve só o último pregão. Sem série
histórica, o custo do short é resolvido por **proxy conservadora declarada** (D-058), não por
medição: para datas sem BDI real, `build_proxy_borrow_state` fornece taxa 0 → piso 5% + tarifas +
2×, disponibilidade pela elegibilidade de ADTV, profundidade não vinculante a R$500 mil, e todo
bloco carrega reason `proxy`. A proxy é corroborada pelo único snapshot real (taxas observáveis
abaixo do piso). O custo passa a ser premissa, não demonstração de investibilidade histórica do
short — declarado como tal. Aplicar taxa atual ao passado, interpretar ausência como zero ou
remover o gate seria outra coisa (alteração silenciosa), e não é o que se fez.

### 4.2 Cenários e capacidade

| Cenário | Custos monetários | Regras de investibilidade |
|---|---|---|
| zero | zero | ADTV, participação, estoque e disponibilidade continuam valendo |
| base | fórmulas acima | contrato primário |
| 2× | dobra custo à vista e aluguel all-in | mesmos sinais e elegibilidade |

Não há cap de turnover: toda mudança de peso é executada, medida e paga. O portfólio é tratado
como long/short autofinanciado; remuneração de caixa, margem e spread de financiamento não são
modelados e serão declarados.

Por bloco, a capacidade é o menor entre:

- vista: `min_i 0,05·ADTV_i/|Δw_i|`;
- aluguel: `min_short 0,01·estoque_alugado_i/|w_i|`.

Reportam-se mínimo, percentil 10 e mediana. A estratégia só será chamada de investível no
patrimônio de referência se a capacidade for de ao menos R$ 500 mil em todos os blocos
operados. A tabela de tarifas atual é hipótese uniforme, não reconstrução das regras históricas.

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

1. teste primário exato com 32 permutações, sem semente; sementes fixas nos bootstraps de
   robustez;
2. dependências pinadas e manifestos de dados versionados;
3. um comando reproduz cada artefato a partir das entradas locais;
4. teste-canário de D+1, inclusive feriado e fim de semana;
5. teste de fronteira para não duplicar o close de execução;
6. teste de elegibilidade usando informação somente até D;
7. teste de caps, bruto, dollar-neutralidade e carteira zerada sem produtor+processador;
8. teste de custo zero, base, 2×, participação, aluguel, capacidade e turnover;
9. teste de deslistagem, ausência de preço e bloco que cruza a fronteira temporal;
10. bloqueio técnico do holdout por padrão.

---

## 7. Disciplina do desenvolvimento e do holdout

O desenvolvimento operacional compreende as safras **2015/16–2018/19**, com todas as
execuções e saídas até 31/12/2019, e está **queimado para a direção** por D-043. Na Fase 4, ele
serve para validar mecânica, invariantes, custos, turnover e atribuição — seu P&L não confirma
H′ nem autoriza alterar direção, score ou parâmetros.

Há uma restrição de materialização registrada em R26/D-056: o peso nacional exige a safra
CONAB anterior, mas o painel de vintages começa em 2017/18. Logo, somente 2018/19 é computável
com dados reais sob o contrato atual. As três safras anteriores não recebem equal-weight, PAM,
peso futuro ou backfill. A álgebra completa é validada por testes sintéticos; o único smoke test
real admissível no desenvolvimento é 2018/19 e continua sem valor confirmatório para H′.

A safra **2019/20 é uma zona de transição excluída**: seus retornos cairiam em 2020, mas ela não
pertence às cinco safras congeladas do holdout. Bloco que cruza 31/12/2019 é rejeitado por
inteiro, nunca truncado.

O holdout de retornos 2020–2025 permanece lacrado mesmo após D-053. “Desenho econômico
congelado” não significa “permissão para olhar”: a abertura só ocorre na Fase 6, depois de
fechar a Fase 4.0, implementar e testar o motor e pré-registrar a suíte de robustez.

O holdout é exclusivamente 2020/21–2024/25, com decisões/execuções não anteriores a
01/01/2020 e saídas até 31/12/2025. O motor deve falhar **antes de ler retornos** sem uma
autorização explícita e exclusiva da Fase 6. A liberação não inclui 2019/20 nem 2025/26. A
rodada ocorre uma vez, com hash da especificação e manifestos, e o resultado, qualquer que
seja, vai para o relatório.
