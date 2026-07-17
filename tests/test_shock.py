"""Testes do C2 ``Shock`` (features/shock.py) — álgebra conferível no papel.

Janela sintética curta (soja/MT, 1–10 de dezembro) com dois municípios de pesos PAM 0,75/0,25
e climatologia de 10 safras com acumulados 1..10 mm (média 5,5; desvio amostral 3,0277). Cada
teste ancora um pedaço do contrato congelado: convenção de sinal (seca ⇒ Shock positivo), PIT
(corte segue o ``avail_date``, não o relógio), mesmo trecho por deslocamento, mínimo de 10
safras, cobertura diária obrigatória, peso CONAB da safra anterior (nunca a corrente) e
renormalização nacional sobre janelas já iniciadas.
"""

import numpy as np
import pandas as pd
import pytest

from quantagro.features.shock import (
    FINAL_LAG_DAYS,
    PRELIM_LAG_DAYS,
    conab_uf_weights,
    shock_asof,
    stamp_municipal_panel,
    uf_shock_asof,
)
from quantagro.features.shock_spec import CropRegionWindow
from quantagro.ingest.pam import pam_weights_asof
from quantagro.validate.pit import available_asof

# Janela sintética: soja/MT, 1–10 de dezembro do primeiro ano da safra.
SOY_MT = CropRegionWindow("soy", "SOJA", "UNICA", "MT", "R1-R6", 12, 1, 0, 12, 10, 0)
# PR entra depois (1–10 de janeiro) para o teste de cobertura nacional parcial.
SOY_PR = CropRegionWindow("soy", "SOJA", "UNICA", "PR", "R1-R6", 1, 1, 1, 1, 10, 1)

M1, M2 = "5100102", "5103403"  # pesos PAM 0,75 / 0,25
PR1 = "4104808"

ANO = "2015/16"
FIRST_CLIM_YEAR = 2005  # 2005..2014 → exatamente as 10 safras mínimas
CLIM_MEAN, CLIM_STD = 5.5, float(np.std(np.arange(1, 11), ddof=1))


def _municipal_rows(kind, start, days, values):
    """Linhas do painel municipal: `values` = {código: mm/dia} constante no trecho."""
    dates = pd.date_range(start, periods=days, freq="D")
    return [
        {
            "ref_date": d,
            "kind": kind,
            "uf": code[:2].replace("51", "MT").replace("41", "PR"),
            "municipality_code": code,
            "precip_mm": float(mm),
            "n_cells": 10,
            "n_valid_cells": 10,
        }
        for d in dates
        for code, mm in values.items()
    ]


def _municipal_panel(current=None, ufs=("MT",)):
    """Painel completo: climatologia final 2005..2014 (acumulado = ano−2004) + prelim corrente."""
    rows = []
    values_mt = {M1: 1.0, M2: 1.0}
    values_pr = {PR1: 1.0}
    for year in range(FIRST_CLIM_YEAR, 2015):
        per_day = (year - 2004) / 10.0  # acumulado do trecho de 10 dias = year − 2004
        if "MT" in ufs:
            rows += _municipal_rows("final", f"{year}-12-01", 10, {k: per_day for k in values_mt})
        if "PR" in ufs:
            rows += _municipal_rows(
                "final", f"{year + 1}-01-01", 10, {k: per_day for k in values_pr}
            )
    if current is not None:
        if "MT" in ufs:
            rows += _municipal_rows("prelim", "2015-12-01", 10, {M1: current, M2: current})
        if "PR" in ufs:
            rows += _municipal_rows("prelim", "2016-01-01", 10, {PR1: current})
    return stamp_municipal_panel(pd.DataFrame(rows))


def _pam_panel(ufs=("MT",)):
    rows = []
    quantities = {M1: 3000.0, M2: 1000.0, PR1: 500.0}
    for code, qty in quantities.items():
        uf = "MT" if code.startswith("51") else "PR"
        if uf not in ufs:
            continue
        rows.append(
            {
                "ref_date": pd.Timestamp("2014-12-31"),
                "avail_date": pd.Timestamp("2015-09-01"),
                "ref_year": 2014,
                "crop": "soy",
                "uf": uf,
                "municipality_code": code,
                "municipality_name": code,
                "quantity_tonnes": qty,
                "value_status": "observed",
            }
        )
    return pd.DataFrame(rows)


