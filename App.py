import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Scalping TA Signal App", page_icon="📈", layout="centered")

st.title("⚡ Live Crypto Scalping & TA App")
st.caption("Real-Time Data via Public API (EMA, RSI & Candlestick Patterns)")

# Symbol to CoinGecko ID Mapping
COIN_MAP = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'SOL': 'solana',
    'XRP': 'ripple',
    'ADA': 'cardano',
    'DOGE': 'dogecoin',
    'KAT': 'kaspium',  # OR 'kaspa' depending on ticker
    'PEPE': 'pepe',
    'BNB': 'binancecoin'
}

def get_crypto_data(coin_symbol):
    sym = coin_symbol.strip().upper().replace("USDT", "")
    coin_id = COIN_MAP.get(sym, sym.lower())
    
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=1"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            prices = [item[1] for item in res.json().get('prices', [])]
            if len(prices) >= 20:
                return prices, sym
    except Exception:
        pass
    
    # Backup API (CoinCap) if CoinGecko fails
    try:
        url_backup = f"https://api.coincap.io/v2/assets/{coin_id}/history?interval=m5"
        res2 = requests.get(url_backup, headers=headers, timeout=8)
        if res2.status_code == 200:
            data = res2.json().get('data', [])
            prices = [float(x['priceUsd']) for x in data]
            if len(prices) >= 20:
                return prices, sym
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
    prices, clean_sym = get_crypto_data(symbol)
    if not prices:
        return None

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
        "Coin": f"{clean_sym}/USDT",
        "Price ($)": f"{current_price:.4f}" if current_price < 1 else f"{current_price:.2f}",
        "Signal": signal,
        "Trend": trend,
        "RSI": round(rsi, 2)
    }

# --- SEARCH ANY COIN ---
st.subheader("🔍 Any Coin Search")
custom_coin = st.text_input("Enter Coin Name (e.g. BTC, ETH, SOL, DOGE):", value="BTC")

if st.button("Analyze Custom Coin"):
    if custom_coin:
        with st.spinner("Fetching Market Data..."):
            res = analyze_coin(custom_coin)
            if res:
                col1, col2, col3 = st.columns(3)
                col1.metric("Coin", res["Coin"])
                col2.metric("Price", f"${res['Price ($)']}")
                col3.metric("Signal", res["Signal"])
                st.json(res)
            else:
                st.error(f"Could not fetch data for '{custom_coin}'. Try typing BTC, ETH, SOL, DOGE or PEPE.")

st.divider()

# --- LIVE WATCHLIST ---
st.subheader("📊 Market Scalping Dashboard")

if st.button("🔄 Refresh Market Data"):
    st.rerun()

watchlist = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOGE']
results = []

with st.spinner("Analyzing Watchlist Coins..."):
    for sym in watchlist:
        analysis = analyze_coin(sym)
        if analysis:
            results.append(analysis)

if results:
    df = pd.DataFrame(results)
    st.dataframe(df, use_container_width=True)
