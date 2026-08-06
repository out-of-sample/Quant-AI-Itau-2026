# Executáveis do projeto

Os scripts são interfaces finas sobre `src/quantagro/`. A lógica testável permanece no pacote;
os executáveis organizam entradas, saídas e validações.

## Publicação de resultados

| Comando | Função |
|---|---|
| `python scripts/build_public_figures.py` | regenera os SVGs de `results/figures/` apenas com dados públicos versionados |
| `python scripts/build_public_series.py` | deriva a série compacta estratégia × livre de risco dos painéis locais selados |

O primeiro comando funciona num clone limpo. O segundo exige `10_metrics.json` e o parquet H4
arquivados localmente; a saída compacta já está versionada. Nenhum deles reexecuta ou recalibra a
estratégia.

## Qualidade

| Comando | Função |
|---|---|
| `python scripts/quality.py` | porta canônica: Ruff, links, guards e pytest |
| `python scripts/check_lookahead.py …` | tripwire contra `.shift(-N)` não justificado |
| `python scripts/check_secrets.py …` | padrões determinísticos de credenciais |
| `python scripts/check_docs.py …` | links locais Markdown e HTML |

## Construção de dados

- `build_municipal_panel.py`: CHIRPS diário regionalizado por município;
- `build_cane_monthly_panel.py`: painel mensal de cana;
- `build_equity_returns.py`: retorno total point-in-time;
- `build_market_state_dev.py`: universo, ADTV e estado de aluguel no desenvolvimento;
- `build_h4_controls.py` e `build_h5_geographic_scores.py`: controles e placebo;
- `build_holdout_inputs.py` e `build_holdout_source_manifest.py`: pacote pré-execução.

## Testes econômicos e diagnósticos

- `run_gate.py`: H1a/H1b e portão do mecanismo;
- `run_h2a.py`, `run_h2a_diag.py`, `run_h2a_local.py`: família de transmissão de preço;
- `run_equity_reaction.py`: reação das ações no desenvolvimento;
- `run_cotton_h1.py` e `run_cane_h1.py`: canais adicionais;
- `run_robustness_h1.py`: grid pré-registrado de robustez;
- `run_smoke_dev.py` e `run_diagnostics_dev.py`: engenharia e atribuição no desenvolvimento.

## Rodada selada

`run_holdout_once.py` e `run_holdout_report.py` preservam o protocolo de D-072–D-075. O
resultado `v1` já foi executado e selado. **Não use `--execute` para substituir, recalibrar ou
“confirmar” o resultado publicado.** Uma extensão deve receber nova especificação, pacote e
holdout; consulte [`../REPRODUCING.md`](../REPRODUCING.md).
