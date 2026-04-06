# -*- coding: utf-8 -*-
"""
Stock Analyzer + Rule #1 + NASDAQ100 + S&P500 + SCORE + TREND
"""

import streamlit as st
import yfinance as yf
import pandas as pd

# -----------------------------
# NASDAQ 100
# -----------------------------
NASDAQ_100 = [
    "AAPL","MSFT","AMZN","NVDA","GOOGL","GOOG","META","TSLA","AVGO","PEP"
]

# -----------------------------
# S&P 500 (נשלף אוטומטית)
# -----------------------------
@st.cache_data
def get_sp500():
    table = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
    df = table[0]
    return df["Symbol"].tolist()

# -----------------------------
# פונקציות
# -----------------------------
def prepare_revenue_series(revenue_series):
    revenue_series = revenue_series.dropna()
    revenue_series = revenue_series.sort_index()  # 🔥 תיקון קריטי
    revenue_series = revenue_series.tail(5)
    return revenue_series

def calculate_yearly_growth(revenue_series):
    return (revenue_series.pct_change() * 100)[1:]

def calculate_cagr(revenue_series):
    if len(revenue_series) < 2:
        return None
    start, end = revenue_series.iloc[0], revenue_series.iloc[-1]
    years = len(revenue_series) - 1
    return ((end / start) ** (1/years) - 1) * 100

def calculate_trend(revenue_series):
    try:
        growth = calculate_yearly_growth(revenue_series)

        if len(growth) < 2:
            return None

        last_year = growth.iloc[-1]
        prev_avg = growth.iloc[:-1].mean()

        # 🔥 תיקון לוגיקה + מניעת רעש
        if last_year > prev_avg * 1.05:
            return "⬆️"
        elif last_year < prev_avg * 0.95:
            return "⬇️"
        else:
            return "➡️"

    except:
        return None

def calculate_revenue_metrics(revenue_series):
    try:
        return revenue_series.mean(), revenue_series.iloc[-1]
    except:
        return None, None

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

# -----------------------------
# UI
# -----------------------------
st.title("📊 Stock Analyzer PRO")

# שילוב רשימות
sp500 = get_sp500()
ALL_STOCKS = list(set(NASDAQ_100 + sp500))

user_input = st.text_area("מניות:", ",".join(ALL_STOCKS), height=150)

if st.button("🚀 הרץ"):
    stocks = [s.strip().upper() for s in user_input.split(",") if s.strip()]
    results = []

    for stock in stocks:
        try:
            ticker = yf.Ticker(stock)
            earnings = ticker.financials.T
            info = ticker.info

            if 'Total Revenue' not in earnings.columns:
                continue

            revenue = prepare_revenue_series(earnings['Total Revenue'])

            if len(revenue) < 2:
                continue

            cagr = calculate_cagr(revenue)
            if cagr is None or cagr <= 0:
                continue

            trend = calculate_trend(revenue)
            revenue_avg, revenue_last = calculate_revenue_metrics(revenue)

            price = info.get("currentPrice")
            target = info.get("targetMeanPrice")
            forward_pe = info.get("forwardPE")
            eps = info.get("trailingEps")

            upside = ((target / price) - 1) * 100 if price and target else None

            peg = info.get("pegRatio")
            if peg is None and cagr and forward_pe:
                peg = forward_pe / cagr

            sticker, buy = calculate_rule1_price(eps, cagr, forward_pe or 15)
            decision = get_decision(price, buy, sticker)

            score = calculate_score(cagr, peg, upside, price, buy)
            if decision == "EXPENSIVE 🔴":
                score = score / 2

            results.append({
                "Symbol": stock,
                "Price": price,
                "Revenue_Avg": round(revenue_avg, 0) if revenue_avg else None,
                "Revenue_Last": round(revenue_last, 0) if revenue_last else None,
                "CAGR_%": round(cagr,1),
                "Trend": trend,
                "PEG": round(peg,2) if peg else None,
                "Upside_%": round(upside,1) if upside else None,
                "Sticker": sticker,
                "Buy": buy,
                "Decision": decision,
                "Score": score
            })

        except:
            continue

    df = pd.DataFrame(results)

    if df.empty:
        st.warning("לא נמצאו מניות מתאימות")
        st.stop()

    df = df.sort_values(by="Score", ascending=False)

    st.subheader("📊 דירוג מניות")
    st.dataframe(df)

    st.subheader("🏆 Top 10 (BUY / WATCH)")
    top10 = df[df["Decision"].isin(["BUY 🟢", "WATCH 🟡"])]

    if top10.empty:
        st.info("אין מניות מתאימות כרגע")
    else:
        st.dataframe(top10.head(10))

    st.caption(f"סה״כ מניות: {len(df)}")
