import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Dashboard Ações", page_icon="📊", layout="wide")

# 🔥 layout full width
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
    return yf.Ticker(ticker).history(period="1y").dropna()

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

    if ticker == "QQQ3.MI":
        if min(vals) <= -20:
            return "🔥 Entrada 3x"
        if min(vals) <= -15:
            return "⚠️ Atenção 3x"

    if min(vals) <= -20:
        return "🔥 Queda >20%"
    if min(vals) <= -15:
        return "⚠️ Queda >15%"
    if max(vals) >= 20:
        return "📈 Subida forte"
    return "Normal"

rows = []

for ticker in TICKERS:
    hist = get_history(ticker)

    if hist.empty or len(hist) < 30:
        continue

    price = hist["Close"].iloc[-1]

    rows.append({
        "Ticker": NAMES.get(ticker, ticker),
        "raw": ticker,
        "Preço": price,
        "Hoje %": calc_variation(hist, 2),
        "5d": calc_variation(hist, 5),
        "7d": calc_variation(hist, 7),
        "14d": calc_variation(hist, 14),
        "30d": calc_variation(hist, 30),
        "3m": calc_variation(hist, 63),
        "6m": calc_variation(hist, 126),
    })

df = pd.DataFrame(rows)

styled_df = df.drop(columns=["raw"]).style.format({
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
        st.session_state.selected_ticker = df.iloc[idx]["raw"]
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
chart = hist.tail(days)

st.markdown(f"### 📈 {NAMES.get(ticker, ticker)} ({st.session_state.selected_period})")

fig = go.Figure()
fig.add_trace(go.Scatter(x=chart.index, y=chart["Close"]))

st.plotly_chart(fig, use_container_width=True)
