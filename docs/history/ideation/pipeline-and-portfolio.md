# Arquitetura de projeto, lições dos anos anteriores e ideia de portfólio

Documento de trabalho. Objetivo: sair do óbvio "pegar dado → codar a tese → backtest" e
desenhar um projeto com várias camadas — na linha do que os dois exemplos de anos
anteriores (`03_Exemplos_Anos_Anteriores/`) fizeram bem.

---

## 1. O que os dois exemplos anteriores fazem bem (e vale copiar)

**[Persona: Estatístico/a cético/a — lendo os dois relatórios de fora]**

### KernelNet (2º lugar 2025 — causalidade de Granger não-linear em rede de ações)
- **Teste de pré-condição antes de qualquer afirmação causal**: rodam teste de
  estacionariedade (ADFuller) em cada série antes de sequer tentar o teste de causalidade.
  Não assumem — verificam.
- **Correção de múltiplas comparações (Benjamini-Hochberg/FDR)**: ao testar causalidade
  entre *todos os pares* de 30 ativos (=435 pares), a chance de achar relação "significativa"
  por puro acaso é alta. Eles corrigem os p-valores para isso antes de aceitar uma aresta no
  grafo. **Esse é o tipo de rigor que separa um projeto que parece sério de um que só parece
  bonito.**
- **Arquitetura de rolling window explícita e documentada com diagrama**: grafo e modelo de
  ML são reconstruídos a cada 30 dias, sempre só com dado disponível até o dia anterior —
  e eles desenham o diagrama disso especificamente para provar ausência de look-ahead, não
  só afirmam que evitaram.
- **Camada de ML separada e com escopo limitado**: o Random Forest não decide *o quê*
  comprar — só otimiza *como* executar (stop gain/loss/tempo de permanência) dado o
  contexto (VIX, SELIC, volatilidade do par). A tese em si (causalidade não-linear) fica
  isolada da camada de ML. Isso facilita explicar o "porquê" sem misturar com a parte de
  "ajuste fino".
- **Alocação proporcional à confiança do sinal**, não binária (tamanho da posição varia
  conforme quantos *drivers* concordam).
- **Validação em mercado diferente (S&P 500) como teste de generalização**: rodaram a
  mesma metodologia inteira num universo diferente (30 ações mais líquidas dos EUA) para
  checar se o alfa é um artefato do mercado brasileiro ou algo mais estrutural. Achado
  positivo lá reforça a tese sem inflar o resultado do backtest principal.
- **Seção de limitações separada e honesta**: custo computacional, ausência de teste em
  "cisne negro", sugestão explícita de próximo passo técnico (Graph Neural Networks).

### Kairos (detecção de anomalia com LSTM Autoencoder num índice temático de IA)
- **Taxonomia de features em 5 categorias**, não uma lista solta: preço/retorno,
  volatilidade/risco, liquidez/fluxo, contexto macro (pra separar choque específico do
  setor de choque de mercado amplo), fundamentos (trajetória de EPS). Pensar em *categorias*
  de feature em vez de uma lista ad-hoc é o que dá estrutura pro "Modelagem" do edital.
- **Documentam uma hipótese que testaram e que estava ERRADA**, e o pivô: a hipótese
  inicial era "anomalia = pânico, então vender". Testaram, deu resultado negativo, e em vez
  de esconder isso, investigaram *por que* deu errado, descobriram que anomalia na verdade
  antecedia continuação de tendência (não reversão), e reformularam a tese com a nova
  evidência. **Isso é ouro para os critérios "Análise dos Resultados" e "Conclusão" do
  edital — a banca explicitamente valoriza honestidade analítica, não só resultado bonito.**
- **Três tabelas de sensibilidade sistemática**: variam threshold, tamanho de janela e
  complexidade do modelo *um de cada vez*, mostram que o resultado não desmorona em nenhuma
  vizinhança da escolha final — prova de que não é um ponto "garimpado" a dedo.
