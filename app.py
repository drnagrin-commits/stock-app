import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np

DISCOUNT_RATE = 0.15
MOS_MARGIN = 0.5

DEFAULT_TICKERS = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA",
    "AVGO","COST","PEP","ADBE","CSCO","NFLX","AMD","INTC",
    "TXN","QCOM","AMGN","INTU","ISRG","AMAT","BKNG",
    "ADI","LRCX","MU","PANW","SNPS","CDNS","KLAC"
]

# =========================
# EPS Growth
# =========================
def get_growth(stock):
    try:
        earnings = stock.earnings

        if earnings is None or len(earnings) < 3:
            return None

        eps = earnings["Earnings"].values
        growth_rates = []

        for i in range(1, len(eps)):
            if eps[i-1] > 0:
                growth_rates.append((eps[i]/eps[i-1]) - 1)

        return np.mean(growth_rates) if growth_rates else None

    except:
        return None


# =========================
# Sticker + Future PE
# =========================
def calculate_sticker(eps, growth):
    future_eps = eps * ((1 + growth) ** 10)

    future_pe = min(growth * 100 * 2, 25)

    future_price = future_eps * future_pe
    sticker = future_price / ((1 + DISCOUNT_RATE) ** 10)

    return sticker, future_pe


# =========================
# Market Sentiment
# =========================
def get_sentiment(future_pe, forward_pe):
    if not forward_pe:
        return "No Data"

    ratio = forward_pe / future_pe

    if ratio > 1.2:
        return "🔴 Overvalued"
    elif ratio < 0.8:
        return "🟢 Undervalued"
    else:
        return "🟡 Fair"


# =========================
# Analyze Stock
# =========================
def analyze(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        price = info.get("currentPrice")
        eps = info.get("trailingEps")
        roic = info.get("returnOnCapital")
        forward_pe = info.get("forwardPE")

        growth = get_growth(stock)

        if not price or not eps or not growth or roic is None:
            return None

        sticker, future_pe = calculate_sticker(eps, growth)
        mos = sticker * MOS_MARGIN
        upside = (sticker - price) / price * 100

        score = (
            growth * 100 * 0.4 +
            roic * 100 * 0.3 +
            upside * 0.3
        )

        # Decision Rule #1
        if price < mos:
            decision = "🔥 STRONG BUY"
        elif price < sticker:
            decision = "🟢 BUY"
        else:
            decision = "🟡 WAIT"

        sentiment = get_sentiment(future_pe, forward_pe)

        return {
            "Ticker": ticker,
            "Price": round(price,2),
            "EPS": round(eps,2),
            "%Growth": round(growth*100,1),
            "ROIC%": round(roic*100,1),
            "Future PE": round(future_pe,1),
            "Forward PE": round(forward_pe,1) if forward_pe else None,
            "Market Sentiment": sentiment,
            "Sticker": round(sticker,2),
            "MOS": round(mos,2),
            "Upside%": round(upside,1),
            "Score": round(score,1),
            "Decision": decision
        }

    except:
        return None


# =========================
# UI
# =========================
st.title("📊 Rule #1 Screener PRO")

tickers_input = st.text_input(
    "Enter Tickers (comma separated)",
    ",".join(DEFAULT_TICKERS)
)

tickers = [t.strip().upper() for t in tickers_input.split(",")]

results = []

for t in tickers:
    res = analyze(t)
    if res:
        results.append(res)

df = pd.DataFrame(results)

if not df.empty:
    df = df.sort_values(by="Score", ascending=False)
    st.dataframe(df)
else:
    st.write("No valid data (missing EPS / Growth / ROIC)")
