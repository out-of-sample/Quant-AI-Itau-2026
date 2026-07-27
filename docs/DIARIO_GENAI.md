# Diário de uso de IA generativa

Registro contínuo e datado de onde a IA generativa entrou no processo, o que ela produziu, e
**o que precisou ser corrigido**. Este arquivo é a fonte da seção "Uso de IA Generativa" do
relatório final (15% da nota).

**Regra deste diário**: registrar tanto os acertos quanto os **erros e as propostas da IA que
foram derrubadas pela verificação**. Um relato em que a IA só acerta não é um relato de uso
crítico — é publicidade, e um avaliador experiente reconhece a diferença. O que demonstra uso
maduro é a **validação**: o que foi checado, como, e o que caiu na checagem.

---

## Onde a IA foi usada (e onde não foi)

| Etapa | Uso | Por quê |
|---|---|---|
| Levantamento de teses | **Intenso** | Varrer literatura acadêmica e mapear fontes de dados brasileiras é trabalho de amplitude, não de julgamento |
| Verificação de disponibilidade de dados | **Intenso** | Testar dezenas de endpoints públicos ao vivo |
| Formalização da tese | **Assistido** | A crítica econômica veio da IA, mas a decisão foi do time |
| **Escolha da tese** | ❌ **Não delegada** | Decisão do time, tomada sobre material comparativo |
| **Decisões de desenho do backtest** | ❌ **Não delegadas** | Pré-registro é responsabilidade do time |
| Implementação | (fase futura) | — |

---

## 2026-07-13 — Levantamento e comparação de teses

**Uso**: geração e avaliação de um conjunto amplo de teses de dados alternativos, cada uma
ancorada em literatura acadêmica internacional e cruzada com a disponibilidade real de dados
públicos brasileiros. Resultado: 21 teses documentadas e pontuadas em 8 critérios
(`05_Ideacao_Tese/teses_candidatas.md`).

**Valor real**: amplitude. Mapear 21 teses com base acadêmica e verificação de fonte de dados
manualmente levaria semanas.

**Validação humana**: a escolha final **não** foi delegada. A IA produziu o material
comparativo; a decisão foi do time.

**O que a IA errou aqui** — e foi pego na verificação:
- Propôs uma tese de "insônia corporativa" (horário de submissão de documentos à CVM como
  proxy de estresse da diretoria). **A verificação do dataset da CVM mostrou que não existe
  campo de horário** — só a data. O mecanismo era impossível como concebido. A tese foi
  reformulada para outro paper cujo mecanismo cabe no dado que existe de fato.
- Superestimou a granularidade dos dados de PIX do Banco Central (assumiu dado municipal;
  **é mensal e nacional**).

---

## 2026-07-14 — Verificação empírica das fontes de dados

**Uso**: agentes de pesquisa em paralelo testando **ao vivo** (requisição real) cada fonte de
dados da tese escolhida: NASA POWER, CHIRPS, ERA5, INMET, CONAB, ComexStat, ANTAQ, B3,
yfinance.

**Valor real**: alto, e **mudou decisões de projeto** — não foi um exercício de confirmação.
Quatro achados que teriam invalidado ou danificado o backtest se descobertos tarde:

1. **NASA POWER reescreve o passado.** A verificação leu o campo `sources` da própria resposta
   da API e mostrou que os últimos ~2 meses vêm de um produto provisório (GEOS-IT) depois
   substituído por MERRA-2. Um backtest construído sobre essa série teria **lookahead embutido
   e não removível**. → Fonte primária trocada para CHIRPS, que arquiva preliminar e final
   separadamente (decisão D-003).

2. **O universo agro da B3 mudou em 2025.** JBSS3 foi deslistada, BRF e Marfrig se fundiram,
   Santos Brasil saiu via OPA — e o yfinance **apaga tickers deslistados**. Como esses eram o
   lado *processador* (short) da tese, o viés de sobrevivência seria fatal. → Fonte de preços
   trocada para o COTAHIST da B3 (decisão D-004).

3. **A CONAB publica um painel de vintages.** Descoberta não antecipada: o arquivo de
   levantamentos guarda **todas as 12 estimativas** de cada safra, com revisões de −15% a +20%.
   Isso **melhorou a tese**, inserindo um elo causal intermediário datável (decisão D-005).

4. **Bug silencioso na API do ComexStat**: NCM com zero à esquerda passado como número retorna
   lista **vazia com `success: true`** — falha sem erro. Afeta café e carnes. Só apareceu
   porque a consulta foi de fato executada, não presumida.

**O que a IA errou aqui**:
- **A própria IA havia proposto**, na fase de ideação, usar dados portuários (ANTAQ/AIS) como
  "camada de granularidade" sobre o ComexStat. A verificação derrubou: a ANTAQ tem latência de
  **~40 dias**, enquanto o ComexStat entrega porto de embarque por NCM em **3-5 dias úteis**.
  A camada proposta era **estritamente pior** que o dado que já tínhamos. Descartada (D-006).
- Também havia expectativa de usar o dado **semanal** do MDIC para ganhar frequência. A
  verificação mostrou que o órgão **sobrescreve a mesma URL toda semana e não arquiva
  histórico** — não existe série para backtestar. Descartado.

> **A lição metodológica**: em ambos os casos, a proposta da IA era plausível e teria passado
> numa leitura superficial. Só caiu porque **foi testada contra a fonte real**. É por isso que
> nenhuma fonte entrou em `02_DADOS.md` sem ter sido consultada ao vivo, e por isso o documento
> marca explicitamente o que permanece **NÃO CONFIRMADO**.

---

## 2026-07-14 — Crítica econômica da formulação inicial

**Uso**: submeter a tese a uma crítica adversarial estruturada, do ponto de vista de asset
pricing.

**Resultado — o achado conceitual mais importante do projeto até agora.** A formulação
inicial, intuitiva, era *"detectou seca ⇒ vende ações do agro"*. A crítica mostrou que isso
está **economicamente errado**: o Brasil é um dos maiores exportadores mundiais dessas
commodities, então uma quebra de safra brasileira é um **choque de oferta global** e **eleva**
o preço internacional. Para o produtor, o efeito é ambíguo (vende menos, a preço maior); para
o frigorífico, que compra grão como insumo, é inequivocamente negativo.

**Impacto**: a estratégia deixou de ser uma aposta direcional e passou a ser **long/short
cross-seccional dentro do setor** — market-neutral por construção, mais defensável, e com
uma tese de ineficiência mais precisa (custo de *agregação* de informação pública, não
assimetria de acesso). Ver decisão D-002.

**Validação humana**: o raciocínio econômico foi conferido contra a lógica de exposição a
insumo/produto das empresas reais do universo, e virou uma hipótese formal com critério de
falsificação declarado (H4), não uma afirmação aceita por soar bem.

---

## 2026-07-14 — Verificação da fenologia e dos limiares agronômicos

**Uso**: levantar, com fonte primária, em que janela do ano o clima afeta cada cultura e quais
limiares de estresse são citáveis (CONAB, Embrapa, ZARC/MAPA).

**Valor real**: **pegou um erro de desenho que teria invertido o sinal.**

**O que a IA errou** — dois erros graves, ambos pegos porque a checagem foi contra fonte
primária e não contra a memória do modelo:

1. 🔴 **A premissa "menos chuva ⇒ preço sobe ⇒ compra o produtor" estava errada para a cana.**
   Na cana, seca no **verão** (crescimento) reduz a tonelagem — ruim. Mas seca no **inverno**
   (maturação) faz a planta parar de crescer e **acumular sacarose**: o **ATR sobe** — bom.
   Confirmado na safra 2024/25, em que a produtividade caiu e o **ATR subiu 1,33%**. Um sinal
   linear aplicado à cana o ano inteiro estaria **com o sinal trocado em metade do tempo**.
   → O modelo passou a definir o choque **por cultura × fase fenológica** (decisão D-010).
   Este erro produziria um backtest com resultado medíocre e *inexplicável*, e teria sido
   quase impossível de diagnosticar depois do fato.

2. **O limiar de "34-35 °C causa aborto de flores na soja" foi atribuído à Embrapa e não é
   dela.** A fonte primária (Embrapa Soja, sistema SECA) fala em **40 °C**. O número de 35 °C
   circula em textos de mercado e foi reproduzido acriticamente. → Corrigido; o documento agora
   marca explicitamente que 35 °C **não pode ser citado como Embrapa**.

**Validação humana**: nenhum limiar entrou no modelo sem fonte primária. O documento
`09_FENOLOGIA_E_LIMIARES.md` marca item a item o que é **CONFIRMADO** (lido da fonte), o que é
**derivado** (inferido do ciclo da cultura) e o que permanece **NÃO CONFIRMADO** — e o que está
não-confirmado **está proibido de virar parâmetro do sinal**.

> **Padrão que emergiu do projeto**: as propostas da IA que caíram — ANTAQ como camada de
> granularidade, dado semanal do MDIC, NASA POWER como fonte point-in-time, NDVI como sinal em
> tempo real, sinal linear na cana, limiar de 35 °C — eram **todas plausíveis**. Nenhuma teria
> sido rejeitada numa leitura superficial. Todas caíram ao serem testadas contra a fonte real.
> A conclusão prática que levamos para o resto do projeto é que **o valor da IA aqui está na
> amplitude da busca, e o valor do time está na verificação** — e que inverter essa divisão de
> trabalho seria a forma mais rápida de produzir um resultado bonito e errado.

---

## 2026-07-15 — Fundação de engenharia do repositório

**Uso**: montar, com assistência da IA, o esqueleto de engenharia antes de qualquer código de
pesquisa — empacotamento (`pyproject.toml`), lockfile reprodutível com hashes, ganchos de
pré-commit, CI no GitHub Actions, guards determinísticos de lookahead e de segredo, e o
teste-canário da convenção de sinal.

**Valor real**: velocidade em trabalho de configuração de baixo julgamento (escrever workflow
de CI, regex de detecção, estrutura de pacote) — o tipo de tarefa em que a IA rende sem risco
conceitual, desde que **cada peça seja executada de verdade**, e não só escrita.

**Validação humana**: nada foi aceito no papel. Criou-se o ambiente, instalou-se o stack,
rodou-se lint + guards + testes, e — o passo que pegou os erros — validou-se uma instalação
**limpa a partir do lockfile**, reproduzindo exatamente os passos da CI.

**O que a IA errou** — e caiu na verificação:
- **Lockfile quebrado**: o lock gerado com `--generate-hashes` não instalava em `--require-hashes`
  porque `setuptools` (dependência do `pip-tools`) ficava sem pin. Só apareceu ao instalar do
  zero num venv limpo; passaria despercebido enquanto se usasse o venv de desenvolvimento.
  Corrigido com `--allow-unsafe`.
- **Falso alarme de sintaxe**: a IA leu `except OSError, UnicodeDecodeError:` (sem parênteses,
  produzido pelo `ruff format`) como se fosse erro de Python 2. Testar a sintaxe mostrou que é
  **válida em Python 3.14** (PEP 758). O reflexo certo — verificar em vez de "consertar" — evitou
  reverter código correto.
- **Dois formatadores**: a configuração inicial trazia `black` **e** `ruff format`, que podem
  discordar. A checagem de formatação expôs o conflito; ficou só o `ruff format`.
- **Regra de lint inexistente**: `ignore = ["PD901"]` referenciava uma regra já removida do ruff;
  o próprio ruff avisou.

> A mesma lição das fases anteriores se repetiu numa tarefa "puramente técnica": as saídas da IA
> eram plausíveis e passariam numa leitura superficial. O que as separou do que estava certo foi
> **executá-las** — instalar do zero, compilar, rodar — não revisá-las no editor.

---

## 2026-07-15 — Verificação ao vivo das fontes de proventos (R5)

**Uso**: testar ao vivo, endpoint a endpoint, as fontes gratuitas candidatas a fornecer os
eventos corporativos que faltam ao COTAHIST (ajuste de dividendos/JCP/splits).

**Valor real**: transformou uma pendência vaga ("achar uma fonte de proventos") numa decisão
com trade-off medido (D-013). O achado central: a API **oficial da B3 não cobre os deslistados**
(BRF e Santos Brasil retornam 0; JBS congela em 2019) — o mesmo survivorship que já tínhamos
resolvido no preço reaparece nos proventos. A StatusInvest cobre a cauda, mas é agregador.

**Validação humana**: em vez de confiar na StatusInvest de cara, cruzou-se contra a B3 onde as
duas se sobrepõem. O cross-check **passou** (valores idênticos; `ed` = data-com da B3), mas
também **expôs um gotcha**: a StatusInvest reescreve valores por ação para splits posteriores
(um dividendo pré-split apareceu pela metade). Sem o cruzamento, isso entraria silencioso no
fator de ajuste.

