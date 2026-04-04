# -*- coding: utf-8 -*-
"""
Stock Financial Overview - Streamlit GUI (FIXED GROWTH)
כולל תיקון סדר כרונולוגי לחישוב Growth ו-CAGR
"""

import streamlit as st
import yfinance as yf
import pandas as pd

# -----------------------------
# פונקציות חישוב
# -----------------------------
def calculate_yearly_growth(revenue_series):
    revenue_series = revenue_series.dropna()
    revenue_series = revenue_series.head(5)

    # 🔥 תיקון: סדר כרונולוגי נכון (ישן -> חדש)
    revenue_series = revenue_series[::-1]

    growth = revenue_series.pct_change() * 100
    return growth[1:]

def calculate_cagr(revenue_series):
    revenue_series = revenue_series.dropna().head(5)

    # 🔥 תיקון: סדר כרונולוגי
    revenue_series = revenue_series[::-1]

    if len(revenue_series) < 2:
        return None

    start_value = revenue_series.iloc[0]
    end_value = revenue_series.iloc[-1]
    n_years = len(revenue_series) - 1

    cagr = (end_value / start_value) ** (1/n_years) - 1
    return cagr * 100

# -----------------------------
# UI
# -----------------------------
st.title("📊 Stock Financial Overview (Fixed Growth)")

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

                # חישוב אפסייד לפי אנליסטים
                if isinstance(current_price, (int, float)) and isinstance(analyst_target, (int, float)):
                    upside = ((analyst_target / current_price) - 1) * 100
                    upside_str = f"{upside:.2f}%"
                else:
                    upside_str = "N/A"

                result = {
                    "symbol": stock,
                    "Current_Price": current_price,
                    "Analyst_Target": analyst_target,
                    "Upside_%": upside_str,
                    "CAGR_Total_Revenue": f"{cagr:.2f}%" if cagr is not None else "N/A",
                    "Trailing_PE": info.get("trailingPE", "N/A"),
                    "Forward_PE": info.get("forwardPE", "N/A"),
                    "EPS": info.get("trailingEps", "N/A"),
                    "PEG_Ratio": info.get("pegRatio", "N/A")
                }

                # הוספת צמיחה שנתית
                for i, val in enumerate(yearly_growth, 1):
                    result[f"Year_{i}_Growth"] = f"{val:.2f}%"

                results.append(result)

            except Exception as e:
                st.error(f"שגיאה ב-{stock}: {e}")

        if results:
            df_results = pd.DataFrame(results)
            st.write("### 📊 טבלת נתונים פיננסיים")
            st.dataframe(df_results)
        else:
            st.warning("לא התקבלו נתונים.")
