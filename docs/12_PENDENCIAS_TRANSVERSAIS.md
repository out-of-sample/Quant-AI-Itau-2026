# Registro de pendências transversais

Este documento é a fonte única para dívidas abertas que atravessam o projeto e **não** são
entregáveis normais de uma fase futura. Ele evita que ressalvas antigas, marcadores
`[A CONFIRMAR]` e decisões de governança fiquem dispersos entre documentos.

Não entram aqui tarefas já pertencentes ao plano sequencial — por exemplo, os rodadores de
H1a/H1b, a matriz de exposição, o backtest, a robustez, o holdout e a identidade visual. O
andamento dessas tarefas continua em `00_PLANO_MESTRE.md` §4 e `03_ARQUITETURA.md` §6.

## 1. Regra de manutenção

- Cada pendência recebe um identificador estável `PT-NNN`, prioridade, origem, impacto,
  critério objetivo de encerramento e estado.
- Pendência encerrada **não é apagada**: recebe data e evidência de encerramento, preservando
  a trilha de auditoria.
- Um marcador disperso só permanece no documento de origem quando traz contexto útil; nesse
  caso, ele aponta para este registro.
- Limitação irremovível e conscientemente aceita não é pendência. Ela permanece no registro
  de riscos (`07_RISCOS_E_DECISOES.md`).
- Trabalho opcional ou pertencente a uma fase posterior não é duplicado aqui.

Estados: `ABERTA`, `EM ANDAMENTO`, `BLOQUEADA` ou `ENCERRADA`.

## 2. Pendências ativas

| ID | Prioridade | Pendência | Origem e impacto | Critério de encerramento | Estado |
|---|---|---|---|---|---|
| **PT-001** | **P0 — antes de H1** | Definir formalmente se o holdout 2020–2025 veda também os desfechos físicos de H1a/H1b ou apenas retornos e decisões da estratégia | O split foi congelado em D-008, mas o CHIRPS operacional começa em 2015/16 e o painel de vintages CONAB em 2017/18. Usar 2020–2025 em H1 aumenta poder, porém deixa a validação do mecanismo influenciar o desenho antes do backtest; não usar reduz H1a a pouquíssimos anos-safra de desenvolvimento. A ambiguidade precisa ser resolvida **antes** de executar os rodadores | Nova decisão D-NNN, anterior a qualquer resultado de H1, declara o perímetro do lacre, o N efetivo resultante e o custo metodológico da escolha | **ENCERRADA (2026-07-17, D-029)** — o lacre veda a estratégia e seus parâmetros, não os testes físicos: H1a/H1b rodam no span cheio 2015/16–2024/25 (N efetivo ~8 e ~9 anos-safra) com sub-amostras dev/holdout reportadas em separado. N efetivo e custo declarados em D-029, antes de qualquer resultado de H1 |
| **PT-002** | **P0 — governança** | Confirmar no canal oficial a aplicabilidade e o mecanismo da entrega intermediária de 31/07/2026 | O edital local registra a data, mas o status operacional da entrega não está comprovado no repositório. Uma interpretação errada pode gerar descumprimento administrativo independente da qualidade científica | Evidência oficial datada (regulamento atualizado, comunicado ou resposta da organização) arquivada ou referenciada, com a conclusão refletida no plano mestre | **ABERTA** |
| **PT-003** | **P1 — fundamentação** | Completar ou substituir as três referências centrais da tese climática em `10_REFERENCIAS.md` §1 | Os títulos vieram da ideação sem autoria/DOI verificados; a tese escolhida não pode chegar ao relatório com base acadêmica menos rastreável que as teses descartadas | Cada entrada foi aberta na fonte primária e ganhou citação completa, ou foi removida/substituída por referência verificável que sustente a mesma afirmação | **ABERTA** |
| **PT-004** | **P1 — metodologia** | Curar as referências canônicas dos métodos e produtos efetivamente usados | `10_REFERENCIAS.md` §§3–4 ainda marca Newey–West/HAC, BH-FDR, block bootstrap, fatores, CHIRPS e ONI como pistas ou lacunas. A variante de bootstrap será decidida na implementação de H1; este item controla a rastreabilidade bibliográfica, não a escolha por resultado | Métodos que permanecerem no projeto têm citação conferida na fonte; produtos citados no relatório têm referência completa. Métodos/produtos descartados são removidos da lista ativa | **ABERTA** |
| **PT-005** | **P1 — qualidade de dado** | Reforçar a proveniência das poucas datas antigas do calendário CONAB que ficaram com evidência única ou apenas planejada | R10 foi resolvido operacionalmente e o carimbo falha alto, mas grãos 2017/18 9º levantamento tem apenas fonte K2; café 2017 e cana 2017/18 têm apenas calendários planejados. Erro de poucos dias afeta o corte de H1a | Segunda fonte primária/independente confirma as datas; ou uma decisão D-NNN mantém a data conservadora e pré-registra sensibilidade explícita ao deslocamento, citando as linhas afetadas | **ABERTA** |
| **PT-006** | **P3 — arquivo de ideação** | Decidir o tratamento de duas referências incompletas de teses não escolhidas | Payne (2010) e Chen–Nordhaus (2019) têm título incompleto em `10_REFERENCIAS.md` §2. Não sustentam a tese final, mas o marcador público não deve permanecer indefinidamente sem classificação | Completar na fonte ou registrar explicitamente que as entradas ficam fora da bibliografia final e são preservadas apenas como pista histórica da ideação | **ABERTA** |

