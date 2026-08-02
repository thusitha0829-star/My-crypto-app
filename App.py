import streamlit as st
import yfinance as yf
import pandas as pd

# Page Config
st.set_page_config(page_title="SMC Stable Swing", page_icon="📈", layout="wide")

st.title("📈 SMC Stable Swing Signal Terminal")
st.caption("Confirmed Closed-Candle Signals Only (No Repainting / No Frequent Flips)")

default_watchlist = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD', 'BNB-USD', 'DOGE-USD']

def get_swing_df(symbol):
    sym = symbol.strip().upper().replace("USDT", "-USD")
    if not sym.endswith("-USD"):
        sym += "-USD"
    
    try:
        ticker = yf.Ticker(sym)
        # Using 4H / 1H interval for stable swing setups
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

def analyze_stable_swing(symbol):
    data = get_swing_df(symbol)
    if not data:
        return None
    
    df, clean_sym = data
    
    # IMPORTANT: We ignore the currently open live candle (iloc[-1]) 
    # and ONLY use closed candles (iloc[-2]) to stop repainting!
    closed_df = df.iloc[:-1] 
    
    close = closed_df['Close']
    high = closed_df['High']
    low = closed_df['Low']
    
    entry_price = close.iloc[-1]
    
    ema50 = close.ewm(span=50, adjust=False).mean().iloc[-1]
    ema200 = close.ewm(span=200, adjust=False).mean().iloc[-1]
    rsi = calculate_rsi(close).iloc[-1]
    
    swing_high = high.iloc[-30:].max()
    swing_low = low.iloc[-30:].min()

    # Closed Candle Confluence Rules
    bullish_bos = entry_price > high.iloc[-15:-1].max()
    bearish_bos = entry_price < low.iloc[-15:-1].min()

    bullish_ob = entry_price <= (swing_low + (swing_high - swing_low) * 0.35)
    bearish_ob = entry_price >= (swing_high - (swing_high - swing_low) * 0.35)

    bullish_fvg = (close.iloc[-1] > close.iloc[-2]) and (close.iloc[-2] > close.iloc[-3]) and (rsi < 60)
    bearish_fvg = (close.iloc[-1] < close.iloc[-2]) and (close.iloc[-2] < close.iloc[-3]) and (rsi > 40)

    bullish_sweep = (low.iloc[-1] <= low.iloc[-30:-2].min()) and (entry_price > low.iloc[-1])
    bearish_sweep = (high.iloc[-1] >= high.iloc[-30:-2].max()) and (entry_price < high.iloc[-1])

    is_bullish = (bullish_bos or bullish_ob or bullish_fvg or bullish_sweep) and (entry_price > ema200 or rsi < 55)
    is_bearish = (bearish_bos or bearish_ob or bearish_fvg or bearish_sweep) and (entry_price < ema200 or rsi > 45)

    signal = "⏳ WAIT (Consolidating)"
    bias = "NEUTRAL"
    sl, tp1, tp2 = 0.0, 0.0, 0.0

    if is_bullish and not is_bearish:
        signal = "🚀 SWING LONG"
        bias = "🟢 BULLISH"
        sl = swing_low * 0.992
        risk = entry_price - sl
        tp1 = entry_price + (risk * 2.5)
        tp2 = entry_price + (risk * 4.0)

    elif is_bearish and not is_bullish:
        signal = "📉 SWING SHORT"
        bias = "🔴 BEARISH"
        sl = swing_high * 1.008
        risk = sl - entry_price
        tp1 = entry_price - (risk * 2.5)
        tp2 = entry_price - (risk * 4.0)

    return {
        "Coin": clean_sym,
        "Signal": signal,
        "Bias": bias,
        "Confirmed Entry ($)": entry_price,
        "SL": sl,
        "TP1": tp1,
        "TP2": tp2,
        "RSI": round(rsi, 1)
    }

# UI Code
st.subheader("🔍 Stable SMC Analysis (Confirmed Candle)")
custom_coin = st.text_input("Enter Ticker (e.g. BTC, ETH, SOL):", value="BTC")

if st.button("Analyze Confirmed Setup"):
    res = analyze_stable_swing(custom_coin)
    if res:
        p_fmt = lambda val: f"${val:.4f}" if val < 1 else f"${val:.2f}"
        st.markdown(f"### Result for **{res['Coin']}**")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Confirmed Signal", res["Signal"])
        c2.metric("Market Bias", res["Bias"])
        c3.metric("Entry Price", p_fmt(res["Confirmed Entry ($)"]))
        c4.metric("RSI", res["RSI"])

        if "LONG" in res["Signal"] or "SHORT" in res["Signal"]:
            st.write("---")
            r1, r2, r3 = st.columns(3)
            r1.metric("🛑 Stop Loss (SL)", p_fmt(res["SL"]))
            r2.metric("🎯 Take Profit 1", p_fmt(res["TP1"]))
            r3.metric("🚀 Take Profit 2", p_fmt(res["TP2"]))
    else:
        st.error("Error fetching data.")

st.divider()
st.subheader("📊 Watchlist (Confirmed Closed Candles)")

if st.button("🔄 Refresh Watchlist"):
    st.rerun()

results = []
for sym in default_watchlist:
    analysis = analyze_stable_swing(sym)
    if analysis:
        p_f = lambda x: f"${x:.4f}" if x < 1 else f"${x:.2f}"
        results.append({
            "Coin": analysis["Coin"],
            "Signal": analysis["Signal"],
            "Bias": analysis["Bias"],
            "Confirmed Entry ($)": p_f(analysis["Confirmed Entry ($)"]),
            "SL ($)": p_f(analysis["SL"]) if analysis["SL"] > 0 else "-",
            "TP1 ($)": p_f(analysis["TP1"]) if analysis["TP1"] > 0 else "-",
            "TP2 ($)": p_f(analysis["TP2"]) if analysis["TP2"] > 0 else "-",
            "RSI": analysis["RSI"]
        })

if results:
    st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
