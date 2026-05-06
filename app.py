import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

from ta.trend import EMAIndicator, ADXIndicator
from ta.momentum import StochasticOscillator

st.set_page_config(page_title="Scanner FII Institucional", layout="wide")
st.title("🏢 Scanner Institucional FIIs (Pullback + Probabilidade 2%)")

# =========================
# LISTA AMPLIADA (TIJOLO)
# =========================
fiis = [
# Logística
"HGLG11","BTLG11","XPLG11","BRCO11","VILG11","RBRL11","GARE11","GGRC11",
"SDIL11","PATL11","HLOG11","ALZR11","LGCP11",

# Shoppings
"XPML11","HGBS11","VISC11","HSML11","MALL11","ABCP11","FIGS11",

# Lajes
"PVBI11","HGRE11","JSRE11","BRCR11","VINO11",

# Híbridos com tijolo forte
"KNRI11","HGRU11"
]

tickers = [x + ".SA" for x in fiis]

# =========================
# DATA
# =========================
@st.cache_data(ttl=3600)
def get_data(ticker, period="1y"):
    try:
        df = yf.download(ticker, period=period, progress=False)

        if df is None or df.empty:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df[["Open","High","Low","Close","Volume"]]
        df = df.apply(pd.to_numeric, errors='coerce')
        df.dropna(inplace=True)

        if len(df) < 100:
            return None

        return df
    except:
        return None

# =========================
# INDICADORES
# =========================
def add_indicators(df):

    close = pd.Series(df["Close"].values.flatten(), index=df.index)
    high = pd.Series(df["High"].values.flatten(), index=df.index)
    low = pd.Series(df["Low"].values.flatten(), index=df.index)

    df["ema69"] = EMAIndicator(close, 69).ema_indicator()

    stoch = StochasticOscillator(high, low, close, 14, 3)
    df["k"] = stoch.stoch()
    df["d"] = stoch.stoch_signal()

    adx = ADXIndicator(high, low, close, 14)
    df["adx"] = adx.adx()
    df["di_plus"] = adx.adx_pos()
    df["di_minus"] = adx.adx_neg()

    return df.dropna()

# =========================
# CONFIRMAÇÃO SEMANAL
# =========================
def weekly_confirmation(ticker):
    df = get_data(ticker, "2y")

    if df is None:
        return False

    df = df.resample("1W").last()
    df = add_indicators(df)

    if df is None or df.empty:
        return False

    last = df.iloc[-1]

    return (
        last["Close"] > last["ema69"] and
        last["di_plus"] > last["di_minus"] and
        last["k"] > last["d"]
    )

# =========================
# FALSO ROMPIMENTO
# =========================
def falso_rompimento(df):
    if len(df) < 2:
        return True

    last = df.iloc[-1]
    prev = df.iloc[-2]

    return last["High"] > prev["High"] and last["Close"] < prev["High"]

# =========================
# PROBABILIDADE +2%
# =========================
def probabilidade_2(df):

    ganhos = 0
    total = 0

    for i in range(len(df)-10):
        entrada = df["Close"].iloc[i]
        alvo = entrada * 1.02  # 🔥 AJUSTADO PRA 2%

        janela = df["High"].iloc[i:i+10]

        if len(janela) < 10:
            continue

        total += 1

        if janela.max() >= alvo:
            ganhos += 1

    if total == 0:
        return 0

    return round((ganhos / total) * 100, 1)

# =========================
# STATUS
# =========================
def status_ativo(trend, trigger):
    if not trend:
        return "Perdeu Tendência"
    elif not trigger:
        return "Observação"
    else:
        return "Setup Ativo"

# =========================
# SCANNER
# =========================
results = []
progress = st.progress(0)

for i, ticker in enumerate(tickers):

    df = get_data(ticker)

    if df is None:
        continue

    try:
        volume = float(df["Volume"].iloc[-1])
    except:
        continue

    if volume < 200000:
        continue

    df = add_indicators(df)

    if df is None or df.empty:
        continue

    last = df.iloc[-1]

    trend = last["Close"] > last["ema69"]
    dmi_ok = last["di_plus"] > last["di_minus"]
    trigger = last["k"] > last["d"]

    semanal = weekly_confirmation(ticker)

    if falso_rompimento(df):
        continue

    prob = probabilidade_2(df)

    score = 0
    if trend: score += 25
    if dmi_ok: score += 25
    if trigger: score += 25
    if semanal: score += 25

    results.append({
        "Ticker": ticker.replace(".SA",""),
        "Preço": round(last["Close"],2),
        "Volume": int(volume),
        "Prob +2%": prob,
        "Score": score,
        "Semanal": semanal,
        "Status": status_ativo(trend, trigger)
    })

    progress.progress((i+1)/len(tickers))

df_res = pd.DataFrame(results)

# =========================
# OUTPUT
# =========================
if not df_res.empty:

    df_res = df_res.sort_values(by=["Score","Prob +2%"], ascending=False)

    st.subheader("🏆 Ranking Institucional")
    st.dataframe(df_res, use_container_width=True)

    st.subheader("🔥 Entradas Premium")

    entradas = df_res[
        (df_res["Score"] >= 75) &
        (df_res["Status"] == "Setup Ativo")
    ]

    st.dataframe(entradas, use_container_width=True)

else:
    st.warning("Nenhum ativo encontrado.")
