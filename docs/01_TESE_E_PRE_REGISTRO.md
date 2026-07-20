# Tese, formalização e pré-registro de hipóteses

> **Status**: v1 — congelado antes de qualquer contato com dados de retorno.
> **Regra de ouro deste documento**: tudo aqui foi escrito *antes* de rodar o primeiro
> backtest. Se mudarmos algo depois de ver resultados, a mudança tem que ser registrada
> em `07_RISCOS_E_DECISOES.md` com data e justificativa. Um plano que muda silenciosamente
> depois de ver o resultado não é um plano, é overfitting narrado.

> **Estado posterior preservado sem reescrever o pré-registro.** A formulação abaixo é o
> registro original. D-037–D-043 mostraram que o canal de preço não teve suporte e que a
> reação das ações foi contrária à direção proposta. D-044 abriu uma hipótese nova,
> Q-dominante, sem inverter retroativamente este documento. A extensão de algodão foi
> pré-registrada em D-048 e rejeitada em D-049. O desenho operacional vigente deve ser lido no
> log de decisões e no `00_PLANO_MESTRE.md`; o holdout de retornos permanece lacrado.

---

## 1. A tese em uma frase

> Choques climáticos nas regiões produtoras brasileiras carregam informação sobre a oferta
> futura de commodities agrícolas, e essa informação chega ao preço das ações da B3 **com
> defasagem e de forma heterogênea entre empresas** — porque o mesmo choque é *bom* para
> quem vende a commodity e *ruim* para quem a compra como insumo. Exploramos a defasagem
> (timing) e a heterogeneidade (cross-section), e usamos o dado de comércio exterior como
> confirmação independente de que o choque de fato se materializou em oferta física.

---

## 2. O erro que quase cometemos (e por que a tese não é o óbvio)


A formulação ingênua da tese seria:

> "Detectamos seca → a safra vai cair → *vende* ações do agro."

**Isso está economicamente errado**, e é importante que o time entenda por quê antes de
escrever uma linha de código. O Brasil é um dos maiores exportadores mundiais de soja,
milho, açúcar, café e carne. Uma quebra de safra brasileira não é um evento local — é um
**choque de oferta global**, que *empurra o preço internacional da commodity para cima*.

Para uma empresa que **vende** a commodity (SLC Agrícola, São Martinho, BrasilAgro), uma
seca tem dois efeitos de sinais opostos:

| Canal | Efeito de uma seca | Impacto no lucro do produtor |
|---|---|---|
| **Quantidade** | produz menos sacas | negativo |
| **Preço** | preço internacional sobe | **positivo** |

O efeito líquido é **ambíguo** e depende de quanto da lavoura *dela* foi atingida versus
quanto do agregado global foi atingido. Um produtor cuja lavoura escapou da seca enquanto o
resto do país secou é o grande vencedor: vende o mesmo volume a um preço muito maior.

Já para uma empresa que **compra** a commodity como insumo — um frigorífico (JBS, BRF,
Marfrig, Minerva) compra milho e farelo de soja para ração — o canal bruto é negativo: o
custo do insumo sobe e comprime a margem. Hedge, repasse de preço e diversificação podem
atenuar esse efeito; por D-034, eles não são presumidos nem ignorados sem fonte PIT.

### A consequência: onde está o alfa

O alfa **não** está em prever a direção do setor agro como bloco. Está na **dispersão
cross-seccional** que o choque pode criar dentro do setor: o mesmo evento climático tem
canais diferentes para produtores e processadores. A direção líquida dos produtores é o
objeto da Fase 3.1, não uma premissa já resolvida. Um índice setorial agregado
mistura os dois e cancela o efeito — que é exatamente a razão pela qual essa informação
pode continuar não-arbitrada.

Isso transforma a estratégia de uma **aposta direcional** (frágil, fácil de estar errada,
correlacionada com o mercado) em uma **estratégia de valor relativo dentro do setor**
(long produtores / short processadores num choque negativo de oferta, e o inverso numa
supersafra), que é dollar-neutral por construção e mais defensável do que uma aposta
direcional no setor.

Essa carteira é **dollar-neutral por construção**, não neutra a mercado. Beta, tamanho,
liquidez, câmbio e commodity podem permanecer diferentes entre as pontas; serão medidos e,
quando viável, neutralizados explicitamente. H4 testa se o retorno residual ainda é apenas
exposição reembalada.

