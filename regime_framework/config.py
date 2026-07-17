# ==============================================================================
# CONFIGURATION
# ==============================================================================
# All strategy parameters live here. Edit this file before running.
# No hardcoded values exist anywhere else in the codebase.


class StrategyConfig:
    """
    Central configuration for all strategy parameters.

    Backtest period
    ---------------
    START_DATE, END_DATE : 'YYYY-MM-DD' strings

    Regime detection
    ----------------
    REGIME_TREND_LOOKBACK    : SMA window for the trend signal (days)
    REGIME_VIX_THREASHOLD    : VIX/VIX3M ratio threshold; below = contango = Risk ON
    REGIME_CREDIT_LOOKBACK   : Rolling window for the HYG/IEF Z-score (days)
    REGIME_CREDIT_Z          : Z-score magnitude threshold (symmetric, applied as -Z)
    REGIME_DETECTION_TICKERS : Tickers used to build the three regime signals

    Trading universe
    ----------------
    TRADING_UNIVERSE : list of tickers to trade (currently single-asset)
    BENCHMARK_TICKER : ticker used as the buy-and-hold benchmark

    Cash management
    ---------------
    US_TREASURY_FOR_CASH : if True, idle cash earns the 3-month T-bill rate
                           loaded from DGS3MO.csv (FRED format)

    Position sizing
    ---------------
    POSITION_SIZE_RISK_OFF : fraction of portfolio invested in Risk OFF regime
    POSITION_SIZE_CAUTIONS : fraction of portfolio invested in Cautious regime
    POSITION_SIZE_RISK_ON  : fraction of portfolio invested in Risk ON regime
    POSITION_SIZE_BH       : fraction invested in the buy-and-hold benchmark

    Rebalancing
    -----------
    WEEKLY_ROTATION : if True, rebalance only on Mondays using the prior
                      Friday regime signal; if False, rebalance daily

    Portfolio
    ---------
    INITIAL_CAPITAL : starting capital in USD

    Output
    ------
    OUTPUT_DIR : directory where charts and CSV exports are saved
    """

    # Backtest period
    START_DATE = "2024-03-16"
    END_DATE   = "2026-07-15"

    # Regime detection
    REGIME_TREND_LOOKBACK    = 200
    REGIME_VIX_THREASHOLD    = 1
    REGIME_CREDIT_LOOKBACK   = 100
    REGIME_CREDIT_Z          = 2
    REGIME_DETECTION_TICKERS = ["^VIX", "^VIX3M", "^GSPC", "HYG", "IEF"]

    # Trading universe and benchmark
    TRADING_UNIVERSE = ["SPY"]
    BENCHMARK_TICKER = "SPY"

    # Cash management
    US_TREASURY_FOR_CASH = False

    # Position sizing
    POSITION_SIZE_RISK_OFF = 0.0
    POSITION_SIZE_CAUTIONS = 0.5
    POSITION_SIZE_RISK_ON  = 1.0
    POSITION_SIZE_BH       = 1.0

    # Rebalancing frequency
    WEEKLY_ROTATION = False

    # Portfolio
    INITIAL_CAPITAL = 100_000

    # Output
    OUTPUT_DIR = "."