- **Estratégia posicionada como overlay tático/satélite**, não substituto do
  benchmark — mais fácil de defender numericamente e narrativamente do que "bater o
  Ibovespa sempre".
- **Seção de IA generativa concreta e limitada**: three usos específicos (debug, apoio a
  planejamento de experimentos, redação), com um exemplo real de a IA *errar* (bug no
  cálculo do Sharpe) e a equipe pegar o erro — isso demonstra validação humana em vez de
  confiança cega, que é exatamente o que o Manual de Avaliação da CVM pede em "uso adequado"
  (seção 2.5) mesmo sem ser esse o foco de vocês agora.

**Padrão comum aos dois**: nenhum dos dois é "pegar dado → codar tese → backtest". Ambos
têm validação estatística antes da tese (estacionariedade / normalização e taxonomia de
features), uma camada de geração de sinal, uma camada de decisão de posição separada, testes
de sensibilidade/robustez como seção própria, e um teste de generalização fora da amostra
principal (mercado diferente / distribuição de regime diferente).

---

## 2. Arquitetura de pipeline proposta (genérica, reaplicável às nossas teses)

**[Persona: Engenheiro/a de dados + Especialista em backtesting]**

```
Camada 0 — Ingestão
  → puxar cada fonte bruta (NASA POWER, ComexStat, ONS, CVM, preços) com cache local,
    sempre guardando a versão "como publicada na época" (nunca a revisada retroativamente)

Camada 1 — Validação e limpeza
  → checar buracos, duplicatas, mudança de metodologia da fonte no meio da série
  → testes de estacionariedade / normalização onde fizer sentido (ex: retornos)
  → documentar decisões de imputação (o que fazer com dado faltante) explicitamente

Camada 2 — Engenharia de features (por categoria, não lista solta)
  → sinal "bruto" da tese (ex: anomalia de chuva, crescimento de exportação)
  → contexto macro (pra separar efeito específico da tese de movimento de mercado amplo —
    ex: Ibovespa, câmbio, Selic no dia)
  → contexto do próprio ativo (volatilidade recente, liquidez, momentum)

Camada 3 — Teste de significância antes de aceitar o sinal
  → se testar múltiplos ativos/regiões/parâmetros ao mesmo tempo, corrigir por múltiplas
    comparações (Benjamini-Hochberg, como o KernelNet fez) antes de aceitar qualquer sinal
    como "real"

Camada 4 — Geração de sinal → decisão de posição
  → sinal bruto vira decisão observável (comprar/vender/ranking/peso), com threshold e
    lógica explícitos
  → tamanho de posição proporcional à confiança do sinal, não binário

Camada 5 — Camada de execução/ajuste (opcional, separada da tese)
  → aqui é onde ML pode entrar sem contaminar a tese central: otimizar parâmetros de saída
    (stop, tempo de permanência), não decidir a direção

Camada 6 — Backtest com arquitetura anti-look-ahead explícita
  → rolling window documentada com diagrama (igual KernelNet Figura 4)
  → custos de transação explícitos
  → benchmark definido a priori, não escolhido depois de ver o resultado

Camada 7 — Testes de robustez (seção própria, não um parágrafo)
  → sensibilidade a hiperparâmetros (grid simples, 2-3 valores por parâmetro, tabela)
  → teste de generalização: outro sub-período, outro subconjunto de ativos, ou (se a tese
    permitir) outro país/mercado com dado análogo
  → hipóteses testadas e descartadas, documentadas com honestidade (padrão Kairos)

Camada 8 — Interpretação e conclusão
  → o que funcionou, o que não funcionou, por quê (não só métricas)
  → limitações reais assumidas explicitamente
  → próximos passos concretos, não genéricos
```

Isso não precisa ser implementado tudo de uma vez nem em todas as teses com a mesma
profundidade — mas ter esse esqueleto em mente desde já evita que o projeto vire só
"baixei o dado, rodei uma correlação, plotei um gráfico".

