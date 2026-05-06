import streamlit as st
import pandas as pd
import yfinance as yf

from ta.trend import EMAIndicator, ADXIndicator
from ta.momentum import StochasticOscillator

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Scanner FIIs Premium", layout="wide")
st.title("🏢 Scanner FIIs - Tijolo + Fundamentos")

# =========================
# LISTA (SUA)
# =========================
fiis = [
"HGLG11","BTLG11","XPLG11","BRCO11","VILG11","RBRL11","GARE11","GGRC11","ALZR11",
"LGCP11","GALG11","SDIL11","PATL11","HLOG11","BLMG11",
"XPML11","HGBS11","VISC11","HSML11","MALL11","FIGS11","ABCP11","GSFI11","WPSH11","ELDO11"
]

tickers = [x + ".SA" for x in fiis]

# =========================
# FUNDAMENTOS (SIMULADO / EDITÁVEL)
# =========================
fundamentos = {
"HGLG11": {"pvp":0.98, "vac":0.03, "cap":0.09},
"BTLG11": {"pvp":1.02, "vac":0.04, "cap":0.085},
"XPLG11": {"pvp":1.01, "vac":0.05, "cap":0.082},
"BRCO11": {"pvp":1.00, "vac":0.04, "cap":0.088},
"VILG11": {"pvp":0.97, "vac":0.02, "cap":0.09},
"GARE11": {"pvp":0.95, "vac":0.03, "cap":0.095},
"GGRC11": {"pvp":0.92, "vac":0.01, "cap":0.10},
"XPML11": {"pvp":1.03, "vac":0.04, "cap":0.08},
"HGBS11": {"pvp":1.02, "vac":0.05, "cap":0.078},
"VISC11": {"pvp":1.01, "vac":0.04, "cap":0.079},
"HSML11": {"pvp":0.99, "vac":0.03, "cap":0.085},
"MALL11": {"pvp":0.96, "vac":0.02, "cap":0.087},
}

# =========================
# DATA
# =========================
@st.cache_data(ttl=3600)
def get_data(ticker):
    try:
        df = yf.download(ticker, period="1y", progress=False)
        if df.empty:
            return None
        df = df[["Open","High","Low","Close","Volume"]]
        df.dropna(inplace=True)
        return df
    except:
        return None

# =========================
# FILTRO FUNDAMENTAL
# =========================
def filtro_fundamental(ticker):
    t = ticker.replace(".SA","")

    if t not in fundamentos:
        return False

    f = fundamentos[t]

    return (
        f["pvp"] < 1.05 and
        f["vac"] < 0.06 and
        f["cap"] > 0.08
    )

# =========================
# INDICADORES
# =========================
def add_indicators(df):
    df["ema69"] = EMAIndicator(df["Close"], 69).ema_indicator()

    stoch = StochasticOscillator(df["High"], df["Low"], df["Close"], 14, 3)
    df["k"] = stoch.stoch()
    df["d"] = stoch.stoch_signal()

    adx = ADXIndicator(df["High"], df["Low"], df["Close"], 14)
    df["adx"] = adx.adx()

    return df

# =========================
# SCANNER
# =========================
results = []
progress = st.progress(0)

for i, ticker in enumerate(tickers):

    # FILTRO FUNDAMENTAL PRIMEIRO
    if not filtro_fundamental(ticker):
        progress.progress((i+1)/len(tickers))
        continue

    df = get_data(ticker)

    if df is None or len(df) < 100:
        continue

    # liquidez
    if df["Volume"].iloc[-1] < 200000:
        continue

    df = add_indicators(df)
    last = df.iloc[-1]

    score = 0
    if last["Close"] > last["ema69"]: score += 30
    if last["adx"] > 15: score += 30
    if last["k"] > last["d"]: score += 40

    results.append({
        "Ticker": ticker.replace(".SA",""),
        "Preço": round(last["Close"],2),
        "Score": score,
        "P/VP": fundamentos[ticker.replace(".SA","")]["pvp"],
        "Vacância": fundamentos[ticker.replace(".SA","")]["vac"],
        "Cap Rate": fundamentos[ticker.replace(".SA","")]["cap"]
    })

    progress.progress((i+1)/len(tickers))

df_res = pd.DataFrame(results)

# =========================
# OUTPUT
# =========================
if not df_res.empty:
    df_res = df_res.sort_values(by="Score", ascending=False)

    st.subheader("🏆 Ranking Premium")
    st.dataframe(df_res, use_container_width=True)

else:
    st.warning("Nenhum FII passou nos filtros.")
