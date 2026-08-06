# Auditoria de fechamento da Fase 1

> **Status:** auditoria histórica concluída em D-025/D-026. Este documento preserva as
> evidências que autorizaram a fase seguinte; não é um checklist ainda em andamento.

Registro das verificações que autorizaram o início de C2. O objetivo foi testar integridade,
proveniência e capacidade point-in-time da ingestão — **não** avaliar a estratégia. Nenhum
sinal, retorno de carteira, Sharpe ou resultado do holdout foi calculado.

---

## 1. Preços e eventos corporativos

### Protocolo

- **Universo**: 19 tickers vivos do universo definido, sem selecionar pelo resultado.
- **Janela**: 02/01/2023–30/12/2025; 748 pregões comuns para a maioria dos papéis. AGXY3 tem
  429 por IPO e MBRF3 tem 67 por início de negociação.
- **Primária**: fechamento bruto e presença no pregão pelo COTAHIST/B3.
- **Eventos**: B3 oficial; StatusInvest apenas para cauda deslistada ou quando a B3 devolve
  histórico de caixa inteiramente vazio; registro manual somente com fonte primária.
- **Comparador**: retorno do `adjclose` Yahoo, limiar diário absoluto de 0,5%. O Yahoo é um
  detector independente, não a autoridade: toda divergência foi confrontada com fechamento
  B3 e evento societário antes de alterar o pipeline.

### Resultado por papel

| Ticker | Pregões | Classificação final |
|---|---:|---|
| SLCE3 | 748 | consistente após a correção D-016 já existente |
| AGRO3 | 748 | diferença de convenção em dividendo grande; retorno CRSP mantido |
| SOJA3 | 748 | consistente |
| BEEF3 | 748 | quatro divergências causadas por barras Yahoo, inclusive reescala temporária em abr/2025 |
| SMTO3 | 748 | consistente |
| CSAN3 | 748 | consistente |
| JALL3 | 748 | consistente |
| RAIZ4 | 748 | uma barra Yahoo incorreta e reversão no pregão seguinte |
| TTEN3 | 748 | consistente |
| VITT3 | 748 | **corrigido**: bonificação de 10%, data-com 12/04/2024, ausente do endpoint B3 atual |
| AGXY3 | 429 | consistente |
| SUZB3 | 748 | uma barra Yahoo incorreta e reversão no pregão seguinte |
| KLBN11 | 748 | **corrigido**: bonificação 10%, repetição ON/PN/UNIT e quatro parcelas iguais legítimas; barras Yahoo de 2023 não servem como referência fina |
| RAIL3 | 748 | consistente |
| HBSA3 | 748 | reescala temporária Yahoo em mar/2025; COTAHIST mantido |
| KEPL3 | 748 | uma barra Yahoo incorreta e reversão no pregão seguinte |
| MDIA3 | 748 | consistente |
| CAML3 | 748 | consistente |
| MBRF3 | 67 | consistente desde o início da negociação |

### Correções incorporadas

1. `b3_stock_to_events(..., ticker)` filtra o marcador de classe do ISIN e deduplica o mesmo
   evento por data/ratio. Sem isso, a bonificação de uma UNIT podia entrar três vezes.
2. O normalizador StatusInvest preserva linhas iguais. KLBN11 tem quatro parcelas com a mesma
   data-com e valor nominal; a soma, após a bonificação posterior de 1%, reproduz o evento
   agregado da fonte independente. Sem identificador do direito, deduplicar seria destrutivo.
3. `events_manual.py` passou a registrar as bonificações VITT3 e KLBN11. A primeira está no
   Fato Relevante CVM ID 1214846; a segunda, no BDI/B3 de 09/07/2024. Data, razão e URL da
   fonte primária acompanham cada entrada.
4. No cross-check de papel vivo, StatusInvest só substitui a B3 quando o histórico oficial de
   caixa vem vazio. Somar fontes indiscriminadamente gerou eventos espúrios em séries já
   cobertas pela B3 e foi rejeitado no próprio teste.

### Limite residual

Papéis deslistados não existem no Yahoo. Neles, a defesa é COTAHIST + eventos B3/StatusInvest,
tripwire de retorno absoluto e inspeção das datas terminais. Para papéis vivos, o Yahoo também
contém barras erradas e usa convenção multiplicativa em dividendos grandes; uma divergência é
um alerta para investigação, nunca autorização automática para alterar a série oficial.

---

## 2. Preço da commodity para H2a/H2b

### CEPEA/ESALQ

O banco oficial permite selecionar produto, especificação, frequência e período e gerar
Excel. A licença CC BY-NC 4.0 permite uso acadêmico com atribuição. Não foi localizada API
pública estável; o acesso HTTP direto é protegido por JavaScript/Cloudflare.

**Decisão**: validação brasileira manual, com arquivo bruto e hash preservados; não é
dependência do pipeline primário.

Fontes:
- `https://www.cepea.org.br/br/consultas-ao-banco-de-dados-do-site.aspx`
- `https://www.cepea.org.br/br/licenca-de-uso-de-dados.aspx`

### Futuros agro B3

A B3 disponibiliza ajustes diários e resumos por vencimento em sua área histórica. Isso
resolve a dúvida de acesso, mas não entrega uma série contínua: é preciso definir rolagem,
tratar vencimentos e distinguir ajuste observado de ajuste calculado pela metodologia da
bolsa.

**Decisão**: robustez brasileira. Futuros internacionais são a fonte primária de H2a/H2b;
fonte, regra de rolagem e horizonte exatos serão congelados na Fase 3.1 antes da execução,
evitando interpretar salto de contrato como preço econômico.

Fonte: `https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/`

---

## 3. Vintage do ComexStat

A documentação oficial estabelece três reprocessamentos ordinários:

1. semanal, para o mês corrente;
2. mensal, para todo o ano corrente;
3. anual, em fevereiro, quando o ano anterior é reprocessado e então estabilizado salvo
   revisão extraordinária.

A API e os CSVs anuais expõem apenas o vintage atual. A busca por snapshots do CSV oficial no
Wayback não retornou cópias, e não foram encontrados snapshots das respostas `POST`. Portanto,
não é possível quantificar retrospectivamente a revisão nem reconstruir o valor conhecido na
primeira divulgação de cada mês.

**Decisão (D-026)**: ComexStat continua sendo o desfecho físico de H1b *ex post*, mas sai do
gate 1.0/0.5/0.0 do backtest primário. Usar hoje o dado final com `avail_date` histórica da
primeira publicação seria lookahead de vintage. As capturas datadas já implementadas permitem
medir revisões prospectivamente.

Fontes:
- `https://www.gov.br/mdic/pt-br/assuntos/comercio-exterior/estatisticas/perguntas-frequentes-faq/5-por-que-os`
- `https://www.gov.br/mdic/pt-br/assuntos/comercio-exterior/estatisticas/perguntas-frequentes-faq/3-quando-sao-divulgadas`
- `https://www.gov.br/mdic/pt-br/assuntos/comercio-exterior/estatisticas/base-de-dados-bruta`

---

## 4. Conclusão do portão

A Fase 1 está encerrada porque as fontes centrais têm contrato explícito, os riscos de vintage
que podem ser mitigados foram tratados e o único uso historicamente impossível — o gate
ComexStat — foi retirado do sinal, em vez de ser aproximado silenciosamente. C2 `Shock` foi
construído em D-027/D-028 (raster CHIRPS → município → UF → painel CONAB). O próximo portão é
testar H1a/H1b antes de qualquer backtest de ações, após resolver PT-001. Dívidas legadas que
não pertencem às fases futuras estão centralizadas em `docs/history/pending.md`.