---

## 3. Ideia de portfólio multi-tese (em vez de uma tese isolada)

**[Persona: Especialista em asset pricing / Portfolio manager]**

Em vez de escolher *uma* tese e apostar tudo nela, dá pra montar um portfólio com
**múltiplos sleeves (fatias) descorrelacionados**, cada um vindo de uma tese diferente —
isso é literalmente como fundos quantitativos reais são montados, e dá muito mais
"robustez" no sentido que você pediu (mais camadas, mais passos), além de proteger contra
uma tese individual simplesmente não funcionar no período testado (o edital deixa claro que
resultado ruim isolado não elimina o trabalho, mas um portfólio de várias teses é uma defesa
estrutural mais forte que "confiar numa ideia só").

**Desenho de portfólio sugerido, usando as teses já mapeadas**:

| Sleeve | Teses que entram | Papel no portfólio | Frequência |
|---|---|---|---|
| **Hard data / commodities** | Clima (1) + ComexStat (2) combinadas | Núcleo direcional — long/overweight em agro-exportadoras quando o sinal combinado (antecipação de safra + confirmação de embarque) é positivo | Baixa (safra/mensal) |
| **Macro regional** | ONS (3) | Overlay de timing — ajusta exposição a uma cesta industrial/Ibovespa amplo conforme anomalia de atividade regional | Semanal |
| **Market-neutral / pares** | TNIC/CVM (5) | Sleeve descorrelacionado do mercado — pair trade entre empresas que estão ficando textualmente mais parecidas, no espírito do que o KernelNet fez com causalidade (mas com concorrência textual em vez de causalidade de preço) | Anual (Formulário de Referência é anual) |
| **Event-driven** | Timing CVM (6) | Overlay de curto prazo em torno de datas de divulgação de resultado — entra e sai rápido, não fica exposto o tempo todo | Trimestral (janela de earnings) |

**Por que isso é mais robusto do que uma tese sozinha**:
- Os sleeves têm frequências e fontes de risco diferentes — se uma tese não funcionar no
  período testado, não derruba o portfólio inteiro (mesma lógica de diversificação que
  qualquer risk manager aplicaria).
- Dá material concreto pro critério "Modelagem" (20%) mostrar uma arquitetura de decisão
  em camadas (sinal por sleeve → agregação → portfólio final), não um sinal único.
- Dá material pro critério "Backtest" (15%) rodar testes de robustez *por sleeve* e depois
  no portfólio agregado — mostra que vocês entendem a diferença entre "a tese individual
  funciona" e "o portfólio é robusto".
- Combina naturalmente com o pivô de honestidade do padrão Kairos: dá pra mostrar
  explicitamente "essa tese isolada teve Sharpe baixo, mas no portfólio agregado a
  correlação baixa com as outras ainda agrega valor" — um argumento mais sofisticado do que
  só "nosso Sharpe foi X".

**Risco de fazer isso**: mais complexidade operacional — juntar 4 fontes de dado, 4
frequências diferentes, precisa de uma camada de agregação de portfólio (pesos entre
sleeves) que é trabalho adicional real. Como você pediu para não nos preocuparmos com prazo
agora, isso deixa de ser um bloqueio — mas é importante que o time saiba que está
escolhendo o caminho mais ambicioso, não o mais rápido.

**Alternativa mais simples, mesmo espírito**: se o portfólio de 4 sleeves parecer grande
demais, dá pra ter o mesmo efeito de "camadas" com só a dupla Clima+ComexStat, mas
estruturada como duas camadas dentro da *mesma* tese (sinal antecedente da camada climática
→ filtro de confirmação da camada ComexStat → só gera posição quando as duas concordam) em
vez de portfólio de sleeves — mais simples de implementar, ainda assim muito mais robusto
que um sinal único.
