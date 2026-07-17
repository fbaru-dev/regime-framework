"""
Market regime detection and backtesting pipeline.

Edit regime_framework/config.py to change all parameters.
Run with:  python run_analysis.py
"""

import datetime
import os

import pandas as pd

from regime_framework.config import StrategyConfig
from regime_framework import (
    download_data,
    get_historical_data,
    calculate_regimes,
    generate_signals,
    run_backtest,
    run_benchmark,
    calculate_metrics,
    plot_results,
    plot_spy,
    plot_vix,
)


def main():
    config = StrategyConfig()

    # ── HEADER ────────────────────────────────────────────────────────────────
    print("=" * 70)
    print("REGIME-BASED TRADING STRATEGY - PRODUCTION BACKTEST")
    print("=" * 70)
    print("\nConfiguration:")
    print(f"  Period         : {config.START_DATE} to {config.END_DATE}")
    print(f"  Initial Capital: ${config.INITIAL_CAPITAL:,.0f}")
    print(f"  Position Sizes : Risk ON={config.POSITION_SIZE_RISK_ON:.0%}  "
          f"Cautious={config.POSITION_SIZE_CAUTIONS:.0%}  "
          f"Risk OFF={config.POSITION_SIZE_RISK_OFF:.0%}")
    print(f"  Weekly Rotation: {config.WEEKLY_ROTATION}")
    print(f"  T-Bill Cash    : {config.US_TREASURY_FOR_CASH}")
    print(f"  Benchmark      : {config.BENCHMARK_TICKER}")

    # ── STEP 1: DATA ──────────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print("STEP 1: DATA ACQUISITION")
    print("=" * 70)

    print(f"\nFetching {config.REGIME_DETECTION_TICKERS} for regime detection...")
    regime_data = download_data(config.REGIME_DETECTION_TICKERS,
                                config.START_DATE, config.END_DATE)

    print(f"\nFetching {config.TRADING_UNIVERSE[0]} for trading...")
    trading_data = get_historical_data(config.TRADING_UNIVERSE[0],
                                       config.START_DATE, config.END_DATE)

    print(f"\nFetching {config.BENCHMARK_TICKER} for benchmark...")
    benchmark_data = get_historical_data(config.BENCHMARK_TICKER,
                                         config.START_DATE, config.END_DATE)

    # ── STEP 2: REGIME DETECTION ──────────────────────────────────────────────
    print(f"\n{'='*70}")
    print("STEP 2: REGIME DETECTION")
    print("=" * 70)

    regime = calculate_regimes(
        regime_data,
        regime_trend_lookback  = config.REGIME_TREND_LOOKBACK,
        regime_vix_threashold  = config.REGIME_VIX_THREASHOLD,
        regime_credit_lookback = config.REGIME_CREDIT_LOOKBACK,
        regime_credit_z        = config.REGIME_CREDIT_Z,
    )

    regime_stats = regime.groupby("Regime")[["Signal_1", "Signal_2", "Signal_3"]].agg(["count"])
    print("\nRegime Statistics:")
    print(regime_stats)

    # ── STEP 3: SIGNAL GENERATION ─────────────────────────────────────────────
    print(f"\n{'='*70}")
    print("STEP 3: SIGNAL GENERATION")
    print("=" * 70)

    signals = generate_signals(regime, config)

    position_changes = signals[signals["PositionChange"] == 1]["PositionChange"].count()
    print(f"\nTotal Position Changes : {position_changes}")
    print(f"Average Holding Period : {len(signals) / max(position_changes, 1):.1f} days")

    # ── STEP 4: BACKTEST ──────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print("STEP 4: BACKTESTING")
    print("=" * 70)

    start_date     = signals.index.min()
    trading_data   = trading_data[trading_data.index >= start_date]
    benchmark_data = benchmark_data[benchmark_data.index >= start_date]

    print("\nRunning strategy backtest...")
    backtest_results = run_backtest(signals, trading_data, config)

    print("Running benchmark backtest...")
    benchmark_results = run_benchmark(benchmark_data, config)

    # ── STEP 5: PERFORMANCE ANALYSIS ─────────────────────────────────────────
    print(f"\n{'='*70}")
    print("STEP 5: PERFORMANCE ANALYSIS")
    print("=" * 70)

    metrics = calculate_metrics(
        backtest_results["Strategy_Returns"],
        benchmark_results["Returns"],
    )

    print(f"\n{'Metric':<25} {'Strategy':>15} {'Benchmark':>15}")
    print("-" * 70)
    print(f"{'Total Return':<25} {metrics['Total Return']:>14.2%} {metrics['Benchmark Return']:>14.2%}")
    print(f"{'Annual Return':<25} {metrics['Annual Return']:>14.2%} {metrics['Benchmark Annual Return']:>14.2%}")
    print(f"{'Volatility':<25} {metrics['Volatility']:>14.2%} {metrics['Benchmark Volatility']:>14.2%}")
    print(f"{'Sharpe Ratio':<25} {metrics['Sharpe Ratio']:>14.2f} {metrics['Benchmark Sharpe']:>14.2f}")
    print(f"{'Sortino Ratio':<25} {metrics['Sortino Ratio']:>14.2f} {'N/A':>15}")
    print(f"{'Max Drawdown':<25} {metrics['Max Drawdown']:>14.2%} {metrics['Benchmark Max DD']:>14.2%}")
    print(f"{'Calmar Ratio':<25} {metrics['Calmar Ratio']:>14.2f} {metrics['Benchmark Calmar']:>14.2f}")
    print(f"{'Win Rate':<25} {metrics['Win Rate']:>14.2%} {'N/A':>15}")
    print(f"{'Alpha':<25} {metrics['Alpha']:>14.2%} {'N/A':>15}")
    print("-" * 70)

    # ── STEP 6: VISUALISATION ─────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print("STEP 6: VISUALIZATION")
    print("=" * 70)

    plot_results(
        backtest_results, benchmark_results, signals, metrics, config,
        save_path=config.OUTPUT_DIR,
        filename="regime_strategy_performance",
    )

    # SPY + SMA200 chart (from 2019 onward for readability)
    benchmark_data["SMA200"] = benchmark_data["Close"].rolling(200).mean()
    start_spy = datetime.datetime(2019, 1, 1)
    spy_plot_data = benchmark_data[benchmark_data.index >= start_spy]
    plot_spy(spy_plot_data, save_path=config.OUTPUT_DIR, filename="spy")

    # VIX vs VIX3M chart (from 2019 onward)
    vix_data  = regime_data["VIX"][regime_data.index  >= start_spy]
    vix3m_data = regime_data["VIX3M"][regime_data.index >= start_spy]
    plot_vix(vix_data, vix3m_data, save_path=config.OUTPUT_DIR, filename="vix")

    # ── EXPORT ────────────────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print("EXPORTING RESULTS")
    print("=" * 70)

    export_df = backtest_results[[
        "Close", "PositionChange", "TargetPosition", "CurrentPosition",
        "CurrentCash", "CurrentHoldings", "CurrentPortfolio", "Shares",
        "Strategy_Returns", "Cumulative_Returns",
    ]].copy()
    export_df["Regime"]            = signals["Regime"]
    export_df["Benchmark_Returns"] = benchmark_results["Returns"]

    results_path = os.path.join(config.OUTPUT_DIR, "regime_strategy_results.csv")
    export_df.to_csv(results_path)
    print(f"Results exported to '{results_path}'")

    metrics_df = pd.DataFrame([metrics]).T
    metrics_df.columns = ["Value"]
    metrics_path = os.path.join(config.OUTPUT_DIR, "regime_strategy_metrics.csv")
    metrics_df.to_csv(metrics_path)
    print(f"Metrics exported to '{metrics_path}'")

    print(f"\n{'='*70}")
    print("BACKTEST COMPLETED SUCCESSFULLY")
    print("=" * 70)

if __name__ == "__main__":
    main()
