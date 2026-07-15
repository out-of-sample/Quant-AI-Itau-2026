"""Camada de features: anomalia climática por célula/fase, exposição E, gate de confirmação.

Toda estatística de normalização (climatologia, z-score) é expanding/rolling com dados
anteriores a t — nunca a média do período inteiro, que seria lookahead.
"""
