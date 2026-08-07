# Teses candidatas — Desafio Quant AI 2026

Documento de trabalho (não é o relatório final). 21 teses de dados alternativos,
organizadas por tema (o que cada uma investiga), não por como ou quando eu cheguei nelas.
Critérios usados para filtrar:

1. **Respaldo acadêmico real** — existe paper sério por trás, não só uma anedota de mercado.
2. **Original para o Brasil** — pesquisei se já foi testado aqui; se já foi (mesmo que nos
   EUA seja clássico), a tese perde pontos de "criatividade" no critério do edital.
3. **Dado gratuito e obtível** — qualquer coisa que dependa de scraping frágil, acesso pago
   ou dataset que não existe publicamente foi rebaixada ou descartada.
4. **Alinhado ao perfil do time** — forte em código/dados, sem bagagem de economia. Prioriza
   teses com mecanismo fácil de explicar e trabalho técnico (pipeline, séries temporais,
   NLP) onde vocês têm vantagem.

Ver também `pipeline_e_portfolio.md` (lições dos relatórios de anos anteriores, arquitetura
de pipeline em camadas, ideia de portfólio multi-tese).

---

## 1. Agronegócio, clima e comércio exterior

### 1. Choque climático → ações do agronegócio listado na B3

**Resumo**: usar dados de chuva e temperatura por satélite para descobrir, semanas antes do
resultado sair, se a safra de empresas do agronegócio (como SLC Agrícola) vai ser boa ou
ruim — e comprar ou vender a ação com base nisso antes do mercado perceber.

**Hipótese central**: anomalias de chuva/temperatura numa região produtora, medidas
durante a janela crítica do ciclo da safra (ex: enchimento de grãos da soja), antecipam em
semanas/meses uma surpresa (positiva ou negativa) no resultado trimestral de empresas com
operação concentrada naquela região — e o mercado só precifica isso por completo perto da
divulgação do balanço.

**Racional econômico**: o choque climático afeta produtividade física antes de afetar
qualquer número contábil. Entre o choque e o resultado trimestral que o revela há uma
defasagem de meses — a mesma defasagem que existe entre "a safra quebrou" e "o mercado
formalmente sabe disso". Investidores de varejo (e boa parte dos institucionais menores) não
acompanham dado agrometeorológico regional linha a linha; isso cria a janela de subreação.

**Base acadêmica** (múltiplos papers, não um só):
- Literatura de temperatura/ENSO e retorno de ações agrícolas nos EUA mostra efeito real
  mas de curta duração (~3-6 meses, torna-se estatisticamente indistinguível depois disso) —
  *"The effect of temperature anomaly and macroeconomic fundamentals on agricultural
  commodity futures returns"* (Energy Economics, 2021) e *"The Impact of El Niño-Southern
  Oscillation on U.S. Food and Agricultural Stock Returns"*.
- A literatura mais recente de "weather shocks e retorno de ações" documenta especificamente
  um padrão de **subreação inicial seguida de correção** — exatamente o tipo de ineficiência
  que uma estratégia sistemática tenta capturar.

**Dados (grátis, já confirmados)**:
- **NASA POWER API** (`power.larc.nasa.gov`) — sem restrição de uso, sem conta. Parâmetros
  relevantes: `PRECTOTCORR` (precipitação diária corrigida) e `T2M` (temperatura a 2m),
  histórico diário desde 1981, resolução ~0,5°×0,5° (suficiente para diferenciar
  macrorregiões produtoras como MT vs. BA vs. RS).
- **CONAB** (Companhia Nacional de Abastecimento) — calendário de plantio/colheita por
  estado e produto, e séries de acompanhamento de safra (público, mas em PDF/planilha —
  exige algum trabalho de parsing).
- Preços via `brapi.dev` ou `yfinance`.

**Desenho de sinal (concreto)**:
1. Mapear, por empresa do universo, as regiões (estado/coordenada aproximada) onde ela tem
   operação relevante — via relatório anual/formulário de referência (ver risco abaixo).
2. Para cada região e cada ciclo de safra, calcular o desvio (z-score) da chuva acumulada
   na janela crítica em relação à média histórica de 20-30 anos da mesma janela.
3. Threshold de anomalia (ex: |z| > 1) dispara sinal de over/underweight na empresa exposta,
   mantido até ~1-2 semanas após a divulgação do resultado trimestral que deveria refletir o
   efeito.
4. Complementar isolando o "efeito preço" da commodity (que já é público e precificado) do
   "efeito produtividade local" (que é o que estamos tentando capturar de forma antecipada).

**Universo sugerido e mapeamento aproximado**: SLC Agrícola (SLCE3 — MT/BA/PI, soja/algodão/
milho), BrasilAgro (AGRO3 — múltiplos estados, efeito também via valor da terra arrendada),
São Martinho (SMTO3 — SP, cana), Boa Safra Sementes (SOJA3 — MT), JBS/Marfrig/Minerva
(JBSS3/MRFG3/BEEF3 — efeito mais indireto, via custo de ração/preço do boi, sinal
provavelmente mais fraco que nas agrícolas "puras").

**Riscos específicos deste desenho**:
- *Poucas observações independentes de verdade*: mesmo com dado diário, cada empresa só
  passa por ~1 ciclo de safra relevante por ano — 5 anos de histórico são só 5-10 "eventos"
  de safra independentes, não milhares de linhas de dado. O desenho estatístico do backtest
  precisa contar eventos, não dias, para não parecer um teste "inflado" (isso é exatamente o
  tipo de coisa que o critério de Backtest do edital, 15%, vai cobrar).
- *Look-ahead via revisão de dado*: a CONAB revisa estimativas de safra ao longo do tempo —
  usar sempre a primeira publicação disponível na época, nunca a versão revisada
  retroativamente.
- Mapear "empresa → região" não é automático, exige leitura de relatórios.

**Espaço para GenAI**: extrair de relatórios anuais e fatos relevantes (texto livre em
português) a localização geográfica das operações de cada empresa é um uso concreto e
defensável de IA generativa dentro do próprio pipeline de dados — não só na escrita do
relatório.

**Por que funcionaria especificamente no Brasil (não é só "copiar o paper americano")**
*[Persona: Quant researcher]*
- Cobertura de sell-side (analistas de banco/corretora publicando research) para small/mid
  caps do agro brasileiro é bem mais rala que nos EUA — poucas casas cobrem SLC Agrícola ou
  BrasilAgro de perto, o que significa menos gente processando dado agrometeorológico
  regional profissionalmente e mais espaço para a subreação que a tese explora.
- A base de investidor pessoa física brasileiro cresceu muito desde 2019-2020 (corretoras
  digitais, redução de taxa) — investidor de varejo tende a reagir a *resultado*, não a
  *dado climático antecedente*, o que sustenta a defasagem temporal da tese.
- Geografia agrícola brasileira é mapeável por bioma/estado de forma bem mais discreta que
  o "corn belt" americano (mais difuso) — o que torna o trabalho de "empresa → região"
  mais tratável, não menos.
- Brasil tem **dois ciclos de plantio por ano** em boa parte do Centro-Oeste (safra de
  verão + safrinha de milho) — dá dois eventos por ano em vez de um só como nos EUA,
  parcialmente compensando a limitação de poucas observações independentes.

**Limitações reais** *[Persona: Estatístico/a cético/a]*
- **Diversificação geográfica dilui o sinal**: uma empresa com fazendas em múltiplos
  biomas (ex: BrasilAgro) pode compensar internamente uma quebra regional com uma safra boa
  em outro estado — o que é boa gestão de risco da empresa, mas prejudica exatamente o
  sinal que estamos tentando capturar.
- **Hedge cambial e de commodity**: grandes produtoras protegem receita com contratos
  futuros/NDF — parte do choque físico pode já estar neutralizado contabilmente antes de
  chegar ao resultado trimestral, o que reduz (sem necessariamente zerar) o efeito
  esperado.
- **Exposição concentrada em poucos meses do ano**: o portfólio fica com posição ativa só
  numa fração do tempo, o que precisa ser considerado explicitamente na forma de anualizar
  retorno/Sharpe (não dá pra tratar como se fosse um sinal ativo o ano inteiro).
- **Qualidade do dado climático**: NASA POWER é dado de reanálise (modelado), não estação
  meteorológica real — tem erro de medição, maior em áreas de relevo mais complexo.

**Pipeline específico desta tese** *[Persona: Engenheiro/a de dados]*
1. Ingestão diária de `PRECTOTCORR`/`T2M` do NASA POWER para coordenadas de operação de
   cada empresa (via item de relatório anual — na v1 pode ser mapeamento manual de 6-8
   empresas, não precisa de automação completa).
2. Cálculo de anomalia (z-score) na janela crítica da safra, usando o calendário CONAB por
   estado/produto para definir a janela.
3. Cruzamento com o histórico de *revisões* da CONAB para garantir que estamos usando só a
   informação que estaria disponível na época (nunca a estimativa revisada
   retroativamente).
4. Geração de sinal + integração com preço (a tese do ComexStat, abaixo, detalha o
   cruzamento).
5. Backtest com janela por ciclo de safra (não por dia corrido) — a unidade de teste
   estatístico é o evento de safra, não a linha de dado diário.

### 2. NDVI (índice de vegetação por satélite) → validação cruzada da tese climática

**Resumo**: usar imagem de satélite que mostra "quão verde" está a lavoura para confirmar,
por outro ângulo, o mesmo sinal de choque climático da tese acima — não é uma ideia nova,
é um reforço dela.

**Hipótese**: quedas anômalas de NDVI nas áreas plantadas antecipam surpresa negativa de
resultado agrícola.
**Dado**: MODIS/Sentinel-2 via Google Earth Engine, gratuito, cobre o Brasil inteiro; precisa
de poligonização das fazendas (via CAR, público) — só SLC Agrícola e BrasilAgro divulgam
localização com detalhe suficiente pra isso.
**Minha leitura — não é uma tese nova, é um upgrade da tese climática**: NDVI é literalmente
outra forma de medir o mesmo fenômeno (estresse hídrico na safra) que a tese climática já
cobre com NASA POWER. Faz mais sentido como **camada de robustez/validação cruzada** (chuva
prevê, NDVI confirma o efeito na vegetação antes do embarque) do que como tese separada —
apresentar como duas teses seria redundante pra banca.

**Por que funcionaria especificamente no Brasil** *[Persona: Quant researcher]*
- O CAR (Cadastro Ambiental Rural) é uma exigência legal brasileira que obriga produtores a
  georreferenciar suas propriedades — é uma base de poligonização pronta e pública que não
  tem equivalente tão acessível em muitos outros países agrícolas grandes (nos EUA, o
  Common Land Unit do USDA é mais restrito). Isso barateia exatamente a parte mais cara
  dessa tese em outros contextos.
- Área agrícola brasileira é grande e contígua o suficiente (fazendas de milhares de
  hectares no Centro-Oeste) para que a resolução do MODIS (250m) já seja informativa — não
  precisa necessariamente do Sentinel-2 (10m, mais pesado de processar) para captar o sinal
  agregado por fazenda.

**Limitações reais** *[Persona: Estatístico/a cético/a]*
- **Cobertura de nuvens é assimétrica com o próprio sinal que queremos medir**: NDVI óptico
  não atravessa nuvem. Em anos de excesso de chuva (quando também queremos medir o efeito),
  a cobertura de nuvem aumenta e a disponibilidade de imagem "limpa" cai — justamente no
  cenário em que a tese climática (chuva em excesso) mais precisaria de confirmação visual.
  Anos de seca (menos nuvem) têm cobertura melhor, o que introduz um viés assimétrico de
  disponibilidade de dado entre os dois tipos de choque que a tese tenta capturar.
- **MODIS (250m) vs. Sentinel-2 (10m) é uma escolha real, não trivial**: MODIS revisita mais
  rápido (composto de 16 dias) mas mistura múltiplos talhões numa mesma célula; Sentinel-2 é
  fino o bastante para isolar talhões individuais mas revisita mais devagar e tem arquivo
  bem mais pesado para processar — a escolha errada pode gerar sinal com resolução
  inadequada pro tamanho médio de fazenda do universo escolhido.

**Pipeline específico (como camada dentro da tese climática)** *[Persona: Engenheiro/a de
dados]*
1. Poligonizar as fazendas de SLC Agrícola/BrasilAgro via CAR (shapefile público).
2. Puxar série de NDVI (MODIS/MOD13Q1 como baseline, Sentinel-2 como checagem de robustez
   pontual) recortada pelos polígonos, ao longo da janela crítica de safra já definida.
3. Calcular anomalia de NDVI (z-score vs. média histórica do mesmo talhão/janela) e
   comparar contra a anomalia de chuva/temperatura já calculada — os dois sinais devem
   concordar na maior parte do tempo; divergência sistemática é sinal de erro no pipeline
   ou de mecanismo mal compreendido, e vale investigar antes de confiar em qualquer um dos
   dois isoladamente.
