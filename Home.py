"""
Dashboard Cerveja Zero Brasil - Página Única
Análise completa do mercado com layout otimizado
"""

import streamlit as st
import pandas as pd
import altair as alt
from data_pipeline import (
    build_data_bundle,
    METRIC_ZERO_VOL,
    METRIC_REGULAR_VOL,
    METRIC_ZERO_SHARE,
    METRIC_BREWERIES,
    METRIC_SPENDING,
    METRIC_DENSITY_STATE,
    METRIC_CONCENTRATION_VOLUME,
    METRIC_CONCENTRATION_BREWERIES,
)
from metrics import compute_main_kpis
from ui_sections import render_choropleth_map

st.set_page_config(
    page_title="Cerveja Zero no Brasil",
    page_icon="🍺",
    layout="wide",
)

# CSS Dark Mode
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    * {
        font-family: 'Inter', sans-serif;
    }

    /* Dark background */
    .main {
        background: linear-gradient(135deg, #0a0f1e 0%, #1a1f2e 50%, #0f1419 100%);
    }

    /* Streamlit overrides */
    .stApp {
        background: linear-gradient(135deg, #0a0f1e 0%, #1a1f2e 50%, #0f1419 100%);
    }

    /* Text colors */
    h1, h2, h3, p, div, span, label {
        color: #e2e8f0 !important;
    }

    /* Header com gradiente vibrante */
    .main-header {
        background: linear-gradient(135deg, #0f766e 0%, #06b6d4 50%, #8b5cf6 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 3rem;
        box-shadow: 0 20px 60px rgba(15, 118, 110, 0.3),
                    0 0 100px rgba(139, 92, 246, 0.2);
        position: relative;
        overflow: hidden;
    }
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: pulse 4s ease-in-out infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 0.3; }
        50% { opacity: 0.6; }
    }
    .main-header h1 {
        color: #ffffff !important;
        font-size: 3rem !important;
        font-weight: 800 !important;
        margin: 0;
        text-shadow: 0 4px 20px rgba(0,0,0,0.5);
        position: relative;
        z-index: 1;
    }
    .main-header p {
        color: #e0f2fe !important;
        font-size: 1.2rem !important;
        margin: 1rem 0 0 0;
        position: relative;
        z-index: 1;
    }

    /* KPI Cards - Dark Glass Morphism */
    .kpi-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(51, 65, 85, 0.6) 100%);
        backdrop-filter: blur(10px);
        border: 2px solid rgba(15, 118, 110, 0.3);
        border-radius: 16px;
        padding: 1.5rem;
        height: 180px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: all 0.4s ease;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        position: relative;
        overflow: hidden;
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(circle at top right, rgba(15, 118, 110, 0.15), transparent);
        opacity: 0;
        transition: opacity 0.4s ease;
    }
    .kpi-card:hover {
        border-color: #0f766e;
        box-shadow: 0 12px 48px rgba(15, 118, 110, 0.4),
                    0 0 80px rgba(15, 118, 110, 0.2);
        transform: translateY(-4px) scale(1.02);
    }
    .kpi-card:hover::before {
        opacity: 1;
    }
    .kpi-label {
        font-size: 0.85rem;
        font-weight: 700;
        color: #06b6d4 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.75rem;
    }
    .kpi-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: #ffffff !important;
        margin: 0.5rem 0;
        line-height: 1;
        text-shadow: 0 2px 10px rgba(15, 118, 110, 0.5);
    }
    .kpi-delta {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-top: 0.75rem;
    }
    .kpi-delta-positive {
        color: #10b981 !important;
        font-weight: 700;
        font-size: 1.1rem;
        text-shadow: 0 0 20px rgba(16, 185, 129, 0.6);
    }
    .kpi-delta-neutral {
        color: #94a3b8 !important;
        font-weight: 700;
        font-size: 1.1rem;
    }
    .kpi-delta-negative {
        color: #ef4444 !important;
        font-weight: 700;
        font-size: 1.1rem;
        text-shadow: 0 0 20px rgba(239, 68, 68, 0.6);
    }
    .kpi-status {
        font-size: 0.8rem;
        color: #cbd5e1 !important;
        margin-top: 0.5rem;
    }

    /* Section headers com glow */
    .section-title {
        font-size: 2rem !important;
        font-weight: 800 !important;
        color: #ffffff !important;
        margin: 3rem 0 2rem 0;
        padding-bottom: 1rem;
        border-bottom: 3px solid transparent;
        border-image: linear-gradient(90deg, #0f766e, #06b6d4, #8b5cf6) 1;
        text-shadow: 0 0 30px rgba(15, 118, 110, 0.6);
    }

    /* Info box - Neon style */
    .info-box {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%);
        border-left: 4px solid #06b6d4;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 2rem 0;
        color: #e0f2fe !important;
        box-shadow: 0 8px 32px rgba(6, 182, 212, 0.2);
    }

    .info-box strong {
        color: #22d3ee !important;
        font-size: 1.1rem !important;
    }

    /* Surprise boxes */
    .surprise-box {
        background: linear-gradient(135deg, rgba(249, 115, 22, 0.2) 0%, rgba(234, 88, 12, 0.2) 100%);
        border: 2px solid rgba(249, 115, 22, 0.5);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        box-shadow: 0 8px 32px rgba(249, 115, 22, 0.3);
    }

    .surprise-emoji {
        font-size: 2.5rem;
        display: inline-block;
        animation: bounce 2s infinite;
    }

    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }

    /* === GAMIFICAÇÃO CSS === */

    /* Painel de jogador */
    .player-panel {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(59, 130, 246, 0.15));
        border: 2px solid rgba(139, 92, 246, 0.4);
        border-radius: 20px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 0 40px rgba(139, 92, 246, 0.3);
    }

    /* Botões gamificados */
    .stButton>button {
        background: linear-gradient(135deg, #10b981, #06b6d4) !important;
        border: 3px solid #10b981 !important;
        border-radius: 15px !important;
        color: white !important;
        font-weight: 800 !important;
        font-size: 1.1rem !important;
        padding: 0.75rem 2rem !important;
        box-shadow: 0 0 30px rgba(16, 185, 129, 0.5) !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }

    .stButton>button:hover {
        transform: scale(1.1) translateY(-3px) !important;
        box-shadow: 0 0 50px rgba(16, 185, 129, 0.8) !important;
        border-color: #06b6d4 !important;
    }

    /* Animação de shake (erro) */
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-10px); }
        20%, 40%, 60%, 80% { transform: translateX(10px); }
    }

    .shake {
        animation: shake 0.5s;
    }

    /* Animação de pulse (badge) */
    @keyframes pulse-badge {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.15); }
    }

    .badge {
        display: inline-block;
        animation: pulse-badge 2s infinite;
        font-size: 2rem;
        margin: 0 0.5rem;
    }

    /* Efeito glow em cards de missão */
    .missao-card {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(6, 182, 212, 0.1));
        border: 2px solid rgba(16, 185, 129, 0.4);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(16, 185, 129, 0.2);
        transition: all 0.4s ease;
        cursor: pointer;
    }

    .missao-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 48px rgba(16, 185, 129, 0.4);
        border-color: #10b981;
    }

    /* Fade in animation */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .fade-in {
        animation: fadeIn 0.6s ease-out;
    }

    /* Progress bar gamificada */
    .progress-bar-custom {
        height: 30px;
        background: linear-gradient(90deg, #10b981, #06b6d4, #8b5cf6);
        border-radius: 15px;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.5);
    }

    /* Vida (hearts) */
    .vida {
        font-size: 2rem;
        display: inline-block;
        animation: pulse-badge 1.5s infinite;
    }

    /* ================================
       RESPONSIVIDADE - MOBILE FIRST
       ================================ */

    /* BASE - Mobile (320px+) */
    .main-header h1 {
        font-size: clamp(1.8rem, 5vw, 3rem) !important;
    }

    .main-header p {
        font-size: clamp(0.9rem, 2.5vw, 1.2rem) !important;
    }

    .section-title {
        font-size: clamp(1.5rem, 4vw, 2rem) !important;
    }

    .kpi-card {
        height: auto;
        min-height: 160px;
    }

    .kpi-value {
        font-size: clamp(1.8rem, 4vw, 2.5rem) !important;
    }

    .kpi-label {
        font-size: clamp(0.75rem, 2vw, 0.85rem) !important;
    }

    /* Botões com touch targets adequados */
    .stButton>button {
        min-height: 48px !important;
        min-width: 120px !important;
        font-size: clamp(0.9rem, 2vw, 1.1rem) !important;
        padding: 0.75rem 1.5rem !important;
    }

    /* Painel de jogador responsivo */
    .player-panel {
        padding: clamp(1rem, 3vw, 1.5rem);
    }

    /* Cards de missão */
    .missao-card {
        padding: clamp(1rem, 3vw, 1.5rem);
    }

    .missao-card h3 {
        font-size: clamp(1.1rem, 3vw, 1.5rem) !important;
    }

    /* Info boxes */
    .info-box {
        padding: clamp(1rem, 3vw, 1.5rem);
        font-size: clamp(0.9rem, 2vw, 1rem) !important;
    }

    /* Surprise boxes */
    .surprise-box {
        padding: clamp(1rem, 3vw, 1.5rem);
    }

    .surprise-emoji {
        font-size: clamp(2rem, 5vw, 2.5rem) !important;
    }

    /* TABLET (768px+) */
    @media (min-width: 768px) {
        .main-header {
            padding: 3rem 2rem;
        }

        .kpi-card {
            height: 180px;
        }

        .player-panel {
            padding: 1.5rem;
        }

        .stButton>button {
            min-width: 150px !important;
        }
    }

    /* DESKTOP (1024px+) */
    @media (min-width: 1024px) {
        .main-header h1 {
            font-size: 3rem !important;
        }

        .main-header p {
            font-size: 1.2rem !important;
        }

        .section-title {
            font-size: 2rem !important;
        }

        .kpi-value {
            font-size: 2.5rem !important;
        }

        .stButton>button {
            font-size: 1.1rem !important;
        }
    }

    /* ULTRA-WIDE (1920px+) */
    @media (min-width: 1920px) {
        .main-header {
            max-width: 1600px;
            margin: 0 auto;
        }

        .stApp {
            max-width: 1800px;
            margin: 0 auto;
        }
    }

    /* MOBILE SPECIFIC - Smaller screens */
    @media (max-width: 767px) {
        /* Stack elements vertically */
        .main-header {
            padding: 2rem 1rem;
        }

        .main-header h1 {
            font-size: 1.8rem !important;
            line-height: 1.2;
        }

        .main-header p {
            font-size: 0.95rem !important;
            margin-top: 0.75rem;
        }

        /* KPI cards stack */
        .kpi-card {
            margin-bottom: 1rem;
        }

        /* Player panel simplified */
        .player-panel h3 {
            font-size: 1.3rem !important;
        }

        .player-panel p {
            font-size: 0.85rem !important;
        }

        /* Larger touch targets */
        .stRadio > label {
            min-height: 44px;
            display: flex;
            align-items: center;
        }

        .stSelectbox > div {
            min-height: 48px;
        }

        /* Simplify badges display */
        .badge {
            font-size: 1.5rem !important;
            margin: 0 0.25rem;
        }

        /* Mission cards */
        .missao-card h3 {
            font-size: 1.1rem !important;
            line-height: 1.3;
        }

        .missao-card p {
            font-size: 0.85rem !important;
        }

        /* Reduce padding everywhere */
        .section-title {
            margin: 2rem 0 1.5rem 0;
            padding-bottom: 0.75rem;
        }

        .info-box, .surprise-box {
            margin: 1rem 0;
        }

        /* Metrics smaller */
        .vida {
            font-size: 1.5rem !important;
        }
    }

    /* VERY SMALL MOBILE (320px-480px) */
    @media (max-width: 480px) {
        .main-header h1 {
            font-size: 1.5rem !important;
        }

        .main-header p {
            font-size: 0.85rem !important;
        }

        .kpi-value {
            font-size: 2rem !important;
        }

        .kpi-label {
            font-size: 0.7rem !important;
        }

        .stButton>button {
            font-size: 0.95rem !important;
            padding: 0.6rem 1rem !important;
            width: 100%;
        }

        .player-panel {
            padding: 1rem;
        }

        .section-title {
            font-size: 1.4rem !important;
        }

        .badge {
            font-size: 1.2rem !important;
        }

        /* Simplify layout further */
        .missao-card {
            padding: 0.75rem;
        }

        .missao-card h3 {
            font-size: 1rem !important;
        }

        .info-box strong {
            font-size: 0.95rem !important;
        }
    }

    /* Landscape mobile */
    @media (max-height: 500px) and (orientation: landscape) {
        .main-header {
            padding: 1.5rem 1rem;
        }

        .kpi-card {
            min-height: 140px;
        }

        .player-panel {
            padding: 1rem;
        }
    }

    /* Print styles (bonus) */
    @media print {
        .stButton, .player-panel, .missao-card {
            display: none !important;
        }

        .main-header {
            background: white !important;
            color: black !important;
        }

        * {
            color: black !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Função helper para gráficos - Dark Mode
def optimize_chart(chart, height=400):
    return chart.properties(
        height=height,
        background="transparent"
    ).configure_view(
        stroke="rgba(148, 163, 184, 0.2)",
        strokeWidth=1
    ).configure_axis(
        gridColor="rgba(148, 163, 184, 0.15)",
        gridOpacity=0.3,
        labelColor="#94a3b8",
        labelFontSize=12,
        titleColor="#e2e8f0",
        titleFontSize=14,
        titleFontWeight=700
    ).configure_legend(
        labelColor="#cbd5e1",
        titleColor="#e2e8f0",
        orient="top",
        labelFontSize=11
    )

# Load data
@st.cache_data(ttl=86400)
def load_data():
    return build_data_bundle(timeout_s=8, min_year=2021, max_year=2026)

try:
    bundle = load_data()
    df = bundle["unified"]
    meta = bundle["runtime_meta"]
except Exception as e:
    st.error(f"⚠️ Erro ao carregar dados. Pressione 'C' para limpar o cache.\n\n**Detalhe:** `{e}`")
    st.stop()

# Sidebar
with st.sidebar:
    st.markdown("### ℹ️ Sobre")
    st.caption(f"**Fontes:** MAPA, IBGE, Euromonitor")
    st.caption(f"**Status:** {'🟢 Online' if meta.status == 'online' else '🟡 Cache'}")
    st.caption(f"**Atualização:** {meta.last_refresh_utc[:10]}")

# Fixar configurações (sem filtros)
available_years = sorted(df["year"].unique())
selected_year = max(available_years)
status_filter = ["official", "estimated"]
filtered_df = df[df["data_status"].isin(status_filter)].copy()

# Header
st.markdown("""
<div class="main-header">
    <h1>🍺 Cerveja Zero no Brasil</h1>
    <p>🚀 Hypergrowth: +537% em 2024 • 🏆 2º Maior Consumidor Mundial</p>
</div>
""", unsafe_allow_html=True)

# === KPIs ===
st.markdown('<div class="section-title">📈 Indicadores Principais</div>', unsafe_allow_html=True)

kpis = compute_main_kpis(filtered_df, selected_year)

# Grid 3x2
cols = st.columns(3)

for idx, kpi in enumerate(kpis):
    col_idx = idx % 3

    # Determine delta color
    delta_val = kpi['delta'].get('pct_change', 0)
    if delta_val is None or delta_val == 0:
        delta_class = "kpi-delta-neutral"
        arrow = "→"
    elif delta_val > 0:
        delta_class = "kpi-delta-positive"
        arrow = "↗"
    else:
        delta_class = "kpi-delta-negative"
        arrow = "↘"

    delta_text = kpi['delta'].get('formatted', '0.0%')
    status_badge = "🟢 Oficial" if kpi.get('status') == 'official' else "🔵 Estimado"

    with cols[col_idx]:
        st.markdown(f"""
<div class="kpi-card">
    <div>
        <div class="kpi-label">{kpi['label']}</div>
        <div class="kpi-value">{kpi['formatted_value']}</div>
    </div>
    <div>
        <div class="kpi-delta">
            <span class="{delta_class}">{arrow} {delta_text}</span>
        </div>
        <div class="kpi-status">{status_badge}</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# === STORYTELLING INTERATIVO ===
st.markdown('<div class="section-title">📖 Descubra o Boom Zero</div>', unsafe_allow_html=True)

st.markdown("""
<div class="info-box" style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(6, 182, 212, 0.2)); border-color: #10b981;">
    <strong style="color: #10b981; font-size: 1.2rem;">🚀 A cerveja zero EXPLODIU no Brasil!</strong>
    <p style="margin-top: 0.5rem;">
    • <b>+537% em 2024:</b> 757 milhões de litros<br>
    • <b>🏆 2º lugar mundial</b> em consumo de cerveja zero<br>
    • <b>11,9 piscinas olímpicas</b> produzidas POR DIA
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Pergunta 2: Como explicar?
st.markdown("### 🤯 Como explicar esse boom de 537%?")

with st.expander("🏃 **1. Tendência Global de Saúde e Bem-Estar**", expanded=True):
    st.markdown("""
    - Consumidores buscam **equilíbrio** entre prazer e saúde
    - Movimento *sober curious* (curiosos pela sobriedade) cresce globalmente
    - Zero álcool permite **socializar sem ressaca**
    - Especialmente forte entre jovens 25-35 anos
    """)

with st.expander("🌍 **2. Brasil = Mercado Estratégico Global**"):
    st.markdown("""
    - 🥈 **2º maior consumidor mundial** de cerveja zero (só perde para China)
    - Ultrapassou os EUA em 2024
    - Mercado de **R$ 4 bilhões** e crescendo
    - Clima tropical favorece consumo o ano todo
    """)

with st.expander("🏭 **3. Investimento Massivo das Marcas**"):
    st.markdown("""
    - **Heineken 0.0** chegou em 2020 e consolidou liderança
    - **Ambev** reagiu forte: Budweiser Zero e Corona Cero (2022)
    - Marcas cresceram **+20% em 2024** (vs +1% mercado total)
    - Qualidade melhorou drasticamente (sabor próximo ao original)
    """)

with st.expander("📱 **4. Mudança Cultural e Lei Seca**"):
    st.markdown("""
    - Lei Seca mais rigorosa desde 2008
    - Cultura de **dirigir após beber** diminuiu
    - Redes sociais valorizam **estilo de vida saudável**
    - Cerveja zero = **sem culpa, com prazer**
    """)

st.markdown("---")

st.markdown("### 🏆 Quem domina o mercado zero no Brasil?")

st.markdown("""
**Top 3 Marcas Zero (2024):**

🥇 **Heineken 0.0** - Líder
- Lançada em 2020
- Brasil = mercado estratégico global

🥈 **Budweiser Zero** - +20% em 2024
- Ambev (lançada em 2022)

🥉 **Corona Cero** - +20% em 2024
- Ambev (lançada em 2022)
""")

st.markdown("---")

# === MERCADO DE MARCAS ===
st.markdown('<div class="section-title">🏢 Panorama do Mercado Brasileiro</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Market Share", "🚀 Crescimento Zero", "🏆 Top Marcas"])

with tab1:
    st.markdown("**Distribuição do Mercado por Fabricante (2024)**")

    # Dados de market share
    market_data = pd.DataFrame({
        'Fabricante': ['Ambev', 'Heineken Brasil', 'Grupo Petrópolis', 'Outros'],
        'Share': [59.3, 24.4, 11.3, 5.0],
        'Marcas': ['Brahma, Skol, Bud, Corona', 'Heineken, Amstel', 'Itaipava, Petra', 'Artesanais']
    })

    market_chart = alt.Chart(market_data).mark_arc(
        innerRadius=80,
        outerRadius=130,
        stroke='#1e293b',
        strokeWidth=3
    ).encode(
        theta=alt.Theta('Share:Q'),
        color=alt.Color(
            'Fabricante:N',
            scale=alt.Scale(
                domain=['Ambev', 'Heineken Brasil', 'Grupo Petrópolis', 'Outros'],
                range=['#f59e0b', '#10b981', '#06b6d4', '#64748b']
            ),
            legend=alt.Legend(title="Fabricante", titleColor="#e2e8f0", labelColor="#cbd5e1")
        ),
        tooltip=[
            alt.Tooltip('Fabricante:N', title='Fabricante'),
            alt.Tooltip('Share:Q', format='.1f', title='Market Share (%)'),
            alt.Tooltip('Marcas:N', title='Principais Marcas')
        ]
    )

    labels = market_chart.mark_text(radius=150, fontSize=14, fontWeight='bold', color='#e2e8f0').encode(
        text=alt.Text('Share:Q', format='.1f')
    )

    st.altair_chart(optimize_chart(market_chart + labels, 350), use_container_width=True)

    st.markdown("""
    <div class="info-box">
        <strong>💡 Insight:</strong> Mercado concentrado mas em transformação.
        Ambev mantém liderança histórica (59%), enquanto Heineken cresce forte (24%)
        e Petrópolis surpreende com Petra em alta.
    </div>
    """, unsafe_allow_html=True)

with tab2:
    st.markdown("**Crescimento Comparativo: Zero vs Premium vs Total (2024)**")

    growth_data = pd.DataFrame({
        'Categoria': ['Cerveja Zero', 'Cervejas Premium', 'Mercado Total'],
        'Crescimento': [20.0, 10.0, 1.0],
        'Cor': ['#10b981', '#f59e0b', '#64748b']
    })

    growth_chart = alt.Chart(growth_data).mark_bar(
        cornerRadiusTopRight=10,
        opacity=0.9
    ).encode(
        x=alt.X('Crescimento:Q', title='Crescimento (%)', scale=alt.Scale(domain=[0, 22])),
        y=alt.Y('Categoria:N', sort='-x', title=''),
        color=alt.Color('Cor:N', scale=None, legend=None),
        tooltip=[
            alt.Tooltip('Categoria:N', title='Categoria'),
            alt.Tooltip('Crescimento:Q', format='.1f', title='Crescimento (%)')
        ]
    )

    text = growth_chart.mark_text(align='left', dx=5, fontSize=13, color='#e2e8f0', fontWeight='bold').encode(
        text=alt.Text('Crescimento:Q', format='.0f')
    )

    st.altair_chart(optimize_chart(growth_chart + text, 300), use_container_width=True)

    st.markdown("""
    <div class="surprise-box">
        <span class="surprise-emoji">🚀</span>
        <strong style="color: #10b981;">Zero cresce 20x mais que o mercado total!</strong>
        <p style="margin-top: 0.5rem; color: #a7f3d0;">
        Enquanto o mercado total cresce apenas 1%, cerveja zero dispara com +20% em 2024.
        Até cervejas premium (+10%) ficam para trás nessa corrida.
        </p>
    </div>
    """, unsafe_allow_html=True)

with tab3:
    st.markdown("**Top 5 Marcas Mais Consumidas no Brasil (2024)**")

    brands_data = pd.DataFrame({
        'Marca': ['Brahma', 'Heineken', 'Skol', 'Amstel', 'Budweiser'],
        'Consumo': [43.1, 40.6, 36.6, 33.2, 28.8],
        'Fabricante': ['Ambev', 'Heineken', 'Ambev', 'Heineken', 'Ambev']
    })

    brands_chart = alt.Chart(brands_data).mark_bar(
        cornerRadiusTopRight=10,
        opacity=0.9
    ).encode(
        x=alt.X('Consumo:Q', title='% Consumidores'),
        y=alt.Y('Marca:N', sort='-x', title=''),
        color=alt.Color(
            'Fabricante:N',
            scale=alt.Scale(
                domain=['Ambev', 'Heineken'],
                range=['#f59e0b', '#10b981']
            ),
            legend=alt.Legend(title="Fabricante", titleColor="#e2e8f0", labelColor="#cbd5e1")
        ),
        tooltip=[
            alt.Tooltip('Marca:N', title='Marca'),
            alt.Tooltip('Consumo:Q', format='.1f', title='% Consumidores'),
            alt.Tooltip('Fabricante:N', title='Fabricante')
        ]
    )

    text_brands = brands_chart.mark_text(align='left', dx=5, fontSize=12, color='#e2e8f0', fontWeight='bold').encode(
        text=alt.Text('Consumo:Q', format='.1f')
    )

    st.altair_chart(optimize_chart(brands_chart + text_brands, 300), use_container_width=True)

    st.caption("Fonte: Brazil Panels (2024)")

st.markdown("---")

# === EVOLUÇÃO TEMPORAL ===
st.markdown('<div class="section-title">📈 Evolução do Mercado Zero</div>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("**📈 Volume de Cerveja Zero: Crescimento Explosivo**")
    st.caption("💡 2024 = 11,9 piscinas olímpicas produzidas por dia!")

    volume_df = filtered_df[
        (filtered_df["metric"] == METRIC_ZERO_VOL) &
        (filtered_df["segment"] == "Brasil")
    ].copy()

    base = alt.Chart(volume_df)

    # Linha principal com gradiente neon
    line = base.mark_line(
        point=alt.OverlayMarkDef(size=150, filled=True, color="#10b981"),
        strokeWidth=5,
        color="#10b981"
    ).encode(
        x=alt.X("year:Q", axis=alt.Axis(format="d", title="Ano")),
        y=alt.Y("value:Q", title="Volume (bilhões de litros)"),
        tooltip=[
            alt.Tooltip("year:Q", title="Ano", format="d"),
            alt.Tooltip("value:Q", title="Volume", format=".3f"),
        ]
    )

    # Área de projeção
    proj_df = volume_df[volume_df["year"] >= 2024]
    area = alt.Chart(proj_df).mark_area(opacity=0.25, color="#10b981").encode(
        x="year:Q", y="value:Q"
    )

    # Rótulos com valores
    labels = base.mark_text(
        fontSize=13,
        fontWeight='bold',
        dy=-15,
        color='#10b981'
    ).encode(
        x=alt.X('year:Q'),
        y=alt.Y('value:Q'),
        text=alt.Text('value:Q', format='.2f')
    )

    st.altair_chart(optimize_chart(line + area + labels, 380), use_container_width=True)

with col2:
    st.markdown("**📊 Market Share**")
    st.caption("🎯 Caminho para 10% até 2028")

    share_df = filtered_df[
        (filtered_df["metric"] == METRIC_ZERO_SHARE) &
        (filtered_df["segment"] == "Brasil")
    ].copy()

    share_chart = alt.Chart(share_df).mark_area(
        line={'color': '#f59e0b', 'strokeWidth': 4},
        color=alt.Gradient(
            gradient='linear',
            stops=[
                alt.GradientStop(color='rgba(251, 191, 36, 0.3)', offset=0),
                alt.GradientStop(color='rgba(245, 158, 11, 0.6)', offset=1)
            ],
            x1=0, x2=0, y1=1, y2=0
        )
    ).encode(
        x=alt.X("year:Q", axis=alt.Axis(format="d", title="Ano")),
        y=alt.Y("value:Q", title="Share (%)", scale=alt.Scale(domain=[0, 6])),
        tooltip=[alt.Tooltip("year:Q", format="d"), alt.Tooltip("value:Q", format=".1f", title="Share %")]
    )

    # Rótulos com valores percentuais
    share_labels = alt.Chart(share_df).mark_text(
        fontSize=12,
        fontWeight='bold',
        dy=-12,
        color='#f59e0b'
    ).encode(
        x=alt.X("year:Q"),
        y=alt.Y("value:Q"),
        text=alt.Text("value:Q", format=".1f")
    )

    st.altair_chart(optimize_chart(share_chart + share_labels, 380), use_container_width=True)

# Surprise Insight
st.markdown("""
<div class="surprise-box">
    <span class="surprise-emoji">💰</span>
    <strong style="color: #fbbf24; font-size: 1.2rem;">Mercado Vale R$ 4 Bilhões</strong>
    <p style="color: #fcd34d; margin-top: 0.5rem;">Equivalente a 15 estádios do Maracanã lotados com ingressos de R$ 100 cada!</p>
</div>
""", unsafe_allow_html=True)

# Comparison
st.markdown("**⚖️ Batalha de Gigantes: Zero vs. Tradicional**")
st.caption("A cerveja zero cresce enquanto a tradicional se mantém estável")

comp_df = filtered_df[
    (filtered_df["metric"].isin([METRIC_ZERO_VOL, METRIC_REGULAR_VOL])) &
    (filtered_df["segment"] == "Brasil")
].copy()
comp_df["categoria"] = comp_df["metric"].map({
    METRIC_ZERO_VOL: "Cerveja Zero",
    METRIC_REGULAR_VOL: "Cerveja Tradicional"
})

comp_chart = alt.Chart(comp_df).mark_line(
    point=alt.OverlayMarkDef(size=120, filled=True),
    strokeWidth=4
).encode(
    x=alt.X("year:Q", axis=alt.Axis(format="d", title="Ano")),
    y=alt.Y("value:Q", title="Volume (bi L)"),
    color=alt.Color(
        "categoria:N",
        scale=alt.Scale(
            domain=["Cerveja Zero", "Cerveja Tradicional"],
            range=["#10b981", "#64748b"]
        ),
        legend=alt.Legend(title="Categoria", titleColor="#e2e8f0", labelColor="#cbd5e1")
    ),
    tooltip=[
        alt.Tooltip("year:Q", format="d", title="Ano"),
        alt.Tooltip("categoria:N", title="Tipo"),
        alt.Tooltip("value:Q", format=".2f", title="Volume")
    ]
)

# Rótulos com valores diferenciados por cor
comp_labels = alt.Chart(comp_df).mark_text(
    fontSize=11,
    fontWeight='bold',
    dy=-12
).encode(
    x=alt.X("year:Q"),
    y=alt.Y("value:Q"),
    text=alt.Text("value:Q", format=".2f"),
    color=alt.Color(
        "categoria:N",
        scale=alt.Scale(
            domain=["Cerveja Zero", "Cerveja Tradicional"],
            range=["#10b981", "#94a3b8"]
        ),
        legend=None
    )
)

st.altair_chart(optimize_chart(comp_chart + comp_labels, 350), use_container_width=True)

st.markdown("---")

# === GEOGRAFIA ===
st.markdown('<div class="section-title">🌍 Geografia Cervejeira do Brasil</div>', unsafe_allow_html=True)

st.markdown("**🗺️ Densidade de Cervejarias: O Mapa da Oportunidade**")
st.caption("Sul = Saturação | Norte/Nordeste = Deserto de oportunidades")

density_df = filtered_df[
    (filtered_df["metric"] == METRIC_DENSITY_STATE) &
    (filtered_df["year"] == 2024)
].copy()

if not density_df.empty:
    map_df = density_df[["segment", "value"]].copy()
    map_df.columns = ["state", "density"]
    render_choropleth_map(map_df, "density", "state", "Cervejarias / 100k hab")

st.markdown("""
<div class="surprise-box">
    <span class="surprise-emoji">🌊</span>
    <strong style="color: #06b6d4; font-size: 1.2rem;">Deserto Cervejeiro</strong>
    <p style="color: #67e8f9; margin-top: 0.5rem;">Norte: 1 cervejaria para cada 200 mil pessoas | Sul: 1 para cada 32 mil! 6x mais oportunidades no Norte!</p>
</div>
""", unsafe_allow_html=True)

st.markdown("**🏆 Rankings por Estado**")

col1, col2 = st.columns(2)

with col1:
    st.markdown("*Top 10: Número de Cervejarias*")

    brew_state = filtered_df[
        (filtered_df["metric"] == METRIC_BREWERIES) &
        (filtered_df["segment_type"] == "state") &
        (filtered_df["year"] == selected_year)
    ].nlargest(10, "value")

    if not brew_state.empty:
        brew_chart = alt.Chart(brew_state).mark_bar(
            color="#10b981",
            cornerRadiusTopRight=10,
            opacity=0.9
        ).encode(
            x=alt.X("value:Q", title="Cervejarias"),
            y=alt.Y("segment:N", sort="-x", title=""),
            tooltip=[
                alt.Tooltip("segment:N", title="Estado"),
                alt.Tooltip("value:Q", format=",.0f", title="Cervejarias")
            ]
        )

        text = brew_chart.mark_text(align='left', dx=5, fontSize=11, color='#e2e8f0', fontWeight='bold').encode(
            text=alt.Text("value:Q", format=",.0f")
        )

        st.altair_chart(optimize_chart(brew_chart + text, 320), use_container_width=True)

with col2:
    st.markdown("*Top 10: Gasto com Cerveja (R$ bi)*")

    spending_df = filtered_df[
        (filtered_df["metric"] == METRIC_SPENDING) &
        (filtered_df["segment_type"] == "state") &
        (filtered_df["year"] == 2025)
    ].copy()

    # Remover "Outros"
    spending_df = spending_df[spending_df["segment"] != "Outros"].nlargest(10, "value")

    if not spending_df.empty:
        spend_chart = alt.Chart(spending_df).mark_bar(
            color="#f59e0b",
            cornerRadiusTopRight=10,
            opacity=0.9
        ).encode(
            x=alt.X("value:Q", title="R$ bilhões"),
            y=alt.Y("segment:N", sort="-x", title=""),
            tooltip=[
                alt.Tooltip("segment:N", title="Estado"),
                alt.Tooltip("value:Q", format=".2f", title="R$ bi")
            ]
        )

        text = spend_chart.mark_text(align='left', dx=5, fontSize=11, color='#e2e8f0', fontWeight='bold').encode(
            text=alt.Text("value:Q", format=".1f")
        )

        st.altair_chart(optimize_chart(spend_chart + text, 320), use_container_width=True)

st.markdown("---")

# === CONCENTRAÇÃO ===
st.markdown('<div class="section-title">🎯 Estrutura do Mercado: Tsunami Artesanal</div>', unsafe_allow_html=True)

st.markdown("""
<div class="surprise-box">
    <span class="surprise-emoji">🌊</span>
    <strong style="color: #a78bfa; font-size: 1.2rem;">Tsunami Artesanal</strong>
    <p style="color: #c4b5fd; margin-top: 0.5rem;">99% das cervejarias (artesanais) produzem apenas 5% do volume. 1% (grandes marcas) domina 50%! David vs Golias cervejeiro.</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("**📊 Distribuição do Volume Produzido**")
    st.caption("Quem produz quanto?")

    conc_vol = filtered_df[
        (filtered_df["metric"] == METRIC_CONCENTRATION_VOLUME) &
        (filtered_df["year"] == 2024)
    ].copy()

    if not conc_vol.empty:
        vol_donut = alt.Chart(conc_vol).mark_arc(innerRadius=70, outerRadius=110, stroke="#1e293b", strokeWidth=2).encode(
            theta="value:Q",
            color=alt.Color(
                "segment:N",
                scale=alt.Scale(
                    domain=["Top 1%", "Microbreweries"],
                    range=["#10b981", "#334155"]
                ),
                legend=alt.Legend(title="Segmento", titleColor="#e2e8f0", labelColor="#cbd5e1")
            ),
            tooltip=[
                alt.Tooltip("segment:N", title="Segmento"),
                alt.Tooltip("value:Q", format=".1f", title="% do Volume")
            ]
        )

        labels = vol_donut.mark_text(radius=140, fontSize=16, fontWeight='bold', color='#e2e8f0').encode(
            text=alt.Text("value:Q", format=".0f")
        )

        st.altair_chart(optimize_chart(vol_donut + labels, 300), use_container_width=True)

with col2:
    st.markdown("**🏭 Distribuição de Estabelecimentos**")
    st.caption("Número de cervejarias")

    conc_brew = filtered_df[
        (filtered_df["metric"] == METRIC_CONCENTRATION_BREWERIES) &
        (filtered_df["year"] == 2024)
    ].copy()

    if not conc_brew.empty:
        brew_donut = alt.Chart(conc_brew).mark_arc(innerRadius=70, outerRadius=110, stroke="#1e293b", strokeWidth=2).encode(
            theta="value:Q",
            color=alt.Color(
                "segment:N",
                scale=alt.Scale(
                    domain=["Top 1%", "Microbreweries"],
                    range=["#f59e0b", "#334155"]
                ),
                legend=alt.Legend(title="Segmento", titleColor="#e2e8f0", labelColor="#cbd5e1")
            ),
            tooltip=[
                alt.Tooltip("segment:N", title="Segmento"),
                alt.Tooltip("value:Q", format=".1f", title="% Cervejarias")
            ]
        )

        labels = brew_donut.mark_text(radius=140, fontSize=16, fontWeight='bold', color='#e2e8f0').encode(
            text=alt.Text("value:Q", format=".0f")
        )

        st.altair_chart(optimize_chart(brew_donut + labels, 300), use_container_width=True)


st.markdown("---")

st.markdown("""
<div style="text-align: center; margin-top: 3rem; padding: 2rem; color: #64748b;">
    <p style="font-size: 0.9rem;">🎮 Dashboard Gamificado • Dados oficiais MAPA, IBGE e Euromonitor • Última atualização: 2025</p>
</div>
""", unsafe_allow_html=True)
