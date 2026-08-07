"""Build the repository's public SVG figures from versioned result data.

No figure is a crop of the five-page report. The charts below are a separate,
reproducible reading layer for GitHub. They use only the standard library and
the compact JSON/CSV artifacts committed under ``results/data``.
"""

# SVG fragments and chart copy are deliberately kept as readable literals.
# ruff: noqa: E501

from __future__ import annotations

import json
import math
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "results/data"
OUT = ROOT / "results/figures"

PAPER = "#F6F3EA"
WHITE = "#FFFFFF"
INK = "#17201F"
MUTED = "#5E6965"
GRID = "#D9DED9"
GREEN = "#123B2A"
GREEN_2 = "#2C6B4B"
BLUE = "#2468C4"
BLUE_2 = "#7BA6DC"
AMBER = "#F2C230"
RED = "#B85C42"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def pct(value: float, decimals: int = 1, signed: bool = True) -> str:
    sign = "+" if signed and value > 0 else ""
    return f"{sign}{value * 100:.{decimals}f}%"


def num(value: float, decimals: int = 2) -> str:
    return f"{value:.{decimals}f}"


def text(x: float, y: float, value: str, cls: str = "body", anchor: str = "start") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" text-anchor="{anchor}">{escape(value)}</text>'
    )


def multiline(
    x: float,
    y: float,
    lines: list[str],
    cls: str = "body",
    gap: float = 22,
    anchor: str = "start",
) -> str:
    tspans = "".join(
        f'<tspan x="{x:.1f}" dy="{0 if i == 0 else gap}">{escape(line)}</tspan>'
        for i, line in enumerate(lines)
    )
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" text-anchor="{anchor}">{tspans}</text>'


def start_svg(title: str, description: str, height: int = 680) -> list[str]:
    return [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 '
        f'{height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{escape(title)}</title>',
        f'<desc id="desc">{escape(description)}</desc>',
        """<style>
          text { font-family: 'IBM Plex Sans', Inter, Arial, sans-serif; fill: #17201F; }
          .display { font-family: Fraunces, Georgia, serif; font-size: 34px; font-weight: 650; }
          .title { font-size: 22px; font-weight: 650; }
          .subtitle { font-size: 16px; fill: #5E6965; }
          .body { font-size: 16px; }
          .small { font-size: 13px; fill: #5E6965; }
          .micro { font-family: 'IBM Plex Mono', monospace; font-size: 11px; fill: #5E6965; }
          .number { font-family: Fraunces, Georgia, serif; font-size: 28px; font-weight: 650; }
          .label { font-family: 'IBM Plex Mono', monospace; font-size: 12px; font-weight: 650; letter-spacing: .04em; }
          .inverse { fill: #F6F3EA; }
        </style>""",
        f'<rect width="1200" height="{height}" rx="16" fill="{PAPER}"/>',
    ]


def finish_svg(parts: list[str], source: str, height: int = 680) -> str:
    parts.extend(
        [
            f'<line x1="56" y1="{height - 40}" x2="1144" y2="{height - 40}" stroke="{GRID}"/>',
            text(56, height - 19, f"FONTE · {source}", "micro"),
            text(1144, height - 19, "SERIEMA · DO CANTO À CARTEIRA", "micro", "end"),
            "</svg>",
        ]
    )
    return "\n".join(parts) + "\n"


