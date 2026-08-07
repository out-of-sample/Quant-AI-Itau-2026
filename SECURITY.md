# Política de segurança

## Versões suportadas

Este é um artefato de pesquisa, não um serviço implantado. Correções de segurança são feitas na
branch `main`; snapshots e commits históricos não recebem backport.

| Versão | Suporte |
|---|---:|
| `main` | sim |
| commits e artefatos anteriores | não |

## Como reportar uma vulnerabilidade

Não abra uma issue pública com credenciais, tokens, dados restritos ou instruções de exploração.
Use o formulário privado **Report a vulnerability** na aba Security do GitHub:

<https://github.com/out-of-sample/Quant-AI-Itau-2026/security/advisories/new>

Inclua, quando possível:

- commit ou versão afetada;
- impacto e pré-condições;
- passos mínimos para reproduzir;
- evidência sem segredo real;
- proposta de mitigação, se houver.

Se o canal privado não estiver habilitado, abra apenas uma issue genérica solicitando contato
dos mantenedores, sem revelar o conteúdo sensível.

## Escopo

São especialmente relevantes falhas que possam:

- expor chaves ou credenciais usadas por módulos de ingestão;
- executar conteúdo não confiável ao processar arquivos de fontes externas;
- escrever fora dos diretórios de dados esperados;
- alterar silenciosamente manifestos, hashes ou artefatos selados;
- contornar validações point-in-time de forma que invalide resultados publicados.

Resultados financeiros ruins, indisponibilidade de uma fonte pública, divergências esperadas de
vintage e hipóteses de pesquisa falsificadas não são vulnerabilidades de segurança. Bugs
reproduzíveis sem conteúdo sensível podem ser reportados pelas issues normais.
