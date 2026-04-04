import streamlit as st
import pandas as pd
from core import analyze

st.title("Rule #1 AI App")

tickers_input = st.text_input("Enter Tickers", "NVDA,AMD,AMAT,TSLA")

tickers = [t.strip() for t in tickers_input.split(",")]

data = []
for t in tickers:
    res = analyze(t)
    if res:
        data.append(res)

df = pd.DataFrame(data)

if not df.empty:
    st.dataframe(df)
