import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Page Config
st.set_page_config(
    page_title="SMC/ICT Swing Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Modern UI
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
</style>
""", unsafe_allow_html=True)

# Header Section
st.title("📈 SMC / ICT Swing Trading Terminal")
st.caption("Multi-Rule Confluence Engine (BOS, Order Blocks, FVG & Liquidity Sweeps) - 1H/4H Swing Setup")

default_watchlist = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD', 'BNB-USD', 'DOGE-USD']

def get_swing_df(symbol):
    sym = symbol.strip().upper().replace("USDT", "-USD")
    if not sym.endswith("-USD"):
        sym += "-USD"
    
    try:
        ticker = yf.Ticker(sym)
        # Swing trading requires higher timeframes like 1h or 1d
        df = ticker.history(period="60d", interval="1h")
        if not df.empty and len(df) >= 50:
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

def analyze_swing_setup(symbol):
    data = get_swing_df(symbol)
    if not data:
        return None
    
    df, clean_sym = data
    close = df['Close']
    high = df['High']
    low = df['Low']
    
    current_price = close.iloc[-1]
    
    # Technical Indicators for Trend & Momentum
    ema50 = close.ewm(span=50, adjust=False).mean().iloc[-1]
    ema200 = close.ewm(span=200, adjust=False).mean().iloc[-1]
    rsi = calculate_rsi(close).iloc[-1]
    
    # Swing Levels (Last 30 candles for Swing structure)
    swing_high = high.iloc[-30:].max()
    swing_low = low.iloc[-30:].min()
    recent_high = high.iloc[-10:].max()
    recent_low = low.iloc[-10:].min()

    # --- BOOK RULES IMPLEMENTATION (Any 1 Rule Matching = Signal Trigger) ---
    
    # Rule 1: Market Structure Break (BOS / Trend Continuation)
    bullish_bos = current_price > high.iloc[-15:-1].max()
    bearish_bos = current_price < low.iloc[-15:-1].min()

    # Rule 2: Order Block (OB) / Mitigation Zone Touch
    # Bullish: Price pulled back to near a recent major low structure (Discount zone)
    bullish_ob = current_price <= (swing_low + (swing_high - swing_low) * 0.35)
    # Bearish: Price pulled back to near a recent major high structure (Premium zone)
    bearish_ob = current_price >= (swing_high - (swing_high - swing_low) * 0.35)

    # Rule 3: FVG (Fair Value Gap) filling or bouncing simulation via momentum
    bullish_fvg = (close.iloc[-1] > close.iloc[-2]) and (close.iloc[-2] > close.iloc[-3]) and (rsi < 60)
    bearish_fvg = (close.iloc[-1] < close.iloc[-2]) and (close.iloc[-2] < close.iloc[-3]) and (rsi > 40)

    # Rule 4: Liquidity Sweep (Took out old low/high and reversing)
    bullish_sweep = (low.iloc[-1] <= low.iloc[-30:-2].min()) and (current_price > low.iloc[-1])
    bearish_sweep = (high.iloc[-1] >= high.iloc[-30:-2].max()) and (current_price < high.iloc[-1])

    # Combining rules: If ANY bullish rule matches AND price is above/near EMA structure
    is_bullish_signal = (bullish_bos or bullish_ob or bullish_fvg or bullish_sweep) and (current_price > ema200 or rsi < 55)
    is_bearish_signal = (bearish_bos or bearish_ob or bearish_fvg or bearish_sweep) and (current_price < ema200 or rsi > 45)

    signal = "⏳ WAIT (No Clear Setup)"
    bias = "NEUTRAL"
    sl, tp1, tp2 = 0.0, 0.0, 0.0

    if is_bullish_signal and not is_bearish_signal:
        signal = "🚀 SWING LONG (BUY)"
        bias = "🟢 BULLISH"
        sl = swing_low * 0.992  # Safe Swing Stop Loss below market structure
        risk = current_price - sl
        tp1 = current_price + (risk * 2.5)  # Swing RR 1:2.5
        tp2 = current_price + (risk * 4.0)  # Swing RR 1:4

    elif is_bearish_signal and not is_bullish_signal:
        signal = "📉 SWING SHORT (SELL)"
        bias = "🔴 BEARISH"
        sl = swing_high * 1.008  # Safe Swing Stop Loss above market structure
        risk = sl - current_price
        tp1 = current_price - (risk * 2.5)  # Swing RR 1:2.5
        tp2 = current_price - (risk * 4.0)  # Swing RR 1:4

    return {
        "Coin": clean_sym,
        "Signal": signal,
        "Bias": bias,
        "Entry": current_price,
        "SL": sl,
        "TP1": tp1,
        "TP2": tp2,
        "RSI": round(rsi, 1)
    }

# --- SEARCH SINGLE COIN ---
st.subheader("🔍 Single Asset Swing Analysis")
c1, c2 = st.columns([3, 1])
with c1:
    custom_coin = st.text_input("Enter Coin Symbol (e.g. BTC, ETH, SOL, ADA):", value="BTC", label_visibility="collapsed")
with c2:
    search_btn = st.button("🔎 Run Strategy", use_container_width=True)

if search_btn or custom_coin:
    with st.spinner("Analyzing SMC / ICT Rules (BOS, FVG, OB, Liquidity)..."):
        res = analyze_swing_setup(custom_coin)
        if res:
            p_fmt = lambda val: f"${val:.4f}" if val < 1 else f"${val:.2f}"
            
            st.markdown(f"### 📊 Setup Result for **{res['Coin']}**")
            
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            col_s1.metric("Strategy Signal", res["Signal"])
            col_s2.metric("Structure Bias", res["Bias"])
            col_s3.metric("Entry Price Zone", p_fmt(res["Entry"]))
            col_s4.metric("RSI (1H)", res["RSI"])

            st.write("")
            
            if "LONG" in res["Signal"] or "SHORT" in res["Signal"]:
                st.success(f"✅ **Rule Match Found!** Valid SMC/ICT Swing Setup detected based on your strategy rules.")
                r1, r2, r3 = st.columns(3)
                r1.metric("🛑 Stop Loss (SL)", p_fmt(res["SL"]))
                r2.metric("🎯 Take Profit 1 (1:2.5)", p_fmt(res["TP1"]))
                r3.metric("🚀 Take Profit 2 (1:4.0)", p_fmt(res["TP2"]))
            else:
                st.info("💡 **Market is in Consolidation.** None of the strict entry rules triggered yet. Wait for a clear Liquidity Sweep or BOS.")
        else:
            st.error(f"Could not load data for '{custom_coin}'. Try entering standard symbols like BTC, ETH, SOL.")

st.divider()

# --- MARKET SCANNER DASHBOARD ---
st.subheader("📊 Market-Wide Swing Opportunities Dashboard (1H Timeframe)")

if st.button("🔄 Scan Market Now"):
    st.rerun()

results = []
with st.spinner("Scanning all watchlist assets using multi-rule strategy..."):
    for sym in default_watchlist:
        analysis = analyze_swing_setup(sym)
        if analysis:
            p_f = lambda x: f"${x:.4f}" if x < 1 else f"${x:.2f}"
            results.append({
                "Coin": analysis["Coin"],
                "Signal": analysis["Signal"],
                "Bias": analysis["Bias"],
                "Entry ($)": p_f(analysis["Entry"]),
                "Stop Loss ($)": p_f(analysis["SL"]) if analysis["SL"] > 0 else "-",
                "TP1 (1:2.5) ($)": p_f(analysis["TP1"]) if analysis["TP1"] > 0 else "-",
                "TP2 (1:4) ($)": p_f(analysis["TP2"]) if analysis["TP2"] > 0 else "-",
                "RSI": analysis["RSI"]
            })

if results:
    df_res = pd.DataFrame(results)
    st.dataframe(df_res, use_container_width=True, hide_index=True)
