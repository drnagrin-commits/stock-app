# -*- coding: utf-8 -*-
"""
SOXX Analyzer + Rule #1 + Weighted ETF Score + Contribution Ranking
"""

import streamlit as st
import yfinance as yf
import pandas as pd

# --------------------------------
# SOXX Holdings + Weights (%)
# --------------------------------
SOXX_WEIGHTS = {
    "AVGO":10.3,
    "NVDA":9.8,
    "MU":7.6,
    "AMD":7.1,
    "MRVL":5.0,
    "AMAT":4.8,
    "INTC":4.5,
    "MPWR":4.0,
    "KLAC":4.0,
    "TER":3.8,
    "LRCX":3.7,
    "TXN":3.6,
    "ADI":3.4,
    "ASML":3.4,
    "QCOM":3.3,
    "NXPI":3.2,
    "TSM":3.0,
    "MCHP":2.5,
    "ON":2.4,
    "ENTG":2.2,
    "ALAB":1.8,
    "CRDO":1.7,
    "MTSI":1.6,
    "NVMI":1.5,
    "ASX":1.4,
    "AMKR":1.3,
    "UMC":1.2,
    "QRVO":1.1,
    "SWKS":1.0,
    "OLED":0.9,
    "STM":0.9,
    "LSCC":0.8,
    "ONTO":0.8,
    "COHR":0.7
}

STOCKS = list(SOXX_WEIGHTS.keys())

# --------------------------------
# Functions
# --------------------------------

def prepare_revenue_series(revenue_series):
    revenue_series = revenue_series.dropna()
    revenue_series = revenue_series.sort_index()
    revenue_series = revenue_series.tail(5)
    return revenue_series


def calculate_yearly_growth(revenue_series):
    revenue_series = prepare_revenue_series(revenue_series)
    return (revenue_series.pct_change()*100)[1:]


def calculate_cagr(revenue_series):
    revenue_series = prepare_revenue_series(revenue_series)

    if len(revenue_series)<2:
        return None

    start=revenue_series.iloc[0]
    end=revenue_series.iloc[-1]
    years=len(revenue_series)-1

    return ((end/start)**(1/years)-1)*100


def calculate_trend(revenue_series):
    try:
        growth=calculate_yearly_growth(revenue_series)

        if len(growth)<2:
            return None

        last=growth.iloc[-1]
        avg_prev=growth.iloc[:-1].mean()

        if last > avg_prev*1.05:
            return f"⬆️ {round(last,1)}%"
        elif last < avg_prev*0.95:
            return f"⬇️ {round(last,1)}%"
        else:
            return f"➡️ {round(last,1)}%"

    except:
        return None


def calculate_rule1_price(eps,growth_rate,future_pe=15):
    try:
        if eps is None or growth_rate is None:
            return None,None

        g=growth_rate/100
        future_eps=eps*((1+g)**10)
        future_price=future_eps*future_pe

        sticker=future_price/(1.15**10)
        buy=sticker*0.5

        return round(sticker,2),round(buy,2)

    except:
        return None,None


def get_decision(price,buy,sticker):

    if None in [price,buy,sticker]:
        return "N/A"

    if price<buy:
        return "BUY 🟢"

    elif price<sticker:
        return "WATCH 🟡"

    else:
        return "EXPENSIVE 🔴"


def calculate_score(cagr,peg,upside,price,buy):

    score=0

    if cagr:
        if cagr>15:
            score+=30
        elif cagr>10:
            score+=20
        elif cagr>5:
            score+=10

    if peg:
        if peg<1:
            score+=25
        elif peg<2:
            score+=15
        elif peg<3:
            score+=5

    if upside:
        if upside>30:
            score+=20
        elif upside>15:
            score+=10
        elif upside>5:
            score+=5

    if price and buy:
        mos=(buy-price)/buy*100

        if mos>30:
            score+=25
        elif mos>15:
            score+=15
        elif mos>0:
            score+=5

    return score


# --------------------------------
# UI
# --------------------------------

st.title("📊 SOXX Analyzer + Weighted ETF Score")

user_input = st.text_area(
    "מניות:",
    ",".join(STOCKS),
    height=150
)

