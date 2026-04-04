import pandas as pd

def get_nasdaq100():
    url = "https://en.wikipedia.org/wiki/Nasdaq-100"
    tables = pd.read_html(url)
    
    df = tables[4]  # הטבלה של החברות
    
    tickers = df["Ticker"].tolist()
    
    # תיקון תווים
    tickers = [t.replace(".", "-") for t in tickers]
    
    return tickers