4. Só promover NDVI de "camada de validação" para "sinal com peso próprio" se ele
   adicionar poder preditivo incremental mensurável sobre o sinal climático sozinho (teste
   estatístico explícito, não só concordância visual).

### 3. Volume de exportação (ComexStat) → antecipação de receita de exportadoras

**Resumo**: acompanhar mês a mês quanto minério, celulose ou soja o Brasil está exportando
de verdade, e usar isso para prever se empresas como Vale ou Suzano vão ter receita melhor
ou pior que o esperado — antes do balanço trimestral confirmar.

**Hipótese central**: o volume mensal exportado de um produto (NCM) específico, publicado
pelo MDIC com defasagem de 30-40 dias, antecipa a receita trimestral de empresas
concentradas naquele produto — chegando ao mercado mais rápido que o balanço trimestral
(que sai 45-60 dias depois do fechamento do trimestre).

**Racional econômico / honestidade sobre a base teórica**: diferente da tese climática, não
existe um paper clássico específico ligando dado de comércio exterior a retorno de ação
individual — a base aqui é a lógica bem estabelecida de "nowcasting" com dados de comércio
exterior (usada por bancos centrais para prever PIB antes dos números oficiais), que estamos
traduzindo do nível macro para o nível de receita de uma empresa específica. É a tese com a
base acadêmica mais fraca das duas principais deste bloco — mas o dado é o mais limpo de
toda a lista.

**Dados (grátis, já confirmados)**: API oficial `api-comexstat.mdic.gov.br` — exportação/
importação por NCM (8 dígitos), UF, município, via de transporte, granularidade **mensal**.
NCMs de referência: soja em grão `1201.90.00`, minério de ferro `2601.11`/`2601.12`,
celulose `4703`, carne bovina `0201`/`0202`, carne de frango `0207`.

**Desenho de sinal**: crescimento YoY (ou vs. média móvel de 12 meses) do volume exportado
do NCM relevante, **ajustado pelo preço internacional da commodity** (para isolar o efeito
volume do efeito preço, que já é público) → sinal de receita acima/abaixo do esperado antes
do trimestre fechar.

**Universo sugerido**: Vale (VALE3 — minério, empresa dominante no NCM, sinal deve ser
limpo), Suzano (SUZB3 — celulose), CSN (CSNA3 — aço), além das agro da tese climática (soja/
carne também aparecem no ComexStat, reforçando aquele sinal).

**Risco específico**: nem todo NCM tem uma empresa dominante — minério de ferro funciona bem
porque a Vale concentra a maioria das exportações brasileiras do produto, mas celulose e aço
têm mais players relevantes, o que dilui a limpeza do sinal. Checar concentração de mercado
por NCM antes de comprometer o universo.

**Por que combina bem com a tese climática**: clima antecipa a safra, ComexStat confirma o
embarque já realizado — dá um modelo com lógica em duas etapas (sinal antecedente + sinal
confirmatório), que ajuda bastante no critério de Modelagem (20%).

**Por que funcionaria especificamente no Brasil** *[Persona: Quant researcher]*
- ComexStat sai com defasagem de 30-40 dias — mais rápido que a maioria dos dados de
  comércio exterior de mercados emergentes comparáveis, e claramente mais rápido que o
  balanço trimestral (45-60 dias). Essa velocidade de publicação não é padrão global, é uma
  característica específica do sistema brasileiro (SISCOMEX) que vale explorar.
- Concentração de mercado: minério de ferro é dominado pela Vale (~70%+ das exportações
  brasileiras do produto) — isso é incomum, a maioria dos NCMs de commodity não tem um
  player tão dominante, o que torna esse caso particularmente limpo para sinal
  firm-specific.
- Times de research doméstico usam ComexStat para leitura macro (balança comercial) — não
  encontrei uso sistemático dele como sinal de timing de ação individual, é um "buraco" de
  aplicação, não de dado.

**Limitações reais** *[Persona: Estatístico/a cético/a]*
- Valor FOB declarado nem sempre reflete receita realizada de forma limpa (efeitos de
  câmbio, hedge, preço de transferência entre empresas do mesmo grupo em operações
  verticalizadas de mineração/logística).
- Agregação por NCM pode misturar diferentes graus/qualidades do mesmo produto com preços
  bem diferentes entre si — um crescimento de volume "aparente" pode esconder mudança de mix
  de qualidade, não de quantidade real.
- Embarques são "grumosos" (lumpy): um navio grande atracando no fim do mês pode distorcer
  o dado mensal sem refletir tendência real — precisa de suavização (média móvel) antes de
  gerar sinal.
- Empresas com venda doméstica relevante (ex: CSN vende bastante aço no mercado interno)
  têm parte da receita fora do alcance do sinal — funciona melhor quanto maior a proporção
  exportada da receita total.

**Pipeline específico desta tese** *[Persona: Engenheiro/a de dados]*
1. Ingestão mensal do ComexStat por NCM + UF/município + via de transporte.
2. Checagem de concentração de mercado por NCM (só aceitar como sinal firm-specific quando
   a empresa-alvo detém claramente a maior fatia; caso contrário, tratar como sinal
   setorial).
3. Suavização (média móvel 3 meses) para reduzir o efeito de embarques concentrados.
4. Ajuste pelo preço internacional da commodity (série separada) para isolar o efeito
   volume do efeito preço, que já é público e precificado.
5. Cruzamento com a camada climática: sinal final só dispara quando as duas camadas
   concordam — reduz falso positivo de cada camada isolada.

### 4. AIS + ANTAQ → nowcasting de exportação via rastreamento portuário

**Resumo**: acompanhar quanta carga está de fato sendo carregada nos portos brasileiros (e,
se der certo, rastrear os próprios navios) para saber, antes até do dado oficial de
exportação, que uma empresa como a Vale está embarcando mais ou menos minério do que o
normal.

**Hipótese**: volume de carga atracada/despachada (ANTAQ) e rastreamento de navios (AIS)
antecipa receita de exportadoras antes até do ComexStat mensal sair.
**Paper**: Cerdeiro, Komaromi, Liu & Saeed, *"World Seaborne Trade in Real Time"*, IMF
Working Paper 2020/057 — nowcasting de comércio marítimo via AIS bruto.
**Dado**: ANTAQ (Sistema de Desempenho Portuário) — confirmado, gratuito, granular por
porto/terminal/carga/data. AIS gratuito (AISHub/Global Fishing Watch) — **cobertura
brasileira não confirmada**, maior incerteza deste item.
**Minha leitura — é a versão mais rápida/granular da tese do ComexStat**: mesma lógica,
dado ainda mais antecedente (embarque físico em vez de declaração aduaneira mensal). Testar
a viabilidade do AIS gratuito o quanto antes — se não viabilizar, a tese sobrevive só com
ANTAQ (confirmado e robusto), perdendo o componente de rastreio por navio individual.

**Por que funcionaria especificamente no Brasil** *[Persona: Quant researcher]*
- A infraestrutura portuária de commodities brasileira é excepcionalmente concentrada: Ponta
  da Madeira e Tubarão (Vale, minério), Paranaguá (grãos) e Santos (multi-produto)
  respondem por parcela desproporcional do volume exportado — diferente de sistemas
  portuários mais distribuídos (ex: costa do Golfo americana, com dezenas de portos
  relevantes), aqui um número pequeno de terminais já cobre a maior parte do sinal que
  interessa, o que reduz o escopo de engenharia necessário.
- ANTAQ é dado regulatório obrigatório (mesma lógica institucional da tese do ONS) — a
  transparência não depende de boa vontade comercial do operador portuário.

**Limitações reais** *[Persona: Estatístico/a cético/a]*
- **ANTAQ é autodeclarado pelos operadores portuários**: não é uma verificação
  independente, é o próprio terminal reportando seu movimento — risco de inconsistência de
  metodologia entre operadores diferentes, mesmo dentro do mesmo porto.
- **Atribuição navio → empresa não é trivial mesmo com AIS funcionando**: navios são
  frequentemente afretados (não são propriedade da exportadora), e contratos de afretamento
  mudam — "este navio pertence à Vale" pode estar errado se for na verdade um afretamento de
  curto prazo de uma trading terceira despachando carga da Vale. Precisa de uma camada de
  validação cruzada com o porto/berço de origem (mais confiável) em vez de confiar só na
  identidade do navio.
- **Ainda depende da mesma limitação de concentração de mercado por produto** que a tese do
  ComexStat já tem — funciona melhor onde há operador dominante do terminal.

**Pipeline específico (como camada dentro da tese do ComexStat)** *[Persona: Engenheiro/a de
dados]*
1. Testar viabilidade prática do AIS gratuito para cobertura da costa brasileira
   imediatamente (é a maior incerteza da tese) — se inviável, seguir só com ANTAQ.
2. Ingestão do SDP/ANTAQ por porto/terminal/tipo de carga/data de atracação-desatracação.
3. Mapear terminal → empresa dominante apenas onde a relação é conhecida e estável (Ponta
   da Madeira/Tubarão → Vale é o caso mais limpo); tratar os demais como sinal
   multi-empresa/setorial.
4. Agregar volume por semana/mês e comparar contra o sinal de volume da tese do ComexStat
   como checagem cruzada — divergência sistemática entre "o que atracou" e "o que foi
   declarado" é, em si, informação interessante (pode sinalizar estoque em trânsito ou
   mudança de destino), não só ruído a ser descartado.

### 5. SAR (radar de satélite) → estoque em pátios de minério/combustível

**Resumo**: usar imagem de radar de satélite (que enxerga através de nuvem) para tentar
estimar se o pátio de estoque de minério de uma mineradora está enchendo ou esvaziando — é
a ideia mais difícil tecnicamente de toda a lista.

**Hipótese**: variação no backscatter de radar sobre pátios de minério ou tanques de
combustível antecipa volume de vendas trimestral.
**Paper**: Mukherjee, Panayotov & Shon, *"Eye in the Sky: Private Satellites and Government
Macro Data"*, **Journal of Financial Economics** 141(1), 2021 — mercado de petróleo dos EUA.
**Dado**: Sentinel-1 (SAR), gratuito, funciona com nuvem (relevante no Brasil tropical) —
mas resolução (~10m) **não é suficiente** para a técnica clássica de "sombra de tanque"
usada no paper original (que exige imagem óptica paga, <3m). A versão 100% gratuita é mais
grosseira.
**Minha leitura**: tecnicamente a mais difícil de todo o levantamento (processamento de SAR
tem curva de aprendizado real, mesmo pra time de CS). Só entra se sobrar apetite técnico —
tratar como extensão da tese de NDVI/clima, não como projeto principal.

**Por que funcionaria especificamente no Brasil** *[Persona: Quant researcher]*
- Esta é, na verdade, a única tese do levantamento onde o Brasil tem uma vantagem
  *estrutural* real para SAR especificamente: cobertura de nuvem tropical é um problema
  crônico para sensoriamento óptico aqui (mais que na maior parte dos EUA/Europa), e SAR
  atravessa nuvem — o caso de uso "por que usar radar em vez de imagem óptica" é mais forte
  no Brasil do que seria em climas temperados, mesmo que a resolução gratuita ainda seja uma
  limitação real (abaixo).

**Limitações reais** *[Persona: Estatístico/a cético/a]*
- **Resolução (10m) não substitui a técnica original do paper** (sombra de tanque, que
  exige <3m, imagem paga) — a versão gratuita mede variação de área/volume aparente de
  pátio a céu aberto (minério), não volume de tanque fechado (petróleo) com a mesma
  precisão.
- **Processamento de SAR tem etapas específicas que a tese climática/NDVI não exige**:
  correção de speckle (ruído característico de radar), calibração radiométrica, e
  normalização por ângulo de incidência (a mesma área pode retornar backscatter diferente
  dependendo do ângulo da passagem do satélite) — sem isso, variação no sinal pode ser
  artefato de geometria de aquisição, não mudança real no pátio.
- **Sem dado de referência para calibrar durante a fase de aprendizado**: ao contrário da
  tese climática (onde dá pra checar contra safra/resultado divulgado), não há uma forma
  fácil de saber se "o pátio está X% maior" está correto sem alguma verificação externa
  (ex: comparar contra volume de embarque já conhecido via ANTAQ/ComexStat do mesmo
  período) — a validação precisa vir de outra tese, não de si mesma.

**Pipeline específico** *[Persona: Engenheiro/a de dados]*
1. Ingestão de produtos Sentinel-1 GRD via Copernicus Data Space Ecosystem, para as
   coordenadas dos pátios de interesse (Ponta da Madeira/Tubarão como ponto de partida, por
   já serem bem documentados).
