# Método

Esta camada responde **como a SERIEMA foi construída**. Ela começa na regra econômica e só depois
desce para dados e implementação.

| Pergunta | Documento | Estado |
|---|---|---|
| O que é o sinal e como ele vira posição? | [`strategy.md`](strategy.md) | síntese canônica |
| Onde e quando a chuva é medida? | [`climate-signal.md`](climate-signal.md) | especificação v1 congelada |
| Qual dado podia ser usado em cada data? | [`data.md`](data.md) | catálogo canônico v1 |
| Como a carteira foi executada e avaliada? | [`backtest.md`](backtest.md) | protocolo v1 congelado |
| Como o software conecta as camadas? | [`pipeline.md`](pipeline.md) | arquitetura implementada |

O resultado não fica duplicado nestes documentos. O endereço canônico dos números pós-holdout é o
[`atlas de resultados`](../../results/README.md), que aponta para os artefatos exatos.

## Três invariantes

1. **Disponibilidade antes de referência.** Uma observação só entra quando `avail_date` permite;
   `ref_date` sozinho nunca autoriza uso.
2. **Vintage faz parte do dado.** Fontes que reescrevem o passado não podem ser reconstruídas com
   uma consulta atual e tratadas como a captura histórica.
3. **O holdout v1 não é espaço de calibração.** A rodada D-075 já ocorreu e está selada. Uma
   extensão precisa de nova especificação, novo identificador e nova amostra.
