# Estratégia quantitativa — choque climático e cross-section do agronegócio brasileiro

Projeto para o Desafio Itaú Asset Quant AI 2026.

---

## A tese

Choques climáticos nas regiões produtoras brasileiras carregam informação sobre a oferta
futura de commodities agrícolas. Essa informação chega ao preço das ações da B3 **com
defasagem e de forma heterogênea entre empresas**: uma seca pode elevar o preço da
commodity, reduzir o volume do produtor atingido e comprimir a margem de quem compra o grão
como insumo.

O Brasil é um dos maiores exportadores mundiais dessas commodities. A hipótese econômica
original era que uma quebra brasileira, como choque de oferta global, elevaria o preço e
criaria dispersão entre empresas. Os testes D-037–D-041 **não deram suporte estatístico a esse
canal de preço**, e D-043 mostrou que o dano de volume dominou nos produtores da amostra. Essa
distinção entre mecanismo plausível e mecanismo demonstrado orienta a reformulação atual.

A estratégia originalmente candidata era **dollar-neutral long/short dentro do agro**. O
teste no desenvolvimento mostrou que comprar produtores sob seca perde: o dano de volume
próprio dominou o benefício de preço. Essa formulação não foi invertida depois do resultado;
uma hipótese nova, Q-dominante, foi pré-registrada e está sendo construída antes de um único
teste no holdout. Neutralidade a mercado, fatores e commodities será testada, não presumida
a partir do notional.

**A ineficiência explorada é de agregação, não de acesso.** O dado é público e gratuito; caro
é cruzar grade meteorológica × mapa de produção agrícola × composição de receita e custo das
empresas.

---

## A cadeia causal (testada em etapas, não assumida)

```
choque climático  →  revisão CONAB  →  preço da commodity  →  ação
   (CHIRPS)             ✅ H1              ❌ H2              ❌ direção original
                            ↑
             ComexStat corroborou soja ex post
```

Cada seta foi tratada como hipótese com **critério de falsificação declarado antes de rodar**.
O mecanismo físico passou, mas os elos financeiros não; por isso a formulação original foi
interrompida e a reformulação é registrada como hipótese nova, não como reinterpretação.

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
| [`11_AUDITORIA_FASE1.md`](docs/11_AUDITORIA_FASE1.md) | Evidências e decisões que fecharam a ingestão point-in-time |
| [`12_PENDENCIAS_TRANSVERSAIS.md`](docs/12_PENDENCIAS_TRANSVERSAIS.md) | Fonte única das dívidas legadas e transversais ainda abertas |
| [`13_MATRIZ_EXPOSICAO.md`](docs/13_MATRIZ_EXPOSICAO.md) | Matriz fundamentalista point-in-time e auditoria do universo |
| [`14_AUDITORIA_CANAIS_EMPRESARIAIS.md`](docs/14_AUDITORIA_CANAIS_EMPRESARIAIS.md) | Portão econômico entre a matriz e a carteira: preço, volume, custo, H2/H3 e neutralidade |
| [`DIARIO_GENAI.md`](docs/DIARIO_GENAI.md) | Registro do uso de IA — acertos **e erros** |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Branches, commits, PRs, checklist de revisão |

---

## O que este projeto assume sobre rigor

Três compromissos que estruturam tudo o mais:

1. **Point-in-time ou nada.** Toda linha de dado carrega `ref_date` (a que se refere) e
   `avail_date` (quando ficou pública). Nenhuma decisão em `t` pode usar linha com
   `avail_date > t`. E, onde a *fonte* reescreve o passado — reanálise climática, revisões do
   ComexStat —, isso está identificado, medido e declarado, não ignorado.

2. **Holdout lacrado.** O recorte de desenvolvimento é 2013–2019, mas o `Shock` primário só
   existe point-in-time desde a safra 2015/16. O período 2020–2025 de retornos da estratégia
   é rodado **uma única vez**, com o desenho já congelado. H1 testou o mecanismo no span cheio,
   com desenvolvimento e holdout reportados separadamente, conforme D-029.

3. **Os achados negativos são reportados.** N efetivo pequeno, transmissão de preço ausente,
   canal líquido do produtor não identificado, beta de commodity e placebo ENSO podem impedir
   a estratégia. Esses vetos estão escritos antes do backtest, não escondidos no rodapé.

---

## Estado atual

**Fase 3.4 — construção dos canais da hipótese reformulada.** H1 confirmou o mecanismo
clima → revisão de safra para soja e milho (D-031), mas os testes de preço e ações derrubaram
a direção financeira original (D-037–D-043). A hipótese Q-dominante foi pré-registrada em
D-044. O algodão foi então testado como extensão independente e **rejeitado**: β=+0,042, sinal
contrário ao esperado, com 0/3 estimativas *leave-one-safra-out* negativas (D-048/D-049).
O próximo canal é a cana, com contrato fenológico e sinal próprios. O holdout de retornos
2020–2025 continua lacrado. Dívidas sem fase proprietária ficam em
[`docs/12_PENDENCIAS_TRANSVERSAIS.md`](docs/12_PENDENCIAS_TRANSVERSAIS.md).