> **Formalmente**: não modelamos `E[retorno do agro | clima]`. Modelamos
> `E[retorno da empresa i | clima] = f(exposição líquida da empresa i à commodity c)`.

Essa reformulação é o principal ativo intelectual do projeto e o que responde ao critério
"Conceito da estratégia" (20%): a ineficiência não é "ninguém olha o tempo" (todo mundo
olha), é que **traduzir o tempo em posicionamento relativo exige juntar três bases
heterogêneas — grade meteorológica, mapa de produção agrícola e composição de receita/custo
das empresas — e essa agregação é cara o suficiente para não estar no preço no dia seguinte.**

---

## 3. Formalização do sinal

Seja:

- `c ∈ C_primário = {soja, milho 2ª safra}` — D-023; outras culturas são especificações
  secundárias e não substituem o resultado primário
- `i ∈ U_t` — empresa no universo elegível na data `t` (universo **dinâmico**, ver §7)
- `Shock_{c,t}` — índice de estresse climático da cultura `c`, agregado nacionalmente,
  observável em `t` (respeitando o lag de publicação — ver `02_DADOS.md`)
- `E_{i,c}` — exposição líquida da empresa `i` à commodity `c`, em `[-1, +1]`:
  `+1` = produtor puro (ganha quando o preço de `c` sobe);
  `-1` = consumidor puro do insumo (perde quando o preço de `c` sobe)

**Sinal bruto por empresa:**

```
S_{i,t} = Σ_c  E_{i,c} · Shock_{c,t}
```

> **Estado após D-043/D-053.** Esta formulação-base preserva o canal histórico de preço/insumo,
> que foi falsificado no desenvolvimento e continua travado como registro. A estratégia H′ é
> uma camada operacional separada: usa `−E·Shock` nos grãos porque o dano de volume próprio
> dominou (`Q>P`) e `+Shock_maturação` para a SMTO3. A mudança, seus limites e o fato de o dev
> estar queimado para a direção estão registrados em D-044–D-053.

**Nota de sinal (importante):** `Shock` é definido como **estresse**. Na álgebra-base, `E>0`
recebe score positivo; `tests/test_signal_sign.py` impede que a hipótese histórica seja
reescrita. Isso não conflita com H′: `backtest/strategy_spec.py` aplica explicitamente o sinal
operacional negativo nos grãos e mantém a cana como submodelo de direção própria.

### 3.1 O componente climático `Shock_{c,t}`

```
Shock_{c,t} = Σ_u  w_{u,c,t} · Shock_{u,c,t}(janela fenológica de c)
```

- `u` — UF do suporte primário congelado em D-023; dentro dela, o clima municipal é ponderado
  pela PAM/IBGE mais recente já publicada, sobre malha municipal fixa de 2013 (D-024)
- `w_{u,c,t}` — **peso de produção** da UF segundo a safra CONAB anterior já encerrada
  (nunca a safra corrente cuja revisão queremos prever; ver §6.2)
- `Shock_{u,c,t}` — anomalia climática padronizada na UF. O caso primário é déficit de
  precipitação CHIRPS; temperatura é robustez. A normalização usa a
  **climatologia do mesmo trecho da janela**, calculada apenas com anos anteriores a `t`
  (climatologia expanding, nunca a média do período inteiro — isso também é lookahead)
- **Janela fenológica**: a anomalia só é contada durante a fase crítica da cultura
  (floração/enchimento de grão), que é quando o estresse hídrico de fato destrói
  produtividade. Chuva em julho no Mato Grosso é irrelevante para a soja porque não há soja
  no campo. Essa janela vem do calendário agrícola (CONAB/Embrapa/ZARC) e é **definida a
  priori por agronomia, não escolhida por grid search no retorno** — ver
  `09_FENOLOGIA_E_LIMIARES.md`.

