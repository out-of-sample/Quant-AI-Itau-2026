# Referências

Registro das referências que o projeto de fato usou — literatura de ideação, métodos
quantitativos e fontes de dados. Existe para dar rastreabilidade científica ao relatório
final e evitar que a fundamentação vire "achismo com verniz acadêmico".

## Regra deste arquivo (ler antes de editar)

- **Só entra o que é rastreável.** Uma referência só é registrada aqui se (a) já aparece
  escrita em algum documento do repo, ou (b) foi verificada na fonte primária por uma pessoa
  do time. Nada entra por memória, plausibilidade ou "eu acho que é esse paper".
- **Lacuna não se preenche por chute.** Onde falta autor, ano, venue ou DOI, o campo fica
  marcado `[A CONFIRMAR]` até alguém abrir a fonte real. Uma citação inventada (autor trocado,
  DOI que não existe, ano errado) é pior do que uma lacuna honesta — e é exatamente o tipo de
  erro que um revisor pega e que destrói a credibilidade do resto do trabalho.
- **Pista ≠ citação.** Quando o método é canônico e a atribuição é "de conhecimento comum"
  (ex.: um estimador com nome próprio), o nome do autor pode entrar como **pista para buscar**,
  sempre marcado `⚠ não verificado`. Só vira citação de verdade — sem o aviso — depois que
  alguém conferiu título/ano/venue na fonte.
- **Proveniência.** Cada entrada diz de onde veio (doc do repo + linha, ou fonte/identificador
  verificável + data da conferência). O git é a trilha de auditoria.

> Status desta primeira versão: montada a partir de uma varredura dos documentos do repo
> (principalmente `docs/history/ideation/candidate-theses.md`). É um ponto de partida, não uma
> bibliografia fechada. **Nenhum autor/ano/DOI foi preenchido de memória.** As lacunas ativas
> e seus critérios de encerramento estão centralizados em `docs/history/pending.md`
> (PT-003, PT-004 e PT-006).

---

## 1. Base acadêmica da tese escolhida (choque climático → safra → ações do agro)

> ⚠️ **Prioridade de curadoria.** Esta é a fundamentação da tese que ficou de pé, e é a
> **menos completa** do repo: os títulos abaixo foram anotados na ideação sem autoria/DOI.
> Antes do relatório final, cada um precisa ser localizado na fonte e completado — ou
> substituído pela referência correta se o título anotado estiver impreciso.

1. *"The effect of temperature anomaly and macroeconomic fundamentals on agricultural
   commodity futures returns"* — **Energy Economics**, 2021.
   `[A CONFIRMAR: autores, volume/páginas, DOI]`
   Proveniência: `docs/history/ideation/candidate-theses.md` §1 (linhas 44-46).

2. *"The Impact of El Niño-Southern Oscillation on U.S. Food and Agricultural Stock Returns"*.
   `[A CONFIRMAR: autores, venue, ano, DOI]`
   Proveniência: `docs/history/ideation/candidate-theses.md` §1 (linha 45-46).

3. Literatura de "weather shocks e retorno de ações" que documenta **subreação inicial seguida
   de correção** — citada de forma **genérica** na ideação, sem um paper específico.
   `[A CONFIRMAR: identificar ao menos um paper concreto desta linha, com autoria e ano]`
   Proveniência: `docs/history/ideation/candidate-theses.md` §1 (linhas 47-49).

---

## 2. Literatura consultada na ideação (teses NÃO escolhidas)

> Estas referências têm citação completa no repo e comprovam que houve varredura de literatura
> nas 21 teses candidatas. **Não são a base da tese final** — ficam registradas como
> proveniência do processo de ideação (critério "respaldo acadêmico real",
> `teses_candidatas.md` §critérios). Só migrar para o §1/§3 se alguma vier a embasar o desenho
> final. Não foram reverificadas na fonte — o que está aqui é o que o time anotou na ideação.