2. Pré-processamento: calibração radiométrica, filtro de speckle (ex: Lee filter), correção
   geométrica.
3. Definição de polígono de pátio e extração de estatística de backscatter (média, desvio)
   por passagem do satélite.
4. Validação inicial obrigatória: comparar a série de backscatter contra o volume de
   embarque já conhecido (ANTAQ/ComexStat) do mesmo período — só tratar como sinal
   antecedente de verdade depois de confirmar que o proxy de fato acompanha uma métrica
   conhecida.

### 6. DETER/PRODES (desmatamento) → risco regulatório para frigoríficos

**Resumo**: monitorar alertas de desmatamento perto das regiões que abastecem frigoríficos
como JBS e Marfrig, e usar isso como sinal de risco de multa ou embargo — especialmente
perto dos prazos em que a Europa vai proibir importar carne ligada a desmatamento.

**Hipótese**: alertas de desmatamento em municípios-polo de fornecimento antecipam risco de
embargo/barreira comercial para frigoríficos e agro listados.
**Paper**: Guidolin & Pedio, *"The Pricing of Biodiversity Risk in Commodity Markets"*,
**Review of Finance** 30(1), 2025 — prêmio de 20-60 p.b./mês em commodities com maior
exposição a risco de biodiversidade.
**Dado**: DETER/PRODES (INPE, TerraBrasilis) — confirmado, gratuito, quase tempo real.
**Minha leitura — novidade mais fraca do lote**: a Chain Reaction Research já publicou
mapeamento de exposição de JBS/Marfrig/Minerva a desmatamento via DETER — não como
estratégia de trading sistemática, mas o "achado" de que existe uma relação já é conhecido
publicamente. A contribuição de vocês seria sistematizar isso quantitativamente, não
descobrir a relação — precisa deixar isso claro pra banca não achar que é plágio de ideia.
Também: rastrear a cadeia de fornecimento até a fazenda de origem é notoriamente difícil
(é o mesmo problema que a própria Chain Reaction Research enfrenta) — plausivelmente precisa
simplificar para desmatamento agregado por bioma/UF em vez de fazenda individual.

**Por que funcionaria especificamente no Brasil** *[Persona: Quant researcher]*
- Diferente das outras teses "ESG-adjacent" (que costumam ser vagas sobre *quando* o risco
  vira preço), esta tem um **calendário regulatório concreto e público** para ancorar o
  sinal: a EUDR (regulação europeia antidesmatamento) tem datas de entrada em vigor e prazos
  de compliance conhecidos com antecedência — dá para desenhar o sinal em torno de eventos
  datados (proximidade de prazo de compliance, cliente europeu específico em risco), em vez
  de um score contínuo vago de "risco ESG". Isso ataca diretamente a fraqueza que eu
  apontava antes ("gera decisão de investimento pouco clara").
- Brasil concentra a maior exposição do mundo a esse risco regulatório específico (maior
  exportador de carne bovina e soja para clientes sensíveis a desmatamento) — o risco é
  estruturalmente mais relevante aqui do que seria adaptar a mesma tese para outro país.

**Limitações reais, aprofundando além do que já foi dito** *[Persona: Estatístico/a
cético/a]*
- Alertas do DETER incluem desmatamento **legal** (dentro de área de reserva legal
  autorizada) misturado com **ilegal** — sem cruzar com a lista de embargos do IBAMA (também
  pública) para filtrar, o sinal bruto tem ruído considerável vindo de atividade
  regulatoriamente permitida.
- **Descompasso de horizonte temporal**: o risco reputacional/regulatório se materializa em
  anos (boicote, perda de contrato, divestimento), mas um sinal de trading precisa de uma
  janela mais curta para ser testável num backtest de poucas semanas de projeto — o desenho
  do sinal precisa ancorar em eventos pontuais (embargo anunciado, prazo de compliance da
  EUDR se aproximando) em vez de tentar capturar o risco reputacional de forma contínua e
  difusa.

**Pipeline específico** *[Persona: Engenheiro/a de dados]*
1. Ingestão de alertas DETER via TerraBrasilis, filtrados geograficamente por bioma/UF de
   operação conhecida das empresas-alvo.
2. Cruzamento com a lista pública de embargos do IBAMA para separar desmatamento
   provavelmente ilegal (maior risco regulatório) do legal.
3. Construção de um índice mensal de intensidade de alerta por região de fornecimento.
4. Sinal ancorado em eventos: janelas ao redor de datas conhecidas de prazo de compliance
   EUDR ou anúncios de embargo, não um score contínuo — testar retorno da empresa nessas
   janelas específicas primeiro (mais fácil de validar) antes de tentar um sinal contínuo.

---

## 2. Atividade econômica regional em alta frequência

### 7. Consumo regional de energia elétrica (ONS) → atividade industrial/varejo

**Resumo**: medir se o consumo de energia elétrica de uma região do Brasil está subindo ou
caindo mais que o normal — como um termômetro da atividade das fábricas por lá — e usar
isso para decidir se vale apostar num grupo de ações industriais daquela região.

**Hipótese central**: uma queda/alta anômala na carga de energia elétrica verificada num
submercado regional do sistema elétrico antecede queda/alta na atividade industrial daquela
região, antes de aparecer em indicadores oficiais de produção (que saem com lag de 1-2
meses).

**Base acadêmica**: literatura de economia de energia sobre consumo elétrico industrial como
proxy de PIB/produção de curto prazo (Payne, *Energy Policy*, 2010, e a linha de pesquisa de
cointegração energia-PIB que segue dele). Uso de eletricidade como indicador de altíssima
frequência para nowcasting é prática real de bancos centrais (ex: BCE, Banco de España usam
dados de consumo elétrico para estimar atividade antes dos números oficiais saírem).

**Dados (grátis, confirmados com mais detalhe agora)**: `dados.ons.org.br` — API de Carga de
Energia Verificada, `apicarga.ons.org.br/prd/cargaverificada`, parâmetros `dat_inicio`,
`dat_fim`, `cod_areacarga`. Granularidade **semi-horária** (48 pontos/dia), sem necessidade
de conta. O sistema elétrico brasileiro é dividido nos 4 submercados padrão (Norte,
Nordeste, Sul, Sudeste/Centro-Oeste) — os códigos exatos de cada `cod_areacarga` não vieram
nas páginas que consultei; é um primeiro passo de ~10 minutos consultar o dicionário de
dados via API/Swagger antes de começar a implementação, não um risco que muda a viabilidade
da tese.

**Desenho de sinal**: anomalia semanal de carga verificada vs. média móvel sazonal (ajustada
por dia da semana e estação do ano) por submercado → proxy de atividade industrial/comercial
regional → sinal de timing para uma cesta setorial (ex: industriais concentrados no
Sudeste/Sul) ou mesmo para o Ibovespa amplo.

**Risco específico**: os 4 submercados são grandes demais para isolar uma única empresa —
Sudeste/Centro-Oeste sozinho concentra a maior parte do PIB industrial do país. Funciona
melhor como sinal de **cesta setorial ou índice** do que como stock-picking fino, o que é
uma diferença importante em relação às teses de clima e ComexStat (essas sim, mais fáceis de
amarrar a uma ação específica).

**Densidade de observações**: a granularidade semi-horária dá um volume de dado bem maior
que a tese climática, ainda que o "evento" relevante (anomalia semanal) limite as
observações efetivamente independentes.

**Por que funcionaria especificamente no Brasil** *[Persona: Quant researcher]*
- O Sistema Interligado Nacional (SIN) é um dos maiores sistemas elétricos totalmente
  interconectados do mundo, e o mix brasileiro é fortemente hidrelétrico — isso torna
  "carga verificada" (demanda) um sinal relativamente limpo de atividade, sem o ruído de
  despacho que sistemas mais fragmentados (múltiplas distribuidoras independentes, como em
  parte dos EUA) costumam ter.
- Publicação é obrigação regulatória do ONS, não decisão comercial — diferente de vários
  países onde o operador de rede é privado e o dado é proprietário, aqui a transparência é
  estrutural, o que é uma vantagem institucional específica do Brasil para esse tipo de
  tese, não um acaso.
- Bancos centrais europeus (BCE, Banco de España) já usam consumo elétrico para nowcasting
  de atividade — a lógica é validada internacionalmente, só não encontrei aplicação dela a
  ações especificamente, nem no Brasil nem fora.

**Limitações reais** *[Persona: Estatístico/a cético/a]*
- **Confusão com o próprio sinal climático**: temperatura afeta demanda de energia
  (ar-condicionado/aquecimento) *e* é a mesma variável usada na tese climática — precisa
  desazonalizar a carga por temperatura antes de interpretar a anomalia residual como
  "atividade", senão as duas teses ficam contaminando uma à outra em vez de se
  complementarem.
- **Autoprodução industrial**: grandes industriais (siderúrgicas, papel e celulose) muitas
  vezes têm cogeração própria — a carga "visível" na rede subestima a produção real desses
  setores justamente nas empresas que mais nos interessariam isolar. É um ponto cego real,
  não hipotético.
- **Granularidade regional é grossa demais para stock-picking**: os 4 submercados cobrem
  regiões inteiras — essa tese precisa ser vendida honestamente como sinal de cesta/índice,
  nunca como se pudesse isolar uma ação específica.

**Pipeline específico desta tese** *[Persona: Engenheiro/a de dados]*
1. Ingestão semi-horária da carga verificada por submercado, agregada para diário/semanal.
2. Desazonalização por dia da semana, estação do ano, **e temperatura** (reusando a série
   de `T2M` da tese climática — ponto de reuso entre teses que reforça a arquitetura em
   camadas).
3. Anomalia (z-score) do resíduo após desazonalização.
4. Mapeamento para uma cesta setorial montada manualmente (não uma ação isolada).
5. Sinal de timing para a cesta ou para o Ibovespa amplo, com posição proporcional à
   magnitude da anomalia.

### 8. Volume de transações PIX (Banco Central) → timing de consumo/varejo

**Resumo**: usar o volume de transações via Pix como um indicador de quanto as pessoas
estão gastando no Brasil, tentando antecipar se o consumo vai bem ou mal antes dos dados
oficiais saírem — mas o dado disponível hoje é mais fraco do que gostaríamos, então esta é
uma tese de reserva, não a principal.

**Atualização importante depois de verificar a API**: confirmei que o recurso principal
("Estatísticas de Transações Pix") é **mensal e nacional/agregado** — não diário, e sem
segmentação clara por setor ou finalidade P2P/P2B na documentação que consultei. Isso é pior
do que eu esperava quando propus essa tese: PIX existe desde novembro/2020, então mensal
agregado dá uma janela de só ~60 observações — pouco para um backtest que a banca não veja
como "garimpado" (o edital pune explicitamente "escolhas oportunistas" no critério de
Backtest).

**Achado que pode reabilitar a tese, ainda não verificado**: o portal do BCB também lista um
recurso separado chamado **"Transações Pix por Município" (JSON)**, distinto do agregado
nacional. Não consegui abrir o conteúdo exato desse recurso na varredura que fiz — se ele de
fato trouxer granularidade municipal (mesmo que só mensal), a tese muda de figura: dá para
construir um sinal **regional** de consumo, no mesmo espírito da tese do ONS, mapeando
municípios com concentração de lojas/operações de uma varejista específica. Vale ~15 minutos
de verificação antes de decidir entre manter ou descartar essa tese.

**Base acadêmica**: linha de pesquisa bem estabelecida nos EUA de "nowcasting" de consumo
com dados de pagamento em altíssima frequência (Opportunity Insights / Chetty et al., usando
dados de cartão de crédito — ganhou muita tração desde a pandemia). A analogia com PIX é
natural mas ainda não foi feita, até onde encontrei, com dado brasileiro.

**Novidade no Brasil**: continua sendo o ponto mais forte desta tese — PIX é exclusivo do
Brasil, sem equivalente direto nos EUA para "copiar 1:1", o que ajuda no critério de
criatividade (20%). Mas novidade sozinha não compensa uma série de ~60 pontos mensais.

**Recomendação**: não priorizar como tese principal; só reconsiderar se o recurso municipal
confirmar granularidade regional de fato.

**Por que funcionaria especificamente no Brasil** *[Persona: Quant researcher]*
- O Pix cresceu tão rápido desde 2020 que hoje é o meio de pagamento mais usado no dia a dia
  do brasileiro, à frente até de cartão de débito — diferente de outros países onde
  pagamento instantâneo ainda é nicho (ex: FedNow nos EUA, recente e pouco adotado), aqui o
  agregado nacional já reflete boa parte do consumo total, não uma fatia pequena e
  enviesada da população.
- Não existe equivalente direto nos EUA para "copiar 1:1" — é dado genuinamente doméstico,
  sem paper americano prévio para comparar.

