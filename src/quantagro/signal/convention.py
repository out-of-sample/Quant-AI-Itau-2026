"""Convenção de sinal do projeto — a fonte única de verdade sobre *quem sobe e quem cai*.

Formalização (docs/01_TESE_E_PRE_REGISTRO.md §3):

    S_{i,t} = Σ_c  E_{i,c} · Shock_{c,t}

Convenções, todas travadas em tests/test_signal_sign.py:

- `Shock_{c,t}` é **estresse**: valor > 0 significa condição climática *ruim* para a
  lavoura (seca/calor na fase crítica), o que empurra o **preço da commodity para cima**.
- `E_{i,c}` é a **exposição líquida** da empresa `i` à commodity `c`, em [-1, +1]:
      +1 = produtor puro   (ganha quando o preço de `c` sobe)
      -1 = consumidor puro do insumo, ex. frigorífico (perde quando o preço de `c` sobe)
- Logo `S_{i,t} > 0` ⇒ esperamos **retorno positivo** para a empresa `i`.
      produtor  (E>0) sob estresse (Shock>0) ⇒ score positivo  ⇒ compra (long)
      frigorífico (E<0) sob o mesmo estresse ⇒ score negativo ⇒ vende (short)

IMPORTANTE — a não-linearidade da cana/café/safrinha (docs/09_FENOLOGIA_E_LIMIARES.md,
decisão D-010) vive **dentro da construção de `Shock`** (o sinal de `Shock` já vem correto
por cultura × fase). Este módulo só combina `E` com `Shock` de forma linear; ele **não**
conhece fenologia. Manter essa separação é o que permite testar a convenção isoladamente.
"""

from __future__ import annotations

import numpy as np

# Direções de posição, para leitura explícita em vez de comparar com 0 espalhado pelo código.
LONG = 1  # score > 0  ⇒ compra
SHORT = -1  # score < 0  ⇒ vende
FLAT = 0  # score == 0 ⇒ sem posição


def raw_signal(exposure: float | np.ndarray, shock: float | np.ndarray):
    """Sinal bruto por empresa/commodity: `E · Shock`.

    Aceita escalar ou array (vetorizado). A soma sobre culturas (Σ_c) é responsabilidade
    do chamador — aqui trava-se apenas a regra elementar de qual sinal cada par (E, Shock)
    produz, que é o ponto onde o bug de inversão nasce.
    """
    return np.asarray(exposure) * np.asarray(shock)


def position_side(score: float | np.ndarray):
    """Lado da posição implicado por um score: LONG / SHORT / FLAT.

    `np.sign` já entrega a convenção correta (1 / -1 / 0). Envolver num nome próprio deixa
    a intenção explícita e dá um único ponto para o teste amarrar.
    """
    return np.sign(score).astype(int)
