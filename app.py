import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

from ta.trend import EMAIndicator, ADXIndicator
from ta.momentum import StochasticOscillator

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Scanner FIIs Institucional", layout="wide")
st.title("🏢 Scanner Institucional - FIIs de Tijolo")

# =========================
# SUA LISTA COMPLETA
# =========================
raw_fiis = """
AAZQ11, ABCP11, AJFI11, ALMI11, ALZR11, AMAR11, ANCR11, APTO11, ARCT11, ARRI11,
ASMT11, ATCR11, ATSA11, BARI11, BBFI11, BBIM11, BBPO11, BBRC11, BEVA11, BLCP11,
BLMC11, BLMO11, BMLC11, BNFS11, BPFF11, BPML11, BPRP11, BRCO11, BRCR11, BRIM11,
BRIO11, BRPR11, BSLH11, BTLG11, BTRA11, BTSG11, BTWR11, BZLI11, CACR11, CARE11,
CBOP11, CCME11, CEOC11, CFHI11, CJCT11, CNES11, CORM11, CPFF11, CPTS11, CRFF11,
CTXT11, CVBI11, CXCE11, CXCO11, CXRI11, CXTL11, CYCR11, DEVM11, DAMI11, DLMT11,
DOMC11, DOX11, DRIT11, DVFF11, EDGA11, EDRX11, ELDO11, ERCR11, ERPA11, EURO11,
EVBI11, FAED11, FAMB11, FATN11, FCFL11, FEXC11, FFI11, FFCI11, FIIP11, FIIB11,
FINF11, FISC11, FISD11, FSTU11, FLCR11, FLMA11, FLRP11, FMOF11, FPAB11, FVPQ11,
GAGL11, GARE11, GALG11, GESE11, GGRC11, GLOG11, GMAT11, GRLV11, GSFI11, GTLG11,
GTWR11, HBRH11, HCHG11, HCRI11, HCTR11, HDFF11, HEDG11, HGBS11, HGCR11, HGFF11,
HGLG11, HGIC11, HGPO11, HGRE11, HGRS11, HGRU11, HLOG11, HMFL11, HMOC11, HOSI11,
HPPM11, HRDF11, BREV11, HSML11, HSON11, HTMX11, HUIC11, HUSC11, IBCR11, IBFF11,
IBIT11, IDFI11, IFIE11, IFIR11, IGFI11, IRDM11, IRIM11, JBRJ11, JCFF11, JFLL11,
JGPX11, JPPA11, JPPC11, JSAF11, JSRE11, KISU11, KNCE11, KNHY11, KNRE11, KNRI11,
KNSC11, LUGG11, LVBI11, MACX11, MALL11, MANA11, MATV11, MAXR11, MBRF11, MCFF11,
MCCI11, MCHY11, MDFF11, MDFC11, MEAL11, MERC11, MFAI11, MFII11, MGCR11, MGFF11,
MGHT11, MGLG11, MOFF11, MOIP11, MORD11, MORE11, MORC11, MXRF11, NAVI11, NEWL11,
NEWU11, NCHB11, NVIF11, NVHO11, OUFF11, OULG11, OURE11, PABY11, PATC11, PATL11,
PAZN11, PBFF11, PLCR11, PLRI11, PNDL11, PNPR11, PRSV11, PQAG11, PQDP11, PRCR11,
PRED11, PRTS11, PVBI11, QAGR11, QFFI11, RBVA11, RBCO11, RBCW11, RBDS11, RBED11,
RBFF11, RBGS11, RBLG11, RBRL11, RBRMD11, RBRR11, RBRS11, RBRY11, RBTS11, RCFA11,
RCRB11, RCRI11, RECR11, RECX11, REED11, REFF11, RELG11, REOD11, RETT11, RFI11,
RFOF11, RHEG11, RIFF11, RILV11, RIOBR11, RLOG11, RMCC11, RNDP11, RNGO11, RNPR11,
ROOF11, RPAR11, RPBI11, RSPD11, RVBI11, RZAG11, RZAK11, RZTR11, SARE11, SCFF11,
SDIL11, SEQR11, SHDP11, SHOP11, SHPH11, SJAU11, SNCI11, SNEL11, SNFF11, SPEV11,
SPFF11, SPLG11, SPTW11, SRVD11, STRX11, TAFI11, TBOF11, TEPH11, TGAR11, TJKR11,
TLCI11, TOUR11, TRNT11, TRXF11, TRXB11, TSNC11, UBSR11, URPR11, VCRR11, VEFM11,
VGHF11, VGIA11, VGIR11, VIFI11, VILG11, VINO11, VISC11, VIUR11, VOTS11, VTLT11,
VTPL11, VVPR11, VXXV11, WPLZ11, WREC11, XPCI11, XPCM11, XPHT11, XPIN11, XPLG11,
XPML11, XPPR11, XPSF11, XTED11, YCHY11
"""

# =========================
# LIMPEZA
# =========================
fiis = list(set([x.strip().upper() + ".SA" for x in raw_fiis.split(",")]))

# =========================
# DATA
# =========================
@st.cache_data
def get_data(ticker):
    try:
        df = yf.download(ticker, period="2y", progress=False)

        if df.empty:
            return df

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df[["Open","High","Low","Close","Volume"]]
        df.dropna(inplace=True)

        return df
    except:
        return pd.DataFrame()

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

    df["vol_ma20"] = df["Volume"].rolling(20).mean()
    df["vol_ma50"] = df["Volume"].rolling(50).mean()

    return df

# =========================
# STATUS
# =========================
def asset_status(df):
    last = df.iloc[-1]

    if last["Close"] < last["ema69"]:
        return "Perdeu Tendência"
    elif last["k"] < last["d"]:
        return "Observação"
    else:
        return "Setup Ativo"

# =========================
# SCANNER
# =========================
results = []
progress = st.progress(0)

max_assets = st.sidebar.slider("Qtd de FIIs", 20, 300, 100)

for i, ticker in enumerate(fiis[:max_assets]):
    try:
        df = get_data(ticker)

        if df.empty or len(df) < 150:
            continue

        df = add_indicators(df)
        last = df.iloc[-1]

        # FILTRO DE LIQUIDEZ
        if last["Volume"] < 200000:
            continue

        score = 0
        if last["Close"] > last["ema69"]: score += 30
        if df["vol_ma20"].iloc[-1] > df["vol_ma50"].iloc[-1]: score += 20
        if last["adx"] > 15: score += 20
        if last["k"] > last["d"]: score += 30

        results.append({
            "Ticker": ticker.replace(".SA",""),
            "Preço": round(last["Close"],2),
            "Score": score,
            "ADX": round(last["adx"],1),
            "Status": asset_status(df)
        })

    except:
        continue

    progress.progress((i+1)/len(fiis[:max_assets]))

df_res = pd.DataFrame(results)

# =========================
# OUTPUT
# =========================
if not df_res.empty:
    df_res = df_res.sort_values(by="Score", ascending=False)

    st.subheader("🏆 Ranking FIIs")
    st.dataframe(df_res, use_container_width=True)

    st.subheader("🔥 Entradas Premium")

    premium = df_res[
        (df_res["Score"] >= 70) &
        (df_res["Status"] == "Setup Ativo")
    ]

    st.dataframe(premium, use_container_width=True)

else:
    st.warning("Nenhum FII qualificado.")
