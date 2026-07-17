"""
Portfolio simulation and performance metrics.

run_backtest()        : regime-driven strategy on a single instrument
run_benchmark()       : buy-and-hold with the same initial capital
calculate_metrics()   : comprehensive performance statistics
"""

import numpy as np
import pandas as pd


def run_backtest(signals: pd.DataFrame, prices_df: pd.DataFrame, config) -> pd.DataFrame:
    """
    Simulate the regime-driven strategy.

    Execution rules:
      - Trades execute at the next day's Close after a rebalancing signal.
      - Rebalancing trigger depends on config.WEEKLY_ROTATION:
          True  -> trades on Mondays (WeeklyChange == 1)
          False -> trades whenever PositionChange == 1
      - Shares are bought/sold as integers (no fractional shares).
      - No transaction costs or slippage modelled.

    Optional cash return:
      If config.US_TREASURY_FOR_CASH is True, idle cash earns the daily
      3-month T-bill rate loaded from DGS3MO.csv (FRED format, column
      'DGS3MO', index 'observation_date'). Rate is divided by 360 to
      produce a daily accrual and forward-filled for missing dates.

    Parameters
    ----------
    signals   : output of generate_signals()
    prices_df : OHLCV DataFrame from get_historical_data()
    config    : StrategyConfig instance

    Returns
    -------
    pd.DataFrame with columns including:
        Close, PositionChange, TargetPosition, CurrentPosition,
        CurrentCash, CurrentHoldings, CurrentPortfolio, Shares,
        Returns, Strategy_Returns, Cumulative_Returns
        CashInterest (if US_TREASURY_FOR_CASH)
    """
    bt = pd.DataFrame(index=prices_df.index)
    bt["Close"]          = prices_df["Close"].values
    bt["PositionChange"] = signals["WeeklyChange"]

    if config.WEEKLY_ROTATION:
        bt["TargetPosition"] = signals["WeeklySignal"]
    else:
        bt["TargetPosition"] = signals["TargetPosition"]

    bt["CurrentPosition"]  = 0.0
    bt["CurrentCash"]      = float(config.INITIAL_CAPITAL)
    bt["CurrentHoldings"]  = 0.0
    bt["CurrentPortfolio"] = float(config.INITIAL_CAPITAL)
    bt["Shares"]           = 0.0

    # T-bill cash interest (optional)
    if config.US_TREASURY_FOR_CASH:
        bt["CashInterest"] = 0.0
        start_date = bt.index.min()
        t_bill = pd.read_csv("DGS3MO.csv", parse_dates=["observation_date"])
        t_bill = t_bill.rename(columns={"observation_date": "Date"})
        t_bill = t_bill.set_index("Date")
        t_bill = t_bill[t_bill.index >= start_date]
        t_bill["TBill"] = t_bill["DGS3MO"].reindex(bt.index)
        t_bill["TBill"] = t_bill["TBill"] / (100 * 360)
        t_bill = t_bill.ffill()

    bt.dropna(inplace=True)

    for i in range(1, len(bt)):
        curr_idx = bt.index[i]
        prev_idx = bt.index[i - 1]

        bt.loc[curr_idx, "CurrentPosition"] = bt.loc[prev_idx, "CurrentPosition"]
        bt.loc[curr_idx, "CurrentCash"]     = bt.loc[prev_idx, "CurrentCash"]
        bt.loc[curr_idx, "Shares"]          = bt.loc[prev_idx, "Shares"]

        target_position  = bt.loc[curr_idx, "TargetPosition"]
        current_position = bt.loc[prev_idx, "CurrentPosition"]

        if bt.loc[prev_idx, "PositionChange"] == 1:
            if target_position != 0:
                execution_price = bt.loc[curr_idx, "Close"]
                portfolio_value = bt.loc[prev_idx, "CurrentPortfolio"]
                holding_value   = bt.loc[prev_idx, "CurrentHoldings"]
                cash_value      = bt.loc[prev_idx, "CurrentCash"]

                trade = target_position - current_position

                if trade > 0:  # Buying
                    if holding_value == 0:
                        trade_value = cash_value * trade
                    else:
                        trade_value = min(trade * portfolio_value, cash_value)
                    bt.loc[curr_idx, "trade_value"] = trade_value

                    shares_to_buy = int(trade_value / execution_price)
                    bt.loc[curr_idx, "Shares"]       += shares_to_buy
                    bt.loc[curr_idx, "SharesChange"]  = shares_to_buy
                    position_value = shares_to_buy * execution_price
                    bt.loc[curr_idx, "CurrentCash"]  -= position_value

                else:  # Selling
                    trade_value = min(trade * holding_value, cash_value)
                    bt.loc[curr_idx, "trade_value"] = trade_value

                    shares_to_sell = -int(trade_value / execution_price)
                    bt.loc[curr_idx, "Shares"]       -= shares_to_sell
                    bt.loc[curr_idx, "SharesChange"]  = shares_to_sell
                    position_value = shares_to_sell * execution_price
                    bt.loc[curr_idx, "CurrentCash"]  += position_value

                bt.loc[curr_idx, "CurrentPosition"] = target_position

            else:  # Full exit
                execution_price     = bt.loc[curr_idx, "Close"]
                shares_to_liquidate = bt.loc[curr_idx, "Shares"]
                trade_value         = shares_to_liquidate * execution_price
                bt.loc[curr_idx, "trade_value"]   = trade_value
                bt.loc[curr_idx, "Shares"]        -= shares_to_liquidate
                bt.loc[curr_idx, "SharesChange"]   = shares_to_liquidate
                bt.loc[curr_idx, "CurrentCash"]   += trade_value

            bt.loc[curr_idx, "CurrentPosition"] = target_position

        # Cash interest accrual
        if config.US_TREASURY_FOR_CASH:
            bt.loc[curr_idx, "Tbill_Rate"]   = np.where(
                bt.loc[curr_idx, "CurrentCash"] > 0,
                t_bill.loc[curr_idx, "TBill"], 0,
            )
            bt.loc[curr_idx, "CashInterest"] = (
                bt.loc[curr_idx, "CurrentCash"] * bt.loc[curr_idx, "Tbill_Rate"]
                + bt.loc[prev_idx, "CashInterest"]
            )

        bt.loc[curr_idx, "CurrentHoldings"]  = (
            bt.loc[curr_idx, "Shares"] * bt.loc[curr_idx, "Close"]
        )
        bt.loc[curr_idx, "CurrentPortfolio"] = (
            bt.loc[curr_idx, "CurrentCash"] + bt.loc[curr_idx, "CurrentHoldings"]
        )

    bt["Returns"]            = bt["Close"].pct_change()
    bt["Strategy_Returns"]   = bt["CurrentPortfolio"].pct_change()
    bt["Cumulative_Returns"] = (1 + bt["Strategy_Returns"]).cumprod()

    return bt


