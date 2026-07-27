# Benchmark das edições anteriores

Comparação do nosso projeto com o acervo de materiais de edições anteriores organizado em
`03_Exemplos_Anos_Anteriores/`. Escrita em 2026-07-27, **antes** da abertura do holdout e
antes de qualquer trabalho de relatório.

## §0. Escopo e regra de uso

Este documento é **referência interna de trabalho**. Nada aqui vai para o relatório final:
o entregável é anônimo, não cita terceiros e não compara times. O objetivo é único —
descobrir o que outras equipes fizeram melhor do que nós em conteúdo técnico, para
decidirmos o que ainda dá tempo de incorporar.

Regras que valem para qualquer conclusão tirada daqui, herdadas de
`03_Exemplos_Anos_Anteriores/README.md`:

1. Nenhuma mudança de desenho pode ser motivada por retorno — nosso ou de terceiros.
2. Toda adoção precisa ser declarada como decisão `D-NNN` **antes** de ser implementada.
3. Diferenças desfavoráveis a nós são registradas com o mesmo peso das favoráveis.
4. Um relatório premiado não é evidência de que o método está correto. Auditamos o
   conteúdo, não a colocação.

A crítica abaixo é dirigida a **artefatos públicos**, nunca a pessoas. Usamos apenas os
nomes dos robôs/estratégias, que são públicos e foram divulgados pela organização.

## §1. O que o acervo é, e o que ele não é

Base material: 8 relatórios/apresentações em acesso direto, 11 repositórios presos a commit
e 23 fontes públicas capturadas. Procedência e grau de confiança em
`03_Exemplos_Anos_Anteriores/00_catalogo/`.

Limitação central, que condiciona tudo o que segue: **nenhum relatório do acervo é de um
projeto campeão.** O material de melhor colocação confirmada é o KernelNet, 2º lugar de
2025. Os campeões de 2023, 2024 e 2025 são conhecidos por nome e tema, pelas fontes
oficiais, mas seus relatórios não são públicos. Estamos comparando contra o 2º lugar e
contra uma cauda de trabalhos não classificados — não contra o padrão vencedor.

## §2. Escala e perfil de quem vence

Levantado das publicações oficiais da organização e do criador do desafio:

| Edição | Escala declarada | Campeã | Vínculo |
|---|---|---|---|
| 2023 | 400+ grupos, 1.200+ alunos, 137 universidades | Fractinho | equipe com mentor docente |
| 2024 | 1.200+ alunos, 126 universidades | Persistence — TDA aplicada a ações da B3 | Poli Quant (USP) |
| 2025 | ~2.500 inscritos, 190 universidades, todos os estados | Prometheus — regimes de mercado e alocação em ações brasileiras | Poli Quant (USP) |

Três leituras que importam para o nosso desenho:

**(a) As colocações de topo saem de ligas quantitativas universitárias.** O top-5 de 2024 é
integralmente formado por equipes de ligas (Poli Quant, Insper Quantitative Finance, Grupo
de Negócios da Poli-USP, FEA.dev, FGV Quant). O Poli Quant é bicampeão (2024 e 2025). Há
continuidade explícita entre edições: membros mais experientes treinam os novos. Não é uma
competição entre times isolados; é uma competição contra estruturas com memória.

**(b) As duas campeãs recentes operaram ações brasileiras com enquadramento de regime e
alocação.** Não cripto, não classes exóticas, não alta frequência. Nossa classe de ativo e
nosso mercado estão alinhados ao que vence.

**(c) Reproduzir o método do campeão anterior não funciona.** O projeto Atlas (2025) aplicou
análise topológica de dados — exatamente a técnica da campeã de 2024 — com a melhor
engenharia de software de todo o acervo, e declara em seu próprio README ter ficado em 40º
lugar entre 953. A técnica não é o diferencial transferível.

## §3. Régua de referência: auditoria do 2º lugar de 2025

Auditamos o relatório do KernelNet com o mesmo padrão que aplicamos ao nosso trabalho.

