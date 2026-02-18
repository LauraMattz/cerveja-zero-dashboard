from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any

import pandas as pd
import requests


DATA_DIR = Path(__file__).parent / "data"

# Unified metric ids used across modules.
METRIC_ZERO_VOL = "volume_zero_billion_liters"
METRIC_REGULAR_VOL = "volume_regular_billion_liters"
METRIC_TOTAL_VOL = "volume_total_billion_liters"
METRIC_ZERO_SHARE = "volume_zero_share_pct"
METRIC_BREWERIES = "breweries_count"
METRIC_REGION_SUDESTE_BREWERIES = "region_sudeste_breweries_count"
METRIC_REGION_NORTE_BREWERIES = "region_norte_breweries_count"
METRIC_REGION_SUDESTE_SHARE = "region_sudeste_share_pct"
METRIC_SPENDING = "spending_billion_reais"
METRIC_TRADE_EXPORT_VOL = "trade_export_volume_million_liters"
METRIC_TRADE_EXPORT_REVENUE = "trade_export_revenue_million_usd"
METRIC_TRADE_IMPORT_GERMANY_VOL = "trade_import_germany_volume_million_liters"
METRIC_TRADE_IMPORT_GERMANY_SHARE = "trade_import_germany_share_pct"
METRIC_TRADE_EXPORT_SA_SHARE = "trade_export_south_america_share_pct"
METRIC_TRADE_EXPORT_PARAGUAY_SHARE = "trade_export_paraguay_share_pct"

# New metrics
METRIC_PER_CAPITA = "consumption_per_capita_liters"
METRIC_DENSITY_STATE = "brewery_density_per_100k"
METRIC_CONCENTRATION_BREWERIES = "market_concentration_breweries_pct"
METRIC_CONCENTRATION_VOLUME = "market_concentration_volume_pct"
METRIC_BEER_STYLE_PCT = "beer_style_percentage"
METRIC_INFLATION_IPCA = "inflation_ipca_beer_pct"
METRIC_GLOBAL_RANK_ZERO = "global_rank_zero_consumption"

RUNTIME_SOURCES = {
    "mapa_2022": "https://www.gov.br/agricultura/pt-br/assuntos/noticias/numero-de-cervejarias-registradas-no-brasil-cresce-11-6-em-2022",
    "mapa_2023": "https://www.gov.br/agricultura/pt-br/assuntos/noticias/mercado-cervejeiro-cresce-6-8-em-2023-e-chega-a-1-847-estabelecimentos-no-brasil",
    "mapa_2024": "https://www.gov.br/agricultura/pt-br/assuntos/noticias/brasil-chega-a-1-949-cervejarias-registradas",
}


@dataclass(frozen=True)
class RuntimeMeta:
    status: str
    last_refresh_utc: str
    source_count: int
    notes: str


def _status_from_year(year: int, official_until: int = 2024) -> str:
    return "official" if year <= official_until else "estimated"


def _to_numeric(value: Any) -> float:
    if pd.isna(value):
        return float("nan")
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return float("nan")
    text = text.replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return float("nan")


def load_base_data() -> dict[str, pd.DataFrame]:
    return {
        "volume": pd.read_csv(DATA_DIR / "zero_vs_regular_beer_volume.csv"),
        "spending": pd.read_csv(DATA_DIR / "alcoholic_beverage_spending_2025.csv"),
        "breweries": pd.read_csv(DATA_DIR / "mapa_breweries_history.csv"),
        "state_breweries": pd.read_csv(DATA_DIR / "mapa_state_breweries_selected.csv"),
        "region_highlights": pd.read_csv(DATA_DIR / "mapa_region_highlights.csv"),
        "trade": pd.read_csv(DATA_DIR / "mapa_trade_2024.csv"),
        "per_capita": pd.read_csv(DATA_DIR / "consumption_per_capita.csv"),
        "density": pd.read_csv(DATA_DIR / "brewery_density_by_state.csv"),
        "concentration": pd.read_csv(DATA_DIR / "market_concentration.csv"),
        "styles": pd.read_csv(DATA_DIR / "beer_styles.csv"),
        "inflation": pd.read_csv(DATA_DIR / "inflation_ipca.csv"),
        "exports_detailed": pd.read_csv(DATA_DIR / "exports_detailed_2024.csv"),
    }


