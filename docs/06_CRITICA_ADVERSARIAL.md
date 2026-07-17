# Crítica adversarial ao próprio projeto

> Este documento existe para atacar a tese, não para defendê-la. Cada objeção abaixo foi
> escrita como se viesse de um avaliador hostil e competente. Onde a defesa é fraca, está
> escrito que é fraca. Onde não há defesa, está escrito que não há.
>
> A razão de existir deste documento é prática: **toda objeção que a banca levantar e que
> já estiver respondida aqui vira ponto a favor; toda objeção que nos pegar de surpresa vira
> ponto contra.** Levantar os problemas antes é mais barato do que ser pego por eles.

---

## As objeções, por gravidade

### 🔴 1. "Vocês têm 12 eventos, não 3.000."

**A objeção.** A safra é anual. O choque climático relevante acontece numa janela de poucas
semanas por ano, por cultura. Um backtest de 2013 a 2025 tem ~3.000 dias úteis, mas **não
tem 3.000 observações independentes — tem ~12 safras**. Pior: soja no MT, GO e MS no mesmo
ano de seca não são três eventos, são um. Qualquer Sharpe, t-stat ou intervalo de confiança
calculado sobre retornos diários está **inflando o N em uma ou duas ordens de grandeza**.

**A defesa.** Parcial, e é honesto reconhecer isso:
- O primário cruza soja e milho 2ª safra, com fases distintas, num painel de UFs. D-023
  deliberadamente não adiciona cana, café e algodão apenas para inflar o N; essas culturas têm
  mecanismos ou vintages diferentes e ficam secundárias.
- Reportamos o **N efetivo** (eventos independentes), não o N nominal (linhas), e agrupamos
  os erros-padrão por ano-safra.
- Usamos *block bootstrap* em vez de inferência i.i.d.

**Onde a defesa é fraca.** Ela não resolve o problema, apenas o mede honestamente. Com ~12
safras, **não temos poder estatístico para detectar um efeito pequeno.** Só conseguiríamos
detectar um efeito grande. Se o efeito verdadeiro for modesto, nosso teste vai ser
inconclusivo, e a resposta correta é dizer "inconclusivo", não espremer significância.
O CHIRPS prelim só começa em 2015/16 (R16), reduzindo ainda mais a janela operacional.

> **Esta é a limitação nº 1 do projeto.** Não tem solução dentro do escopo. Vai para o
> relatório, na seção de limitações, escrita por nós — não descoberta pela banca.

---

### 🔴 2. "Isso é só ficar comprado no futuro da soja, com passos a mais."

**A objeção.** Se o choque climático faz o preço da soja subir, e a SLC Agrícola sobe quando
a soja sobe, então a estratégia é uma forma cara, ilíquida e complicada de fazer o que um
contrato futuro faz melhor. O alfa alegado seria apenas **beta de commodity** disfarçado.

**A defesa.** É a objeção mais séria e por isso virou um teste formal e pré-registrado
(**H4**, *spanning regression* — `05_SUITE_ROBUSTEZ.md` §2.1): regredimos o retorno da
estratégia contra IBOV, USDBRL, os futuros das quatro commodities, o índice El Niño e os
fatores de risco brasileiros (NEFIN). **Se o alfa não sobreviver a isso, dizemos que não
sobreviveu.**

Há uma razão *a priori* para acreditar que sobrevive: a estratégia é **dollar-neutral e
long/short dentro do setor**. O componente comprado (produtores) e o vendido (processadores)
têm exposição de sinais opostos à commodity, então a exposição líquida ao futuro é
**estruturalmente próxima de zero por construção**. O que sobra não é o movimento do preço
da soja — é a **dispersão** entre quem ganha e quem perde com ele.

**Onde a defesa é fraca.** As exposições não se cancelam perfeitamente. Se o beta líquido à
commodity for materialmente diferente de zero, parte do retorno é, sim, beta. Vamos medir e
reportar o beta líquido residual, não afirmar que é zero.

---

### 🔴 3. "O dado climático que vocês usam não existia na época."

**A objeção.** NASA POWER e ERA5 são produtos de **reanálise**, e reanálises **reescrevem o
passado**. O valor de precipitação que a API entrega hoje para março de 2021 não é
necessariamente o que estava disponível em março de 2021. Backtest construído sobre dado
revisado é backtest com lookahead — e nenhum cuidado no código corrige isso, porque o
problema está *na fonte*.

