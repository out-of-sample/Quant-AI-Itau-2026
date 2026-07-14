# Fenologia e limiares agronômicos

> Este documento define **quando** o clima importa e **quanto** de anomalia é relevante, por
> cultura e por estado. É o que impede que a janela do sinal seja escolhida por otimização de
> backtest — ela vem de agronomia, de fonte externa e citável.
>
> Regra: nenhum limiar entra no modelo sem fonte primária. O que não tem fonte está marcado
> como **NÃO CONFIRMADO** e não pode ser usado como parâmetro do sinal.

Fonte primária do calendário: **CONAB — "Calendário de Plantio e Colheita de Grãos no Brasil"**.
As janelas de plantio e colheita são **lidas da CONAB**; as fases críticas marcadas como
*(derivada)* são inferidas do ciclo da cultura e checadas contra literatura da Embrapa.

---

## 1. A ideia central

O clima só importa dentro da **fase reprodutiva** da cultura (floração / enchimento de grão).
Chuva em julho no Mato Grosso é irrelevante para a soja — não há soja no campo. Contar
anomalia fora da janela é injetar ruído puro no sinal e diluir o efeito verdadeiro.

Duas consequências de desenho:

1. **A janela é por cultura E por estado.** MT e RS **não** têm a mesma janela crítica: a soja
   gaúcha é ~1 mês mais tardia. Agregar o Brasil inteiro numa única janela dilui o sinal.
2. **O sinal não é linear nem sempre tem a mesma direção** (ver a cana, §3 — é o ponto mais
   importante deste documento).

---

## 2. Calendário por cultura

### Soja (ciclo 105-135 dias)

| UF | Plantio | Colheita | **Fase crítica R1-R6** *(derivada)* |
|---|---|---|---|
| MT, MS, GO/DF, MG | out – dez | jan – mar | **dez – fev** (núcleo: janeiro) |
| SP, PR | fim set – dez | jan/fev – mar/abr | **dez – fev** |
| **RS** | out – meados jan (**tardio**) | jan/fev – abr/mai | 🔑 **jan – mar** (~1 mês depois) |
| BA (MATOPIBA) | out – dez/jan | fev – mai | **jan – mar** |

> O RS é onde as secas de La Niña (jan-fev) destroem safra. Sua janela **deslocada** é
> justamente o que uma agregação nacional ingênua apagaria.

### Milho 2ª safra (safrinha) — a janela mais explorável

| UF | Plantio | Colheita | **Pendoamento/florescimento** *(derivado)* |
|---|---|---|---|
| MT | jan – mar | mai/jun – ago | 🔑 **abril** (meados mar – meados mai) |
| MS, PR | jan – abr | jun – set | **abr – mai** |
| GO | jan – fev | jun – ago | **abril** |
| MG, SP | jan – mar | jun – set | **abr – mai** |

> 🔑 **Por que esta é a melhor janela do calendário brasileiro para o sinal**: o pendoamento da
> safrinha (~abril) cai **exatamente em cima do "corte das chuvas" do Centro-Oeste**. É a
> assimetria climática mais forte do ano — a lavoura entra na fase de maior sensibilidade
> hídrica justo quando a estação chuvosa termina. Pequenas variações na data do corte das
> chuvas têm efeito desproporcional na produtividade.

### Milho 1ª safra

| UF | Plantio | Colheita | **Crítica** *(derivada)* |
|---|---|---|---|
| Centro-Oeste, Sudeste, Sul | out – dez | jan/fev – jun | **dez – jan** (pendoamento) |

### Algodão

| UF | Plantio | Colheita | **Floração/formação de maçãs** *(derivada)* |
|---|---|---|---|
| MT | dez – fev (2ª safra, pós-soja) | jun – set | **mar – mai** |
| BA | nov – jan | jun – set | **jan – mar** |

### Café arábica (MG/SP/ES) — modelo de Camargo & Camargo (2001), *Bragantia* 60(1)

Ciclo de **dois anos fenológicos**, começando em setembro:

| Fase | Período | Relevância |
|---|---|---|
| Vegetação / gemas foliares | set – mar | — |
| Indução e maturação das gemas florais | abr – ago | — |
| **Florada + chumbinho + expansão dos frutos** | **set – dez** | 🔑 fase crítica nº 1 |
| **Granação** | **jan – mar** | 🔑 fase crítica nº 2 (define peso/qualidade) |
| Maturação → colheita | abr – jun → mai-set | — |
| Repouso / senescência | **jul – ago** | 🔑 **janela de geada** |

> ⚠️ **O café não tem sinal linear na florada.** O mecanismo da florada exige **déficit hídrico
> prévio seguido de retomada de chuva** (set/out). Chuva fora de hora atrapalha; ausência de
> chuva **após** a indução faz a florada falhar. Ou seja: em set/out, anomalia negativa de
> chuva **não é linearmente ruim** — o gatilho é a *sequência* seca→chuva, não o nível.
> Modelar o café como "menos chuva = pior" está errado nessa janela.

