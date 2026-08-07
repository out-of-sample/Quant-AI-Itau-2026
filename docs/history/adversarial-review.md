# Crítica adversarial ao próprio projeto

> **Status pós-resultado:** as objeções foram formuladas antes da rodada final e permanecem
> preservadas. O balanço ao fim do documento foi reconciliado com D-075; H4 de fato falhou,
> enquanto H5 morreu como exigido.
>
> Este documento existe para atacar a tese, não para defendê-la. Cada objeção abaixo foi
> escrita como se viesse de um avaliador hostil e competente. Onde a defesa é fraca, está
> escrito que é fraca. Onde não há defesa, está escrito que não há.
>
> A razão de existir deste documento é prática: **toda objeção que a banca levantar e que
> já estiver respondida aqui vira ponto a favor; toda objeção que nos pegar de surpresa vira
> ponto contra.** Levantar os problemas antes é mais barato do que ser pego por eles.

---

## As objeções, por gravidade

### 🔴 1. "Vocês têm poucos anos-safra, não 3.000 eventos."

**A objeção.** A safra é anual. O choque climático relevante acontece numa janela de poucas
semanas por ano, por cultura. Milhares de barras diárias **não viram milhares de observações
independentes**: o sinal começa em 2015/16 e H1a depende do painel iniciado em 2017/18. Pior:
soja no MT, GO e MS no mesmo
ano de seca não são três eventos, são um. Qualquer Sharpe, t-stat ou intervalo de confiança
calculado sobre retornos diários está **inflando o N em uma ou duas ordens de grandeza**.

**A defesa.** Parcial, e é honesto reconhecer isso:
- O primário cruza soja e milho 2ª safra, com fases distintas, num painel de UFs. D-023
  deliberadamente não adiciona cana, café e algodão apenas para inflar o N; essas culturas têm
  mecanismos ou vintages diferentes e ficam secundárias.
- Reportamos o **N efetivo** (eventos independentes), não o N nominal (linhas), e agrupamos
  os erros-padrão por ano-safra.
- Usamos *block bootstrap* em vez de inferência i.i.d.

**Onde a defesa é fraca.** Ela não resolve o problema, apenas o mede honestamente. Com tão
poucos anos-safra, **não temos poder estatístico para detectar um efeito pequeno.** Só conseguiríamos
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
(**H4**, *spanning regression* — `docs/history/robustness-plan.md` §2.1): regredimos o retorno da
estratégia contra IBOV, USDBRL, os futuros das quatro commodities, o índice El Niño e os
fatores de risco brasileiros (NEFIN). **Se o alfa não sobreviver a isso, dizemos que não
sobreviveu.**

Há uma razão *a priori* para testar se sobrevive: a estratégia é **dollar-neutral e
long/short dentro do setor**, agora sob H′ (`Q>P` nos grãos). Estresse reduz o score dos
produtores e eleva o dos processadores; a SMTO3 é satélite de cana com canal próprio. Isso cria
uma hipótese de dispersão, mas **não** zera por construção o beta ao futuro nem os fatores.

**Onde a defesa é fraca.** As exposições não se cancelam perfeitamente. Se o beta líquido à
commodity for materialmente diferente de zero, parte do retorno é, sim, beta. Vamos medir e
reportar o beta líquido residual, não afirmar que é zero.

---

### 🔴 2A. "Seca pode destruir a produção da empresa que vocês querem comprar."

**A objeção.** A direção positiva dos produtores colapsa dois efeitos opostos: preço maior
para o grão vendido e menor quantidade produzida nas fazendas atingidas. Uma produtora
concentrada exatamente na região seca pode perder receita mesmo com a commodity em alta.
Geografia, hedge e produtividade própria podem dominar a classificação genérica de
"produtor".

**A defesa.** A objeção procedia. D-035 auditou `P/Q/C`; D-037–D-041 não sustentaram o canal
de preço; D-043 mostrou reação acionária contrária à direção antiga. A hipótese H′ (`Q>P`) foi
pré-registrada em D-044 e congelada em D-053, com disclosure de que o desenvolvimento está
queimado para sua direção. O registro antigo não foi reescrito.

**Onde a defesa é fraca.** H′ é uma reformulação motivada por um resultado do desenvolvimento,
não confirmação independente. Geografia e hedge históricos seguem incompletos. Só o holdout
de tiro único pode validar a nova direção; se falhar, não existe segunda inversão.

---

### 🔴 2B. "Fama–MacBeth com quatro ações é teatro estatístico."

**A objeção.** O H3 original exigia regressões cross-sectionais, mas a matriz fundamentalista
tem três ações no início e quatro após 2018. Uma inclinação diária estimada com esse N não
produz uma cross-section informativa; repetir o procedimento em muitos dias não cria novas
empresas independentes.

**A defesa.** D-034 suspendeu o Fama–MacBeth. D-053 congelou o substituto: spread/painel
apenas nos quatro grãos, demean na seção transversal, cluster por ano-safra e permutação
unilateral. A SMTO3 não dilui o teste primário.

