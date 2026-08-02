import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="SMC/ICT Scalping App", page_icon="📈", layout="centered")

st.title("⚡ SMC/ICT Technical Analysis & Signal App")
st.caption("Smart Money Concepts Analysis (Entry, Stop Loss & Take Profit)")

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
    
    # EMA Calculation
    ema20 = close_prices.ewm(span=20, adjust=False).mean().iloc[-1]
    ema50 = close_prices.ewm(span=50, adjust=False).mean().iloc[-1]
    
    # RSI
    rsi = calculate_rsi(close_prices).iloc[-1]
    
    # SMC Swing High & Swing Low (Liquidity Levels - Last 15 candles)
    recent_high = high_prices.iloc[-15:].max()
    recent_low = low_prices.iloc[-15:].min()
    
    signal = "⏳ WAIT"
    entry_price = current_price
    sl = 0.0
    tp1 = 0.0
    tp2 = 0.0
    bias = "NEUTRAL"

    # SMC Long Setup: Price above EMAs + Bullish Bias
    if current_price > ema20 > ema50 and (40 < rsi < 70):
        signal = "🚀 LONG (BUY)"
        bias = "🟢 BULLISH"
        sl = recent_low * 0.998  # Stop loss just below liquidity low
        risk = entry_price - sl
        tp1 = entry_price + (risk * 2)  # RR 1:2
        tp2 = entry_price + (risk * 3)  # RR 1:3

    # SMC Short Setup: Price below EMAs + Bearish Bias
    elif current_price < ema20 < ema50 and (30 < rsi < 60):
        signal = "📉 SHORT (SELL)"
        bias = "🔴 BEARISH"
        sl = recent_high * 1.002  # Stop loss just above liquidity high
        risk = sl - entry_price
        tp1 = entry_price - (risk * 2)  # RR 1:2
        tp2 = entry_price - (risk * 3)  # RR 1:3

    return {
        "Coin": clean_sym,
        "Signal": signal,
        "Market Bias": bias,
        "Entry Price ($)": f"{entry_price:.4f}" if entry_price < 1 else f"{entry_price:.2f}",
        "Stop Loss ($)": f"{sl:.4f}" if sl < 1 else f"{sl:.2f}",
        "Take Profit 1 (1:2) ($)": f"{tp1:.4f}" if tp1 < 1 else f"{tp1:.2f}",
        "Take Profit 2 (1:3) ($)": f"{tp2:.4f}" if tp2 < 1 else f"{tp2:.2f}",
        "RSI": round(rsi, 1)
    }

# --- SEARCH ANY COIN ---
st.subheader("🔍 Single Coin SMC Analysis")
custom_coin = st.text_input("Enter Coin Symbol (e.g. BTC, ETH, SOL, KAT):", value="BTC")

if st.button("Analyze Coin Setup"):
    if custom_coin:
        with st.spinner("Analyzing Market Structure & Liquidity..."):
            res = analyze_smc_setup(custom_coin)
            if res:
                st.markdown(f"### Result for **{res['Coin']}**")
                
                col1, col2 = st.columns(2)
                col1.metric("Signal", res["Signal"])
                col2.metric("Market Bias", res["Market Bias"])
                
                st.divider()
                
                col_a, col_b, col_c, col_d = st.columns(4)
                col_a.metric("Entry Price", f"${res['Entry Price ($)']}")
                col_b.metric("Stop Loss (SL)", f"${res['Stop Loss ($)']}")
                col_c.metric("Target 1 (TP1)", f"${res['Take Profit 1 (1:2) ($)']}")
                col_d.metric("Target 2 (TP2)", f"${res['Take Profit 2 (1:3) ($)']}")
                
                with st.expander("Detailed Setup JSON"):
                    st.json(res)
            else:
                st.error(f"Could not fetch market data for '{custom_coin}'. Make sure ticker is correct.")

st.divider()

# --- LIVE DASHBOARD ---
st.subheader("📊 Market SMC Signal Dashboard (5M Timeframe)")

if st.button("🔄 Refresh Market Signals"):
    st.rerun()

results = []
with st.spinner("Scanning Market Dashboard..."):
    for sym in default_watchlist:
        analysis = analyze_smc_setup(sym)
        if analysis:
            results.append(analysis)

if results:
    df = pd.DataFrame(results)
    st.dataframe(df, use_container_width=True)
