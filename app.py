import yfinance as yf
import pandas as pd
import numpy as np

# =========================
# Rule #1 Parameters
# =========================
DISCOUNT_RATE = 0.15
MOS_FACTOR = 0.5
YEARS = 10

# =========================
# Helper Functions
# =========================
def estimate_growth(stock):
    """
    Try to estimate growth using revenue history
    fallback to default if not available
    """
    try:
        rev = stock.financials.loc["Total Revenue"]
        rev = rev[::-1]  # oldest → newest
        if len(rev) >= 4:
            growth = (rev.iloc[-1] / rev.iloc[0]) ** (1/(len(rev)-1)) - 1
            return min(max(growth, 0.05), 0.25)  # clamp 5%-25%
    except:
        pass
    return 0.10  # fallback


def get_pe(stock):
    try:
        return stock.info.get("forwardPE") or stock.info.get("trailingPE") or 15
    except:
        return 15


def get_eps(stock):
    try:
        return stock.info.get("trailingEps") or 1
    except:
        return 1


def rule1_valuation(eps, growth, pe):
    future_eps = eps * ((1 + growth) ** YEARS)
    future_price = future_eps * pe
    sticker_price = future_price / ((1 + DISCOUNT_RATE) ** YEARS)
    mos_price = sticker_price * MOS_FACTOR
    return sticker_price, mos_price


# =========================
# Main Function
# =========================
def analyze_stocks(tickers):
    results = []

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)

            eps = get_eps(stock)
            growth = estimate_growth(stock)
            pe = get_pe(stock)

            sticker, mos = rule1_valuation(eps, growth, pe)

            price = stock.history(period="1d")["Close"].iloc[-1]

            results.append({
                "Ticker": ticker,
                "EPS": round(eps, 2),
                "Growth %": round(growth * 100, 1),
                "PE": round(pe, 1),
                "Sticker Price": round(sticker, 1),
                "MOS Price": round(mos, 1),
                "Current Price": round(price, 1),
                "Upside %": round((sticker/price - 1) * 100, 1)
            })

        except Exception as e:
            print(f"Error with {ticker}: {e}")

    df = pd.DataFrame(results)
    return df.sort_values(by="Upside %", ascending=False)


# =========================
# Run Example
# =========================
if __name__ == "__main__":
    tickers = [
        "INTC", "QCOM", "NVDA", "AVGO", "MU",
        "AMD", "AMAT", "MRVL", "KLAC", "TER", "MPWR"
    ]

    df = analyze_stocks(tickers)
    print(df)