def _conab_panel():
    """Safra anterior (2014/15) e corrente (2015/16) — só a anterior pode pesar."""
    rows = []
    for ano, lev, avail, prod in [
        ("2014/15", 11, "2015-08-10", {"MT": 100.0, "PR": 100.0}),  # não é o último
        ("2014/15", 12, "2015-09-10", {"MT": 30000.0, "PR": 10000.0}),
        ("2015/16", 1, "2015-10-08", {"MT": 1.0, "PR": 999999.0}),  # corrente: proibida
    ]:
        for uf, p in prod.items():
            rows.append(
                {
                    "ano_agricola": ano,
                    "safra": "UNICA",
                    "uf": uf,
                    "produto": "SOJA",
                    "id_levantamento": lev,
                    "producao_mil_t": p,
                    "ref_date": pd.Timestamp(avail),
                    "avail_date": pd.Timestamp(avail),
                }
            )
    return pd.DataFrame(rows)


class TestStamp:
    def test_lag_por_produto(self):
        panel = _municipal_panel(current=1.0)
        prelim = panel[panel["kind"] == "prelim"]
        final = panel[panel["kind"] == "final"]
        assert ((prelim["avail_date"] - prelim["ref_date"]).dt.days == PRELIM_LAG_DAYS).all()
        assert ((final["avail_date"] - final["ref_date"]).dt.days == FINAL_LAG_DAYS).all()

    def test_kind_desconhecido_falha(self):
        bad = pd.DataFrame(_municipal_rows("raw", "2015-12-01", 1, {M1: 1.0}))
        with pytest.raises(ValueError, match="kind desconhecido"):
            stamp_municipal_panel(bad)


class TestConabUfWeights:
    def test_usa_ultimo_levantamento_da_safra_anterior(self):
        w = conab_uf_weights(_conab_panel(), SOY_MT, ["MT", "PR"], ANO, "2015-12-20")
        assert w["MT"] == pytest.approx(0.75)
        assert w["PR"] == pytest.approx(0.25)

    def test_safra_corrente_nunca_pesa(self):
        # se a corrente (PR=999999) vazasse, o peso do PR explodiria
        w = conab_uf_weights(_conab_panel(), SOY_MT, ["MT", "PR"], ANO, "2015-12-20")
        assert w["PR"] < 0.5

    def test_pit_no_calendario_conab(self):
        # antes do 12º levantamento (avail 10/09), vale o 11º (100/100 → 50/50)
        w = conab_uf_weights(_conab_panel(), SOY_MT, ["MT", "PR"], ANO, "2015-09-01")
        assert w["MT"] == pytest.approx(0.5)

    def test_uf_sem_producao_falha(self):
        with pytest.raises(ValueError, match="sem produção CONAB"):
            conab_uf_weights(_conab_panel(), SOY_MT, ["MT", "GO"], ANO, "2015-12-20")


