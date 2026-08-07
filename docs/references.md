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
- **Pista ≠ citação.** Quando o método é canônico e a atribuição é "de conhecimento comum",
  o nome do autor só vira citação depois que alguém conferiu título/ano/venue na fonte.
- **Proveniência.** Cada entrada diz de onde veio e como foi conferida. O git é a trilha de
  auditoria.

> **Status: bibliografia fechada em 2026-08-06.** Todas as entradas abaixo foram resolvidas
> contra o registro da Crossref (`api.crossref.org`, a autoridade de registro de DOI) ou, quando
> a Crossref ainda não indexava o fascículo, a página oficial do editor (caso da entrada 6).
> Não resta nenhum marcador `[A CONFIRMAR]` nem `⚠ não verificado`.
> A conferência corrigiu **quatro erros** que estavam registrados como se fossem certos — eles
> ficam anotados na própria entrada, porque o erro documentado vale mais que a correção
> silenciosa.

---

## 1. Base acadêmica da tese escolhida (choque climático → safra → ações do agro)

1. Makkonen, A., Vallström, D., Uddin, G. S., Rahman, M. L. & Haddad, M. F. C. (2021).
   *"The effect of temperature anomaly and macroeconomic fundamentals on agricultural
   commodity futures returns"*. **Energy Economics**, 100, 105377.
   DOI [`10.1016/j.eneco.2021.105377`](https://doi.org/10.1016/j.eneco.2021.105377)
   Proveniência: `history/ideation/candidate-theses.md` §1. Autoria e DOI resolvidos na
   Crossref em 2026-08-06 (na ideação constavam só título e ano).

2. Atems, B., Maresca, M., Ma, B. & McGraw, E. (2020). *"The impact of El Niño-Southern
   Oscillation on U.S. food and agricultural stock returns"*. **Water Resources and
   Economics**, 32, 100157.
   DOI [`10.1016/j.wre.2020.100157`](https://doi.org/10.1016/j.wre.2020.100157)
   Proveniência: `history/ideation/candidate-theses.md` §1. Venue e ano resolvidos na Crossref
   em 2026-08-06 — a ideação não registrava nenhum dos dois.

3. A linha de "weather shocks com subreação inicial seguida de correção" foi citada de forma
   **genérica** na ideação, sem um paper específico. **Não foi possível resolver um trabalho
   concreto** que corresponda à anotação, e nenhum candidato foi adotado por aproximação.
   A afirmação, portanto, **não é usada como fundamentação** — a subreação que o projeto
   discute é a hipótese própria, testada em H2a e falsificada (ver
   [`results`](../results/README.md#12-o-canal-de-preço)), não um resultado herdado da
   literatura.

---

## 2. Literatura consultada na ideação (teses NÃO escolhidas)

> Registro de que houve varredura de literatura nas 21 teses candidatas. **Não são a base da
> tese final.** Todas conferidas na Crossref em 2026-08-06; a coluna final mostra o que a
> conferência mudou em relação ao que a ideação havia anotado.

| # | Referência verificada | Tese candidata | Conferência |
|---|---|---|---|
| 4 | Cerdeiro, D., Komaromi, A., Liu, Y. & Saeed, M. (2020). *"World Seaborne Trade in Real Time: A Proof of Concept for Building AIS-based Nowcasts from Scratch"*. IMF Working Papers 2020/057. DOI [`10.5089/9781513544106.001`](https://doi.org/10.5089/9781513544106.001) | Comércio marítimo (AIS) | confirmada; subtítulo completado |
| 5 | Mukherjee, A., Panayotov, G. & Shon, J. (2021). *"Eye in the sky: Private satellites and government macro data"*. Journal of Financial Economics, 141(1), 234–254. DOI [`10.1016/j.jfineco.2021.03.002`](https://doi.org/10.1016/j.jfineco.2021.03.002) | Satélite / estoque de petróleo | confirmada; páginas completadas |
| 6 | Guidolin, M. & Pedio, M. (2026). *"The pricing of biodiversity risk in commodity markets"*. Review of Finance, 30(1), 351–389. DOI [`10.1093/rof/rfaf068`](https://doi.org/10.1093/rof/rfaf068) | Biodiversidade / desmatamento | **corrigida**: o ano era 2025; o fascículo 30(1) é de janeiro de **2026** |
| 7 | Payne, J. E. (2010). *"A survey of the electricity consumption-growth literature"*. **Applied Energy**, 87(3), 723–731. DOI [`10.1016/j.apenergy.2009.06.034`](https://doi.org/10.1016/j.apenergy.2009.06.034) | Consumo elétrico como proxy de atividade | **corrigida**: estava registrada em *Energy Policy*, periódico errado |
| 8 | Henderson, J. V., Storeygard, A. & Weil, D. N. (2012). *"Measuring Economic Growth from Outer Space"*. American Economic Review, 102(2), 994–1028. DOI [`10.1257/aer.102.2.994`](https://doi.org/10.1257/aer.102.2.994) | Luz noturna | confirmada; páginas completadas |
| 9 | Chen, X. & Nordhaus, W. (2019). *"VIIRS Nighttime Lights in the Estimation of Cross-Sectional and Time-Series GDP"*. Remote Sensing, 11(9), 1057. DOI [`10.3390/rs11091057`](https://doi.org/10.3390/rs11091057) | Luz noturna | confirmada; título completado |
| 10 | Baron, M. & Xiong, W. (2017). *"Credit Expansion and Neglected Crash Risk"*. Quarterly Journal of Economics, 132(2), 713–764. DOI [`10.1093/qje/qjx004`](https://doi.org/10.1093/qje/qjx004) | Expansão de crédito / risco de cauda | confirmada; páginas completadas |
| 11 | Chava, S., Gallmeyer, M. & Park, H. (2015). *"Credit conditions and stock return predictability"*. Journal of Monetary Economics, 74, 117–132. DOI [`10.1016/j.jmoneco.2015.06.004`](https://doi.org/10.1016/j.jmoneco.2015.06.004) | Condições de crédito / SCR | confirmada; páginas completadas |

Proveniência das onze: `history/ideation/candidate-theses.md`.

---

## 2.1 Literatura da auditoria de estruturas de monetização (D-062/D-063)

| # | Referência verificada | Uso na auditoria | Conferência |
|---|---|---|---|
| 12 | Silveira, R. L. F., Silva, R. M., Mattos, F. L., Cruz Júnior, J. C. & Capitani, D. H. D. (2025). *"The Reaction of Corn Futures Markets to US and Brazilian Crop Reports"*. Journal of Futures Markets, 45(9), 1298–1323. DOI [`10.1002/fut.22601`](https://doi.org/10.1002/fut.22601) | a reação de preço à **CONAB** é mais fraca que à **WASDE** — apoia por que o canal de preço é fraco | confirmada; autoria completa, fascículo e páginas completados |
| 13 | Katona, Z., Painter, M., Patatoukas, P. N. & Zeng, J. (2024). *"On the Capital Market Consequences of **Big** Data: Evidence from Outer Space"*. Journal of Financial and Quantitative Analysis, 60(2), 551–579. DOI [`10.1017/S0022109023001448`](https://doi.org/10.1017/S0022109023001448) | âncora de "alt-data → throughput físico → surpresa de receita → retorno" (candidato Rumo) | **corrigida**: o título registrado era "…of *Alternative* Data" |
| 14 | Jegadeesh, N. & Livnat, J. (2006). *"Revenue surprises and stock returns"*. Journal of Accounting and Economics, 41(1–2), 147–171. DOI [`10.1016/j.jacceco.2005.10.003`](https://doi.org/10.1016/j.jacceco.2005.10.003) | surpresa de receita → retorno (candidato Rumo) | confirmada; fascículo e páginas completados |

---

## 3. Métodos quantitativos e estatísticos

Cada método abaixo **está implementado** no módulo indicado — a coluna aponta o código, não uma
intenção. Todas as citações foram conferidas na Crossref ou no editor em 2026-08-06.

| Método | Onde está implementado | Citação canônica |
|---|---|---|
| Erros-padrão HAC (Newey-West) | `stats/inference.py::ols_hac`; spanning H4 em `backtest/holdout_analysis.py` | Newey, W. K. & West, K. D. (1987). *"A Simple, Positive Semi-Definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix"*. Econometrica, 55(3), 703–708. DOI [`10.2307/1913610`](https://doi.org/10.2307/1913610) |
| Controle de falsas descobertas (BH-FDR) | `stats/inference.py::bh_fdr` | Benjamini, Y. & Hochberg, Y. (1995). *"Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing"*. JRSS-B, 57(1), 289–300. DOI [`10.1111/j.2517-6161.1995.tb02031.x`](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x) |
| *Moving-block bootstrap* | `stats/inference.py::moving_block_bootstrap` | Künsch, H. R. (1989). *"The Jackknife and the Bootstrap for General Stationary Observations"*. The Annals of Statistics, 17(3), p. 1217 ss. DOI [`10.1214/aos/1176347265`](https://doi.org/10.1214/aos/1176347265) — a página final é registrada de forma divergente por fontes secundárias (1241 vs. 1261) e a Crossref não a informa, então fica só a página inicial e o DOI, que são inequívocos. **Correção**: a versão anterior deste arquivo sugeria o *stationary bootstrap* de Politis & Romano (1994) como pista. O que o projeto implementa é o bloco móvel de Künsch; são estimadores diferentes e a pista estava errada. |
| *Pairs cluster bootstrap* por ano-safra | `stats/inference.py::cluster_bootstrap` | mesma família de reamostragem por cluster; não recebe citação própria porque é aplicação direta do bootstrap não-paramétrico sobre o cluster já declarado |
| Teste de permutação exata (32 *sign-flips*) | `backtest/holdout_spec.py`, `backtest/holdout_analysis.py` | inferência de aleatorização clássica sobre os cinco anos-safra; enumeração completa, sem aproximação de Monte Carlo — não depende de resultado assintótico citável |
| Fatores de risco brasileiros (Mercado, SMB, HML, WML, IML) — *spanning* H4 | `ingest/nefin.py`; regressão em `backtest/holdout_analysis.py` | Dados: **NEFIN/FEA-USP** (§4). Base metodológica: Fama, E. F. & French, K. R. (1993). *"Common risk factors in the returns on stocks and bonds"*. JFE, 33(1), 3–56. DOI [`10.1016/0304-405X(93)90023-5`](https://doi.org/10.1016/0304-405X(93)90023-5); e Carhart, M. M. (1997). *"On Persistence in Mutual Fund Performance"*. Journal of Finance, 52(1), 57–82. DOI [`10.1111/j.1540-6261.1997.tb03808.x`](https://doi.org/10.1111/j.1540-6261.1997.tb03808.x) |
| Sharpe de excesso | `backtest/holdout_report_spec.py::excess_sharpe` | Sharpe, W. F. (1994). *"The Sharpe Ratio"*. The Journal of Portfolio Management, 21(1), 49–58. DOI [`10.3905/jpm.1994.409501`](https://doi.org/10.3905/jpm.1994.409501) |
| Sortino | `backtest/holdout_report_spec.py::tail_risk_metrics` | Sortino, F. A. & Price, L. N. (1994). *"Performance Measurement in a Downside Risk Framework"*. The Journal of Investing, 3(3), 59–64. DOI [`10.3905/joi.3.3.59`](https://doi.org/10.3905/joi.3.3.59) |
| *Deflated Sharpe Ratio* (correção por multiplicidade, 39 tentativas) | `backtest/holdout_report_spec.py::deflated_sharpe_ratio` | Bailey, D. H. & López de Prado, M. (2014). *"The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality"*. The Journal of Portfolio Management, 40(5), 94–107. DOI [`10.2139/ssrn.2460551`](https://doi.org/10.2139/ssrn.2460551) — **ausência corrigida**: o método já era usado e não constava deste arquivo |

---

## 4. Fontes de dados

Diferente da literatura, estas têm URL registrada e testada em
[`methodology/data.md`](methodology/data.md) — são verificáveis.

| Fonte | Papel na tese | Onde está documentada | Paper do produto |
|---|---|---|---|
| CHIRPS (UCSB Climate Hazards Center) | Precipitação — clima primário (vintage prelim/final) | [`data.md`](methodology/data.md) §1.1; `ingest/chirps.py` (D-018) | Funk, C. et al. (2015). *"The climate hazards infrared precipitation with stations — a new environmental record for monitoring extremes"*. Scientific Data, 2, 150066. DOI [`10.1038/sdata.2015.66`](https://doi.org/10.1038/sdata.2015.66) |
| NASA POWER | Temperatura — clima secundário, não entrou no desenho final | [`data.md`](methodology/data.md) §1.2 | não citado: a fonte não entra na versão entregue |
| CONAB — Levantamentos de Safra | Elo causal (revisão de safra) | [`data.md`](methodology/data.md) §2; `ingest/conab*.py` (D-017) | fonte oficial (sem paper) |
| NEFIN / FEA-USP | Fatores de risco (spanning H4) | [`data.md`](methodology/data.md) §5.4; `nefin.com.br/data/risk-factors/`; repositório oficial `nefin/nefin.github.io` (verificados em 2026-07-16) | metodologia oficial `nefin.com.br/resources/NEFIN_methodology.pdf`; base Fama-French/Carhart citada em §3 |
| ComexStat / Secex-MDIC | Desfecho físico H1b *ex post*; não entra no sizing | [`data.md`](methodology/data.md) §3; FAQs oficiais verificadas em 2026-07-16 (D-026) | fonte oficial (sem paper) |
| COTAHIST (B3) | Preços + universo point-in-time | [`data.md`](methodology/data.md) §4.2 | fonte oficial (sem paper) |
| CEPEA/ESALQ | Robustez de preço spot brasileiro | [`data.md`](methodology/data.md) §5.2; banco Excel e licença CC BY-NC 4.0 verificados em 2026-07-16 | fonte oficial (sem paper) |
| B3 — histórico de derivativos | Robustez de preço futuro brasileiro por vencimento | [`data.md`](methodology/data.md) §5.3; ajustes verificados em 2026-07-16 | fonte oficial (sem paper) |
| ONI (NOAA/CPC) | Controle El Niño/La Niña | [`data.md`](methodology/data.md) §1.5; `cpc.ncep.noaa.gov/data/indices/oni.ascii.txt` e metodologia `ONI_v5.php` (verificados em 2026-07-16) | Huang, B. et al. (2017). *"Extended Reconstructed Sea Surface Temperature, Version 5 (ERSSTv5): Upgrades, Validations, and Intercomparisons"*. Journal of Climate, 30(20), 8179–8205. DOI [`10.1175/JCLI-D-16-0836.1`](https://doi.org/10.1175/JCLI-D-16-0836.1) |
| Federal Reserve / FRED — DEXBZUS | Controle diário BRL por USD em H4 | [`data.md`](methodology/data.md) §5.5; série H.10 (verificada em 2026-07-26, D-069) | fonte oficial (sem paper) |
| Teucrium SOYB/CORN/CANE | Proxies negociáveis de soja, milho e açúcar em H4 | [`data.md`](methodology/data.md) §5.5; páginas e benchmarks oficiais (verificados em 2026-07-26, D-069); preços presos por hash | prospectos/factsheets oficiais; sem paper |
| ZARC / MAPA — Tábua de Risco | Validação externa das janelas de plantio | [`climate-signal.md`](methodology/climate-signal.md) §5; CSV 2024/25 + dicionário oficial verificados em 2026-07-16 | fonte oficial (sem paper) |
| PAM / IBGE — SIDRA tabela 1612 | Peso espacial municipal point-in-time | [`data.md`](methodology/data.md) §2.3; [`climate-signal.md`](methodology/climate-signal.md) §4 | fonte oficial; calendário efetivo 2014–2024 curado em `pam_calendar.py` (D-024) |

---

## Como adicionar uma referência

1. Resolva o DOI na Crossref (`api.crossref.org/works?query.bibliographic=…`) ou na página do
   editor **antes** de escrever a entrada.
2. Registre autor, ano, título, venue, volume/fascículo, páginas, DOI e a data da verificação.
3. Se a fonte não resolver, a entrada **não entra** — como no item 3 do §1. Pista ≠ citação, e
   uma lacuna declarada é melhor que uma citação plausível e errada. Esta conferência achou
   quatro citações plausíveis e erradas.
