# -*- coding: utf-8 -*-
"""
Stock Financial Overview - Streamlit GUI
המשתמש מזין מניות, לוחץ על כפתור, ומקבל טבלה עם:
צמיחת הכנסות 5 השנים האחרונות, CAGR, P/E, EPS, PEG, מחיר נוכחי ותחזית אנליסטים.
"""

import streamlit as st
import yfinance as yf
import pandas as pd

# -----------------------------
# פונקציות חישוב
# -----------------------------
def calculate_yearly_growth(revenue_series):
    revenue_series = revenue_series.dropna()
    revenue_series = revenue_series.head(5)  # רק 5 השנים האחרונות
    growth = revenue_series.pct_change() * 100
    return growth[1:]  # שנה ראשונה אין עליה

def calculate_cagr(revenue_series):
    revenue_series = revenue_series.dropna().head(5)
    if len(revenue_series) < 2:
        return None
    start_value = revenue_series.iloc[-1]
    end_value = revenue_series.iloc[0]
    n_years = len(revenue_series) - 1
    cagr = (end_value / start_value) ** (1/n_years) - 1
    return cagr * 100

# -----------------------------
# Streamlit UI
# -----------------------------
st.title("📊 Stock Financial Overview")
st.write("הכנס רשימת מניות מופרדות בפסיק (למשל: AAPL, MSFT, TSLA)")

user_input = st.text_input("רשימת מניות:", "AAPL, MSFT, TSLA")

if st.button("הצג טבלה"):
    stocks = [s.strip().upper() for s in user_input.split(",") if s.strip()]

    if not stocks:
        st.warning("לא הוזנה רשימת מניות תקינה.")
    else:
        results = []

        for stock in stocks:
            try:
                ticker = yf.Ticker(stock)
                earnings = ticker.financials.T
                info = ticker.info

                # צמיחת הכנסות
                if 'Total Revenue' in earnings.columns:
                    revenue = earnings['Total Revenue']
                    yearly_growth = calculate_yearly_growth(revenue)
                    cagr = calculate_cagr(revenue)
                else:
                    yearly_growth = []
                    cagr = None

                analyst_target = info.get("targetMeanPrice", "N/A")
                current_price = info.get("currentPrice", "N/A")

                result = {
                    "symbol": stock,
                    "Current_Price": current_price,
                    "Analyst_Target": analyst_target,
                    "CAGR_Total_Revenue": f"{cagr:.2f}%" if cagr is not None else "N/A",
                    "Trailing_PE": info.get("trailingPE", "N/A"),
                    "Forward_PE": info.get("forwardPE", "N/A"),
                    "EPS": info.get("trailingEps", "N/A"),
                    "PEG_Ratio": info.get("pegRatio", "N/A")
                }

                for i, val in enumerate(yearly_growth, 1):
                    result[f"Year_{i}_Growth"] = f"{val:.2f}%"

                results.append(result)

            except Exception as e:
                st.error(f"לא הצלחנו לקבל נתונים עבור {stock}: {e}")

        if results:
            df_results = pd.DataFrame(results)
            st.write("### טבלת נתונים פיננסיים")
            st.dataframe(df_results)
        else:
            st.warning("לא התקבלו נתונים למניות שהוזנו.")
