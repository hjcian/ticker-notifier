from datetime import datetime, timedelta
from typing import List

import yfinance as yf
from pandas import DataFrame
from pydantic import BaseModel


class Price(BaseModel):
    date: datetime
    price: float


def date_str(date: datetime) -> str:
    """
    取得當前日期的字串格式
    :return: 當前日期的字串格式
    """
    return date.strftime('%Y-%m-%d')


def get_closing_price(history: DataFrame, days_ago: int) -> Price:
    date = datetime.now().date() - timedelta(days=days_ago)

    # history.columns:
    # Index(['Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits',
    #    'Capital Gains'],
    #   dtype='object')

    while date_str(date) not in history.index:
        date -= timedelta(days=1)
        # 如果日期超出範圍，可以選擇拋出例外或返回 None
        if date < history.index.min().date():
            raise ValueError("無法找到有效的收盤價，日期超出範圍")

    closing_price = history.loc[date_str(date)]['Close']
    return Price(price=closing_price,
                 date=date)


class LookbackPriceChange(BaseModel):
    lookback_date: datetime
    lookback_period: int
    lookback_price: float
    current_price: float
    price_change_percent: float


class PriceChangeMessage(BaseModel):
    """
    價格變化的訊息
    """

    ticker: str
    lookback_price_changes: List[LookbackPriceChange]


if __name__ == '__main__':
    # Interesting ticker symbols
    ticker_symbols = [
        "VT"
    ]
    lookback_periods = [
        90,
        60,
        50,
        40,
        30,
        20,
        10,
    ]

    results: List[PriceChangeMessage] = []
    for ticker_symbol in ticker_symbols:
        ticker = yf.Ticker(ticker_symbol)
        today = datetime.now().date()
        enough_days_ago = today - timedelta(days=max(lookback_periods)+10)
        history = ticker.history(start=enough_days_ago,
                                 end=today + timedelta(days=1))
        current_price = get_closing_price(history, 0)

        change_message = PriceChangeMessage(
            ticker=ticker_symbol,
            lookback_price_changes=[]
        )
        for lookback_period in lookback_periods:
            # 取得從 60 天前到今天的歷史資料
            lookback_price = get_closing_price(history, lookback_period)
            change = LookbackPriceChange(
                lookback_date=lookback_price.date,
                lookback_period=lookback_period,
                lookback_price=lookback_price.price,
                current_price=current_price.price,
                price_change_percent=(
                    current_price.price - lookback_price.price) / lookback_price.price
            )
            change_message.lookback_price_changes.append(change)

        results.append(change_message)

    for result in results:
        print(f"Ticker: {result.ticker}")
        for change in result.lookback_price_changes:
            print(
                f"Lookback Period: {change.lookback_period} days ({change.lookback_date.date()})")
            print(f"Lookback Price: {change.lookback_price}")
            print(f"Current Price: {change.current_price}")
            print(f"Price Change Percent: {change.price_change_percent:.2%}")
            print("-" * 40)
