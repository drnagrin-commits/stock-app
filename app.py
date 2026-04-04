# -*- coding: utf-8 -*-
"""
Stock Financial Overview + Rule #1
כולל:
- Growth מתוקן
- CAGR
- PEG (עם fallback)
- Upside
- Rule #1 Sticker Price + Buy Price
"""

import streamlit as st
import yfinance as yf
import pandas as pd

# -----------------------------
# פונקציות חישוב
# -----------------------------
def calculate_yearly_growth(revenue_series):
    revenue_series = revenue_series.dropna().head(5)
    revenue_series = revenue_series[::-1]  # סדר כרונולוגי
    growth = revenue_series.pct_change() * 100
    return growth[1:]

def calculate_cagr(revenue_series):
    revenue_series = revenue_series.dropna().head(5)
    revenue_series = revenue_series[::-1]

    if len(revenue_series) < 2:
        return None

    start_value = revenue_series.iloc[0]
    end_value = revenue_series.iloc[-1]
    n_years = len(revenue_series) - 1

    return ((end_value / start_value) ** (1/n_years) - 1) * 100

def calculate_rule1_price(eps, growth_rate, future_pe=15, discount_rate=0.15, years=10):
    try:
        if eps is None or growth_rate is None:
            return None, None

        growth_rate = growth_rate / 100

        future_eps = eps * ((1 + growth_rate) ** years)
        future_price = future_eps * future_pe
        sticker_price = future_price / ((1 + discount_rate) ** years)
        buy_price = sticker_price * 0.5

        return round(sticker_price, 2), round(buy_price, 2)

    except:
        return None, None

# -----------------------------
# UI
# -----------------------------
st.title("📊 Stock Analyzer + Rule #1")

user_input = st.text_input("הכנס מניות (AAPL, MSFT, TSLA):", "AAPL, MSFT, TSLA")

if st.button("הצג נתונים"):
    stocks = [s.strip().upper() for s in user_input.split(",") if s.strip()]

    results = []

    for stock in stocks:
        try:
            ticker = yf.Ticker(stock)
            earnings = ticker.financials.T
            info = ticker.info

            # Revenue growth
            if 'Total Revenue' in earnings.columns:
                revenue = earnings['Total Revenue']
                yearly_growth = calculate_yearly_growth(revenue)
                cagr = calculate_cagr(revenue)
            else:
                yearly_growth = []
                cagr = None

            current_price = info.get("currentPrice")
            analyst_target = info.get("targetMeanPrice")
            forward_pe = info.get("forwardPE")
            eps = info.get("trailingEps")

            # Upside
            if isinstance(current_price, (int, float)) and isinstance(analyst_target, (int, float)):
                upside = ((analyst_target / current_price) - 1) * 100
                upside_str = f"{upside:.2f}%"
            else:
                upside_str = "N/A"

            # PEG fallback
            peg = info.get("pegRatio")
            if peg is None:
                if cagr and forward_pe:
                    peg = forward_pe / cagr
            peg_str = f"{peg:.2f}" if isinstance(peg, (int, float)) else "N/A"

            # 🔥 Rule #1
            sticker, buy = calculate_rule1_price(
                eps=eps,
                growth_rate=cagr,
                future_pe=forward_pe if forward_pe else 15
            )

            # תוצאה
            result = {
                "symbol": stock,
                "Price": current_price,
                "Target": analyst_target,
                "Upside_%": upside_str,
                "CAGR_%": f"{cagr:.2f}%" if cagr else "N/A",
                "Trailing_PE": info.get("trailingPE"),
                "Forward_PE": forward_pe,
                "EPS": eps,
                "PEG": peg_str,
                "Sticker_Price": sticker,
                "Buy_Price": buy
            }

            # Growth לפי שנים
            for i, val in enumerate(yearly_growth, 1):
                result[f"Growth_Y{i}"] = f"{val:.2f}%"

            results.append(result)

        except Exception as e:
            st.error(f"שגיאה ב-{stock}: {e}")

    if results:
        df = pd.DataFrame(results)

        st.subheader("📊 תוצאות")
        st.dataframe(df)

        # Highlight Rule #1 opportunity
        st.subheader("🔥 הזדמנויות לפי Rule #1")

        opportunities = df[
            (df["Price"].notna()) &
            (df["Buy_Price"].notna()) &
            (df["Price"] < df["Buy_Price"])
        ]

        if not opportunities.empty:
            st.success("יש מניות מתחת ל-Buy Price 🎯")
            st.dataframe(opportunities)
        else:
            st.warning("אין מניות זולות לפי Rule #1 כרגע")