def write(name: str, svg: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(svg, encoding="utf-8")


def pipeline(locale: str = "pt") -> str:
    labels = {
        "pt": {
            "title": "Como a SERIEMA transforma chuva em posição",
            "sub": "A informação muda de escala seis vezes; o tempo disponível limita cada passagem.",
            "steps": [
                ("OBSERVAR", "chuva por célula", "CHIRPS"),
                ("LOCALIZAR", "municípios produtores", "IBGE · PAM"),
                ("CONTEXTUALIZAR", "cultura e janela", "CONAB · fenologia"),
                ("MEDIR", "choque climático", "dado já disponível"),
                ("TRADUZIR", "exposição por empresa", "produtor · processador"),
                ("POSICIONAR", "carteira D+1", "liquidez · custos · caps"),
            ],
            "foot": "ref_date diz a que o dado se refere · avail_date diz quando ele podia ser usado",
        },
        "en": {
            "title": "How SERIEMA turns rainfall into a position",
            "sub": "Information changes scale six times; what was available at the time constrains every step.",
            "steps": [
                ("OBSERVE", "rainfall by grid cell", "CHIRPS"),
                ("LOCATE", "producing municipalities", "IBGE · PAM"),
                ("CONTEXTUALIZE", "crop and window", "CONAB · phenology"),
                ("MEASURE", "climate shock", "available data only"),
                ("TRANSLATE", "company exposure", "producer · processor"),
                ("POSITION", "D+1 portfolio", "liquidity · costs · caps"),
            ],
            "foot": "ref_date says what period a datum describes · avail_date says when it could be used",
        },
    }[locale]
    parts = start_svg(labels["title"], labels["sub"], 500)
    parts += [text(56, 61, labels["title"], "display"), text(56, 92, labels["sub"], "subtitle")]
    y, w, gap = 145, 164, 18
    colors = [BLUE, BLUE, AMBER, AMBER, GREEN_2, GREEN]
    for i, ((head, body, detail), color) in enumerate(zip(labels["steps"], colors, strict=True)):
        x = 56 + i * (w + gap)
        parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="188" rx="12" fill="{WHITE}" stroke="{GRID}"/>'
        )
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="8" rx="4" fill="{color}"/>')
        parts.append(text(x + 18, y + 39, f"0{i + 1}", "label"))
        parts.append(text(x + 18, y + 72, head, "label"))
        words = body.split()
        cut = max(1, math.ceil(len(words) / 2))
        parts.append(
            multiline(x + 18, y + 108, [" ".join(words[:cut]), " ".join(words[cut:])], "body", 21)
        )
        parts.append(text(x + 18, y + 166, detail, "small"))
        if i < 5:
            parts.append(f'<path d="M{x + w + 4} {y + 94}h10" stroke="{MUTED}" stroke-width="2"/>')
            parts.append(
                f'<path d="M{x + w + 12} {y + 89}l7 5-7 5" fill="none" stroke="{MUTED}" stroke-width="2"/>'
            )
    parts.append(f'<rect x="56" y="359" width="1088" height="55" rx="8" fill="{GREEN}"/>')
    parts.append(text(600, 393, labels["foot"], "body inverse", "middle"))
    return finish_svg(parts, "especificações PIT e contrato operacional v1", 500)


def evidence(locale: str = "pt") -> str:
    tr = {
        "pt": {
            "title": "A hipótese não atravessou o projeto intacta",
            "sub": "Cada teste decidiu o próximo — inclusive quando o resultado contrariou a tese.",
            "heads": ["ELO FÍSICO", "CANAL DE PREÇO", "TESE ORIGINAL", "HIPÓTESE H′", "CARTEIRA"],
            "labels": [
                "apareceu",
                "não sustentado",
                "falsificada",
                "evidência OOS",
                "sem habilidade",
            ],
            "details": [
                "β −0,067 · t −5,96",
                "6 testes · 0 significativos",
                "β −0,091 · t −3,60",
                "p = 0,0625",
                "+16,97% vs +63,31%",
            ],
        },
        "en": {
            "title": "The hypothesis did not survive the project unchanged",
            "sub": "Each test determined the next step — including when evidence contradicted the thesis.",
            "heads": [
                "PHYSICAL LINK",
                "PRICE CHANNEL",
                "ORIGINAL THESIS",
                "H′ HYPOTHESIS",
                "PORTFOLIO",
            ],
            "labels": ["detected", "unsupported", "falsified", "OOS evidence", "no skill"],
            "details": [
                "β −0.067 · t −5.96",
                "6 tests · 0 significant",
                "β −0.091 · t −3.60",
                "p = 0.0625",
                "+16.97% vs +63.31%",
            ],
        },
    }[locale]
    parts = start_svg(tr["title"], tr["sub"], 560)
    parts += [text(56, 61, tr["title"], "display"), text(56, 92, tr["sub"], "subtitle")]
    colors = [GREEN, RED, RED, BLUE, AMBER]
    xs = [96, 316, 536, 756, 976]
    y = 258
    parts.append(f'<line x1="96" y1="{y}" x2="976" y2="{y}" stroke="{GRID}" stroke-width="5"/>')
    for i, (x, color) in enumerate(zip(xs, colors, strict=True)):
        parts.append(f'<circle cx="{x}" cy="{y}" r="18" fill="{color}"/>')
        if i < len(xs) - 1:
            parts.append(f'<path d="M{x + 22} {y}h170" stroke="{color}" stroke-width="3"/>')
        parts.append(text(x, 176, f"0{i + 1}", "label", "middle"))
        parts.append(multiline(x, 205, tr["heads"][i].split(" "), "label", 16, "middle"))
        parts.append(text(x, 309, tr["labels"][i], "title", "middle"))
        parts.append(text(x, 340, tr["details"][i], "small", "middle"))
    if locale == "pt":
        conclusion = [
            "Resultado científico: o clima contém informação física.",
            "Resultado financeiro: não demonstramos que ela remunera o risco.",
        ]
    else:
        conclusion = [
            "Scientific result: climate contains physical information.",
            "Financial result: we did not show that it rewards risk.",
        ]
    parts.append(f'<rect x="96" y="380" width="880" height="90" rx="10" fill="{GREEN}"/>')
    parts.append(multiline(536, 416, conclusion, "body inverse", 26, "middle"))
    return finish_svg(parts, "evidence_summary_v1.json e artefatos citados", 560)


