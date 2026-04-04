import yfinance as yf
from ai_module import predict_price, ai_decision

DISCOUNT_RATE = 0.15
MOS_MARGIN = 0.5

def sticker(eps, growth, pe):
    future_eps = eps * ((1+growth)**10)
    future_price = future_eps * pe
    return future_price / ((1+DISCOUNT_RATE)**10)


def growth(stock):
    try:
        rev = stock.financials.loc["Total Revenue"]
        rev = rev[::-1] # oldest → newest
        if len(rev) >= 4:
            Egrowth = (rev.iloc[-1] / rev.iloc[0]) ** (1/(len(rev)-1)) - 1
            return min(max(Egrowth, 0.05), 1.25) # clamp 5%-25%
    except:
        pass
    return 0.10 # fallback


def analyze(ticker):
    s = yf.Ticker(ticker)

    try:
        price = s.info["currentPrice"]
        eps = s.info["trailingEps"]
        pe = s.info.get("trailingPE", 20)

        earnings = s.earnings
        eps_history = earnings["Earnings"].values if earnings is not None else [eps]

        hist = s.history(period="1y")
        predicted_price = predict_price(hist["Close"].values)

        stick = sticker(eps, growth, pe)
        mos = stick * 0.5

        ai_signal = ai_decision(price, stick, mos, predicted_price)

        return {
            "Ticker": ticker,
            "Price": round(price,2),
            "Sticker": round(stick,2),
            "MOS": round(mos,2),
            "AI": ai_signal
        }

    except:
        return None




