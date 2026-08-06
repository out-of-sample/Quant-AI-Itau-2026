# Dados

O repositório separa dado volumoso de evidência versionável. Um diretório ausente em um clone
limpo não significa pipeline incompleto: `raw/`, `interim/` e `processed/` são criados
localmente e ficam fora do Git.

| Caminho | Git | Conteúdo |
|---|---:|---|
| `raw/` | não | resposta original de cada fonte, sem transformação |
| `interim/` | não | tabelas normalizadas com `ref_date` e `avail_date` |
| `processed/` | não | painéis, features e saídas volumosas |
| [`manifests/`](manifests/) | sim | captura, vintage, tamanho, URL e/ou SHA-256 |
| [`reference/`](reference/) | sim | contratos, exceções curadas, resumos e selo final |

Os manifestos são parte da evidência do backtest. Não os regenere para “atualizar” uma execução
histórica: uma captura nova deve produzir um novo manifesto e um novo identificador de
experimento.

Detalhes por provedor estão em [`../docs/02_DADOS.md`](../docs/02_DADOS.md). Os limites de
reprodução e redistribuição estão em [`../REPRODUCING.md`](../REPRODUCING.md).
