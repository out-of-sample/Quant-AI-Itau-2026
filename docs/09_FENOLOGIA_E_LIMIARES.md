# Especificação fenológica e regional do `Shock`

> **Especificação primária congelada em 16/07/2026 (D-023), antes de observar retornos.**
> O contrato executável está em `features/shock_spec.py`. Mudá-lo depois de consultar retorno,
> Sharpe ou alfa cria uma nova especificação secundária e exige decisão datada em
> `07_RISCOS_E_DECISOES.md`; não reescreve silenciosamente o caso primário.

Este documento define quais culturas, regiões, períodos e variáveis climáticas entram no
`Shock` primário. Seu objetivo é limitar graus de liberdade: a agronomia escolhe o desenho;
o backtest apenas o avalia.

---

## 1. Caso primário congelado

O caso primário usa **somente soja e milho 2ª safra** e **somente déficit de precipitação
CHIRPS**. A temperatura NASA POWER, outras culturas, caixas retangulares e deslocamentos de
janela são testes secundários.

| Cultura | UFs fixadas | Cobertura física no 12º lev. 2024/25 | Fase crítica |
|---|---|---:|---|
| Soja | MT, GO, PR, RS, MS, MG, BA | **82,2%** da produção nacional | R1–R6: floração, formação de vagens e enchimento |
| Milho 2ª safra | MT, PR, GO, MS | **86,2%** da produção nacional | pré-floração ao início do enchimento de grãos |

A regra de seleção foi definida sem retornos: para cada cultura, adotou-se o menor conjunto de
UFs que ultrapassa 80% da produção no último 12º levantamento encerrado disponível na data do
congelamento. O limiar reduz ruído geográfico sem transformar a escolha de estados em busca de
resultado. O suporte fica **fixo** daqui em diante; apenas os pesos point-in-time variam.

### Por que o primário não inclui todas as culturas

- **Soja e milho 2ª safra** têm mecanismo hídrico linear e citável, grande relevância física,
  exportação diretamente observável e 12 vintages anuais da CONAB desde 2017/18.
- **Algodão** tem somente poucos anos datáveis no painel: `id_levantamento=99` impede carimbar
  boa parte da história anterior a 2022/23.
- **Café** exige uma sequência seca→chuva na florada e mistura arábica/conilon; um déficit
  linear seria biologicamente errado.
- **Cana** inverte o sinal entre crescimento e maturação e o painel datável também é curto.
- Incluir todas as variantes no teste principal multiplicaria hipóteses com um número efetivo
  de safras já pequeno (R1). Algodão, café e cana permanecem extensões pré-declaradas, não
  alternativas a serem promovidas porque geraram um resultado melhor.

---

## 2. Janelas críticas por cultura e UF

As datas são inclusivas e relativas ao ano-safra `AAAA/AA`. Foram reconciliadas com o
calendário de plantio/colheita da CONAB, o ZARC/MAPA e a fisiologia descrita pela Embrapa.
Não há ajuste por retorno.

| Cultura | UF | Janela primária | Fase |
|---|---|---|---|
| Soja | MT, GO, PR, MS, MG | **1/dez(AAAA)–fim/fev(AA)** | R1–R6 |
| Soja | RS, BA | **1/jan–31/mar(AA)** | R1–R6; calendário mais tardio |
| Milho 2ª | MT | **15/mar–15/mai(AA)** | floração/enchimento; corte das chuvas |
| Milho 2ª | GO | **15/mar–30/abr(AA)** | floração/enchimento |
| Milho 2ª | PR, MS | **1/abr–31/mai(AA)** | floração/enchimento |

O código materializa inclusive 29 de fevereiro em safra bissexta e falha para ano-safra fora
do formato `AAAA/AA`. O deslocamento de calendário do RS não pode ser apagado por uma única
janela nacional.

### Evidência fisiológica usada

- **Soja**: a necessidade hídrica atinge 7–8 mm/dia na floração e no enchimento; R1–R6 exige
  cerca de 120–300 mm distribuídos em 30–60 dias. Temperaturas acima de 40 °C são adversas à
  floração e à retenção de vagens.
