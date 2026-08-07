# Documentação

Esta documentação está organizada pela pergunta do leitor, não pela ordem em que o projeto foi
construído. A narrativa curta está no [`README`](../README.md); os números detalhados estão no
[`atlas de resultados`](../results/README.md).

## Quero entender como funciona

Leia nesta ordem:

1. [`methodology/strategy.md`](methodology/strategy.md) — hipótese econômica, universo e regra de
   posição;
2. [`methodology/climate-signal.md`](methodology/climate-signal.md) — culturas, regiões, janelas e
   definição do choque;
3. [`methodology/data.md`](methodology/data.md) — fontes, disponibilidade e tratamento de vintage;
4. [`methodology/backtest.md`](methodology/backtest.md) — execução, liquidez, custos e holdout;
5. [`methodology/pipeline.md`](methodology/pipeline.md) — contratos entre as camadas de software.

O [índice metodológico](methodology/README.md) também indica quais documentos são canônicos e
quais especificações estão congeladas.

## Quero verificar o resultado

- [`../results/README.md`](../results/README.md) — teste por teste, safras, custos, sensibilidades,
  concentração e fronteira de claims;
- [`../results/data/`](../results/data/) — JSONs e CSVs usados nas figuras públicas;
- [`../REPRODUCING.md`](../REPRODUCING.md) — o que um clone verifica e o que exige os snapshots
  point-in-time arquivados.

## Quero entender como a pesquisa chegou aqui

O [`history/README.md`](history/README.md) abre a trilha de pré-registro, falsificações,
auditorias e decisões D-001–D-075. Ela foi preservada porque prova que o desenho final não foi
inventado depois do resultado; não é a melhor porta de entrada para conhecer a estratégia.

## Quero entender a comunicação do projeto

- [`identity.md`](identity.md) — nome, título editorial e sistema visual;
- [`genai.md`](genai.md) — contribuições concretas, validações e erros de IA generativa;
- [`references.md`](references.md) — bibliografia e proveniência;
- [`../report/relatorio-seriema.pdf`](../report/relatorio-seriema.pdf) — relatório final de cinco
  páginas.

## O que deliberadamente não está aqui

Dados brutos e intermediários volumosos não são redistribuídos. O repositório publica manifestos,
contratos, resultados compactos e código de ingestão; consulte
[`methodology/data.md`](methodology/data.md) para a fronteira exata. Rascunhos visuais e tentativas
criativas também não fazem parte da documentação pública: apenas decisões e artefatos finais.
