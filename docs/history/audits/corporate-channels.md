# Auditoria dos canais empresariais — portão da Fase 3.1

> **Status:** auditoria histórica concluída em D-035 e estendida para cana em D-052. As frases
> de “próximo passo” abaixo registram o estado de cada data; as resoluções posteriores estão no
> log D-036–D-053 e não reescrevem este portão.
>
> Protocolo inserido em D-034 **antes de consultar qualquer retorno de ação**. A matriz
> fundamentalista D-032/D-033 permanece como registro PIT válido de exposição ao grão, mas não
> será convertida em score ou carteira até atravessar este portão.

---

## 1. Por que este portão existe

H1 confirmou que o clima antecipa a revisão da safra. Isso não prova, sozinho, que uma seca
beneficia uma produtora agrícola listada. Para a produtora, dois canais têm sinais opostos:

- o choque agregado reduz a oferta e pode elevar o preço da commodity;
- o choque nas fazendas da própria empresa reduz o volume que ela tem para vender.

A matriz atual identifica venda ou compra direta do grão, materialidade e composição entre
soja/milho. Ela ainda não separa preço de quantidade, não representa a localização das
operações e não atenua a exposição por hedge. Além disso, seus quatro nomes tornam o H3
Fama–MacBeth e o cap original incompatíveis com o N real.

O objetivo desta fase não é acrescentar complexidade. É impedir que uma direção econômica
ambígua seja transformada em posição por uma fórmula simples demais.

## 2. Escopo e proibições

### Entra nesta fase

1. fontes corporativas PIT de geografia, mix, hedge e mudanças de perímetro;
2. decomposição econômica dos canais de preço, volume próprio e custo de insumo;
3. H2a no período de desenvolvimento, depois de especificação exata pré-registrada;
4. redefinição de H3 para um universo de três/quatro ações;
5. decisão R19 sobre início, concentração, cap e eventual hedge externo.

### Não entra nesta fase

- retorno de ação, Sharpe, drawdown ou resultado da estratégia;
- período 2020–2025 de preços financeiros para escolher desenho;
- inclusão de empresa porque melhora diversificação;
- granularidade sem fonte PIT reproduzível;
- ajuste de regra porque um parâmetro gerou retorno melhor.

H2a usa retorno de **commodity** somente no desenvolvimento até 2019, pois testa um elo
econômico anterior ao equity. Seu recorte 2020–2025 ficou lacrado até a rodada única de D-075 e
não foi reaberto depois dela: H2a não é reexecutado no holdout.

## 3. Decomposição candidata — ainda não é o score final

Para cada empresa `i`, cultura `c`, região `u` e data `t`, a auditoria buscará três exposições
não negativas:

- `P(i,c,t)`: benefício de preço para quem vende o grão;
- `Q(i,c,u,t)`: dano de quantidade nas áreas produtivas próprias;
- `C(i,c,t)`: custo de insumo para quem compra o grão/derivado imediato.

Uma representação candidata é:

```text
S(i,t) = soma_c [
    (P(i,c,t) - C(i,c,t)) * Shock_nacional(c,t)
    - soma_u Q(i,c,u,t) * Shock_regional(c,u,t)
]
```

O primeiro termo representa o preço agregado; o segundo, a quebra de produção da própria
empresa. Hedge de venda ou de insumo pode atenuar `P`/`C` apenas quando houver evidência PIT
reproduzível. Na ausência dela, o projeto não inventa um percentual: registra a lacuna e testa
uma faixa conservadora como sensibilidade.

Essa fórmula é uma **hipótese de trabalho** do portão. Sua forma final será congelada em nova
decisão antes do primeiro retorno de ação.

## 4. Auditoria corporativa point-in-time

Para cada vintage de AGRO3, SLCE3, BRFS3 e JBSS3, procurar na ordem CVM/SEC → RI:

