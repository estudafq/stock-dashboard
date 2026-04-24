import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(layout="wide")

# Lista de ações
stocks = ["AAPL","MSFT","GOOGL","AMZN","NVDA","META","TSLA","AMD","AVGO","ASML"]

st.title("📊 Dashboard Ações")

# Função para obter dados (corrigida para evitar erro de cache)
@st.cache_data(ttl=300)
def get_data(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="6mo")
    return hist

# Construir tabela
data = []

for s in stocks:
    hist = get_data(s)

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

    # Sinal
    signal = "Normal"
    if p30 <= -20:
        signal = "🔥🔥 Oportunidade"
    elif p30 <= -15:
        signal = "⚠️ Atenção"

    data.append([s, price, p5, p7, p14, p30, signal])

df = pd.DataFrame(data, columns=["Ticker","Preço","5d","7d","14d","30d","Sinal"])

# Seleção
selected = st.selectbox("Seleciona a ação", df["Ticker"])

# Mostrar tabela
st.dataframe(df, use_container_width=True)

# Gráfico
st.subheader(f"📈 Gráfico: {selected}")

hist = get_data(selected)

period = st.radio("Período", ["1 mês","3 meses","6 meses"])

if period == "1 mês":
    chart_data = hist.tail(30)
elif period == "3 meses":
    chart_data = hist.tail(90)
else:
    chart_data = hist

st.line_chart(chart_data["Close"])

# Análise automática
st.subheader("📊 Análise automática")

last = chart_data["Close"].iloc[-1]
first = chart_data["Close"].iloc[0]
variation = ((last / first) - 1) * 100

if variation <= -20:
    st.error("Queda superior a 20%. Pode ser oportunidade, mas verifica notícias e resultados.")
elif variation <= -15:
    st.warning("Queda relevante. Boa zona para analisar entrada.")
elif variation >= 15:
    st.info("Subida forte recente. Evitar comprar por impulso.")
else:
    st.success("Comportamento estável sem sinais extremos.")

# Info extra
st.subheader("📌 Sugestão")

st.write("""
✔ Confirmar sempre com notícias  
✔ Ver se a queda foi por resultados  
✔ Analisar tendência geral do mercado  
✔ Não comprar só porque caiu  
""")
