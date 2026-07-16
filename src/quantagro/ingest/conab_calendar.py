"""Calendário curado de divulgação dos levantamentos da CONAB (risco R10).

O `Levantamento*.txt` não traz a data em que cada levantamento foi divulgado — só o
número. Este módulo é o mapa `(dataset, ano_agricola, id_levantamento) → data de
divulgação`, levantado **ano a ano de fontes primárias, sem nenhuma interpolação**
(R10: errar por poucos dias contamina o estudo de evento).

Regras de curadoria (mesma disciplina de `ingest/events_manual.py`):

1. Cada data entra com a fonte anotada no comentário da safra. Fontes usadas:
   - [gov.br]   listing oficial atual (gov.br/conab, "Publicado em") — confiável para
                itens criados já no site novo (pós-migração de nov/2023) e para as
                safras em que as datas variam organicamente E batem com o calendário;
   - [cal20XX]  PDF oficial "Calendário de Divulgação de Safras" do ano (via Wayback) —
                data *planejada*; vira evidência forte quando outra fonte confirma;
   - [K2]       página Joomla antiga da CONAB (snapshots do Wayback) — data de
                publicação do item; tempo-real é forte, item importado na migração
                de ~mar/2018 NÃO é confiável (descartado quando conflita);
   - [AMPA]     espelho same-day da AMPA (timestamp de download no nome do arquivo,
                validado 7/7 contra datas conhecidas);
   - [upload]   timestamp de upload do PDF no site antigo da CONAB (OlalaCMS);
   - [news]     notícia datada do mesmo dia (Agência Brasil, novacana, udop, Cecafé,
                ConabCast — o slug do ConabCast carrega a data).
2. Uma data só entra sem ressalva com **duas fontes independentes concordando** ou uma
   fonte oficial de data efetiva (não planejada). Quando só existe a data planejada, a
   entrada existe mas está marcada no comentário — melhor do que buraco, e o conflito
   conhecido de maior magnitude observado foi de ~1 semana (cana 1º/2021-22).
3. Divergência entre fontes se resolve por evidência (notícia do dia vence data
   nominal); irresolvida, vale a **mais tardia** (atrasar sinal nunca cria lookahead).
4. Descoberta que invalide uma data → corrigir AQUI, com a fonte nova no comentário;
   o histórico do git é a trilha de auditoria.

Fatos que o mapa carrega (não são bugs):
- Café 2020 não tem 2º levantamento (suspenso na pandemia) — o painel também não tem.
- Grãos "ano puro" (culturas de inverno) e `id_levantamento == 99` ficam fora do mapa
  ⇒ `attach_avail_date` falha alto se aparecerem (filtrar antes é decisão consciente).
- O listing gov.br da safra 2022/23 de grãos exibe datas nominais falsas (artefato da
  migração — todas "dia 10", com sábados); as datas aqui vêm de K2 + calendário (12/12
  concordantes).
"""

from __future__ import annotations

import pandas as pd

from quantagro.validate.pit import AVAIL_COL, REF_COL

