import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="Dashboard Ações",
    page_icon="📊",
    layout="wide"
)

TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AMD", "AVGO", "ASML"]

PERIOD_MAP = {
    "5d": 5,
    "7d": 7,
    "14d": 14,
    "30d": 30,
    "3m": 63,
    "6m": 126
}

st.title("📊 Dashboard Ações")

@st.cache_data(ttl=300)
def get_history(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1y", interval="1d")
    hist = hist.dropna()
    return hist

def calc_variation(hist, days):
    if len(hist) <= days:
        return None
    last = hist["Close"].iloc[-1]
    previous = hist["Close"].iloc[-days]
    return ((last / previous) - 1) * 100

def format_price_and_change(price, change):
    if change is None:
        return f"{price:.2f} (n/d)"
    sign = "+" if change >= 0 else ""
    return f"{price:.2f} ({sign}{change:.2f}%)"

def format_percent(value):
    if value is None:
        return "n/d"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}%"

def signal_from_variation(v30, v3m, v6m):
    values = [v for v in [v30, v3m, v6m] if v is not None]
    if not values:
        return "Sem dados"

    min_drop = min(values)

    if min_drop <= -20:
        return "🔥🔥 Queda > 20%"
    elif min_drop <= -15:
        return "⚠️ Queda > 15%"
    elif min_drop >= 15:
        return "📈 Subida forte"
    else:
        return "Normal"

rows = []

for ticker in TICKERS:
    hist = get_history(ticker)

    if hist.empty or len(hist) < 30:
        continue

    price = hist["Close"].iloc[-1]
    daily_change = calc_variation(hist, 2)

    v5 = calc_variation(hist, 5)
    v7 = calc_variation(hist, 7)
    v14 = calc_variation(hist, 14)
    v30 = calc_variation(hist, 30)
    v3m = calc_variation(hist, 63)
    v6m = calc_variation(hist, 126)

    rows.append({
        "Ticker": ticker,
        "Preço": format_price_and_change(price, daily_change),
        "Hoje %": daily_change,
        "5d": v5,
        "7d": v7,
        "14d": v14,
        "30d": v30,
        "3m": v3m,
        "6m": v6m,
        "Sinal": signal_from_variation(v30, v3m, v6m)
    })

df = pd.DataFrame(rows)

display_df = df.copy()

for col in ["Hoje %", "5d", "7d", "14d", "30d", "3m", "6m"]:
    display_df[col] = display_df[col].apply(format_percent)

def color_values(value):
    if isinstance(value, str):
        if value.startswith("+"):
            return "color: #22c55e; font-weight: 700;"
        if value.startswith("-"):
            return "color: #ef4444; font-weight: 700;"
    return ""

styled_df = display_df.style.map(color_values)

st.markdown("### Tabela geral")

event = st.dataframe(
    styled_df,
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-cell"
)

selected_ticker = df.iloc[0]["Ticker"]
selected_period_label = "30d"
selected_days = 30

try:
    selected = event.selection

    if selected.get("cells"):
        cell = selected["cells"][0]
        row_index = cell["row"]
        column_name = cell["column"]

        selected_ticker = df.iloc[row_index]["Ticker"]

        if column_name in PERIOD_MAP:
            selected_period_label = column_name
            selected_days = PERIOD_MAP[column_name]
        else:
            selected_period_label = "30d"
            selected_days = 30

    elif selected.get("rows"):
        row_index = selected["rows"][0]
        selected_ticker = df.iloc[row_index]["Ticker"]
        selected_period_label = "30d"
        selected_days = 30

except Exception:
    pass

hist = get_history(selected_ticker)
chart_data = hist.tail(selected_days)

st.markdown(f"### 📈 Gráfico: {selected_ticker}, período {selected_period_label}")

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=chart_data.index,
    y=chart_data["Close"],
    mode="lines",
    name="Preço de fecho"
))

fig.update_layout(
    height=480,
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
    st.error(f"{selected_ticker} caiu {variation:.2f}% no período selecionado. É uma queda superior a 20%, pode ser zona de oportunidade, mas exige confirmação com notícias, resultados e tendência geral do mercado.")
elif variation <= -15:
    st.warning(f"{selected_ticker} caiu {variation:.2f}% no período selecionado. É uma queda relevante, boa zona para analisar com calma.")
elif variation >= 15:
    st.info(f"{selected_ticker} subiu {variation:.2f}% no período selecionado. Pode haver risco de compra por impulso.")
else:
    st.success(f"{selected_ticker} variou {variation:.2f}% no período selecionado. Sem sinal extremo.")

st.caption("Dados obtidos via yfinance. Podem ter atraso e não substituem análise financeira profissional.")