**Onde a defesa é fraca.** Trocar o estimador não fabrica poder: o holdout tem cinco
anos-safra. A permutação exata ainda é um item da Fase 4.0 (D-054), a fechar sem P&L.

---

### 🔴 2C. "Dollar-neutral não é market-neutral."

**A objeção.** R$ 0,50 comprado e R$ 0,50 vendido zeram notional, não beta. Com produtores
menores e processadores maiores, as pontas podem carregar diferenças de mercado, tamanho,
liquidez, dólar e commodity. Chamar a carteira de market-neutral antes de medir essas
exposições superestima o desenho.

**A defesa.** A linguagem foi corrigida para dollar-neutral. Betas e fatores serão medidos,
eventuais restrições serão declaradas e H4 continua sendo teste existencial de *spanning*.

**Onde a defesa é fraca.** Com cinco nomes — e só quatro no teste primário — neutralizar fatores pode tornar a carteira
inviável ou eliminar o próprio sinal. A prioridade será transparência sobre exposições
residuais, não prometer neutralidade que o universo não suporta.

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
  (`docs/history/robustness-plan.md` §2.4).
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
deslistagem) e, após D-033, exposição fundamental igualmente PIT. O primário contém somente
os quatro nomes com canal direto comprovado; um universo amplo não é fabricado com empresas
indiretas. Publicamos a contagem de elegíveis ao longo do tempo como gráfico.

**Onde a defesa é fraca.** A defesa contra survivorship ficou rigorosa, mas o universo
econômico continua estreito: quatro grãos no teste e SMTO3 como satélite. D-053 resolveu a
inviabilidade do cap antigo, não a escassez de nomes nem o poder cross-seccional.

---

### 🟡 6. "Vocês precificam por UF, mas a fazenda não é o estado."

**A objeção.** A CONAB divulga por UF. Embora o CHIRPS p05 tenha células de ~5 km e o pipeline
as agregue por município com pesos PAM, a SLC
Agrícola tem fazendas em pontos específicos que podem estar completamente fora da área
atingida por uma seca "do Mato Grosso". Estamos atribuindo a uma empresa um choque que pode
não ter tocado uma única fazenda dela.

**A defesa.** D-027/D-028 evitam a antiga aproximação por caixa/grade grosseira: cada célula
CHIRPS é associada à malha municipal IBGE 2013, municípios são ponderados pela PAM disponível
em `t` e só então agregados à UF. Ainda assim, é uma fonte de **ruído de medida** — que atenua o coeficiente
estimado (viés para zero), tornando nosso teste **conservador**, não otimista. Ou seja: o
ruído joga contra nós, não a nosso favor. Se acharmos sinal apesar dele, o efeito verdadeiro
é maior do que o medido.

Esse ruído ficou mais importante após o canal de preço falhar: H′ depende justamente de o
dano de volume próprio alcançar a empresa exposta. A regionalização municipal melhora o
choque agregado, mas não localiza fazendas históricas de cada companhia; a defesa é parcial.

**Melhoria possível (não obrigatória)**: usar o CAR/mapas de propriedade para localizar as
fazendas das empresas listadas e construir um choque **específico da empresa**, em vez de um
choque da UF. Seria uma contribuição forte, mas é trabalho substancial. Registrado como
robustez futura, não como pendência solta nem como escopo primário.

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

**A objeção.** AGRO3, SLCE3 e SMTO3 podem ter volume e aluguel limitados. Uma
estratégia que precisa entrar e sair em 21 dias nesses nomes tem custo de mercado que come
o alfa.

**A defesa.** A Fase 4.0 congela o filtro de ADTV, o modelo de slippage, aluguel e a política
de indisponibilidade sem consultar P&L; custos dobrados entram na robustez. Também reportamos a
**capacidade** estimada da estratégia (quanto capital ela suporta antes de o alfa
desaparecer) — que é a métrica que uma gestora de verdade olharia.

**Onde a defesa é fraca.** É provável que a capacidade seja **baixa**. Uma estratégia com
capacidade de poucos milhões de reais é academicamente interessante e comercialmente
irrelevante. Vamos reportar o número em vez de omiti-lo.

---

## Balanço honesto

| | |
|---|---|
| **O que sobreviveu** | O mecanismo clima→revisão CONAB; a direção de H′ no holdout (`p=0,0625`); P&L nominal positivo; placebo geográfico morto. |
| **O que é frágil** | N efetivo pequeno, concentração e proxies de investibilidade. Não há engenharia que transforme cinco anos-safra em uma amostra grande. |
| **O que matou a claim forte** | H4 falhou (`t=−1,03`) e o Sharpe de excesso ao risk-free foi `−0,50`. A carteira não demonstrou alpha climático nem habilidade sob a régua congelada. |
| **Conclusão adversarial** | A informação física existe e o sinal chegou à carteira, mas não remunerou o risco. O estudo é evidência de estratégia, não evidência de uma vantagem investível. |