def performance(locale: str = "pt") -> str:
    payload = load_json(DATA / "holdout_v1/public_series.json")
    series = payload["series"]
    title = (
        "A carteira ganhou; o caixa ganhou mais"
        if locale == "pt"
        else "The portfolio gained; cash gained more"
    )
    sub = (
        "Índice base 100 · retorno líquido após custos · drawdown da SERIEMA abaixo"
        if locale == "pt"
        else "Base-100 index · net return after costs · SERIEMA drawdown below"
    )
    parts = start_svg(title, sub, 720)
    parts += [text(56, 61, title, "display"), text(56, 92, sub, "subtitle")]
    x0, x1, y0, y1 = 74, 1125, 140, 475
    values = [row[key] for row in series for key in ("strategy_index", "risk_free_index")]
    vmin, vmax = 75, math.ceil(max(values) / 10) * 10
    for tick in range(vmin, vmax + 1, 15):
        y = y1 - (tick - vmin) / (vmax - vmin) * (y1 - y0)
        parts.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="{GRID}"/>')
        parts.append(text(x0 - 10, y + 5, str(tick), "small", "end"))

    def line_path(key: str, low: float, high: float, top: float, bottom: float) -> str:
        pts = []
        for i, row in enumerate(series):
            if i % 3 and i != len(series) - 1:
                continue
            x = x0 + i / (len(series) - 1) * (x1 - x0)
            y = bottom - (row[key] - low) / (high - low) * (bottom - top)
            pts.append(f"{x:.1f},{y:.1f}")
        return "M" + " L".join(pts)

    parts.append(
        f'<path d="{line_path("risk_free_index", vmin, vmax, y0, y1)}" fill="none" stroke="{BLUE}" stroke-width="4"/>'
    )
    parts.append(
        f'<path d="{line_path("strategy_index", vmin, vmax, y0, y1)}" fill="none" stroke="{GREEN}" stroke-width="4"/>'
    )
    end_rf = series[-1]["risk_free_index"]
    end_st = series[-1]["strategy_index"]
    rf_y = y1 - (end_rf - vmin) / (vmax - vmin) * (y1 - y0)
    st_y = y1 - (end_st - vmin) / (vmax - vmin) * (y1 - y0)
    parts += [
        text(
            x1,
            rf_y - 10,
            f"LIVRE DE RISCO  {pct(end_rf / 100 - 1)}"
            if locale == "pt"
            else f"RISK-FREE  {pct(end_rf / 100 - 1)}",
            "label",
            "end",
        ),
        text(x1, st_y - 10, f"SERIEMA  {pct(end_st / 100 - 1)}", "label", "end"),
    ]
    dates = [date.fromisoformat(row["date"]) for row in series]
    for year in range(2021, 2026):
        idx = min(range(len(dates)), key=lambda i: abs((dates[i] - date(year, 1, 1)).days))
        x = x0 + idx / (len(series) - 1) * (x1 - x0)
        parts.append(text(x, 499, str(year), "small", "middle"))

    dd_top, dd_bottom = 535, 630
    parts.append(
        text(x0, dd_top - 12, "DRAWDOWN SERIEMA" if locale == "pt" else "SERIEMA DRAWDOWN", "label")
    )
    dd_min = -0.25
    dd_points = []
    for i, row in enumerate(series):
        if i % 3 and i != len(series) - 1:
            continue
        x = x0 + i / (len(series) - 1) * (x1 - x0)
        y = dd_top + row["drawdown"] / dd_min * (dd_bottom - dd_top)
        dd_points.append(f"{x:.1f},{y:.1f}")
    area = f"M{x0},{dd_top} L" + " L".join(dd_points) + f" L{x1},{dd_top} Z"
    parts.append(f'<path d="{area}" fill="{RED}" fill-opacity="0.24"/>')
    parts.append(f'<path d="M{" L".join(dd_points)}" fill="none" stroke="{RED}" stroke-width="2"/>')
    parts.append(
        text(x1, dd_bottom - 5, "máx. −20,92%" if locale == "pt" else "max −20.92%", "small", "end")
    )
    return finish_svg(parts, "public_series.json · rodada única selada D-075", 720)


