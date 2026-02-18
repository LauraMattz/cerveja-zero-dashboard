from __future__ import annotations

from typing import Any

import pandas as pd

from data_pipeline import (
    METRIC_BREWERIES,
    METRIC_REGULAR_VOL,
    METRIC_SPENDING,
    METRIC_TOTAL_VOL,
    METRIC_ZERO_SHARE,
    METRIC_ZERO_VOL,
    METRIC_PER_CAPITA,
    METRIC_TRADE_EXPORT_VOL,
    METRIC_GLOBAL_RANK_ZERO,
)


def safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None:
        return None
    if pd.isna(numerator) or pd.isna(denominator) or denominator == 0:
        return None
    return float(numerator / denominator)


def fmt_x(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "n/d"
    return f"{value:.2f}x"


def fmt_pct(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "n/d"
    return f"{value:.1f}%"


def fmt_num(value: float | None, decimals: int = 1) -> str:
    if value is None or pd.isna(value):
        return "n/d"
    return f"{value:.{decimals}f}"


def _get_value(
    df: pd.DataFrame,
    metric: str,
    segment: str,
    year: int,
) -> float | None:
    row = df[
        (df["metric"] == metric)
        & (df["segment"] == segment)
        & (df["year"] == year)
    ]
    if row.empty:
        return None
    return float(row.iloc[0]["value"])


def _set_value(
    df: pd.DataFrame,
    metric: str,
    segment: str,
    segment_type: str,
    year: int,
    value: float,
    data_status: str = "estimated",
    source: str = "Scenario simulation",
) -> pd.DataFrame:
    mask = (
        (df["metric"] == metric)
        & (df["segment"] == segment)
        & (df["year"] == year)
    )
    if mask.any():
        df.loc[mask, "value"] = value
        df.loc[mask, "data_status"] = data_status
        df.loc[mask, "source"] = source
        return df

    new_row = pd.DataFrame(
        [
            {
                "year": year,
                "metric": metric,
                "segment": segment,
                "segment_type": segment_type,
                "value": value,
                "data_status": data_status,
                "source": source,
            }
        ]
    )
    return pd.concat([df, new_row], ignore_index=True)


def apply_scenario(
    unified_df: pd.DataFrame,
    growth_zero_pct: float,
    regular_variation_pct: float,
    spending_elasticity_pct: float,
) -> pd.DataFrame:
    df = unified_df.copy()
    growth_zero = growth_zero_pct / 100.0
    regular_change = regular_variation_pct / 100.0
    spending_change = spending_elasticity_pct / 100.0

    # Apply scenario to 2025 and 2026 for volume.
    for year in [2025, 2026]:
        prev_year = year - 1
        prev_zero = _get_value(df, METRIC_ZERO_VOL, "Brasil", prev_year)
        prev_regular = _get_value(df, METRIC_REGULAR_VOL, "Brasil", prev_year)
        if prev_zero is not None:
            new_zero = max(0.0, prev_zero * (1 + growth_zero))
            df = _set_value(df, METRIC_ZERO_VOL, "Brasil", "country", year, new_zero)
        if prev_regular is not None:
            new_regular = max(0.0, prev_regular * (1 + regular_change))
            df = _set_value(df, METRIC_REGULAR_VOL, "Brasil", "country", year, new_regular)

        zero_value = _get_value(df, METRIC_ZERO_VOL, "Brasil", year)
        regular_value = _get_value(df, METRIC_REGULAR_VOL, "Brasil", year)
        if zero_value is not None and regular_value is not None:
            total_value = max(0.0, zero_value + regular_value)
            share_value = (zero_value / total_value * 100) if total_value > 0 else 0.0
            df = _set_value(df, METRIC_TOTAL_VOL, "Brasil", "country", year, total_value)
            df = _set_value(
                df,
                METRIC_ZERO_SHARE,
                "Brasil",
                "country",
                year,
                min(100.0, max(0.0, share_value)),
            )

    # Spending elasticity affects 2026 against 2025 for each state.
    spending_2025 = df[(df["metric"] == METRIC_SPENDING) & (df["year"] == 2025)]
    for _, row in spending_2025.iterrows():
        segment = str(row["segment"])
        value_2026 = max(0.0, float(row["value"]) * (1 + spending_change))
        df = _set_value(df, METRIC_SPENDING, segment, "state", 2026, value_2026)

    return df


def compute_insights(
    unified_df: pd.DataFrame,
    selected_year: int,
    selected_state: str | None,
) -> list[dict[str, str]]:
    year_base = selected_year
    year_prev = max(2024, selected_year - 1)

    zero_selected = _get_value(unified_df, METRIC_ZERO_VOL, "Brasil", year_base)
    zero_prev = _get_value(unified_df, METRIC_ZERO_VOL, "Brasil", year_prev)
    zero_ratio = safe_ratio(zero_selected, zero_prev)

    share_selected = _get_value(unified_df, METRIC_ZERO_SHARE, "Brasil", year_base)
    share_prev = _get_value(unified_df, METRIC_ZERO_SHARE, "Brasil", year_prev)
    share_delta = None
    if share_selected is not None and share_prev is not None:
        share_delta = share_selected - share_prev

    brewers_2026 = _get_value(unified_df, METRIC_BREWERIES, "Brasil", 2026)
    brewers_2024 = _get_value(unified_df, METRIC_BREWERIES, "Brasil", 2024)
    brewers_ratio = safe_ratio(brewers_2026, brewers_2024)

    sp_spending_2025 = _get_value(unified_df, METRIC_SPENDING, "São Paulo", 2025)
    mg_spending_2025 = _get_value(unified_df, METRIC_SPENDING, "Minas Gerais", 2025)
    sp_vs_mg = safe_ratio(sp_spending_2025, mg_spending_2025)

    state_label = selected_state if selected_state else "São Paulo"
    state_brew_2026 = _get_value(unified_df, METRIC_BREWERIES, state_label, 2026)
    state_brew_2024 = _get_value(unified_df, METRIC_BREWERIES, state_label, 2024)
    state_growth_ratio = safe_ratio(state_brew_2026, state_brew_2024)

    insights = [
        {
            "title": f"Cerveja zero em {year_base}",
            "value": fmt_x(zero_ratio),
            "subtitle": f"Comparado com {year_prev}. Ex.: 1.20x significa 20% maior.",
        },
        {
            "title": "Participacao da zero",
            "value": fmt_pct(share_selected),
            "subtitle": f"Ganhou {fmt_num(share_delta, 2)} pontos percentuais vs {year_prev}.",
        },
        {
            "title": "Cervejarias no Brasil",
            "value": fmt_x(brewers_ratio),
            "subtitle": "Comparacao de 2026 com 2024.",
        },
        {
            "title": "SP vs MG (gasto 2025)",
            "value": fmt_x(sp_vs_mg),
            "subtitle": "Quanto Sao Paulo representa em relacao a Minas Gerais.",
        },
        {
            "title": f"{state_label}: 2026 vs 2024",
            "value": fmt_x(state_growth_ratio),
            "subtitle": "Crescimento de cervejarias no periodo.",
        },
    ]
    return insights


def state_options(unified_df: pd.DataFrame) -> list[str]:
    rows = unified_df[
        (unified_df["segment_type"] == "state")
        & (
            (unified_df["metric"] == METRIC_BREWERIES)
            | (unified_df["metric"] == METRIC_SPENDING)
        )
    ]
    options = sorted(rows["segment"].dropna().unique().tolist())
    return options


def compute_benchmark(
    unified_df: pd.DataFrame,
    state_a: str,
    state_b: str,
    year_base: int,
) -> pd.DataFrame:
    metrics_to_compare = [
        ("Cervejarias", METRIC_BREWERIES),
        ("Gasto (R$ bi)", METRIC_SPENDING),
    ]
    rows: list[dict[str, Any]] = []
    for label, metric in metrics_to_compare:
        a_val = _get_value(unified_df, metric, state_a, year_base)
        b_val = _get_value(unified_df, metric, state_b, year_base)
        ratio = safe_ratio(a_val, b_val)
        diff = None
        if a_val is not None and b_val is not None:
            diff = a_val - b_val
        rows.append(
            {
                "metric_label": label,
                "state_a": state_a,
                "state_b": state_b,
                "a_value": a_val,
                "b_value": b_val,
                "ratio_a_over_b": ratio,
                "diff_a_minus_b": diff,
            }
        )

    # Growth proxy: 2024->2026 breweries ratio.
    a_growth = safe_ratio(
        _get_value(unified_df, METRIC_BREWERIES, state_a, 2026),
        _get_value(unified_df, METRIC_BREWERIES, state_a, 2024),
    )
    b_growth = safe_ratio(
        _get_value(unified_df, METRIC_BREWERIES, state_b, 2026),
        _get_value(unified_df, METRIC_BREWERIES, state_b, 2024),
    )
    rows.append(
        {
            "metric_label": "Crescimento 2026/2024 (cervejarias)",
            "state_a": state_a,
            "state_b": state_b,
            "a_value": a_growth,
            "b_value": b_growth,
            "ratio_a_over_b": safe_ratio(a_growth, b_growth),
            "diff_a_minus_b": None if a_growth is None or b_growth is None else (a_growth - b_growth),
        }
    )
    return pd.DataFrame(rows)


def compute_delta(
    current: float | None,
    previous: float | None,
) -> dict[str, Any]:
    """
    Calculates delta between two values and returns dict with:
    - pct_change: percentage change
    - arrow: unicode arrow (↗ ↘ →)
    - color: color code for display
    - formatted: formatted string like "+45.2%"
    """
    if current is None or previous is None or pd.isna(current) or pd.isna(previous):
        return {
            "pct_change": None,
            "arrow": "→",
            "color": "#64748b",
            "formatted": "n/d",
        }

    if previous == 0:
        return {
            "pct_change": None,
            "arrow": "→",
            "color": "#64748b",
            "formatted": "n/d",
        }

    pct_change = ((current - previous) / previous) * 100

    if pct_change > 0.5:
        arrow = "↗"
        color = "#0f766e"  # Verde (crescimento)
    elif pct_change < -0.5:
        arrow = "↘"
        color = "#dc2626"  # Vermelho (queda)
    else:
        arrow = "→"
        color = "#64748b"  # Cinza (estável)

    sign = "+" if pct_change > 0 else ""
    formatted = f"{sign}{pct_change:.1f}%"

    return {
        "pct_change": pct_change,
        "arrow": arrow,
        "color": color,
        "formatted": formatted,
    }


def generate_sparkline_svg(
    values: list[float],
    width: int = 60,
    height: int = 20,
    color: str = "#0f766e",
) -> str:
    """
    Generates a mini SVG sparkline chart from a list of values.
    Returns SVG string that can be embedded in HTML.
    """
    if not values or len(values) < 2:
        return ""

    # Normalize values to 0-1 range
    min_val = min(values)
    max_val = max(values)
    range_val = max_val - min_val if max_val != min_val else 1

    normalized = [(v - min_val) / range_val for v in values]

    # Create points for polyline (invert Y because SVG coordinates start at top)
    points = []
    step_x = width / (len(values) - 1)
    for i, val in enumerate(normalized):
        x = i * step_x
        y = height - (val * height)  # Invert Y
        points.append(f"{x:.1f},{y:.1f}")

    polyline = " ".join(points)

    svg = f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}"
        style="display:inline-block; vertical-align:middle; margin-left:8px;">
        <polyline points="{polyline}"
            fill="none" stroke="{color}" stroke-width="1.5" />
    </svg>'''

    return svg


def compute_kpi_with_delta(
    df: pd.DataFrame,
    metric: str,
    segment: str,
    current_year: int,
    label: str,
    unit: str = "",
    decimals: int = 2,
    include_sparkline: bool = True,
) -> dict[str, Any]:
    """
    Computes a KPI with delta comparison to previous year and optional sparkline.

    Returns dict with:
    - label: display label
    - current_value: current year value
    - previous_value: previous year value
    - formatted_value: formatted string with unit
    - delta: dict from compute_delta()
    - sparkline_svg: SVG string (if include_sparkline=True)
    - status: data status (official/estimated)
    """
    current_val = _get_value(df, metric, segment, current_year)
    previous_val = _get_value(df, metric, segment, current_year - 1)

    # Get data status
    status_row = df[
        (df["metric"] == metric)
        & (df["segment"] == segment)
        & (df["year"] == current_year)
    ]
    status = status_row.iloc[0]["data_status"] if not status_row.empty else "unknown"

    # Format current value
    if current_val is None or pd.isna(current_val):
        formatted_value = "n/d"
    else:
        formatted_value = f"{current_val:.{decimals}f}{unit}"

    # Compute delta
    delta = compute_delta(current_val, previous_val)

    # Generate sparkline (last 4-5 years)
    sparkline_svg = ""
    if include_sparkline and current_val is not None:
        years = range(max(2021, current_year - 4), current_year + 1)
        values = []
        for year in years:
            val = _get_value(df, metric, segment, year)
            if val is not None:
                values.append(val)

        if len(values) >= 2:
            sparkline_svg = generate_sparkline_svg(
                values,
                color="#0f766e" if delta["arrow"] == "↗" else "#3b82f6"
            )

    return {
        "label": label,
        "current_value": current_val,
        "previous_value": previous_val,
        "formatted_value": formatted_value,
        "delta": delta,
        "sparkline_svg": sparkline_svg,
        "status": status,
    }


def compute_main_kpis(
    df: pd.DataFrame,
    year: int,
) -> list[dict[str, Any]]:
    """
    Computes the 6 main KPIs for the dashboard overview page.
    """
    kpis = [
        compute_kpi_with_delta(
            df, METRIC_ZERO_VOL, "Brasil", year,
            "Volume Cerveja Zero", " bi L", decimals=3
        ),
        compute_kpi_with_delta(
            df, METRIC_ZERO_SHARE, "Brasil", year,
            "Market Share Zero", "%", decimals=1
        ),
        compute_kpi_with_delta(
            df, METRIC_BREWERIES, "Brasil", year,
            "Cervejarias no Brasil", "", decimals=0
        ),
        compute_kpi_with_delta(
            df, METRIC_PER_CAPITA, "Brasil", year,
            "Consumo Per Capita", " L/hab", decimals=1
        ),
        compute_kpi_with_delta(
            df, METRIC_TRADE_EXPORT_VOL, "Brasil", year,
            "Exportações", " M L", decimals=0
        ),
        compute_kpi_with_delta(
            df, METRIC_GLOBAL_RANK_ZERO, "Brasil", year,
            "Ranking Global Zero", "º", decimals=0,
            include_sparkline=False
        ),
    ]

    return kpis