> 🔴 **O sinal não é linear nem tem direção única em todas as culturas.** Três exceções
> confirmadas na literatura agronômica, que precisam estar no modelo — não são detalhes:
>
> - **Cana**: seca no **verão** (crescimento, nov-abr) reduz tonelagem — ruim. Seca no
>   **inverno** (maturação, mai-set) **aumenta o ATR/sacarose** — *boa*. Um z-score linear
>   aplicado à cana o ano inteiro teria **o sinal trocado em metade do tempo**.
> - **Café**: a florada (set/out) exige **seca seguida de retomada de chuva**. Menos chuva
>   nessa janela **não é linearmente ruim** — o gatilho é a *sequência*, não o nível.
> - **Milho safrinha**: o efeito é fortemente **assimétrico no tempo** — déficit *no*
>   embonecamento custa −40% a −50% de produtividade; o mesmo déficit depois custa −10% a
>   −20%. Exige janela estreita e bem posicionada, não média sazonal larga.
>
> Consequência: `Shock_{c,t}` é definido **por cultura e por fase**, com direção
> explicitamente declarada em cada uma. Um sinal linear único para todas as culturas está
> errado, e produziria um resultado medíocre e inexplicável.

### 3.2 O componente de exposição `E_{i,c}`

Estimado por **dois métodos independentes**, que se cruzam:

**Método A — fundamentalista (prior, "de baixo para cima")**
Direção causal, materialidade ordinal e composição por cultura, extraídas de divulgações da
própria empresa (CVM/SEC, documentos de oferta e RI). A regra exata está congelada em
`13_MATRIZ_EXPOSICAO.md`: `E = direção × materialidade × peso da cultura`. Os pesos usam
receita/custo por cultura; volume ou área são o fallback; cesta soja+milho não separável usa
divisão igual explicitamente marcada. Cada vintage carrega `ref_date` e `avail_date` e nunca é
preenchido para trás. *Vantagem*: interpretável, estável, auditável e não circular. *Custo*:
baixa frequência, escala ordinal e exclusão conservadora de empresas ambíguas.

**Método B — estatístico (validação, "de cima para baixo")**
Beta rolling da ação contra o retorno do futuro da commodity, **controlando por Ibovespa e
USDBRL** (sem esse controle, capturamos só beta de mercado e de câmbio, já que exportadora
sobe com dólar):

```
r_{i,t} = α + β_mkt·r_IBOV,t + β_fx·r_USDBRL,t + Σ_c γ_{i,c}·r_{fut c,t} + ε
```
`γ_{i,c}` estimado em janela móvel (ex. 252 dias) → normalizado para `[-1,+1]`.
*Vantagem*: automatizável, atualiza sozinho. *Risco*: ruidoso, endógeno, e pode capturar
correlação espúria.

**Como usamos os dois**: A é o prior; B é o teste de sanidade.
**A discordância entre A e B é informação, não ruído** — se a empresa se declara produtora
mas o mercado a precifica como consumidora (ou vice-versa), isso vai para o relatório como
achado. Registramos a matriz de discordância explicitamente.

**Decisão pré-registrada**: o resultado **primário** usa o Método A (exposição
fundamentalista, point-in-time e auditável). O Método B entra como **teste de robustez**, não como
o resultado principal. Motivo: `E` estimado por regressão dos próprios retornos cria uma
dependência circular entre o sinal e o alvo que enfraquece a interpretação causal.

### 3.3 A camada intermediária: a revisão da estimativa de safra da CONAB

Entre o choque climático (causa) e o preço da ação (efeito) existe um elo intermediário que
é **observável, quantificável e — o mais importante — tem data de publicação conhecida**:
a revisão da estimativa oficial de safra.

A CONAB publica **12 levantamentos** ao longo de cada safra, e o arquivo público
`LevantamentoGraos.txt` preserva **todas as estimativas anteriores** — ou seja, é um painel
de *vintages* verdadeiro. Exemplo (soja, Mato Grosso, mil toneladas):

| Safra | 1º Lev. | 4º Lev. | 6º Lev. | 12º Lev. | Revisão total |
|---|---|---|---|---|---|
| 2023/24 (seca) | 44.348 | 40.200 | 37.568 | 40.420 | **−15% do 1º ao 6º** |
| 2022/23 (boa) | 41.146 | 42.534 | 43.903 | 46.906 | **+14%** |

Revisões dessa magnitude são eventos materiais para uma empresa cuja receita depende do
volume e do preço da commodity.

**Isso reformula a cadeia causal do projeto de forma mais forte e mais testável:**

```
choque climático  →  revisão da estimativa CONAB  →  preço da commodity / ação
   (t)                (publicada em t+k,               (reprecificação)
                       data conhecida)
```

