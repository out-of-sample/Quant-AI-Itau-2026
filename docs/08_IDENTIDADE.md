# Identidade da estratégia

> Status: **nome aprovado pelo time em 28/07/2026.** Sistema visual em construção.
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
| Título editorial | O CERRADO ANTES DO BOLETIM | entrega tese, território e mecanismo |

### Por que este nome

**Território.** A seriema é a ave típica do Cerrado, e o Cerrado é literalmente o polígono onde
o `Shock` é calculado: MT, GO, MS, MG e BA aparecem nas janelas congeladas de soja, milho 2ª e
cana (`features/shock_spec.py`). A brasilidade não é decoração aplicada por fora — é o bioma
dentro do qual o modelo opera.

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
topete da ave lido como uma curva de precipitação. Logo, mascote e peças finais ainda não
existem.

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

---

Se o nome mudar, o pacote de código é renomeado junto — hoje ele usa um nome técnico neutro
(`quantagro`) justamente para não travar essa decisão.
