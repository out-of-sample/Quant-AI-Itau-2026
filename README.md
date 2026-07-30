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
uma hipótese nova, Q-dominante, foi pré-registrada (D-044), congelada antes de qualquer
retorno fora da amostra (D-053) e avaliada **uma única vez** no holdout (D-075). Neutralidade
a mercado, fatores e commodities foi testada, não presumida a partir do notional — e é
exatamente onde a estratégia falhou.

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

2. **Holdout de tiro único.** O recorte de desenvolvimento é 2013–2019, mas o `Shock` primário
   só existe point-in-time desde a safra 2015/16. O período 2020–2025 de retornos da estratégia
   foi rodado **uma única vez**, em 27/07/2026, com o desenho congelado desde D-053 e o que
   seria reportado pré-registrado em D-073. Não houve segunda tentativa: o resultado registrado
   é o resultado. H1 testou o mecanismo no span cheio, com desenvolvimento e holdout reportados
   separadamente, conforme D-029.

3. **Os achados negativos são reportados.** N efetivo pequeno, transmissão de preço ausente,
   canal líquido do produtor não identificado, beta de commodity e placebo ENSO podem impedir
   a estratégia. Esses vetos estavam escritos antes do backtest — e **um deles se realizou**.

---

## Resultado (holdout 2020/21–2024/25, rodada única selada em D-075)

| | |
|---|---|
| Teste primário H′ (permutação exata, α=0,10 unilateral) | p = 0,0625 — **passou**; 4 de 5 anos-safra com inclinação positiva |
| Retorno total da carteira, cenário base | **+16,97%** em 1.186 pregões (CAGR 3,36%, vol 12,5%, drawdown máx. −20,9%) |
| H4 — alpha contra mercado, fatores e commodity | alpha diário −0,000238, t = −1,03 — **falhou** |
| Placebo geográfico H5 | morreu como devia (p = 0,56; 43% da magnitude real) |
| Contra o benchmark que declaramos antes (risk-free) | Sharpe de excesso **−0,50**; Deflated Sharpe 0,025 com 39 tentativas declaradas |

**A leitura honesta é negativa.** A carteira ganhou dinheiro nominal e perdeu para o CDI ao
longo de todo o holdout. Pela régua pré-registrada, as claims liberadas são *P&L out-of-sample
positivo* e *evidência out-of-sample da estratégia*; a claim de **alpha climático está vetada**,
porque H4 falhou. A conclusão do projeto é **ausência de evidência de habilidade**, e ela vai
para a primeira página do relatório, não para o rodapé.

Duas observações pós-selo que registramos sem agir sobre elas: BRFS3 responde por 67% do P&L
bruto (HHI 0,56) e remover a SMTO3 elevaria o retorno de +17% para +67%. Ambas são achados,
**não** autorização para mexer numa carteira já selada.

---

## Estado atual

**Fase 7 — relatório e identidade.** A rodada técnica está encerrada desde 27/07/2026: o
holdout foi aberto uma única vez e selado, e não há terceira tentativa. O que resta é converter
o material em um PDF de 5 páginas, 16:9, anônimo — o único entregável avaliado. Dívidas sem
fase proprietária ficam em
[`docs/12_PENDENCIAS_TRANSVERSAIS.md`](docs/12_PENDENCIAS_TRANSVERSAIS.md).

---

## Como rodar

```bash
python3.14 -m venv .venv && source .venv/bin/activate
pip install -r requirements.lock && pip install -e . --no-deps
pytest                                              # suíte completa
python scripts/check_lookahead.py $(git ls-files '*.py')   # tripwire de lookahead
```

Os dados brutos não são versionados (são grandes e regeneráveis pelos módulos de `ingest/`);
o que garante a auditabilidade é o par código-de-download + `data/manifests/`, que registra o
hash e a data de captura de cada vintage usado.
