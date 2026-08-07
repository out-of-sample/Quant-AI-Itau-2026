## O que muda

<!-- Descreva a mudança e o problema que ela resolve. -->

## Por que

<!-- Explique a decisão e, quando aplicável, a hipótese econômica ou metodológica. -->

## Como foi verificado

<!-- Liste comandos, testes, hashes ou conferências manuais. -->

- [ ] `python scripts/quality.py`
- [ ] Documentação e links afetados foram atualizados

## Checklist quant

- [ ] Nenhum sinal usa dado com `avail_date` posterior à decisão
- [ ] Fontes que reescrevem o passado têm vintage tratado e manifestado
- [ ] A mudança não introduz seleção de universo por sobrevivência
- [ ] Custos, execução e calendário permanecem coerentes com a especificação
- [ ] Artefatos selados `v1` não foram alterados
- [ ] Nova hipótese ou estratégia, se houver, tem identificador e avaliação próprios

## Dados e segurança

- [ ] Nenhum dado bruto, segredo, token ou caminho local foi adicionado
- [ ] Dependências novas estão justificadas e o lockfile foi regenerado com hashes

<!-- Marque itens não aplicáveis como N/A e explique brevemente. -->
