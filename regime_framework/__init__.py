"""
Market Regime Framework
=======================

Multi-signal market regime detection and backtesting framework.

Three independent signals — price trend, volatility term structure, and
credit spreads — are combined to classify each trading day as Risk ON (1),
Cautious (2), or Risk OFF (0). Position sizing and rebalancing frequency
are fully configurable via StrategyConfig.

Public API
----------
Configuration
    StrategyConfig

Data
    download_data
    get_historical_data

Regime detection
    calculate_regimes

Signal generation
    generate_signals

Backtest and metrics
    run_backtest
    run_benchmark
    calculate_metrics

Plotting
    plot_results
    plot_spy
    plot_vix
"""

from .config   import StrategyConfig
from .data     import download_data, get_historical_data
from .regimes  import calculate_regimes
from .signals  import generate_signals
from .backtest import run_backtest, run_benchmark, calculate_metrics
from .plotting import (
    plot_results,
    plot_spy,
    plot_vix,
    plot_returns_with_regime,
    plot_returns_and_drawdown,
    plot_monthly_heatmap,
)

__all__ = [
    "StrategyConfig",
    "download_data",
    "get_historical_data",
    "calculate_regimes",
    "generate_signals",
    "run_backtest",
    "run_benchmark",
    "calculate_metrics",
    "plot_results",
    "plot_spy",
    "plot_vix",
    "plot_returns_with_regime",
    "plot_returns_and_drawdown",
    "plot_monthly_heatmap",
]