import streamlit as st
from analysis import analyze_stocks
from data import get_nasdaq100

st.title("📈 Rule #1 Stock Analyzer")

default_tickers = get_nasdaq100()

tickers_input = st.text_input(
    "Enter tickers (comma separated):",
    ",".join(default_tickers[:10])
)

tickers = [t.strip().upper() for t in tickers_input.split(",")]

if st.button("Analyze"):
    with st.spinner("Analyzing..."):
        df = analyze_stocks(tickers)

        if "Error" in df.columns:
            st.error("No data returned. Try fewer stocks.")
        else:
            st.dataframe(df)