- **Milho**: a exigência hídrica máxima ocorre no embonecamento ou logo depois. Déficit antes,
  durante e depois dessa fase reduz a produtividade em aproximadamente 20–30%, 40–50% e
  10–20%, respectivamente. Isso sustenta uma janela estreita, não uma estação inteira.

Os valores absolutos servem para interpretação e robustez. O primário é contínuo e
padronizado; não cria um degrau arbitrário em 120 mm, 7 mm/dia ou outro limiar.

---

## 3. Definição matemática sem lookahead

Para cultura `c`, UF `u`, safra `s` e data de decisão `D`, seja `W_{c,u,s}` a janela da seção
anterior. Só entram dias cujo CHIRPS preliminar já tem `avail_date ≤ D`:

```text
P_{c,u,s}(D) = precipitação acumulada do início de W
               até min(fim de W, último dia disponível em D)

z_{c,u,s}(D) = [P_{c,u,s}(D) − média expanding do mesmo trecho em safras anteriores]
               / desvio expanding do mesmo trecho em safras anteriores

Shock_{c,u,s}(D) = −z_{c,u,s}(D)
```

Logo, chuva abaixo da climatologia gera `Shock > 0`. Essa convenção identifica **estresse
físico**, não determina sozinha retorno acionário. A hipótese original de que o benefício de
preço dominaria no produtor foi rejeitada em D-037–D-043; a direção financeira reformulada é
tratada separadamente em D-044 e não reescreve a definição climática.

Regras duras:

1. **Climatologia expanding**, com no mínimo dez safras estritamente anteriores a `s`.
   Média aritmética e desvio-padrão amostral (`ddof=1`); não há EWMA nem ponderação escolhível.
2. Comparar sempre o **mesmo trecho da janela**. Em 20 de janeiro, o acumulado corrente não
   pode ser comparado com dezembro–fevereiro completo dos anos anteriores.
3. Antes do início da janela, `Shock` fica ausente; depois do fim, permanece fixo para a safra.
4. Desvio histórico zero, menos de dez safras ou cobertura climática insuficiente geram
   ausente e falha de qualidade — nunca zero de estresse.
5. O CHIRPS `prelim` é o dado operacional primário; `final` mede contaminação por revisão.
6. Lag primário de clima = sete dias corridos; 3 e 14 dias são sensibilidades já declaradas.
7. A climatologia expanding usa o CHIRPS `final` histórico; o sinal corrente usa `prelim`.
   Como o arquivo prelim começa em 2015 e os primeiros meses foram carregados em bloco, o
   primeiro ano-safra completo do caso primário é **2015/16**. Não há sinal primário em
   2013–2014 (R16).

### Agregação nacional

O teste H1a usa diretamente `Shock_{c,u,s}` no painel UF × cultura. Para gerar o sinal nacional:

```text
Shock_{c,s}(D) = Σ_u w_CONAB_{c,u,s−1} · Shock_{c,u,s}(D)
```

`w_CONAB` vem da **safra anterior já encerrada e publicada**, restrita às UFs fixadas e
renormalizada para somar 1. A estimativa corrente que será revisada em H1a nunca pode também
definir seu próprio peso.

---

## 4. Geografia: municípios e UFs, não caixas escolhidas à mão

As caixas `MT_norte` e `MATOPIBA_BA` em `ingest/chirps.py` e seus centroides no POWER foram
úteis para validar download, GeoTIFF, `nodata`, join entre fontes e revisão prelim→final. Elas
continuam como **smoke tests de ingestão**, mas não definem a geografia do sinal primário.

O procedimento congelado é:

1. Obter a média CHIRPS diária dentro da malha municipal IBGE **edição 2013**, fixa para todo
   o teste e gerada antes da primeira janela operacional (D-024).
2. Dentro de cada UF, ponderar municípios pela quantidade produzida na PAM/SIDRA tabela 1612,
   usando o ano mais recente cuja **data oficial de divulgação** seja `≤ D`.