| # | Referência (como anotada no repo) | Tese candidata | Proveniência |
|---|---|---|---|
| 4 | Cerdeiro, Komaromi, Liu & Saeed, *"World Seaborne Trade in Real Time"*, IMF Working Paper 2020/057 | Comércio marítimo em tempo real (AIS) | `teses_candidatas.md` l.283-284 |
| 5 | Mukherjee, Panayotov & Shon, *"Eye in the Sky: Private Satellites and Government Macro Data"*, Journal of Financial Economics 141(1), 2021 | Satélite / estoque de petróleo | `teses_candidatas.md` l.337-338 |
| 6 | Guidolin & Pedio, *"The Pricing of Biodiversity Risk in Commodity Markets"*, Review of Finance 30(1), 2025 | Risco de biodiversidade / desmatamento | `teses_candidatas.md` l.392-394 |
| 7 | Payne, *Energy Policy*, 2010 (linha de cointegração energia-PIB) `[título específico A CONFIRMAR]` | Consumo elétrico como proxy de atividade | `teses_candidatas.md` l.455-457 |
| 8 | Henderson, Storeygard & Weil, *"Measuring Economic Growth from Outer Space"*, American Economic Review 102(2), 2012 | Luz noturna | `teses_candidatas.md` l.598-600 |
| 9 | Chen & Nordhaus, *"VIIRS Nighttime Lights..."*, Remote Sensing, 2019 `[título completo A CONFIRMAR]` | Luz noturna | `teses_candidatas.md` l.600-601 |
| 10 | Baron & Xiong, *"Credit Expansion and Neglected Crash Risk"*, Quarterly Journal of Economics 132(2), 2017 | Expansão de crédito / risco de cauda | `teses_candidatas.md` l.657-658 |
| 11 | Chava, Gallmeyer & Park, *"Credit Conditions and Stock Return Predictability"*, Journal of Monetary Economics 74, 2015 | Condições de crédito / SCR | `teses_candidatas.md` l.708-709 |

---

## 2.1 Literatura da auditoria de estruturas de monetização (D-062)

> Levantadas durante a auditoria D-062 (logística/Rumo × spread soja–milho) via busca web, **não
> abertas na fonte primária**. Ficam como pista para a fundamentação do relatório (o mecanismo
> "clima → produção → ativo" e a fraqueza do canal de preço). Conferir antes de qualquer citação.

| # | Referência (como retornada na busca) | Uso na auditoria | Status |
|---|---|---|---|
| 12 | Silveira et al., *"The Reaction of Corn Futures Markets to US and Brazilian Crop Reports"*, Journal of Futures Markets, 2025, DOI 10.1002/fut.22601 | evidência de que a reação de preço à **CONAB** é mais fraca que à **WASDE** (por que o canal de preço/(d) é fraco) | `⚠ não verificado — conferir autoria/ano/DOI na fonte` |
| 13 | Katona, Painter, Patatoukas & Zeng, *"On the Capital Market Consequences of Alternative Data: Evidence from Outer Space"*, JFQA 60(2), 2025 | âncora do mecanismo "alt-data → throughput físico → surpresa de receita → retorno" (candidato Rumo) — já citada em `teses_candidatas.md` l.1096-1098 | `⚠ não verificado na fonte` |
| 14 | Jegadeesh & Livnat, *"Revenue Surprises and Stock Returns"*, Journal of Accounting and Economics, 2006 | surpresa de receita → retorno (candidato Rumo) — já citada em `teses_candidatas.md` l.1098-1099 | `⚠ não verificado na fonte` |

---

## 3. Métodos quantitativos e estatísticos

Os métodos abaixo **são usados** no desenho (fato: aparecem nos docs indicados). O que falta é
a **citação canônica de cada um**, que ninguém fixou ainda. A coluna "pista" traz a atribuição
usualmente aceita apenas como **ponto de partida de busca** — `⚠ não verificado`, não citar no
relatório antes de conferir na fonte.

| Método | Onde é usado no projeto | Pista para a referência (⚠ não verificado) |
|---|---|---|
| Erros-padrão robustos a autocorrelação/heterocedasticidade (Newey-West / HAC) | `03_ARQUITETURA` §sinal, `05_SUITE_ROBUSTEZ` §testes | ⚠ Newey & West (~1987) — confirmar |
| Controle de falsas descobertas em família de testes (BH-FDR) | `03_ARQUITETURA`, `05_SUITE_ROBUSTEZ` | ⚠ Benjamini & Hochberg (~1995) — confirmar |
| Block bootstrap para inferência em série dependente | `03_ARQUITETURA`, `05_SUITE_ROBUSTEZ`, `06_CRITICA_ADVERSARIAL`, `07_RISCOS` | ⚠ variante e fonte a definir (ex.: block bootstrap estacionário) — confirmar |
| Fatores de risco brasileiros (Mercado, SMB, HML, WML, IML) — *spanning regression* H4 | `02_DADOS` §5.4, `05_SUITE_ROBUSTEZ`, `06_CRITICA_ADVERSARIAL` | Dados: **NEFIN/FEA-USP** (ver §4). Base metodológica dos fatores: ⚠ Fama & French / Carhart — confirmar quais |
| Métricas de desempenho (Sharpe, Sortino) | `04_PROTOCOLO_BACKTEST` | ⚠ Sharpe; Sortino — confirmar edições/anos se forem citadas |

