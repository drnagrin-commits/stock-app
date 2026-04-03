import numpy as np
from sklearn.linear_model import LinearRegression

def predict_growth(eps_history):
    if len(eps_history) < 3:
        return 0.1

    y = np.array(eps_history)
    X = np.arange(len(y)).reshape(-1,1)

    model = LinearRegression()
    model.fit(X, y)

    future = model.predict([[len(y)+3]])[0]
    growth = (future / y[-1]) ** (1/3) - 1

    return max(min(growth, 0.25), 0.05)

def predict_price(price_history):
    y = np.array(price_history)
    X = np.arange(len(y)).reshape(-1,1)

    model = LinearRegression()
    model.fit(X, y)

    return model.predict([[len(y)+30]])[0]

def ai_decision(price, sticker, mos, predicted_price):
    trend = (predicted_price / price) - 1

    if price < mos and trend > 0.1:
        return "STRONG BUY"
    elif price < sticker and trend > 0:
        return "BUY"
    else:
        return "WAIT"