**O que a IA errou**: chutou `GetListedStockDividends` como o endpoint de eventos em ações da
B3 — retornou 404. O nome correto (`GetListedSupplementCompany`) foi achado testando candidatos,
não presumido — e a checagem seguinte mostrou que ele também **trunca** as listas, ressalva que
entrou no registro antes de virar armadilha no código.

---

## 2026-07-15 — Fetcher de proventos em dinheiro da B3

**Uso**: escrever o fetcher/normalizador do endpoint `GetListedCashDividends` da B3 → schema
`CorporateEvent`, com testes.

**Valor real**: normalização com os cuidados certos (decimal brasileiro, filtro de classe ON/PN
pelo sufixo do ticker, dedupe de registros repetidos, descarte de eventos sem data-com).

**Validação humana**: fixture com resposta **real** da B3 amarra o parse; teste ao vivo, ponta a
ponta, contra a API.

**O que a IA errou** — e o teste ao vivo pegou (o fixture não pegaria):
- A IA fixou `pageSize=200`. A B3 **devolve vazio acima de ~120** — o fetch retornava zero
  silenciosamente. Corrigido para 100.
- A IA não paginava. PETROBRAS tem **337 eventos em 4 páginas**; sem paginar, truncaria em 100.
  Corrigido para percorrer `totalPages`.

> Lição registrada: um fixture prova o *parse*, mas só o teste **contra a fonte viva** pega
> truncamento silencioso de paginação. Os dois erros passariam verdes numa suíte só de fixture.

---

## 2026-07-15 — Eventos em ações da B3 (o `factor`)

**Uso**: normalizar os eventos em ações (`GetListedSupplementCompany`) para `share_ratio`.

**Valor real**: o campo `factor` da B3 não é auto-explicativo. Em vez de assumir uma fórmula,
a interpretação foi **calibrada contra o preço real do COTAHIST** em eventos conhecidos.

**Validação humana** — o passo que definiu o desenho:
- Baixou-se o preço em torno da data-ex de um split (SLC, 13/12/2023): o preço caiu **2,08×**,
  confirmando `DESDOBRAMENTO factor=100 ⇒ ratio 2,0` (isto é, `1 + factor/100`).
- E de um grupamento (MGLU, 24/05/2024): o preço **saltou 9,96×**, confirmando
  `GRUPAMENTO factor=0,10 ⇒ ratio 0,10` — semântica **diferente** (o `factor` já é o ratio).

**O que a IA errou / teria errado**: a tentação era aplicar uma única fórmula a todos os
labels. Isso teria invertido/escalado errado o grupamento. Além disso, `INCORPORACAO`/`RESGATE`
não são ratios simples (o papel vira outro ou é resgatado) — se tratados como `share_ratio`
produziriam retorno espúrio na deslistagem; foram separados como eventos terminais.

> É o mesmo padrão do erro da cana (D-010): uma regra "óbvia" e uniforme que estaria errada em
> parte dos casos, pega só porque foi conferida contra o dado real, não contra a intuição.

---

## 2026-07-16 — Fetcher da StatusInvest (a cauda deslistada)

**Uso**: escrever o fetcher/normalizador dos proventos da StatusInvest para os papéis que a API
da B3 não cobre (JBSS3 pós-2019, BRFS3, STBP3), com o cuidado do campo `adj` (D-013).

**Valor real**: a calibração ao vivo, feita **antes** de escrever o código, encontrou um campo
não documentado — **`sov`** ("valor original") — que resolve na própria fonte o problema que
esperávamos ter de resolver à mão: quando `adj=True`, o `v` está reescrito para a base
pós-split, mas o `sov` preserva o nominal da época. Sem essa sondagem, o desenho teria sido
reconstruir o nominal multiplicando pelos fatores de split (mais código, mais hipóteses, mais
chance de erro).

**Validação humana**:
- **Cross-check quantitativo contra a B3** na sobreposição (SLC, 8 registros): 7 batem exatos,
  1 diverge 3,9e-4 — a StatusInvest reconstrói o nominal com arredondamento do fator. A
  tolerância (5e-4) e o caso divergente estão documentados e travados em teste de CI.
- Cobertura da cauda confirmada ao vivo: JBSS3 22 eventos (11 pós-2019), BRFS3 22, STBP3 50.
- Teste ponta a ponta contra a fonte viva, além das fixtures reais.

**O que a IA errou / quase errou**: a premissa herdada da sessão anterior era que o valor
nominal exigiria reconstrução externa (foi assim que D-013 registrou o risco). A sondagem
derrubou a premissa — para melhor. Ficou também um achado que teria virado bug no montador:
BRFS3 traz provento com data-com **posterior** à incorporação pela Marfrig; se a série de preços
não cortar na data de deslistagem via COTAHIST, esse resíduo entraria no retorno de um papel
que já não existia.

---

## 2026-07-16 — Montador da série de retorno total

**Uso**: implementar a peça que junta COTAHIST + as três fontes de eventos numa série de
retorno total por papel (fecha R5), com as regras de merge, corte na deslistagem e tripwire
de split perdido (D-015).

**Valor real**: a validação ponta a ponta contra dados reais, não sintéticos — COTAHIST de
nov-dez/2023 e mai-jun/2025 baixados com manifesto de vintage, eventos ao vivo das APIs. No
dia ex do desdobramento 2:1 da SLC, o retorno cru é **−51,8%** e o montado **−3,7%** (o
movimento real do papel); na JBS, o dividendo que só a StatusInvest tem é absorvido no ex e a
série termina exatamente na deslistagem (06/06/2025).

**Validação humana**: além do caso real acima, o merge foi testado com as fixtures reais das
duas fontes (incluindo o caso divergente de 3,9e-4 e o par dividendo+JCP na mesma data-com),
e o corte pós-deslistagem reproduz o resíduo real da BRFS3.

**O que a IA errou / precisou corrigir**:
- O registro de 15/07 chamava 13/12/2023 de "data-ex" do split da SLC. A validação de hoje
  desambiguou: 13/12 é a **data-com**; a queda de preço acontece em **14/12**. O motor já
  mapeava certo (1º pregão estritamente após a data-com) — mas se a convenção tivesse sido
  implementada a partir daquela frase, o ajuste cairia um pregão cedo demais.
- O limiar inicial do tripwire (35%) não pegaria um split 1,5:1 perdido (−33%). Corrigido
  para 30%, com o piso de detecção **declarado** — e a limitação honesta de que bonificação
  pequena (12,5% → −11%) escapa de qualquer limiar útil e exige cross-check externo.

---

## 2026-07-16 — C1 (carimbo PIT + universo dinâmico) e o cross-check que achou um evento fantasma

**Uso**: implementar a camada C1 (`validate/pit.py`, `validate/universe.py`) e executar a
validação pendente de D-015: cross-check da série de retorno total contra o *adjclose* do
Yahoo.

**Valor real — o universo dinâmico validado contra 2025 real**: com o COTAHIST A2025, o
universo reproduz as quatro deslistagens do ano nas datas exatas (JBSS3 sai em 06/06,
BRFS3/MRFG3 em 22/09 com a fusão, STBP3 em 02/10) e ainda captura a **entrada** do MBRF3 em
dezembro, quando completa os 60 pregões de seasoning. O universo respira nos dois sentidos —
é a antítese do survivorship.

**Valor real — o cross-check pegou um buraco de verdade**: SLCE3 divergiu 9,1% do Yahoo num
único dia (09/05/2023), sem nenhum evento em **nenhuma** das nossas fontes (B3 dinheiro, B3
ações, StatusInvest em todos os `chartProventsType`).

**Validação humana — a cadeia de hipóteses, com as erradas registradas**:
1. Primeira hipótese da IA: *redução de capital com restituição* (~R$ 3,59/ação). Derrubada:
   nenhuma fonte brasileira registra restituição, e a busca por fato societário não achou nada.
2. Segunda hipótese: *o Yahoo está errado e a queda foi mercado* (o 1T23 saiu em maio).
   Derrubada: o resultado saiu em 15/05, não 09/05.
3. A pista decisiva veio da aritmética: −9,04% ≈ 1/1,1 − 1 ⇒ **bonificação de 10%**. Busca
   dirigida confirmou na fonte primária: AGO/E de 27/04/2023, 1 ON nova para cada 10,
   data-base 08/05, ex 09/05 (RI da SLC). `(1,1×35,92)/39,49 − 1 = +0,06%` = exatamente o
   retorno do Yahoo no dia.
4. Consequência estrutural: o truncamento do supplement da B3 (ressalva desde D-013) virou
   **omissão material confirmada**. Resposta de processo em D-016: cross-check obrigatório
   por papel vivo + registro curado com proveniência (`events_manual.py`). Após a correção,
   SLCE3 fecha limpo (max 2,6e-3 em 748 pregões).

**O que mais a verificação separou**: a divergência da AGRO3 em 25/10/2023 (nosso −8,04% vs
Yahoo −9,00%) **não é bug** — é a convenção multiplicativa do Yahoo distorcendo dividendo
grande (10,6%); nossa álgebra é o retorno real do acionista (CRSP). Saber qual divergência é
buraco e qual é convenção é exatamente o tipo de julgamento que o cross-check automatizado
sozinho não faz.

---

## 2026-07-16 — Ingestão CONAB e o calendário R10 (arqueologia de datas)

**Uso**: implementar a ingestão dos painéis de vintages da CONAB (grãos/café/cana) e
construir o mapa `(safra, nº do levantamento) → data de divulgação` que o arquivo não traz
(risco R10) — pesquisa ano a ano, 2017/18 → 2026, sem interpolar.

**Valor real**: a parte de código é rotineira; o valor esteve na **arqueologia de fontes**.
A IA reconstruiu ~180 datas de divulgação triangulando: PDFs oficiais do Calendário de
Divulgação recuperados do Wayback Machine (2017, 2021-2023), a página antiga da CONAB
(Joomla), que guardava a data de publicação de cada boletim, em oito snapshots do Wayback
(2018-2023), o espelho da associação de produtores de MT (AMPA) — que baixava o boletim no
dia da divulgação e o timestamp fica gravado no nome do arquivo —, timestamps de upload do
site antigo da própria CONAB e notícias datadas do dia (Agência Brasil, novacana, udop,
Cecafé, ConabCast). Fazer isso à mão levaria dias; levou uma tarde.

**Validação humana/mecânica**: nenhuma fonte entrou sem calibração — o espelho da AMPA foi
validado contra 7 datas já conhecidas por outras vias (7/7 no mesmo dia) antes de ser aceito
como evidência; as datas da página antiga foram cruzadas com os calendários oficiais
(2020/21-2022/23: 33/33 concordantes). Testes automatizados travam sanidade do mapa (dia
útil, monotônico por safra, 12 levantamentos por safra fechada de grãos) e âncoras
verificadas em ≥2 fontes. Verificação ao vivo de ponta a ponta reproduziu o exemplo canônico
da tese: em 15/03/2024, a última estimativa visível de soja/MT é o 6º levantamento
(12/03/2024, 37.568 mil t) — nunca o 7º.

**O que a verificação pegou (a lição da sessão)**: o **site oficial atual da CONAB mente**
sobre a safra 2022/23 de grãos — o listing exibe "Publicado em dia 10" para os 12
levantamentos, incluindo dois sábados, com erro de até 6 dias contra as datas reais
(artefato da migração de site de nov/2023). A primeira coleta, ingênua, tinha aceitado essas
datas; o padrão uniforme + sábados disparou a suspeita, e a triangulação derrubou as 12. No
sentido oposto, a página antiga também engana: itens pré-migração de 2018 carregam data de
importação, não de publicação (o "6º lev 04/04/18" era importação; a data real, 08/03/2018,
veio do espelho AMPA). Duas fontes oficiais, dois modos de falha diferentes — a regra que
sobrou está em D-017: nenhuma data entra com fonte única quando há como triangular, e na
dúvida vale a mais tardia.

---

## 2026-07-16 — Ingestão do clima primário (CHIRPS)

**Uso**: desenhar e implementar a ingestão point-in-time da precipitação CHIRPS — a fonte que
dispara a tese (choque climático) — com o vintage prelim/final preservado, sem depender de GDAL.

**Valor real**: a IA de-riscou o desenho inteiro **por sondagem ao vivo antes de escrever
código**, o que evitou dois becos. (1) Confirmou que o GeoTIFF do CHIRPS é *sem compressão* e
tem geotransform auto-descrito → dá para ler só com `tifffile` (Python puro), sem rasterio/GDAL,
que nem tem wheel para cp314. (2) Mediu que a revisão prelim→final é **material** (soja/MT
15/01/2024: +23% num dia), o que valida empiricamente a decisão de usar o CHIRPS como primária
justamente pelo vintage. Fixture de teste é um recorte real do grid global que reproduz
exatamente os valores da extração global.

