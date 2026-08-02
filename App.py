import streamlit as st
import yfinance as yf
import pandas as pd

# Page Config
st.set_page_config(
    page_title="SMC Pro Scalper",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Modern Dark UI
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .stCard {
        background-color: #1e222d;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
    .metric-label { font-size: 0.85rem; color: #848e9c; font-weight: 600; }
    .metric-value { font-size: 1.4rem; font-weight: 700; color: #f0b90b; }
    .buy-signal { color: #0ecb81; font-weight: 800; font-size: 1.2rem; }
    .sell-signal { color: #f6465d; font-weight: 800; font-size: 1.2rem; }
    .wait-signal { color: #f0b90b; font-weight: 800; font-size: 1.2rem; }
</style>
""", unsafe_allow_html=True)

# Header Section
st.title("⚡ SMC / ICT Live Trading Terminal")
st.caption("Real-Time Smart Money Concepts Analysis | 5M Timeframe | Auto Risk-to-Reward Engine")

default_watchlist = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD', 'DOGE-USD']

def get_crypto_df(symbol):
    sym = symbol.strip().upper().replace("USDT", "-USD")
    if not sym.endswith("-USD"):
        sym += "-USD"
    
    try:
        ticker = yf.Ticker(sym)
        df = ticker.history(period="1d", interval="5m")
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

def analyze_smc_setup(symbol):
    data = get_crypto_df(symbol)
    if not data:
        return None
    
    df, clean_sym = data
    close_prices = df['Close']
    high_prices = df['High']
    low_prices = df['Low']

    current_price = close_prices.iloc[-1]
    
    ema20 = close_prices.ewm(span=20, adjust=False).mean().iloc[-1]
    ema50 = close_prices.ewm(span=50, adjust=False).mean().iloc[-1]
    rsi = calculate_rsi(close_prices).iloc[-1]
    
    recent_high = high_prices.iloc[-15:].max()
    recent_low = low_prices.iloc[-15:].min()
    
    signal = "⏳ WAIT"
    entry_price = current_price
    sl, tp1, tp2 = 0.0, 0.0, 0.0
    bias = "NEUTRAL"

    if current_price > ema20 > ema50 and (40 < rsi < 70):
        signal = "🚀 LONG"
        bias = "🟢 BULLISH"
        sl = recent_low * 0.998
        risk = entry_price - sl
        tp1 = entry_price + (risk * 2)
        tp2 = entry_price + (risk * 3)

    elif current_price < ema20 < ema50 and (30 < rsi < 60):
        signal = "📉 SHORT"
        bias = "🔴 BEARISH"
        sl = recent_high * 1.002
        risk = sl - entry_price
        tp1 = entry_price - (risk * 2)
        tp2 = entry_price - (risk * 3)

    return {
        "Coin": clean_sym,
        "Signal": signal,
        "Bias": bias,
        "Entry": entry_price,
        "SL": sl,
        "TP1": tp1,
        "TP2": tp2,
        "RSI": round(rsi, 1)
    }

# --- SINGLE COIN SEARCH ---
st.subheader("🔍 Single Coin Technical Deep-Dive")
c1, c2 = st.columns([3, 1])
with c1:
    custom_coin = st.text_input("Enter Coin Symbol (e.g. BTC, ETH, SOL, PEPE, DOGE):", value="BTC", label_visibility="collapsed")
with c2:
    search_btn = st.button("🔎 Analyze Coin", use_container_width=True)

if search_btn or custom_coin:
    with st.spinner("Calculating Liquidity Levels & SMC Setup..."):
        res = analyze_smc_setup(custom_coin)
        if res:
            p_fmt = lambda val: f"${val:.4f}" if val < 1 else f"${val:.2f}"
            
            st.markdown(f"### 📊 Analysis for **{res['Coin']}**")
            
            # Key Stats Cards
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            col_s1.metric("Signal", res["Signal"])
            col_s2.metric("Market Bias", res["Bias"])
            col_s3.metric("Current / Entry Price", p_fmt(res["Entry"]))
            col_s4.metric("RSI Indicator", res["RSI"])

            st.write("")
            
            if res["Signal"] != "⏳ WAIT":
                st.success(f"**Trade Setup Found!** Follow strict Risk Management (R:R Ratio 1:2 & 1:3).")
                r1, r2, r3 = st.columns(3)
                r1.metric("🛑 Stop Loss (SL)", p_fmt(res["SL"]))
                r2.metric("🎯 Take Profit 1 (1:2)", p_fmt(res["TP1"]))
                r3.metric("🚀 Take Profit 2 (1:3)", p_fmt(res["TP2"]))
            else:
                st.info("💡 **No Clean SMC Entry Right Now.** Price is consolidating or RSI is out of optimal zone. Wait for market structure break.")
        else:
            st.error(f"Could not load market data for '{custom_coin}'. Please check the symbol.")

st.divider()

# --- DASHBOARD BOARD ---
st.subheader("📊 Market Watchlist Dashboard")

if st.button("🔄 Refresh Market Data"):
    st.rerun()

results = []
with st.spinner("Scanning Watchlist Assets..."):
    for sym in default_watchlist:
        analysis = analyze_smc_setup(sym)
        if analysis:
            p_f = lambda x: f"${x:.4f}" if x < 1 else f"${x:.2f}"
            results.append({
                "Coin": analysis["Coin"],
                "Signal": analysis["Signal"],
                "Bias": analysis["Bias"],
                "Entry ($)": p_f(analysis["Entry"]),
                "Stop Loss ($)": p_f(analysis["SL"]) if analysis["SL"] > 0 else "-",
                "TP1 (1:2) ($)": p_f(analysis["TP1"]) if analysis["TP1"] > 0 else "-",
                "TP2 (1:3) ($)": p_f(analysis["TP2"]) if analysis["TP2"] > 0 else "-",
                "RSI": analysis["RSI"]
            })

if results:
    df = pd.DataFrame(results)
    st.dataframe(df, use_container_width=True, hide_index=True)