| Bloco | Evidência buscada | Uso |
|---|---|---|
| Mix | receita, volume ou área por soja/milho | atualizar composição por cultura |
| Geografia produtiva | hectares/produção por fazenda, município ou UF | construir `Q(i,c,u,t)` para produtores |
| Preço | parcela de vendas exposta ao preço da commodity | construir `P(i,c,t)` |
| Insumo | participação de milho/soja no custo | construir `C(i,c,t)` |
| Hedge | percentual vendido/comprado ou protegido, horizonte e preço | atenuar canal somente quando comparável |
| Perímetro | aquisições, vendas de ativos, fusões e mudança de segmento | abrir novo vintage, nunca reescrever o anterior |

Cada observação precisa de `ref_date`, `avail_date`, fonte, localizador, métrica e unidade. Um
relatório atual não pode preencher silenciosamente anos antigos. Fonte sem data comprovável
recebe limite posterior conservador; ausência permanece ausência.

### Estado inicial das lacunas

| Ticker | O que D-033 prova | O que falta para o canal líquido |
|---|---|---|
| AGRO3 | venda direta, materialidade e mix soja/milho | geografia por cultura, hedge e novos vintages |
| SLCE3 | venda direta e receita por cultura | geografia por cultura, hedge e vintages anteriores/posteriores |
| BRFS3 | milho/soja como custo direto, com atualização em 2018 | abertura da cesta, hedge de insumo e mudanças de perímetro |
| JBSS3 | segmento direto de aves/suínos com materialidade limitada | exposição consolidada, hedge, abertura da cesta e data de disponibilidade mais forte |

## 5. H2 passa a ter dois testes com papéis diferentes

### H2a — transmissão preditiva ao preço da commodity — portão

Pergunta: usando apenas o `Shock` que já estava disponível em `t`, o estresse brasileiro
antecipa retorno da commodity com o sinal esperado no horizonte pré-especificado?

Especificação congelada em **D-036** (pré-registrada antes do resultado):

- **mecanismo, não estratégia** ⇒ roda no **span cheio 2018/19–2024/25** com sub-amostras
  dev/holdout em separado (princípio de D-029; reconcilia a restrição dev-only escrita antes);
- fonte do desfecho = preço mundial FRED/IMF (soja `PSOYBUSDM`, milho `PMAIZMTUSDM`), de que o
  produtor é *price-taker* (D-035); regressor = `Shock` nacional as-of fim de mês na janela;
- retorno forward `log(P[m+h]/P[m])`, primário `h=3`, `h∈{1,2,3}` robustez; sinal esperado `β>0`;
- inferência agrupada por ano-safra × cultura + bootstrap; N efetivo declarado;
- não escolhe futuro, horizonte ou janela pelo melhor resultado.

**Regra do portão (direcional + ressalva)**: `β>0` e p unilateral < 0,10 ⇒ passa; `β>0` fraco
⇒ inconclusivo (long segue com ressalva, confirmar no holdout); `β<0` significativo ⇒ reprova.
Se H2a reprovar, não se presume `P>0` para produtores; a ponta long é reformulada antes de
qualquer backtest de ações.

**Resultado (D-037, 2026-07-19): INCONCLUSIVO-negativo.** No spec primário (h=3, span cheio,
pooled) β=−0,017 (p lado negativo=0,113): sinal **oposto** ao esperado, não significativo — o
portão não reprova, mas **não confirma** o canal de preço; no h=1 o pooled é significativamente
negativo. Duas leituras não resolvidas: transmissão fraca ao preço **mundial USD**, ou reação
**contemporânea** + reversão que um teste forward não capta. O canal `P` do lado long fica sem
suporte empírico; a decisão de reformular o long / pré-registrar diagnóstico contemporâneo ou em
BRL (CEPEA) / reduzir ao processador é o próximo passo. Detalhe em `07` D-037.