**Validação humana/mecânica**: verificação ao vivo de ponta a ponta — `download_chirps` real
baixou prelim e final, o raster global (2000×7200) passou na tripwire de formato e as caixas
bateram exatamente com o recorte da fixture. 18 testes novos (URL, leitura, `nodata`, caixa fora
do grid, painel, vintage prelim≠final, carimbo PIT, download com sessão fake). Suite 154/154.

**O que a IA errou**: dois erros pegos na própria verificação. (1) Ao sondar o prelim, montou a
URL com `.tif` e concluiu "prelim dá 404 → não é arquivado" — conclusão que, se aceita,
mataria a premissa de vintage do CHIRPS. Só ao ler o **href real** do listing viu que os prelim
são `.tif.gz` (o `.gz` tinha sido cortado); o arquivo existe e é histórico. (2) O primeiro
leitor usava `tifffile.geotiff_metadata`, que só popula com `GeoKeyDirectoryTag` — funcionava no
arquivo real, mas quebrava na fixture recortada. Corrigido para ler as tags 33550/33922 direto
da página (robusto e independe de geokeys). A lição repetida: **conclusão de fetcher só vale
depois do teste ao vivo** — inspeção de URL não basta.

---

## 2026-07-16 — Ingestão do clima secundário (NASA POWER)

**Uso**: implementar a ingestão de temperatura do POWER sabendo que a fonte **não preserva
vintage** — o desafio não era baixar (JSON trivial), e sim tratar a limitação com honestidade.

**Valor real**: a IA sondou o mecanismo de vintage ao vivo *antes* de codar e transformou uma
propriedade incômoda da fonte num carimbo de proveniência de primeira classe. Lendo o campo
`header.sources` em duas consultas, mostrou empiricamente que um fetch de 2015 vem como `MERRA2`
(definitivo) e um de jun/2026 como `GEOSIT` (provisório). Isso virou `classify_vintage` +
coluna `source_vintage` no painel + registro no manifesto — a limitação passou de "declarada no
texto" para "mensurável no dado". Decisões de escopo (só temperatura; pontos = centroides das
caixas do CHIRPS para casar `region`) saíram diretas da leitura crítica da fonte.

**Validação humana/mecânica**: verificação ao vivo de ponta a ponta — `download_power` real
baixou os dois pontos em duas faixas de data e a classificação de vintage bateu (2015 definitivo,
2026 provisório), com a célula real da grade no manifesto. 15 testes novos (classificação nas 4
ramificações, parse, fill −999→NaN, painel, carimbo PIT lag 3d, download com manifesto de
vintage, join `region` com o CHIRPS). Suite 169/169.

**O que a IA errou**: (1) primeira asserção do teste de PIT assumia que em D+3−1 haveria "a
última linha visível anterior", mas com lag de 3 dias **nada** ainda está disponível naquele
ponto — o `available_asof` retorna vazio e `.max()` vira `NaT`. Corrigido para afirmar o que é
de fato verdade (filtro vazio antes da avail_date; entra o 01/01 mas não o 02/01 em D+3). Erro
honesto de raciocínio sobre a própria regra PIT, pego pelo teste. (2) Uma linha longa demais
(E501) na montagem da URL — trivial, mas o `ruff` travou antes de subir, como deve.

---

## 2026-07-16 — Ingestão da confirmação por comércio exterior (ComexStat)

**Uso**: implementar a ingestão do ComexStat sabendo que a fonte tem uma armadilha silenciosa
documentada (NCM como int) e não preserva vintage.

**Valor real**: a IA reconfirmou ao vivo, antes de codar, o gotcha do NCM (café `"09011110"` =
2 linhas; `9011110` int = 0 linhas com `success:true`) e transformou isso no guardrail central do
módulo — `_validate_ncms` falha alto para qualquer NCM que não seja string de 8 dígitos, antes de
tocar a rede, mais um meta-teste que garante que a própria constante `THESIS_NCMS` não cai na
armadilha. O endpoint `dates/updated` virou prova de vintage no manifesto. Schema do POST fixado
por consulta real, não por suposição.

**Validação humana/mecânica**: 19 testes novos (guardrail nas 5 entradas ruins, parse com
métricas string→int e `ref_date` no fim do mês, resposta-armadilha vazia, carimbo mensal,
download com manifesto de vintage e `success=False` levantando). Fixtures são respostas reais,
inclusive a resposta vazia do NCM-int. Suite 188/188.

**O que a verificação pegou (a lição da sessão)**: a verificação ao vivo do `download_comex`
bateu em **HTTP 429 Too Many Requests** — o rate limit que a doc marcava como "não confirmado
numericamente" se materializou por causa das minhas próprias sondagens em sequência. Não é bug do
código (o caminho é idêntico ao teste de sessão fake, que passa), mas é um **achado real**: a
fonte limita requisição de fato, o que vira justificativa empírica do cache agressivo e entra no
D-020. O "erro" da verificação (bater no limite) foi mais informativo que um sucesso limpo teria
sido. Também foram pegos dois E501 (mensagem de erro e nome de arquivo montados inline) — o `ruff`
travou antes do commit, e a correção extraiu um helper `_stamped_name` que de quebra removeu uma
duplicação real entre o download e o manifesto.

---

## 2026-07-16 — Ingestão do controle ENSO (ONI/NOAA)

**Uso**: transformar o controle pré-registrado de El Niño/La Niña em uma fonte point-in-time,
sem tratar um arquivo histórico revisado como se fosse conhecido em tempo real.

**Valor real**: a consulta à metodologia oficial revelou que o ONI não é uma observação
mensal simples: é uma média sobreposta de três meses, atualizada até o dia 5, cujos valores
recentes podem mudar por mais dois meses. Isso virou duas datas distintas no dado
(`initial_avail_date` e `avail_date`) e uma regra conservadora verificável, em vez de um lag
escolhido por conveniência. A pesquisa também detectou que a NOAA passou a usar RONI para
monitoramento operacional em 2026. Como o pré-registro diz ONI, a troca foi rejeitada; RONI
ficou reservado como robustez futura.

**Validação humana/mecânica**: fixture com 11 linhas reais do arquivo oficial; testes de
schema, temporadas, travessia de ano em NDJ, duplicatas, cache, manifesto e filtro *as-of*.
O downloader real leu 917 temporadas (DJF/1950–AMJ/2026), reproduziu ONI 0,98 na cauda e
gravou hash. Para AMJ/2026, o código distinguiu publicação inicial em 05/07 de disponibilidade
conservadora em 05/09.

**O que a IA errou**: o primeiro comando de validação ao vivo tinha aspas escapadas dentro de
uma *f-string* passada a `python -c` e falhou com `SyntaxError`. Nenhum dado foi escrito no
projeto; o comando foi refeito com argumentos simples no `print` e a validação passou. Mais
importante, a hipótese inicial do catálogo dizia que ONI “preserva vintage”; a fonte oficial a
falsificou. O resumo de dados foi corrigido para não carregar essa segurança inexistente.

---

## 2026-07-16 — Ingestão dos fatores de risco NEFIN

**Uso**: implementar os controles brasileiros da regressão de *spanning* H4 sem confundir
observação diária com disponibilidade diária nem assumir que a fonte era append-only.

**Valor real**: a investigação identificou que o site oficial é servido por um repositório
GitHub Pages público. Isso permitiu substituir a URL mutável por uma URL presa ao SHA do commit
e, principalmente, comparar dois vintages oficiais. O teste mostrou revisão material do HML:
4.484 de 6.218 datas sobrepostas mudaram acima de `1e-10`, 3.889 por mais de 1 bp e a maior
mudança foi 2,759 p.p. O achado mudou o contrato: NEFIN virou snapshot de atribuição ex post,
nunca dado D+1 para a carteira.

**Validação humana/mecânica**: dois commits oficiais baixados por SHA e comparados; fixtures
reais preservam cinco datas na sobreposição e uma data nova. O downloader real obteve 6.299
pregões (02/01/2001–02/06/2026), commit de 19/06/2026, e reproduziu a revisão de 05/11/2001.
Testes cobrem schema, decimais, nulos, duplicatas, SHA, resposta da API, cache, manifesto,
revisão de vintage e filtro *as-of*.

**O que a IA errou**: ao montar inicialmente o teste, completou o prefixo observado do commit
com um sufixo não verificado. Antes da validação ao vivo, a checagem de proveniência exigiu o
SHA completo da API oficial e substituiu o valor pela sequência correta
`e12ab2b324cbd0d26e300477949349711598bccc`. O episódio reforça a regra de
`10_REFERENCIAS.md`: identificador plausível não é proveniência; copiar somente da fonte.

---

## 2026-07-16 — Congelamento fenológico e regional do `Shock`

**Uso**: reconciliar a formulação ampla da tese com o que as fontes realmente permitem e
transformar culturas, UFs, janelas e geografia numa especificação testável antes de consultar
retornos.

**Valor real**: a leitura conjunta do painel CONAB e das fontes oficiais reduziu o caso
primário a soja + milho 2ª safra e chuva CHIRPS. O CSV oficial do ZARC, antes marcado como não
testado, foi baixado e inspecionado: cerca de 202 MB, 36 decêndios, município, grupo de ciclo,
solo, manejo e níveis de risco. Isso permitiu separar fonte agronômica de validação de um
seletor de parâmetros. A geografia também mudou: caixas lat/lon úteis para testar ingestão não
são uma base científica suficiente para o sinal; o contrato agora usa PAM/IBGE municipal,
agregação por UF e peso CONAB da safra anterior.

**Validação humana/mecânica**: participações físicas foram recalculadas diretamente no
`LevantamentoGraos.txt` real (12º lev. 2024/25), sem abrir séries de retorno; calendário e
fisiologia foram conferidos em CONAB, MAPA/ZARC e Embrapa. O contrato em
`features/shock_spec.py` tem testes para escopo, UFs, direção do estresse, safra bissexta,
janela tardia do RS, janela estreita da safrinha e falha alta em ano-safra ambíguo.

**O que a IA errou**: a primeira reação foi expandir manualmente as duas caixas existentes
para mais regiões produtoras. A auditoria cética mostrou que isso apenas multiplicaria
retângulos escolhidos pelo pesquisador e não resolveria o alinhamento com a CONAB por UF. A
segunda hipótese — usar o ZARC dinamicamente por município — também foi rebaixada: sem saber
solo, cultivar e data real de semeadura, a granularidade oficial pode virar falsa precisão e
abre dezenas de escolhas. Ambas foram substituídas por um primário menor e por uma geografia
baseada em pesos físicos auditáveis.

Uma segunda checagem derrubou uma afirmação herdada da ingestão: “CHIRPS cobre desde 1981” é
verdade para o produto final, mas não para o prelim operacional. Consultas oficiais retornaram
404 em 2008/2013 e 200 em 2015; o índice de 2015 mostrou janeiro/início de fevereiro carregados
em bloco em 17/02. O primeiro ano-safra primário foi então movido para 2015/16 e a redução de
amostra entrou como R16, em vez de preencher os anos faltantes com dados revisados.

---

## 2026-07-16 — Regionalização PIT com PAM e malha municipal IBGE

**Uso**: transformar a geografia congelada em D-023 numa ingestão reproduzível, sem usar
fronteiras futuras, valores PAM ainda não publicados ou decisões orientadas por retorno.

**Valor real**: a pesquisa reuniu as datas efetivas de divulgação da PAM 2014–2024 e separou
os dois relógios (`ref_date` e `avail_date`). Também testou a API de malhas com `periodo`: ela
entregou 2019–2022, mas retornou erro 500 para 2014–2018 e 2023–2024. Em vez de misturar
vintages e *fallbacks*, foi localizada a edição municipal IBGE 2013 arquivada, cujos membros
foram gerados em março/2015. Isso levou à decisão de suporte fixo pré-amostra. A solução usa
PyShp puro e mantém geocódigo, bbox, GeoJSON, versão, hash e datas auditáveis.

**Validação humana/mecânica**: fixtures reais preservam resposta SIDRA e dois polígonos sem
simplificação do ZIP oficial. A captura integral somou 38.467 linhas PAM; as sete malhas foram
parseadas e casaram com toda produção positiva nos estados/culturas do primário em três cortes
*as-of* (2015, 2020 e 2025). Testes cobrem calendário, códigos de produto/unidade, símbolos,
pesos, schema geográfico, SIRGAS, bbox, cache, manifestos e falha de cobertura. Nenhum retorno
foi consultado. A data interna 16/03/2015, igual nos sete ZIPs oficiais, também virou tripwire
contra substituição silenciosa do artefato pré-amostra.