if st.button("🚀 הרץ"):

    stocks=[s.strip().upper()
            for s in user_input.split(",")
            if s.strip()]

    results=[]

    for stock in stocks:

        try:

            ticker=yf.Ticker(stock)

            earnings=ticker.financials.T
            info=ticker.info

            if 'Total Revenue' not in earnings.columns:
                continue

            revenue=earnings["Total Revenue"]

            cagr=calculate_cagr(revenue)

            if cagr is None or cagr<=0:
                continue

            trend=calculate_trend(revenue)

            price=info.get("currentPrice")
            target=info.get("targetMeanPrice")
            forward_pe=info.get("forwardPE")
            trailing_pe=info.get("trailingPE")
            eps=info.get("trailingEps")

            upside=((target/price)-1)*100 if price and target else None

            peg=info.get("pegRatio")

            if peg is None and cagr and forward_pe:
                peg=forward_pe/cagr

            sticker,buy=calculate_rule1_price(
                eps,
                cagr,
                forward_pe or 15
            )

            decision=get_decision(
                price,
                buy,
                sticker
            )

            score=calculate_score(
                cagr,
                peg,
                upside,
                price,
                buy
            )

            if decision=="EXPENSIVE 🔴":
                score=score/2

            weight=SOXX_WEIGHTS.get(stock,0)

            contribution=score*weight/100

            results.append({
                "Symbol":stock,
                "Weight_%":weight,
                "Price":price,
                "Analyst_Target":target,
                "Trailing_PE":round(trailing_pe,2)
                    if isinstance(trailing_pe,(int,float)) else None,
                "Forward_PE":round(forward_pe,2)
                    if isinstance(forward_pe,(int,float)) else None,
                "CAGR_%":round(cagr,1),
                "Trend":trend,
                "PEG":round(peg,2)
                    if peg else None,
                "Upside_%":round(upside,1)
                    if upside else None,
                "Sticker":sticker,
                "Buy":buy,
                "Decision":decision,
                "Score":score,
                "SOXX_Contribution":round(contribution,2)
            })

        except:
            continue


    df=pd.DataFrame(results)

    if df.empty:
        st.warning("לא נמצאו נתונים")
        st.stop()


    df=df.sort_values(
        by="Score",
        ascending=False
    )


    st.subheader("📊 דירוג מניות")
    st.dataframe(df)


    # --------------------------------
    # Weighted SOXX Summary
    # --------------------------------

    numeric_cols=[
        "Price","Analyst_Target",
        "Trailing_PE","Forward_PE",
        "CAGR_%","PEG",
        "Upside_%","Sticker",
        "Buy","Score"
    ]

    summary={}

    for col in numeric_cols:

        valid=df[[col,"Weight_%"]].dropna()

        if len(valid)>0:

            summary[col]=round(
                (
                    valid[col]*
                    valid["Weight_%"]
                ).sum()
                /
                valid["Weight_%"].sum(),
                2
            )


    summary_row=pd.DataFrame([{
        "Symbol":"SOXX Weighted Avg",
        **summary
    }])

    st.subheader("📌 SOXX Weighted Average")
    st.dataframe(summary_row)


    # --------------------------------
    # Top 10 investable
    # --------------------------------

    st.subheader("🏆 Top 10 BUY / WATCH")

    top10=df[
        df["Decision"].isin(
            ["BUY 🟢","WATCH 🟡"]
        )
    ]

    if len(top10)==0:
        st.info("אין כרגע BUY/WATCH")
    else:
        st.dataframe(
            top10.head(10)
        )


    # --------------------------------
    # Contribution Ranking
    # --------------------------------

    st.subheader(
        "🏅 Biggest Contributors To SOXX Score"
    )

    contrib=df.sort_values(
        by="SOXX_Contribution",
        ascending=False
    )[
        [
            "Symbol",
            "Weight_%",
            "Score",
            "SOXX_Contribution"
        ]
    ]

    st.dataframe(
        contrib.head(15)
    )

    total_score=df[
        "SOXX_Contribution"
    ].sum()

    st.metric(
        "Composite SOXX Score",
        round(total_score,2)
    )

    st.caption(
        f"סה״כ מניות שנותחו: {len(df)}"
    )
