# Documentação técnica

Esta documentação registra o desenho, a execução e as limitações da SERIEMA. O idioma canônico
é português; o [`README.en.md`](../README.en.md) oferece uma visão geral integral em inglês.

## Comece aqui

1. [`00_PLANO_MESTRE.md`](00_PLANO_MESTRE.md) — tese, arco completo e resultado final;
2. [`01_TESE_E_PRE_REGISTRO.md`](01_TESE_E_PRE_REGISTRO.md) — hipótese original preservada;
3. [`04_PROTOCOLO_BACKTEST.md`](04_PROTOCOLO_BACKTEST.md) — carteira e execução congeladas;
4. [`05_SUITE_ROBUSTEZ.md`](05_SUITE_ROBUSTEZ.md) — testes, vetos e resultado selado;
5. [`06_CRITICA_ADVERSARIAL.md`](06_CRITICA_ADVERSARIAL.md) — leitura crítica pós-resultado.

O relatório final está em [`../report/relatorio-seriema.pdf`](../report/relatorio-seriema.pdf).
Para a fronteira exata de reprodução, consulte [`../REPRODUCING.md`](../REPRODUCING.md).

## Papel de cada documento

| Documento | Papel | Política de manutenção |
|---|---|---|
| [`00_PLANO_MESTRE.md`](00_PLANO_MESTRE.md) | síntese canônica e estado final | manter atual |
| [`01_TESE_E_PRE_REGISTRO.md`](01_TESE_E_PRE_REGISTRO.md) | pré-registro original | congelado; contexto posterior só em avisos |
| [`02_DADOS.md`](02_DADOS.md) | catálogo de fontes, latência e vintage | canônico para dados v1 |
| [`03_ARQUITETURA.md`](03_ARQUITETURA.md) | contratos das camadas e implementação | manter atual |
| [`04_PROTOCOLO_BACKTEST.md`](04_PROTOCOLO_BACKTEST.md) | protocolo executado | congelado como v1 |
| [`05_SUITE_ROBUSTEZ.md`](05_SUITE_ROBUSTEZ.md) | testes pré-declarados e seus vetos | congelado como v1; resultado final visível |
| [`06_CRITICA_ADVERSARIAL.md`](06_CRITICA_ADVERSARIAL.md) | crítica e limites | manter reconciliado com o resultado |
| [`07_RISCOS_E_DECISOES.md`](07_RISCOS_E_DECISOES.md) | riscos + D-001–D-075 | histórico append-only |
| [`08_IDENTIDADE.md`](08_IDENTIDADE.md) | nome e sistema visual | canônico para a marca |
| [`09_FENOLOGIA_E_LIMIARES.md`](09_FENOLOGIA_E_LIMIARES.md) | contrato agronômico do `Shock` | congelado como v1 |
| [`10_REFERENCIAS.md`](10_REFERENCIAS.md) | bibliografia e proveniência | completar apenas contra fonte |
| [`11_AUDITORIA_FASE1.md`](11_AUDITORIA_FASE1.md) | evidência do portão de ingestão | histórico concluído |
| [`12_PENDENCIAS_TRANSVERSAIS.md`](12_PENDENCIAS_TRANSVERSAIS.md) | dívidas públicas ainda abertas | manter atual |
| [`13_MATRIZ_EXPOSICAO.md`](13_MATRIZ_EXPOSICAO.md) | matriz empresa × cultura e reconstrução H′ | histórico concluído |
| [`14_AUDITORIA_CANAIS_EMPRESARIAIS.md`](14_AUDITORIA_CANAIS_EMPRESARIAIS.md) | portão econômico P/Q/C | histórico concluído |
| [`DIARIO_GENAI.md`](DIARIO_GENAI.md) | contribuições, validações e erros de IA | histórico append-only |

## Arquivos especializados

- [`research/ideation/`](research/ideation/): arquivo pré-backtest das 21 teses avaliadas;
- [`adr/`](adr/): decisões futuras de arquitetura que não pertençam ao log científico;
- [`assets/`](assets/): marca, painel do resultado e social preview públicos.

## Regra editorial

“Antigo” não significa “obsoleto”. Pré-registros, auditorias e decisões preservam o que era
conhecido em cada etapa e não são reescritos para parecer que o desenho final sempre existiu.
Correções factuais recebem nota datada; uma extensão da pesquisa cria nova especificação e novo
identificador. Resumos de estado, por outro lado, devem refletir o encerramento em D-075.
