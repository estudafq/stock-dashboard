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

def fmt_pct(v):
    if v is None:
        return "n/d"
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.2f}%"

def pct_html(v):
    if v is None:
        return "<span style='color:#94a3b8'>n/d</span>"
    color = "#22c55e" if v >= 0 else "#ef4444"
    sign = "+" if v >= 0 else ""
    return f"<span style='color:{color}; font-weight:700'>{sign}{v:.2f}%</span>"

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

    values = {label: calc_variation(hist, days) for label, days in PERIODS.items()}

    rows.append({
        "Ticker": ticker,
        "Preço": price,
        "Hoje": today,
        **values,
        "Sinal": signal(values["30d"], values["3m"], values["6m"])
    })

df = pd.DataFrame(rows)

st.markdown("### Tabela geral, clica na ação ou numa percentagem")

header = st.columns([1.2, 1.5, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.8])
headers = ["Ticker", "Preço", "Hoje", "5d", "7d", "14d", "30d", "3m", "6m", "Sinal"]

for col, h in zip(header, headers):
    col.markdown(f"**{h}**")

for _, row in df.iterrows():
    cols = st.columns([1.2, 1.5, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.8])

    ticker = row["Ticker"]

    if cols[0].button(ticker, key=f"{ticker}_ticker", use_container_width=True):
        st.session_state.selected_ticker = ticker
        st.session_state.selected_period = "30d"
        st.rerun()

    cols[1].markdown(
        f"**{row['Preço']:.2f}** ({pct_html(row['Hoje'])})",
        unsafe_allow_html=True
    )

    cols[2].markdown(pct_html(row["Hoje"]), unsafe_allow_html=True)

    for i, p in enumerate(["5d", "7d", "14d", "30d", "3m", "6m"], start=3):
        label = fmt_pct(row[p])
        if cols[i].button(label, key=f"{ticker}_{p}", use_container_width=True):
            st.session_state.selected_ticker = ticker
            st.session_state.selected_period = p
            st.rerun()

    cols[9].markdown(row["Sinal"])

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