> Nota: só vale a pena citar formalmente o método no relatório final se ele **entrar de fato**
> na versão entregue. Método que a gente cortar sai daqui também.

---

## 4. Fontes de dados (referências verificáveis)

Diferente da literatura, estas têm URL registrada e testada em `docs/methodology/data.md` — são
verificáveis. Muitas têm também um **paper de referência do produto** (que descreve o dado);
esse paper, quando citado, entra com o mesmo cuidado dos §1-3.

| Fonte | Papel na tese | Onde está documentada | Paper do produto (se for citar) |
|---|---|---|---|
| CHIRPS (UCSB Climate Hazards Center) | Precipitação — clima primário (vintage prelim/final) | `02_DADOS` §1.1; `ingest/chirps.py` (D-018) | ⚠ Funk et al. (~2015), *Scientific Data* — confirmar |
| NASA POWER | Temperatura — clima secundário | `02_DADOS` §1.2 | `[A CONFIRMAR se for citado]` |
| CONAB — Levantamentos de Safra | Elo causal (revisão de safra) | `02_DADOS` §2; `ingest/conab*.py` (D-017) | fonte oficial (sem paper) |
| NEFIN / FEA-USP | Fatores de risco (spanning H4) | `02_DADOS` §5.4; `nefin.com.br/data/risk-factors/`; repositório oficial `nefin/nefin.github.io` (verificados em 2026-07-16) | Metodologia oficial `nefin.com.br/resources/NEFIN_methodology.pdf`; base Fama-French/Carhart ainda exige citação canônica antes do relatório |
| ComexStat / Secex-MDIC | Desfecho físico H1b *ex post*; não entra no sizing | `02_DADOS` §3; FAQs oficiais de divulgação/reprocessamento verificadas em 2026-07-16 (D-026) | fonte oficial (sem paper) |
| COTAHIST (B3) | Preços + universo point-in-time | `02_DADOS` §4.2 | fonte oficial (sem paper) |
| CEPEA/ESALQ | Robustez de preço spot brasileiro | `02_DADOS` §5.2; banco Excel e licença CC BY-NC 4.0 verificados em 2026-07-16 | fonte oficial (sem paper) |
| B3 — histórico de derivativos | Robustez de preço futuro brasileiro por vencimento | `02_DADOS` §5.3; ajustes do pregão verificados em 2026-07-16 | fonte oficial (sem paper) |
| ONI (NOAA/CPC) | Controle El Niño/La Niña | `02_DADOS` §1.5; arquivo oficial `cpc.ncep.noaa.gov/data/indices/oni.ascii.txt`; metodologia `ONI_v5.php` (verificados em 2026-07-16) | Huang et al. (2017), *Journal of Climate*, citado pela NOAA para ERSST.v5 — `[A CONFIRMAR: referência completa/DOI antes de citar]` |
| Federal Reserve / FRED — DEXBZUS | Controle diário BRL por USD em H4 | `02_DADOS` §5.5; série oficial H.10 `fred.stlouisfed.org/series/DEXBZUS` (verificada em 2026-07-26, D-069) | fonte oficial (sem paper) |
| Teucrium SOYB/CORN/CANE | Proxies negociáveis de futuros de soja, milho e açúcar em H4 | `02_DADOS` §5.5; páginas e benchmarks oficiais `teucrium.com/soyb`, `/corn`, `/cane` (verificados em 2026-07-26, D-069); preços capturados pelo Yahoo Chart e presos por hash | prospectos/factsheets oficiais dos fundos; sem paper |
| ZARC / MAPA — Tábua de Risco | Validação externa das janelas de plantio | `docs/methodology/climate-signal.md` §5; CSV 2024/25 + dicionário oficial verificados em 16/07/2026 | fonte oficial (sem paper) |
| PAM / IBGE — SIDRA tabela 1612 | Peso espacial municipal point-in-time | `02_DADOS` §2.3; `docs/methodology/climate-signal.md` §4 | fonte oficial; calendário efetivo 2014–2024 curado em `pam_calendar.py` (D-024) |

---

## Como adicionar uma referência

1. Se veio de um doc do repo: cite o doc + linha na proveniência, verbatim, com lacunas
   marcadas `[A CONFIRMAR]`.
2. Se a fonte foi aberta e conferida: registre autor, ano, título, venue, DOI/URL, data da
   verificação e identificador verificável da fonte. Só aí remova os avisos `⚠`.
3. Nunca copie uma citação "que parece certa" de um LLM sem abrir a fonte. Pista ≠ citação.