**O que a IA errou**: a primeira implementação supôs que qualquer símbolo diferente de `-`
deveria bloquear os pesos. O teste integral revelou 130 ocorrências de `...`, que no SIDRA
significam dado indisponível e se concentram em municípios urbanos. Bloquear toda a série era
excessivo; convertê-las em zero seria cientificamente errado. A regra foi corrigida para
preservar `NaN`, normalizar apenas a tonelagem reportada e carregar a contagem de ausentes por
cultura/UF. A suposição inicial de que `periodo` cobriria toda a API de malhas também foi
falsificada antes de entrar no código.
Uma revisão posterior pegou ainda um erro de cache antes do PR: o nome inicial da captura
identificava produto e anos, mas não as UFs. O escopo estadual passou a fazer parte do nome,
impedindo que consultas diferentes reutilizem silenciosamente o mesmo arquivo.

---

## 2026-07-16 — Auditoria de fechamento da Fase 1

**Uso**: confrontar os preços montados dos 19 papéis vivos com uma fonte ajustada independente,
investigar cada divergência contra dados oficiais e resolver as pendências CEPEA, futuros B3 e
vintage ComexStat antes de construir features.

**Valor real**: o cross-check encontrou duas bonificações de 10% ausentes do endpoint B3 atual
(VITT3 e KLBN11), além da SLC já conhecida; revelou que o supplement repete o mesmo evento para
ON, PN e UNIT; e mostrou que quatro parcelas iguais da KLBN11 eram direitos legítimos que o
normalizador apagava. Fontes CVM/B3 confirmaram data-com e razão antes de qualquer correção.
A pesquisa oficial também mudou o desenho: o CEPEA possui exportação Excel licenciada, a B3
publica ajustes de derivativos por vencimento e os vintages históricos da primeira divulgação
do ComexStat não são recuperáveis. O gate de exportação foi retirado do sizing primário antes
de observar retornos; H1b permanece como validação física *ex post*.

**Validação humana/mecânica**: 19 tickers, 2023–2025, com COTAHIST oficial como base e limiar
de 0,5% contra Yahoo. As correções fizeram VITT3 voltar a diferença máxima de 0,07%; os saltos
de eventos da KLBN11 em 2024–2025 foram absorvidos. Documentação oficial CEPEA/B3/MDIC e
documentos societários foram preservados em `11_AUDITORIA_FASE1.md`; testes com fixtures reais
travam as classes KLBN e as quatro parcelas iguais.

**O que a IA errou**: a primeira implementação somou StatusInvest como fallback para todos os
papéis vivos. O rerun integral criou novas divergências em SOJA3, SMTO3, VITT3 e CAML3: a fonte
secundária estava sendo tratada como verdade adicional mesmo quando a B3 já cobria a empresa.
A política foi corrigida para substituição apenas quando a B3 devolve histórico vazio; lacuna
pontual exige documento primário e registro curado. A investigação também mostrou que vários
alertas não eram bugs nossos: BEEF3, RAIZ4, SUZB3, HBSA3 e KEPL3 têm barras Yahoo que revertem
depois. Ajustar o COTAHIST para “bater” teria introduzido erro. Por fim, a expectativa inicial
de quantificar a revisão ComexStat via Wayback falhou: não havia snapshots do CSV consultado.
A ausência de evidência virou restrição do experimento, não número inventado.

---

## 2026-07-17 — Regionalização raster→município (primeira metade do C2 `Shock`)

**Uso**: implementar a geografia congelada em D-023/D-024 — média de precipitação CHIRPS por
polígono municipal da malha IBGE 2013 — sem GDAL, com ponto-em-polígono vetorizado em numpy,
índice município→células cacheável e painel municipal diário.

**Valor real**: a peça cara do C2 ficou pronta e barata: o índice das 7 UFs (2.634 municípios,
110.489 células) calcula em ~12 s uma única vez, e cada raster diário agrega em 0,12 s. A regra
even-odd cobre buracos e multipolígonos sem dependência nova. A validação ao vivo revelou dois
fatos da malha que nenhum doc registrava: as lagoas Mirim e dos Patos entram como polígonos
não-municipais no RS (excluídas do índice), e três municípios reais são menores que a célula
p05 (fallback auditável pelo centroide). Ambos viraram teste, doc e decisão D-027.

**Validação humana/mecânica**: aritmética sintética conferível no papel (grade 10×10 de 1°);
contagem de células vs. área municipal oficial (Cuiabá ~3.500 km² → 118 células de ~30,25 km²;
Acorizal ~840 km² → 27); revisão prelim→final visível no nível municipal no dia real de
15/01/2024 (Cuiabá 2,67 → 3,05 mm); 2.634/2.634 municípios cobertos no raster global real.

**O que a IA errou**: o filtro de polígonos de água (código de município `0000`) derrubou os
próprios testes sintéticos — os geocódigos fictícios escolhidos antes ("5100001") caíam na
regra recém-criada. A suíte pegou na hora; os testes passaram a usar geocódigos reais. Erro
barato, mas ilustra o padrão: regra nova de validação precisa rodar contra tudo que já existia,
não só contra o caso que a motivou.

---

## 2026-07-17 — Cálculo do `Shock` as-of (segunda metade do C2)

**Uso**: implementar `features/shock.py` — acumulado da janela fenológica até a data de corte,
climatologia expanding do mesmo trecho, `Shock = −z`, agregação UF (PAM *as-of*) e nacional
(CONAB da safra anterior) — resolvendo os quatro pontos que o contrato D-023 deixava em aberto
(mesmo trecho por deslocamento, pesos espaciais únicos em `t`, carimbo por produto CHIRPS,
renormalização nacional sobre janelas iniciadas), registrados em D-028.

**Valor real**: o sinal da tese existe e é uma função pura de `t`: cada painel de entrada é
filtrado por `avail_date ≤ t` dentro da própria função — o lookahead é morto por construção,
não por disciplina do chamador. Seis guardas falham alto (buraco de cobertura, peso PAM sem
painel, <10 safras, climatologia degenerada, UF sem CONAB, painel sem carimbo). O desenho
separou o custo: o caro (raster→município) é cacheável e independe de `t`; o barato (pesos,
janela, z) roda por data de decisão.

**Validação humana/mecânica**: 16 testes com álgebra conferível no papel (climatologia 1..10
⇒ média 5,5/desvio 3,0277; PIT movendo o corte com o `avail_date`; safra CONAB corrente
proibida de pesar) e execução de ponta a ponta com dados 100% reais (110 rasters CHIRPS +
PAM/SIDRA + CONAB + malha IBGE): soja/MT em 20/12/2024 deu `Shock = +0,98` (71 mm vs.
96 ± 26 mm), a PAM *as-of* escolheu sozinha a edição 2023 e os maiores pesos municipais
saíram Sorriso, Diamantino e Campo Novo do Parecis — a geografia real da soja de MT emergiu
do pipeline sem nenhuma coordenada escolhida à mão.

**O que a IA errou**: nada foi derrubado na verificação desta etapa — os 16 testes passaram na
primeira execução e a validação ao vivo confirmou a álgebra. O registro honesto é o contrário
do habitual: a ausência de erro aqui deve-se ao custo pago antes (contrato congelado em D-023,
fixtures reais das etapas anteriores e a álgebra desenhada nos testes antes do primeiro run ao
vivo), não a sorte. Ponto de atenção deixado para H1a: `Shock` recalculado em `t' > t` pode
diferir se uma edição PAM entrou no meio — comportamento point-in-time correto, mas o rodador
precisa fixar `t` nos cortes dos levantamentos (documentado em D-028).

---

## 2026-07-17 — Auditoria documental e registro único de pendências

**Uso**: varrer documentação e código em busca de estados defasados, marcadores de pendência e
contradições entre decisões já implementadas e textos antigos; separar dívida legada de trabalho
normal de fases futuras; criar um registro público com prioridade e critério de encerramento.

**Valor real**: a auditoria corrigiu a descrição do repositório como “Fase 0 sem implementação”,
marcadores que ainda tratavam PAM/regionalização/`Shock` e o cross-check de preços como abertos,
e o gate ComexStat que permanecia no protocolo apesar de ter sido removido em D-026. Também
encontrou uma superestimação científica mais séria: alguns textos ainda prometiam 18 anos de
sinal ou aproximadamente 12–18 safras, embora o CHIRPS operacional comece em 2015/16 e H1a
dependa do painel CONAB iniciado em 2017/18. O projeto passa a reportar N efetivo por teste.

**Validação humana/mecânica**: busca global por `TODO`, `a definir`, `a confirmar`, “pendente”,
checkboxes e frases de próximo passo; reconciliação com D-017–D-028, estado dos módulos em
`03_ARQUITETURA.md` e checklist do plano mestre. Cada resultado foi classificado como: dívida
transversal (`12_PENDENCIAS_TRANSVERSAIS.md`), entrega de fase futura, limitação aceita em R-NNN
ou registro histórico já encerrado por decisão posterior.

**O que a IA errou**: a primeira leitura tratou todas as ocorrências textuais de “pendente” como
backlog potencial. Isso misturava checklists de revisão, decisões históricas preservadas e
trabalho corretamente alocado a fases futuras. A classificação foi refeita pelo **critério de
propriedade**: só entra no registro transversal o que já deveria ter sido resolvido, cruza fases
ou não tem outro lugar canônico. Essa correção evitou transformar o novo arquivo numa segunda
cópia do plano mestre.

---

## 2026-07-17 — Perímetro do holdout para os testes de mecanismo (D-029, PT-001)

**Uso**: estruturar a decisão de PT-001 — se o holdout 2020–2025 lacra também os desfechos
físicos de H1a/H1b — antes de qualquer resultado; levantar o N efetivo por perímetro a partir
das fontes já ingeridas e articular o custo metodológico de cada opção.

**Valor real**: a IA aterrissou o trade-off em números verificáveis sem tocar em resultado —
contou anos-safra disponíveis cruzando o calendário de vintages CONAB (grãos começam em
2017/18) com o Shock prelim (2015/16). Isso expôs que lacrar os desfechos físicos deixaria H1a
com ~2–3 anos-safra (clusters), tornando o portão mais importante do projeto estatisticamente
intestável. A decisão ratificada (lacre veda a estratégia, não o mecanismo; span cheio com
sub-amostras dev/holdout reportadas em separado) ficou em D-029.

**Validação humana/mecânica**: a contagem de N efetivo saiu do `conab_calendar.py` (12
levantamentos/safra, painel 2017/18→2025/26), não de estimativa. A escolha do perímetro foi
decidida pelo time (ratificação humana) antes de rodar qualquer regressão — o critério de
encerramento de PT-001 exige exatamente isso. Nenhum resultado de H1 foi consultado.

**O que a IA acertou por construção**: recusou o caminho de decidir o perímetro silenciosamente.
Por ser decisão congelada-antes-de-resultado e com poder de veto, foi tratada como ratificação
explícita do time, não como default do agente — coerente com a disciplina de que parâmetro de
desenho não se justifica por conveniência estatística sem o custo declarado.

---

## 2026-07-17 — Rodadores do portão da Fase 2 (D-030 pré-registro, D-031 resultado)

**Uso**: pré-registrar em D-030 a especificação exata de H1a/H1b (variável dependente, regressor,
sinal esperado, `climatology_first_year=2000`, família BH-FDR) e implementar a maquinaria — módulo
`stats` (cluster-robust, Newey–West, cluster/block bootstrap, BH-FDR), rodadores H1a/H1b,
orquestrador do portão, e o builder do painel municipal CHIRPS (streaming de 6.197 rasters).
A spec foi commitada **antes** dos resultados (história do git prova a ordem).

**Valor real**: o portão foi atravessado com evidência forte — H1a agrupado β=−0,067, sinal
correto (estresse ⇒ revisão para baixo), consistente no desenvolvimento e no holdout. O
pipeline inteiro (regionalização, `Shock` as-of, regressão agrupada, BH-FDR) rodou de ponta a
ponta com dados reais, e o BH-FDR foi conferido linha a linha contra o statsmodels.

**O que a IA errou, e como a verificação pegou** (três erros, todos apanhados por execução, não
por inspeção):
1. **Explosão de desempenho**: o painel municipal tem ~16M linhas e `_stretch_sum` refiltra a
   cada ano de climatologia × spec × corte. A primeira rodada travou. Só um teste de tempo (não
   a leitura do código) revelou o custo real; a correção foi memoizar por corte + split por UF.
2. **Bug de memoização sutil**: a primeira chave usou o `vis_max` cru do prelim, mas depois do
   fim da janela o `vis_max` cresce enquanto o **corte fica preso em `window_end`** — então todo
   levantamento tardio era cache-miss recomputando o mesmo `Shock`. Só o benchmark de 2 safras
   (112s, não 300s+) confirmou que a chave certa é o **corte clamado**, não o `vis_max`.
