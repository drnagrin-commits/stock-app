# -*- coding: utf-8 -*-
import streamlit as st
import yfinance as yf
import pandas as pd

# -----------------------------
# NASDAQ 100
# -----------------------------
NASDAQ_100 = [
    "AAPL","MSFT","AMZN","NVDA","GOOGL","GOOG","META","TSLA","AVGO","PEP",
    "COST","CSCO","ADBE","NFLX","CMCSA","INTC","AMD","TXN","QCOM","AMGN",
    "HON","INTU","AMAT","ISRG","BKNG","ADI","MDLZ","GILD","LRCX","MU",
    "REGN","VRTX","FISV","CSX","ADP","ATVI","SNPS","PYPL","CDNS","KLAC",
    "MAR","MELI","ORLY","FTNT","ABNB","WDAY","KDP","NXPI","MRVL","CHTR"
]

# -----------------------------
# פונקציות
# -----------------------------
def calculate_cagr(revenue_series):
    revenue_series = revenue_series.dropna().head(5)[::-1]
    if len(revenue_series) < 2:
        return None
    start, end = revenue_series.iloc[0], revenue_series.iloc[-1]
    years = len(revenue_series) - 1
    return ((end / start) ** (1/years) - 1) * 100

def calculate_rule1_price(eps, growth_rate, future_pe=15):
    try:
        if eps is None or growth_rate is None:
            return None, None
        growth_rate = growth_rate / 100
        future_eps = eps * ((1 + growth_rate) ** 10)
        future_price = future_eps * future_pe
        sticker = future_price / (1.15 ** 10)
        buy = sticker * 0.5
        return round(sticker, 2), round(buy, 2)
    except:
        return None, None

def get_decision(price, buy, sticker):
    if price is None or buy is None or sticker is None:
        return "N/A"
    if price < buy:
        return "BUY 🟢"
    elif price < sticker:
        return "WATCH 🟡"
    else:
        return "EXPENSIVE 🔴"

def calculate_score(cagr, peg, upside, price, buy):
    score = 0

    if cagr:
        if cagr > 15: score += 30
        elif cagr > 10: score += 20
        elif cagr > 5: score += 10

    if peg:
        if peg < 1: score += 25
        elif peg < 2: score += 15
        elif peg < 3: score += 5

    if upside:
        if upside > 30: score += 20
        elif upside > 15: score += 10
        elif upside > 5: score += 5

    if price and buy:
        mos = (buy - price) / buy * 100
        if mos > 30: score += 25
        elif mos > 15: score += 15
        elif mos > 0: score += 5

    return score

def clean(val):
    return round(val, 2) if isinstance(val, (int, float)) else None

# -----------------------------
# UI
# -----------------------------
st.title("📊 NASDAQ Analyzer + Rule #1 + Score")

user_input = st.text_area("מניות:", ",".join(NASDAQ_100), height=120)

if st.button("🚀 הרץ"):
    stocks = [s.strip().upper() for s in user_input.split(",") if s.strip()]
    results = []

    for stock in stocks:
        try:
            ticker = yf.Ticker(stock)
            info = ticker.info
            earnings = ticker.financials.T

            # Growth
            if 'Total Revenue' in earnings.columns:
                cagr = calculate_cagr(earnings['Total Revenue'])
            else:
                cagr = None

            # נתונים בסיסיים
            price = info.get("currentPrice")
            trailing_pe = info.get("trailingPE")
            forward_pe = info.get("forwardPE")
            eps = info.get("trailingEps")

            # Analyst target
            analyst_target = info.get("targetMeanPrice")

            # Upside
            if isinstance(price, (int, float)) and isinstance(analyst_target, (int, float)):
                upside = ((analyst_target - price) / price) * 100
            else:
                upside = None

            # PEG
            peg = info.get("pegRatio")
            if peg is None and cagr and forward_pe:
                peg = forward_pe / cagr

            # Rule #1
            sticker, buy = calculate_rule1_price(eps, cagr, forward_pe or 15)

            # Decision
            decision = get_decision(price, buy, sticker)

            # Score
            score = calculate_score(cagr, peg, upside, price, buy)

            results.append({
                "Symbol": stock,
                "Price": clean(price),
                "Trailing_PE": clean(trailing_pe),
                "Forward_PE": clean(forward_pe),
                "CAGR_%": clean(cagr),
                "PEG": clean(peg),
                "Upside_%": clean(upside),
                "Analyst_Target": clean(analyst_target),
                "Sticker": sticker,
                "Buy": buy,
                "Decision": decision,
                "Score": score
            })

        except Exception as e:
            st.error(f"שגיאה ב-{stock}: {e}")

    # DataFrame
    df = pd.DataFrame(results)

    if df.empty:
        st.warning("לא התקבלו נתונים")
    else:
        # סינון בטוח
        if "CAGR_%" in df.columns:
            df = df[df["CAGR_%"].notna()]

        df = df.sort_values(by="Score", ascending=False)

        st.subheader("📊 תוצאות")
        st.dataframe(df)

        st.subheader("🏆 Top 10")
        st.dataframe(df.head(10))
