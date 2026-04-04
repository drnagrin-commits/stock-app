import yfinance as yf
import pandas as pd

DISCOUNT_RATE = 0.15
MOS_FACTOR = 0.5
YEARS = 10


def get_price(stock):
    try:
        price = stock.fast_info.get("lastPrice")
        if price:
            return price
    except:
        pass

    try:
        return stock.history(period="5d")["Close"].dropna().iloc[-1]
    except:
        return None


def get_eps(stock):
    try:
        return stock.info.get("trailingEps")
    except:
        return None


def get_pe(stock):
    try:
        return stock.info.get("forwardPE") or stock.info.get("trailingPE")
    except:
        return None


def estimate_growth(stock):
    try:
        rev = stock.financials.loc["Total Revenue"][::-1]
        if len(rev) >= 3:
            growth = (rev.iloc[-1] / rev.iloc[0]) ** (1/(len(rev)-1)) - 1
            return min(max(growth, 0.05), 0.25)
    except:
        pass
    return 0.10


def get_roic(stock):
    try:
        return stock.info.get("returnOnCapital") or stock.info.get("returnOnEquity")
    except:
        return None


def rule1_calc(eps, growth, pe):
    future_eps = eps * ((1 + growth) ** YEARS)
    future_price = future_eps * pe
    sticker = future_price / ((1 + DISCOUNT_RATE) ** YEARS)
    mos = sticker * MOS_FACTOR
    return sticker, mos


def score_mos(price, mos):
    if price < mos:
        return 10
    elif price < mos * 1.2:
        return 7
    else:
        return 3


def analyze_stocks(tickers):
    results = []

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)

            price = get_price(stock)
            eps = get_eps(stock)
            pe = get_pe(stock)
            growth = estimate_growth(stock)
            roic = get_roic(stock)

            if not price or not eps or not pe:
                continue

            sticker, mos = rule1_calc(eps, growth, pe)
            upside = (sticker / price - 1) * 100

            # 4M scores (פשוטים אבל אפקטיביים)
            m1 = 10 if roic and roic > 0.15 else 5
            m2 = 8 if growth > 0.10 else 5
            m3 = 8 if eps > 0 else 4
            m4 = score_mos(price, mos)

            score = round((m1 + m2 + m3 + m4) / 4, 1)

            decision = "BUY" if score >= 7 else "WATCH" if score >= 5 else "AVOID"

            results.append({
                "Ticker": ticker,
                "Price": round(price, 2),
                "EPS": round(eps, 2),
                "Growth %": round(growth * 100, 1),
                "ROIC %": round((roic or 0) * 100, 1),
                "PE": round(pe, 1),
                "Sticker": round(sticker, 1),
                "MOS": round(mos, 1),
                "Upside %": round(upside, 1),
                "M1": m1,
                "M2": m2,
                "M3": m3,
                "M4": m4,
                "Score": score,
                "Decision": decision
            })

        except Exception as e:
            print(f"{ticker} failed: {e}")

    df = pd.DataFrame(results)

    if len(df) == 0:
        return pd.DataFrame([{"Error": "No valid data returned"}])

    return df.sort_values(by="Upside %", ascending=False)