**O que ele faz bem, e nós ainda não temos:** tese enunciada em uma frase ("a propagação de
informação entre ativos não é instantânea nem linear"); página de *factsheet* no padrão da
indústria; identidade visual completa e coerente; sete fluxogramas que substituem texto;
correção BH-FDR aplicada aos testes de causalidade entre pares; replicação da lógica num
segundo universo independente (30 maiores do S&P 500) como argumento barato de robustez; e
uma seção de uso de IA generativa com tabela ferramenta×tarefa, um caso concreto de
encadeamento de modelos e **uma falha assumida** (uma implementação incorreta de índice de
Sharpe sugerida por assistente, pega na verificação humana).

**O que não sobrevive à auditoria metodológica:**

- Janela de teste de 04/07/2022 a 29/12/2023 — **18 meses**. É precisamente o risco de
  escolha oportunista de período que o critério de backtest do edital diz observar.
- Retorno anualizado de 54,85% com Sharpe de 1,286 implica volatilidade da ordem de 40%
  ao ano, num livro descrito como mercado-neutro. O drawdown máximo reportado (−26,94%)
  é pior que o do índice de referência no mesmo período (−18,35%).
- Custo de 0,05% por operação e **nenhum custo de aluguel** para a perna vendida, numa
  estratégia long/short com rotação diária.
- O alvo do modelo de aprendizado de máquina é, textualmente, a combinação de parâmetros de
  saída "que resulta no maior retorno histórico". O rótulo é definido pelo resultado que se
  quer prever. A validação usa 5-fold cross-validation sobre série temporal, sem purga nem
  embargo entre treino e teste.
- Nenhum teste estatístico sobre o P&L: nenhum p-valor, nenhuma permutação, nenhum
  intervalo de confiança. A taxa de acerto de 71,97% é apresentada como virtude.
- Seção de limitações restrita a custo computacional e ausência de teste em crise aguda.

Conclusão operacional, sem arrogância: o padrão de rigor estatístico exigido para chegar ao
2º lugar é **inferior ao que já praticamos**. Isso não significa que o rigor não conte — o
documento de critérios afirma o contrário, ver §4 — mas significa que ele não é, sozinho, o
que separa o 2º do 1º lugar.

## §4. O que os documentos oficiais de 2026 dizem sobre onde o rigor pesa

Verificado em `01_Edital_e_Regras/`:

- Relatório final: PDF, **máximo 5 páginas**, 16:9, referência de ~750 palavras, anonimato
  integral, capa conta no limite. Seis páginas eliminam a equipe.
- Na avaliação do relatório, "os avaliadores não terão acesso a explicações adicionais,
  códigos-fonte ou materiais externos".
- Etapas: quartas de final com 20–30 equipes (apresentação online gravada); semifinal com
  8–10 equipes com **apresentação ao vivo e Q&A com banca técnica**; final presencial com 3
  equipes, avaliada por gestores.
- Código: "o envio do código-fonte não será exigido nas etapas iniciais, salvo se houver
  indicação expressa"; e **"equipes finalistas poderão ser solicitadas a compartilhar
  materiais adicionais para fins de validação metodológica, esclarecimento técnico ou
  comprovação do desenvolvimento apresentado"**.
- Critérios: "o desempenho das equipes não será avaliado exclusivamente com base em
  resultados históricos. A banca considerará, de forma prioritária, a qualidade do processo
  de desenvolvimento da estratégia."
- Desempate: a banca pode considerar consistência metodológica e **capacidade de defesa
  técnica**.

Isto define a divisão de trabalho do projeto: o relatório de 5 páginas é o filtro que
seleciona finalistas, e nele o rigor precisa aparecer comprimido e visual; a defesa técnica
e a validação metodológica são onde a profundidade do processo é efetivamente cobrada. As
duas coisas precisam existir, em ordem.

## §5. Padrões recorrentes do acervo, e onde nosso projeto está acima

Os defeitos abaixo aparecem repetidamente e são todos evitados por contrato no nosso
projeto. Listamos com o exemplo mais nítido de cada um.

| Padrão observado | Onde aparece | Nosso contrato |
|---|---|---|
| Inversão do sinal depois de observar P&L negativo, apresentada como descoberta | Kairos (2025) — o texto declara a inversão explicitamente | D-043 falsificou a tese original e recusamos inverter; a convenção rejeitada segue travada em teste |
| Escolha de hiperparâmetro pelo maior retorno, apresentada como evidência anti-overfitting | Kairos (limiar, janela, dimensão); CRYPO (janelas de MACD por ativo) | Parâmetro só se justifica por lógica econômica/agronômica; grid de robustez pré-registrado em D-065 antes de rodar |
| Seleção de ativos e pesos calculados no mesmo período usado para avaliar | CRYPO — pesos proporcionais ao crescimento no período de otimização | Universo é função de `t`; pesos de produção da última safra já divulgada |
| Preço ajustado retroativo como insumo | todo o acervo (yfinance/Bloomberg) | Motor de retorno total *forward-only*; nível ajustado embute dividendo futuro |
| Ausência de custo de aluguel na perna vendida | KernelNet, Satobot, MARK | Proxy conservadora declarada e calibrada (D-058) |
| Ausência de qualquer teste de significância sobre o resultado | KernelNet, CRYPO, Satobot, LSTMinator | Permutação exata de 32 sign-flips, BH-FDR sobre a família |
| Métricas internamente inconsistentes | CRYPO — volatilidade anualizada de 5,41% numa carteira de altcoins; Sharpe usando um índice de mercado como taxa livre de risco; beta −0,002 descrito como "market neutral" | Suíte de testes e reconciliação de atribuição no motor |
| Entrega com marcadores de rascunho | LSTMinator — `[ADICIONAR REFERÊNCIA]` e `[FIGURA TAL]` no PDF final | — |
| Recomendação de alocação real apesar de evidência não significativa | MARK — conclui que a estratégia "está pronta para compor o portfólio dos nossos investidores" com alfa de 0,64% e p-valor 0,83 | Níveis de afirmação fixados por claim em D-068 |

Onde estamos acima de **todos** os 11 repositórios, em substância e não em estilo:

1. **Point-in-time real.** `ref_date` versus `avail_date` em toda tabela, com vintage
   rastreado por manifesto. Nenhum outro projeto do acervo distingue a data a que o dado se
   refere da data em que ele ficou público.
2. **Holdout lacrado desde o desenho**, com executor indivisível em que a tentativa é
   consumida antes do I/O (D-072). O mais próximo é o walk-forward do Atlas — que é boa
   prática, mas não é um lacre.
3. **Pré-registro datado anterior à materialização** (log D-001 a D-072).
4. **Falsificação assumida sem correção post-hoc** (D-043).
5. **Custos de investibilidade**: ADTV, cap de participação, aluguel, AUM, capacidade.
6. **564 testes automatizados, CI e guards** de lookahead e de segredos. Nenhum dos 11
   repositórios tem integração contínua; apenas um tem suíte de testes (14 arquivos).
7. **Dados primários originais**: CHIRPS regionalizado por polígono municipal, PAM/IBGE,
   calendário de boletins CONAB curado, ComexStat, ONI, NEFIN. O restante do acervo é
   essencialmente yfinance.
8. **Placebos espacial e temporal** (D-065/D-066, D-070/D-071). Nenhum projeto do acervo
   executa um placebo.

## §6. Lacunas técnicas reais — o que outros fizeram melhor e ainda dá para fazer

Esta é a seção que motivou o documento. São itens de conteúdo, não de apresentação.

### 6.1 Validação do mecanismo contra uma fonte de safra independente

**Quem fez melhor:** KernelNet replicou a lógica num segundo universo (S&P 500) e usou isso
como argumento de robustez. É barato e é eficaz.

**Nossa lacuna:** D-066 encontrou que o placebo espacial não morre — embaralhar UFs destrói
~69% do coeficiente, mas resta ~31% significativo. Caracterizamos isso como componente
nacional-comum. O que **não** sabemos é se esse componente comum vem da safra física ou do
processo de revisão da própria CONAB. Nossa cadeia inteira depende de um único órgão como
desfecho.

**O que dá para fazer:** testar se o mesmo choque climático prevê a revisão de produção
brasileira publicada por um **segundo estimador oficial independente**, com calendário de
divulgação datado. Se o efeito aparece nas duas fontes, ele está na safra; se aparece só na
CONAB, está no processo do órgão — e isso mudaria materialmente o que podemos afirmar.
É return-agnóstico, não toca o holdout e ataca diretamente nosso resultado mais fraco.

**Estado da fonte, sem promessa:** o arquivo histórico do USDA que era servido pela Mann
Library (`usda.library.cornell.edu`) responde HTTP 200 mas redireciona para
`esmis.nal.usda.gov`, em plataforma nova. Não confirmamos a existência do arquivo vintage,
o formato, nem a cobertura da estimativa de produção brasileira. **Pista, não fonte
validada** — precisa de sondagem própria antes de virar plano.

### 6.2 Métricas por janela, incluindo as ruins

**Quem fez melhor:** Atlas reporta KPIs por cada uma das 9 janelas out-of-sample do
walk-forward, inclusive uma janela com Sharpe negativo (−0,360). Isso comunica estabilidade
com honestidade e é muito mais informativo que um número agregado.

**Nossa lacuna:** o holdout produz uma avaliação única sobre cinco anos-safra. Um número só,
sem distribuição.

**O que dá para fazer:** pré-registrar, **antes** de abrir, o reporte descritivo de métricas
por ano-safra dentro do holdout, com o compromisso explícito de publicar os anos ruins. Não
consome grau de liberdade estatístico porque é descritivo, mas precisa estar pré-registrado
para não virar seleção posterior.

### 6.3 Caracterização de risco da carteira

**Quem fez melhor:** MARK reporta CVaR, beta e information ratio por geografia, além de
retorno. Atlas reporta Sortino, Calmar, tempo submerso e turnover.

**Nossa lacuna:** nossa carteira nunca foi caracterizada por risco. Temos P&L, atribuição e
turnover. Não temos VaR, CVaR, tempo submerso, nem beta contra mercado — apesar de
`dollar-neutral` não implicar neutralidade de beta, coisa que nós mesmos registramos em
D-034. Pela lente de gestão de risco, é uma lacuna genuína.

**O que dá para fazer:** definir e pré-registrar o conjunto de estatísticas descritivas de
risco a computar sobre o resultado do holdout. Descritivo, não altera a estratégia.

### 6.4 Benchmark de performance declarado

**Quem fez melhor:** MARK construiu deliberadamente um "Tailor Made Index" — carteira
equal-weighted do mesmo universo — para ser o comparador justo, além do índice global.

**Nossa situação:** temos algo superior como contrafactual (a carteira setorial ingênua de
D-060 e a decomposição ortogonal de D-064). Mas **não declaramos um benchmark de
performance** para o livro. Para uma carteira dollar-neutral o comparador natural é o CDI,
e isso precisa estar escrito antes de vermos o número.

### 6.5 Correção pelo número de especificações testadas

**Quem fez:** ninguém, em todo o acervo.

**Por que é nossa oportunidade e não nossa lacuna:** a correção do Sharpe pelo número de
tentativas exige saber quantas especificações foram efetivamente testadas — número que
quase nenhum projeto consegue declarar honestamente. Nosso log de decisões dá essa contagem
de forma auditável. É implementável, é único, e transforma nosso registro de processo em
número.

### 6.6 Ausência de camada de risco na estratégia

**Quem fez:** Atlas tem kill-switch por drawdown e controle de turnover.

**Nossa situação:** não temos stop, alvo de volatilidade nem kill-switch. Isso é uma
**escolha** — adicionar overlay agora significa mexer no contrato congelado, e não
recomendamos. Mas a ausência precisa ser declarada no relatório como decisão consciente e
justificada, não passar como esquecimento. Um gestor na banca vai perguntar.

## §7. Lacunas estruturais — o que não dá para corrigir nesta edição

Registradas para serem ditas com todas as letras no relatório, não para serem escondidas.

1. **Tamanho de amostra.** O CHIRPS preliminar só existe a partir de 2015 e o primeiro
   ano-safra completo é 2015/16; o holdout tem cinco anos-safra. Atlas trabalhou com oito
   anos de dados diários e nove janelas out-of-sample. É limite físico da fonte, não
   escolha. Continua sendo a limitação nº 1 do projeto.
2. **Largura do cross-section.** Cinco nomes. Os comparáveis operam 30 ações (KernelNet),
   universo do Ibovespa (Atlas) ou centenas de ativos (MARK). D-062 e D-063 já enumeraram e
   fecharam o espaço de veículos alternativos: não existe veículo brasileiro líquido com
   sensibilidade limpa a um nowcast de produção marginal.
3. **Dados pagos de mercado.** MARK usou Bloomberg, inclusive para composição histórica de
   índices. Não temos acesso equivalente. O impacto real é baixo — nossa vantagem de dados
   está em fontes públicas primárias que ninguém mais processou.
4. **Track record fora de amostra em tempo real.** Não há tempo hábil para acompanhamento
   prospectivo. Nenhum time do acervo tem, mas seria o argumento mais forte possível.
5. **Microestrutura e intradiário.** Sem book histórico gratuito da B3, operamos no
   fechamento. Impede refinar execução além do que já está modelado.
6. **Memória institucional.** Não é técnico, mas é o fator com maior correlação observada
   com colocação de topo. Nosso contrapeso possível é profundidade de processo, que é
   exatamente o que o log de decisões acumula.

## §8. Pendências abertas por esta comparação

| # | Item | Natureza | Bloqueia o holdout? |
|---|---|---|---|
| 1 | Sondar a disponibilidade e o vintage do segundo estimador oficial de safra (§6.1) | investigação de fonte | não |
| 2 | Pré-registrar métricas por ano-safra do holdout (§6.2) | pré-registro | **sim** — precisa ser anterior |
| 3 | Pré-registrar estatísticas descritivas de risco (§6.3) | pré-registro | **sim** — precisa ser anterior |
| 4 | Declarar benchmark de performance do livro (§6.4) | pré-registro | **sim** — precisa ser anterior |
| 5 | Especificar a correção pelo número de tentativas (§6.5) | pré-registro | **sim** — precisa ser anterior |
| 6 | Declarar a ausência de camada de risco como escolha (§6.6) | redação | não |
| 7 | Nome, identidade visual e factsheet | entregável | não |

Os itens 2 a 5 são pré-registros: se forem escritos depois de vermos o resultado do holdout,
perdem inteiramente o valor que os justifica. Eles precisam entrar antes da rodada única.