3. **Carimbo faltando**: `shock_asof` chama `available_asof(conab, t)` por dentro (pesos
   nacionais), que exige `avail_date`; H1b passava o CONAB cru. Peguei antes de rodar ao ler o
   contrato de `conab_uf_weights`, não depois de um traceback.

**Disciplina anti-p-hacking**: a inferência foi reportada com honestidade cética — com apenas 8
clusters, o p normal-assintótico (2,6e-9) é otimista; o honesto `t(7)` (~6e-4) e o bootstrap por
cluster (p≈0) são os que valem, e ambos passam com folga. O achado seria reportado igual se
tivesse falhado (a regra do portão em D-030 previa parar e reformular).

---

## 2026-07-17 — Matriz fundamentalista point-in-time de exposição (D-032/D-033)

**Uso**: dividir em pesquisas delimitadas a auditoria econômica dos 21 candidatos e a busca de
fontes primárias históricas; transformar a regra pré-registrada em um registro versionado e em
validação automatizada. A regra foi commitada antes de a matriz ser materializada, deixando no
histórico a ordem regra → resultado.

**Valor real**: a auditoria derrubou a hipótese conveniente de um núcleo com cerca de 14 nomes.
Logística, sementes, equipamentos, açúcar, celulose e alimentos sem canal soja/milho comprovado
não viraram exposição só para engrossar o cross-section. O resultado conservador tem quatro
empresas e cinco vintages PIT: AGRO3/SLCE3 positivos, BRFS3/JBSS3 negativos. A verificação
também encontrou uma incompatibilidade matemática anterior ao backtest: há um único produtor
até março de 2018 (50% do bruto para neutralidade) e dois depois (25% cada), ambos incompatíveis
com cap de 20%.

**Validação humana/mecânica**: cada inclusão foi refeita a partir de CVM/SEC ou RI, com conta,
localizador, `ref_date` e `avail_date`; data incerta recebeu limite posterior conservador. O
código falha para fonte sem HTTPS, vintage incompleto, data invertida, duplicata, escala fora
do pré-registro ou pesos que não somam 1. O teste-canário acrescenta uma divulgação futura e
prova que a matriz histórica não muda.

**O que a IA errou ou divergiu**: a classificação paralela inicial tratou JBSS3 como ambígua
por causa da diversificação global. A fonte primária mostrou um segmento direto de aves/suínos
com 10,7% da receita consolidada; a decisão final não ignorou a objeção, mas limitou a
materialidade a 0,50 e marcou a cesta soja/milho como não resolvida. Em sentido oposto, a ideia
anterior de usar MDIA3, KEPL3 e CAML3 como shorts foi rejeitada: trigo, equipamentos e direção
agrícola ambígua não satisfazem o canal causal congelado. A divergência serviu para estreitar a
regra, não para escolher a versão com mais ativos.

---

## 2026-07-17 — Crítica externa e criação do portão econômico da Fase 3.1 (D-034)

**Uso**: submeter a documentação do projeto a uma segunda avaliação crítica, com foco na
qualidade potencial da entrega final, e reconciliar cada observação com o estado real do
repositório antes de aceitá-la.

**Valor real**: a leitura externa destacou geografia corporativa, hedge e a ambiguidade entre
preço maior e volume próprio menor para produtores. A reconciliação interna revelou dois
problemas ainda mais objetivos: H3/Fama–MacBeth era incompatível com uma cross-section de
três a quatro ações, e uma carteira dollar-neutral vinha sendo chamada incorretamente de
market-neutral. Isso levou à D-034: score e carteira ficam bloqueados até uma auditoria PIT
dos canais `P/Q/C`, H2 ser separado em teste preditivo e diagnóstico de evento, e H3 receber
um desenho compatível com o N real.

**Validação humana/mecânica**: as afirmações foram comparadas com D-032/D-033, a matriz
versionada, o protocolo de backtest e o pré-registro. A equipe separou sugestões novas de
afirmações desatualizadas: a matriz `E` já existia e era PIT, mas ainda não representava o
efeito líquido completo; a identidade visual continuava pendente. O novo protocolo foi
registrado antes de consultar retornos acionários.

**O que a IA errou ou excedeu**: a projeção numérica de nota tratou partes planejadas como se
já estivessem implementadas e chamou Veranico de descrição exata sem conferir que o sinal usa
déficit acumulado, não necessariamente uma estiagem curta. A equipe não adotou a previsão de
nota; adotou apenas as críticas que sobreviveram ao confronto com os artefatos do projeto.

---

## 2026-07-18 — Auditoria PIT dos canais empresariais (D-035)

**Uso**: conduzir a auditoria corporativa point-in-time dos quatro nomes diretos (AGRO3,
SLCE3, BRFS3, JBSS3) exigida pelo portão da Fase 3.1 — mix, geografia produtiva, canal de
preço/insumo, hedge e perímetro por vintage — sem consultar nenhum retorno de ação, e
formalizar a decisão do fork `P/Q/C`.

**Valor real**: a IA localizou e leu as fontes primárias datáveis direto do EDGAR (submissions
JSON + documentos): enumerou os 13 vintages 20-F da BrasilAgro com data de arquivamento =
`avail_date`, extraiu o mix de receita e a geografia de fazendas do FY2014 e do FY2019,
confirmou os 28,5% de custo de insumo da BRF (FY2017) e achou que a Pilgrim's Pride (aves da
JBS nos EUA) é SEC-listed, fornecendo uma âncora datável para o custo de ração em milho
**americano**. Isso transformou uma ambiguidade conceitual (produtor: preço maior vs. volume
próprio menor) em achados concretos: para AGRO3 a cana subiu a 48% da receita operacional e o
grão caiu; `Q` de produtores está parcialmente **fora** do Shock (PI/Paraguai; MA/PI/PA); o
custo da JBS é diluído por bovino e partido entre EUA/BR/Europa.

**Validação humana/mecânica**: cada número foi extraído do texto cru do próprio arquivo
(download + strip de HTML + grep de contexto), não de resumo de terceiros; as datas de
disponibilidade vêm do campo `filingDate` do EDGAR. O que não pôde ser lido numa fonte datável
— área plantada por cultura×UF×vintage e percentuais exatos de hedge — foi **declarado como
lacuna** em `data/reference/corporate_audit_v1.json`, não preenchido. A decisão resultante
(manter D-033; `P/Q` não separáveis; long condicionado a H2a) segue `14` §3 e `13` §7.

**O que a IA errou ou o processo pegou**: a tentação de preencher o % de hedge da SLC "de
memória" foi barrada pela própria regra do projeto (pista ≠ citação) — registrou-se a lacuna.
O WebFetch levou 403 da SEC (proteção anti-bot); o caminho correto foi `curl` com User-Agent
de contato, como a SEC exige. A materialidade de D-033 **não** foi reescrita apesar de a
auditoria sugerir atenuação: reabrir um registro congelado por argumento qualitativo seria
erro; a atenuação entra como sensibilidade no futuro congelamento do score, não como rewrite.

---

## 2026-07-19 — H2a: portão do lado long, pré-registro e resultado (D-036/D-037)

**Uso**: desenhar, pré-registrar e executar o teste de transmissão do `Shock` ao preço da
commodity (portão do canal de preço `P` do lado long), incluindo achar uma fonte de preço
gratuita, vintage-estável e sem chave.

**Valor real**: a IA verificou ao vivo que yfinance não estava no ambiente e que Stooq bloqueia
por JS, e encontrou o FRED/IMF (soja PSOYBUSDM, milho PMAIZMTUSDM) como fonte mensal sem chave,
com histórico até 1992 — evitando adicionar dependência pip. Implementou a ingestão datada, o
rodador (Shock nacional as-of fim de mês na janela → retorno forward do preço) e reaproveitou a
memoização de H1a quando a primeira execução estourou o timeout (~49 chamadas de `shock_asof`).

**Validação humana/mecânica**: pré-registro (D-036) commitado **antes** do resultado — a ordem
é provada no git. A memoização foi introduzida como otimização que **não muda o número** (mesmo
`uf_shock_asof` + pesos CONAB, só sem revarrer o painel). Resultado rodado uma vez e reportado
como veio: β=−0,017 no spec primário, **inconclusivo-negativo** — o oposto da tese.

**O que a IA NÃO fez (a parte importante)**: não trocou a fonte (para CEPEA/BRL) nem o horizonte
para "melhorar" o resultado depois de vê-lo desfavorável. O pré-registro existe exatamente para
barrar esse resgate post-hoc; a troca de fonte só é admissível como robustez pré-registrada, com
justificativa própria. O achado negativo foi registrado (D-037) e reabriu R20, em vez de ser
suavizado. A leitura honesta (transmissão fraca ao USD **ou** reação contemporânea invisível a um
teste forward) foi declarada sem escolher a mais conveniente.

---

## 2026-07-20 — Diagnósticos de H2a: contemporâneo e BRL (D-038/D-039)

**Uso**: dado o forward-negativo de H2a (D-037), desenhar e rodar dois diagnósticos
pré-registrados para separar "transmissão fraca ao preço mundial" de "reação contemporânea
invisível a um teste forward", e testar o canal de câmbio (BRL).

**Valor real**: a IA achou no FRED o câmbio mensal EXBZUS (sem chave), montou o preço em BRL
= mundial × câmbio, e reaproveitou todo o maquinário de H2a mudando só o desfecho (retorno
contemporâneo na janela e conversão BRL). Rodou uma vez: os quatro desfechos pooled deram nulo;
o contemporâneo ≈ zero descartou a leitura de reversão. Resultado registrado (D-039) com a
consequência para a tese, sem suavizar.

**Validação humana/mecânica**: pré-registro (D-038) commitado antes do resultado (ordem no git).
Inferência confiável lida só nas células com clusters suficientes (pooled, 14 clusters); as
células por cultura com 2 clusters e bootstrap p=0,000 foram explicitamente tratadas como não
confiáveis, não celebradas.

**O que a IA NÃO fez / cuidou**: não trocou o primário de H2a para "consertar" o resultado;
manteve os diagnósticos como testes separados e sem veto. Reconheceu o limite do proxy BRL (não
tem a base local CEPEA) e classificou o CEPEA como uma fonte economicamente **distinta** — o
preço certo para o processador — e não uma quinta tentativa da mesma medida, mas marcou-o como
o **último** teste de preço para não virar busca por especificação. A acumulação de nulos foi
lida como resposta, não como convite a seguir testando indefinidamente.

---

## 2026-07-20 (tarde) — Último teste de preço: local BRL (D-040/D-041)

**Uso**: rodar o último teste de preço da tese com o preço LOCAL brasileiro (o que o produtor
recebe / o processador paga), fonte que o D-025 já dizia ser difícil (CEPEA sem API).

**Valor real**: a IA confirmou ao vivo que o CEPEA está atrás de Cloudflare (curl/WebFetch
inúteis) e, em vez de pedir download manual de Excel, achou o IPEADATA (API OData aberta do
governo) espelhando a série Seab-PR/DERAL do preço recebido pelo agricultor — reproduzível,
mensal, cobertura 2015-2024 completa, e economicamente ainda mais direto que o CEPEA para o lado
produtor (receita realizada). Reaproveitou todo o maquinário de H2a mudando só a fonte.

**Validação humana/mecânica**: pré-registro (D-040) commitado antes do resultado; substituição
CEPEA→IPEADATA/DERAL declarada e justificada ANTES de ver o número, com as limitações (é Paraná,
não nacional; revisão modesta). Regra de parada declarada: este era o último teste de preço.

**O resultado e a honestidade**: sinal CERTO (positivo em ambos os desfechos, forward +0,031, o
maior de todas as 6 medidas) mas SEM significância (p 0,21). A IA não vendeu o sinal positivo
como vitória nem o tratou como nulo puro — reportou o que é: direcionalmente real, porém sem
poder, com ~7 safras. Fechou a família de 6 testes de preço e nomeou a consequência dura: o elo
produção→preço→ação não está estabelecido; a força testada da tese é clima→revisão CONAB. Não
propôs rodar um sétimo teste de preço (respeitou a própria regra de parada).

---

## 2026-07-20 (noite) — Reação das ações: o primeiro teste de retorno, e o mais duro (D-042/D-043)

**Uso**: montar e rodar o primeiro teste que toca retorno de ação — o score `E·Shock` ordena os
retornos dos 4 nomes no desenvolvimento? — reaproveitando o motor de retorno total PIT e os
fetchers de evento.

**Valor real**: a IA montou o retorno total dos 4 nomes ao vivo (COTAHIST 2014-2019 + eventos),
construiu o painel score×retorno-forward demeanado na seção transversal (neutro a mercado) e
rodou. Resultado: **β=−0,09, t=−3,6, P&L −4%/período, todas as correlações por nome negativas** —
a estratégia perde e o sinal é **invertido**.