def _build_unified_local(base: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    volume_df = base["volume"].copy()
    total = volume_df["Total_Beer_Billion_Liters"].replace(0, float("nan"))
    volume_df["Zero_Share"] = (
        volume_df["Zero_Beer_Billion_Liters"] / total * 100
    )
    for _, row in volume_df.iterrows():
        year = int(row["Year"])
        status = _status_from_year(year)
        source = "Projeto beer_analyses (serie de volume)"
        rows.extend(
            [
                {
                    "year": year,
                    "metric": METRIC_ZERO_VOL,
                    "segment": "Brasil",
                    "segment_type": "country",
                    "value": float(row["Zero_Beer_Billion_Liters"]),
                    "data_status": status,
                    "source": source,
                },
                {
                    "year": year,
                    "metric": METRIC_REGULAR_VOL,
                    "segment": "Brasil",
                    "segment_type": "country",
                    "value": float(row["Regular_Beer_Billion_Liters"]),
                    "data_status": status,
                    "source": source,
                },
                {
                    "year": year,
                    "metric": METRIC_TOTAL_VOL,
                    "segment": "Brasil",
                    "segment_type": "country",
                    "value": float(row["Total_Beer_Billion_Liters"]),
                    "data_status": status,
                    "source": source,
                },
                {
                    "year": year,
                    "metric": METRIC_ZERO_SHARE,
                    "segment": "Brasil",
                    "segment_type": "country",
                    "value": float(row["Zero_Share"]),
                    "data_status": status,
                    "source": source,
                },
            ]
        )

    for _, row in base["breweries"].iterrows():
        year = int(row["year"])
        rows.append(
            {
                "year": year,
                "metric": METRIC_BREWERIES,
                "segment": "Brasil",
                "segment_type": "country",
                "value": float(row["breweries_count"]),
                "data_status": "official",
                "source": str(row.get("source", "MAPA")),
            }
        )

    for _, row in base["state_breweries"].iterrows():
        year = int(row["year"])
        state_name = str(row["state"]).replace("Sao Paulo", "São Paulo").strip()
        rows.append(
            {
                "year": year,
                "metric": METRIC_BREWERIES,
                "segment": state_name,
                "segment_type": "state",
                "value": float(row["breweries_count"]),
                "data_status": "official",
                "source": str(row.get("source", "MAPA")),
            }
        )

    region_df = base["region_highlights"].copy()
    for _, row in region_df.iterrows():
        year = int(row["year"])
        if not pd.isna(row.get("sudeste_breweries")):
            rows.append(
                {
                    "year": year,
                    "metric": METRIC_REGION_SUDESTE_BREWERIES,
                    "segment": "Sudeste",
                    "segment_type": "region",
                    "value": float(row["sudeste_breweries"]),
                    "data_status": "official",
                    "source": str(row.get("source", "MAPA")),
                }
            )
        if not pd.isna(row.get("norte_breweries")):
            rows.append(
                {
                    "year": year,
                    "metric": METRIC_REGION_NORTE_BREWERIES,
                    "segment": "Norte",
                    "segment_type": "region",
                    "value": float(row["norte_breweries"]),
                    "data_status": "official",
                    "source": str(row.get("source", "MAPA")),
                }
            )
        if not pd.isna(row.get("sudeste_share_pct")):
            rows.append(
                {
                    "year": year,
                    "metric": METRIC_REGION_SUDESTE_SHARE,
                    "segment": "Sudeste",
                    "segment_type": "region",
                    "value": float(row["sudeste_share_pct"]),
                    "data_status": "official",
                    "source": str(row.get("source", "MAPA")),
                }
            )

    spending_df = base["spending"].copy()
    for _, row in spending_df.iterrows():
        rows.append(
            {
                "year": 2025,
                "metric": METRIC_SPENDING,
                "segment": str(row["state"]),
                "segment_type": "state",
                "value": float(row["spending_billion_reais"]),
                "data_status": "official",
                "source": "Recorte regional do projeto (2025)",
            }
        )

    trade_metric_map = {
        "Exportacoes de cerveja (volume)": METRIC_TRADE_EXPORT_VOL,
        "Faturamento de exportacoes": METRIC_TRADE_EXPORT_REVENUE,
        "Importacao da Alemanha (volume)": METRIC_TRADE_IMPORT_GERMANY_VOL,
        "Participacao da Alemanha na importacao": METRIC_TRADE_IMPORT_GERMANY_SHARE,
        "Participacao da America do Sul no destino das exportacoes": METRIC_TRADE_EXPORT_SA_SHARE,
        "Participacao do Paraguai no volume exportado": METRIC_TRADE_EXPORT_PARAGUAY_SHARE,
    }
    trade_segment_map = {
        METRIC_TRADE_EXPORT_VOL: "Brasil",
        METRIC_TRADE_EXPORT_REVENUE: "Brasil",
        METRIC_TRADE_IMPORT_GERMANY_VOL: "Alemanha",
        METRIC_TRADE_IMPORT_GERMANY_SHARE: "Alemanha",
        METRIC_TRADE_EXPORT_SA_SHARE: "America do Sul",
        METRIC_TRADE_EXPORT_PARAGUAY_SHARE: "Paraguai",
    }
    for _, row in base["trade"].iterrows():
        metric_name = trade_metric_map.get(str(row["metric"]))
        if not metric_name:
            continue
        rows.append(
            {
                "year": 2024,
                "metric": metric_name,
                "segment": trade_segment_map[metric_name],
                "segment_type": "flow",
                "value": float(row["value"]),
                "data_status": "official",
                "source": str(row.get("source", "MAPA")),
            }
        )

    # Per capita consumption
    for _, row in base["per_capita"].iterrows():
        rows.append(
            {
                "year": int(row["year"]),
                "metric": METRIC_PER_CAPITA,
                "segment": "Brasil",
                "segment_type": "country",
                "value": float(row["liters_per_capita"]),
                "data_status": _status_from_year(int(row["year"])),
                "source": str(row["source"]),
            }
        )

    # Brewery density by state
    for _, row in base["density"].iterrows():
        rows.append(
            {
                "year": 2024,
                "metric": METRIC_DENSITY_STATE,
                "segment": str(row["state"]),
                "segment_type": "state",
                "value": float(row["breweries_per_100k"]),
                "data_status": "official",
                "source": "MAPA Anuario 2025",
            }
        )

    # Market concentration
    for _, row in base["concentration"].iterrows():
        rows.extend([
            {
                "year": 2024,
                "metric": METRIC_CONCENTRATION_BREWERIES,
                "segment": str(row["segment"]),
                "segment_type": "market_segment",
                "value": float(row["breweries_pct"]),
                "data_status": "official",
                "source": "MAPA Anuario 2025",
            },
            {
                "year": 2024,
                "metric": METRIC_CONCENTRATION_VOLUME,
                "segment": str(row["segment"]),
                "segment_type": "market_segment",
                "value": float(row["volume_pct"]),
                "data_status": "official",
                "source": "MAPA Anuario 2025",
            },
        ])

    # Beer styles
    for _, row in base["styles"].iterrows():
        rows.append(
            {
                "year": 2024,
                "metric": METRIC_BEER_STYLE_PCT,
                "segment": str(row["style"]),
                "segment_type": "style",
                "value": float(row["percentage"]),
                "data_status": "official",
                "source": "MAPA Anuario 2025",
            }
        )

    # Inflation IPCA
    for _, row in base["inflation"].iterrows():
        rows.append(
            {
                "year": int(row["year"]),
                "metric": METRIC_INFLATION_IPCA,
                "segment": "Brasil",
                "segment_type": "country",
                "value": float(row["ipca_beer_pct"]),
                "data_status": "official",
                "source": "IBGE",
            }
        )

    # Global rank (fixed value)
    rows.append(
        {
            "year": 2024,
            "metric": METRIC_GLOBAL_RANK_ZERO,
            "segment": "Brasil",
            "segment_type": "country",
            "value": 2.0,
            "data_status": "official",
            "source": "Ranking global consumo cerveja zero",
        }
    )

    unified = pd.DataFrame(rows)
    unified["year"] = unified["year"].astype(int)
    unified["value"] = unified["value"].astype(float)
    return unified


def fetch_runtime_updates(timeout_s: int = 8) -> dict[str, pd.DataFrame]:
    updates: dict[str, pd.DataFrame] = {}
    parsed_rows: list[dict[str, Any]] = []

    for source_id, url in RUNTIME_SOURCES.items():
        try:
            response = requests.get(url, timeout=timeout_s)
            response.raise_for_status()
        except Exception:
            continue
        text = response.text
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).lower()

        year_match = re.search(r"(2022|2023|2024)", source_id)
        if not year_match:
            continue
        year = int(year_match.group(1))
        candidates = re.findall(
            r"(\d{1,3}(?:[.,]\d{3})+|\d{3,4})\s+(?:cervejarias|estabelecimentos)",
            text,
        )
        values = [_to_numeric(item) for item in candidates]
        values = [v for v in values if not pd.isna(v)]
        if not values:
            continue
        parsed_rows.append(
            {
                "year": year,
                "metric": METRIC_BREWERIES,
                "segment": "Brasil",
                "segment_type": "country",
                "value": float(max(values)),
                "data_status": "official",
                "source": url,
            }
        )

    if parsed_rows:
        updates["unified"] = pd.DataFrame(parsed_rows)
    return updates