# ---------------------------------------------------------------------------
# GRÃOS — 12 levantamentos por ano-safra (out → set). Painel começa em 2017/18.
# ---------------------------------------------------------------------------
_GRAOS: dict[str, dict[int, str]] = {
    # 1º-3º [cal2017+AMPA ✓✓]; 4º [upload 09h02 + cal2017 + AMPA ✓✓✓]; 1º também
    # [upload 09h01]. 5º-7º [AMPA] (7º confirmado por news MAPA de 10/04; o K2 11/04
    # é item importado na migração, descartado). 8º,10º-12º [K2+AMPA ✓✓]; 9º [K2]
    # (única data desta safra com fonte única — AMPA não arquivou jun/2018).
    "2017/18": {
        1: "2017-10-10",
        2: "2017-11-09",
        3: "2017-12-12",
        4: "2018-01-11",
        5: "2018-02-08",
        6: "2018-03-08",
        7: "2018-04-10",
        8: "2018-05-10",
        9: "2018-06-12",
        10: "2018-07-10",
        11: "2018-08-09",
        12: "2018-09-11",
    },
    # [K2 tempo-real em 3 snapshots consistentes (dez/18, jan/19, nov/19)];
    # 1º,2º,7º também [AMPA ✓✓]; 5º também [news Agência Brasil 12/02/2019 ✓✓].
    "2018/19": {
        1: "2018-10-11",
        2: "2018-11-08",
        3: "2018-12-11",
        4: "2019-01-10",
        5: "2019-02-12",
        6: "2019-03-12",
        7: "2019-04-11",
        8: "2019-05-09",
        9: "2019-06-11",
        10: "2019-07-11",
        11: "2019-08-08",
        12: "2019-09-10",
    },
    # [K2 tempo-real (snapshots jun/20 e jan/21) + gov.br ✓✓ nas 12].
    "2019/20": {
        1: "2019-10-10",
        2: "2019-11-13",
        3: "2019-12-10",
        4: "2020-01-08",
        5: "2020-02-11",
        6: "2020-03-10",
        7: "2020-04-09",
        8: "2020-05-12",
        9: "2020-06-09",
        10: "2020-07-08",
        11: "2020-08-11",
        12: "2020-09-10",
    },
    # 1º-3º [K2 tempo-real + gov.br ✓✓]; 4º-12º [cal2021 + gov.br ✓✓].
    "2020/21": {
        1: "2020-10-08",
        2: "2020-11-10",
        3: "2020-12-10",
        4: "2021-01-13",
        5: "2021-02-11",
        6: "2021-03-11",
        7: "2021-04-08",
        8: "2021-05-12",
        9: "2021-06-10",
        10: "2021-07-08",
        11: "2021-08-10",
        12: "2021-09-09",
    },
    # 1º-3º [cal2021 + gov.br ✓✓]; 4º-12º [cal2022 + gov.br ✓✓]. (O K2 do 9º diz
    # 01/07/22 — republicação tardia do item; planejado + listing concordam em 08/06.)
    "2021/22": {
        1: "2021-10-07",
        2: "2021-11-11",
        3: "2021-12-09",
        4: "2022-01-11",
        5: "2022-02-10",
        6: "2022-03-10",
        7: "2022-04-07",
        8: "2022-05-12",
        9: "2022-06-08",
        10: "2022-07-07",
        11: "2022-08-11",
        12: "2022-09-08",
    },
    # [K2 tempo-real (snapshots fev/23 e set/23) + cal2022/cal2023, 12/12 ✓✓].
    # O listing gov.br desta safra é o artefato de migração (datas nominais "dia 10").
    "2022/23": {
        1: "2022-10-06",
        2: "2022-11-09",
        3: "2022-12-08",
        4: "2023-01-12",
        5: "2023-02-08",
        6: "2023-03-09",
        7: "2023-04-13",
        8: "2023-05-11",
        9: "2023-06-13",
        10: "2023-07-13",
        11: "2023-08-10",
        12: "2023-09-06",
    },
    # 1º-3º [cal2023 + gov.br ✓✓]; 4º [news cal2024 ("atualizada" de 04→10/jan) +
    # gov.br ✓✓]; 12º [news cal2024 + gov.br ✓✓]; 5º-11º [gov.br] (era pós-migração,
    # datas orgânicas; PDF cal2024 indisponível para dupla checagem — Wayback trunca).
    "2023/24": {
        1: "2023-10-10",
        2: "2023-11-09",
        3: "2023-12-07",
        4: "2024-01-10",
        5: "2024-02-08",
        6: "2024-03-12",
        7: "2024-04-11",
        8: "2024-05-14",
        9: "2024-06-13",
        10: "2024-07-11",
        11: "2024-08-13",
        12: "2024-09-12",
    },
    # 4º-12º [cal2025 + gov.br, 9/9 ✓✓]; 1º-3º [gov.br] (itens nativos do site novo).
    "2024/25": {
        1: "2024-10-15",
        2: "2024-11-14",
        3: "2024-12-12",
        4: "2025-01-14",
        5: "2025-02-13",
        6: "2025-03-13",
        7: "2025-04-10",
        8: "2025-05-15",
        9: "2025-06-12",
        10: "2025-07-10",
        11: "2025-08-14",
        12: "2025-09-11",
    },
    # 1º-4º [cal2025 + gov.br ✓✓]; 5º-10º [gov.br] (site vivo; 10º divulgado em
    # 14/07/2026, dois dias antes desta escrita).
    "2025/26": {
        1: "2025-10-14",
        2: "2025-11-13",
        3: "2025-12-11",
        4: "2026-01-15",
        5: "2026-02-12",
        6: "2026-03-13",
        7: "2026-04-14",
        8: "2026-05-14",
        9: "2026-06-11",
        10: "2026-07-14",
    },
}