---

## 3. 🔴 Cana-de-açúcar — o caso de sinal invertido

**Este é o achado mais importante deste documento**, porque contradiz a intuição que estava
na formulação inicial da tese.

| Fase | Período | Efeito de uma **seca** |
|---|---|---|
| Grande crescimento (máxima demanda hídrica) | **nov – abr** | 🔴 **Ruim** — menos TCH (tonelagem) |
| **Maturação** | **mai – set** | 🟢 **BOA** — a planta para de crescer e **acumula sacarose** ⇒ **ATR sobe** |

Safra/moagem no Centro-Sul: **abril → novembro/dezembro**. Ano-safra oficial: 1/abr a 31/mar.

**Confirmação empírica (safra 2024/25)**: o déficit hídrico derrubou a produtividade **e o ATR
subiu 1,33%**. Os dois efeitos ocorreram na mesma safra, em fases diferentes.

> **Consequência direta para o modelo**: um sinal do tipo *"chuva abaixo da média ⇒ preço sobe
> ⇒ compra o produtor"* aplicado à cana **o ano inteiro teria o sinal trocado em metade do
> tempo**. A cana exige um sinal **condicional à fase fenológica**, com direção que se inverte
> entre verão e inverno — não um z-score linear.
>
> Este é exatamente o tipo de erro que produz um backtest com resultado medíocre e
> inexplicável, e que teria sido quase impossível diagnosticar depois. Fica registrado como
> requisito de implementação, não como observação.

---

## 4. Limiares agronômicos (só os que têm fonte primária)

### Soja — Embrapa Soja (sistema SECA) ✅

| Parâmetro | Valor |
|---|---|
| Necessidade hídrica total | **450 a 800 mm/ciclo** |
| **Fase crítica R1-R6** | **120 a 300 mm** bem distribuídos em 30-60 dias |
| Demanda diária (floração/enchimento) | **7 a 8 mm/dia** |
| Faixa térmica ótima | **20-30 °C** |
| **Estresse térmico** | **acima de 40 °C**: reduz crescimento, danifica a floração, diminui retenção de vagens — agravado se coincidir com déficit hídrico |
| Fase mais sensível | **enchimento de grãos** (mais que a floração isolada) |

> ⚠️ **Correção importante**: o limiar de **34-35 °C** para aborto de flores em soja, que
> aparece com frequência em textos de mercado, **não foi confirmado na Embrapa** — a fonte
> primária fala em **40 °C**. **Não usar 35 °C atribuindo à Embrapa.** Ou se usa 40 °C
> (citável), ou se busca paper específico de *heat stress* que sustente outro número.

### Milho — Embrapa Milho e Sorgo ✅

**Período crítico**: da pré-floração ao início do enchimento de grãos.

| Momento do déficit hídrico | Perda de produtividade |
|---|---|
| **Antes** do embonecamento | −20% a −30% |
| 🔑 **No embonecamento** | **−40% a −50%** |
| **Depois** | −10% a −20% |

Mecanismo: dessecação de estilos-estigmas, aborto de sacos embrionários, morte de grãos de
pólen. Acima de **35 °C**, queda da atividade da redutase do nitrato.

> A assimetria −40/−50% *no* embonecamento contra −10/−20% *depois* é o que justifica uma
> janela **estreita** e bem posicionada, em vez de uma média sazonal larga.

### Café — ZARC / Camargo ✅

- Déficit hídrico anual **> 150 mm** compromete a longevidade econômica do *C. arabica*.
- Faixa apta: temperatura média anual 18-22 °C **e** déficit anual < 150 mm.
- ⚠️ A tolerância de "~100 mm sem perdas" citada para a seca de 2014 vem de fonte secundária —
  **NÃO CONFIRMADO**, não usar como parâmetro.

### Geada no café ✅ (mecanismo) / ⚠️ (base histórica)

| | |
|---|---|
| Ocorrência | **T < 2 °C no abrigo** (~1,5 m) ≈ −2 a −3 °C na relva |
| Letal para o cafeeiro | **< −2 °C** |
| **Proxy operacional** | **T_min de abrigo ≤ 2 °C** — praticamente nenhuma estação mede temperatura de relva |
| Evento de referência | **20/07/2021**, T_min entre −2 e 0 °C na faixa MG/SP (Passos, São Sebastião do Paraíso, Pouso Alegre, Santa Rita do Sapucaí) |

