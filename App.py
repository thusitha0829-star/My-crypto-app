import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Scalping TA Signal App", page_icon="📈", layout="centered")

st.title("⚡ Live Crypto Scalping App")
st.caption("Real-Time Data via Yahoo Finance (EMA & RSI)")

default_watchlist = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD', 'DOGE-USD']

def get_crypto_data(symbol):
    sym = symbol.strip().upper().replace("USDT", "-USD")
    if not sym.endswith("-USD"):
        sym += "-USD"
    
    try:
        ticker = yf.Ticker(sym)
        df = ticker.history(period="1d", interval="5m")
        if not df.empty and len(df) >= 20:
            prices = df['Close'].tolist()
            return prices, sym.replace("-USD", "/USDT")
    except Exception:
        pass
    return None, sym

def calculate_ema(prices, period):
    if len(prices) < period: return prices[-1]
    k = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    for price in prices[period:]:
        ema = (price * k) + (ema * (1 - k))
    return ema

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    gains, losses = [], []
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        gains.append(change if change > 0 else 0)
        losses.append(abs(change) if change < 0 else 0)
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0: return 100
    return 100 - (100 / (1 + (avg_gain / avg_loss)))

def analyze_coin(symbol):
    data = get_crypto_data(symbol)
    if not data:
        return None
    
    prices, clean_sym = data
    current_price = prices[-1]
    ema20 = calculate_ema(prices, 20)
    ema50 = calculate_ema(prices, 50)
    rsi = calculate_rsi(prices)

    if current_price > ema20 > ema50 and (35 < rsi < 68):
        signal = "🚀 LONG (BUY)"
    elif current_price < ema20 < ema50 and (32 < rsi < 65):
        signal = "📉 SHORT (SELL)"
    else:
        signal = "⏳ WAIT"

    trend = "🟢 Bullish" if current_price > ema20 else "🔴 Bearish"

    return {
        "Coin": clean_sym,
        "Price ($)": f"{current_price:.4f}" if current_price < 1 else f"{current_price:.2f}",
        "Signal": signal,
        "Trend": trend,
        "RSI": round(rsi, 2)
    }

# --- SEARCH ANY COIN ---
st.subheader("🔍 Any Coin Search")
custom_coin = st.text_input("Enter Coin Ticker (e.g. BTC, ETH, SOL, DOGE):", value="BTC")

if st.button("Analyze Custom Coin"):
    if custom_coin:
        with st.spinner("Fetching Live Market Data..."):
            res = analyze_coin(custom_coin)
            if res:
                col1, col2, col3 = st.columns(3)
                col1.metric("Coin", res["Coin"])
                col2.metric("Price", f"${res['Price ($)']}")
                col3.metric("Signal", res["Signal"])
                st.json(res)
            else:
                st.error(f"Could not fetch data for '{custom_coin}'. Try entering valid symbol like BTC, SOL, ETH.")

st.divider()

# --- LIVE WATCHLIST ---
st.subheader("📊 Market Scalping Dashboard (5M)")

if st.button("🔄 Refresh Data"):
    st.rerun()

results = []
with st.spinner("Analyzing Market Watchlist..."):
    for sym in default_watchlist:
        analysis = analyze_coin(sym)
        if analysis:
            results.append(analysis)

if results:
    df = pd.DataFrame(results)
    st.dataframe(df, use_container_width=True)
