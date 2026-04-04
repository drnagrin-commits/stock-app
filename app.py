import streamlit as st
import pandas as pd
from core import analyze
from data import get_nasdaq100

st.title("📊 Rule #1 Screener PRO")

# ברירת מחדל NASDAQ 100
default_tickers = ["aapl"]

tickers_input = st.text_area(
    "Enter Tickers (comma separated)",
    ",".join(default_tickers)
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
    st.write("No valid data")