# ---------------------------------------------------------------------------
# CAFÉ — 4 levantamentos por ano civil (jan, mai, set, dez; 4º de 2024 em diante
# deslizou para janeiro do ano seguinte). Painel começa em 2017.
# ---------------------------------------------------------------------------
_CAFE: dict[str, dict[int, str]] = {
    # [cal2017] — só data planejada (nenhuma fonte de data efetiva sobreviveu).
    "2017": {1: "2017-01-17", 2: "2017-05-18", 3: "2017-09-21", 4: "2017-12-21"},
    # 1º [news Agência Brasil 18/01/2018 + cal2017 ✓✓]; 2º-4º [K2 tempo-quase-real].
    "2018": {1: "2018-01-18", 2: "2018-05-17", 3: "2018-09-18", 4: "2018-12-18"},
    # [K2 tempo-quase-real (snapshot jul/2020)].
    "2019": {1: "2019-01-17", 2: "2019-05-16", 3: "2019-09-17", 4: "2019-12-17"},
    # [K2]. SEM 2º levantamento — suspenso na pandemia (ausente também do painel).
    "2020": {1: "2020-01-16", 3: "2020-09-22", 4: "2020-12-17"},
    # [K2 + cal2021, 4/4 ✓✓].
    "2021": {1: "2021-01-21", 2: "2021-05-25", 3: "2021-09-21", 4: "2021-12-16"},
    # [K2 + cal2022, 4/4 ✓✓].
    "2022": {1: "2022-01-18", 2: "2022-05-19", 3: "2022-09-20", 4: "2022-12-15"},
    # [K2 + cal2023 ✓✓]; 4º também [gov.br ✓✓].
    "2023": {1: "2023-01-19", 2: "2023-05-18", 3: "2023-09-20", 4: "2023-12-14"},
    # 1º [news cal2024 — planejado]; 2º [ConabCast slug 2024-05-23 + Cecafé ✓✓ — o
    # gov.br mostra 25/05, um sábado: artefato, descartado]; 3º [gov.br + news
    # cal2024 ✓✓]; 4º deslizou para janeiro [gov.br + news cal2024 + ConabCast ✓✓✓].
    "2024": {1: "2024-01-18", 2: "2024-05-23", 3: "2024-09-19", 4: "2025-01-21"},
    # [cal2025 + gov.br, 4/4 ✓✓].
    "2025": {1: "2025-01-28", 2: "2025-05-06", 3: "2025-09-04", 4: "2025-12-04"},
    # 1º [cal2025 + gov.br ✓✓]; 2º [gov.br] (site vivo).
    "2026": {1: "2026-02-05", 2: "2026-05-21"},
}

