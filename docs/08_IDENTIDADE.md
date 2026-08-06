# Identidade da estratégia

> Status: **nome e sistema visual concluídos.** Nome aprovado em 28/07/2026; relatório e
> aplicações finais lacrados em 01/08/2026.
> Vale 5% da nota. O critério do edital é *nome + identidade visual coerentes com a tese* —
> ou seja, o nome não é enfeite, ele precisa **dizer o que a estratégia faz**.

---

## O nome: **SERIEMA**

> **SERIEMA**
> *Canta antes da chuva.*

Três camadas com funções distintas, para não sobrecarregar uma palavra só:

| Camada | Texto | Função |
|---|---|---|
| Nome do robô | SERIEMA | memorável, sonoro, apropriável |
| Tagline | Canta antes da chuva. | nomeia a antecipação, sem prometer retorno |
| Título editorial | DO CANTO À CARTEIRA | entrega ave, cadeia e desfecho |

### Por que este nome

**Território.** A seriema é uma ave emblemática do Cerrado, bioma central para a produção
agrícola coberta pelo modelo e para a origem cultural do nome. O suporte congelado do `Shock`,
porém, **não se limita ao Cerrado**: também inclui PR e RS em grãos e SP em cana
(`features/shock_spec.py`). O bioma sustenta a linhagem da marca, não uma descrição exaustiva
da geografia da estratégia.

**Antecipação.** A crença rural brasileira é direta: seriema cantando anuncia chuva. Isso
espelha o único elo que o projeto de fato demonstrou — H1, o choque climático antecipando a
revisão de safra da CONAB (D-031).

**Propagação da informação.** O canto da seriema se ouve a cerca de um quilômetro; ela é
chamada de "a voz do Cerrado". A metáfora não é só de previsão, é de **informação que viaja
pelo território antes de ser oficial** — que é exatamente o objeto do modelo, e a ineficiência
de agregação que a tese aponta.

**Encerramento honesto.** A seriema praticamente não voa: corre no chão. Para um projeto cuja
conclusão selada é P&L nominal positivo **sem** evidência de alpha nem de habilidade contra o
risk-free (D-075), ter um símbolo que não promete voo é um ativo, não um constrangimento.

### Controle de honestidade — obrigatório

O canto da seriema é **folclore, não meteorologia**. A ave entra como linhagem, nunca como
evidência. É proibido, em qualquer peça: afirmar que a seriema prevê chuva; sugerir que o
modelo "detecta" um fenômeno meteorológico nomeado; usar a crença popular como suporte de
claim. O enquadramento correto é o contraste — o sertanejo lê o canto, nós lemos a grade de
chuva; a ambição é a mesma, o método é que é auditável.

---

## Direção visual

Paleta de verde profundo, azul cobalto e amarelo âmbar, justificada pela **física do dado** e
não pela bandeira: precipitação é azul, anomalia é âmbar, vegetação é verde. Sem bandeira
literal, futebol ou ufanismo textual. A linguagem gráfica recorrente são curvas de chuva — o
topete da ave lido como uma curva de precipitação.

## Sistema visual final

| Elemento | Decisão |
|---|---|
| Símbolo | seriema desenhada como um `S`, em uma cor por aplicação; ave mineral no fundo escuro e verde no fundo claro |
| Verde profundo | `#123B2A` — território, vegetação e série da carteira |
| Azul cobalto | `#2468C4` — precipitação, dados e benchmark |
| Amarelo âmbar | `#F2C230` — anomalia, decisão e pontos de atenção |
| Papel | `#F6F3EA` — base editorial de baixo contraste agressivo |
| Tipografia de títulos | Fraunces, para autoridade editorial sem aparência bancária genérica |
| Tipografia técnica | IBM Plex Sans e IBM Plex Mono, para números, fontes e especificações |

O símbolo vetorial público está em `assets/brand/seriema.svg`. O sistema completo aparece
no relatório final `../report/relatorio-seriema.pdf`; a mesma linguagem abre o README sem criar uma
identidade concorrente para o repositório.

---

## Nomes descartados, e por quê

| Nome | Por que caiu |
|---|---|
| **VERANICO** | Nomeia a estiagem curta no meio da estação chuvosa. Exigia ressalva taxonômica — o sinal primário mede déficit acumulado, que pode ser seca persistente — e **contradizia o mecanismo da cana**, onde seca no inverno é benéfica. Defeito técnico, não de gosto |
| **ISOIETA** | Conceito correto (linha de igual precipitação), mas sonoridade ruim como nome de robô. As curvas permanecem como linguagem visual |
| **JANELA / ENTRETEMPO** | Genéricos: serviriam para qualquer estratégia de timing |
| **MONÇÃO** | Dupla referência elegante — as chuvas e as *monções*, expedições fluviais do Brasil colonial —, mas exige nota de rodapé |
| **CERES** | Deusa romana da agricultura; imediatamente legível, mas genérico. Serviria para qualquer estratégia agro |
| **ENTRESSAFRA** | Nomeia o período em que **não** há lavoura no campo — o oposto da janela em que o sinal opera |

O funil anterior falhava porque nomeava a **entrada** do modelo (chuva, estação, seca) em vez
do **ato** do robô. O território que resolveu foi o dos bioindicadores da cultura rural
brasileira.

O título de trabalho **O CERRADO ANTES DO BOLETIM** também foi descartado: superdeclarava a
geografia porque PR, RS e SP não são Cerrado. **DO CANTO À CARTEIRA** foi fechado em
31/07/2026 por conectar ave, sinal e decisão de alocação sem esse defeito factual.

---

O pacote de código permanece com o nome técnico neutro `quantagro`. A marca identifica a
estratégia e a peça editorial; separar os dois evita transformar uma identidade de pesquisa em
promessa de produto de software.