## 3. Itens explicitamente fora deste registro

| Item | Onde é controlado | Por que não é pendência transversal |
|---|---|---|
| Rodadores H1a/H1b e escolha da inferência final | `00_PLANO_MESTRE.md` §4, Fase 2 | entrega da fase atual |
| Fricções e diagnósticos do backtest | Fase 4.2–4.3 e `04_PROTOCOLO_BACKTEST.md` | entregas futuras com fase proprietária; o motor 4.1 e sua contabilidade foram fechados em D-056. A cobertura restrita do dev é risco R26, não dívida transversal |
| H4/H5 e pacote da rodada única | D-068–D-072, Fases 5–6 e `05_SUITE_ROBUSTEZ.md` | pacote técnico encerrado em D-072; resta somente a decisão civil da Fase 6, que não é pendência transversal |
| CEPEA, futuros B3, CAR e extensões opcionais | `02_DADOS.md` e `05_SUITE_ROBUSTEZ.md` | limitações/extensões já localizadas, não dívidas legadas |
| Nome e identidade visual | Fase 7 e `08_IDENTIDADE.md` | decisão futura do time |
| Rate limit numérico da NASA POWER e vintage térmico imperfeito | R3/R12 em `07_RISCOS_E_DECISOES.md` | limitação aceita e mitigada por cache; POWER não é fonte primária |
| Ausência de comparador Yahoo para deslistados | D-016/D-025 | limitação aceita, sem fonte gratuita equivalente conhecida |
| Progresso semanal da CONAB | `09_FENOLOGIA_E_LIMIARES.md` §7 | descartado do experimento primário; não há ação ativa |

## 4. Auditoria documental de 2026-07-17

Esta auditoria retirou marcadores que já não representavam trabalho aberto:

- regionalização raster→município e cálculo do `Shock`, concluídos em D-027/D-028;
- ingestão PAM/IBGE, concluída em D-024;
- cross-check dos 19 papéis vivos, concluído em D-025;
- gate histórico do ComexStat, removido em D-026 por vintage irrecuperável;
- descrição do projeto como “Fase 0, sem implementação”;
- afirmações de cobertura operacional de 18 anos ou de aproximadamente 12–18 safras. O
  sinal primário começa em 2015/16 e H1a depende do painel CONAB iniciado em 2017/18; o N
  efetivo será reportado por teste, não inferido do número de linhas do painel.