**A defesa.** Esta objeção é **procedente** e nós a confirmamos empiricamente (o campo
`sources` da API NASA POWER mostra que os últimos ~2 meses vêm de um produto provisório,
GEOS-IT, que depois é sobrescrito por MERRA-2; o ERA5T é sobrescrito pelo ERA5 final ~2-3
meses depois). Nossa resposta:
- Adotar **CHIRPS** como fonte primária de precipitação, porque é a única que **arquiva as
  versões preliminar e final separadamente** — o que nos dá um proxy honesto de *vintage*.
- Rodar um teste de robustez explícito comparando o sinal com dado preliminar vs. final
  (`05_SUITE_ROBUSTEZ.md` §2.4).
- Usar variáveis **robustas a revisão** (acumulados de precipitação ao longo de semanas, não
  picos diários).

**Onde a defesa é fraca.** Para a **temperatura** não encontramos fonte gratuita que preserve
vintage. Por isso D-023 retirou o POWER do caso primário antes de observar retornos: temperatura
é apenas robustez, com contaminação declarada. Ainda resta risco de vintage nos pesos espaciais
da PAM, que revisa anos antigos (R15); captura datada não reconstrói versões anteriores que o
IBGE já sobrescreveu.

---

### 🟡 4. "O sinal é El Niño, e vocês estão chamando de agronomia."

**A objeção.** ENSO afeta simultaneamente o clima brasileiro, o clima dos concorrentes (EUA,
Argentina), o preço global de alimentos e o apetite global a risco. Um índice de "estresse
climático no Brasil" é, em boa parte, uma leitura defasada do El Niño. Se o alfa existe,
pode vir do ENSO, e a narrativa agronômica seria decoração.

**A defesa.** Dois testes pré-registrados: (i) **ONI como controle** nas regressões e na
*spanning regression*; (ii) **placebo espacial** — recalcular o choque em regiões sem
produção agrícola. Se o alfa sobreviver ao placebo, a explicação agronômica está morta e a
explicação macro/ENSO está viva.

**Onde a defesa é fraca.** ENSO e clima produtor brasileiro são genuinamente colineares.
Controlar por ONI pode remover parte do sinal verdadeiro junto com o confundidor. Vamos
reportar o resultado **com e sem** o controle, e deixar a diferença visível em vez de
escolher a especificação que favorece a conclusão desejada.

---

### 🟡 5. "Metade do universo não existia em 2013."

**A objeção.** SOJA3, TTEN3, JALL3, RAIZ4, VITT3 abriram capital em 2020-21. Um backtest
longo com o universo de hoje é **survivorship + backfill bias** puro. E um backtest restrito
ao período em que todos existem tem 4-5 anos — curto demais para qualquer afirmação séria.

**A defesa.** Universo **dinâmico** (a ação entra na data efetiva de IPO + 60 dias, sai na
deslistagem) e **dois backtests declarados a priori**: núcleo histórico 2013-2025 com
universo restrito, e universo amplo 2021-2025. Publicamos a contagem de ativos elegíveis ao
longo do tempo como gráfico.

**Onde a defesa é fraca.** Não há saída limpa. O período com universo rico é justamente o
período de holdout, o que significa que a parte mais interessante do cross-section **não
pode ser usada para desenvolver nada** sem queimar o holdout. É um custo real que estamos
pagando conscientemente, e é a razão de o backtest primário ser o de universo restrito.

---

### 🟡 6. "Vocês precificam por UF, mas a fazenda não é o estado."

**A objeção.** A CONAB divulga por UF. A grade meteorológica utilizável tem ~55 km. A SLC
Agrícola tem fazendas em pontos específicos que podem estar completamente fora da área
atingida por uma seca "do Mato Grosso". Estamos atribuindo a uma empresa um choque que pode
não ter tocado uma única fazenda dela.

**A defesa.** É verdade, e é uma fonte de **ruído de medida** — que atenua o coeficiente
estimado (viés para zero), tornando nosso teste **conservador**, não otimista. Ou seja: o
ruído joga contra nós, não a nosso favor. Se acharmos sinal apesar dele, o efeito verdadeiro
é maior do que o medido.

Além disso, o mecanismo de **preço** (o canal dominante da tese) não depende da localização
da fazenda: se o Mato Grosso seca, o preço da soja sobe para **todos**, inclusive para o
produtor cuja lavoura escapou. E o produtor que escapou é justamente o mais beneficiado.

