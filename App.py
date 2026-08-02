import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Scalping TA Signal App", page_icon="📈", layout="centered")

st.title("⚡ Live Scalping & TA Analysis App")
st.caption("Binance Real-Time Data (EMA, RSI & Candlestick Patterns)")

default_symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'ADAUSDT', 'DOGEUSDT', 'KATUSDT']

def get_binance_data(symbol, interval='5m', limit=100):
    formatted_symbol = symbol.strip().upper()
    if not formatted_symbol.endswith('USDT'):
        formatted_symbol += 'USDT'
        
    url = f"https://api.binance.com/api/v3/klines?symbol={formatted_symbol}&interval={interval}&limit={limit}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            return res.json(), formatted_symbol
    except Exception as e:
        pass
    return None, formatted_symbol

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

def check_candlestick_patterns(candles):
    if len(candles) < 4: return "NONE"
    o1, h1, l1, c1 = float(candles[-2][1]), float(candles[-2][2]), float(candles[-2][3]), float(candles[-2][4])
    o2, h2, l2, c2 = float(candles[-1][1]), float(candles[-1][2]), float(candles[-1][3]), float(candles[-1][4])
    body2 = abs(c2 - o2)

    if (c2 > o2) and ((o2 - float(candles[-1][3])) > body2 * 2) and ((float(candles[-1][2]) - c2) < body2 * 0.5): return "BULLISH_HAMMER"
    if (c2 < o2) and ((float(candles[-1][2]) - o2) > body2 * 2) and ((c2 - float(candles[-1][3])) < body2 * 0.5): return "SHOOTING_STAR"
    if (c1 < o1) and (c2 > o2) and (c2 > o1) and (o2 < c1): return "BULLISH_ENGULFING"
    if (c1 > o1) and (c2 < o2) and (c2 < o1) and (o2 > c1): return "BEARISH_ENGULFING"
    return "NONE"

def analyze_symbol(symbol):
    data, full_symbol = get_binance_data(symbol)
    if not data:
        return None
    close_prices = [float(c[4]) for c in data]
    price = close_prices[-1]
    ema20 = calculate_ema(close_prices, 20)
    ema50 = calculate_ema(close_prices, 50)
    rsi = calculate_rsi(close_prices)
    pattern = check_candlestick_patterns(data)

    if price > ema20 > ema50 and (35 < rsi < 68) and pattern in ["BULLISH_HAMMER", "BULLISH_ENGULFING"]:
        signal = "🚀 LONG (BUY)"
    elif price < ema20 < ema50 and (32 < rsi < 65) and pattern in ["SHOOTING_STAR", "BEARISH_ENGULFING"]:
        signal = "📉 SHORT (SELL)"
    else:
        signal = "⏳ WAIT"

    trend = "🟢 Bullish" if price > ema20 else "🔴 Bearish"
    
    return {
        "Coin": full_symbol,
        "Price ($)": f"{price:.4f}" if price < 1 else f"{price:.2f}",
        "Signal": signal,
        "Trend": trend,
        "RSI": round(rsi, 2),
        "Candle Pattern": pattern
    }

# --- SEARCH ANY COIN ---
st.subheader("🔍 Any Coin Search")
custom_coin = st.text_input("Enter Coin Name (e.g. BTC, KAT, SOL, PEPE):", value="BTC")

if st.button("Analyze Custom Coin"):
    if custom_coin:
        with st.spinner("Fetching Binance Data..."):
            res = analyze_symbol(custom_coin)
            if res:
                col1, col2, col3 = st.columns(3)
                col1.metric("Coin", res["Coin"])
                col2.metric("Price", f"${res['Price ($)']}")
                col3.metric("Signal", res["Signal"])

                st.json(res)
            else:
                st.error(f"'{custom_coin}' not found on Binance! Try typing full symbol like BTCUSDT.")

st.divider()

# --- LIVE WATCHLIST ---
st.subheader("📊 Market Scalping Dashboard (5M Timeframe)")

if st.button("🔄 Refresh Market Data"):
    st.rerun()

results = []
with st.spinner("Analyzing Main Watchlist..."):
    for sym in default_symbols:
        analysis = analyze_symbol(sym)
        if analysis:
            results.append(analysis)

if results:
    df = pd.DataFrame(results)
    st.dataframe(df, use_container_width=True)
