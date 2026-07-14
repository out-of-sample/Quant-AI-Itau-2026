# Como trabalhamos neste repositório

Somos 2-3 pessoas mexendo no mesmo código. Estas regras existem para que ninguém sobrescreva
o trabalho do outro, para que a `main` nunca quebre, e para que, no fim, o histórico do git
conte a história do projeto — que é matéria-prima direta do relatório final.

---

## 1. Autoria dos commits

Todo commit sai no nome do integrante do time que o fez. Mensagens de commit e descrições
de PR não levam assinaturas, rodapés ou trailers de coautoria de nenhum tipo — só a
descrição técnica da mudança.

O uso de ferramentas de IA generativa ao longo do projeto é registrado em
`docs/DIARIO_GENAI.md`, que é a fonte da seção "Uso de IA Generativa" do relatório final.
Esse registro é feito lá, de forma estruturada e analisável — não espalhado pelo histórico
do git.

---

## 2. Branches

`main` é a linha do tempo oficial. **Ninguém commita direto na `main`.** Todo trabalho
acontece numa branch e volta via Pull Request.

| Prefixo | Para quê | Exemplo |
|---|---|---|
| `feat/` | funcionalidade nova (código que vai para produção) | `feat/ingest-nasa-power` |
| `fix/` | correção de bug | `fix/lag-publicacao-comexstat` |
| `docs/` | documentação, relatório, planejamento | `docs/protocolo-backtest` |
| `chore/` | infra, CI, dependências, formatação | `chore/setup-ci` |
| `exp/` | **experimento de pesquisa** (ver abaixo) | `exp/janela-fenologica-alternativa` |

### O tipo `exp/` — específico de pesquisa quantitativa

Pesquisa quant é feita de tentativas que morrem. Uma branch `exp/` é **descartável**:
pode ter notebook bagunçado, código feio, caminho sem saída. Ela **nunca faz merge direto
na `main`**.

O ciclo é:
1. Cria `exp/<ideia>`, testa a ideia, olha o resultado.
2. **Registra a conclusão** — funcionou ou não — em `docs/07_RISCOS_E_DECISOES.md` (se for
   uma decisão de desenho) ou em `docs/adr/` (se for uma escolha de arquitetura).
3. Se a ideia vingou, **reescreve limpo** numa branch `feat/` e essa sim vira PR.
4. A branch `exp/` pode ser deletada. **O aprendizado não se perde porque está no
   documento, não na branch.**

Isso resolve o problema clássico de pesquisa: hipóteses testadas e descartadas são o
material mais valioso para os critérios "Análise dos Resultados" (15%) e "Conclusão" (10%)
do edital — a banca premia honestidade sobre o que não funcionou. Se elas só existirem numa
branch morta, elas somem. Por isso o passo 2 é obrigatório, não opcional.

### Regra de ouro das branches

Branch curta. Se uma branch está aberta há mais de ~3 dias, ela provavelmente devia ter
sido quebrada em duas. Branch longa = conflito de merge doloroso = trabalho perdido.

---

## 3. Mensagens de commit (Conventional Commits)

```
<tipo>(<escopo opcional>): <descrição no imperativo, minúscula, sem ponto final>

<corpo opcional: o PORQUÊ, não o o-quê — o diff já mostra o o-quê>
```

Tipos: `feat`, `fix`, `docs`, `chore`, `test`, `refactor`, `perf`.

Bons exemplos:
```
feat(ingest): adicionar cliente da API NASA POWER com cache local
fix(signal): corrigir sinal invertido na exposicao de frigorificos

O sinal estava tratando frigorifico como produtor. Seca subindo preco de milho
comprime a margem deles, entao a exposicao tem que ser negativa. Coberto agora
por tests/test_signal_sign.py.
```

Ruim: `update`, `mudancas`, `wip`, `fix bug`.

**Um commit = uma ideia.** Se a mensagem precisa de "e" para descrever o que foi feito,
provavelmente são dois commits.

---

## 4. Pull Requests

- **Todo PR precisa de aprovação de pelo menos 1 outra pessoa do time** antes do merge.
  Isso não é burocracia: num projeto quant, um bug de lookahead que passa despercebido
  invalida o resultado inteiro e a gente só descobre tarde demais. Segundo par de olhos é
  a defesa mais barata que existe.
- O PR só pode ser mergeado com a **CI verde** (lint + testes passando).
- Merge na `main` via **squash** — mantém o histórico da `main` legível, uma entrada por
  mudança lógica.
- Descrição do PR: o que muda, por quê, e **o que foi feito para verificar** que está certo.

### Checklist de revisão para PRs que mexem em sinal ou backtest

Antes de aprovar, o revisor confirma:
- [ ] Nenhum dado usado na decisão de `t` só estaria disponível depois de `t` (lookahead)
- [ ] Nenhum `.shift(-1)` ou uso de barra futura sem justificativa explícita
- [ ] Nenhuma estatística (média, desvio, z-score, min/max) calculada sobre o período
      **inteiro** e depois aplicada retroativamente — tem que ser *expanding* ou *rolling*
- [ ] Se cria um parâmetro novo: ele foi escolhido por lógica econômica/agronômica ou por
      "testei e esse foi o que deu o melhor Sharpe"? Se for o segundo, é overfitting —
      registrar como robustez, não como escolha primária
- [ ] O holdout (2020-2025) continua lacrado?

---

## 5. Fluxo do dia a dia

```bash
git switch main && git pull                  # sempre partir do main atualizado
git switch -c feat/minha-mudanca             # branch nova
# ... trabalha, commita em pedaços pequenos ...
git push -u origin feat/minha-mudanca        # sobe a branch
# abre o PR no GitHub, pede review, CI roda sozinha
# depois do merge:
git switch main && git pull
git branch -d feat/minha-mudanca             # limpa
```

---

## 6. O que NÃO entra no git

- Dados brutos baixados (`data/raw/`, `data/interim/`) — são grandes e regeneráveis pelo
  código de ingestão. O que garante reprodutibilidade é o **código que baixa**, mais o
  hash/manifesto do que foi baixado, não o CSV commitado.
- Chaves, tokens, `.env`.
- Saídas de notebook (limpar antes de commitar).

Se você precisa que um dado seja reproduzível, o caminho é: código de ingestão determinístico
+ registro em `data/manifests/` (data de download, hash, versão da fonte).
