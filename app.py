import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Dashboard Ações", page_icon="📊", layout="wide")

st.markdown("""
<style>
.block-container {
    padding-left: 1rem;
    padding-right: 1rem;
    max-width: 100% !important;
}
</style>
""", unsafe_allow_html=True)

TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "META", "TSLA", "AMD", "AVGO", "ASML",
    "QQQ3.MI"
]

NAMES = {
    "QQQ3.MI": "QQQ3 (Nasdaq 3x)"
}

PERIODS = {
    "5d": 5,
    "7d": 7,
    "14d": 14,
    "30d": 30,
    "3m": 63,
    "6m": 126
}

if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = "AAPL"

if "selected_period" not in st.session_state:
    st.session_state.selected_period = "30d"

st.title("📊 Dashboard Ações")

@st.cache_data(ttl=300)
def get_history(ticker):
    return yf.Ticker(ticker).history(period="1y", interval="1d").dropna()

def calc_variation(hist, days):
    if len(hist) <= days:
        return None
    return ((hist["Close"].iloc[-1] / hist["Close"].iloc[-days]) - 1) * 100

def color_pct(val):
    if isinstance(val, (int, float)):
        if val > 0:
            return "color:#22c55e; font-weight:700;"
        if val < 0:
            return "color:#ef4444; font-weight:700;"
    return ""

def signal(v30, v3m, v6m, ticker):
    vals = [v for v in [v30, v3m, v6m] if v is not None]
    if not vals:
        return "Sem dados"

    min_v = min(vals)
    max_v = max(vals)

    if ticker == "QQQ3.MI":
        if min_v <= -20:
            return "🔥 Entrada 3x"
        if min_v <= -15:
            return "⚠️ Atenção 3x"

    if min_v <= -20:
        return "🔥 Queda >20%"
    if min_v <= -15:
        return "⚠️ Queda >15%"
    if max_v >= 20:
        return "📈 Subida forte"
    return "Normal"

rows = []

for ticker in TICKERS:
    hist = get_history(ticker)

    if hist.empty or len(hist) < 30:
        continue

    price = hist["Close"].iloc[-1]
    today = calc_variation(hist, 2)

    v5 = calc_variation(hist, 5)
    v7 = calc_variation(hist, 7)
    v14 = calc_variation(hist, 14)
    v30 = calc_variation(hist, 30)
    v3m = calc_variation(hist, 63)
    v6m = calc_variation(hist, 126)

    rows.append({
        "Ticker": NAMES.get(ticker, ticker),
        "raw_ticker": ticker,
        "Preço": price,
        "Hoje %": today,
        "5d": v5,
        "7d": v7,
        "14d": v14,
        "30d": v30,
        "3m": v3m,
        "6m": v6m,
        "Sinal": signal(v30, v3m, v6m, ticker)
    })

df = pd.DataFrame(rows)

styled_df = df.drop(columns=["raw_ticker"]).style.format({
    "Preço": "{:.2f}",
    "Hoje %": "{:+.2f}%",
    "5d": "{:+.2f}%",
    "7d": "{:+.2f}%",
    "14d": "{:+.2f}%",
    "30d": "{:+.2f}%",
    "3m": "{:+.2f}%",
    "6m": "{:+.2f}%"
}).map(color_pct, subset=["Hoje %", "5d", "7d", "14d", "30d", "3m", "6m"])

st.markdown("### Tabela geral")
st.caption("Ordena clicando nos títulos. Clica numa linha para selecionar a ação.")

event = st.dataframe(
    styled_df,
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row"
)

try:
    if event.selection.rows:
        idx = event.selection.rows[0]
        st.session_state.selected_ticker = df.iloc[idx]["raw_ticker"]
except:
    pass

st.markdown("### Período")

period = st.segmented_control(
    "Período",
    options=list(PERIODS.keys()),
    default=st.session_state.selected_period,
    label_visibility="collapsed"
)

if period:
    st.session_state.selected_period = period

ticker = st.session_state.selected_ticker
days = PERIODS[st.session_state.selected_period]

hist = get_history(ticker)
chart_data = hist.tail(days)

name = NAMES.get(ticker, ticker)

st.markdown(f"### 📈 Gráfico: {name}, período {st.session_state.selected_period}")

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=chart_data.index,
    y=chart_data["Close"],
    mode="lines",
    name=name
))

fig.update_layout(
    height=500,
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis_title="Data",
    yaxis_title="Preço",
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

first = chart_data["Close"].iloc[0]
last = chart_data["Close"].iloc[-1]
variation = ((last / first) - 1) * 100

st.markdown("### 📊 Análise automática")

if variation <= -20:
    st.error(f"{name} caiu {variation:.2f}%. Possível oportunidade, mas confirmar fundamentos.")
elif variation <= -15:
    st.warning(f"{name} caiu {variation:.2f}%. Boa zona para analisar.")
elif variation >= 20:
    st.info(f"{name} subiu {variation:.2f}%. Cuidado com entrada tardia.")
else:
    st.success(f"{name} variou {variation:.2f}%. Sem sinal extremo.")

st.caption("Dados via yfinance. Podem ter atraso.")