**Diagnósticos (D-038 pré-registro / D-039 resultado, 2026-07-20).** Os quatro desfechos pooled
span cheio deram **nulo**: contemporâneo USD −0,001, contemporâneo BRL +0,005, forward USD
−0,017, forward BRL +0,004 — nenhum significativo. O contemporâneo ≈ zero **descarta** a leitura
"reage na janela e reverte". O canal de preço mundial (USD e proxy BRL) **não resgatado**. Resta
o teste do **preço local CEPEA** (base brasileira, o preço certo para o processador), como último
teste de preço; se nulo, mecanismo de preço morto. Detalhe em `07` D-039.

**Teste local (D-040 pré-registro / D-041 resultado, 2026-07-20).** CEPEA está atrás de Cloudflare
(D-025); usado o preço local recebido pelo agricultor via IPEADATA/DERAL-Seab-PR. Resultado:
`contemp_local` +0,007 (p 0,33), `forward local` +0,031 (p 0,21) — **sinal certo (positivo)**,
ao contrário do mundial, mas **sem significância**. Fecha a família (6 medidas, nenhuma
significativa): o elo produção→preço→ação não está estatisticamente estabelecido; a força testada
da tese é clima→revisão CONAB (H1). Próximo passo = reformular o sinal no elo provado / reduzir /
aceitar com ressalva. Detalhe em `07` D-041.

### H2b — reação à publicação CONAB — diagnóstico

Pergunta: a surpresa do levantamento move o preço ao redor da divulgação?

Resultado nulo não invalida automaticamente H2a: o mercado pode incorporar clima antes da
publicação oficial. H2b mede timing e surpresa residual; não é condição necessária para a
estratégia antecedente.

## 6. H3 precisa ser compatível com o cross-section observado

O Fama–MacBeth originalmente pré-registrado fica **suspenso** como teste primário: três ou
quatro ações por data não sustentam uma regressão cross-sectional com controles. Mantê-lo
apenas porque estava no plano produziria precisão aparente.

Antes de retornos, a fase deve escolher e pré-registrar um desenho que:

- trate o spread produtor–processador como unidade econômica observável;
- não transforme dias sobrepostos em eventos independentes;
- agrupe ou reamostre por ano-safra;
- comporte efeitos fixos/controles sem alegar N cross-sectional inexistente;
- inclua inferência por randomização/permutação quando ela for informativa;
- declare quando o resultado é descritivo ou inconclusivo.

Alternativas admissíveis para a decisão: estudo de spread por evento/horizonte; painel com
interação `Shock × exposição` e efeitos fixos; combinação dos dois, com um único primário.

**Escolha congelada (D-053).** O primário é o **spread produtor–processador** medido como painel
`Shock×exposição` demeanado na seção transversal, **só nos 4 nomes de grãos** (a cana, de
mecanismo fraco, fica de fora do teste para não diluir a força), cluster por ano-safra,
**inferência por permutação** (mais honesta que a assintótica com 5 clusters) e **unilateral**
α=0,10 (direção dada por H′). O Fama–MacBeth fica descartado. Contrato em
`src/quantagro/backtest/strategy_spec.py`.

## 7. Dollar-neutral não é market-neutral

Notional comprado igual ao vendido garante apenas soma de pesos igual a zero. Não neutraliza
automaticamente beta de mercado, tamanho, liquidez, câmbio ou commodity — especialmente com
produtores menores contra processadores maiores.

O primário será chamado **dollar-neutral long/short**. Neutralização de beta, hedge de índice
e controles fatoriais serão decisões/testes explícitos. H4 continua sendo o teste existencial
de alfa residual; ele não deve ser antecipado por linguagem que prometa neutralidade inexistente.

## 8. Critérios de saída

A Fase 3.1 só termina quando todos forem atendidos:

- auditoria PIT dos quatro nomes concluída, com lacunas declaradas;
- decisão sobre manter ou decompor a matriz D-033 registrada antes de equity;
- H2a especificado e executado apenas no desenvolvimento; H2b classificado como diagnóstico;
- H3 substituído por desenho compatível com o N real;
- R19 resolvido sem retorno de ação;
- nomenclatura corrigida para dollar-neutral e riscos fatoriais explícitos;
- score e protocolo de carteira congelados em nova decisão.

