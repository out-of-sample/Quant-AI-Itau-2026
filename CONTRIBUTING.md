# Como contribuir com este repositório

O ciclo original de pesquisa está concluído e a rodada fora da amostra foi selada. Contribuições
continuam bem-vindas para corrigir bugs, melhorar reprodução e propor extensões, desde que não
reescrevam os artefatos `v1` nem transformem análises pós-selo em escolhas retroativas.

Antes de começar, procure uma issue existente ou abra uma usando os formulários do GitHub.
Mudanças pequenas de documentação podem ir direto a um PR; alterações de estratégia, dados ou
inferência devem explicar previamente a nova hipótese e o novo perímetro de avaliação.

---

## 1. Autoria dos commits

Todo commit sai no nome do integrante do time que o fez. Mensagens de commit e descrições
de PR não levam assinaturas, rodapés ou trailers de coautoria de nenhum tipo — só a
descrição técnica da mudança.

O uso de ferramentas de IA generativa ao longo do projeto é registrado em
`docs/genai.md`, que é a fonte da seção "Uso de IA Generativa" do relatório final.
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
2. **Registra a conclusão** — funcionou ou não — em `docs/history/decisions.md` (decisão
   científica) ou na issue/PR correspondente (decisão puramente de implementação).
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

- **Regra normal**: todo PR precisa de aprovação de pelo menos 1 outra pessoa do time antes do
  merge. Num projeto quant, um bug de lookahead que passa despercebido invalida o resultado
  inteiro; um segundo par de olhos é a defesa mais barata que existe.
- **Exceção temporária enquanto o desenvolvimento estiver individual**: o autor pode mergear
  o próprio PR sem review somente depois de a CI ficar verde e de executar localmente a suíte
  relevante. A exigência de aprovação volta automaticamente quando o trabalho colaborativo
  for retomado.
- O PR só pode ser mergeado com a **CI verde** (lint + testes passando).
- Merge na `main` via **merge commit** — preserva os commits intencionais da branch e deixa o
  limite de cada PR explícito no histórico.
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
- [ ] Os registros e resultados selados `v1` permanecem byte a byte inalterados?
- [ ] Se a mudança propõe uma nova estratégia, ela usa novo identificador, novo pré-registro e
      nova avaliação — sem substituir o holdout publicado?

---

## 5. Setup do ambiente (primeira vez neste clone)

O ambiente é Python 3.14. As versões exatas de tudo — runtime e
ferramental — vivem em `requirements.lock` (gerado com hashes, reprodutível bit a bit).

```bash
python3.14 -m venv .venv && source .venv/bin/activate
python -m pip install --require-hashes -r requirements.lock  # stack travado, idêntico à CI
python -m pip install -e . --no-deps        # pacote quantagro em modo editável
pre-commit install                      # ativa os ganchos de qualidade a cada commit
```

A partir daí, todo commit passa automaticamente por: `ruff` (lint), `ruff format`, o tripwire
de lookahead (`scripts/check_lookahead.py`) e o de segredos (`scripts/check_secrets.py`). A
mesma bateria roda na CI — o gancho local só existe para você não descobrir na CI o que dá
para pegar na sua máquina.

Antes de abrir um PR, rode a mesma porta de qualidade da CI:

```bash
python scripts/quality.py
```

**Adicionou ou mudou uma dependência?** Edite `pyproject.toml` e regenere o lock:

```bash
pip-compile --generate-hashes --allow-unsafe --extra dev -o requirements.lock pyproject.toml
```

`--allow-unsafe` é obrigatório (pina `setuptools`/`wheel`, sem os quais a instalação com hash
falha). Commite `pyproject.toml` e `requirements.lock` juntos, sempre.

---

## 6. Fluxo do dia a dia

```bash
git switch main && git pull                  # sempre partir do main atualizado
git switch -c feat/minha-mudanca             # branch nova
# ... trabalha, commita em pedaços pequenos ...
git push -u origin feat/minha-mudanca        # sobe a branch
# abre o PR no GitHub; CI roda sozinha; pede review quando a regra normal estiver vigente
# depois do merge:
git switch main && git pull
git branch -d feat/minha-mudanca             # limpa
```

---

## 7. O que NÃO entra no git

- Dados brutos baixados (`data/raw/`, `data/interim/`) — são grandes e regeneráveis pelo
  código de ingestão. O que garante reprodutibilidade é o **código que baixa**, mais o
  hash/manifesto do que foi baixado, não o CSV commitado.
- Chaves, tokens, `.env`.
- Saídas de notebook (limpar antes de commitar).

O relatório final, seus assets canônicos e os artefatos pequenos de referência são exceções
intencionais: fazem parte do registro público do estudo. Veja `REPRODUCING.md` para a fronteira
completa entre reprodução de software, de dados e da rodada selada.

---

## 8. Licença das contribuições

Ao enviar uma contribuição, você declara ter direito de fazê-lo e concorda que ela seja
distribuída sob a licença Apache-2.0 do repositório. Não envie conteúdo de terceiros sem termos
compatíveis nem dados cuja redistribuição não esteja autorizada.

Se você precisa que um dado seja reproduzível, o caminho é: código de ingestão determinístico
+ registro em `data/manifests/` (data de download, hash, versão da fonte).