def crop_years(locale: str = "pt") -> str:
    report = load_json(DATA / "holdout_v1/12_descriptive_report.json")["crop_year_performance"]
    values = report["per_crop_year"]
    title = (
        "Só duas das cinco safras foram positivas"
        if locale == "pt"
        else "Only two of five crop years were positive"
    )
    sub = (
        "Retorno líquido e Sharpe de excesso por ano-safra"
        if locale == "pt"
        else "Net return and excess Sharpe by crop year"
    )
    parts = start_svg(title, sub, 620)
    parts += [text(56, 61, title, "display"), text(56, 92, sub, "subtitle")]
    years = list(values)
    x0, gap, bw, zero = 115, 205, 110, 320
    scale = 1050
    parts.append(
        f'<line x1="70" y1="{zero}" x2="1135" y2="{zero}" stroke="{INK}" stroke-width="1.5"/>'
    )
    for i, year in enumerate(years):
        x = x0 + i * gap
        ret = values[year]["compounded_return"]
        h = abs(ret) * scale
        y = zero - h if ret >= 0 else zero
        color = GREEN if ret >= 0 else RED
        parts.append(
            f'<rect x="{x}" y="{y:.1f}" width="{bw}" height="{h:.1f}" rx="5" fill="{color}"/>'
        )
        parts.append(
            text(x + bw / 2, y - 12 if ret >= 0 else y + h + 27, pct(ret, 1), "title", "middle")
        )
        parts.append(text(x + bw / 2, 475, year, "label", "middle"))
        sharpe = values[year]["excess_sharpe"]
        parts.append(text(x + bw / 2, 507, f"Sharpe ex. {sharpe:+.2f}", "small", "middle"))
    note = (
        "2023/24 respondeu por 109,7% do P&L líquido total; as outras safras, em conjunto, reduziram o resultado."
        if locale == "pt"
        else "2023/24 produced 109.7% of total net P&L; all other crop years combined reduced the result."
    )
    parts.append(
        f'<rect x="83" y="535" width="1050" height="38" rx="7" fill="{WHITE}" stroke="{GRID}"/>'
    )
    parts.append(text(608, 560, note, "small", "middle"))
    return finish_svg(parts, "12_descriptive_report.json", 620)


def costs() -> str:
    scenarios = load_json(DATA / "holdout_v1/02_portfolio.json")["payload"]["scenarios"]
    parts = start_svg(
        "Quanto os custos mudam a conclusão?",
        "Retorno total sob zero, base e dobro dos custos.",
        560,
    )
    parts += [
        text(56, 61, "Custos consomem 12,59 pontos percentuais", "display"),
        text(56, 92, "Retorno total do mesmo desenho operacional", "subtitle"),
    ]
    entries = [
        ("SEM CUSTOS", scenarios["zero"]),
        ("CUSTO BASE", scenarios["base"]),
        ("CUSTO ×2", scenarios["double"]),
    ]
    max_ret = max(v["total_return"] for _, v in entries)
    for i, (label, values) in enumerate(entries):
        y = 160 + i * 100
        w = values["total_return"] / max_ret * 760
        color = BLUE_2 if i == 0 else GREEN if i == 1 else RED
        parts.append(text(56, y + 24, label, "label"))
        parts.append(f'<rect x="220" y="{y}" width="{w:.1f}" height="42" rx="6" fill="{color}"/>')
        parts.append(text(235 + w, y + 29, pct(values["total_return"], 2), "title"))
        parts.append(
            text(1120, y + 27, f"DD {pct(values['max_drawdown'], 1, False)}", "small", "end")
        )
    borrow = scenarios["base"]["borrow_cost_brl"]
    spot = scenarios["base"]["spot_cost_brl"]
    parts.append(
        text(
            220,
            474,
            f"Base: aluguel R$ {borrow:,.0f} · negociação R$ {spot:,.0f}".replace(",", "."),
            "small",
        )
    )
    return finish_svg(parts, "02_portfolio.json", 560)