Duas consequências metodológicas importantes:

**(a) A hipótese central fica diretamente falsificável.** A pergunta deixa de ser a vaga
"o clima afeta as ações?" e passa a ser a específica: **o choque climático observado prevê a
revisão que a CONAB vai publicar?** Se prevê, temos um sinal antecedente de uma informação
que o mercado só vai receber semanas depois, num evento datado. Se não prevê, a tese está
errada e sabemos disso cedo, com pouco código escrito.

**(b) Permite um estudo de evento.** As datas de publicação dos levantamentos são conhecidas
(mensais, em torno do dia 15). Podemos medir o retorno anormal das ações **na janela ao redor
da publicação**, condicionado ao sinal climático prévio. Isso isola a reprecificação de uma
forma que uma regressão de retornos diários não consegue.

**Limitações desta camada, declaradas desde já:**

1. **O painel de vintages só começa na safra 2017/18** — são ~9 safras. A série histórica
   longa da CONAB (desde 1976/77) traz apenas o número **final**, sem os vintages. Isso
   limita severamente o poder estatístico desta camada específica (ver `05_SUITE_ROBUSTEZ.md`
   §6 sobre N efetivo).
2. **O arquivo não traz a data de publicação de cada levantamento** — só o número (1 a 12).
   R10/D-017 resolveram o carimbo com calendário curado ano a ano, sem interpolação. As poucas
   datas antigas com evidência única continuam como dívida de proveniência PT-005.
3. **O desfecho é por UF, não por município.** O clima primário usa CHIRPS p05 (~5 km),
   agregado por município e ponderado pela PAM antes de chegar à UF (D-027/D-028). Isso reduz
   a aproximação espacial, mas não identifica a localização exata das fazendas das empresas.

### 3.4 A camada de confirmação: comércio exterior (ComexStat)

O sinal climático é uma **previsão** de choque de oferta. O volume exportado (kg líquido,
por NCM, mensal, Secex/MDIC) é a **realização observada** desse choque.

Isso cumpre uma função primária e uma possível extensão prospectiva, que não devem ser
confundidas:

**(a) Como teste do mecanismo econômico (validação da tese, não do trade)**
Pergunta pré-registrada: *o choque climático em `t` prevê queda no volume exportado em
`t+3` a `t+6` meses?* Se **não** prevê, o mecanismo econômico que postulamos é falso, e
qualquer alfa que aparecesse seria coincidência. Este teste roda **antes** de olhar
retornos, e o resultado — inclusive negativo — vai para o relatório (padrão Kairos:
documentar a hipótese falsificada é o que a banca premia em "Análise dos Resultados").

**(b) Como confirmação de posição — somente prospectiva, fora do experimento primário**

A auditoria de vintage da Fase 1 mostrou que a Secex reprocessa todo o ano corrente a cada
mês e só estabiliza o ano anterior em fevereiro. A API e os CSVs públicos servem apenas o
vintage mais recente; o Wayback não preservou os arquivos anuais consultados nem foram
encontrados snapshots das respostas `POST`. Portanto, aplicar retrospectivamente pesos
1.0/0.5/0.0 usando a base final como se
ela fosse a primeira publicação seria **lookahead de vintage**.

Por D-026, o ComexStat permanece central em H1b como realização física *ex post*, mas sai do
dimensionamento do backtest primário. Capturas prospectivas continuam sendo armazenadas e,
quando houver histórico suficiente, poderão testar um gate realmente point-in-time. Esta é
uma redução de escopo metodológica feita antes de observar retornos, não o abandono da tese
Clima + ComexStat: uma fonte antecipa a safra e a outra testa se o mecanismo chegou ao fluxo
exportado.

---

## 4. As hipóteses, formalmente

Pré-registradas. Cada uma tem um critério de falsificação explícito — se o teste falhar,
o resultado vai para o relatório como achado negativo, não é escondido.