Se a evidência não permitir resolver o sinal líquido de produtores, o portão falha. O projeto
deve então usar uma ponta long economicamente identificável, reduzir a tese a processadores ou
reportar que o mecanismo físico não foi traduzido em estratégia investível.

## 9. Resultado da auditoria dos quatro nomes (D-035)

Auditoria conduzida nas fontes primárias datáveis, sem consultar nenhum retorno de ação. O
registro estruturado por nome, vintage, fonte, localizador e **lacuna declarada** está em
`data/reference/corporate_audit_v1.json`. Fontes efetivamente lidas: 20-F da BrasilAgro
(FY2014 e FY2019, SEC CIK 1499849), 20-F da BRF (FY2017, CIK 1122491) e 10-K da Pilgrim's
Pride (FY2018, CIK 802481, subsidiária de aves da JBS nos EUA); SLCE3 e a JBS consolidada
apoiam-se na âncora datada de D-033 e em geografia pública, com os números finos declarados
como lacuna a fechar na fonte primária CVM.

### 9.1 Achados por nome (todos sem retornos)

| Nome | Papel | Canal | Achado material da auditoria |
|---|---|---|---|
| **AGRO3** | produtor (+) | `P`, `Q` | Grão é **minoria e declinante**: cana passou de 29% (FY2014) a **48%** (FY2019) da receita operacional; ganho na venda de fazendas domina o lucro; algodão entrou. `Q` **parcialmente fora do Shock** (Cremaq/PI + Paraguai/Cresca). Hedge multi-cultura (% não divulgado). |
| **SLCE3** | produtor (+) | `P`, `Q` | Algodão dilui o canal grão (soja+milho = 47,5% da receita, já em D-033). Fazendas em MT/MS/GO/MG/BA **+ MA/PI/PA fora do Shock**. Pré-venda/hedge intensos atenuam `P` (% = lacuna declarada). |
| **BRFS3** | processador (−) | `C` | Milho+farelo/grão de soja = **28,5% do custo** (2017), **de origem brasileira** ⇒ `C` dentro do Shock. Repasse parcial ao preço de venda + hedge **atenuam** o `C` líquido; direção de curto prazo permanece −1. |
| **JBSS3** | processador (−) | `C` | Processador **mais diluído**: bovino (maior segmento) pouco intensivo em grão; insumo **geograficamente partido** — Pilgrim's/EUA (feed = 28,5% do custo US, milho americano, **fora** do Shock) + Seara/BR (dentro) + Moy Park/Europa (trigo, fora). Só a fatia Seara é co-localizada. |

### 9.2 Decisão (critério de saída §8, itens 1 e 2)

1. **As direções de D-033 são defensáveis** na evidência PIT: produtores vendem o grão
   (price-taker), processadores o compram como ração.
2. **`P` e `Q` não são PIT-separáveis** com as fontes disponíveis — área plantada por
   cultura×UF×vintage e percentuais de hedge são lacunas declaradas. Por §3 deste documento e
   por `docs/history/audits/exposures.md` §7, a ausência é **limite de identificação**, não preenchida.
   ⇒ **mantém-se a matriz D-033 (opção 1)**; não se constrói um termo `Q` separado nem um
   score `P/Q/C` explícito.
3. **A materialidade efetiva é atenuada** em todos os nomes (culturas não-primárias, hedge,
   geografia parcialmente fora do Shock). Isso **não reescreve** D-033 (registro congelado sob
   regra própria), mas entra como **haircut candidato** e como eixo de sensibilidade a ser
   decidido no congelamento do score, apenas no desenvolvimento.
4. **O lado long fica condicionado a H2a**: como `Q` está parcialmente fora do Shock, `P`
   tende a dominar, mas o sinal líquido do produtor **não é resolvível só pelo fundamento**.
   Se H2a (transmissão de preço) falhar, o long é reformulado. Isso **endereça R20 por
   evidência, não por presunção**.
