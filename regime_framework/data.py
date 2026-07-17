"""
Data download from Yahoo Finance.

Two loaders serve different purposes:

  download_data()       -- multi-ticker download for VIX, VIX3M, SPX, HYG, IEF.
                           Returns daily closing prices used by calculate_regimes().

  get_historical_data() -- single-ticker OHLCV download for the trading instrument.
                           Returns full OHLCV including unadjusted Close used as the
                           execution price in run_backtest().
"""

import pandas as pd
import yfinance as yf


def download_data(tickers: list, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Download daily closing prices for regime signal construction.

    Parameters
    ----------
    tickers    : list of Yahoo Finance ticker strings
                 (default: ["^VIX", "^VIX3M", "^GSPC", "HYG", "IEF"])
    start_date : 'YYYY-MM-DD' (inclusive)
    end_date   : 'YYYY-MM-DD' (exclusive in yfinance convention)

    Returns
    -------
    pd.DataFrame with tz-naive DatetimeIndex and columns:
        SPX, VIX, VIX3M, HYG, IEF
    Rows with any NaN dropped.
    """
    data = yf.download(tickers, start=start_date, end=end_date,
                       auto_adjust=False, progress=False)
    data.index = data.index.tz_localize(None)

    if isinstance(data.columns, pd.MultiIndex):
        close = (data["Adj Close"]
                 if "Adj Close" in data.columns.levels[0]
                 else data["Close"])
    else:
        close = data

    mapping = {
        "^GSPC": "SPX",
        "^VIX":  "VIX",
        "^VIX3M": "VIX3M",
        "HYG":   "HYG",
        "IEF":   "IEF",
    }
    close = close.rename(columns=mapping)

    df = close[["SPX", "VIX", "VIX3M", "HYG", "IEF"]].dropna().sort_index()

    df = df.reset_index()
    df["Date"] = pd.to_datetime(df["Date"])
    df.set_index("Date", inplace=True)

    return df


def get_historical_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Download SPY (or any ticker) OHLCV data for use in the backtest.

    Uses Ticker.history() with auto_adjust=False to preserve the unadjusted
    Close price, which is the execution price in run_backtest().

    Parameters
    ----------
    ticker     : Yahoo Finance ticker string (e.g. 'SPY')
    start_date : 'YYYY-MM-DD' (inclusive)
    end_date   : 'YYYY-MM-DD' (exclusive in yfinance convention)

    Returns
    -------
    pd.DataFrame with tz-naive DatetimeIndex and standard OHLCV columns.
    """
    t  = yf.Ticker(ticker)
    df = t.history(start=start_date, end=end_date,
                   interval="1d", auto_adjust=False)
    df.index = df.index.tz_localize(None)

    print(f"Downloaded {len(df)} data points for {ticker} "
          f"from {df.index[0].date()} to {df.index[-1].date()}")
    return df