def sensitivity() -> str:
    scenarios = load_json(DATA / "holdout_v1/09_sensitivities.json")["payload"]
    baseline = load_json(DATA / "holdout_v1/02_portfolio.json")["payload"]["scenarios"]["base"][
        "total_return"
    ]
    groups = [
        (
            "ADTV",
            "adtv_brl",
            [("R$ 4 mi", "4000000"), ("base · R$ 8 mi", None), ("R$ 12 mi", "12000000")],
        ),
        ("CAP CANA", "cane_cap", [("10%", "0.1"), ("base · 15%", None), ("20%", "0.2")]),
        ("CAP GRÃOS", "grain_cap", [("30%", "0.3"), ("base · 40%", None), ("50%", "0.5")]),
        (
            "LAG TOTAL",
            "total_signal_lag_days",
            [("base", None), ("14 dias", "14"), ("21 dias", "21")],
        ),
    ]
    parts = start_svg(
        "Sensibilidade de um parâmetro por vez", "Retorno líquido em variantes pré-definidas.", 690
    )
    parts += [
        text(56, 61, "A direção depende do timing; não de um único cap", "display"),
        text(
            56, 92, "Retorno líquido · um parâmetro alterado por vez · base = +16,97%", "subtitle"
        ),
    ]
    panel_w = 255
    for g, (title_, key, items) in enumerate(groups):
        x0 = 56 + g * 272
        parts.append(text(x0, 142, title_, "label"))
        parts.append(
            f'<rect x="{x0}" y="162" width="{panel_w}" height="420" rx="10" fill="{WHITE}" stroke="{GRID}"/>'
        )
        zero = 380
        parts.append(
            f'<line x1="{x0 + 28}" y1="{zero}" x2="{x0 + panel_w - 22}" y2="{zero}" stroke="{INK}"/>'
        )
        for i, (label, variant) in enumerate(items):
            val = baseline if variant is None else scenarios[key][variant]["total_return"]
            h = abs(val) * 620
            bx = x0 + 34 + i * 70
            by = zero - h if val >= 0 else zero
            color = AMBER if variant is None else GREEN_2 if val >= 0 else RED
            parts.append(
                f'<rect x="{bx}" y="{by:.1f}" width="42" height="{h:.1f}" rx="4" fill="{color}"/>'
            )
            parts.append(
                text(bx + 21, by - 8 if val >= 0 else by + h + 18, pct(val, 1), "small", "middle")
            )
            parts.append(multiline(bx + 21, 523, label.split(" · "), "micro", 15, "middle"))
    parts.append(
        text(
            56,
            616,
            "Leitura: atrasar o sinal para 14 dias torna o resultado negativo; ampliar o cap de grãos o eleva.",
            "body",
        )
    )
    return finish_svg(parts, "09_sensitivities.json · 02_portfolio.json", 690)


def leave_one_out() -> str:
    by_name = load_json(DATA / "holdout_v1/07_loo_name.json")["payload"]
    by_year = load_json(DATA / "holdout_v1/08_loo_year.json")["payload"]
    parts = start_svg(
        "O resultado sobrevive sem cada nome ou safra?",
        "Leave-one-out reotimiza os pesos após cada exclusão.",
        720,
    )
    parts += [
        text(56, 61, "O resultado é concentrado e não aditivo", "display"),
        text(
            56, 92, "Retorno líquido ao retirar um componente e recalcular a carteira", "subtitle"
        ),
    ]

    def panel(x0: int, title_: str, values: list[tuple[str, float]]) -> None:
        parts.append(text(x0, 145, title_, "label"))
        zero_x, scale = x0 + 220, 410
        parts.append(f'<line x1="{zero_x}" y1="170" x2="{zero_x}" y2="580" stroke="{INK}"/>')
        for i, (label, val) in enumerate(values):
            y = 193 + i * 73
            w = abs(val) * scale
            x = zero_x if val >= 0 else zero_x - w
            color = GREEN if val >= 0 else RED
            parts.append(text(x0, y + 23, label, "body"))
            parts.append(
                f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="32" rx="4" fill="{color}"/>'
            )
            parts.append(
                text(
                    x + w + 8 if val >= 0 else x - 8,
                    y + 23,
                    pct(val, 1),
                    "small",
                    "start" if val >= 0 else "end",
                )
            )

    panel(56, "RETIRAR UM NOME", [(k, v["total_return"]) for k, v in by_name.items()])
    panel(650, "RETIRAR UMA SAFRA", [(k, v["total_return"]) for k, v in by_year.items()])
    parts.append(
        text(
            56,
            633,
            "A exclusão muda limites e redistribui pesos; portanto os efeitos não somam e não são atribuições marginais.",
            "small",
        )
    )
    return finish_svg(parts, "07_loo_name.json · 08_loo_year.json", 720)