**Validação humana/mecânica**: pré-registro (D-042) commitado antes do resultado (ordem no git).
O tripwire de retorno suspeito pegou dois saltos: o −31% da JBSS3 em 22/05/2017 foi reconhecido
como o **crash real da delação** (legítimo), e o −46,5% da SLCE3 em 02/05/2019 como um **split 2:1
não capturado** — confirmado no preço bruto (41,10→20,10) e por fonte primária (AGE 30/04/2019),
adicionado à curadoria com proveniência. Sem esse conserto, o lado long estaria corrompido.

**A honestidade que definiu o passo**: o sinal veio invertido, e a tentação óbvia — "então basta
inverter: short produtor, long processador, que aí ganha" — é **exatamente** o p-hacking que a
gente havia discutido a fundo. A IA **não inverteu**. Reportou o negativo como veio, explicou que
é economicamente coerente (a seca corta o volume do produtor, `Q>P`, batendo com a auditoria
D-035 e o preço fraco D-041), e registrou "a seca prejudica o produtor" como **hipótese nova a
pré-registrar**, não como gatilho para virar a estratégia. Também: quando o Shock nacional D-028
(safra anterior) reduziria o dev a 2 safras, trocou para média simples das UFs por um motivo
estrutural (poder), **antes** de ver o β, e declarou a simplificação.

---

## 2026-07-20 (noite) — Algodão: teste H1 pré-registrado e canal rejeitado (D-048/D-049)

**Uso**: auditar a cobertura histórica, congelar e executar o teste que decidiria se o
algodão poderia reforçar o score Q-dominante, sem consultar retorno de ação.

**Valor real**: a IA generalizou o rodador H1a para contratos de janela explícitos, integrou
o produto 2689 da PAM/SIDRA e construiu um rodador isolado com painel, inferência agrupada,
diagnósticos por UF/safra e *leave-one-safra-out*. A auditoria anterior ao teste corrigiu uma
estimativa otimista: apesar de a série CONAB citar algodão desde 2017/18, só 2022/23–2024/25
têm múltiplos vintages numerados e datáveis. O critério foi congelado com N=3 antes do primeiro
`Shock` de algodão.

**Validação humana/mecânica**: a captura oficial do SIDRA foi versionada por manifesto
(6.138 linhas, 558 municípios, BA+MT, 2014–2024) e uma resposta real mínima virou fixture. O
teste executado uma vez produziu β agrupado `+0,0421`, BA e MT positivos, três safras positivas
e 0/3 LOO negativos. Como D-048 exigia β<0 e ao menos 2/3 LOO<0, o canal foi rejeitado sem
trocar janela, cultura, desfecho ou direção. A decomposição posterior em área e produtividade
foi rotulada apenas como explicação: área positiva e produtividade nula não resgatam o teste.

**O que a IA errou**: a primeira carga ao vivo filtrou a PAM para municípios com produção
positiva. Isso violou o contrato da regionalização, que exige o universo municipal completo —
inclusive pesos zero — para detectar qualquer município do painel climático fora da base de
pesos. O pipeline falhou alto antes de estimar coeficientes. A correção preservou todos os
municípios e mudou somente a preparação do dado, não o pré-registro. A estimativa inicial de
quatro a nove safras úteis também estava errada e foi substituída pelo inventário efetivo de
três safras **antes** do teste.

---

## 2026-07-20 — Cana: dois mecanismos separados e portão físico corroborado (D-050/D-051)

**Uso**: transformar a extensão de cana em um teste reproduzível sem consultar retorno de ação,
desde a auditoria agronômica e de cobertura até a captura climática, inferência e veredito.

**Valor real**: a IA identificou que um único índice de seca seria biologicamente incoerente e
formalizou dois contratos incapazes de se substituir: maturação jun–ago→ATR como portão e
crescimento dez–fev→tonelagem como diagnóstico. Também encontrou o produto mensal arquivado do
CHIRPS, acrescentou SP — 51,5% da produção nacional no recorte — e construiu streaming com 198
rasters, manifesto por hash, PAM 2696, malha 2013 e um registro imutável da primeira execução.
O teste passou a regra congelada (β `+0,0134`, 8/8 LOO, 5/5 UFs), mas a leitura foi mantida
fraca porque p convencional `0,12` e bootstrap `0,27` não rejeitam zero.

**Validação humana/mecânica**: as fontes oficiais da Embrapa e CONAB foram conferidas antes do
resultado; o SIDRA confirmou que 2696 é cana-de-açúcar; o painel materializado contém cinco UFs,
439.956 linhas município×mês e zero precipitação ausente. Dois commits anteriores ao cálculo
preservam a hipótese e o contrato executável. Testes travam fases, meses, UFs, critério de
aprovação e o registro de resultado; hashes ligam as entradas e saídas à primeira execução.

**O que a IA errou**: a tentativa de auditoria por subagente não concluiu e foi encerrada; ela
não foi apresentada como segunda opinião. A proposta inicial também tratava o passe físico como
quase suficiente para adicionar SMTO3/JALL3. A revisão cética separou ATR por tonelada de
receita total e abriu R24: a exposição empresarial PIT ainda pode matar o canal. A frequência
mensal foi adotada somente após verificar que as janelas congeladas usam meses civis completos;
não foi uma troca motivada pelo coeficiente.

---

## 2026-07-20 (noite) — Auditoria dos veículos de cana e re-análise de poder (D-045 nota, D-052)

**Uso**: (a) re-rodar a análise de poder com o universo real pós-canais; (b) auditar
point-in-time se o ATR favorável da cana (D-051) se traduz em ação assinável, sem tocar retorno.

**Valor real**: a IA reusou o simulador de D-045 sem alterá-lo e mostrou que a premissa de "~8
nomes" caiu (algodão 0 nomes, cana ≤2 condicionais) — universo real é 4–6, e a expansão virou
alavanca fraca (+8pp), movendo o peso da aposta contra o inconclusivo do "quantos nomes" para o
"tamanho do efeito sobreviver". Na auditoria, separou o canal da cana como de **quantidade**
(ATR = açúcar recuperável/tonelada), o que explica por que ele sobrevive ao hedge de preço
(~96% travado na SMTO3) enquanto o canal de preço de grãos morreu (D-037/D-041). Achou o ponto
que decide os dois nomes: geografia e cana própria são bons nos dois, mas a **JALL3 fez IPO em
fev/2021** — zero histórico no dev, holdout-only.

**Validação humana**: a data do IPO da JALL3 e a geografia das usinas foram conferidas em
múltiplas fontes; o time decidiu a opção 1 (SMTO3 no score, JALL3 fora). Registro estruturado
com fontes e lacunas em `data/reference/cane_corporate_audit_v1.json`.

**O que a IA errou**: nada foi derrubado nesta passada, mas a própria IA rebaixou o tier de
evidência: as fontes primárias CVM (formulário de referência) **não** foram baixadas — WebFetch
deu 403 em XP/NovaCana e a SEC não cobre nomes só da B3 —, então os percentuais finos (% cana
própria por safra, mix por vintage, % hedge) ficaram como **lacuna declarada**, não preenchidos
de memória. A decisão foi construída para **não depender** deles (apoia-se no IPO e na
geografia, fatos robustos), e isso ficou explícito no registro. Tier inferior ao de D-035, que
leu 20-F direto.

---

## 2026-07-20 (noite) — Congelamento da estratégia reformulada, Fase 3.5 (D-053)

**Uso**: transformar as decisões de desenho em um contrato executável e imutável, anterior ao
holdout, sem rodar retorno.

**Valor real**: a IA separou explicitamente o que a fase pode e não pode fazer — a força
estatística é limitada pelos 5 anos-safra e nenhuma escolha aqui a levanta. Sobre isso, alinhou
cada fork à prioridade certa: teste primário só nos grãos (A1) porque **misturar a cana fraca
diluiria o t-stat do sinal forte** — isso serve a prioridade de força; e esclareceu que o sizing
(B1) **não afeta o teste primário**, só o P&L, então é escolha de lucro, não de força. Encontrou
o bug de construção do sizing (o cap iterativo oscilava num caso degenerado) e trocou por
water-filling por lado, que garante dollar-neutral + caps por construção. Também notou que o R19
**se dissolve** sob H′ (a concentração era artefato do long-produtor antigo; no holdout os 5
nomes estão vivos).

**Validação humana/mecânica**: 13 testes novos travam universo, direção H′, caps, execução, anos
do holdout e a garantia cruzada de que H′ não altera a convenção de mecanismo falsificada
(`test_signal_sign.py` intacto). Suíte = 400. As prioridades (força > lucro, sob rigor) foram
dadas pelo time; a IA reconciliou a recomendação com elas em vez de empurrar a própria.

**O que a IA errou**: a primeira implementação do sizing (clip + renormaliza em loop) não
convergia — a normalização reempurrava os nomes capados por cima do limite. O teste com input
degenerado pegou na hora; a correção (water-filling por lado, com bruto reduzido quando um cap
torna Σ|w|=1 inviável) é matematicamente sã e determinística. Sem o teste do caso extremo, o bug
teria passado silencioso para a Fase 4.

---

## 2026-07-20 (noite) — Auditoria de transição para a Fase 4 (D-054)

**Uso**: confrontar o plano, o protocolo de backtest, a suíte de robustez e o contrato
executável D-053 antes de construir a máquina ou consultar novo P&L.

**Valor real**: a auditoria distinguiu “estratégia econômica congelada” de “backtest
inteiramente especificado”. Encontrou graus de liberdade ainda abertos em calendário,
composição de scores, universo incompleto, permutação, liquidez, custos e fronteiras do
holdout; eles viraram o gate explícito da Fase 4.0. Também detectou documentação contraditória
(cap antigo de 20%, H3 suspenso e carteira ainda candidata) e reorganizou o plano para que as
Fases 4–6 não apareçam dentro do registro da Fase 3.

**Validação humana/mecânica**: nenhum retorno ou P&L foi carregado. A revisão cruzou D-053 com
`strategy_spec.py` e seus testes. Um caso sintético reproduzível mostrou que o water-filling
devolvia peso de 29,7% sob cap de 25%; a correção agora mantém nomes capados fora do conjunto
livre, verifica soma/caps e ganhou teste de regressão. A suíte completa e a CI validam a mudança.

**O que a IA errou**: a revisão anterior de D-053 declarou o water-filling matematicamente são,
mas testou apenas os caps do universo corrente e não a API genérica que o código oferecia. Uma
segunda auditoria encontrou que o algoritmo podia “reabrir” um nome capado na iteração
seguinte. Também ficou claro que a frase “todas as escolhas de desenho” no contrato era forte
demais: D-053 não definia vários detalhes operacionais. O registro foi corrigido em vez de
tratar a implementação futura como preenchimento neutro.

---

## 2026-07-20 (noite) — Fechamento operacional return-agnóstico da Fase 4.0 (D-055)

**Uso**: transformar os sete graus de liberdade de D-054 em contrato executável antes do
primeiro P&L da máquina. Duas auditorias independentes trabalharam em paralelo: uma reconciliou
calendário, score, universo incompleto e partição temporal com o código; outra pesquisou custos,
liquidez e aluguel em fontes primárias.

**Valor real**: a revisão encontrou a solução conservadora para a colisão entre o horizonte de
21 pregões e sinais persistentes: uma grade de blocos contíguos, sem cohorts sobrepostos, entre
jan/set de cada safra. Também explicitou que o demean poderia fabricar long/short entre duas
produtoras quando faltasse o processador; agora o bloco fica zerado sem os dois lados. A
inferência virou enumeração exata dos 32 sign-flips dos cinco anos-safra, sem t assintótico
frágil. O piso de ADTV foi derivado do pior Δpeso permitido, não escolhido por Sharpe.

**Validação humana/mecânica**: as recomendações foram cruzadas com `shock.py`,
`cane_shock.py`, `exposure.py`, `universe.py` e D-008/D-053. Testes sintéticos travam D+1, 21
intervalos sem retorno duplicado, score soja+milho sem renormalização, cinco UFs da cana,
produtor+processador, exclusão de 2019/20, holdout fechado, 32 permutações e álgebra de
custos/capacidade. Nenhum retorno ou P&L foi carregado.

**O que a IA errou**: a pesquisa de custos trouxe 3,45 bps de uma página oficial da B3, mas a
página era de outro segmento, não a tabela correta de ações listadas. A conferência na fonte
específica encontrou 3,0 bps em operação regular e 3,2 bps no leilão de fechamento. O contrato
usa 3,5 bps arredondados para cima e documenta a escolha. A auditoria de código inicialmente
propôs aceitar blocos parcialmente ausentes; isso foi endurecido: preço ou evento terminal
faltante bloqueia o bloco até auditoria, em vez de criar seleção de amostra silenciosa.