⚠️ **Não existe catálogo oficial de eventos históricos de geada.** A lista de anos que circula
(1975, 1994, 2000, 2021...) vem de imprensa técnica. **O caminho honesto é construir a base**:
o INMET **BDMEP** fornece T_min diária histórica por estação, gratuita, em CSV. Contar dias com
T_min ≤ 2 °C em jun-ago nas estações do Sul de Minas / Cerrado Mineiro / Alta Mogiana produz um
índice de geada **replicável e auditável**.

---

## 5. Duas fontes que melhoram a parametrização da janela

### ZARC / MAPA — janela de semeadura oficial, por município

O Zoneamento Agrícola de Risco Climático entrega **janelas de semeadura decendiais com
80/70/60% de probabilidade de sucesso**, por município × tipo de solo × ciclo de cultivar.

> **Por que importa**: é a fonte mais granular e mais **defensável** para parametrizar a janela
> do sinal — uma janela vinda de uma portaria oficial do Ministério da Agricultura não pode ser
> acusada de ter sido escolhida a dedo para maximizar o Sharpe. É o oposto de garimpo de
> parâmetro.

⚠️ **NÃO TESTADO**: formato e download do dataset aberto. Verificar antes de depender.

### CONAB "Progresso de Safra" — alinhamento dinâmico da fase

Publica **% plantado e % colhido por UF, semanalmente**. Isso permite alinhar a fase
fenológica **dinamicamente, ano a ano** (uma safra atrasada não tem a mesma janela crítica de
uma safra adiantada), em vez de fixar "janeiro = enchimento" para sempre.

> É uma melhoria real de precisão sobre o calendário estático, e usa dado que já estava
> disponível na época — sem lookahead.

⚠️ **NÃO CONFIRMADO**: se há API/CSV estruturado ou apenas boletim em PDF.

---

## 6. NDVI — verificado, e com uma ressalva que muda seu papel

### ✅ INPE Brazil Data Cube (WTSS) — funciona, gratuito, sem token

```
https://data.inpe.br/bdc/wtss/v4/time_series?coverage=mod13q1-6.1&attributes=NDVI,pixel_reliability
```
- Produtos: MODIS `mod13q1-6.1` / `myd13q1-6.1` (NDVI/EVI, 16 dias, 250 m), Sentinel-2
  (`S2-16D-2`), Landsat, CBERS, e **LST** (`mod11a2-6.1` — temperatura de superfície).
- **Série desde 2000-02-18.**
- Qualidade verificada: um pixel agrícola em MT na safra 23/24 devolveu a curva de dupla safra
  perfeitamente legível (pico da soja em nov-dez, colheita em janeiro, safrinha em fev-mar).

### 🔴 A ressalva que redefine o papel do NDVI

**A latência real é de ~4 meses, não 16 dias.** O serviço *anuncia* a timeline até junho/2026,
mas os valores só existem até **06/03/2026** (testado em 4 pontos: MT, Sul de MG, PR, Oeste da
BA; requisições além disso retornam erro 500).

> **Consequência**: o NDVI é **excelente para o backtest histórico e inútil como sinal em tempo
> quase-real.** Isso o rebaixa de "camada de sinal" para **camada de validação** — serve para
> confirmar, *ex post*, que o choque climático detectado de fato se traduziu em perda de vigor
> vegetativo, o que **valida o mecanismo** (H1). Não serve para gerar posição.

**NÃO CONFIRMADO**: se o atraso de ~4 meses é crônico ou um backlog transitório.

### Alternativas avaliadas

- **SATVeg (Embrapa)**: ❌ **pago** (grátis só por 1 mês/1.000 requisições; depois R$ 250/mês).
  Entrega o mesmo produto MODIS que o WTSS do INPE entrega de graça. **Descartado.**
- **Google Earth Engine**: gratuito para uso acadêmico; vantagem de agregar por município sem
  baixar raster. Latência de processamento **NÃO CONFIRMADA**.

### ⚠️ Risco estrutural: o MODIS está sendo desligado

A NASA vai encerrar a coleta científica do **Terra (fev/2027)** e do **Aqua (set/2027)**.
Para o **backtest histórico (2000-2026) isso é irrelevante** — os dados existem e continuam
existindo. Mas um robô "de produção" baseado em MODIS **já nasce com data de validade**. A
migração natural é para **VIIRS** ou **Sentinel-2**. Ponto a declarar na seção de próximos
passos do relatório, não um bloqueio para o trabalho.

---

## 7. Itens em aberto

1. Formato/download do dataset aberto do **ZARC** (não testado).
2. Se o **"Progresso de Safra"** da CONAB é raspável (API/CSV) ou só PDF.
3. Se o atraso de ~4 meses do **WTSS/BDC** é crônico ou transitório.
4. Limiar de estresse térmico da soja entre 35 °C e 40 °C — buscar paper primário de *heat
   stress* ou usar 40 °C (Embrapa).
5. Janelas de plantio da **cana** (cana de ano vs. ano e meio) por UF — a CONAB não detalha.
