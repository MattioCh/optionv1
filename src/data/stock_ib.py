# %%
from datetime import datetime, timedelta, timezone
import pytz
import threading, time

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.client import BarData
from ibapi.utils import iswrapper

import pandas as pd


class IB(EClient, EWrapper):

    def __init__(self):
        EClient.__init__(self, self)
        self.data = []

    @iswrapper
    def error(self, reqId, code, msg):
        """Logging Error"""
        print(f"Error {reqId}, code: {code}, message: {msg}")

    @iswrapper
    def historicalData(self, reqId: int, bar: BarData) -> None:
        self.data.append([bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume])

    @iswrapper
    def historicalDataEnd(self, reqId: int, start: str, end: str):
        start_time = datetime.strptime(start, "%Y%m%d %H:%M:%S")
        end_time = datetime.strptime(end, "%Y%m%d %H:%M:%S")
        super().historicalDataEnd(reqId, start, end)
        print(
            "Historical data request with request ID: ",
            reqId,
            " for period between ",
            start_time,
            " and ",
            end_time,
            " is complete.",
        )


def get_stock_price(
    app: IB, symbol: str, exchange: str = "SMART", currency: str = "USD"
):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = "STK"
    contract.exchange = exchange
    contract.currency = currency

    app.data = []
    app.reqMarketDataType(1)  # Live data
    app.reqMktData(1001, contract, "", False, False, [])
    time.sleep(2)
    if app.data:
        return app.data[-1]  # Last received price data
    else:
        return None


def get_option_chain_historical_prices(
    app: IB,
    symbol: str,
    expiry: str,
    strike: float,
    right: str,
    exchange: str = "SMART",
    currency: str = "USD",
    endDateTime: str = "",
    durationStr: str = "1 D",
    barSizeSetting: str = "1 hour",
):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = "OPT"
    contract.exchange = exchange
    contract.currency = currency
    contract.lastTradeDateOrContractMonth = expiry  # Format: YYYYMMDD
    contract.strike = strike
    contract.right = right  # 'C' for Call, 'P' for Put

    app.data = []
    app.reqHistoricalData(
        reqId=2001,
        contract=contract,
        endDateTime=endDateTime,
        durationStr=durationStr,
        barSizeSetting=barSizeSetting,
        whatToShow="TRADES",
        useRTH=0,
        formatDate=1,
        keepUpToDate=False,
        chartOptions=[],
    )
    time.sleep(10)
    return pd.DataFrame(
        app.data, columns=["date", "open", "high", "low", "close", "volume"]
    )


def create_contract() -> Contract:
    ticker = Contract()
    ticker.symbol = "TQQQ"
    ticker.secType = "STK"
    ticker.exchange = "ARCA"
    ticker.currency = "USD"
    return ticker


def run_loop(app):
    app.run()


if __name__ == "__main__":
    app = IB()
    app.connect(host="localhost", port=4002, clientId=1)
    time.sleep(2)
    api_thread = threading.Thread(target=run_loop, args=(app,))
    api_thread.start()

    ticker = create_contract()

    eastern = pytz.timezone("US/Eastern")
    query_time = (
        datetime(2025, 3, 12, 9, 0, tzinfo=eastern).strftime("%Y%m%d %H:%M:%S")
        + " US/Eastern"
    )
    print(query_time)
    bars = app.reqHistoricalData(
        reqId=2,
        contract=ticker,
        endDateTime=query_time,
        durationStr="1 D",
        # barSizeSetting="30 secs",
        barSizeSetting="1 hour",
        whatToShow="TRADES",
        useRTH=0,
        formatDate=1,
        keepUpToDate=False,
        chartOptions=[],
    )
    time.sleep(10)
    for bar in app.data:
        print(bar)

    df = pd.DataFrame(app.data)
    df = df.set_axis(["date", "open", "high", "low", "close", "volume"], axis=1)
    print(df)
    print(df.describe())

    # Example: Get QQQ March option chain historical prices
    option_expiry = "20240315"  # March 15, 2024
    option_strike = 430.0  # Example strike price
    option_right = "C"  # 'C' for Call, 'P' for Put

    option_df = get_option_chain_historical_prices(
        app,
        symbol="QQQ",
        expiry=option_expiry,
        strike=option_strike,
        right=option_right,
        exchange="SMART",
        currency="USD",
        endDateTime=query_time,
        durationStr="1 D",
        barSizeSetting="1 hour",
    )

    print(option_df)
    app.disconnect()
