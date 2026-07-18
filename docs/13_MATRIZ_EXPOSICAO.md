# Matriz de exposição fundamentalista

> Especificação do Método A de D-007. Este documento separa, de propósito, a regra definida
> antes da classificação das empresas do resultado da aplicação dessa regra. Nenhum retorno
> de ação participa da construção da matriz.

---

## 1. Papel da matriz

O choque climático é observado por cultura, mas a decisão de investimento é por empresa. A
matriz `E` faz essa tradução:

```text
S(i,t) = soma_c E(i,c,t) * Shock(c,t)
```

No experimento primário, `c` pertence a `{soja, milho 2ª safra}`. Exposição positiva indica
receita diretamente beneficiada pelo encarecimento do grão; exposição negativa indica custo
direto de insumo que comprime margem quando o grão encarece.

`E` não é estimada com retornos. Betas de commodity pertencem ao Método B de robustez e nunca
alteram retroativamente a matriz primária.

## 2. Unidade de observação e contrato point-in-time

Cada vintage da matriz é identificado por `ticker × exposure_id` e contém exatamente uma
linha para cada cultura primária. Toda linha carrega:

- `ref_date`: data de referência econômica do documento;
- `avail_date`: primeira data em que a evidência podia ser conhecida;
- URL, título e localização dentro da fonte;
- direção, materialidade e peso da cultura;
- resumo factual suficiente para refazer a classificação.

Para uma decisão em `t`, usa-se somente o último vintage integral da empresa com
`avail_date <= t`. Não há preenchimento para trás: antes da primeira evidência admissível, a
empresa não possui exposição definida e não integra o universo. Uma nova divulgação pode
alterar `E` para frente, nunca reescrever datas anteriores.

Fontes admissíveis, em ordem:

1. CVM/SEC e documentos de oferta;
2. relatório anual, release ou apresentação no RI da companhia;
3. fonte secundária apenas como pista — nunca como evidência final.

Quando a data exata de publicação não puder ser provada, usa-se um limite posterior
conservador, identificado como `conservative_bound`. A matriz não usa a data econômica do
relatório como se fosse a data de disponibilidade.

## 3. Regra de construção congelada

Para empresa `i` e cultura `c`:

```text
E(i,c) = direction(i) * materiality(i) * crop_weight(i,c)
```

### 3.1 Direção

| Valor | Critério |
|---:|---|
| `+1` | a companhia produz e vende diretamente soja/milho como atividade operacional recorrente |
| `-1` | a companhia compra diretamente soja, milho ou derivado imediato como insumo recorrente de produção |
| `0` | não há canal direto comprovado |

Logística, armazenagem, sementes, fertilizantes, defensivos, máquinas e exposição genérica
ao ciclo do agro são canais **indiretos**. Não recebem sinal primário. Uma empresa que compra
e vende o mesmo grão, ou cuja direção líquida não é demonstrável, fica fora do primário.

### 3.2 Materialidade

A escala é ordinal porque as companhias divulgam métricas incompatíveis entre si. Usar uma
porcentagem de receita de um produtor como se fosse comparável a uma porcentagem de custo de
um frigorífico criaria precisão falsa.

| `materiality` | Evidência consolidada disponível antes da decisão |
|---:|---|
| `1,00` | canal direto representa pelo menos 50% da receita/custo consolidado |
| `0,50` | canal direto representa de 10% (inclusive) a menos de 50% |
| `0,25` | canal direto comprovado, mas abaixo de 10% ou sem percentual consolidado separável |
| `0,00` | indireto, ambíguo ou sem evidência admissível |

Se a fonte trouxer apenas segmento, a participação do segmento no consolidado é o limite
superior da materialidade; não se presume que 100% do segmento seja sensível ao grão.

### 3.3 Composição entre culturas

Os `crop_weight` são não negativos e somam 1 dentro de cada vintage elegível:

1. usar a decomposição de receita/custo por cultura, se existir;
2. na ausência dela, usar volume físico ou área plantada por cultura;
3. se a companhia comprovar uma cesta conjunta soja+milho sem abertura, usar `0,5/0,5` e
   marcar `equal_split_unresolved`;
4. nunca desmembrar uma categoria agregada por memória, notícia ou conveniência.

A divisão igual é uma hipótese explícita de ignorância, não uma estimativa. Ela será objeto
de sensibilidade na Fase 5.

## 4. Critérios de inclusão e veto

Uma empresa só é elegível ao sinal primário se:

- tiver ao menos um vintage completo e admissível disponível em `t`;
- a direção econômica for direta e não ambígua;
- as duas culturas estiverem representadas, inclusive com peso zero quando cabível;
- a fonte e a conta da classificação forem reproduzíveis;
- também passar pelos filtros point-in-time de negociação, seasoning e liquidez.

Ausência de evidência não significa exposição zero; significa **não elegível**. Nomes não
devem ser promovidos apenas para aumentar o cross-section.

## 5. Testes obrigatórios

O código deve falhar alto para:

- vintage incompleto, cultura desconhecida ou duplicata;
- `ref_date > avail_date`;
- materialidade fora de `{0, 0,25, 0,50, 1}`;
- pesos negativos ou cuja soma difira de 1;
- `E` fora de `[-1,+1]`;
- dois vintages da mesma empresa com a mesma `avail_date`.

O teste-canário point-in-time acrescenta uma divulgação futura e verifica que a matriz
observável no passado permanece idêntica.

## 6. Resultado da aplicação

Esta seção será preenchida somente depois de a regra acima estar registrada no histórico do
git. Ela mostrará tanto os nomes incluídos quanto todos os candidatos recusados, com o motivo.
