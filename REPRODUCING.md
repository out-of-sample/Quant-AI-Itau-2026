# Guia de reprodução e verificação

Este projeto distingue três objetivos que costumam ser chamados, de forma imprecisa, de
“reproduzir o resultado”. A distinção é importante porque dados point-in-time não permanecem
necessariamente disponíveis no provedor depois da captura original.

## 1. O que um clone público permite verificar

Sem qualquer dado privado ou credencial, um clone limpo permite:

- instalar exatamente o ambiente verificado, a partir de um lockfile com hashes;
- executar os 607 testes unitários, parametrizados e sintéticos, que passam sem qualquer dado
  local além do que o próprio repositório versiona;
- rodar Ruff e os guards determinísticos de lookahead e segredos;
- inspecionar a especificação congelada da estratégia, do backtest e da rodada única;
- conferir hashes, cobertura e claims nos registros pequenos de `data/reference/`;
- auditar quais arquivos e vintages alimentaram o experimento em `data/manifests/`.

Isso verifica o **software e o protocolo**. Não baixa automaticamente quase 1 GB de dados nem
promete que APIs externas ainda devolvem em 2026 o mesmo snapshot histórico.

## 2. Ambiente

Requisitos:

- CPython `3.14.x`;
- Git;
- acesso à internet somente para instalar dependências e, se desejado, consultar as fontes;
- Linux é o ambiente testado pela CI.

```bash
git clone https://github.com/out-of-sample/Quant-AI-Itau-2026.git
cd Quant-AI-Itau-2026
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes -r requirements.lock
python -m pip install -e . --no-deps
python scripts/quality.py
```

O `requirements.lock` inclui dependências de runtime e desenvolvimento com versões e hashes.
`pyproject.toml` descreve o pacote; o lockfile é a autoridade para o ambiente reproduzido.

### O lock está congelado de propósito

O SHA-256 do `requirements.lock` está atestado no preflight da rodada única
([`00_preflight.json`](results/data/holdout_v1/00_preflight.json), bloco `source_attestations`) e
**continua batendo byte a byte**. É o último vínculo exato entre este repositório e o ambiente sob
o qual o experimento foi executado, então ele não recebe atualização incremental de dependência —
o `Dependabot` foi configurado sem o ecossistema `pip` por essa razão. Uma retomada da pesquisa
gera lock novo e identificador de experimento novo, não bump sobre o lock antigo.

> **Divergência conhecida e esperada:** o `pyproject.toml` **não** bate mais com o hash atestado
> (`adee00f9…` no selo, outro hoje). A causa é metadado de empacotamento alterado depois da
> rodada — licença, keywords, classificadores e URLs, adicionados ao preparar o repositório
> público. Nenhuma dependência ou versão mudou. O registro selado é imutável e continua correto;
> quem auditar deve usar o `requirements.lock` como definição do ambiente, não o `pyproject.toml`.

### Comandos de qualidade

```bash
python scripts/quality.py              # porta completa
python scripts/quality.py --skip-tests # verificações estáticas
python scripts/quality.py --fix        # formata e executa a porta completa
```

O `Makefile` oferece aliases equivalentes para ambientes que já possuem `make`, mas não é uma
dependência do projeto.

## 3. Camadas de dados

| Camada | Versionada? | Função |
|---|---:|---|
| `data/raw/` | não | respostas originais dos provedores |
| `data/interim/` | não | parquets normalizados e inputs do motor |
| `data/processed/` | não | saídas volumosas e artefatos de execução |
| `data/manifests/` | sim | URL, data de captura, vintage, tamanho e/ou hash |
| `data/reference/` | sim | contratos, exceções curadas, resumos e selo final |
| `tests/fixtures/` | sim | amostras pequenas para testes determinísticos |

Os dados grandes não são republicados por três razões: tamanho, termos próprios das fontes e
necessidade de preservar o vintage efetivamente observado. A política detalhada, fonte a fonte,
está em [`docs/methodology/data.md`](docs/methodology/data.md).

## 4. Reproduzir a ingestão

Os módulos em `src/quantagro/ingest/` e os executáveis em `scripts/` documentam as chamadas,
parsers e validações. Eles podem ser executados para construir uma captura **nova**, mas uma
captura nova não é automaticamente o mesmo vintage usado no estudo.

Antes de comparar qualquer saída:

1. confira `ref_date` e `avail_date`;
2. compare o hash e a data de captura com `data/manifests/`;
3. verifique em `docs/methodology/data.md` se a fonte reescreve o passado;
4. trate divergência de vintage como diferença de dado, não como falha silenciosa do código.

Não existe um alvo único “baixar tudo” porque algumas fontes exigem calendários curados,
downloads em lotes ou snapshots que já não são servidos historicamente. Essa limitação é parte
do resultado metodológico do projeto.

## 5. Reprodução exata da rodada selada

A reprodução bit a bit requer os seis parquets arquivados em `data/interim/holdout/`, além do
manifesto correspondente. O resumo versionado identifica cada um por caminho, tamanho e
SHA-256 em
[`data/reference/holdout_inputs_summary_v1.json`](data/reference/holdout_inputs_summary_v1.json).

O executor de `scripts/run_holdout_once.py` foi construído para uma rodada econômica única.
**Não execute `--execute` para “tentar de novo” ou substituir o resultado publicado.** O registro
canônico é:

- [`data/reference/holdout_run_record_v1.json`](data/reference/holdout_run_record_v1.json);
- [`data/reference/holdout_result_v1.json`](data/reference/holdout_result_v1.json);
- [`data/reference/holdout_run_record_v1_attempt1_failed.json`](data/reference/holdout_run_record_v1_attempt1_failed.json).

Uma pesquisa derivada deve criar outra especificação, outro identificador de pacote e outro
holdout. Nunca deve sobrescrever os artefatos `v1`.

## 6. Verificar o relatório

```bash
sha256sum report/relatorio-seriema.pdf
```

Valor esperado:

```text
6f2db0179a67d0a742c40d79aea106f78984e4865237948e66239b13aa54be9f
```

Os números do PDF devem reconciliar com `data/reference/holdout_result_v1.json` e com as fontes
indicadas em `docs/methodology/backtest.md`. O PDF é uma síntese editorial; os JSONs selados e
o código são a trilha de auditoria.

## 7. Limites conhecidos

- Reexecução futura de APIs não garante o vintage original.
- Alguns dados históricos são redistribuíveis apenas sob os termos do provedor.
- O holdout contém cinco anos-safra; o N efetivo é pequeno apesar do painel diário.
- Passar a suíte comprova invariantes implementados, não prova a hipótese econômica.
- Os guards são tripwires conservadores e não substituem revisão humana de lookahead.

Esses limites são declarados para tornar a reprodução verificável, não para sugerir uma precisão
que o acervo público não oferece.