**Limitações reais** *[Persona: Estatístico/a cético/a]*
- PIX mistura consumo de varejo com transferências pessoa-a-pessoa sem relação nenhuma com
  atividade econômica (aluguel, empréstimo entre amigos, divisão de conta) — sem uma forma
  pública de segmentar isso, é um problema de "pureza de sinal" que persiste mesmo que a
  granularidade geográfica melhore. Não é só um problema de resolução de dado, é um problema
  de composição do que está sendo medido.
- Janela histórica curta (Pix existe desde novembro/2020) limita bastante o número de
  observações independentes disponíveis, mesmo se a granularidade mensal/nacional
  melhorasse — um teto estrutural que nenhum ajuste de pipeline resolve sozinho.

**Pipeline específico** *[Persona: Engenheiro/a de dados]*
1. Primeiro passo obrigatório: verificar o conteúdo real do recurso "Transações Pix por
   Município" — se ele não existir com a granularidade esperada, encerrar a investigação
   dessa tese aqui, antes de investir mais tempo.
2. Se só o agregado nacional estiver disponível: tratar como sinal de **timing de índice**
   (ex: cesta de consumo/varejo do Ibovespa), nunca como stock-picking — construir
   crescimento YoY do volume Pix como feature de nowcasting de consumo agregado.
3. Se o recorte municipal se confirmar: replicar a lógica de mapeamento região→empresa já
   usada nas teses de energia (ONS) e luz noturna, mirando varejistas com presença regional
   concentrada.
4. Em qualquer cenário, tratar qualquer resultado de backtest com cautela estatística extra,
   dado o pequeno número de observações independentes disponível.

### 9. Luz noturna (VIIRS) → atividade econômica regional

**Resumo**: medir a quantidade de luz artificial vista do espaço à noite numa região
específica, como um jeito indireto de saber se o comércio e a construção por lá estão
aquecidos — mas essa ideia se sobrepõe bastante com as duas anteriores (energia e Pix).

**Hipótese**: variação de luminosidade noturna por polígono geográfico antecipa surpresa de
resultado de empresas com exposição regional concentrada (varejo/incorporadoras regionais).
**Papers**: Henderson, Storeygard & Weil, *"Measuring Economic Growth from Outer Space"*,
**American Economic Review** 102(2), 2012 (fundador da linha); Chen & Nordhaus,
*"VIIRS Nighttime Lights..."*, **Remote Sensing**, 2019.
**Dado**: NASA Black Marble (VIIRS), gratuito, diário, desde 2012, via Earthdata/Earth
Engine. Já existem estudos brasileiros ligando luz noturna a PIB municipal (não a ações).
**Minha leitura — risco real de redundância**: é a terceira variação de "proxy de atividade
econômica regional em alta frequência" ao lado das duas teses acima (energia e Pix). Só vale
como tese autônoma se o foco for varejo/construção regional especificamente (onde as outras
duas são mais fracas, por serem nacionais/setoriais demais) — senão, uma banca vai perguntar
"por que as três?".

**Por que funcionaria especificamente no Brasil** *[Persona: Quant researcher]*
- Já existe precedente acadêmico doméstico (estudos ligando luz noturna a PIB municipal no
  Vale do Paraíba/SP e no RS, via INPE/OBT) — reduz o risco de "isso não funciona na
  geografia/atmosfera brasileira", diferente das outras teses de satélite da lista, que
  estão extrapolando de contexto totalmente estrangeiro.
- Padrão de varejo regional brasileiro é mais concentrado em polos urbanos bem definidos
  (ex: capitais nordestinas para o Grupo Mateus) do que o varejo americano mais disperso em
  subúrbios de baixa densidade — mais fácil desenhar um polígono que realmente captura só a
  operação da empresa-alvo.

**Limitações reais** *[Persona: Estatístico/a cético/a]*
- **Redundância conceitual com energia e Pix continua sendo o problema central**, não
  resolvido por aprofundar a tese em si — é uma questão de desenho de portfólio (quais das
  três entram, e por quê), não de qualidade técnica da luz noturna isoladamente.
- **"Blooming"/dispersão de luz**: luz artificial "vaza" para além da fonte real no sensor
  VIIRS, especialmente em áreas urbanas densas — exatamente onde queremos a granularidade
  mais fina (ex: isolar uma loja específica de um shopping) é onde o efeito de contaminação
  entre polígonos vizinhos é mais forte. Precisa de correção específica (produtos
  "stray-light corrected"), não é plug-and-play.
- Composto mensal do VIIRS sofre interferência de luar e nuvem residual — precisa filtrar
  antes de interpretar variação mês a mês como mudança real de atividade.

**Pipeline específico (só se decidirem por ela apesar da redundância)**
*[Persona: Engenheiro/a de dados]*
1. Definir polígonos ao redor da operação da empresa-alvo (ex: raio ao redor de lojas do
   Grupo Mateus).
2. Puxar composto mensal VIIRS "stray-light corrected" via Earth Engine, filtrando períodos
   de lua cheia/nuvem residual.