3. Para H1a, manter o painel por UF. Para o sinal nacional, agregar as UFs pelos pesos CONAB
   da safra anterior encerrada (§3).

Formalmente, para município `m` dentro de `u`:

```text
Clima_{c,u,t} = Σ_{m∈u} [q_PAM(m,c,y(D)) / Σ_j q_PAM(j,c,y(D))] · Clima_{m,t}
```

Essa composição separa dois papéis:

- **PAM/IBGE** localiza a produção dentro da UF, com granularidade municipal;
- **CONAB** determina a importância nacional da UF com informação anterior à safra corrente.

### Limitações declaradas da geografia

- A PAM é anual e pode revisar anos antigos. O calendário efetivo 2014–2024 está curado em
  `pam_calendar.py`; capturas e manifestos provam a versão usada, mas não reconstroem valores
  originalmente publicados. Os 130 símbolos `...` da captura integral permanecem `NaN` e são
  contabilizados por cultura/UF.
- A PAM não separa milho 1ª e 2ª safra por município. Nos quatro estados selecionados, o peso
  municipal de milho total é um proxy espacial para o milho 2ª safra; essa aproximação entra
  como risco, não como precisão fictícia.
- Média municipal não é máscara de talhão. Ela é mais defensável do que uma caixa arbitrária,
  mas ainda dilui microclimas e heterogeneidade dentro de municípios grandes.
- A malha 2013 evita fronteiras futuras e quebra estrutural do suporte, ao custo de ignorar
  refinamentos de limites posteriores. Geocódigo positivo ausente falha alto; não é descartado.
- O ZARC identifica municípios e decêndios aptos, mas não informa onde e quando cada produtor
  efetivamente semeou. Usá-lo para mover a janela safra a safra fingiria precisão inexistente.

---

## 5. O papel confirmado do ZARC

O item que antes estava marcado como “formato não testado” foi resolvido. O Portal de Dados
Abertos do MAPA publica CSV por safra, UTF-8 e separado por `;`, com:

- cultura, safra, grupo de ciclo, solo, município/geocódigo, UF e manejo;
- 36 colunas `dec1`–`dec36`, uma por decêndio;
- níveis de risco 20%, 30% e 40%; zero significa período não indicado naquela combinação.

O arquivo 2024/25 foi aberto e inspecionado em 16/07/2026 (cerca de 202 MB). O dicionário
oficial confirma que `Cod_Ciclo` representa os grupos I–VI, `Cod_Outros_Manejos=1` é sequeiro
e `dec1`–`dec36` são períodos de plantio. O conjunto oferece arquivos desde 2016/17.

**Uso no desenho**: fonte externa para validar se as janelas fixas são agronomicamente
plausíveis e, futuramente, para uma robustez pré-declarada por grupo de ciclo. Não entra como
seletor dinâmico do caso primário, porque escolher solo, ciclo e nível de risco depois dos
resultados reabriria dezenas de graus de liberdade.

Fontes oficiais verificadas:

- [Tábua de Risco ZARC — dados abertos do MAPA](https://dados.agricultura.gov.br/dataset/tabua-de-risco-zoneamento-agricola-de-risco-climatico)
- [Dicionário oficial da Tábua de Risco](https://dados.agricultura.gov.br/dataset/6d3d141c-885e-41a4-ab7f-dc8ff323b96f/resource/bebb0ebb-bc75-460c-b900-a7a1ebd87bee/download/dicionario-de-dados-tabua-de-risco-2026.pdf)
- [Calendário de Plantio e Colheita de Grãos — CONAB](https://antigo.conab.gov.br/institucional/publicacoes/outras-publicacoes/item/download/28424_34d371f808b23d9bd37b9101c8ed5094)
- [Soja em Carência de Água — Embrapa Soja](https://bioinfo.cnpso.embrapa.br/seca/index.php?id=73&option=com_content&view=article)
- [Manejo hídrico do milho — Embrapa Milho e Sorgo](https://www.embrapa.br/en/web/agencia-de-informacao-tecnologica/cultivos/milho/producao/irrigacao/manejo)
- [PAM — Produção Agrícola Municipal/IBGE](https://www.ibge.gov.br/estatisticas/economicas/agricultura-e-pecuaria/9117-producao-agricola-municipal-culturas-temporarias-e-permanentes.html)

---

## 6. Especificações secundárias pré-declaradas

Não são candidatas intercambiáveis ao primário. Cada bloco responde a uma pergunta específica
e seus testes pertencem a uma família sujeita a BH-FDR.

| Especificação | Pergunta | Regra fixa |
|---|---|---|
| Temperatura POWER | calor acrescenta informação à chuva? | soja: dias `T_max > 40 °C`; milho: dias `T_max > 35 °C`; mesma janela e UF; limitação de vintage D-019 |
| Vintage CHIRPS final | quanto o dado revisado infla o mecanismo? | trocar apenas `prelim` por `final`; todo o resto idêntico |
| Lag climático | resultado depende da hipótese operacional? | 3, 7 e 14 dias; 7 é primário |
| Janela temporal | efeito sobrevive a pequena imprecisão fenológica? | deslocar o bloco completo em −10 e +10 dias; sem otimizar cada borda |
| ZARC por ciclo | janela oficial mais granular confirma o sinal? | se implementada, fixar previamente solo, manejo, risco e grupo; nunca selecionar pelo retorno |
| Algodão | o mecanismo replica numa cultura concentrada em MT/BA? | contrato D-047: MT 15/mar–31/mai e BA 1/fev–30/abr. **Testado e rejeitado em D-049** (β de produção +0,042, sinal contrário; 0/3 LOO negativos); não entra no score |
| Café | a sequência seca→chuva acrescenta mecanismo distinto? | especificação própria; déficit linear é proibido |
| Cana | crescimento e ATR respondem com sinais opostos? | nov–abr: seca ruim; mai–set: seca favorece ATR; nunca um z-score anual único |

### NDVI

NDVI continua sendo **validação ex post**, nunca gerador de posição (D-011). A latência real
observada no INPE/BDC foi de cerca de quatro meses. Seu uso é verificar se o choque climático
antecedeu perda de vigor vegetativo, não antecipar o mercado.

### Detalhe preservado das extensões

Estas regras não integram o primário, mas continuam registradas para impedir que uma extensão
futura volte à formulação biologicamente errada.

**Algodão**

| UF | Plantio típico | Floração/formação de maçãs |
|---|---|---|
| MT | dez–fev, em grande parte após soja | **mar–mai** |
| BA | nov–jan | **jan–mar** |

MT e BA respondiam por aproximadamente 91% da pluma no 12º levantamento 2024/25. A extensão
usa chuva nas duas janelas, mas seu H1a tem poucos anos datáveis por causa do legado
`id_levantamento=99`.

**Café**

O ciclo fenológico é bienal. Florada, chumbinho e expansão dos frutos concentram-se em
setembro–dezembro; granação, em janeiro–março; a janela de geada é julho–agosto. A florada
exige déficit hídrico prévio **seguido de retomada de chuva**: menos chuva isoladamente não é
um estresse monotônico. Uma eventual extensão deve codificar a sequência, separar
arábica/conilon e declarar regiões antes dos resultados.

Como referências agronômicas secundárias já verificadas: déficit anual acima de 150 mm
compromete a longevidade econômica do arábica; faixa de aptidão citada de 18–22 °C com déficit
abaixo de 150 mm. Para geada, o proxy operacional documentado é `T_min` no abrigo `≤2 °C`
(aproximadamente −2 a −3 °C na relva). Não existe catálogo oficial completo de geadas; um
índice histórico teria de ser construído com estações do INMET/BDMEP.

**Cana-de-açúcar**

| Fase Centro-Sul | Período | Efeito da seca |
|---|---|---|
| grande crescimento | nov–abr | **ruim**: reduz tonelagem/TCH |
| maturação | mai–set | pode ser **boa para ATR**: reduz crescimento e favorece sacarose |

Na safra 2024/25, produtividade caiu enquanto o ATR subiu 1,33%, confirmação de que os dois
canais podem divergir. A extensão deve modelar tonelagem e ATR separadamente; um `Shock`
anual linear de seca é proibido.

O contrato D-050 fixa duas janelas Centro-Sul mais estreitas e sem sobreposição: **dez–fev**
para crescimento/tonelagem (diagnóstico, β esperado negativo) e **jun–ago** para
maturação/ATR (portão, β esperado positivo). O suporte SP+MG+GO+MS+PR responde por 87,8% da
produção CONAB 2024/25. O teste usa os oito ciclos completos e datáveis 2018/19–2025/26 e
CHIRPS mensal, preservando `prelim` no trecho corrente e `final` na climatologia.

Fontes oficiais verificadas antes do teste:

- Embrapa, [Características da cana-de-açúcar](https://www.embrapa.br/en/web/agencia-de-informacao-tecnologica/cultivos/cana-de-acucar/pre-producao/caracteristicas): calor e água favorecem crescimento; menor disponibilidade hídrica e temperaturas amenas favorecem maturação e sacarose;
- Embrapa, [Clima](https://www.embrapa.br/en/web/agencia-de-informacao-tecnologica/cultivos/cana-de-acucar/pre-producao/caracteristicas/clima): água é essencial ao crescimento e a maturação interrompe crescimento vegetativo para acumular sacarose;
- CONAB, [Safra de cana-de-açúcar](https://www.gov.br/conab/pt-br/atuacao/informacoes-agropecuarias/safras/safra-de-cana-de-acucar): quatro levantamentos anuais e boletins oficiais usados no calendário point-in-time.

**Resultado D-051.** Maturação/ATR passou o critério direcional: β `+0,0134`, 8/8 exclusões
de safra e 5/5 UFs positivas, mas sem significância convencional ou por bootstrap. O
diagnóstico crescimento/tonelagem teve β `−0,0061`, sinal esperado porém fraco. Isso valida
com ressalva a separação fenológica; não prova receita nem retorno de usina.

**NDVI/INPE Brazil Data Cube**

O WTSS do INPE foi testado com MODIS `mod13q1-6.1`/`myd13q1-6.1` (16 dias, 250 m; série desde
2000). A curva de dupla safra em MT era legível, mas o serviço entregava dados com atraso real
de cerca de quatro meses em 2026. SATVeg foi descartado por cobrar pelo mesmo produto MODIS;
Google Earth Engine não teve latência confirmada. Terra/Aqua têm encerramento científico
previsto para 2027, então uma versão operacional futura migraria para VIIRS ou Sentinel-2.

---

## 7. Graus de liberdade fechados e estado de implementação

| Elemento | Estado após D-028 |
|---|---|
| culturas primárias | fechado: soja + milho 2ª |
| UFs primárias | fechadas: 7 da soja + 4 do milho 2ª |
| canal climático primário | fechado: déficit CHIRPS prelim |
| janelas | fechadas em `features/shock_spec.py` |
| climatologia | fechada: expanding, mínimo 10 safras |
| início operacional | fechado: safra 2015/16; `prelim` anterior não existe |
| geografia | implementada: PAM/IBGE point-in-time (D-024) + raster→município (D-027) + município→UF→CONAB as-of (D-028) |
| nível de risco/ciclo ZARC | não é parâmetro primário; só robustez futura pré-fixada |
| temperatura | secundária; limiares fixados, vintage imperfeito declarado |
| progresso semanal da CONAB | descartado do primário; não há ação ativa nem dependência do pipeline |

O `Shock` já pode ser calculado sem voltar às caixas ilustrativas. O próximo passo é usá-lo
nos rodadores H1a/H1b, sujeito à decisão prévia sobre o perímetro do holdout (PT-001 em
`12_PENDENCIAS_TRANSVERSAIS.md`). ZARC, temperatura e outras culturas permanecem robustez
futura deliberada, não pendências desta trilha.