def merge_with_priority(local_df: pd.DataFrame, online_df: pd.DataFrame) -> pd.DataFrame:
    if online_df is None or online_df.empty:
        return local_df.copy()
    if local_df is None or local_df.empty:
        return online_df.copy()

    merge_keys = ["year", "metric", "segment"]
    merged = pd.concat([local_df, online_df], ignore_index=True)
    merged = merged.drop_duplicates(subset=merge_keys, keep="last")
    return merged


def _metric_fallback_growth(df: pd.DataFrame) -> dict[str, float]:
    growth_map: dict[str, float] = {}
    official_df = df[df["data_status"] == "official"].copy()
    if official_df.empty:
        return growth_map

    for metric, metric_df in official_df.groupby("metric"):
        growth_rates: list[float] = []
        for _, segment_df in metric_df.groupby("segment"):
            segment_df = segment_df.sort_values("year")
            if len(segment_df) < 2:
                continue
            prev = segment_df.iloc[-2]
            curr = segment_df.iloc[-1]
            if prev["value"] == 0:
                continue
            growth_rates.append((curr["value"] - prev["value"]) / prev["value"])
        growth_map[metric] = float(pd.Series(growth_rates).median()) if growth_rates else 0.0
    return growth_map


def _clamp_metric(metric: str, value: float) -> float:
    if "share" in metric:
        return max(0.0, min(100.0, value))
    return max(0.0, value)


