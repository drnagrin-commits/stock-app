# -*- coding: utf-8 -*-
"""
Stock Analyzer + Rule #1 + NASDAQ100 + SCORE
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
def calculate_yearly_growth(revenue_series):
    revenue_series = revenue_series.dropna().head(5)[::-1]
    return (revenue_series.pct_change() * 100)[1:]

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

# -----------------------------
# 🔥 SCORING FUNCTION
# -----------------------------
def calculate_score(cagr, peg, upside, price, buy):
    score = 0

    # CAGR (30)
    if cagr:
        if cagr > 15:
            score += 30
        elif cagr > 10:
            score += 20
        elif cagr > 5:
            score += 10

    # PEG (25)
    if peg:
        if peg < 1:
            score += 25
        elif peg < 2:
            score += 15
        elif peg < 3:
            score += 5

    # Upside (20)
    if upside:
        if upside > 30:
            score += 20
        elif upside > 15:
            score += 10
        elif upside > 5:
            score += 5

    # Margin of Safety (25)
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
st.title("📊 NASDAQ 100 Analyzer + SCORE")

user_input = st.text_area("מניות:", ",".join(NASDAQ_100), height=150)

if st.button("🚀 הרץ"):
    stocks = [s.strip().upper() for s in user_input.split(",") if s.strip()]
    results = []

    for stock in stocks:
        try:
            ticker = yf.Ticker(stock)
            earnings = ticker.financials.T
            info = ticker.info

            # Growth
            if 'Total Revenue' in earnings.columns:
                revenue = earnings['Total Revenue']
                cagr = calculate_cagr(revenue)
            else:
                cagr = None

            price = info.get("currentPrice")
            target = info.get("targetMeanPrice")
            forward_pe = info.get("forwardPE")
            eps = info.get("trailingEps")

            # Upside
            upside = None
            if price and target:
                upside = ((target / price) - 1) * 100

            # PEG
            peg = info.get("pegRatio")
            if peg is None and cagr and forward_pe:
                peg = forward_pe / cagr

            # Rule #1
            sticker, buy = calculate_rule1_price(eps, cagr, forward_pe or 15)

            # Decision
            decision = get_decision(price, buy, sticker)

            # 🔥 SCORE
            score = calculate_score(cagr, peg, upside, price, buy)
            analyst_target = info.get("targetMeanPrice")
            results.append({
                "Symbol": stock,
                "Price": price,
                "Analyst_Target": analyst_target if analyst_target else "N/A",
                "Trailing_PE": round(info.get("trailingPE"), 2) if isinstance(info.get("trailingPE"), (int, float)) else None,
                "Forward_PE": round(forward_pe, 2) if isinstance(forward_pe, (int, float)) else None,
                "CAGR_%": round(cagr,1) if cagr else None,
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

    # 🔥 מיון לפי ציון
    df = df.sort_values(by="Score", ascending=False)

    st.subheader("📊 דירוג מניות")
    st.dataframe(df)

    # Top 10
    st.subheader("🏆 Top 10")
    st.dataframe(df.head(10))
