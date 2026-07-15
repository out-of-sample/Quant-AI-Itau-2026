"""Camada de ingestão: baixa as fontes públicas e as persiste cruas, sem transformar.

Cada fonte grava um manifesto em data/manifests/ (data do download, hash, versão/vintage
da fonte) — é o que torna o backtest auditável sem versionar os dados brutos.
"""