def ensure_years_with_forecast(
    df: pd.DataFrame,
    min_year: int = 2025,
    max_year: int = 2026,
) -> pd.DataFrame:
    if df.empty:
        return df

    result = df.copy()
    fallback_growth = _metric_fallback_growth(result)
    generated_rows: list[dict[str, Any]] = []

    group_cols = ["metric", "segment", "segment_type"]
    for group_key, group in result.groupby(group_cols, dropna=False):
        metric, segment, segment_type = group_key
        group = group.sort_values("year").copy()
        existing_years = set(int(y) for y in group["year"].tolist())
        metric_default_growth = fallback_growth.get(metric, 0.0)

        for year in range(min_year, max_year + 1):
            if year in existing_years:
                continue

            history = group[group["year"] < year].sort_values("year")
            if history.empty:
                continue

            if len(history) >= 3 and history["value"].tail(3).min() > 0:
                window = history.tail(3)
                year_span = int(window.iloc[-1]["year"] - window.iloc[0]["year"])
                if year_span > 0:
                    growth_rate = (window.iloc[-1]["value"] / window.iloc[0]["value"]) ** (
                        1 / year_span
                    ) - 1
                else:
                    growth_rate = metric_default_growth
                base_value = float(history.iloc[-1]["value"])
                next_value = base_value * (1 + growth_rate)
                method = "CAGR"
            elif len(history) >= 2:
                window = history.tail(2)
                year_span = int(window.iloc[-1]["year"] - window.iloc[0]["year"])
                if year_span <= 0:
                    annual_delta = 0.0
                else:
                    annual_delta = (window.iloc[-1]["value"] - window.iloc[0]["value"]) / year_span
                base_value = float(history.iloc[-1]["value"])
                next_value = base_value + annual_delta
                method = "linear"
            else:
                base_value = float(history.iloc[-1]["value"])
                next_value = base_value * (1 + metric_default_growth)
                method = "fallback"

            next_value = _clamp_metric(metric, float(next_value))
            generated = {
                "year": year,
                "metric": metric,
                "segment": segment,
                "segment_type": segment_type,
                "value": next_value,
                "data_status": "estimated",
                "source": f"Estimated ({method})",
            }
            generated_rows.append(generated)
            group = pd.concat([group, pd.DataFrame([generated])], ignore_index=True).sort_values("year")
            existing_years.add(year)

    if generated_rows:
        result = pd.concat([result, pd.DataFrame(generated_rows)], ignore_index=True)
    return result.sort_values(["metric", "segment", "year"]).reset_index(drop=True)


def build_data_bundle(
    timeout_s: int = 8,
    min_year: int = 2025,
    max_year: int = 2026,
) -> dict[str, Any]:
    base = load_base_data()
    unified_local = _build_unified_local(base)
    runtime_updates = fetch_runtime_updates(timeout_s=timeout_s)
    runtime_df = runtime_updates.get("unified", pd.DataFrame())
    unified_merged = merge_with_priority(unified_local, runtime_df)
    unified = ensure_years_with_forecast(unified_merged, min_year=min_year, max_year=max_year)

    status = "online" if not runtime_df.empty else "offline"
    note = "Runtime updates from official pages applied." if status == "online" else "Offline mode (dados locais)."
    runtime_meta = RuntimeMeta(
        status=status,
        last_refresh_utc=datetime.now(timezone.utc).isoformat(),
        source_count=len(RUNTIME_SOURCES),
        notes=note,
    )

    return {
        "unified": unified,
        "runtime_meta": runtime_meta,
        "runtime_sources": RUNTIME_SOURCES,
    }
