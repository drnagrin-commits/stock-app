
# -*- coding: utf-8 -*-
"""
Stock Analyzer + Rule #1 + NASDAQ100 + SCORE + TREND (With %)
"""

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
    "MAR","MELI","ORLY","FTNT","ABNB","WDAY","KDP","NXPI","MRVL","CHTR",
    "MNST","AEP","EXC","LULU","ROST","ODFL","DXCM","PAYX","XEL","CTAS",
    "FAST","SIRI","EA","IDXX","BIIB","VRSK","ILMN","TEAM","EBAY","WBA",
    "ANSS","CPRT","ZM","PDD","LCID","RIVN","ZS","CRWD","DDOG","OKTA",
    "PANW","DOCU","MTCH","SPLK","ALGN","SGEN","VRSN","CDW","PCAR","DLTR",
    "TTWO","UAL","KHC","GEHC","FANG","MCHP","ON","ASML"
]

# -----------------------------
# פונקציות
# -----------------------------
def prepare_revenue_series(revenue_series):
    revenue_series = revenue_series.dropna()
    revenue_series = revenue_series.sort_index()  # 🔥 קריטי
    revenue_series = revenue_series.tail(5)
    return revenue_series

def calculate_yearly_growth(revenue_series):
    revenue_series = prepare_revenue_series(revenue_series)
    return (revenue_series.pct_change() * 100)[1:]

def calculate_cagr(revenue_series):
    revenue_series = prepare_revenue_series(revenue_series)

    if len(revenue_series) < 2:
        return None

    start, end = revenue_series.iloc[0], revenue_series.iloc[-1]
    years = len(revenue_series) - 1

    return ((end / start) ** (1/years) - 1) * 100

def calculate_trend(revenue_series):
    try:
        growth_series = calculate_yearly_growth(revenue_series)

        if len(growth_series) < 2:
            return None

        last_year = growth_series.iloc[-1]
        avg_previous = growth_series.iloc[:-1].mean()

        # 🔥 לוגיקה עם סף + הצגת אחוז
        if last_year > avg_previous * 1.05:
            return f"⬆️ {round(last_year,1)}%"
        elif last_year < avg_previous * 0.95:
            return f"⬇️ {round(last_year,1)}%"
        else:
            return f"➡️ {round(last_year,1)}%"

    except:
        return None

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
        if cagr > 15:
            score += 30
        elif cagr > 10:
            score += 20
        elif cagr > 5:
            score += 10

    if peg:
        if peg < 1:
            score += 25
        elif peg < 2:
            score += 15
        elif peg < 3:
            score += 5

    if upside:
        if upside > 30:
            score += 20
        elif upside > 15:
            score += 10
        elif upside > 5:
            score += 5

    if price and buy:
        mos = (buy - price) / buy * 100
        if mos > 30:
            score += 25
        elif mos > 15:
            score += 15
        elif mos > 0:
            score += 5

    return score

# -----------------------------
# UI
# -----------------------------
st.title("📊 NASDAQ 100 Analyzer + SCORE + TREND")

user_input = st.text_area("מניות:", ",".join(NASDAQ_100), height=150)

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

            revenue = earnings['Total Revenue']

            cagr = calculate_cagr(revenue)
            if cagr is None or cagr <= 0:
                continue

            trend = calculate_trend(revenue)

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
                "Analyst_Target": target if target else "N/A",
                "Trailing_PE": round(info.get("trailingPE"), 2) if isinstance(info.get("trailingPE"), (int, float)) else None,
                "Forward_PE": round(forward_pe, 2) if isinstance(forward_pe, (int, float)) else None,
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
        st.info("אין מניות BUY/WATCH כרגע")
    else:
        st.dataframe(top10.head(10))

    st.caption(f"סה״כ מניות שנותחו: {len(df)}")
