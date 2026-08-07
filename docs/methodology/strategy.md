# Estratégia

## A pergunta

A SERIEMA investiga se chuva observada localmente pode antecipar a revisão nacional de safra e, por
meio da exposição econômica das empresas, produzir um sinal sistemático em ações brasileiras do
agronegócio.

A hipótese de ineficiência é de **agregação**, não de acesso: CHIRPS, IBGE/PAM e CONAB são fontes
públicas. A dificuldade está em alinhar células de chuva, municípios produtores, calendário de cada
cultura, data de publicação e exposição empresarial sem usar o futuro.

## A cadeia econômica

Para o núcleo de grãos, a receita do produtor pode ser lida como:

> receita = quantidade colhida × preço realizado

O primeiro elo apareceu: déficit de chuva antecipou revisão negativa da CONAB. O segundo não se
sustentou: a família de testes de preço não mostrou compensação convincente. No desenvolvimento,
comprar o produtor — a direção original — foi antipreditivo. A pesquisa então registrou uma nova
hipótese, H′: **o dano de quantidade domina o eventual benefício de preço**.

Essa reformulação não rebatiza a tese antiga. A hipótese original e sua falsificação permanecem na
[`trilha histórica`](../history/README.md).

## Do choque à posição

1. O modelo mede o desvio de chuva em janelas agronômicas fixas para soja, milho segunda safra e
   cana.
2. O choque municipal é agregado com pesos agrícolas conhecidos no momento da decisão.
3. Uma matriz empresa × cultura traduz o choque para cada ação elegível.
4. No núcleo de grãos, produtor exposto fica vendido e processador fica comprado, conforme H′.
5. Cana usa um mecanismo separado: seca de maturação pode elevar ATR; SMTO3 entra comprada com
   peso limitado.
6. A carteira é dimensionada por intensidade do sinal, com neutralidade em dólares por lado,
   limites por nome, liquidez, custos e execução D+1.

O universo congelado tem cinco nomes: AGRO3, SLCE3, BRFS3, JBSS3 e SMTO3. Isso é um experimento
cross-sectional pequeno; não deve ser lido como um produto amplo de ações.

## Decisão e horizonte

- frequência de decisão: blocos contíguos entre janeiro e setembro;
- execução: pregão seguinte ao instante elegível;
- permanência-base: 21 pregões;
- AUM simulado: R$ 500 mil;
- filtro-base de ADTV21: R$ 8 milhões;
- custos: negociação à vista e aluguel conservador para a ponta vendida;
- holdout: anos-safra 2020/21–2024/25, rodados uma única vez.

Os valores normativos e exceções estão em [`backtest.md`](backtest.md) e nos contratos em
`src/quantagro/backtest/`. O que aconteceu depois da execução está em
[`results/`](../../results/README.md).

## O que a estratégia não é

- não é previsão meteorológica: a chuva já ocorreu quando entra no modelo;
- não é market-neutral: a construção é dollar-neutral e pode carregar outros riscos;
- não é evidência de alpha apenas porque o P&L nominal foi positivo;
- não é execução ao vivo nem recomendação de investimento.