---

## 2026-07-20 (noite) — Motor diário e auditoria de integração da Fase 4.1 (D-056)

**Uso**: implementar o motor vetorizado sem abrir o holdout e submeter contratos de dados,
timing, posições e custos a duas auditorias independentes antes de qualquer P&L observado.

**Valor real**: a revisão detectou que fazer `ffill` dos pesos-alvo rebalancearia a carteira
diariamente sem registrar ordens. O motor passou a manter quantidades de índice de retorno
total, aplicar o último retorno à posição antiga, negociar uma única vez contra o drift e
resolver implicitamente o patrimônio pós-custo para instalar pesos exatos. A segunda auditoria
encontrou que a whitelist do universo podia remover um pregão B3 inteiro quando nenhum dos
cinco nomes negociasse; `UniverseState` agora deriva o calendário antes do filtro e expõe
reason codes e ADTV. Testes-canário fecham D+1, 21 intervalos, transição, saída, atribuição,
aluguel, turnover, participação e bloqueio do holdout antes da leitura do parquet.

**Validação humana/mecânica**: a álgebra foi confrontada com D-053/D-055 e implementada como
ledger cuja identidade diária é verificada em runtime. Casos sintéticos reproduzem a fórmula
direta do retorno do bloco e provam que uma alta intrabloco causa drift, não ordem. O cenário
zero continua exigindo short disponível e participação admissível. Nenhum retorno observado
foi usado para escolher a contabilidade ou executar a carteira.

**O que a IA errou**: a primeira leitura do plano supôs que as quatro safras de desenvolvimento
poderiam ser materializadas. A auditoria dos schemas mostrou que o peso nacional exige a safra
CONAB anterior, enquanto o painel de vintages começa em 2017/18; apenas 2018/19 é computável
sem backfill. A correção foi declarar R26 e proibir equal-weight/peso futuro, não fabricar
histórico. A primeira proposta de custo também tratava a dedução como aproximação aditiva após
instalar o alvo; a revisão contábil mostrou que isso deixaria os pesos pós-custo inexatos e foi
substituída por um solver autofinanciado antes dos testes finais.

---

## 2026-07-20 (noite) — Fricções reais, snapshot offline e bloqueio do aluguel (D-057)

**Uso**: materializar SMTO3, ADTV, eventos corporativos e as condições de aluguel da Fase 4.2,
sem abrir o holdout nem usar P&L para alterar os parâmetros congelados.

**Valor real**: a captura de eventos foi transformada em processo retomável por fonte depois
que a B3 aplicou rate limit. Isso revelou que o código emissor do endpoint de eventos em ações
não é o nome comercial (`SLC AGRICOLA`), mas o código (`SLCE`); usar o nome poderia congelar um
vazio como se significasse “sem evento”. O snapshot final contém cinco tickers, hashes e
horários, e o build offline absorve o split 3:1 real da SMTO3. O estado COTAHIST mostrou, sem
retornos, que AGRO3 nunca supera o piso de ADTV no dev, enquanto o bloco 2018/19 preserva o
núcleo com SLCE3. O parser BDI identificou taxa repetida em linha sem contrato e linha Total
que seria duplicada se somada às modalidades; ambas ganharam testes.

**Validação humana/mecânica**: os códigos emissores foram conferidos em respostas ao vivo. O
split da SMTO3 foi confrontado com duas linhas reais do COTAHIST (R$52,45 → R$17,45) e evento
B3 de razão 3. O retorno extremo da JBSS3 em 22/05/2017 foi confrontado com a sequência de
preços oficial e com comunicado da CVM sobre os fatos e processos de maio/2017. Duas
exportações BDI reais de 17/07/2026 validaram BOM, preâmbulo, decimal brasileiro, modalidades e
totais. Testes sintéticos provam que o gate de 1% usa o patrimônio corrente e falha alto quando
o arquivo está incompleto.

**O que a IA errou**: a primeira implementação da captura usou nomes comerciais como
`issuingCompany`, causando respostas não JSON e retries inúteis; a captura foi corrigida para
códigos emissores e passou a invalidar cache quando a consulta muda. O primeiro payload do BDI
enviou datas `dd/mm/aaaa` e `FinalDate` vazio, recebendo HTTP 500; a inspeção do cliente oficial
mostrou que ambos os campos usam ISO. Mais importante, D-055 foi fechado supondo que o BDI
histórico poderia ser ingerido. A auditoria oficial mostrou retenção antiga de 10 dias e
centralização só em 2023: não há evidência pública suficiente para 2018/19. Em vez de preencher
o passado com taxa atual ou zeros, o projeto abriu R27 e bloqueou o smoke test.

Uma auditoria independente antes do commit encontrou mais duas inferências perigosas: a
primeira versão aceitava “arquivo completo” pela presença de linhas, sem provar a integridade do
arquivo inteiro, e o motor podia instalar um alvo mesmo sem negociação do papel no close de
execução. As correções passaram a exigir CSV + manifesto + hash + contagem para criar cobertura,
um painel explícito de negociação nas fronteiras e falha para retorno total menor que −100%.
Também se corrigiu a descrição do snapshot: o hash é da serialização JSON canônica do payload
interpretado, não dos bytes HTTP originais. Essas mudanças ocorreram antes de qualquer P&L de
carteira ou acesso ao holdout.

## 2026-07-20 — Fase 4.2, resolução do fork R27 (D-058)

**Uso**: com o time tendo escolhido "calibrar o custo de aluguel a partir do dado público de
2023+", pedimos à IA para capturar essa série e calibrar a taxa por nome.

**Valor real**: a IA sondou o endpoint de exportação da B3 ao vivo e **mostrou que a premissa da
tarefa era falsa** — não existe série histórica gratuita: 2024, jan/2025, jul/2025 e jan–jun/2026
retornam "Nenhum resultado"; só o último pregão (2026-07-17) traz dado. E os dois processadores
(BRFS3/JBSS3) nem constam do único snapshot. Em vez de fabricar uma calibração, a IA re-desenhou
a solução: as taxas reais observáveis (AGRO3 0,08%; SLCE3 0,19%; SMTO3 4,65%) ficam **abaixo do
piso de 5% já congelado**, então a premissa conservadora domina o custo real e a série faltante
não o mudaria. Virou uma proxy declarada e sinalizada (`build_proxy_borrow_state`, reason
`proxy`), corroborada por evidência versionada, sem tocar no motor congelado nem em retornos.

**Validação humana**: sondagem reproduzível de múltiplas datas; leitura das taxas direto do
snapshot local; conferência de que o piso all-in (6,7% base / 13,4% no 2×) supera o observável;
482 testes verdes, ruff e guards limpos. A decisão de opção (proxy vs. long-only vs. fonte paga)
foi do time, com as três medidas (rigor/poder/lucro) postas na mesa.

**O que a IA errou**: a própria IA havia proposto ao time a expressão "calibrar de 2023+" antes de
checar a viabilidade da fonte — otimismo sobre o dado que a sondagem derrubou. O registro guarda
o erro: a "calibração" acabou sendo confirmação do piso, não estimativa de um número novo, e isso
foi dito ao time sem maquiar.

## 2026-07-20 — Fase 4, smoke de engenharia do motor (D-059)

**Uso**: pedimos à IA para montar e rodar o smoke test do dev 2018/19 — primeiro P&L do projeto.

**Valor real**: a IA reusou os assemblies canônicos (`run_equity_reaction`, `run_cane_h1`) para
montar retornos/ADTV/scores reais + proxy de aluguel e rodou o motor ponta a ponta nos três
cenários. Validou engenharia (dollar-neutral, caps, custos escalando, holdout bloqueado) e
descobriu, ao rodar, que **SMTO3 não é scoreável no dev** (a série de vintages CONAB da cana só
começa em 2018/19, sem peso do ano anterior) — a cana é, na prática, holdout-only.

**Validação humana**: o run real falhou duas vezes por motivos legítimos (CONAB sem carimbo
`avail_date`; cana sem peso do ano anterior) antes de passar — cada falha foi lida e tratada, não
contornada. Saída conferida contra as invariantes esperadas.

**O que a IA NÃO fez (e é o ponto)**: o dev deu +36%, e a IA se recusou a chamar isso de sucesso.
A direção H′ foi derivada deste mesmo dev; o P&L é circular. O banner do script, o D-059 e o plano
dizem explicitamente que só o holdout valida. Resistir ao número bonito é o comportamento certo.

---

## 2026-07-20 — Fase 4.3, diagnósticos setor-vs-clima (D-060)

**Uso**: a pedido do time (após um passo-atrás de revisão geral do projeto), a IA desenhou e
implementou os diagnósticos descritivos do dev — atribuição por nome e uma decomposição que separa
"aposta de setor" de "sinal cross-section de clima" — para transformar dois gargalos suspeitados em
fato medido.