| # | Hipótese | Teste | Critério de falsificação |
|---|---|---|---|
| **H1a** (mecanismo — o elo central) | O choque climático prevê a **revisão da estimativa de safra da CONAB** antes de ela ser publicada | Regressão `revisão_{lev n} ~ Shock` acumulado até a data de corte do levantamento, painel (safra × UF × cultura), erros agrupados por ano-safra | Coeficiente sem o sinal esperado ou não-significativo após BH-FDR |
| **H1b** (mecanismo físico) | O choque prevê a produção/exportação física da cultura | Regressão preditiva `Δ log(volume exportado)_{t+h} ~ Shock_t`, `h ∈ {3,4,5,6}` meses, erros-padrão Newey-West | idem |
| **H2a** (transmissão preditiva a preço) | O choque disponível antes do mercado prevê o retorno subsequente da commodity | Família pré-registrada mundial/local, contemporânea/forward (D-036–D-041) | **falhou**: nenhuma das seis medidas foi significativa; o canal `P` não sustenta a direção original |
| **H2b** (reação à CONAB) | A publicação do levantamento pode concentrar incorporação de informação já parcialmente observável | Estudo de evento na janela pré-registrada ao redor da divulgação da CONAB | ausência de retorno anormal é diagnóstico compatível com antecipação; não falsifica H2a isoladamente |
| **H3 original** (defasagem no equity) | `E·Shock` previa retorno relativo na direção produtor-comprado/processador-vendido | Painel no desenvolvimento, pré-registrado em D-042 | **falsificada em D-043**: reação anti-preditiva; não inverter silenciosamente |
| **H3′ / H′** (reformulada) | sob `Q>P`, o negativo de `E·Shock` nos grãos prevê o spread relativo; cana é satélite separado | spread/painel apenas nos quatro grãos, demean cross-sectional, cluster por ano-safra, permutação unilateral α=0,10; contrato D-053 | avaliada uma vez no holdout; dev não confirma a direção porque foi usado para formulá-la |
| **H4** (a que mata o projeto) | O retorno da estratégia **não é apenas beta de commodity reembalado** | *Spanning regression*: `r_strat ~ α + IBOV + USDBRL + futuros (soja, milho, açúcar, café) + fatores NEFIN (SMB, HML, WML, IML)` | **α ≤ 0** ou não-significativo ⇒ a estratégia é uma forma cara de comprar o futuro da soja, e temos que dizer isso |
| **H5** (especificidade / placebo) | O sinal vem da agronomia, não de um confundidor macro | Placebo espacial: recalcular `Shock` usando células de grade **sem produção agrícola relevante** (Amazônia central, litoral) | Se o alfa **sobrevive** ao placebo, o sinal está capturando outra coisa (ENSO, risco global, FX) e não o que dizemos que captura |

**H4 e H5 são as duas que podem matar o projeto** e por isso são as mais importantes.
Uma banca de gestora vai fazer exatamente essas duas perguntas. Rodá-las por conta própria,
antes, e reportar o resultado honestamente, é o que separa um trabalho sério de um pitch.

> **Resultado de H1 (2026-07-17, pré-registro D-030, resultado D-031).** **H1a confirmado**: o
> choque climático prevê a revisão da CONAB — coeficiente agrupado **−0,067** por unidade de
> `Shock` (estresse ⇒ revisão para baixo), `t(7)` p≈6e-4, bootstrap por cluster p≈0, sobrevive
> ao BH-FDR; o efeito é consistente no desenvolvimento (−0,057) e no holdout (−0,072) e nas duas
> culturas. **H1b** corrobora a soja ex post (3º e 6º mês pós-colheita); milho fraco (N=7). A
> cadeia climático → revisão de safra é real. Depois disso, H2a falhou (D-037–D-041), a direção
> H3 original foi falsificada (D-043) e H′ foi pré-registrada e congelada (D-044/D-053). H4/H5
> permanecem para a robustez; o holdout de retornos continua lacrado.

### Confundidor conhecido: ENSO (El Niño / La Niña)

El Niño/La Niña afeta simultaneamente (i) o clima brasileiro, (ii) o clima dos outros
grandes produtores (EUA, Argentina) e (iii) o apetite global a risco. Nosso sinal pode ser
um proxy disfarçado de ENSO. **Controle pré-registrado**: incluir o índice ONI (Oceanic
Niño Index, NOAA, mensal, público) como controle nas regressões de H3 e como fator na
spanning regression de H4. Se o alfa morre ao controlar por ONI, o achado é "o sinal é
ENSO" — o que ainda é um resultado publicável, mas uma tese diferente da nossa, e teríamos
que dizê-lo com todas as letras.

