# Market Regime Framework

A multi-signal market regime detection and backtesting framework that classifies the market into Risk ON, Risk OFF, and Cautious states, then sizes a SPY position accordingly and evaluates performance against a buy-and-hold benchmark.

---

## Motivation

Rather than timing the market with price signals alone, this framework combines three independent indicators drawn from different parts of the market — trend, volatility term structure, and credit spreads — to classify the current regime. The intuition is that genuine risk-off environments show up simultaneously in all three: price breaks below its long-term trend, the volatility curve inverts (fear is short-dated), and credit spreads widen. When all three agree, the signal is high-conviction. When they partially agree, the framework takes a reduced position rather than going fully in or out.

---

## Framework Overview

The analysis proceeds in five stages:

| Stage | Module | Description |
|-------|--------|-------------|
| **Data download** | `data.py` | SPY OHLCV + VIX, VIX3M, SPX, HYG, IEF from Yahoo Finance |
| **Regime detection** | `regimes.py` | Three signals combined into Regime 0 / 1 / 2 |
| **Signal generation** | `signals.py` | Daily regime → daily or weekly rebalancing position |
| **Backtest** | `backtest.py` | Share-level portfolio simulation + benchmark |
| **Visualisation** | `plotting.py` | 6-panel dashboard, SPY chart, VIX chart |

---

## The Three Regime Signals

All thresholds are configurable in `StrategyConfig`.

### Signal 1 — Trend (SPX vs SMA)
```
Risk ON  : SPX > SMA(REGIME_TREND_LOOKBACK)
Risk OFF : SPX < SMA(REGIME_TREND_LOOKBACK)
```
Default lookback: 200 days.

### Signal 2 — Volatility Term Structure (VIX / VIX3M)
```
Risk ON  : VIX / VIX3M < REGIME_VIX_THREASHOLD   (contango)
Risk OFF : VIX / VIX3M >= REGIME_VIX_THREASHOLD   (backwardation)
```
Default threshold: 1. A ratio below 1 means the vol surface is in contango — a calm, risk-on configuration. Above 1 means near-term fear exceeds medium-term — a stress signal.

### Signal 3 — Credit Spread Proxy (HYG / IEF Z-Score)
```
Risk ON  : Z-Score > -REGIME_CREDIT_Z
Risk OFF : Z-Score <= -REGIME_CREDIT_Z
```
Default Z threshold: 2 (i.e. Risk OFF when Z < −2). The Z-score is computed on a rolling window of `REGIME_CREDIT_LOOKBACK` days (default 100). A Z-score below −2 signals genuine credit stress.

---

## Regime Classification

| Regime | Label | Signal 1 | Signal 2 | Signal 3 | Position |
|--------|-------|----------|----------|----------|----------|
| 1 | Risk ON | ON | ON | ON | `POSITION_SIZE_RISK_ON` |
| 2 | Cautious | Two of three ON | — | — | `POSITION_SIZE_CAUTIONS` |
| 0 | Risk OFF | All others | — | — | `POSITION_SIZE_RISK_OFF` |

---

## Signal Generation and Rebalancing

Controlled by `WEEKLY_ROTATION` in `StrategyConfig`:

**Daily mode (`WEEKLY_ROTATION = False`)**
Position changes every day the regime changes, with a one-day lag (no lookahead). Higher turnover but faster reaction.

**Weekly mode (`WEEKLY_ROTATION = True`)**
The last trading day of each week determines the target position. That position takes effect the following Monday. Lower turnover, consistent with the slow-moving nature of the three signals.

---

## Backtest Design

- **Initial capital**: configurable via `INITIAL_CAPITAL` (default $100,000)
- **Instrument**: first ticker in `TRADING_UNIVERSE` (default SPY)
- **Execution price**: next day's Close after a position change signal
- **Position sizing**: integer shares, cash-constrained
- **Cash return**: optional — set `US_TREASURY_FOR_CASH = True` to earn the 3-month T-bill rate on idle cash. Requires `DGS3MO.csv` downloaded from FRED.

**No transaction costs or slippage are modelled.**

---

## Performance Metrics

| Metric | Description |
|--------|-------------|
| Total Return | Cumulative return over the full period |
| Annual Return | CAGR |
| Volatility | Annualised standard deviation of daily returns |
| Sharpe Ratio | (Annual return − risk-free rate) / annualised vol |
| Sortino Ratio | (Annual return − risk-free rate) / downside deviation |
| Max Drawdown | Worst peak-to-trough decline |
| Calmar Ratio | Annual return / abs(max drawdown) |
| Win Rate | Fraction of days with positive returns |
| Alpha | Strategy annual return minus benchmark annual return |

Risk-free rate defaults to 2% and is subtracted in both Sharpe and Sortino. All metrics computed for both strategy and benchmark.

---

## Installation

```bash
git clone https://github.com/fbaru-dev/regime-framework.git
cd regime-framework
pip install -r requirements.txt
```

---

## Quick Start

```bash
python run_analysis.py
```

All parameters are in `regime_framework/config.py`. Edit `StrategyConfig` before running.

---

## Usage as a Library