class TestUfShock:
    def _shock(self, current, t="2015-12-20"):
        panel = _municipal_panel(current=current)
        visible = available_asof(panel, t)
        weights = pam_weights_asof(_pam_panel(), t)
        return uf_shock_asof(t, ANO, SOY_MT, visible, weights, FIRST_CLIM_YEAR)

    def test_z_conferido_no_papel(self):
        # corrente 1,25 mm/dia → acumulado UF = 12,5; climatologia 1..10 → z = (12,5−5,5)/3,0277
        row = self._shock(current=1.25)
        assert row["status"] == "ok"
        assert row["elapsed_days"] == 9  # janela completa (10 dias, inclusiva)
        assert row["precip_mm"] == pytest.approx(12.5)
        assert row["clim_mean_mm"] == pytest.approx(CLIM_MEAN)
        assert row["clim_std_mm"] == pytest.approx(CLIM_STD)
        assert row["z"] == pytest.approx((12.5 - CLIM_MEAN) / CLIM_STD)
        assert row["shock"] == pytest.approx(-(12.5 - CLIM_MEAN) / CLIM_STD)

    def test_convencao_de_sinal_seca_e_estresse_positivo(self):
        seco = self._shock(current=0.0)
        chuvoso = self._shock(current=2.0)
        assert seco["shock"] > 0 > chuvoso["shock"]

    def test_pit_corta_pelo_avail_e_usa_o_mesmo_trecho(self):
        # em 12/12, só ref ≤ 05/12 é visível (lag 7): trecho de 5 dias, clima 0,5..5,0
        row = self._shock(current=1.25, t="2015-12-12")
        assert row["elapsed_days"] == 4
        assert row["precip_mm"] == pytest.approx(1.25 * 5)
        assert row["clim_mean_mm"] == pytest.approx(CLIM_MEAN / 2)
        assert row["clim_std_mm"] == pytest.approx(CLIM_STD / 2)

    def test_antes_da_janela_nao_ha_shock(self):
        row = self._shock(current=1.0, t="2015-12-05")  # lag 7 ⇒ nada da janela visível
        assert row["status"] == "window_not_started"
        assert np.isnan(row["shock"])

    def test_menos_de_dez_safras_falha(self):
        panel = _municipal_panel(current=1.0)
        visible = available_asof(panel, "2015-12-20")
        weights = pam_weights_asof(_pam_panel(), "2015-12-20")
        with pytest.raises(ValueError, match="mínimo 10"):
            uf_shock_asof("2015-12-20", ANO, SOY_MT, visible, weights, 2006)

    def test_buraco_de_cobertura_falha_alto(self):
        panel = _municipal_panel(current=1.0)
        hole = panel[
            ~((panel["kind"] == "prelim") & (panel["ref_date"] == pd.Timestamp("2015-12-03")))
        ]
        visible = available_asof(hole, "2015-12-20")
        weights = pam_weights_asof(_pam_panel(), "2015-12-20")
        with pytest.raises(ValueError, match="sem cobertura diária"):
            uf_shock_asof("2015-12-20", ANO, SOY_MT, visible, weights, FIRST_CLIM_YEAR)

    def test_municipio_com_peso_fora_do_painel_falha(self):
        panel = _municipal_panel(current=1.0)
        panel = panel[panel["municipality_code"] != M2]
        visible = available_asof(panel, "2015-12-20")
        weights = pam_weights_asof(_pam_panel(), "2015-12-20")
        with pytest.raises(ValueError, match="fora do painel municipal"):
            uf_shock_asof("2015-12-20", ANO, SOY_MT, visible, weights, FIRST_CLIM_YEAR)


class TestShockAsof:
    def test_nacional_pondera_pelo_conab_anterior(self):
        panel = _municipal_panel(current=1.25, ufs=("MT", "PR"))
        out = shock_asof(
            "2016-01-20",
            ANO,
            panel,
            _pam_panel(ufs=("MT", "PR")),
            _conab_panel(),
            FIRST_CLIM_YEAR,
            windows=(SOY_MT, SOY_PR),
        )
        uf = out[out["level"] == "uf"].set_index("uf")
        nat = out[out["level"] == "national"].iloc[0]
        # ambos os trechos completos e com a mesma climatologia ⇒ mesmo z; pesos 0,75/0,25
        expected = 0.75 * uf.loc["MT", "shock"] + 0.25 * uf.loc["PR", "shock"]
        assert nat["shock"] == pytest.approx(expected)
        assert nat["uf_coverage_weight"] == pytest.approx(1.0)
        assert uf.loc["MT", "national_weight"] == pytest.approx(0.75)

    def test_nacional_renormaliza_sobre_janelas_iniciadas(self):
        panel = _municipal_panel(current=1.25, ufs=("MT", "PR"))
        out = shock_asof(
            "2015-12-20",  # PR (janeiro) ainda não começou
            ANO,
            panel,
            _pam_panel(ufs=("MT", "PR")),
            _conab_panel(),
            FIRST_CLIM_YEAR,
            windows=(SOY_MT, SOY_PR),
        )
        uf = out[out["level"] == "uf"].set_index("uf")
        nat = out[out["level"] == "national"].iloc[0]
        assert uf.loc["PR", "status"] == "window_not_started"
        assert nat["uf_coverage_weight"] == pytest.approx(0.75)
        assert nat["shock"] == pytest.approx(uf.loc["MT", "shock"])  # renormalizado

    def test_painel_sem_carimbo_falha(self):
        panel = _municipal_panel(current=1.0).drop(columns=["avail_date"])
        with pytest.raises(ValueError, match="avail_date"):
            shock_asof(
                "2015-12-20",
                ANO,
                panel,
                _pam_panel(),
                _conab_panel(),
                FIRST_CLIM_YEAR,
                windows=(SOY_MT,),
            )
