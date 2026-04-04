import yfinance as yf
import numpy as np

DISCOUNT_RATE = 0.15
MOS_FACTOR = 0.5
YEARS = 10


# =========================
# Growth (Revenue based)
# =========================

def estimate_growth(stock):
    # ניסיון 1: Revenue
    try:
        rev = stock.financials.loc["Total Revenue"][::-1]
        if len(rev) >= 3:
            growth = (rev.iloc[-1] / rev.iloc[0]) ** (1/(len(rev)-1)) - 1
            return min(max(growth, 0.05), 0.25)
    except:
        pass

    # ניסיון 2: EPS growth
        try:
            eps_hist = stock.info.get("earningsQuarterlyGrowth")
            if eps_hist:
                return min(max(eps_hist, 0.05), 0.25)
        except:
            pass

    # fallback
    return 0.10
# =========================
# Data Extractors
# =========================
def get_eps(stock):
    return stock.info.get("trailingEps")


def get_roic(stock):
    return stock.info.get("returnOnCapital")


def get_pe(stock, growth):
    # Rule #1 Future PE
    return min(growth * 100 * 2, 25)


def get_forward_pe(stock):
    return stock.info.get("forwardPE")


# =========================
# Valuation
# =========================
def rule1(eps, growth, pe):
    future_eps = eps * ((1 + growth) ** YEARS)
    future_price = future_eps * pe
    sticker = future_price / ((1 + DISCOUNT_RATE) ** YEARS)
    mos = sticker * MOS_FACTOR
    return sticker, mos


# =========================
# 4M Scoring
# =========================
def score_4m(growth, roic, upside):
    moat = min(growth * 100, 25)
    management = min(roic * 100 if roic else 0, 25)
    margin_safety = min(max(upside, 0), 25)
    meaning = 20  # placeholder קבוע

    total = moat + management + margin_safety + meaning

    return moat, management, margin_safety, meaning, total


# =========================
# Sentiment
# =========================
def sentiment(future_pe, forward_pe):
    if not forward_pe:
        return "No Data"

    ratio = forward_pe / future_pe

    if ratio > 1.2:
        return "Overvalued"
    elif ratio < 0.8:
        return "Undervalued"
    return "Fair"


# =========================
# Analyze Single Stock
# =========================
def analyze(ticker):
    try:
        stock = yf.Ticker(ticker)

        eps = get_eps(stock)
        growth = estimate_growth(stock)
        roic = get_roic(stock)

        if not eps or not growth or roic is None:
            return None

        pe = get_pe(stock, growth)
        forward_pe = get_forward_pe(stock)

        sticker, mos = rule1(eps, growth, pe)

        price = stock.fast_info.get("lastPrice", None)
        if price is None or eps is None:
    continue

        upside = (sticker / price - 1) * 100

        moat, management, mos_score, meaning, score = score_4m(
            growth, roic, upside
        )

        if price < mos:
            decision = "STRONG BUY"
        elif price < sticker:
            decision = "BUY"
        else:
            decision = "WAIT"

        return {
            "Ticker": ticker,
            "Price": round(price,2),
            "EPS": round(eps,2),
            "Growth%": round(growth*100,1),
            "ROIC%": round(roic*100,1),
            "Future PE": round(pe,1),
            "Forward PE": round(forward_pe,1) if forward_pe else None,
            "Sentiment": sentiment(pe, forward_pe),
            "Sticker": round(sticker,1),
            "MOS": round(mos,1),
            "Upside%": round(upside,1),
            "Moat": round(moat,1),
            "Management": round(management,1),
            "MOS Score": round(mos_score,1),
            "Meaning": meaning,
            "Score": round(score,1),
            "Decision": decision
        }

    except:
        return None
