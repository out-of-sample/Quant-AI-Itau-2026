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

## Modelo de entrada (para as próximas)

```
## AAAA-MM-DD — <etapa>

**Uso**: o que foi pedido à IA.
**Valor real**: o que economizou ou destravou de fato.
**Validação humana**: como foi conferido.
**O que a IA errou**: erros e propostas derrubadas na verificação. ← não pular
```
