# Estratégia quantitativa — choque climático e cross-section do agronegócio brasileiro

Projeto para o Desafio Itaú Asset Quant AI 2026.

---

## A tese

Choques climáticos nas regiões produtoras brasileiras carregam informação sobre a oferta
futura de commodities agrícolas. Essa informação chega ao preço das ações da B3 **com
defasagem e de forma heterogênea entre empresas**: uma seca é *boa* para quem **vende** a
commodity (o preço internacional sobe) e *ruim* para quem a **compra** como insumo (a margem
é comprimida).

O Brasil é um dos maiores exportadores mundiais dessas commodities — logo, uma quebra de safra
brasileira é um **choque de oferta global**, e **eleva** o preço. É por isso que a leitura
intuitiva ("detectou seca ⇒ vende agro") está economicamente errada, e por que o alfa não está
na direção do setor, mas na **dispersão dentro dele**.

A estratégia é, portanto, **market-neutral long/short dentro do agro**: comprada em
produtores, vendida em processadores, dimensionada pela exposição líquida de cada empresa a
cada commodity.

**A ineficiência explorada é de agregação, não de acesso.** O dado é público e gratuito; caro
é cruzar grade meteorológica × mapa de produção agrícola × composição de receita e custo das
empresas.

---

## A cadeia causal (testada em etapas, não assumida)

```
choque climático  →  revisão da estimativa de safra da CONAB  →  preço da commodity  →  ação
   (CHIRPS)            (painel de vintages, data conhecida)        (futuro/CEPEA)      (B3)
                                        ↑
                     confirmação independente: volume exportado (ComexStat)
```

Cada seta é uma hipótese com **critério de falsificação declarado antes de rodar**. Se o clima
não prevê a revisão da CONAB, o mecanismo é falso e o projeto para e reformula — em vez de
seguir para o backtest e encontrar um alfa que seria coincidência.

---

## Documentação

Comece por **[`docs/00_PLANO_MESTRE.md`](docs/00_PLANO_MESTRE.md)**.

| | |
|---|---|
| [`01_TESE_E_PRE_REGISTRO.md`](docs/01_TESE_E_PRE_REGISTRO.md) | Hipóteses formalizadas e **pré-registradas**, com critério de falsificação |
| [`02_DADOS.md`](docs/02_DADOS.md) | Fontes, latências e **quais delas reescrevem o passado**. Todas testadas ao vivo |
| [`03_ARQUITETURA.md`](docs/03_ARQUITETURA.md) | Pipeline em camadas e o contrato de cada uma |
| [`04_PROTOCOLO_BACKTEST.md`](docs/04_PROTOCOLO_BACKTEST.md) | Execução, custos, universo dinâmico, holdout |
| [`05_SUITE_ROBUSTEZ.md`](docs/05_SUITE_ROBUSTEZ.md) | Testes de robustez, com resultado esperado declarado **antes** |
| [`06_CRITICA_ADVERSARIAL.md`](docs/06_CRITICA_ADVERSARIAL.md) | O projeto atacado por um avaliador hostil |
| [`07_RISCOS_E_DECISOES.md`](docs/07_RISCOS_E_DECISOES.md) | Riscos vivos e log datado de decisões |
| [`08_IDENTIDADE.md`](docs/08_IDENTIDADE.md) | Nome e identidade visual |
| [`09_FENOLOGIA_E_LIMIARES.md`](docs/09_FENOLOGIA_E_LIMIARES.md) | Quando o clima importa, por cultura e estado |
| [`10_REFERENCIAS.md`](docs/10_REFERENCIAS.md) | Referências acadêmicas, métodos e fontes usados — só o rastreável, lacunas marcadas |
| [`DIARIO_GENAI.md`](docs/DIARIO_GENAI.md) | Registro do uso de IA — acertos **e erros** |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Branches, commits, PRs, checklist de revisão |

---

## O que este projeto assume sobre rigor

Três compromissos que estruturam tudo o mais:

1. **Point-in-time ou nada.** Toda linha de dado carrega `ref_date` (a que se refere) e
   `avail_date` (quando ficou pública). Nenhuma decisão em `t` pode usar linha com
   `avail_date > t`. E, onde a *fonte* reescreve o passado — reanálise climática, revisões do
   ComexStat —, isso está identificado, medido e declarado, não ignorado.

2. **Holdout lacrado.** Desenvolvimento em 2013-2019; 2020-2025 é rodado **uma única vez**,
   com o desenho já congelado. O resultado vai para o relatório, qualquer que seja.

3. **Os achados negativos são reportados.** Há três coisas que podem matar a tese (N efetivo
   pequeno; a estratégia ser apenas beta de commodity; o sinal ser El Niño disfarçado). Estão
   escritas no documento de entrada, não escondidas no rodapé.

---

## Estado atual

**Fase 0 — planejamento e pré-registro.** Tese formalizada, hipóteses congeladas, fontes de
dados verificadas ao vivo, arquitetura especificada, riscos mapeados. Ainda sem implementação.