5. **O universo não muda**: nenhum novo nome direto emergiu; os vetos de D-033 se mantêm. A
   concentração (R19) **não pode ser diluída adicionando nomes diretos** — permanece aberta
   para a decisão de carteira.

**Custo/limitação declarado.** Optar por não decompor `P/Q` é assumir um limite de
identificação: o sinal permanece o canal de preço/insumo de D-033, agora com a ressalva
explícita de que a ponta long depende de H2a e que a materialidade real é menor que a
participação de receita sugere. Fechar as lacunas de área-por-UF e de hedge exigiria vintage
CVM que as fontes lidas não entregaram de forma datável.

## 10. Auditoria dos veículos de cana (D-052)

Auditoria PIT dos dois nomes candidatos do submodelo da cana (D-050/D-051), sem consultar
retorno de ação, respondendo ao R24. Registro estruturado por nome, fonte e lacuna declarada em
`data/reference/cane_corporate_audit_v1.json`. **Tier de evidência inferior ao da §9**: as
fontes primárias CVM (formulário de referência) não foram baixadas — WebFetch deu 403 em
XP/NovaCana e a SEC não cobre nomes só da B3 —, então os percentuais finos vêm de síntese de
imprensa setorial/RI e ficam como lacuna declarada. A decisão não depende deles.

### 10.1 Achados por nome (sem retornos)

| Nome | Papel | Achado material |
|---|---|---|
| **SMTO3** | produtor de cana (+) | Usinas em SP (×3) + Boa Vista/GO — **dentro** do choque (SP/MG/GO/MS/PR). **~70% cana própria** (30% terceiros a CONSECANA → offset parcial do ATR). Mix ~47% açúcar; Boa Vista/GO **só etanol**. Hedge trava **~96% do preço** do açúcar ~1 safra à frente. **IPO 2007 → histórico dev + holdout completo.** |
| **JALL3** | produtor de cana (+) | Usinas em GO (×2) + MG (adquirida 2022) — **dentro** do choque. **100% cana própria** (exposição mais limpa, sem offset CONSECANA). Mix ~50–60% açúcar, **>⅓ orgânico premium**. Hedge de preço até ~2 anos. **IPO 08/02/2021 → zero histórico no dev, só holdout.** |

### 10.2 Decisão (opção 1, decidida pelo time)

1. **O canal da cana é de quantidade, não de preço.** ATR = açúcar recuperável por tonelada:
   mais ATR rende mais açúcar **e** etanol da mesma cana, então o sinal **sobrevive ao hedge de
   preço** — ao contrário do canal de preço de grãos que falhou (D-037/D-041). É o que justifica
   manter cana como submodelo. Mas ATR ≠ receita total, e o canal de tonelagem veio fraco em
   D-051: o sinal físico líquido **não é provado** (R24).
2. **SMTO3 entra no universo scoreado, com haircut declarado** (30% terceiros, hedge, GO só
   etanol). Único veículo testável no dev e negociável no holdout. Direção +1 sob o submodelo.
3. **JALL3 fica fora do score.** A exposição é a mais limpa, mas o IPO de fev/2021 a deixa
   **holdout-only, sem dev**. Pôr no teste de tiro único um nome nunca validável é o risco de
   descoberta falsa que o projeto blinda. O mecanismo já está validado por D-051 no CONAB e
   independe do IPO; excluí-la não enfraquece o canal.
4. **Universo scoreado = 5 nomes** (4 grãos + SMTO3). O ganho de 5→6 é marginal (~+4–8pp,
   re-análise D-045) e não paga o custo metodológico.

**Custo/limitação.** Assumimos abrir mão do nome economicamente mais limpo (JALL3) em nome da
disciplina PIT, e um tier de evidência menor que o das §9 (percentuais finos = lacuna). O peso
da SMTO3 no score, refletindo a força estatística fraca da cana, é decidido no congelamento da
Fase 3.5, apenas no desenvolvimento.