def attribution() -> str:
    metrics = load_json(DATA / "holdout_v1/10_metrics.json")["payload"]
    split = load_json(DATA / "holdout_v1/04_sector_climate.json")["payload"]
    values = [(row["ticker"], row["gross_pnl_brl"]) for row in metrics["attribution_by_name"]]
    parts = start_svg(
        "De onde veio o resultado?",
        "Atribuição bruta por nome e decomposição aritmética setor-clima.",
        680,
    )
    parts += [
        text(56, 61, "BRFS3 respondeu por 67% do P&L bruto", "display"),
        text(56, 92, "Concentração por nome e decomposição do retorno do livro", "subtitle"),
    ]
    parts.append(text(56, 145, "P&L BRUTO POR NOME", "label"))
    zero_x, scale = 250, 0.0032
    parts.append(f'<line x1="{zero_x}" y1="170" x2="{zero_x}" y2="520" stroke="{INK}"/>')
    for i, (ticker, value) in enumerate(values):
        y = 184 + i * 65
        w = abs(value) * scale
        x = zero_x if value >= 0 else zero_x - w
        color = GREEN if value >= 0 else RED
        parts.append(text(56, y + 22, ticker, "body"))
        parts.append(
            f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="31" rx="4" fill="{color}"/>'
        )
        label = f"R$ {value / 1000:+.1f} mil".replace(".", ",")
        label_x = x + w + 8 if value >= 0 else zero_x + 10
        parts.append(text(label_x, y + 22, label, "small"))
    parts.append(text(690, 145, "RETORNO ARITMÉTICO DO LIVRO", "label"))
    x, y, total_w = 690, 215, 420
    climate_w = split["climate_share"] * total_w
    sector_w = total_w - climate_w
    parts.append(f'<rect x="{x}" y="{y}" width="{sector_w:.1f}" height="72" rx="6" fill="{BLUE}"/>')
    parts.append(
        f'<rect x="{x + sector_w}" y="{y}" width="{climate_w:.1f}" height="72" rx="6" fill="{AMBER}"/>'
    )
    parts.append(text(x + sector_w / 2, y + 44, "SETOR 68%", "label inverse", "middle"))
    parts.append(text(x + sector_w + climate_w / 2, y + 44, "CLIMA 32%", "label", "middle"))
    parts.append(
        multiline(
            690,
            339,
            [
                f"livro {pct(split['book_arith_return'])}",
                f"componente setorial {pct(split['sector_arith_return'])}",
                f"componente climático {pct(split['climate_arith_return'])}",
            ],
            "body",
            31,
        )
    )
    parts.append(
        f'<rect x="690" y="461" width="420" height="82" rx="8" fill="{WHITE}" stroke="{GRID}"/>'
    )
    parts.append(
        multiline(
            710,
            490,
            [
                "A decomposição não resgata o claim de alpha:",
                "o spanning multifatorial encontrou t = −1,03.",
            ],
            "small",
            22,
        )
    )
    return finish_svg(parts, "10_metrics.json · 04_sector_climate.json · 05_h4_spanning.json", 680)


def main() -> None:
    figures = {
        "pipeline.svg": pipeline("pt"),
        "pipeline-en.svg": pipeline("en"),
        "evidence-path.svg": evidence("pt"),
        "evidence-path-en.svg": evidence("en"),
        "performance.svg": performance("pt"),
        "performance-en.svg": performance("en"),
        "crop-years.svg": crop_years("pt"),
        "crop-years-en.svg": crop_years("en"),
        "costs.svg": costs(),
        "parameter-sensitivity.svg": sensitivity(),
        "leave-one-out.svg": leave_one_out(),
        "attribution.svg": attribution(),
    }
    for name, svg in figures.items():
        write(name, svg)
    print(f"wrote {len(figures)} figures to {OUT}")


if __name__ == "__main__":
    main()
