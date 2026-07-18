# Auditoria dos canais empresariais — portão da Fase 3.1

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
econômico anterior ao equity. Seu recorte 2020–2025 permanece lacrado para confirmação futura.

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

- roda somente no desenvolvimento até 2019 nesta fase;
- usa a fonte e a regra de rolagem congeladas antes do resultado;
- agrupa inferência por ano-safra e declara N efetivo;
- não escolhe futuro, horizonte ou janela pelo melhor resultado.

Se H2a não sustentar o canal de preço, não se presume `P>0` para produtores. A ponta long é
reformulada antes de qualquer backtest de ações.

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
