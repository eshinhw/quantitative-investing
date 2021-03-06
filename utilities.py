import smtplib
import credentials
import numpy as np
import pandas as pd
import datetime as dt
from typing import List
import pandas_datareader.data as web
from email.message import EmailMessage

START_DATE = dt.datetime(1970, 1, 1)
END_DATE = dt.datetime.today()

def get_daily_prices(symbol):
    return web.DataReader(symbol, "yahoo", START_DATE, END_DATE)

def calculate_prev_min_low(symbol: str, period: int):
    df = get_daily_prices(symbol)
    df["Low_" + str(period)] = df["Low"].shift(1).rolling(window=period).min()
    return df["Low_" + str(period)].iloc[-1]

def calculate_prev_max_high(symbol: str, period: int):
    df = get_daily_prices(symbol)
    df["High_" + str(period)] = df["High"].shift(1).rolling(window=period).max()
    return df["High_" + str(period)].iloc[-1]

def get_historical_monthly_prices(symbol: str):
    prices = get_daily_prices(symbol)
    prices.dropna(inplace=True)
    prices.reset_index(inplace=True)
    prices = prices[["Date", "Adj Close"]]
    prices["STD_YM"] = prices["Date"].map(lambda x: dt.datetime.strftime(x, "%Y-%m"))
    month_list = prices["STD_YM"].unique()
    monthly_prices = pd.DataFrame()
    for m in month_list:
        monthly_prices = monthly_prices.append(prices[prices["STD_YM"] == m].iloc[-1, :])
    monthly_prices = monthly_prices.drop(columns=["STD_YM"], axis=1)
    monthly_prices.set_index("Date", inplace=True)
    return monthly_prices[:-1]

def calculate_momentum(symbol: str, periods: List[int]):
    ret = []
    ret.append(symbol)
    monthly_prices = get_historical_monthly_prices(symbol)
    for period in periods:
        monthly_returns = monthly_prices.apply(lambda x: x / x.shift(period) - 1, axis=0)
        monthly_returns = monthly_returns.rename(columns={"Adj Close": "Returns"})
        mom = float(monthly_returns['Returns'][-1])
        if mom == np.nan:
            mom = float('-inf')
        print(mom)
        ret.append(mom)
    return ret

def sendEmail(subject, curr_pos, filters, watchlist):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = credentials.GMAIL_ADDRESS
    msg['To'] = credentials.GMAIL_ADDRESS
    # msg.set_content("hello?")

    msg.add_alternative(f"""\

        <!DOCTYPE html>
        <html>
            <body>
                <p> Hello Investors,<br> Below is the daily summary of your portfolio and updated stock watchlist.<br> Have a good evening :) </p>
                <h1> Portfolio Overview </h1>
                <h3> Investment Summary </h3>
                {curr_pos}
                <h1> Watchlist - S&P500 Discounted Stocks </h1>
                <h3> Conditional Filters </h3>
                {filters}
                <br>
                {watchlist}
            </body>
        </html>
    """, subtype='html')
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(credentials.GMAIL_ADDRESS, credentials.GMAIL_PW)
        smtp.send_message(msg)