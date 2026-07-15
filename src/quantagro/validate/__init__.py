"""Camada de validação: carimba ref_date e avail_date e faz valer o point-in-time.

Invariante desta camada: nenhuma linha sai daqui sem avail_date. O restante do pipeline
tem permissão de filtrar apenas por avail_date, nunca por ref_date (regra dura do projeto).
"""