**Melhoria possível (não obrigatória)**: usar o CAR/mapas de propriedade para localizar as
fazendas das empresas listadas e construir um choque **específico da empresa**, em vez de um
choque da UF. Seria uma contribuição forte, mas é trabalho substancial. Registrado como
próximo passo, não como escopo.

---

### 🟡 7. "Quem é o trouxa do outro lado?"

**A objeção.** Toda estratégia de alfa precisa responder: *por que essa informação não está
no preço?* Meteorologia é pública, gratuita e olhada por toda mesa de commodities do mundo.
Trading houses (Cargill, Bunge, Louis Dreyfus) têm meteorologistas próprios e agrônomos em
campo. A ideia de que um time acadêmico vai chegar antes deles é implausível.

**A defesa.** A tese **não** é que sabemos do clima antes deles. É que:
- **O canal de transmissão é diferente do que eles operam.** As trading houses operam a
  informação no mercado de **commodities físicas e futuros**, onde ela é de fato precificada
  rápido. A pergunta é se ela chega com a mesma velocidade ao **cross-section de ações
  brasileiras** — um mercado menor, com menos analistas dedicados, e onde a tradução de
  "choque de oferta" para "qual empresa ganha e qual perde" exige juntar três bases de dados
  heterogêneas.
- **A ineficiência que exploramos é de agregação, não de acesso.** O dado é público; caro é
  cruzá-lo. Essa é uma forma clássica e defensável de ineficiência (custo de processamento
  de informação, não assimetria de acesso).

**Onde a defesa é fraca.** É um argumento *a priori* e **pode simplesmente estar errado**.
O teste H4 (spanning) é quem decide. Se o alfa não existir, a resposta honesta é: "a
informação já estava no preço" — e isso, por si, é um achado relatável.

---

### 🟢 8. "O período tem dois eventos que dominam tudo."

**A objeção.** A seca/geada de 2021 e o superciclo de commodities de 2021-22 são eventos
enormes. Um backtest que "funciona" pode estar só capturando esses dois episódios.

**A defesa.** Testes de subperíodo e *exclusão da melhor janela* estão na suíte de robustez
(§4). Se o alfa depende de 2021, dizemos que depende de 2021.

**Nota.** Este é um risco que pode acabar **confirmando** a tese em vez de destruí-la: se a
estratégia funciona *especialmente* em anos de choque climático extremo e fica neutra em anos
normais, isso é exatamente o comportamento previsto pelo mecanismo — não um defeito. O que
seria suspeito é o inverso: alfa constante e suave em anos sem choque nenhum.

---

### 🟢 9. "Os ativos são ilíquidos demais para isso ser operável."

**A objeção.** JALL3, VITT3, AGRO3, SOJA3 são small caps com volume diário baixo. Uma
estratégia que precisa entrar e sair em 21 dias nesses nomes tem custo de mercado que come
o alfa.

**A defesa.** Filtro de liquidez (ADTV mínimo) e modelo de *slippage* proporcional à
participação no volume, mais um teste de robustez com custos dobrados. Também reportamos a
**capacidade** estimada da estratégia (quanto capital ela suporta antes de o alfa
desaparecer) — que é a métrica que uma gestora de verdade olharia.

**Onde a defesa é fraca.** É provável que a capacidade seja **baixa**. Uma estratégia com
capacidade de poucos milhões de reais é academicamente interessante e comercialmente
irrelevante. Vamos reportar o número em vez de omiti-lo.

---

## Balanço honesto

| | |
|---|---|
| **O que é forte** | A reformulação produtor-vs-processador (a heterogeneidade cross-seccional) é economicamente correta, não-óbvia e original no contexto brasileiro. A cadeia causal tem um elo intermediário observável e datável (a revisão da CONAB), o que torna a tese **falsificável em etapas** em vez de ser uma caixa-preta de "clima → retorno". |
| **O que é frágil** | O N efetivo (poucas dezenas de eventos independentes). Não tem conserto. |
| **O que pode matar** | H4 (a estratégia ser só beta de commodity) e H5 (o sinal ser ENSO disfarçado). |
| **O que fazemos se morrer** | Reportamos. Um projeto que testa a própria tese com rigor e conclui que ela não se sustenta pontua nos critérios de Backtest (15%), Análise de Resultados (15%) e Conclusão (10%) — e é infinitamente mais defensável do que um Sharpe bonito que não sobrevive à primeira pergunta da banca. |