---

## 5. Definição do experimento primário (congelada)

Um único conjunto de parâmetros é declarado **primário**. Todo o resto é robustez.
Isto existe para impedir que o resultado reportado seja o melhor de centenas de
combinações testadas — que é a forma mais comum de auto-engano em backtest.

| Parâmetro | Valor primário | Justificativa (**não** derivada de retorno) |
|---|---|---|
| Variável climática | **déficit de precipitação acumulada CHIRPS** na janela fenológica; temperatura é secundária | Canal dominante e única fonte climática com vintage reconstruível; D-023 reduz graus de liberdade e a contaminação POWER |
| Climatologia base | z-score vs. média/desvio **expanding** dos anos anteriores (mín. 10 anos) | Único jeito de não usar o futuro. Descarta a climatologia fixa 1991-2020, que é lookahead |
| Culturas e UFs | soja (MT, GO, PR, RS, MS, MG, BA) + milho 2ª (MT, PR, GO, MS) | Menor suporte acima de 80% da produção no 12º lev. 2024/25, congelado sem consultar retornos (D-023) |
| Janela fenológica | fixa por cultura × UF em `features/shock_spec.py` | CONAB/ZARC/Embrapa; datas e custo documentados em `09_FENOLOGIA_E_LIMIARES.md` |
| Lag de publicação do clima | **7 dias corridos** | Conservador vs. a latência real da fonte (ver `02_DADOS.md`); sensibilidade testada em 3/7/14 dias |
| Uso do ComexStat | H1b *ex post*; **não entra no sizing primário** | Vintages históricos da primeira publicação não são recuperáveis; usar a base final como gate criaria lookahead (D-026) |
| Exposição `E_{i,c}` | Método A fundamentalista PIT; H′ aplica o negativo nos grãos | D-033 preserva a exposição auditável; D-035/D-043 mostram que `Q>P`; D-053 separa mecanismo histórico e direção operacional |
| Horizonte de holding | 21 dias úteis (~1 mês) | Compatível com a hipótese de difusão lenta e declarado antes de consultar retornos |
| Execução | no **close de D+1** após o sinal de D | Nunca no mesmo close que gerou o sinal |
| Construção do portfólio | dollar-neutral, proporcional ao score demeanado, bruto 1,0×; caps 0,40/grão e 0,15/SMTO3 | D-053; neutralidade fatorial não é presumida |
| Custos | componentes definidos; valores e cenários são gate return-agnóstico da Fase 4.0 | Ver D-054 e `04_PROTOCOLO_BACKTEST.md` |
| Benchmark | Ibovespa **e** CDI, ambos declarados a priori | Não escolher depois qual "ganhou" |

---

## 6. Split temporal e disciplina de holdout (congelado)


O edital cita nominalmente "escolha oportunista de período" como viés a ser mitigado. Nossa
resposta:

```
├─────────── DESENVOLVIMENTO (in-sample) ───────────┤├──── HOLDOUT (lacrado) ────┤
2013-01-01                              2019-12-31   2020-01-01        2025-12-31
```

- **Todo** o desenvolvimento — escolha de variável climática, calibração de limiares,
  decisões de desenho — acontece **exclusivamente** até 2019. O recorte declarado começa em
  2013, mas o `Shock` primário point-in-time só produz observações desde 2015/16 (R16).
- O produto CHIRPS `prelim` só existe a partir de 2015 e seu início foi carregado em bloco;
  portanto o sinal point-in-time começa na safra **2015/16**. 2013-2014 permanecem no recorte
  de preços/universo, mas não recebem `Shock` primário (R16).
- O período 2020-2025 é **lacrado**. D-053 congelou a estratégia econômica, mas D-054 exige
  fechar a mecânica operacional e implementar o bloqueio técnico antes da liberação exclusiva
  da Fase 6. Rodamos **uma única vez**, e o resultado vai para o relatório.
- O holdout contém COVID (2020), o superciclo de commodities (2021-22), a guerra na Ucrânia
  e a seca histórica de 2021 no Brasil. É um teste **duro** e de regime genuinamente
  diferente. Se a estratégia sobreviver a ele, o resultado é forte. Se não sobreviver,
  isso também é um resultado, e vamos reportá-lo.