def run_benchmark(prices_df: pd.DataFrame, config) -> pd.DataFrame:
    """
    Simulate a buy-and-hold strategy with config.INITIAL_CAPITAL.

    Parameters
    ----------
    prices_df : OHLCV DataFrame from get_historical_data()
    config    : StrategyConfig instance

    Returns
    -------
    pd.DataFrame with columns:
        Close, Portfolio_Value, Returns, Cumulative_Returns
    """
    bench = pd.DataFrame(index=prices_df.index)
    bench["Close"] = prices_df["Close"]

    initial_shares          = config.INITIAL_CAPITAL / bench["Close"].iloc[0]
    bench["Portfolio_Value"]    = initial_shares * bench["Close"]
    bench["Returns"]            = bench["Portfolio_Value"].pct_change()
    bench["Cumulative_Returns"] = (1 + bench["Returns"]).cumprod()

    return bench


def calculate_metrics(
    returns_series: pd.Series,
    benchmark_returns: pd.Series,
    risk_free_rate: float = 0.02,
) -> dict:
    """
    Compute comprehensive performance metrics for strategy and benchmark.

    Parameters
    ----------
    returns_series    : daily strategy returns
    benchmark_returns : daily benchmark returns
    risk_free_rate    : annual risk-free rate used in Sharpe and Sortino
                        (default 2%)

    Returns
    -------
    dict with keys:
        Total Return, Annual Return, Volatility,
        Sharpe Ratio, Sortino Ratio, Max Drawdown, Calmar Ratio,
        Win Rate, Avg Win, Avg Loss,
        Benchmark Return, Benchmark Annual Return, Benchmark Volatility,
        Benchmark Sharpe, Benchmark Max DD, Benchmark Calmar,
        Alpha
    """
    returns       = returns_series.dropna()
    bench_returns = benchmark_returns.dropna()
    ann_factor    = 252

    total_return     = (1 + returns).prod() - 1
    benchmark_total  = (1 + bench_returns).prod() - 1

    n_years          = len(returns) / ann_factor
    ann_return       = (1 + total_return) ** (1 / n_years) - 1
    bench_ann_return = (1 + benchmark_total) ** (1 / n_years) - 1

    volatility       = returns.std() * np.sqrt(ann_factor)
    bench_volatility = bench_returns.std() * np.sqrt(ann_factor)

    excess_return = ann_return - risk_free_rate
    sharpe        = excess_return / volatility if volatility > 0 else 0

    bench_excess  = bench_ann_return - risk_free_rate
    bench_sharpe  = bench_excess / bench_volatility if bench_volatility > 0 else 0

    cum_returns  = (1 + returns).cumprod()
    running_max  = cum_returns.expanding().max()
    max_dd       = ((cum_returns - running_max) / running_max).min()

    bench_cum    = (1 + bench_returns).cumprod()
    bench_max    = bench_cum.expanding().max()
    bench_max_dd = ((bench_cum - bench_max) / bench_max).min()

    calmar       = ann_return / abs(max_dd)       if max_dd != 0       else 0
    bench_calmar = bench_ann_return / abs(bench_max_dd) if bench_max_dd != 0 else 0

    win_rate  = (returns > 0).sum() / len(returns)
    wins      = returns[returns > 0]
    losses    = returns[returns < 0]
    avg_win   = wins.mean()   if len(wins)   > 0 else 0
    avg_loss  = losses.mean() if len(losses) > 0 else 0

    downside_returns = returns[returns < 0]
    downside_std     = downside_returns.std() * np.sqrt(ann_factor)
    sortino          = excess_return / downside_std if downside_std > 0 else 0

    return {
        "Total Return":           total_return,
        "Annual Return":          ann_return,
        "Volatility":             volatility,
        "Sharpe Ratio":           sharpe,
        "Sortino Ratio":          sortino,
        "Max Drawdown":           max_dd,
        "Calmar Ratio":           calmar,
        "Win Rate":               win_rate,
        "Avg Win":                avg_win,
        "Avg Loss":               avg_loss,
        "Benchmark Return":       benchmark_total,
        "Benchmark Annual Return": bench_ann_return,
        "Benchmark Volatility":   bench_volatility,
        "Benchmark Sharpe":       bench_sharpe,
        "Benchmark Max DD":       bench_max_dd,
        "Benchmark Calmar":       bench_calmar,
        "Alpha":                  ann_return - bench_ann_return,
    }
