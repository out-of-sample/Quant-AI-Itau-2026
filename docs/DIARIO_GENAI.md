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

## Modelo de entrada (para as próximas)

```
## AAAA-MM-DD — <etapa>

**Uso**: o que foi pedido à IA.
**Valor real**: o que economizou ou destravou de fato.
**Validação humana**: como foi conferido.
**O que a IA errou**: erros e propostas derrubadas na verificação. ← não pular
```
