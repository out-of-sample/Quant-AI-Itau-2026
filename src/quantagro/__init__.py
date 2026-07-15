"""quantagro — pipeline da estratégia long/short agro dirigida por choque climático.

Organização em camadas (ver docs/03_ARQUITETURA.md):
    ingest → validate → features → stats → signal → backtest → robustness → report

Regra dura do projeto (docs/00_PLANO_MESTRE.md): nenhum sinal usa dado indisponível
no instante da decisão. Toda tabela carrega ref_date e avail_date; filtra-se por avail_date.
"""

__version__ = "0.0.0"
