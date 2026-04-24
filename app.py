import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Dashboard Ações", page_icon="📊", layout="wide")

TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AMD", "AVGO", "ASML"]

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
    hist = yf.Ticker(ticker).history(period="1y", interval="1d")
    return hist.dropna()

def calc_variation(hist, days):
    if len(hist) <= days:
        return None
    last = hist["Close"].iloc[-1]
    previous = hist["Close"].iloc[-days]
    return ((last / previous) - 1) * 100

def signal(v30, v3m, v6m):
    values = [v for v in [v30, v3m, v6m] if v is not None]
    if not values:
        return "Sem dados"

    min_v = min(values)
    max_v = max(values)

    if min_v <= -20:
        return "🔥 Queda > 20%"
    if min_v <= -15:
        return "⚠️ Queda > 15%"
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
        "Ticker": ticker,
        "Preço": price,
        "Hoje %": today,
        "5d": v5,
        "7d": v7,
        "14d": v14,
        "30d": v30,
        "3m": v3m,
        "6m": v6m,
        "Sinal": signal(v30, v3m, v6m)
    })

df = pd.DataFrame(rows)

def color_pct(value):
    if isinstance(value, (int, float)):
        if value > 0:
            return "color: #22c55e; font-weight: 700;"
        if value < 0:
            return "color: #ef4444; font-weight: 700;"
    return ""

styled_df = df.style.format({
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
st.caption("Podes ordenar a tabela clicando nos cabeçalhos. Clica numa linha para escolher a ação.")

event = st.dataframe(
    styled_df,
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row"
)

try:
    selected_rows = event.selection.rows
    if selected_rows:
        st.session_state.selected_ticker = df.iloc[selected_rows[0]]["Ticker"]
except Exception:
    pass

st.markdown("### Escolhe o período do gráfico")

period = st.segmented_control(
    "Período",
    options=list(PERIODS.keys()),
    default=st.session_state.selected_period,
    label_visibility="collapsed"
)

if period:
    st.session_state.selected_period = period

selected_ticker = st.session_state.selected_ticker
selected_period = st.session_state.selected_period
selected_days = PERIODS[selected_period]

hist = get_history(selected_ticker)
chart_data = hist.tail(selected_days)

st.markdown(f"### 📈 Gráfico: {selected_ticker}, período {selected_period}")

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=chart_data.index,
    y=chart_data["Close"],
    mode="lines+markers",
    name=selected_ticker
))

fig.update_layout(
    height=500,
    margin=dict(l=20, r=20, t=40, b=20),
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
    st.error(f"{selected_ticker} caiu {variation:.2f}% em {selected_period}. Queda superior a 20%, pode ser oportunidade, mas confirma notícias, resultados e tendência geral.")
elif variation <= -15:
    st.warning(f"{selected_ticker} caiu {variation:.2f}% em {selected_period}. Queda relevante, boa zona para analisar entrada.")
elif variation >= 20:
    st.info(f"{selected_ticker} subiu {variation:.2f}% em {selected_period}. Cuidado com compra por impulso.")
else:
    st.success(f"{selected_ticker} variou {variation:.2f}% em {selected_period}. Sem sinal extremo.")

st.caption("Dados obtidos via yfinance. Podem ter atraso e não substituem análise financeira profissional.")