# ---------------------------------------------------------------------------
# CANA — 4 levantamentos por ano-safra (abr, ago, nov/dez, abr seguinte).
# Painel começa em 2017/18. O 4º de uma safra e o 1º da seguinte saem próximos
# (às vezes no mesmo dia/boletim de abril).
# ---------------------------------------------------------------------------
_CANA: dict[str, dict[int, str]] = {
    # [cal2017] — só data planejada, como no café 2017.
    "2017/18": {1: "2017-04-18", 2: "2017-08-24", 3: "2017-12-19", 4: "2018-04-17"},
    # [K2 tempo-quase-real (snapshot jan/2021)].
    "2018/19": {1: "2018-05-03", 2: "2018-08-21", 3: "2018-12-20", 4: "2019-04-23"},
    # [K2 tempo-quase-real].
    "2019/20": {1: "2019-05-07", 2: "2019-08-22", 3: "2019-12-19", 4: "2020-04-23"},
    # 1º-3º [K2 tempo-real]; 4º [K2] — atrasado (planejado 20/abr no cal2021) e
    # publicado junto com o 1º da safra seguinte em 18/05/2021.
    "2020/21": {1: "2020-05-05", 2: "2020-08-20", 3: "2020-12-15", 4: "2021-05-18"},
    # 1º [K2] — adiado (planejado 29/abr no cal2021); 2º-3º [K2 + cal2021 ✓✓];
    # 4º [K2 + cal2022 ✓✓].
    "2021/22": {1: "2021-05-18", 2: "2021-08-19", 3: "2021-11-23", 4: "2022-04-20"},
    # 1º [K2 em 2 snapshots + news novacana de 27/04 ✓✓✓ — cal2022 planejava 28];
    # 2º [K2 + cal2022 ✓✓]; 3º [K2] — adiado (planejado 22/dez); 4º [K2] (cal2023
    # planejava 19/abr; K2 20/abr, mais tardia, vale a regra 3).
    "2022/23": {1: "2022-04-27", 2: "2022-08-19", 3: "2022-12-27", 4: "2023-04-20"},
    # 1º-2º [K2 + cal2023 ✓✓]; 3º [news udop datada 29/11 + cal2023 ✓✓];
    # 4º [gov.br + news cal2024 ✓✓].
    "2023/24": {1: "2023-04-26", 2: "2023-08-17", 3: "2023-11-29", 4: "2024-04-18"},
    # [gov.br]; 1º-3º também [news cal2024 ✓✓]; 4º também [cal2025 ✓✓].
    "2024/25": {1: "2024-04-25", 2: "2024-08-22", 3: "2024-11-28", 4: "2025-04-17"},
    # 1º-3º [cal2025 + gov.br ✓✓]; 4º [gov.br] (cal2025 planejava 16/abr; o listing
    # vivo diz 17/abr — efetiva e mais tardia, vale a regra 3).
    "2025/26": {1: "2025-04-29", 2: "2025-08-26", 3: "2025-11-04", 4: "2026-04-17"},
    # [gov.br] (site vivo).
    "2026/27": {1: "2026-04-28"},
}

_CALENDARIO = {"graos": _GRAOS, "cafe": _CAFE, "cana": _CANA}


def conab_calendar(dataset: str) -> pd.DataFrame:
    """O calendário curado de um dataset como DataFrame arrumado.

    Colunas: `ano_agricola`, `id_levantamento`, `avail_date`. É a materialização do
    mapa R10 — consumidores fazem o join via `attach_avail_date`, não na mão.
    """
    if dataset not in _CALENDARIO:
        raise ValueError(f"dataset desconhecido: {dataset!r} (use {sorted(_CALENDARIO)})")
    rows = [
        (ano, lev, data) for ano, levs in _CALENDARIO[dataset].items() for lev, data in levs.items()
    ]
    out = pd.DataFrame(rows, columns=["ano_agricola", "id_levantamento", AVAIL_COL])
    out[AVAIL_COL] = pd.to_datetime(out[AVAIL_COL])
    return out


def attach_avail_date(df: pd.DataFrame, dataset: str) -> pd.DataFrame:
    """Carimba `ref_date`/`avail_date` num painel parseado, via o calendário curado.

    Toda linha precisa de data: um `(ano_agricola, id_levantamento)` fora do calendário
    é erro — cobre lev 99, culturas de inverno (ano "puro" de grãos) e safras ainda não
    curadas. Silêncio aqui viraria lookahead ou perda de dado sem registro; quem quiser
    usar só o subconjunto coberto filtra ANTES, como decisão explícita.

    Para um levantamento, a estimativa "nasce pública": `ref_date = avail_date` (a data
    da divulgação). O objeto de estudo é a *revisão entre* levantamentos, e essa é
    datada pelo próprio calendário.
    """
    cal = conab_calendar(dataset)
    out = df.merge(cal, on=["ano_agricola", "id_levantamento"], how="left")
    sem_data = out[AVAIL_COL].isna()
    if sem_data.any():
        faltando = sorted(
            set(
                zip(
                    out.loc[sem_data, "ano_agricola"],
                    out.loc[sem_data, "id_levantamento"],
                    strict=True,
                )
            )
        )
        raise ValueError(
            f"{len(faltando)} chave(s) (ano_agricola, id_levantamento) sem data no "
            f"calendário curado: {faltando[:5]}... Filtre linhas fora do escopo antes "
            "(lev 99, culturas de inverno) ou complete o calendário com fonte primária."
        )
    out[REF_COL] = out[AVAIL_COL]
    return out
