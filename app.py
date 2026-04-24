import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

st.set_page_config(layout="wide")

stocks = ["AAPL","MSFT","GOOGL","AMZN","NVDA","META","TSLA","AMD","AVGO","ASML"]

st.title("📊 Dashboard Ações")

@st.cache_data(ttl=300)
def get_data(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="3mo")
    info = stock.fast_info
    return hist, info

data = []

for s in stocks:
    hist, info = get_data(s)
    if len(hist) < 30:
        continue

    price = hist["Close"].iloc[-1]

    def perf(days):
        try:
            return ((price / hist["Close"].iloc[-days]) - 1) * 100
        except:
            return 0

    p5 = perf(5)
    p7 = perf(7)
    p14 = perf(14)
    p30 = perf(30)

    signal = "Normal"
    if p30 <= -20:
        signal = "🔥🔥 Oportunidade"
    elif p30 <= -15:
        signal = "⚠️ Atenção"

    data.append([s, price, p5, p7, p14, p30, signal])

df = pd.DataFrame(data, columns=["Ticker","Preço","5d","7d","14d","30d","Sinal"])

selected = st.selectbox("Seleciona a ação", df["Ticker"])

st.dataframe(df, use_container_width=True)

st.subheader(f"📈 Gráfico: {selected}")

hist, _ = get_data(selected)

period = st.radio("Período", ["1 mês","3 meses"])

if period == "1 mês":
    chart_data = hist.tail(30)
else:
    chart_data = hist

st.line_chart(chart_data["Close"])

# análise automática
last30 = ((chart_data["Close"].iloc[-1] / chart_data["Close"].iloc[0]) - 1) * 100

st.subheader("📊 Análise")

if last30 <= -20:
    st.error("Queda superior a 20%. Pode ser oportunidade, mas verifica notícias.")
elif last30 <= -15:
    st.warning("Queda relevante. Boa zona para analisar entrada.")
else:
    st.info("Sem queda significativa recente.")
