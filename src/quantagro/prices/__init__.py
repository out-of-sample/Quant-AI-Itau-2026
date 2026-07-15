"""Camada de preços: constrói a série de retorno total a partir do COTAHIST + eventos.

Invariante desta camada: o preço bruto do COTAHIST (não ajustado) é combinado com os eventos
corporativos (dividendos/JCP da B3 + StatusInvest; splits/bonificações da B3) para produzir
**retorno total diário, point-in-time e delisting-aware** — nunca uma série de "preço ajustado"
retroativo, que embutiria lookahead. Ver docs/02_DADOS.md §4.2.1 e a decisão D-013.
"""
