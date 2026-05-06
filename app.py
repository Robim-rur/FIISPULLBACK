import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

from ta.trend import EMAIndicator, ADXIndicator
from ta.momentum import StochasticOscillator

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Scanner FIIs Profissional", layout="wide")
st.title("🏢 Scanner FIIs - Pullback + Probabilidade (1.5%)")

# =========================
# SETORES
# =========================
setores = {
"Logística": ["HGLG11","BTLG11","XPLG11","BRCO11","VILG11","RBRL11","GARE11","GGRC11","LVBI11","PATL11","SDIL11","HLOG11"],
"Shoppings": ["XPML11","HGBS11","VISC11","HSML11","MALL11","ABCP11","FIGS11"],
"Lajes": ["PVBI11","HGRE11","JSRE11","BRCR11","VINO11"],
"Híbridos": ["KNRI11","HGRU11","TRXF11","ALZR11"]
}

# =========================
# LISTA FINAL
# =========================
fiis = sorted(set(sum(setores.values(), [])))
tickers = [x + ".SA" for x in fiis]

# =========================
# FUNÇÕES
# =========================
def get_setor(ticker):
    t = ticker.replace(".SA","")
    for setor, lista in setores.items():
        if t in lista:
            return setor
    return "Outros"

@st.cache_data(ttl=3600)
def get_data(ticker):
    try:
        df = yf.download(ticker, period="1y", progress=False)

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
        df["di_plus"] = adx.adx_pos()
        df["di_minus"] = adx.adx_neg()

        return df.dropna()
    except:
        return None

def weekly_confirmation(ticker):
    df = get_data(ticker)
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

def falso_rompimento(df):
    if len(df) < 2:
        return True
    last = df.iloc[-1]
    prev = df.iloc[-2]
    return last["High"] > prev["High"] and last["Close"] < prev["High"]

def probabilidade(df):
    ganhos = 0
    total = 0

    for i in range(len(df)-10):
        entrada = df["Close"].iloc[i]
        alvo = entrada * 1.015

        janela = df["High"].iloc[i:i+10]

        if len(janela) < 10:
            continue

        total += 1
        if janela.max() >= alvo:
            ganhos += 1

    if total == 0:
        return 0

    return round((ganhos/total)*100,1)

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
        volume = 0

    df = add_indicators(df)
    if df is None or df.empty:
        continue

    last = df.iloc[-1]

    trend = last["Close"] > last["ema69"]
    dmi_ok = last["di_plus"] > last["di_minus"]
    trigger = last["k"] > last["d"]
    semanal = weekly_confirmation(ticker)

    falso = falso_rompimento(df)

    prob = probabilidade(df)

    # SCORE COMPLETO (SEM EXCLUSÃO)
    score = 0
    if trend: score += 25
    if dmi_ok: score += 25
    if trigger: score += 20
    if semanal: score += 20
    if volume > 200000: score += 5
    if not falso: score += 5

    results.append({
        "Ticker": ticker.replace(".SA",""),
        "Setor": get_setor(ticker),
        "Preço": round(last["Close"],2),
        "Volume": int(volume),
        "Prob +1.5%": prob,
        "Score": score
    })

    progress.progress((i+1)/len(tickers))

df_res = pd.DataFrame(results)

# =========================
# OUTPUT
# =========================
if not df_res.empty:

    df_res = df_res.sort_values(by=["Score","Prob +1.5%"], ascending=False)

    def classificar(score):
        if score >= 70:
            return "ENTRADA"
        elif score >= 40:
            return "OBSERVAR"
        else:
            return "DESCARTAR"

    df_res["Classificação"] = df_res["Score"].apply(classificar)

    # =========================
    # HEATMAP
    # =========================
    def heatmap(val):
        if val >= 70:
            return "background-color: #00cc66"
        elif val >= 40:
            return "background-color: #ffcc00"
        else:
            return "background-color: #ff4d4d"

    st.subheader("🔥 Heatmap Geral")

    st.dataframe(
        df_res.style.applymap(heatmap, subset=["Score"]),
        use_container_width=True
    )

    # =========================
    # MELHOR POR SETOR
    # =========================
    st.subheader("🏆 Melhor por Setor")

    top_setor = df_res.groupby("Setor").head(1)
    st.dataframe(top_setor, use_container_width=True)

    # =========================
    # RANKING POR SETOR
    # =========================
    st.subheader("📊 Ranking por Setor")

    for setor in df_res["Setor"].unique():
        st.markdown(f"### {setor}")
        st.dataframe(
            df_res[df_res["Setor"] == setor],
            use_container_width=True
        )

    # =========================
    # ALERTA
    # =========================
    entradas = df_res[df_res["Classificação"] == "ENTRADA"]

    if not entradas.empty:
        st.success("🚨 OPORTUNIDADES ENCONTRADAS")
        st.dataframe(entradas.head(3), use_container_width=True)
    else:
        st.info("Nenhuma entrada clara no momento.")

else:
    st.warning("Nenhum ativo encontrado.")
