from __future__ import annotations

import inspect
from typing import Any

import altair as alt
import streamlit as st


def _with_chart_presentation(chart: alt.Chart) -> alt.Chart:
    return (
        chart.properties(background="#ffffff")
        .configure_view(stroke="#dbeafe", strokeWidth=1.2)
        .configure_axis(
            gridColor="#e2e8f0",
            tickColor="#94a3b8",
            labelColor="#334155",
            titleColor="#0f172a",
        )
        .configure_legend(labelColor="#334155", titleColor="#0f172a")
    )


def _supports_on_select() -> bool:
    try:
        signature = inspect.signature(st.altair_chart)
    except (TypeError, ValueError):
        return False
    return "on_select" in signature.parameters


def _extract_field(payload: Any, field: str) -> Any:
    field_lower = field.lower()
    if isinstance(payload, dict):
        for key, value in payload.items():
            if str(key).lower() == field_lower:
                return value
            nested = _extract_field(value, field)
            if nested is not None:
                return nested
    elif isinstance(payload, list):
        for item in payload:
            nested = _extract_field(item, field)
            if nested is not None:
                return nested
    return None


def render_clickable_chart(
    chart: alt.Chart,
    key: str,
    select_field: str | None = None,
    height: int | None = None,
) -> Any:
    chart = _with_chart_presentation(chart)
    if height is not None:
        chart = chart.properties(height=height)

    if not _supports_on_select():
        st.altair_chart(chart, key=key, use_container_width=True)
        return None

    event = st.altair_chart(
        chart,
        key=key,
        use_container_width=True,
        on_select="rerun",
    )
    if select_field is None or event is None:
        return None

    payload = getattr(event, "selection", None)
    if payload is None and isinstance(event, dict):
        payload = event.get("selection")
    value = _extract_field(payload, select_field)
    if isinstance(value, list) and value:
        value = value[0]
    return value


def render_story_stepper() -> int:
    steps = [
        "Panorama",
        "Aceleracao da Zero",
        "Geografia do mercado",
        "Cenarios 2025-2026",
        "Recomendacoes",
    ]
    descriptions = {
        1: "Visao executiva dos indicadores centrais e leitura de contexto.",
        2: "Foco no crescimento da cerveja zero e ganho de participacao.",
        3: "Distribuicao regional e leitura de estados com maior peso.",
        4: "Teste de cenarios e comparacao direta entre estados.",
        5: "Fechamento com recomendacoes objetivas para decisao.",
    }
    if "story_step" not in st.session_state:
        st.session_state.story_step = 1

    st.markdown("### Modo apresentacao")
    selected = st.select_slider(
        "Etapa",
        options=list(range(1, len(steps) + 1)),
        value=int(st.session_state.story_step),
        format_func=lambda i: f"{i}. {steps[i - 1]}",
    )
    st.session_state.story_step = int(selected)

    col1, col2, col3 = st.columns([1, 1, 5])
    with col1:
        if st.button("Anterior", use_container_width=True):
            st.session_state.story_step = max(1, st.session_state.story_step - 1)
    with col2:
        if st.button("Proximo", use_container_width=True):
            st.session_state.story_step = min(len(steps), st.session_state.story_step + 1)
    with col3:
        st.progress(st.session_state.story_step / len(steps))
        st.caption(f"Etapa {st.session_state.story_step}/{len(steps)}: {steps[st.session_state.story_step - 1]}")
        st.markdown(
            f"<div class='story-hint'>{descriptions[st.session_state.story_step]}</div>",
            unsafe_allow_html=True,
        )

    return int(st.session_state.story_step)


def section_visible(story_mode: bool, current_step: int, expected_step: int) -> bool:
    if not story_mode:
        return True
    return current_step == expected_step


def render_insight_cards(cards: list[dict[str, str]]) -> None:
    tones = ["tone-teal", "tone-orange", "tone-blue", "tone-pink", "tone-lime", "tone-slate"]
    columns = st.columns(min(3, max(1, len(cards))))
    for index, card in enumerate(cards):
        col = columns[index % len(columns)]
        tone = tones[index % len(tones)]
        with col:
            st.markdown(
                f"""
<div class="insight-card {tone}">
  <h4>{card["title"]}</h4>
  <div class="big">{card["value"]}</div>
  <div class="small">{card["subtitle"]}</div>
</div>
""",
                unsafe_allow_html=True,
            )


def render_delta_card(kpi: dict[str, Any], col_index: int = 0) -> None:
    """
    Renders a KPI card with delta comparison and sparkline.
    kpi dict should contain: label, formatted_value, delta, sparkline_svg, status
    """
    delta = kpi.get("delta", {})
    arrow = delta.get("arrow", "→")
    color = delta.get("color", "#64748b")
    formatted_delta = delta.get("formatted", "")
    sparkline = kpi.get("sparkline_svg", "")
    status = kpi.get("status", "unknown")

    # Status badge
    status_badge = "🟢 Oficial" if status == "official" else "🔵 Estimado"

    st.markdown(
        f"""
<div class="delta-card">
    <div class="delta-label">{kpi['label']}</div>
    <div class="delta-value">
        {kpi['formatted_value']}
        {sparkline}
    </div>
    <div class="delta-change" style="color: {color};">
        <span style="font-size: 1.2em;">{arrow}</span>
        <span style="margin-left: 4px;">{formatted_delta}</span>
    </div>
    <div class="delta-status">{status_badge}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_choropleth_map(df: Any, metric_column: str, state_column: str, title: str) -> None:
    """
    Renders an interactive choropleth map of Brazil using plotly.
    df: DataFrame with state data
    metric_column: column name for the metric to visualize
    state_column: column name for state abbreviations
    title: map title
    """
    try:
        import plotly.express as px

        # Map state abbreviations to full names for better display
        state_names = {
            "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas",
            "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo",
            "GO": "Goiás", "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul",
            "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná",
            "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
            "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina",
            "SP": "São Paulo", "SE": "Sergipe", "TO": "Tocantins"
        }

        # Create geojson URL for Brazil states
        geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"

        fig = px.choropleth(
            df,
            geojson=geojson_url,
            locations=state_column,
            color=metric_column,
            featureidkey="properties.sigla",
            color_continuous_scale="Teal",
            title=title,
            hover_data={state_column: True, metric_column: True},
        )

        fig.update_geos(
            fitbounds="locations",
            visible=False,
        )

        fig.update_layout(
            margin={"r": 0, "t": 30, "l": 0, "b": 0},
            height=500,
        )

        st.plotly_chart(fig, use_container_width=True)

    except ImportError:
        st.warning("Plotly não está instalado. Execute: pip install plotly")
    except Exception as e:
        st.error(f"Erro ao renderizar mapa: {str(e)}")
        # Fallback to bar chart
        import altair as alt
        chart = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X(f"{metric_column}:Q", title=title),
                y=alt.Y(f"{state_column}:N", sort="-x", title="Estado"),
                color=alt.Color(f"{metric_column}:Q", scale=alt.Scale(scheme="teals")),
            )
        )
        st.altair_chart(_with_chart_presentation(chart), use_container_width=True)