```python
from regime_framework.config import StrategyConfig
from regime_framework import (
    download_data, get_historical_data,
    calculate_regimes, generate_signals,
    run_backtest, run_benchmark, calculate_metrics,
    plot_results,
)

config = StrategyConfig()
config.START_DATE       = "2010-01-01"
config.END_DATE         = "2024-01-01"
config.WEEKLY_ROTATION  = True
config.INITIAL_CAPITAL  = 50_000

regime_data  = download_data(config.REGIME_DETECTION_TICKERS,
                              config.START_DATE, config.END_DATE)
trading_data = get_historical_data(config.TRADING_UNIVERSE[0],
                                   config.START_DATE, config.END_DATE)

regime  = calculate_regimes(regime_data,
                             config.REGIME_TREND_LOOKBACK,
                             config.REGIME_VIX_THREASHOLD,
                             config.REGIME_CREDIT_LOOKBACK,
                             config.REGIME_CREDIT_Z)
signals = generate_signals(regime, config)

start = signals.index.min()
trading_data = trading_data[trading_data.index >= start]

backtest  = run_backtest(signals, trading_data, config)
benchmark = run_benchmark(trading_data, config)
metrics   = calculate_metrics(backtest["Strategy_Returns"], benchmark["Returns"])
plot_results(backtest, benchmark, signals, metrics, config)
```

---

## Output Files

Saved to `OUTPUT_DIR` (default: current directory).

| Filename | Format | Description |
|----------|--------|-------------|
| `regime_strategy_performance.png` | PNG 300 dpi | 6-panel performance dashboard |
| `spy.png` | PNG 300 dpi | SPY price with SMA overlay |
| `vix.png` | PNG 300 dpi | VIX vs VIX3M time series |
| `regime_strategy_results.csv` | CSV | Full daily backtest data |
| `regime_strategy_metrics.csv` | CSV | Performance metrics table |

---

## Project Structure

```
regime-framework/
├── README.md
├── requirements.txt
├── run_analysis.py               # Entry point — 6-step pipeline
└── regime_framework/
    ├── __init__.py               # Public API exports
    ├── config.py                 # StrategyConfig class — all parameters
    ├── data.py                   # Yahoo Finance downloads
    ├── regimes.py                # Three-signal regime classification
    ├── signals.py                # Daily / weekly position generation
    ├── backtest.py               # Portfolio simulation and metrics
    └── plotting.py               # All matplotlib visualisations
```

---

## Configuration Reference

```python
class StrategyConfig:
    # Period
    START_DATE = "2024-03-16"
    END_DATE   = "2026-07-15"

    # Regime thresholds
    REGIME_TREND_LOOKBACK    = 200   # SMA window (days)
    REGIME_VIX_THREASHOLD    = 1     # VIX/VIX3M contango boundary
    REGIME_CREDIT_LOOKBACK   = 100   # Z-score rolling window (days)
    REGIME_CREDIT_Z          = 2     # Z-score magnitude (applied as -Z)

    # Tickers
    REGIME_DETECTION_TICKERS = ["^VIX", "^VIX3M", "^GSPC", "HYG", "IEF"]
    TRADING_UNIVERSE         = ["SPY"]
    BENCHMARK_TICKER         = "SPY"

    # Cash management
    US_TREASURY_FOR_CASH = False   # True requires DGS3MO.csv from FRED

    # Position sizing
    POSITION_SIZE_RISK_OFF = 0.0
    POSITION_SIZE_CAUTIONS = 0.5
    POSITION_SIZE_RISK_ON  = 1.0
    POSITION_SIZE_BH       = 1.0   # benchmark fraction (display only)

    # Rebalancing
    WEEKLY_ROTATION = False   # False = daily, True = weekly

    # Portfolio
    INITIAL_CAPITAL = 100_000

    # Output
    OUTPUT_DIR = "."
```

---

## Design Notes

### StrategyConfig as a class
Using a class rather than flat module-level variables allows subclassing for parameter sweeps:
```python
class BearMarketConfig(StrategyConfig):
    START_DATE = "2007-04-12"
    END_DATE   = "2009-12-31"
```

### Why parameterise the regime thresholds?
The original code hardcoded `1` and `−2` inside `calculate_regimes()`. Making them configurable via `StrategyConfig` means you can run sensitivity analyses across threshold values without touching the algorithm.

### Sharpe and Sortino with risk-free rate
The previous version used no risk-free rate. The updated version defaults to 2%, making the Sharpe and Sortino ratios more meaningful for comparison against published benchmarks.

### US_TREASURY_FOR_CASH
When `True`, idle cash earns the prevailing 3-month T-bill rate (loaded from FRED's `DGS3MO.csv`). This makes a material difference in long backtests where the strategy spends significant time out of the market during high-rate environments (e.g. 2022–2023).

---

## Known Limitations

- **No transaction costs or slippage**: real execution would reduce returns, particularly with daily rebalancing.
- **Lookback initialisation**: SMA(200) requires 200 days and the credit Z-score requires 100 days. The first ~200 trading days of any dataset are excluded.
- **Single instrument**: the backtest only trades one ticker. The regime signal could be applied to a multi-asset portfolio.
- **DGS3MO.csv required**: `US_TREASURY_FOR_CASH = True` depends on a local CSV file from FRED. Download from: https://fred.stlouisfed.org/series/DGS3MO

---

## Dependencies

- `numpy`
- `pandas`
- `matplotlib`
- `seaborn`
- `yfinance`

---

## License

MIT
