import streamlit as st
import yfinance as yf
import pandas as pd

# Page Config
st.set_page_config(page_title="SMC High-Accuracy Terminal", page_icon="🎯", layout="wide")

# Custom CSS for Developer Header
st.markdown("""
<style>
    .developer-card {
        background-color: #1e222d;
        padding: 15px 25px;
        border-radius: 10px;
        border-left: 5px solid #f0b90b;
        margin-bottom: 25px;
    }
    .dev-title { font-size: 1.8rem; font-weight: 800; color: #ffffff; margin: 0; }
    .dev-sub { font-size: 0.95rem; color: #848e9c; margin-top: 5px; }
    .dev-info { font-size: 1rem; color: #f0b90b; font-weight: 600; margin-top: 8px; }
</style>
""", unsafe_allow_html=True)

# --- DEVELOPER HEADER SECTION ---
DEV_NAME = "THUSITHA"
DEV_PHONE = "+94 74 001 1100"

st.markdown(f"""
<div class="developer-card">
    <div class="dev-title">🎯 SMC High-Probability Trading Engine</div>
    <div class="dev-sub">Multi-Timeframe Confluence (4H Trend Filter + 1H SMC Structure + Volume Validation)</div>
    <div class="dev-info">👤 Developed by: <b>{DEV_NAME}</b> | 📞 Contact: <b>{DEV_PHONE}</b></div>
</div>
""", unsafe_allow_html=True)

default_watchlist = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD', 'BNB-USD', 'DOGE-USD']

def fetch_data(symbol, interval, period):
    sym = symbol.strip().upper().replace("USDT", "-USD")
    if not sym.endswith("-USD"): sym += "-USD"
    try:
        ticker = yf.Ticker(sym)
        df = ticker.history(period=period, interval=interval)
        if not df.empty and len(df) >= 30:
            return df, sym.replace("-USD", "/USDT")
    except Exception:
        pass
    return None, sym

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def analyze_high_accuracy_setup(symbol):
    df_4h, clean_sym = fetch_data(symbol, interval="1d", period="60d")
    df_1h, _ = fetch_data(symbol, interval="1h", period="30d")

    if df_4h is None or df_1h is None:
        return None

    c_4h = df_4h.iloc[:-1]
    c_1h = df_1h.iloc[:-1]

    ema50_htf = c_4h['Close'].ewm(span=50, adjust=False).mean().iloc[-1]
    ema200_htf = c_4h['Close'].ewm(span=200, adjust=False).mean().iloc[-1]
    
    htf_bullish = c_4h['Close'].iloc[-1] > ema50_htf and ema50_htf > ema200_htf
    htf_bearish = c_4h['Close'].iloc[-1] < ema50_htf and ema50_htf < ema200_htf

    avg_vol = c_1h['Volume'].iloc[-20:].mean()
    current_vol = c_1h['Volume'].iloc[-1]
    volume_confirmed = current_vol > (avg_vol * 1.1)

    close_1h = c_1h['Close']
    high_1h = c_1h['High']
    low_1h = c_1h['Low']
    entry_price = close_1h.iloc[-1]

    rsi_1h = calculate_rsi(close_1h).iloc[-1]
    swing_high = high_1h.iloc[-30:].max()
    swing_low = low_1h.iloc[-30:].min()

    bullish_bos = entry_price > high_1h.iloc[-15:-1].max()
    bearish_bos = entry_price < low_1h.iloc[-15:-1].min()

    bullish_sweep = (low_1h.iloc[-1] <= low_1h.iloc[-30:-2].min()) and (entry_price > low_1h.iloc[-1])
    bearish_sweep = (high_1h.iloc[-1] >= high_1h.iloc[-30:-2].max()) and (entry_price < high_1h.iloc[-1])

    is_strong_long = htf_bullish and (bullish_bos or bullish_sweep) and volume_confirmed and (40 < rsi_1h < 68)
    is_strong_short = htf_bearish and (bearish_bos or bearish_sweep) and volume_confirmed and (32 < rsi_1h < 60)

    signal = "⏳ NO SETUP (Low Probability / Consolidating)"
    bias = "🟢 HTF BULLISH" if htf_bullish else ("🔴 HTF BEARISH" if htf_bearish else "⚪ NEUTRAL")
    sl, tp1, tp2 = 0.0, 0.0, 0.0

    if is_strong_long:
        signal = "🔥 HIGH CONFIRMATION LONG"
        sl = swing_low * 0.993
        risk = entry_price - sl
        tp1 = entry_price + (risk * 2.0)
        tp2 = entry_price + (risk * 3.5)

    elif is_strong_short:
        signal = "💥 HIGH CONFIRMATION SHORT"
        sl = swing_high * 1.007
        risk = sl - entry_price
        tp1 = entry_price - (risk * 2.0)
        tp2 = entry_price - (risk * 3.5)

    return {
        "Coin": clean_sym,
        "Signal": signal,
        "HTF Trend": bias,
        "Entry ($)": entry_price,
        "SL": sl,
        "TP1": tp1,
        "TP2": tp2,
        "Volume Status": "✅ Confirmed Spike" if volume_confirmed else "⚠️ Low Vol",
        "RSI": round(rsi_1h, 1)
    }

# UI Layout
st.subheader("🔍 High-Probability Setup Scanner")
custom_coin = st.text_input("Enter Asset Symbol (e.g. BTC, ETH, SOL):", value="BTC")

if st.button("Run Strict Confluence Check"):
    res = analyze_high_accuracy_setup(custom_coin)
    if res:
        p_fmt = lambda val: f"${val:.4f}" if val < 1 else f"${val:.2f}"
        st.markdown(f"### Analysis for **{res['Coin']}**")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Signal Quality", res["Signal"])
        c2.metric("4H Trend Filter", res["HTF Trend"])
        c3.metric("Entry Price", p_fmt(res["Entry ($)"]))
        c4.metric("Volume Filter", res["Volume Status"])

        if "HIGH CONFIRMATION" in res["Signal"]:
            st.success("✅ **High Probability SMC Setup Matched! All 3 Filters Confirmed.**")
            st.write("---")
            r1, r2, r3 = st.columns(3)
            r1.metric("🛑 Strict Stop Loss (SL)", p_fmt(res["SL"]))
            r2.metric("🎯 Target 1 (TP1 - 1:2)", p_fmt(res["TP1"]))
            r3.metric("🚀 Target 2 (TP2 - 1:3.5)", p_fmt(res["TP2"]))
        else:
            st.info("💡 Market conditions do not meet strict criteria right now. Waiting for high-volume structure break.")
    else:
        st.error("Could not retrieve market data.")

st.divider()

st.subheader("📊 High-Accuracy Market Scanner")
if st.button("🔄 Scan Dashboard"):
    st.rerun()

results = []
for sym in default_watchlist:
    analysis = analyze_high_accuracy_setup(sym)
    if analysis:
        p_f = lambda x: f"${x:.4f}" if x < 1 else f"${x:.2f}"
        results.append({
            "Coin": analysis["Coin"],
            "Signal": analysis["Signal"],
            "HTF Trend": analysis["HTF Trend"],
            "Volume": analysis["Volume Status"],
            "Entry ($)": p_f(analysis["Entry ($)"]),
            "SL ($)": p_f(analysis["SL"]) if analysis["SL"] > 0 else "-",
            "TP1 ($)": p_f(analysis["TP1"]) if analysis["TP1"] > 0 else "-",
            "TP2 ($)": p_f(analysis["TP2"]) if analysis["TP2"] > 0 else "-",
            "RSI": analysis["RSI"]
        })

if results:
    st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