3. Calcular anomalia de luminosidade por polígono vs. baseline histórico do mesmo período.
4. **Teste obrigatório de valor incremental**: comparar o poder preditivo da luz noturna
   contra o das outras duas teses no mesmo período/região — só justificar incluir as três se
   cada uma agregar informação que as outras não capturam (não basta todas "fazerem
   sentido" isoladamente).

---

## 3. Crédito e sistema financeiro

### 10. SCR (crédito bancário) → crash risk em ações de bancos

**Resumo**: acompanhar, com dado do Banco Central, o quanto os bancos brasileiros estão
emprestando dinheiro — quando um banco cresce a carteira de crédito rápido demais, isso
costuma ser sinal de problema chegando, não de sucesso, e a ação desse banco tende a
performar pior depois.

**Hipótese**: bancos com crescimento anormal de carteira de crédito têm retorno médio menor
e maior risco de cauda nos 1-3 anos seguintes — o oposto do que a teoria de risco
convencional preveria.
**Paper**: Baron & Xiong, *"Credit Expansion and Neglected Crash Risk"*, **Quarterly
Journal of Economics** 132(2), 2017 — 20 países, 1920-2012, retorno excedente de −37% em 3
anos no percentil 95 de expansão de crédito.
**Dado**: SCR.data (Banco Central), mensal, por segmento de instituição/modalidade/UF/CNAE,
gratuito.
**Universo**: os ~10-15 bancos listados na B3 (Itaú, Bradesco, BB, Santander BR, BTG,
Inter, Banrisul, ABC Brasil, Pan, Daycoval).
**Minha leitura**: universo pequeno é a limitação real — poucos bancos listados reduz poder
de teste em corte transversal, empurra pra análise de série temporal/painel curto.

**Por que funcionaria especificamente no Brasil** *[Persona: Quant researcher]*
- O sistema bancário brasileiro é altamente concentrado (5-6 bancos dominam a maior parte
  do crédito do país) — diferente dos EUA, onde milhares de bancos regionais/community banks
  tornam o crescimento agregado de crédito mais ruidoso, aqui poucos nomes carregam a maior
  parte da atividade, o que facilita isolar o sinal por instituição em vez de precisar de um
  painel enorme.
- O SCR cobre 100% do sistema financeiro regulado, sem amostragem — é um censo, não uma
  pesquisa amostral, o que dá uma qualidade de dado rara para um mercado emergente.

**Limitações reais** *[Persona: Estatístico/a cético/a]*
- Mesmo com o SCR cobrindo todo o sistema, só ~10-15 bancos têm ação listada na B3 — poder
  estatístico limitado em corte transversal, o desenho precisa se apoiar mais em série
  temporal.
- **Bancos públicos (Banco do Brasil, Banrisul) têm mandato que foge do apetite de risco
  puramente comercial** — podem expandir crédito por política pública (ex: crédito rural,
  financiamento habitacional em momento de estímulo) mesmo sem o padrão de afrouxamento de
  risco que o paper original mediu em bancos majoritariamente privados. Precisa tratar
  esses casos separadamente, não misturar no mesmo teste.
- Separar "crescimento de crédito bom" (expansão orgânica com a economia) de "crescimento
  de crédito ruim" (afrouxamento de padrão de concessão) exige normalizar pelo crescimento
  do crédito agregado do sistema — não é automático comparar bancos brutos entre si.

**Pipeline específico** *[Persona: Engenheiro/a de dados]*
1. Ingestão mensal do SCR.data por instituição financeira, agregando carteira total de
   crédito por banco.
2. Cálculo da taxa de crescimento YoY da carteira de cada banco, normalizada pelo
   crescimento do crédito agregado do sistema (para isolar crescimento "anormal"
   específico do banco).
3. Marcar separadamente os bancos públicos na análise, dado o viés potencial de mandato.
4. Backtest: ranking dos bancos por percentil de crescimento anormal de crédito,
   underweight nos que crescem mais rápido, medindo retorno em janelas de 1-3 anos como no
   paper original.

### 11. SCR setorial → estresse em empresas não-financeiras (via inadimplência do setor)

**Resumo**: usar o mesmo dado de empréstimos bancários da tese acima, mas olhando por setor
da economia (não por banco), para ver se a inadimplência de um setor — tipo construção
civil — avisa com antecedência que as empresas não-financeiras desse setor vão mal.

**Hipótese**: deterioração de inadimplência agregada por setor/UF no SCR antecipa
revisão negativa de resultado de empresas não-financeiras daquele setor.
**Paper**: Chava, Gallmeyer & Park, *"Credit Conditions and Stock Return Predictability"*,
**Journal of Monetary Economics** 74, 2015 — usa a *survey* qualitativa do Fed (SLOOS); a
adaptação brasileira troca isso por um **registro administrativo quantitativo muito mais
granular** (o SCR não tem equivalente de abertura pública nos EUA) — isso é upgrade de
qualidade de dado sobre a ideia original, não só tradução geográfica.
**Dado**: mesmo SCR.data da tese acima, mas aqui aplicado como sinal setorial para empresas
não-financeiras, não como sinal de crash risk bancário.
**Minha leitura — combina naturalmente com a tese de crédito bancário acima**: são duas
perguntas de pesquisa diferentes sobre a mesma fonte de dado (uma sobre o banco, outra sobre
o setor tomador) — dá pra apresentar como uma tese "SCR" só, com duas aplicações, em vez de
duas teses separadas competindo por atenção.

**Por que funcionaria especificamente no Brasil** *[Persona: Quant researcher]*
- O SCR existe porque a regulação bancária brasileira exige que toda instituição financeira
  reporte operações de crédito ao Banco Central de forma centralizada — é uma característica
  estrutural da supervisão bancária brasileira (não universal: muitos países mantêm
  registros de crédito confidenciais mesmo para fins de supervisão, sem abertura pública
  agregada). A adaptação de Chava-Gallmeyer-Park já é, portanto, uma melhoria de qualidade
  de dado sobre o paper original (registro administrativo vs. survey qualitativa), não só
  uma tradução geográfica — vale enfatizar isso na apresentação.

**Limitações reais** *[Persona: Estatístico/a cético/a]*
- **CNAE é uma categoria ampla demais em muitos casos**: "Construção de Edifícios" mistura
  construtora de alto padrão com construtora popular, com perfis de risco e ciclo bem
  diferentes — o sinal setorial pode estar diluindo informação relevante ao agregar
  demais.
- **Causalidade reversa é uma preocupação real, não hipotética**: bancos podem apertar
  crédito para um setor *porque já perceberam* deterioração por outros canais (conversas com
  clientes, notícias) — nesse caso, o SCR não estaria "antecipando" estresse, estaria
  *refletindo* algo que o mercado já saberia por outra via. Correlação entre inadimplência
  setorial e retorno futuro não distingue as duas histórias — precisa de um teste de
  causalidade de Granger (no espírito do que o KernelNet, um dos exemplos de anos
  anteriores, fez para validar suas relações causais) antes de tratar isso como sinal
  genuinamente antecedente.
- Defasagem de publicação de ~30-60 dias reduz, mas não elimina, a vantagem de timing.

**Pipeline específico** *[Persona: Engenheiro/a de dados]*
1. Ingestão mensal do SCR.data por CNAE + UF, construindo taxa de inadimplência agregada por
   setor.
2. Teste de causalidade de Granger entre a série de inadimplência setorial e o retorno das
   empresas do setor (não só correlação contemporânea) — condição necessária antes de
   aceitar o sinal como "antecedente" e não "reflexo".
3. Se a causalidade se sustentar: sinal de underweight em cesta setorial quando
   inadimplência sobe de forma anômala, cruzado com a tese de crédito bancário como
   checagem — os dois sinais deveriam se mover de forma coerente, já que vêm da mesma fonte
   de dado subjacente.

---

## 4. Texto, disclosure e comportamento corporativo

### 12. Similaridade textual entre empresas (Hoberg-Phillips / TNIC) via CVM
*(era a #20 do docx antigo — a que eu mais gostei de lá)*

**Resumo**: usar um modelo de linguagem para ler a descrição de produtos que cada empresa
da bolsa é obrigada a publicar, e descobrir quais empresas estão ficando parecidas demais
(ou seja, virando concorrentes diretas) antes que isso apareça nos resultados — porque
concorrência mais forte tende a espremer o lucro de ambas.

**Hipótese central**: se a descrição de produtos/serviços de duas empresas, medida por
similaridade textual (não pela classificação setorial oficial, que é engessada), fica mais
parecida ano a ano, elas estão entrando em rota de concorrência real — um sinal antecedente
de possível compressão de margem para ambas, antes do mercado precificar isso via
classificação setorial tradicional.

**Base acadêmica**: Hoberg & Phillips, *"Text-Based Network Industries and Endogenous
Product Differentiation"*, Journal of Political Economy, 2016 — metodologia consolidada
(TNIC), com base de dados oficial mantida até hoje em Dartmouth, e uma atualização recente
(2025, Journal of Finance) usando embeddings tipo Doc2Vec em vez do TF-IDF original. **A
metodologia já foi adaptada para outros mercados** — encontrei aplicação a empresas chinesas
(usando o SWS Ind como benchmark de comparação) — o que reduz o risco de "isso só funciona
com 10-K americano"; ainda assim, não achei nenhuma aplicação a documentos brasileiros
especificamente, então o ineditismo local se mantém. Os autores originais também
disponibilizam **código Python de replicação** e um ano de dado subjacente — isso reduz um
pouco o risco técnico, porque dá um esqueleto pra adaptar em vez de implementar do zero só a
partir da descrição do paper.

**Dados (grátis, confirmados)**: `dados.cvm.gov.br` — Formulário de Referência das
companhias abertas, especificamente a seção "Descrição das Atividades do Emissor e
Principais Produtos e Serviços Comercializados" (itens 7.1-7.2), texto livre em português.

**Desenho de sinal (concreto)**:
1. Extrair a seção de descrição de produtos de cada empresa do universo, por ano.
2. Gerar representação vetorial do texto — TF-IDF clássico (fiel ao paper original) ou
   embeddings de linguagem mais modernos (abre um gancho natural de uso de GenAI).
3. Calcular similaridade de cosseno par-a-par entre todas as empresas do universo.
4. Construir a rede: cada empresa conectada às N mais similares; "pressão competitiva" =
   grau/densidade da vizinhança de cada empresa na rede.
5. Sinal: aumento de similaridade ano a ano entre um par de empresas → risco de compressão
   de margem para ambas (ex: posição relativa entre o par, ou underweight nas empresas mais
   "cercadas" da rede).

**Universo sugerido**: setores com convergência de produto conhecida tendem a gerar rede
mais interessante — varejo (Magazine Luiza, Via, Renner) ou bancos/fintechs.

**Por que é a mais arriscada tecnicamente**: é NLP real em português do zero, não só séries
numéricas — mais trabalhosa que as demais. Boa candidata a **combinar depois** com uma das
teses de clima, ComexStat ou energia, ou a virar o projeto principal se o time preferir o
desafio técnico.

**Risco adicional a checar**: a qualidade/detalhamento da seção de produtos varia bastante
entre Formulários de Referência de empresas diferentes — vale olhar uma amostra de 5-10
empresas antes de comprometer o desenho todo.

**Espaço para GenAI**: o mais orgânico de toda a lista — processar texto com modelo de
linguagem é literalmente o núcleo do modelo quantitativo, não um acessório. Forte para o
critério de 15% do edital.

**Por que funcionaria especificamente no Brasil** *[Persona: Quant researcher]*
- A classificação setorial oficial da B3 (Setor/Subsetor Bovespa) é grossa e atualizada com
  pouca frequência — é exatamente o tipo de limitação que motivou Hoberg-Phillips nos EUA
  (GICS/SIC engessados), só que num mercado menor, onde as fronteiras setoriais tendem a
  ser ainda mais borradas (Magazine Luiza é varejo ou fintech? Vale é só mineração ou também
  logística/energia?).
- O Brasil teve, na vida real, convergência de produto bem documentada e visível no
  varejo/fintech nos últimos anos (bancos virando varejistas de produtos financeiros,
  varejistas lançando braço bancário) — dá um caso concreto de validação: se a rede
  construída não capturar essa convergência conhecida, é sinal de que o pipeline tem
  problema antes mesmo de confiar no resultado em casos menos óbvios.

**Limitações reais** *[Persona: Estatístico/a cético/a]*
- **Viés de tamanho de texto**: uma empresa que escreve uma seção de produtos mais curta ou
  mais genérica vai parecer "menos parecida" com todo mundo só por escrever menos — um
  artefato do texto, não da realidade econômica. Precisa normalizar por tamanho do
  documento ou, no mínimo, checar a correlação entre tamanho de texto e centralidade na
  rede como diagnóstico antes de confiar no resultado.
- **Frequência anual é lenta**: o Formulário de Referência é atualizado uma vez por ano —
  poucos pontos no tempo para validar se "ficar mais parecido" realmente antecede
  compressão de margem, e com que defasagem. Isso exige um estudo de evento à parte (não é
  automático) para calibrar quanto tempo depois da convergência textual a margem de fato
  reage, se reagir.
- **Boilerplate jurídico**: seções de formulário de referência costumam ter blocos de
  linguagem regulatória padronizada que se repetem entre empresas — se não for removido
  antes de calcular similaridade, infla artificialmente a similaridade entre empresas que
  não têm nada a ver uma com a outra.

**Pipeline específico desta tese** *[Persona: Engenheiro/a de dados]*
1. Extração da seção 7.1-7.2 ("Descrição das Atividades do Emissor e Principais Produtos e
   Serviços") de cada Formulário de Referência, por empresa/ano.
2. Limpeza removendo boilerplate jurídico comum a todos os documentos (checar isso é um
   passo de validação, não só de limpeza).
3. Vetorização (TF-IDF, fiel ao paper original, como baseline) + comparação com embeddings
   modernos como checagem de robustez.
4. Similaridade de cosseno par a par → rede → validação contra o caso conhecido
   varejo/fintech antes de generalizar para o resto do universo.
5. Tracking de delta de similaridade ano a ano por empresa → sinal.

### 13. Timing de submissão de documentos à CVM ("insônia corporativa" — pivotada)
*(era a #2 do docx antigo, trocando SEC EDGAR por CVM)*

**Resumo**: olhar o dia da semana em que uma empresa entrega seu resultado à CVM e quantas
outras empresas entregam no mesmo dia — a ideia é que quem "esconde" o resultado
entregando numa sexta-feira ou junto de muitas outras empresas tende a ter notícia ruim
pra contar.

**Atualização importante depois de verificar o dicionário de dados**: confirmei, lendo o
dicionário oficial (`meta_ipe_cia_aberta.txt`), que o dataset público de documentos da CVM
(sistema IPE) só expõe **`Data_Entrega`** (data, formato AAAA-MM-DD) e `Protocolo_Entrega`
(um ID de protocolo) — **não há campo de hora exata de submissão**. A ideia original
("horário atípico de madrugada") não é construível com esse dataset público. Não vou fingir
que dá.

**Pivô que a mantém viva, com base melhor do que a original**: durante a checagem, encontrei
um paper mais preciso e mais adequado ao dado que realmente temos —
deHaan, Shevlin & Thornock, *"Market (In)Attention and the Strategic Scheduling and Timing
of Earnings Announcements"*, Journal of Accounting and Economics, 2015. O mecanismo real
desse paper não é "hora do dia", e sim: (a) divulgar às **sextas-feiras**, (b) divulgar em
dias com **muitas outras empresas divulgando ao mesmo tempo** (dia de baixa atenção,
"escondido no meio da multidão"), e (c) divulgar com **pouco aviso prévio**. Os autores
mostram que gestores usam essas três táticas para "esconder" más notícias — e o mercado
reage de forma consistente com isso.

**Por que isso funciona com o dado que a CVM realmente disponibiliza**: as três táticas do
paper são construíveis só com `Data_Entrega`:
- dia da semana da entrega (Friday effect);
- quantas outras companhias entregaram documento (`Categoria` = DFP/ITR) na mesma data
  (proxy de "dia de baixa atenção" por volume de divulgações simultâneas);
- comparação entre `Data_Entrega` e o prazo regulatório limite, ou contra o padrão histórico
  da própria empresa (proxy de "entrega de última hora").

**Nova hipótese**: empresas que entregam DFP/ITR numa sexta-feira, ou num dia de alto volume
de entregas simultâneas na CVM, ou no último dia possível do prazo regulatório, têm maior
probabilidade de reportar resultado abaixo do esperado.

**Dados**: sistema IPE (`dados.cvm.gov.br/dataset/cia_aberta-doc-ipe`) para a data de
entrega, cruzado com os datasets estruturados de DFP/ITR (também no portal CVM) para os
números financeiros em si.

**Risco específico**: para medir "surpresa" de resultado, falta uma base de consenso de
analistas gratuita e histórica no Brasil (o equivalente ao I/B/E/S americano não é público).
Precisa usar um proxy mais simples — desvio do crescimento YoY em relação à tendência
recente da própria empresa — o que é razoável, mas mais fraco que comparar contra consenso
de mercado real.

**Por que funcionaria especificamente no Brasil** *[Persona: Quant researcher]*
- O mercado de capitais brasileiro tem uma base de atenção quantitativa (buy-side e
  sell-side) bem menor que a americana — plausivelmente há *menos* gente já precificando
  essa tática de timing de divulgação aqui do que nos EUA, onde o paper original já é de
  2015 e o mercado teve uma década para arbitrar o efeito.
- Os prazos regulatórios da CVM para DFP/ITR são fixos e conhecidos — isso cria, todo
  trimestre, uma coorte natural de "quem entregou de última hora" para estudar, dando uma
  cadência regular de ~4 eventos/ano por empresa.

**Limitações reais** *[Persona: Estatístico/a cético/a]*
- **Falta de consenso de analistas gratuito no Brasil**: sem uma base tipo I/B/E/S, "surpresa"
  precisa ser aproximada por desvio da tendência de crescimento da própria empresa — um
  proxy bem mais fraco que consenso de mercado real, e que pode introduzir ruído não
  relacionado à tática de timing em si.
- **Clustering pode ser só efeito de prazo regulatório, não de tática estratégica**: muitas
  empresas são obrigadas a entregar perto do mesmo prazo por força de regulamento,
  independente de qualquer intenção de "se esconder na multidão" — a métrica de
  "quantas empresas entregaram no mesmo dia" precisa ser comparada contra a taxa-base normal
  de aglomeração perto do prazo, não um número bruto, senão gera falso positivo sistemático.
- **Microestrutura do pregão brasileiro** (leilão de fechamento, liquidez concentrada em
  poucos ativos) pode fazer o efeito de "baixa atenção → reação atrasada" se manifestar de
  forma diferente do documentado no mercado americano — vale checar se o padrão de retorno
  ao redor de divulgação segue lógica parecida antes de assumir que sim.

**Pipeline específico desta tese** *[Persona: Engenheiro/a de dados]*
1. Ingestão do dataset IPE (`Data_Entrega`, `Categoria`, `CNPJ_Companhia`) cruzado com os
   datasets estruturados de DFP/ITR (receita/lucro) do mesmo portal.
2. Cálculo de três features por evento de divulgação: dia da semana; contagem de outras
   empresas que entregaram documento da mesma categoria na mesma data (normalizada pela
   taxa-base de aglomeração perto do prazo regulatório); e antecedência/atraso em relação
   ao prazo limite e ao padrão histórico da própria empresa.
3. Construção do proxy de "surpresa" via desvio da tendência de crescimento YoY da própria
   empresa (documentando explicitamente que isso é mais fraco que consenso de mercado).
4. Teste de associação entre as três features de timing e o proxy de surpresa + retorno
   subsequente.

### 14. CNJ DataJud (litígio trabalhista em massa / recuperação judicial) → estresse + contágio

**Resumo**: monitorar se uma empresa está sendo processada na Justiça do Trabalho em
quantidade anormal — sinal de que ela pode estar demitindo em massa ou com problema
financeiro sério antes de anunciar isso oficialmente — e ver se esse problema "contamina"
fornecedores e clientes dela que também estão na bolsa.

**Hipótese**: aumento anormal de processos trabalhistas contra uma empresa antecipa eventos
de estresse financeiro, com efeito de contágio sobre fornecedores/clientes listados.
**Papers**: Hertzel, Li, Officer & Rodgers, *"Inter-firm Linkages and the Wealth Effects of
Financial Distress along the Supply Chain"*, **Journal of Financial Economics** 87(2), 2008;
Kim & Skinner, *"Measuring securities litigation risk"*, **JAE**, 2012.
**Dado**: API DataJud (CNJ), gratuita, 90 tribunais, 80M+ processos — **mas sem busca direta
por CPF/CNPJ** (LGPD) e com cobertura confiável essencialmente pós-2023.
**Universo**: casos de referência (Americanas, Oi, Light, Marisa) + cadeias de fornecimento
mapeáveis (varejo, frigoríficos, petróleo/E&P).
**Minha leitura**: a mais original e ambiciosa de toda a lista, mas com o maior risco técnico
real (parsing textual de nome de parte, sem CNPJ direto, histórico confiável curto). Mais
adequada a estudo de eventos/casos do que estratégia sistemática de série longa — testar
num piloto pequeno antes de comprometer o projeto a ela.

**Por que funcionaria especificamente no Brasil** *[Persona: Quant researcher]*
- A Justiça do Trabalho brasileira tem um volume de processos por trabalhador muito acima
  do padrão internacional (cultura de litigância trabalhista mais intensa que a maioria dos
  países comparáveis, onde disputas em massa costumam ir para arbitração privada) — isso
  cria mais densidade de "sinal" nesse tipo de dado do que se replicaria em outro mercado.
- A obrigatoriedade de reporte ao CNJ por todos os tribunais cobertos cria uma base
  centralizada única — muitos países não têm um hub único e público de dados judiciais como
  o DataJud.

**Limitações reais** *[Persona: Estatístico/a cético/a]*
- **Resolução de entidade sem CNPJ é frágil**: nome de parte em processo pode divergir da
  marca conhecida (ex: "B2W Digital" vs. "Americanas"), ter erro de digitação em petições, ou
  coincidir com homônimos — risco real de falso positivo/negativo no matching empresa →
  processo.
- **Volume bruto de processos não normalizado é enganoso**: uma empresa grande naturalmente
  gera mais reclamações trabalhistas proporcionalmente ao tamanho do quadro de funcionários,
  sem que isso signifique estresse. Precisa normalizar por headcount — o que, coincidência
  útil, é exatamente o dado que a tese do CAGED já traz, dando um ponto natural de
  cruzamento entre as duas.
- Cobertura confiável começando essencialmente em 2023 limita demais o histórico disponível
  para um backtest tradicional de vários anos.

**Pipeline específico** *[Persona: Engenheiro/a de dados]*
1. Buscar na API DataJud processos na Justiça do Trabalho por nome/razão social das
   empresas do universo, incluindo variações de grafia conhecidas.
2. Normalizar a contagem de processos por headcount da empresa (cruzando com o dado do
   CAGED) para isolar volume *anormal*, não só volume proporcional ao tamanho.
3. Construir índice mensal de "intensidade de litígio anormal" por empresa.
4. Dado o histórico curto, tratar como estudo de eventos/casos-piloto (Americanas, Marisa)
   antes de tentar um backtest sistemático de série longa.

---

## 5. Produção física, mão-de-obra e logística

### 15. CAGED (contratação/demissão formal) → cross-section de retorno

**Resumo**: acompanhar quantas pessoas uma empresa está contratando (dado público do
governo) para tentar prever o retorno futuro da ação dela — empresas contratando rápido
demais tendem, historicamente, a performar pior depois.

**Hipótese**: empresas com taxa líquida de contratação formal anormalmente alta têm retorno
*menor* nos 12 meses seguintes (custo de ajustamento de mão de obra).
**Paper**: Belo, Lin & Bazdresch, *"Labor Hiring, Investment, and Stock Return
Predictability"*, **Journal of Political Economy** 122(1), 2014 — canônico, achado de
~1,5 p.p. de queda no prêmio de risco por 10 p.p. de aumento na taxa de contratação.
**Dado**: CAGED/Novo CAGED (Ministério do Trabalho), microdados de movimentação por CNPJ,
mensal, gratuito, replicado com bom acesso via Base dos Dados.
**Universo**: varejo (Magazine Luiza, Renner, C&A), construção (Cyrela, MRV, Direcional),
frigoríficos, logística (JSL, Vamos, Localiza/Movida).
**Minha leitura**: paper-base é do mesmo calibre dos "clássicos" que vocês já buscam (JPE).
Maior risco real é técnico, não conceitual: reconstruir o CNPJ agregado de cada companhia
aberta (holding + subsidiárias + filiais) é trabalho de match, não de modelagem.

**Por que funcionaria especificamente no Brasil** *[Persona: Quant researcher]*
- O eSocial (base do Novo CAGED) obriga toda empresa formal a reportar admissão/desligamento
  em tempo quase real — cobertura universal do mercado formal, diferente de pesquisas
  amostrais de emprego (como a PNAD), que têm defasagem e margem de erro amostral.
- O mercado de trabalho brasileiro tem rotatividade historicamente alta comparado a
  economias desenvolvidas — mais "eventos" de contratação/demissão por ano por empresa,
  dando mais densidade de observação do que no mercado americano onde o paper original foi
  testado.

**Limitações reais** *[Persona: Estatístico/a cético/a]*
- Reconstruir o CNPJ agregado da empresa aberta (matriz + filiais + subsidiárias) é o
  gargalo real — sem isso, mede-se só uma fração da operação verdadeira da companhia.
- O Novo CAGED (baseado em eSocial, a partir de 2020) tem metodologia diferente do CAGED
  antigo — uma quebra de série real que precisa ser tratada com cuidado se o time quiser
  histórico mais longo que isso.
- Setores com forte sazonalidade de contratação (varejo no fim de ano, agro na safra) podem
  gerar "falsos positivos" de contratação anormal que são só sazonalidade normal — precisa
  desazonalizar antes de interpretar qualquer variação como sinal.

**Pipeline específico** *[Persona: Engenheiro/a de dados]*
1. Construir o de-para de CNPJ (matriz + filiais/subsidiárias) para cada empresa do
   universo, via Receita Federal ou relatórios de RI.
2. Ingestão mensal do CAGED (via Base dos Dados), agregando admissões menos desligamentos
   por CNPJ do grupo.
3. Desazonalizar a série (ajuste por mês do ano e por sazonalidade própria do setor).
4. Calcular a taxa de contratação líquida anormal (desvio da tendência/sazonalidade própria
   da empresa) → sinal de underweight quando anormalmente alta, replicando a lógica do
   paper original.

### 16. ANFAVEA (produção de veículos) → antecipação de receita de autopeças

**Resumo**: acompanhar quantos carros as montadoras fabricam por mês (dado público) para
prever se as fábricas de autopeças que vendem para elas vão ter resultado bom ou ruim antes
do balanço sair.

**Hipótese**: produção mensal de veículos (sai antes do resultado trimestral) antecipa
surpresa de receita das autopeças que vendem para montadoras.
**Papers**: Cohen & Frazzini, *"Economic Links and Predictable Returns"*, **Journal of
Finance** 63(4), 2008 (extensão — vínculo setorial de produção física em vez de vínculo de
propriedade/contrato); Jegadeesh & Livnat 2006 (mesmo de cima).
**Dado**: ANFAVEA, séries mensais desde 1957, gratuitas, "Edições em Excel".
**Universo**: Randon (RAPT4), Iochpe-Maxion (MYPK3), Tupy (TUPY3), Marcopolo (POMO4),
Fras-le (FRAS3) — 5-6 tickers, cluster pequeno mas bem definido.
**Minha leitura**: a mais simples e "limpa" tecnicamente de toda a lista — dado numérico,
série longuíssima, mecanismo muito intuitivo de explicar (monta carro usa peça). Universo
pequeno limita testes de corte transversal, mas funciona bem como estratégia de
nowcasting de earnings por empresa.

**Por que funcionaria especificamente no Brasil** *[Persona: Quant researcher]*
- O mercado automotivo brasileiro é um oligopólio de compradores concentrado — poucas
  montadoras (VW, GM, Stellantis, Toyota, Hyundai) compram de um conjunto relativamente
  pequeno de autopeças listadas, tornando o vínculo "produção da montadora → receita da
  autopeça" mais direto e limpo do que num mercado de fornecedores mais fragmentado.
- A ANFAVEA publica dado desde 1957 — uma das séries industriais mais longas e consistentes
  do Brasil, robustez histórica rara para um país emergente.

**Limitações reais** *[Persona: Estatístico/a cético/a]*
- Universo pequeno (5-6 tickers) limita generalização estatística — o resultado pode
  depender muito de um ou dois casos específicos, não de um padrão amplo.
- Nem toda receita das autopeças vem de montadoras nacionais — exportação é relevante
  (Randon, Fras-le vendem bastante fora do país) — parte da receita fica fora do alcance do
  sinal de produção doméstica.
- Contratos de fornecimento costumam ter estoque-pulmão entre montadora e autopeça — pode
  haver absorção/defasagem de choques de produção que dilui a precisão do timing do sinal.

**Pipeline específico** *[Persona: Engenheiro/a de dados]*
1. Ingestão mensal da produção de veículos por categoria (ANFAVEA).
2. Mapear qual autopeça fornece para qual segmento (ex: Fras-le é mais ligada a veículos
   pesados/comerciais que a carros de passeio) — não tratar a produção agregada como proxy
   uniforme para todas.
3. Calcular crescimento YoY da produção do segmento relevante → sinal antecedente de receita
   da autopeça correspondente.
4. Controlar pela participação de exportação na receita de cada autopeça (via demonstrações
   financeiras) para calibrar o peso esperado do sinal doméstico.

### 17. ANTT (tráfego de pedágio) → antecipação de receita de concessionárias e logística

**Resumo**: usar o número de carros e caminhões passando pelos pedágios federais, todo dia,
como um jeito de saber se o transporte de carga e as próprias concessionárias de rodovia
estão indo bem antes do resultado trimestral sair.

**Hipótese**: volume diário de tráfego pedagiado antecipa surpresa de receita de
concessionárias e serve de proxy de atividade logística para empresas dependentes de frete.
**Papers**: Katona, Painter, Patatoukas & Zeng, *"On the Capital Market Consequences of
Alternative Data: Evidence from Outer Space"*, **JFQA** 60(2), 2025 (satélite de
estacionamento antecipando earnings, mesma família de mecanismo); Jegadeesh & Livnat,
*"Revenue Surprises and Stock Returns"*, **Journal of Accounting and Economics**, 2006.
**Dado**: ANTT, tráfego diário por praça de pedágio, categoria de veículo, gratuito, desde
pelo menos 2017.
**Universo**: CCR/Motiva (MOTV3), Ecorodovias (ECOR3) diretamente; JSL, Vamos, Simpar,
Localiza/Movida indiretamente como proxy logístico.
**Minha leitura**: poucas concessionárias "puro-jogo" listadas — funciona melhor como sinal
setorial/macro de atividade logística do que arbitragem de earnings de uma única empresa.

**Por que funcionaria especificamente no Brasil** *[Persona: Quant researcher]*
- A malha de transporte brasileira é fortemente dependente de rodovia (diferente de países
  com matriz ferroviária/hidroviária mais forte) — tráfego pedagiado capta uma fatia maior
  da atividade logística real do que capturaria numa economia com transporte mais
  diversificado.
- Concessões pedagiadas são obrigadas a reportar tráfego à ANTT como parte da regulação —
  mesma lógica institucional de dado obrigatório que sustenta as teses do ONS e da ANTAQ.

**Limitações reais** *[Persona: Estatístico/a cético/a]*
- Tráfego pedagiado só cobre trechos concedidos, não a malha rodoviária inteira — viés de
  cobertura geográfica, mais forte no Sudeste/Sul, onde há mais concessões.
- Sazonalidade forte (feriados, safra regional, período de festas) precisa ser removida
  antes de interpretar qualquer variação como sinal econômico.
- A categoria "veículo pesado" pode misturar caminhão de carga com ônibus de turismo em
  algumas classificações — checar a granularidade exata antes de assumir que o dado é
  puramente sobre transporte de carga.

**Pipeline específico** *[Persona: Engenheiro/a de dados]*
1. Ingestão diária de tráfego por praça de pedágio e categoria de veículo.
2. Desazonalização (dia da semana, feriados, calendário de safra regional).
3. Construção de um índice de atividade logística por região/rodovia relevante.
4. Validação cruzando o índice com a receita de pedágio já reportada pelas próprias
   concessionárias (CCR/Motiva, Ecorodovias) antes de estender o sinal para o uso mais
   amplo como proxy logístico setorial.

### 18. ANP (vendas de combustível) → proxy regional + distribuidoras

**Resumo**: olhar quanto combustível é vendido por estado como termômetro de atividade
econômica regional e das distribuidoras — mas é a tese com a base acadêmica mais fraca do
grupo, então fica como reserva.

**Hipótese**: volume de vendas de combustível por UF antecipa surpresa de volume das
distribuidoras e serve de proxy de atividade econômica regional.
**Minha leitura antes mesmo do paper**: esta é a de vínculo acadêmico mais fraco do lote — é
extrapolação da família "dado operacional de alta frequência antecipa earnings", não um
paper específico testando exatamente isso. **Não recomendo como tese principal.** Redundante
em espírito com a tese de energia (ONS) que já está na lista.

**Por que funcionaria especificamente no Brasil** *[Persona: Quant researcher]*
- A distribuição de combustíveis no Brasil é dominada por poucas grandes distribuidoras
  (Vibra, Raízen, Ultrapar/Ipiranga) — mercado concentrado, parecido com o bancário, o que
  facilitaria atribuir sinal a uma empresa específica *se* houvesse dado granular o
  suficiente para isso (ver limitação abaixo).
- O Brasil tem mistura obrigatória de etanol na gasolina, definida por política pública e
  variável ao longo do tempo — o dado da ANP também captura esse efeito regulatório
  específico do país, que não existe da mesma forma em outros mercados.

**Limitações reais** *[Persona: Estatístico/a cético/a]*
- Sem uma âncora acadêmica específica (como já sinalizado), o desenho do sinal fica mais
  especulativo que nas demais teses do levantamento.
- Atribuir venda agregada por UF a uma distribuidora específica não é direto — não confirmei
  se o dado público segmenta por marca/distribuidora com granularidade suficiente para isso.
- Redundância com a tese de energia (ONS), como já apontado — ambas tentam medir "quanto uma
  região está economicamente ativa".

**Pipeline específico (caso decidam testar mesmo com a prioridade baixa)**
*[Persona: Engenheiro/a de dados]*
1. Ingestão mensal de vendas por UF e produto (ANP).
2. Checar se existe segmentação por distribuidora nos dados públicos — sem isso, a tese só
   funciona como proxy macro/regional, não firm-specific.
3. Comparar o poder preditivo contra o sinal de energia elétrica (ONS) já existente — só
   manter esta tese se ela agregar informação que o ONS não capta.

---

## 6. Gasto público e imobiliário

### 19. ComprasNet/Portal da Transparência → exposição a ciclo de gasto público

**Resumo**: identificar quais empresas vendem bastante para o governo federal (contratos
públicos são informação aberta) e testar se o ritmo de gasto público, que varia com eleição
e orçamento, afeta o retorno dessas ações de um jeito que o mercado ainda não está de olho.

**Hipótese**: empresas com receita relevante ligada a contratos federais têm retorno
correlacionado ao ritmo de execução orçamentária (ciclo eleitoral/fiscal).
**Paper**: Belo, Gala & Li, *"Government Spending, Political Cycles, and the Cross Section
of Stock Returns"*, **Journal of Financial Economics** 107(2), 2013 — ~6,9% a.a. numa
estratégia long-short nos EUA (bipartidarismo Dem/Rep — precisa reformular a variável de
"ciclo" pro contexto brasileiro).
**Dado**: Compras.gov.br/Portal da Transparência, API pública com CNPJ do vencedor.
**Universo**: saneamento (Sabesp, Copasa), saúde suplementar (Hapvida, Fleury), tecnologia
governamental (TOTVS, Positivo), concessões.
**Minha leitura**: é a tese com mais trabalho manual de mapeamento (a maioria dos grandes
fornecedores diretos do governo não é listada ou tem baixa liquidez) — o link
CNPJ-vencedor → ticker precisa de proxy indireto pra maioria dos casos.

**Por que funcionaria especificamente no Brasil** *[Persona: Quant researcher]*
- O governo brasileiro é um comprador extremamente relevante em setores como saúde
  suplementar, saneamento e tecnologia — participação do gasto público no PIB é maior aqui
  que a média de economias desenvolvidas comparáveis, tornando exposição a contrato público
  um fator de risco mais material no Brasil do que seria adaptar a mesma tese para outro
  país.
- O ciclo orçamentário brasileiro tem características próprias (execução de emendas
  parlamentares, contingenciamento por regra fiscal) que criam padrões de gasto mais
  previsíveis/sazonais do que em sistemas orçamentários mais flexíveis — uma variável de
  "ciclo" bem definida, ainda que diferente da americana.

**Limitações reais** *[Persona: Estatístico/a cético/a]*
- Contratos grandes de infraestrutura costumam ser vencidos por **consórcios**, não uma
  única empresa — mapear CNPJ vencedor → empresa listada exige desagregar a participação de
  cada consorciada, trabalho manual real, não automatizável de forma simples.
- Contrato assinado não equivale a execução financeira efetiva no mesmo período — pode haver
  defasagem grande entre assinatura e o pagamento sendo reconhecido como receita.
- O paper original usa o ciclo bipartidário americano (Democrata/Republicano); o Brasil não
  tem essa estrutura — a variável de "ciclo político" precisa ser redefinida (ex: proximidade
  de eleição, índice de execução orçamentária do Tesouro), uma adaptação metodológica não
  trivial, não uma simples troca de rótulo.

**Pipeline específico** *[Persona: Engenheiro/a de dados]*
1. Ingestão de contratos/licitações via API do Compras.gov.br, filtrando por CNPJ das
   empresas do universo e de subsidiárias/consorciadas conhecidas.
2. Construção de série de valor contratado por empresa/trimestre.
3. Definir uma variável de ciclo político brasileiro (ex: dummy de ano eleitoral, índice de
   execução orçamentária do Tesouro) como adaptação da metodologia original.
4. Teste de correlação entre exposição a gasto público e retorno ao longo desse ciclo.

### 20. ITBI (transações imobiliárias, São Paulo) → antecipação de vendas de incorporadoras

**Resumo**: acompanhar quantos imóveis estão sendo comprados e registrados em São Paulo
para tentar prever se as construtoras vão vender bem — mas descobrimos que esse registro
pode demorar meses ou até anos depois da venda de verdade, o que pode inviabilizar a ideia.

**Hipótese**: volume/valor de transações sujeitas a ITBI antecipa ritmo de vendas
contratadas de incorporadoras com exposição a São Paulo.
**Base acadêmica**: a mais fraca do levantamento inteiro — não achei um paper específico
equivalente aos "clássicos" das outras teses; a lógica se apoia mais na literatura geral de
volume de transação imobiliária afetando retorno de real estate do que num paper
diretamente análogo.
**Dado**: portal da Secretaria da Fazenda de SP — confirmado, gratuito, 2006-2026, mensal,
download direto (não é scraping).
**Minha leitura**: o dado é o melhor de todo o grupo (20 anos de histórico, download direto,
sem fragilidade nenhuma), mas o respaldo acadêmico é o elo fraco — só recomendaria se o time
achar um paper melhor antes de apresentar à banca, ou se reposicionar como extensão natural
da lógica "dado administrativo antecipando fundamento" que a tese de timing CVM já usa.

**Por que funcionaria especificamente no Brasil** *[Persona: Quant researcher]*
- O sistema SQL (Setor-Quadra-Lote) de São Paulo dá geocodificação de precisão de lote, algo
  que não é trivial de conseguir de graça em muitos países — a maioria dos registros
  imobiliários públicos internacionais não chega a esse nível de granularidade espacial sem
  custo.
- Incorporadoras brasileiras não divulgam guidance mensal de vendas como algumas REITs
  americanas fazem — divulgam VSO trimestralmente. Isso deixa mais espaço estrutural para
  um proxy de alta frequência (mensal) ser genuinamente útil, se o problema de defasagem
  abaixo puder ser resolvido.

**Limitações reais** *[Persona: Estatístico/a cético/a]* — **esta é a limitação mais séria
que encontrei ao aprofundar, e muda a leitura da tese**:
- O ITBI é pago no **registro em cartório**, que ocorre depois da assinatura do contrato,
  aprovação de financiamento (quando há) e, no mercado primário, muitas vezes depois da
  entrega das chaves — para lançamentos, esse intervalo pode ser de **meses a anos** entre a
  venda comercial (o que a incorporadora divulga como VSO) e o registro de ITBI. Se esse
  atraso for grande e variável, o ITBI deixa de ser um dado *antecedente* à VSO e passa a
  ser, na melhor das hipóteses, um dado *coincidente com atraso incerto* — o oposto do que a
  tese precisa. Isso é um problema conceitual, não só um risco de execução, e precisa ser
  medido empiricamente **antes** de investir no resto do pipeline.
- Sem campo de "tipo de imóvel" confirmado, distinguir mercado primário (o que interessa
  para incorporadoras) de secundário (revenda, que não afeta a receita da incorporadora)
  exige heurística (ex: cruzar com data de lançamento do empreendimento), não é automático.
- Dado é só de São Paulo — generalizar para outras praças exige checar portais municipais
  separados, com formatos possivelmente diferentes.

**Pipeline específico** *[Persona: Engenheiro/a de dados]* — **reordenado para testar a
limitação crítica primeiro**:
1. **Antes de qualquer outra coisa**: pegar 3-5 lançamentos de incorporadoras conhecidas com
   data de VSO/entrega de chaves pública, e medir empiricamente a defasagem até o pico de
   registros de ITBI na região do empreendimento. Se a defasagem for curta e consistente, a
   tese sobrevive; se for longa/errática, ela não funciona como "antecedente" e deveria ser
   descartada ou reformulada antes de mais trabalho.
2. Só depois desse teste: ingestão mensal do portal da Fazenda de SP, geocodificação via
   SQL, filtro heurístico primário vs. secundário.
3. Agregação por região/faixa de valor → sinal, com a defasagem medida no passo 1 já
   incorporada ao desenho (não como um detalhe a ajustar depois).

---

## 7. Atenção do investidor

### 21. Índice de atenção via Wikipedia pageviews
*(versão ajustada da #21 do docx antigo — troquei Google Trends por Wikipedia)*

**Resumo**: medir quantas pessoas pesquisam sobre uma empresa na Wikipédia como termômetro
de quanto ela está "na moda" entre investidores — mas essa ideia já foi bastante testada no
Brasil usando Google, então corre risco de não parecer original.
- **Paper-base**: mesma família da literatura de "investor attention" (Da-Engelberg-Gao
  2011 é o clássico com Google Trends; existe uma réplica usando Wikipedia pageviews para
  o Nasdaq).
- **Ressalva importante**: **Google Trends em ações do Ibovespa já foi testado múltiplas
  vezes no Brasil** (SciELO, Redalyc, dissertação UFPR — achei pelo menos 3 estudos). Usar
  Wikipedia em vez de Google Trends é uma fonte de dado diferente, mas o mecanismo é quase
  idêntico — uma banca mais rigorosa pode enxergar isso como pouco original, mesmo que a
  fonte de dado específica não tenha sido usada aqui ainda.
- **Leitura**: dado grátis e fácil (API pública da Wikimedia), mas o ineditismo é discutível.
  Só recomendaria se combinada com outra tese, não como sinal único.

**Por que funcionaria especificamente no Brasil** *[Persona: Quant researcher]*
- A Wikipédia em português tem edição e cobertura próprias, tipicamente mais rala para
  empresas brasileiras do que a versão em inglês para empresas americanas — pageviews da
  página em português especificamente poderiam captar atenção de investidor brasileiro de
  forma mais "pura" que o Google Trends, que mistura buscas por motivos totalmente alheios a
  investimento (notícia, curiosidade, trabalho escolar).

**Limitações reais** *[Persona: Estatístico/a cético/a]*
- A redundância com Google Trends já testado no Brasil (acima) continua sendo o problema
  central — troca de fonte de dado, não de mecanismo.
- Volume de pageviews de empresas menores tende a ser baixo e ruidoso, tornando o sinal
  instável fora das blue chips mais conhecidas do público em geral.
- Wikipédia pode ser editada por qualquer pessoa — picos de pageview podem vir de eventos
  sem relação com investimento (matéria de jornalismo, controvérsia, efeméride), que não
  necessariamente preveem retorno da forma que a tese pressupõe.

**Pipeline específico** *[Persona: Engenheiro/a de dados]*
1. Ingestão de pageviews diárias via API REST pública da Wikimedia (sem necessidade de
   token) para a página em português de cada empresa do universo.
2. Cálculo de anomalia (z-score) de pageviews vs. média móvel.
3. Teste de correlação com retorno subsequente, replicando a lógica de reversão de curto
   prazo do paper original de Google Trends (SVI).
4. Comparação direta com um sinal equivalente de Google Trends para o mesmo universo —
   manter a tese só se Wikipedia mostrar poder preditivo incremental sobre o que o Google
   Trends já capturaria.

---

## Descartadas do docx original (e por quê)

| Ideia original | Motivo do descarte |
|---|---|
| Caminhoneiro Invisível, Termômetro da Base | Dado não público (grupos fechados de WhatsApp/Telegram) — inviável |
| Índice do Andaime Parado | Precisa visão computacional em Street View + amostragem manual de bairros — esforço alto, ganho incerto |
| Efeito Pós-Doutorado (LinkedIn) | Sem API pública de LinkedIn para isso; scraping viola ToS e não é confiável |
| Sinal do Visto EB-5 | Dado real (USCIS), mas lag de 6 meses e é sinal macro de fuga de capital, não gera decisão de ação específica |
| Apagão Seletivo (ANEEL por CNPJ) | Substituída pela versão viável com dado do ONS |
| Índice da Cueca, Comida de Fim do Mundo, Lavanderia a Seco, Aposta Desesperada, Dente do Siso | Todas dependem de scraping de e-commerce/agendas sem API pública e sem histórico acessível |
| Rastreador de Jatos Corporativos | Dado existe (ADS-B) mas é para M&A de empresas americanas; adaptar para o Brasil teria universo de eventos pequeno demais |
| Luzes Noturnas (satélite) | Literatura aponta baixa variância temporal da luminosidade — reavaliada como tese de Luz Noturna (VIIRS), com risco de redundância com energia/Pix |
| Roubo de Cobre, Casamentos/Divórcios, Lixo Comercial | Sem fonte de dado brasileira pública e confiável |
| Termômetro do Dengue Econômico | Dado real e público (API InfoDengue/Fiocruz), mas mapear "quais empresas têm >30% da produção" por município exige trabalho manual grande — vale como **sinal secundário/bônus** somado à tese climática, não como tese principal sozinha |
| Índice da Insônia Corporativa (SEC EDGAR) | Substituída pela versão com CVM/IPE (tese de timing de submissão) |
| Similaridade Textual (Hoberg-Phillips) | Não descartada — promovida à lista principal |
| Q&A evasivo em earnings calls, Tom de teleconferências | **Já testado no Brasil** (SciELO: 44 empresas B3, 2010-2017, dicionário Loughran-McDonald) — perderia ponto de originalidade nesse formato |
| Alpha do Empregado (Glassdoor/Love Mondays) | Dado existe e não achei réplica brasileira, mas scraping tem barreira anti-bot forte e cobertura de reviews é esparsa fora das large caps — mantida como ideia de reserva, não priorizada aqui |
| Dev-Alpha (GitHub) | Poucas empresas listadas na B3 são open-source o suficiente para gerar sinal |
| Redes de Concorrência Dinâmica | É essencialmente a mesma ideia do Hoberg-Phillips — não duplicar |

---

## Avaliação por critérios — as 21 teses num só ranking

O `Avaliacao_Comparativa_LLMs(1).xlsx` já tinha uma boa estrutura de 8 critérios (Base
Teórica, Viabilidade, Freq./Profundidade, Sinal-Ruído, Escalabilidade, Custo/Acesso,
Latência, Originalidade), aplicada às 27 teses do docx original por três LLMs. Reaproveitei
o que fazia sentido e troquei o resto por critérios mais específicos pra nossa situação:

**Mantidos do xlsx**: Base Teórica, Custo e Acesso.

**Trocados/adaptados** — o xlsx pontuava "Originalidade" e "Viabilidade" de forma
genérica, sem pesquisa real; aqui essas notas vêm de busca de fato (papers brasileiros
existentes, disponibilidade confirmada de API):
- **Novidade real no Brasil** — substitui "Originalidade": baseada em busca ativa por
  réplicas já publicadas aqui, não em impressão.
- **Complexidade de execução** — substitui "Viabilidade (Eng.)": esforço técnico estimado,
  sem peso de urgência de prazo (fase é de exploração, não de entrega sob pressão).
- **Densidade de observações** — substitui "Freq. e Profundidade" + "Escalabilidade":
  o desafio pune "escolha oportunista de período" (Backtest, 15%), então importa ter
  observações suficientes pra um teste que não pareça garimpado.
- **Gera decisão de investimento clara** — novo, direto do texto do edital ("sinal de
  compra/venda, ranking, alocação, rebalanceamento" — Modelagem, 20%).
- **Facilidade de defender sem bagagem de economia** — novo, dado o perfil do time e que
  a banca faz Q&A nas fases eliminatórias.
- **Espaço orgânico para GenAI** — novo, direto do critério de 15% do edital: teses onde
  IA generativa entra naturalmente no núcleo do modelo (não só na escrita do relatório)
  pontuam mais alto aqui.

**Removido**: "Latência (Alpha Decay)" — relevante para um fundo real decidindo se um sinal
ainda compensa após custos de execução; menos relevante aqui, onde não há execução ao vivo.

Escala 1-5 por critério, soma /40. Aprofundar as teses (raciocínio Brasil-específico,
limitações reais, pipeline) mudou algumas notas de forma real, não cosmética — três exemplos:
ITBI caiu porque o aprofundamento revelou que o intervalo entre venda e registro pode ser de
meses a anos (ataca a premissa de "antecedente"); Desmatamento subiu porque o calendário de
compliance da EUDR dá um jeito concreto de ancorar o sinal; Wikipedia caiu em relação à
avaliação original do xlsx porque a checagem real de novidade achou 3 papers brasileiros
usando a mesma ideia com Google Trends.

| # | Tese | Base Teórica | Novidade BR | Custo/Acesso | Complexidade Execução | Densidade Obs. | Decisão Clara | Fácil Defender | GenAI Orgânica | **Total /40** |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Choque climático → agro | 4 | 5 | 5 | 5 | 4 | 5 | 5 | 3 | **36** |
| 3 | ComexStat → exportadoras | 3 | 5 | 5 | 5 | 5 | 5 | 4 | 2 | **34** |
| 16 | ANFAVEA → autopeças | 3 | 5 | 5 | 5 | 4 | 4 | 5 | 2 | **33** |
| 15 | CAGED → cross-section de retorno | 5 | 5 | 4 | 3 | 5 | 4 | 4 | 2 | **32** |
| 12 | TNIC/Hoberg-Phillips via CVM | 5 | 5 | 4 | 3 | 3 | 4 | 3 | 5 | 32 |
| 10 | SCR bancário → crash risk | 5 | 4 | 5 | 4 | 3 | 4 | 4 | 2 | 31 |
| 17 | ANTT (pedágio) → logística | 4 | 5 | 5 | 4 | 4 | 3 | 4 | 2 | 31 |
| 21 | Wikipedia pageviews (atenção) | 4 | 2 | 5 | 5 | 5 | 4 | 4 | 2 | 31 |
| 7 | Consumo de energia regional (ONS) | 4 | 5 | 4 | 3 | 5 | 3 | 4 | 2 | 30 |
| 11 | SCR setorial → estresse não-financeiro | 4 | 5 | 5 | 4 | 3 | 3 | 3 | 2 | 29 |
| 4 | AIS/ANTAQ → nowcasting portuário | 4 | 5 | 3 | 3 | 4 | 4 | 4 | 2 | 29 |
| 6 | Desmatamento (DETER) | 5 | 2 | 5 | 3 | 3 | 5 | 4 | 2 | 29 |
| 9 | Luz noturna (VIIRS) | 5 | 3 | 4 | 3 | 4 | 3 | 4 | 2 | 28 |
| 13 | Timing de submissão CVM/IPE (pivotada) | 5 | 5 | 4 | 3 | 3 | 3 | 3 | 2 | 28 |
| 19 | ComprasNet (gasto público) | 5 | 5 | 4 | 2 | 4 | 3 | 3 | 2 | 28 |
| 2 | NDVI (satélite/agro) | 3 | 4 | 4 | 3 | 4 | 4 | 4 | 2 | 28 |
| 14 | CNJ DataJud (litígio/RJ) | 5 | 5 | 2 | 2 | 2 | 3 | 3 | 4 | 26 |
| 20 | ITBI (imobiliário SP) | 2 | 5 | 5 | 4 | 4 | 1 | 2 | 2 | 25 |
| 8 | PIX (BCB) → timing consumo | 4 | 5 | 2 | 2 | 2 | 2 | 4 | 2 | 23 |
| 18 | ANP (combustíveis) | 2 | 4 | 4 | 3 | 3 | 2 | 3 | 2 | 23 |
| 5 | SAR (radar de satélite) | 4 | 5 | 2 | 1 | 3 | 3 | 2 | 2 | 22 |

**Como ler isso — a soma sozinha engana em alguns casos**:
- **TNIC (32) e Wikipedia (31) empatam por motivos opostos.** TNIC é rigorosa e genuinamente
  original, mas tecnicamente pesada (Complexidade de Execução = 3, das mais altas da lista).
  Wikipedia é rápida de implementar, mas pouco original (mecanismo quase idêntico ao Google
  Trends, já testado 3x no Brasil).
- **AIS/ANTAQ (29), Desmatamento (29) e SCR setorial (29) chegam ao mesmo total por caminhos
  bem diferentes** — vale olhar a tabela coluna a coluna antes de decidir, não só o total.
- **NDVI e AIS/ANTAQ não deveriam ser lidos como "8ª e 9ª colocadas" isoladas** — são camadas
  de robustez das teses de clima e ComexStat, respectivamente. O ranking inclui elas como
  linhas próprias só para deixar a régua consistente, mas a decisão real é "usar como
  reforço da tese principal", não "escolher entre a tese 1 e a tese 2".
- **ITBI é a que mais caiu ao ser aprofundada** (de 28 para 25): o problema de defasagem
  entre venda e registro derruba a nota de "Decisão Clara" especificamente, porque a
  premissa de ser "antecedente" ficou em dúvida.

---

## Minha recomendação de combo

**Tese principal**: choque climático + ComexStat como duas fontes que se reforçam — uma
antecipa a safra, a outra confirma o embarque. Dá um modelo com lógica em duas etapas
(sinal antecedente + sinal confirmatório), forte no critério de Modelagem (20%), sem
depender de scraping ou NLP. Continua na liderança mesmo depois de aprofundar todas as
outras 19 teses — nenhuma delas supera essa combinação sozinha.

**Upgrades diretos, com o protocolo de validação que o aprofundamento deixou claro que é
necessário — não é "plug and play"**:
- NDVI como validação cruzada da tese climática — mas só promover a sinal com peso próprio
  depois de testar se agrega poder preditivo incremental sobre a chuva sozinha.
- ANTT/AIS como confirmação mais granular da tese do ComexStat — mas testar a viabilidade
  real do AIS gratuito antes de depender dele, e tratar divergência ANTAQ-vs-ComexStat como
  informação, não como ruído a ignorar.

**ITBI sai da lista de consideração até prova em contrário**: o aprofundamento encontrou um
problema conceitual (defasagem entre venda e registro pode ser longa e variável), não só
técnico. Se o time tiver interesse específico em imobiliário, a primeira coisa a fazer é o
teste empírico de defasagem sugerido no pipeline — só depois disso decidir se a tese é
viável, não antes.

**Desmatamento (DETER) é uma candidata secundária real, não descartável**: ancorar o sinal
no calendário de compliance da EUDR em vez de um score contínuo resolve o problema que eu
via antes. Não é páreo para clima/ComexStat como tese principal (a relação JBS/Marfrig/
Minerva-desmatamento já é conhecida publicamente via Chain Reaction Research, então a
"descoberta" não é original, só a sistematização quantitativa seria), mas é um bom candidato
a **sinal de risco/overlay** somado à tese principal, não uma tese concorrente.

**Se sobrar apetite técnico**: ANFAVEA e CAGED são as mais sólidas depois das duas
principais — tão bem fundamentadas quanto TNIC, mas tecnicamente mais simples. TNIC continua
a aposta de maior retorno técnico se o time preferir o desafio de NLP. SCR (bancário +
setorial, agora reavaliado com o requisito de teste de causalidade de Granger) segue como
uma dupla de teses sólida sobre a mesma fonte de dado, com rigor extra necessário antes de
aceitar o sinal como genuinamente antecedente.

**Mais arriscada, mas a mais original de toda a lista**: CNJ DataJud (litígio/recuperação
judicial) — vale um piloto pequeno (checar se dá pra resolver nome de parte → CNPJ de forma
minimamente confiável) antes de comprometer o projeto a ela.

**Recomendo não priorizar, com a razão específica de cada uma**: PIX (granularidade mensal/
nacional confirmada, insuficiente), ANP (elo acadêmico mais fraco do levantamento), SAR
(tecnicamente a mais difícil, mesmo com a vantagem real de nuvem tropical), Luz noturna
(redundante com energia/Pix enquanto isso não for resolvido por um teste de valor
incremental) — todas ficam como material de reserva, não como candidatas de primeira linha.
