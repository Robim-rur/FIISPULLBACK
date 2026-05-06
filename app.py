import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

from ta.trend import EMAIndicator, ADXIndicator
from ta.momentum import StochasticOscillator

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Scanner FIIs Blindado", layout="wide")
st.title("🏢 Scanner FIIs - Versão Blindada")

# =========================
# LISTA
# =========================
fiis = [
"HGLG11","BTLG11","XPLG11","BRCO11","VILG11","RBRL11","GARE11","GGRC11","ALZR11",
"LGCP11","GALG11","SDIL11","PATL11","HLOG11","BLMG11",
"XPML11","HGBS11","VISC11","HSML11","MALL11","FIGS11","ABCP11","GSFI11","WPSH11","ELDO11"
]

tickers = [x + ".SA" for x in fiis]

# =========================
# FUNDAMENTOS (SEGUROS)
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
# DATA NORMALIZADA
# =========================
@st.cache_data(ttl=3600)
def get_data(ticker):
    try:
        df = yf.download(ticker, period="1y", progress=False)

        if df is None or df.empty:
            return None

        # flatten colunas
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df[["Open","High","Low","Close","Volume"]]

        # forçar tipo numérico
        df = df.apply(pd.to_numeric, errors='coerce')

        df.dropna(inplace=True)

        if len(df) < 100:
            return None

        return df

    except:
        return None

# =========================
# FUNÇÃO SEGURA PARA PEGAR VALOR
# =========================
def safe_last(series):
    try:
        return float(series.iloc[-1])
    except:
        return None

# =========================
# FILTRO FUNDAMENTAL
# =========================
def filtro_fundamental(ticker):
    try:
        t = ticker.replace(".SA","")

        if t not in fundamentos:
            return False

        f = fundamentos[t]

        return (
            f["pvp"] < 1.05 and
            f["vac"] < 0.06 and
            f["cap"] > 0.08
        )
    except:
        return False

# =========================
# INDICADORES SEGUROS
# =========================
def add_indicators(df):

    try:
        close = pd.Series(df["Close"].values.flatten(), index=df.index)
        high = pd.Series(df["High"].values.flatten(), index=df.index)
        low = pd.Series(df["Low"].values.flatten(), index=df.index)

        df["ema69"] = EMAIndicator(close, 69).ema_indicator()

        stoch = StochasticOscillator(high, low, close, 14, 3)
        df["k"] = stoch.stoch()
        df["d"] = stoch.stoch_signal()

        adx = ADXIndicator(high, low, close, 14)
        df["adx"] = adx.adx()

        df.dropna(inplace=True)

        return df

    except:
        return None

# =========================
# SCANNER
# =========================
results = []
progress = st.progress(0)

max_assets = st.sidebar.slider("Qtd de ativos", 5, len(tickers), 15)

selected = tickers[:max_assets]

for i, ticker in enumerate(selected):

    try:
        # FUNDAMENTO PRIMEIRO
        if not filtro_fundamental(ticker):
            progress.progress((i+1)/len(selected))
            continue

        df = get_data(ticker)

        if df is None:
            continue

        vol = safe_last(df["Volume"])
        if vol is None or vol < 200000:
            continue

        df = add_indicators(df)

        if df is None or df.empty:
            continue

        last = df.iloc[-1]

        close = safe_last(df["Close"])
        ema = safe_last(df["ema69"])
        adx = safe_last(df["adx"])
        k = safe_last(df["k"])
        d = safe_last(df["d"])

        if None in [close, ema, adx, k, d]:
            continue

        score = 0
        if close > ema: score += 30
        if adx > 15: score += 30
        if k > d: score += 40

        t = ticker.replace(".SA","")

        results.append({
            "Ticker": t,
            "Preço": round(close,2),
            "Score": score,
            "P/VP": fundamentos.get(t, {}).get("pvp", None),
            "Vacância": fundamentos.get(t, {}).get("vac", None),
            "Cap Rate": fundamentos.get(t, {}).get("cap", None)
        })

    except:
        continue

    progress.progress((i+1)/len(selected))

df_res = pd.DataFrame(results)

# =========================
# OUTPUT
# =========================
if not df_res.empty:
    df_res = df_res.sort_values(by="Score", ascending=False)

    st.subheader("🏆 Ranking Blindado")
    st.dataframe(df_res, use_container_width=True)

else:
    st.warning("Nenhum ativo passou nos filtros.")
