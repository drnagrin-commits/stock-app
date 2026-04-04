import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np

DISCOUNT_RATE = 0.15
MOS_MARGIN = 0.5

# NASDAQ 100 (ברירת מחדל)
DEFAULT_TICKERS = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","TSLA",
    "AVGO","COST","PEP","ADBE","CSCO","NFLX","AMD","INTC",
    "CMCSA","TXN","QCOM","AMGN","HON","INTU","ISRG","AMAT",
    "BKNG","ADI","MDLZ","LRCX","MU","GILD","PANW","SNPS",
    "CDNS","KLAC","VRTX","REGN","ADP","MAR","MNST","FTNT"
]

def get_growth(stock):
    try:
        earnings = stock.earnings
        if earnings is None or len(earnings) < 3:
            return 0.1

        eps = earnings["Earnings"].values
        growth_rates = []

        for i in range(1, len(eps)):
            if eps[i-1] > 0:
                growth_rates.append((eps[i]/eps[i-1]) - 1)

        return np.mean(growth_rates) if growth_rates else 0.1
    except:
        return 0.1


def calculate_sticker(eps, growth, pe):
    future_eps = eps * ((1 + growth) ** 10)
    future_price = future_eps * pe
    sticker = future_price / ((1 + DISCOUNT_RATE) ** 10)
    return sticker


def analyze(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        price = info.get("currentPrice")
        eps = info.get("trailingEps")
        pe = info.get("trailingPE", 20)
        roic = info.get("returnOnCapital", None)

        if not price or not eps:
            return None

        growth = get_growth(stock)

        sticker = calculate_sticker(eps, growth, pe)
        mos = sticker * MOS_MARGIN
        upside = (sticker - price) / price * 100

        # Score פשוט
        score = (growth * 100) * 0.4 + (roic or 0) * 100 * 0.3 + upside * 0.3

        # Decision לפי Rule #1 בלבד
        if price < mos:
            decision = "🔥 STRONG BUY"
        elif price < sticker:
            decision = "🟢 BUY"
        else:
            decision = "🟡 WAIT"

        return {
            "Ticker": ticker,
            "Price": round(price,2),
            "EPS": round(eps,2),
            "%Growth": round(growth*100,1),
            "ROIC%": round((roic or 0)*100,1),
            "Sticker": round(sticker,2),
            "MOS": round(mos,2),
            "Upside%": round(upside,1),
            "Score": round(score,1),
            "Decision": decision
        }

    except:
        return None


# UI
st.title("📊 Rule #1 Screener (Yahoo Data Only)")

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
    st.write("No data available")
