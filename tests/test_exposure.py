"""Testes do registro fundamentalista real e de suas travas point-in-time."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from quantagro.features.exposure import (
    PRIMARY_CROPS,
    exposure_asof,
    exposure_matrix_asof,
    load_exposure_registry,
)

REGISTRY_PATH = Path("data/reference/exposure_fundamental_v1.json")


@pytest.fixture
def payload():
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def registry():
    return load_exposure_registry(REGISTRY_PATH)


def _write_payload(tmp_path, payload):
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class TestRealRegistry:
    def test_loads_one_row_per_vintage_and_crop(self, registry):
        assert len(registry) == 10
        assert set(registry["crop"]) == set(PRIMARY_CROPS)
        assert registry["exposure_id"].nunique() == 5

    def test_sign_and_l1_norm_match_direction_and_materiality(self, registry):
        grouped = registry.groupby("exposure_id", sort=False)
        for _, vintage in grouped:
            assert np.sign(vintage["exposure"]).eq(vintage["direction"]).all()
            assert vintage["exposure"].abs().sum() == pytest.approx(vintage["materiality"].iloc[0])

    def test_known_agro_weights_are_reproducible(self, registry):
        agro = registry[registry["exposure_id"] == "agro3_2014_form20f"].set_index("crop")
        assert agro.loc["soy", "exposure"] == pytest.approx(52_457 / (52_457 + 9_965))
        assert agro.loc["corn_second", "exposure"] == pytest.approx(9_965 / (52_457 + 9_965))

    def test_before_first_filing_no_company_is_backfilled(self, registry):
        assert exposure_asof(registry, "2014-03-30").empty

    def test_asof_2015_contains_only_information_then_available(self, registry):
        matrix = exposure_matrix_asof(registry, "2015-12-31")
        assert list(matrix.index) == ["AGRO3", "BRFS3", "JBSS3"]
        assert (matrix.loc["AGRO3"] > 0).all()
        assert (matrix.loc[["BRFS3", "JBSS3"]] < 0).all().all()

    def test_brf_materiality_updates_only_after_2018_filing(self, registry):
        before = exposure_asof(registry, "2018-04-26")
        after = exposure_asof(registry, "2018-04-27")
        assert before.loc[before["ticker"] == "BRFS3", "materiality"].iloc[0] == 0.25
        assert after.loc[after["ticker"] == "BRFS3", "materiality"].iloc[0] == 0.5

    def test_matrix_after_all_vintages_has_two_long_and_two_short_names(self, registry):
        matrix = exposure_matrix_asof(registry, "2019-01-01")
        assert list(matrix.index) == ["AGRO3", "BRFS3", "JBSS3", "SLCE3"]
        assert (matrix.loc[["AGRO3", "SLCE3"]] > 0).all().all()
        assert (matrix.loc[["BRFS3", "JBSS3"]] < 0).all().all()
        assert list(matrix.columns) == list(PRIMARY_CROPS)

    def test_future_vintage_does_not_rewrite_past(self, registry):
        baseline = exposure_matrix_asof(registry, "2017-01-01")
        future = registry[registry["exposure_id"] == "agro3_2014_form20f"].copy()
        future["exposure_id"] = "agro3_future"
        future["ref_date"] = pd.Timestamp("2025-06-30")
        future["avail_date"] = pd.Timestamp("2025-10-31")
        future["exposure"] = future["exposure"] * 0.5
        expanded = pd.concat([registry, future], ignore_index=True)
        pd.testing.assert_frame_equal(baseline, exposure_matrix_asof(expanded, "2017-01-01"))


class TestRegistryTripwires:
    @pytest.mark.parametrize("materiality", [0.1, 0.75, 1.1, 0.0])
    def test_rejects_invalid_or_ineligible_materiality(self, tmp_path, payload, materiality):
        payload["vintages"][0]["materiality"] = materiality
        with pytest.raises(ValueError, match="materiality"):
            load_exposure_registry(_write_payload(tmp_path, payload))

    def test_rejects_missing_crop(self, tmp_path, payload):
        del payload["vintages"][0]["crop_weights"]["corn_second"]
        with pytest.raises(ValueError, match="crop_weights"):
            load_exposure_registry(_write_payload(tmp_path, payload))

    def test_rejects_unknown_crop(self, tmp_path, payload):
        payload["vintages"][0]["crop_weights"]["wheat"] = 0.0
        with pytest.raises(ValueError, match="crop_weights"):
            load_exposure_registry(_write_payload(tmp_path, payload))

    def test_rejects_weights_that_do_not_sum_one(self, tmp_path, payload):
        payload["vintages"][0]["crop_weights"] = {"soy": 0.4, "corn_second": 0.4}
        with pytest.raises(ValueError, match="não somam 1"):
            load_exposure_registry(_write_payload(tmp_path, payload))

    def test_rejects_negative_weight(self, tmp_path, payload):
        payload["vintages"][0]["crop_weights"] = {"soy": 1.1, "corn_second": -0.1}
        with pytest.raises(ValueError, match="negativo"):
            load_exposure_registry(_write_payload(tmp_path, payload))

    def test_rejects_ref_after_availability(self, tmp_path, payload):
        payload["vintages"][0]["ref_date"] = "2020-01-01"
        with pytest.raises(ValueError, match="ref_date"):
            load_exposure_registry(_write_payload(tmp_path, payload))

    def test_rejects_duplicate_id(self, tmp_path, payload):
        payload["vintages"].append(copy.deepcopy(payload["vintages"][0]))
        with pytest.raises(ValueError, match="exposure_id duplicado"):
            load_exposure_registry(_write_payload(tmp_path, payload))

    def test_rejects_same_ticker_and_availability(self, tmp_path, payload):
        duplicate = copy.deepcopy(payload["vintages"][0])
        duplicate["exposure_id"] = "different_id"
        payload["vintages"].append(duplicate)
        with pytest.raises(ValueError, match="mesma avail_date"):
            load_exposure_registry(_write_payload(tmp_path, payload))

    def test_rejects_non_https_source(self, tmp_path, payload):
        payload["vintages"][0]["source"]["url"] = "http://example.com/report"
        with pytest.raises(ValueError, match="HTTPS"):
            load_exposure_registry(_write_payload(tmp_path, payload))

    def test_rejects_non_primary_crop_contract(self, tmp_path, payload):
        payload["crops"] = ["corn_second", "soy"]
        with pytest.raises(ValueError, match="crops deve ser exatamente"):
            load_exposure_registry(_write_payload(tmp_path, payload))


def test_asof_requires_canonical_columns():
    with pytest.raises(ValueError, match="colunas obrigatórias"):
        exposure_asof(pd.DataFrame({"ticker": ["AGRO3"]}), "2020-01-01")


HPRIME_PATH = Path("data/reference/exposure_hprime_v1.json")


class TestHPrimeRegistry:
    """Matriz re-derivada sob H′ de quantidade (D-061). O v1 de preço fica intacto."""

    @pytest.fixture
    def hprime(self):
        return load_exposure_registry(HPRIME_PATH)

    def test_loads_and_validates(self, hprime):
        assert len(hprime) == 10
        assert hprime["exposure_id"].nunique() == 5

    def test_materiality_reductions_of_d061(self, hprime):
        # AGRO3 desce de 1,00 (preço) para 0,50 (quantidade: grão minoria, parte fora do Shock).
        agro = hprime[hprime["exposure_id"] == "agro3_2014_form20f"]
        assert agro["materiality"].iloc[0] == pytest.approx(0.5)
        # JBSS3 desce de 0,50 para 0,25 (só Seara/BR dentro do Shock).
        jbs = hprime[hprime["exposure_id"] == "jbss3_2014_annual_report"]
        assert jbs["materiality"].iloc[0] == pytest.approx(0.25)

    def test_processors_no_longer_identical(self, hprime):
        # O colapso vinha de BRFS3 ≡ JBSS3. Sob H′ a materialidade do último cai ⇒ vetores diferem.
        latest = exposure_matrix_asof(hprime, "2019-01-07")
        assert not np.allclose(latest.loc["BRFS3"].to_numpy(), latest.loc["JBSS3"].to_numpy())

    def test_directions_and_crop_weights_unchanged_vs_price_matrix(self, hprime, registry):
        # D-061 mexe só na materialidade: direção e cesta de cultura são idênticas ao v1.
        for col in ("direction", "crop_weight"):
            merged = registry.merge(hprime, on=["exposure_id", "crop"], suffixes=("_v1", "_hp"))
            assert (merged[f"{col}_v1"] == merged[f"{col}_hp"]).all()
