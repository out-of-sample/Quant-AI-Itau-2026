# Dados públicos dos resultados

Esta camada existe para que os gráficos e tabelas da repo apontem a números inspecionáveis, sem
exigir os parquets completos do experimento.

| Caminho | Conteúdo |
|---|---|
| [`holdout_v1/`](holdout_v1/) | doze blocos e o selo da rodada D-075, mais a série compacta usada na curva pública |
| [`mechanism/`](mechanism/) | H1, H2, algodão, cana e robustez do elo físico |
| [`evidence_summary_v1.json`](evidence_summary_v1.json) | índice narrativo com fontes; não cria novas estatísticas |

Os JSONs `00`–`12` de `holdout_v1/` são cópias byte a byte dos artefatos selados. O arquivo
`public_series.json` é derivado: ele contém apenas data, índices base 100 e drawdown, sem pesos ou
retornos por ação.

Dados brutos e intermediários continuam em `data/` e seguem a política descrita em
[`docs/methodology/data.md`](../../docs/methodology/data.md).
