"""Eventos corporativos curados manualmente — o que as fontes automáticas comprovadamente perdem.

Este registro existe porque o cross-check da série montada contra uma fonte ajustada
independente (Yahoo, `scripts/crosscheck_yahoo.py`) encontrou um evento real ausente de
**todas** as fontes automáticas do projeto — confirmando que o `GetListedSupplementCompany`
da B3 trunca a lista de eventos em ações (ressalva de D-013, agora fato).

Regras deste arquivo:
- **Nunca adicionar evento sem fonte primária citada** (documento societário / RI da empresa).
  Um evento sem proveniência é indistinguível de um ajuste conveniente.
- Cada entrada nasce de uma divergência concreta pega pelo cross-check, nunca de memória.
- O registro é versionado: o histórico do git é a trilha de auditoria de quando e por que
  cada evento entrou.
"""

from __future__ import annotations

import pandas as pd

from quantagro.prices.adjust import CorporateEvent

_MANUAL_EVENTS: dict[str, list[CorporateEvent]] = {
    "SLCE3": [
        # Bonificação de 10% (1 ON nova para cada 10) aprovada na AGO/E de 27/04/2023;
        # data-base (com) 08/05/2023, negociação ex-direito a partir de 09/05/2023,
        # 21.242.259 novas ações. Fonte: RI SLC Agrícola (ri.slcagricola.com.br/bonificacao)
        # e ata da AGO/E de 27/04/2023. Ausente do supplement da B3 (que só lista o
        # desdobramento de 12/2023 e a bonificação de 12/2025) e da StatusInvest.
        # Detectada por divergência de 9,1% no cross-check com o Yahoo em 09/05/2023.
        CorporateEvent(cum_date=pd.Timestamp("2023-05-08"), share_ratio=1.1),
    ],
}


def manual_events(ticker: str) -> list[CorporateEvent]:
    """Eventos curados de um ticker (lista vazia se não houver) — somar aos das APIs."""
    return list(_MANUAL_EVENTS.get(ticker, []))