**Tensão real, assumida com honestidade** (ver §7): o teste primário tem somente AGRO3,
SLCE3, BRFS3 e JBSS3. A SMTO3 foi admitida apenas como satélite da carteira após auditoria da
cana. D-053 resolveu a inviabilidade do cap antigo com caps 0,40/0,15 e redução de bruto, mas
não fabrica diversificação nem poder estatístico; essas limitações permanecem visíveis.

O antigo **Backtest B — universo amplo (2021–2025)** deixa de ser uma promessa: só será
materializado se nova fonte primária provar canal direto para nomes pós-IPO, ou como
diagnóstico do Método B claramente separado. Ele está inteiro no holdout e não calibra nada.
Um gráfico da **contagem de ativos elegíveis ao longo do tempo** permanece obrigatório; agora
ele também torna visível a escassez de exposição fundamental, em vez de escondê-la.

---

## 7. Vieses que estamos atacando explicitamente


| Viés | Como ele entraria aqui | Mitigação implementada |
|---|---|---|
| **Look-ahead climático** | usar dado meteorológico do dia `t` no dia `t` (a fonte só o publica dias depois); usar climatologia calculada com o período inteiro | Lag de publicação explícito (7d) + climatologia *expanding* + teste de sensibilidade ao lag |
| **Look-ahead de reanálise** | NASA POWER/ERA5 **revisam** valores passados. O número que vemos hoje para 2015 pode não ser o que estava disponível em 2015 | Primário usa CHIRPS prelim arquivado. POWER fica somente em robustez térmica, com limitação de vintage declarada (D-023) |
| **Look-ahead do mapa de produção** | ponderar a geografia pela safra corrente, PAM ainda não divulgada ou fronteira futura | Pesos CONAB da safra anterior + PAM mais recente com `avail_date≤t` + malha IBGE 2013 fixa pré-amostra; capturas datadas (D-023/D-024/R15) |
| **Survivorship / backfill do universo** | rodar o histórico com o universo de hoje (só quem sobreviveu e já abriu capital) | **Universo dinâmico**: a ação entra na data de IPO + 60 dias e sai na data de deslistagem. Contagem de ativos plotada |
| **Multiple testing** | culturas × regiões × janelas × lags × limiares = centenas de combinações; alguma vai parecer significativa por acaso | Benjamini-Hochberg (FDR) sobre toda a família de testes + um único conjunto primário pré-registrado (§5) |
| **Escolha oportunista de período** | escolher o período porque foi onde funcionou | Split declarado a priori (§6), holdout lacrado; perímetro de H1 será fechado em PT-001 antes do teste |
| **Autocorrelação inflando t-stats** | o sinal climático é altamente persistente; retornos sobrepostos violam independência | Newey-West + *block bootstrap* para inferência |
| **Viés de sobrevivência do sinal** | testar 21 teses e reportar a que funcionou | As 20 teses descartadas estão documentadas em `05_Ideacao_Tese/teses_candidatas.md` com a justificativa da escolha, feita **antes** de qualquer backtest |
| **Ilusão de liquidez** | assumir que dá para operar R$ 10 mi em JALL3 | Filtro de ADTV mínimo + modelo de slippage proporcional à participação no volume |

---

## 8. O que este projeto **não** é (escopo negativo, declarado)

- **Não** é um modelo de previsão de safra. Não competimos com CONAB/USDA. Usamos o clima
  como sinal *ruidoso e antecedente*, não como estimativa de produtividade.
- **Não** é uma aposta direcional em commodity. Se quiséssemos ficar comprados em soja,
  compraríamos o futuro de soja — é mais barato e mais líquido. A estratégia só se
  justifica se gerar alfa **além** disso (é literalmente o teste H4).
- **Não** usa machine learning para decidir direção. ML, se entrar, entra só na camada de
  execução (padrão KernelNet) e é opcional. Complexidade não pontua por si só, e um sinal
  economicamente interpretável é mais defensável do que um que não conseguimos explicar.
- **Não** promete bater o Ibovespa sempre. É posicionada como estratégia **dollar-neutral
  de valor relativo dentro do agro**; neutralidade a mercado é uma hipótese a testar, não
  uma propriedade do notional. O benchmark honesto inclui CDI e Ibovespa, além da atribuição
  a fatores e commodities em H4.
