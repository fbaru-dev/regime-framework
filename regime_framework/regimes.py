"""
Market regime classification from three independent signals.

Signal 1 -- Trend         : SPX vs SMA(REGIME_TREND_LOOKBACK)
Signal 2 -- Vol term str. : VIX / VIX3M vs REGIME_VIX_THREASHOLD
Signal 3 -- Credit stress : HYG/IEF ratio Z-Score vs -REGIME_CREDIT_Z

Regime 1 (Risk ON)  : all three signals are Risk ON
Regime 2 (Cautious) : exactly two of three signals are Risk ON
Regime 0 (Risk OFF) : one or zero signals are Risk ON
"""

import numpy as np
import pandas as pd


def calculate_regimes(
    data: pd.DataFrame,
    regime_trend_lookback: int,
    regime_vix_threashold: float,
    regime_credit_lookback: int,
    regime_credit_z: float,
) -> pd.DataFrame:
    """
    Classify each trading day into a market regime.

    All threshold parameters are read from StrategyConfig — no hardcoded values.

    Parameters
    ----------
    data                   : output of download_data()
    regime_trend_lookback  : SMA window for Signal 1 (e.g. 200)
    regime_vix_threashold  : VIX/VIX3M threshold for Signal 2 (e.g. 1)
    regime_credit_lookback : rolling window for the credit Z-score (e.g. 100)
    regime_credit_z        : Z-score magnitude; Risk ON when Z > -regime_credit_z

    Returns
    -------
    pd.DataFrame containing all original columns plus:
        SPX_SMA        : SMA of SPX over regime_trend_lookback days
        SPX_Dist_SMA   : SPX minus SMA
        Signal_1       : 1 if SPX > SMA, else 0
        TS             : VIX / VIX3M ratio
        Signal_2       : 1 if TS < regime_vix_threashold, else 0
        CREDIT_RATIO   : HYG / IEF
        CREDIT_ROLL_M  : rolling mean of credit ratio
        CREDIT_ROLL_STD: rolling std of credit ratio
        CREDIT_Z       : Z-score of credit ratio
        Signal_3       : 1 if CREDIT_Z > -regime_credit_z, else 0
        Regime         : 0 (Risk OFF), 1 (Risk ON), 2 (Cautious)

    Rows containing NaN (lookback initialisation period) are dropped.
    """
    regime = data.copy()

    # ------------------------------------------------------------------
    # Signal 1: trend
    # ------------------------------------------------------------------
    regime["SPX_SMA"]      = regime["SPX"].rolling(regime_trend_lookback).mean()
    regime["SPX_Dist_SMA"] = regime["SPX"] - regime["SPX_SMA"]
    regime["Signal_1"]     = np.where(regime["SPX_Dist_SMA"] > 0, 1, 0)

    # ------------------------------------------------------------------
    # Signal 2: volatility term structure
    # ------------------------------------------------------------------
    regime["TS"]       = data["VIX"] / data["VIX3M"]
    regime["Signal_2"] = np.where(regime["TS"] < regime_vix_threashold, 1, 0)

    # ------------------------------------------------------------------
    # Signal 3: credit spread proxy
    # ------------------------------------------------------------------
    regime["CREDIT_RATIO"]    = regime["HYG"] / regime["IEF"]
    regime["CREDIT_ROLL_M"]   = regime["CREDIT_RATIO"].rolling(window=regime_credit_lookback).mean()
    regime["CREDIT_ROLL_STD"] = regime["CREDIT_RATIO"].rolling(window=regime_credit_lookback).std()
    regime["CREDIT_Z"]        = (
        (regime["CREDIT_RATIO"] - regime["CREDIT_ROLL_M"])
        / regime["CREDIT_ROLL_STD"]
    )
    regime["Signal_3"] = np.where(regime["CREDIT_Z"] > -regime_credit_z, 1, 0)

    # ------------------------------------------------------------------
    # Regime classification
    # ------------------------------------------------------------------
    regime["Regime"] = 0

    regime["Regime"] = np.where(
        (regime["Signal_1"] == 1) & (regime["Signal_2"] == 1) & (regime["Signal_3"] == 1),
        1, regime["Regime"],
    )
    regime["Regime"] = np.where(
        (regime["Signal_1"] == 1) & (regime["Signal_2"] == 1) & (regime["Signal_3"] == 0),
        2, regime["Regime"],
    )
    regime["Regime"] = np.where(
        (regime["Signal_1"] == 1) & (regime["Signal_2"] == 0) & (regime["Signal_3"] == 1),
        2, regime["Regime"],
    )
    regime["Regime"] = np.where(
        (regime["Signal_1"] == 0) & (regime["Signal_2"] == 1) & (regime["Signal_3"] == 1),
        2, regime["Regime"],
    )

    regime.dropna(inplace=True)

    return regime