**Valor real**: a IA propôs um benchmark setorial ingênuo que **reusa a máquina de pesos congelada**
(um `E·Shock` constante produtor +1/processador −1, que a inversão H′ vira "short produtor/long
processador") — em vez de escrever um caminho de pesos novo, testável e passível de divergir do
contrato. O diagnóstico revelou, com número, que no dev a carteira real e a ingênua rendem o
**mesmo +36,26%** (incremento de clima +0,00%; R²=0,84 no spread proteína−produtor) e que **JBSS3
sozinho é 54,6% do P&L** — ou seja, o resultado do dev é o rali de proteína de 2019, não alpha
climático.

**Validação humana**: os testes unitários usaram fixtures sintéticas com resposta fechada (livro =
spread ⇒ beta=1, R²=1) e um bloco dev real para o benchmark. A primeira versão tinha um **bug**: a
SMTO3 vazava para o lado "processador" na regressão (defini processador como "tudo que não é
produtor"). O teste de fixture pegou (beta 1,04 em vez de 1,00); corrigido usando o conjunto
`PROCESSORS` explícito. Sem isso, a decomposição estaria contaminada silenciosamente.

**O que a IA errou**: além do vazamento da SMTO3 acima, na revisão geral a própria IA reconheceu que
sua recomendação anterior de **tirar a SMTO3** por ser holdout-only tinha sido dogmática — o time
apontou a incoerência aparente com a JALL3, e a IA revisou para "manter com limitação declarada",
que é a leitura honesta. O diagnóstico não muda o contrato congelado; a inferência segue só no
holdout.

---

## 2026-07-24 — Fase 5, reconstrução da matriz de exposição sob H′ (D-061)

**Uso**: ao retomar o projeto (máquina nova), a IA fez uma leitura geral e, investigando a carteira
congelada com **choques sintéticos** (sem retorno), descobriu que os dois processadores (BRFS3,
JBSS3) tinham exposição **idêntica** na matriz de preço D-033 — o que fazia a carteira colapsar em
**dois estados** dependentes só do sinal do choque, um bit-idêntico à carteira setorial ingênua de
D-060. Ou seja, o `climate_increment=0,0` de D-060 não era artefato amostral, era **identidade
algébrica**. A IA então re-derivou a materialidade sob o critério H′ de quantidade.

**Valor real**: a IA achou, sem olhar P&L, que a matriz nunca fora re-derivada para H′ (D-053 herdou
a de preço e só aplicou o sinal), e que a auditoria D-035 **já tinha os números** para diferenciar os
nomes (BRF 28,5% custo brasileiro co-localizado; JBS "mais diluído", só Seara/BR no Shock). A
correção — AGRO3 1,0→0,5 e JBSS3 0,5→0,25 — quebra o colapso (1→8 estados) usando fonte primária já
documentada, sem dado novo. A IA também **não escondeu** que isso é mexer num input congelado depois
de ver a degeneração, e trouxe a decisão de governança (reconstruir vs. narrar) ao time em vez de
decidir sozinha.

**Validação humana**: cada afirmação-chave foi verificada por execução, não por inspeção — a
degeneração (1 estado) e a correção (8 estados) foram confirmadas **no loader validado do pipeline
real**, não só na função sintética; teste unitário novo trava as duas quedas de materialidade e que
os processadores deixaram de ser idênticos; a reprodução do D-060 na máquina nova bateu bit a bit
(+36,26%, R²=0,838) antes de qualquer mudança, validando a migração.

**O que a IA errou**: na primeira análise a IA afirmou, por álgebra apressada, que diferenciar só a
**materialidade** (mantendo cesta 50/50) **não** quebraria o colapso — que precisaria de cestas de
cultura diferentes. O teste em código **derrubou isso na hora**: materialidade diferente já leva de 1
para 8 estados (porque o produtor tem cesta diferente dos processadores, e o demean responde à
mistura soja×milho). A IA corrigiu o raciocínio a partir do resultado do código. Também houve um erro
de processo na sessão: ao restaurar o token do GitHub, a IA instruiu colar o segredo com prefixo `!`
achando que não entraria na transcrição — **entrou**; o token teve de ser revogado. Lição: segredo
nunca passa pela sessão, só por terminal separado (`read -rsp`).

---

## 2026-07-24 — Fase 5, auditoria das estruturas de monetização (D-062)

**Uso**: o time fez a pergunta estrutural certa — a estrutura de ações é a certa dado que só o H1 é
sólido? — e pediu uma auditoria completa de dois veículos alternativos (logística/Rumo e spread
soja–milho), com múltiplas personas, base acadêmica, pegadinhas e reuso. A IA conduziu a análise:
busca de literatura, extração de fonte primária (20-F Cosan), varredura de liquidez do universo B3, e
um teste de divergência dos choques por cultura.

**Valor real**: a IA achou, sem olhar retorno, a **pegadinha que decide o caso da Rumo**: apesar de
75% do volume ser grão e 42% de MT, a Rumo é **limitada por capacidade** (demanda ferroviária > oferta
no Brasil; 58% do grão de MT vai por caminhão; volume cresce por capex, não por safra) ⇒ o volume
anual é **insensível à revisão marginal** que o nosso sinal prevê. Isso derrubou (b) por um motivo
oposto ao esperado. Para (d), a busca trouxe Silveira (2025, J. Futures Markets): a reação de preço à
CONAB é mais fraca que à WASDE — evidência publicada de por que o canal de preço morreu. Conclusão:
nenhum veículo supera a estratégia atual; a auditoria vira ativo de rigor.

**Validação humana**: o teste de divergência (soja×milho2ª) rodou no pipeline real (corr −0,33,
diferencial 2,7× o nível), return-agnóstico; a liquidez da Rumo e dos vetados foi medida no COTAHIST
real (não de memória); a capacidade-limitação foi corroborada por fonte primária + setorial, não
assumida. As referências acadêmicas ficaram marcadas como **a conferir na fonte primária** antes de
qualquer citação (regra do `10_REFERENCIAS.md`).

**O que a IA errou**: a IA **oscilou de recomendação duas vezes** e precisou se corrigir em público —
primeiro superestimou (d) (elegância sobre substância; ignorou que é aposta de preço no canal morto e
em mercado eficiente), depois superestimou (b) ao ver os 75%/42% (ignorou a capacidade-limitação). Só
a auditoria disciplinada, empurrada pelo time ("pense melhor, não concorde por concordar"), estabilizou
a conclusão. Documentado como lição: entusiasmo com uma tese nova precisa passar pela mesma régua de
falsificação que as antigas, antes de virar recomendação.

---

## 2026-07-26 — Fase 5, correção do canal Rumo e enumeração estruturada (D-063)

**Uso**: o time cobrou a **exaustividade** do D-062 — "e outros canais de transporte? e outras variantes
de spread? e outros jeitos de arrumar o que temos?". A IA mapeou o espaço inteiro de veículos contra os
cinco filtros do reframe e afiou o argumento da Rumo.

**Valor real**: transformou uma resposta amostral ("já olhei Rumo e spread") num **mapa completo** —
ferrovia, porto (STBP3), hidrovia (HBSA3), caminhão, spread soja–milho, basis Brasil−Chicago, crush,
insumos — cada célula com o critério explícito de rejeição. O padrão que emergiu é o entregável: todo
transporte herda o gargalo de capacidade (exceto a hidrovia, que é holdout-only por IPO 2020) e todo
veículo de preço esbarra no canal morto/CBOT. Confirma a verdade estrutural do D-062 com o espaço
mapeado, não só amostrado. Também abriu o thread substantivo de "arrumar o que temos": o **hedge de
setor** (isolar o resíduo climático do beta confirmado no D-060).

**O que a IA errou (e a correção que este registro paga)**: no D-062 a IA rejeitou a Rumo dizendo
"volume anual insensível". Correto na conclusão, **impreciso no argumento**: sob capacidade travada o
sinal não some — **migra do volume para o frete/margem**. O que mata a Rumo não é ausência de canal e
sim que o canal remanescente é abafado por take-or-pay, de **sinal ambíguo/possivelmente perverso**
(safra cheia → congestão → margem da Rumo *sobe*, oposto do produtor), regulado e com o elo
margem→retorno nunca estabelecido. A própria IA identificou a imprecisão ao ser cobrada e corrigiu o
registro. Lição: "certo na conclusão" não dispensa "certo no argumento" — consertar o raciocínio vale
mais que defender a redação de uma decisão recém-tomada.

**Validação humana**: return-agnóstica e documental; nada rodado (rodar RAIL3/STBP3/HBSA3 queimaria
teste com N mínimo e alguns são holdout-only). Contrato congelado e holdout intocados.

---

## 2026-07-26 — Fase 5, hedge de setor como decomposição pré-registrada (D-064)

**Uso**: implementar o thread de "arrumar o que temos" aberto no D-063 — isolar o resíduo climático da
aposta de setor confirmada no D-060. A IA ancorou-se primeiro na máquina existente (`diagnostics.py`,
`build_naive_sector_schedule`), desenhou a projeção em espaço de pesos, e trouxe ao time o fork de
governança (como o hedge entra: decomposição × segunda estratégia × substituir o congelado) antes de
codar, porque toca o contrato congelado e o orçamento de testes do holdout.

**Valor real**: em vez de "resolver" a contaminação de setor mexendo na estratégia (tentador e errado),
a IA formulou a Alternativa 1 — uma decomposição **aditiva, exata e return-agnóstica** (`c = ⟨w,s⟩/⟨s,s⟩`;
`w_clima = w − c·s`, ortogonal a `s`) que separa o retorno do holdout em setor × clima **sem** mudar o
que se negocia e **sem** gastar α extra. Reusou integralmente a carteira setorial ingênua do D-060 como
direção de projeção. Cinco testes unitários fixam as propriedades duras (aditividade, ortogonalidade,
independência de retorno, direção nula, colunas erradas).

**O acerto de processo (contraste com o D-062)**: aqui a IA **não** oscilou. Parou no fork certo,
explicou as três opções em linguagem simples a pedido do time, recomendou a (1) com o porquê (não
multiplicar testes num N=5; não redesenhar o congelado reagindo ao dev) e só implementou após o "ok".
A disciplina do congelamento foi tratada como restrição dura, não como obstáculo a contornar.

**Validação humana**: separação provada return-agnóstica por teste (retornos diferentes → mesmo split
de pesos); aditividade exata contra o bruto do livro; rodada descritiva no dev 2018/19 (circular). O
resíduo de ortogonalidade deu **9,7e-17** (zero de máquina ⇒ projeção exata) e o resíduo climático
(+2,53%, 6,4% do bruto) bateu com o incremento do D-060 (+2,73%) por método independente — dois
caminhos concordando que o clima é fino e o setor domina no dev. A leitura de lucro é exclusiva do
holdout (Fase 6).

---

## 2026-07-26 — Fase 5, pré-registro da suíte de robustez do sinal H1 (D-065)

**Uso**: desenhar a suíte de robustez do mecanismo H1 (clima→revisão CONAB). A IA ancorou-se na máquina
existente (`stats/h1a.py`, `build_h1a_panel`, `run_h1a`, `run_gate.py`) para identificar os botões reais
do desenho (climatologia, prelim/final, lag, janela crítica) e propôs o grid + placebos + critérios.

**Valor real (disciplina)**: a IA insistiu em **separar o pré-registro da execução** — congelar o grid
single-knob e os limiares (banda [0,4; 2,5], placebo <0,5× e p>0,10) num commit **anterior** aos números,
para não poder escolher a posteriori quais perturbações reportar ou onde traçar a banda. Os critérios
foram implementados como código executável (`perturbation_verdict`, `overall_robust`) com 11 testes, e o
`__post_init__` **trava** que cada perturbação mexe em exatamente um botão — o próprio código impede um
desvio multi-knob disfarçado. Mesmo padrão que o projeto usou na matriz `E` (regra antes do dado).

**O que a IA cuidou de não fazer**: não rodou nada ainda (este passo é só o pré-registro); não tratou o
dev como gate (N minúsculo, só descritivo); marcou a fonte `final` com a ressalva de vintage R15/R16; e
registrou que a suíte mede **estabilidade de desenho**, não adiciona poder — evitando vender robustez
como se fosse significância nova.

**Validação humana**: os critérios são testados (perturbação real fora da banda reprova; placebo que
sobrevive vira bandeira vermelha; veredito global exige placebos mortos). Return-agnóstico; holdout de
retornos lacrado. Execução e números no próximo passo.

---

## 2026-07-26 — Fase 5, execução da suíte de robustez do sinal H1 (D-066)

**Uso**: implementar e rodar a suíte pré-registrada em D-065. Decisão de engenharia da IA: **não tocar
no motor de Shock congelado** — cada perturbação constrói inputs modificados para o `build_h1a_panel`
inalterado (climatologia por parâmetro, janela por specs deslocadas, lag por shift de `avail_date`,
fonte final por relabel do painel, placebos por transformação do painel montado).

**Bug que a IA pegou antes de rodar**: o cache memoizado do `_shocks` embutia o lag do prelim (+7d) na
chave; as perturbações de lag e de fonte final mudam a disponibilidade do sinal e teriam causado **hit
de cache incorreto** — exatamente a classe de bug que o projeto teme. Correção mínima: threar um
`signal_lag_days` (default = baseline, protegido pelos testes de H1a que continuaram verdes) só na chave.

**Achado real (return-agnóstico)**: robustez direcional **forte** — as 4 perturbações reais rodáveis
preservaram sinal e magnitude (climatologia +2 = 0,97×; lag +14d = 1,02×; janela +15d = 0,76×; fonte
`final` até **fortalece**, 1,37×); placebo temporal morreu limpo (p=0,42). **Mas** o placebo **espacial
não morreu de todo**: embaralhar UFs destrói ~69% do β, sobrando ~31% significativo (p=0,019) ⇒
**componente nacional-comum forte**. Isso caracteriza H1 como nowcast nacional (não discriminação
regional pura), amarrando com D-060/D-061/D-063.

**Honestidade sobre o veredito**: o gate global pré-registrado deu **NÃO ROBUSTO** e a IA reportou
**fielmente**, sem afrouxar limiar — reprova por (i) só 4<5 reais rodáveis (dois botões caem em piso de
dado: série final começa em 2000; painel só cobre Dez–Mai) e (ii) placebo espacial significativo. A IA
foi explícita de que nenhum dos dois é fragilidade direcional, e de que um gate estrito falhar e ser
reportado assim mesmo é o entregável de rigor — não uma derrota a esconder.

**Validação humana**: baseline reproduz o portão D-030 bit-a-bit (β=−0,0672); transformações cobertas
por 11 testes puros; motor congelado intocado. Mecanismo, não retorno; holdout lacrado.

---

## 2026-07-26 — Fase 5, ramo AGRO3×ADTV (D-067)

**Uso**: fechar antes do holdout o maior ramo operacional restante: a AGRO3 pode nunca, às vezes ou
sempre passar o piso de liquidez. A IA reconciliou o contrato D-055 com o motor real e identificou
que a decisão correta não era escolher uma carteira para cada cenário, mas tornar auditável a regra
PIT já congelada em cada data `D`.

**Valor real**: o motor passou a expor elegibilidade/atividade da AGRO3 e profundidade ativa dos dois
lados econômicos. A auditoria return-agnóstica classifica a trajetória e conta blocos com zero, um ou
dois produtores, sem ler preços ou retornos. A interpretação também foi pré-registrada: se a AGRO3
continuar fora, resultado positivo não será vendido como dispersão cross-sectional entre produtores;
se for intermitente, subgrupos ficam descritivos e não criam novos p-valores.

**Validação humana**: testes sintéticos cobrem os três estados
`never_eligible`/`intermittent`/`always_eligible`, schema incompleto, atividade impossível sem
elegibilidade e os metadados produzidos pela agenda real. O piso R$8 milhões, os pesos, o teste
primário e o bloqueio do holdout não foram alterados; a suíte passou de 519 para 523 testes.

**O que a IA errou**: a primeira fixture contou dois produtores a partir da elegibilidade da AGRO3,
mesmo num caso sintético em que ela estava elegível mas sem score. A revisão distinguiu corretamente
`eligible` de `active`, adicionou uma trava de consistência e passou a medir profundidade somente nos
nomes que de fato chegam ao painel/carteira. O lint também detectou e corrigiu a ordem de imports.

---

## Modelo de entrada (para as próximas)

```
## AAAA-MM-DD — <etapa>

**Uso**: o que foi pedido à IA.
**Valor real**: o que economizou ou destravou de fato.
**Validação humana**: como foi conferido.
**O que a IA errou**: erros e propostas derrubadas na verificação. ← não pular
```
