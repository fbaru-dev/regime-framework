"""
Signal generation from daily regime classifications.

Supports two rebalancing modes controlled by config.WEEKLY_ROTATION:

  False (daily) : TargetPosition changes every day the regime changes.
                  One-day lag applied (yesterday's regime -> today's position).

  True (weekly) : Position determined by last trading day of each week,
                  shifted one week forward. Trades execute on Mondays only.
                  No lookahead bias in either mode.
"""

import numpy as np
import pandas as pd


def generate_signals(regime_data: pd.DataFrame, config) -> pd.DataFrame:
    """
    Convert daily regimes to trading signals.

    Parameters
    ----------
    regime_data : output of calculate_regimes() -- must contain 'Regime' column
    config      : StrategyConfig instance

    Returns
    -------
    pd.DataFrame with columns:
        Regime, year, month, day, dayofweek, week,
        TargetPosition, PositionChange,
        WeeklySignal (if WEEKLY_ROTATION),
        WeeklyChange, WeeklyPosition
    """
    signals = regime_data[["Regime"]].copy()

    signals["year"]      = signals.index.isocalendar().year
    signals["month"]     = signals.index.month
    signals["day"]       = signals.index.day
    signals["dayofweek"] = signals.index.dayofweek
    signals["week"]      = signals.index.isocalendar().week

    # Daily target position (shifted 1 day -- no same-day lookahead)
    signals["TargetPosition"] = 0.0
    signals.loc[signals["Regime"] == 1, "TargetPosition"] = config.POSITION_SIZE_RISK_ON
    signals.loc[signals["Regime"] == 0, "TargetPosition"] = config.POSITION_SIZE_RISK_OFF
    signals.loc[signals["Regime"] == 2, "TargetPosition"] = config.POSITION_SIZE_CAUTIONS

    signals["TargetPosition"] = signals["TargetPosition"].shift(1).ffill()

    # ------------------------------------------------------------------
    # Weekly aggregation (optional)
    # ------------------------------------------------------------------
    if config.WEEKLY_ROTATION:
        last_week_signal = (
            signals
            .groupby(["year", "week"])
            .tail(1)
            .set_index(["year", "week"])
            ["TargetPosition"]
        )

        shifted = last_week_signal.shift(1)

        signals["WeeklySignal"] = shifted.reindex(
            signals.set_index(["year", "week"]).index
        ).values

        signals["WeeklySignal"] = (
            signals.groupby(["year", "week"])["WeeklySignal"].ffill()
        )

    # ------------------------------------------------------------------
    # PositionChange flag
    # ------------------------------------------------------------------
    signals["PositionChange"] = 0

    position_col = "WeeklySignal" if config.WEEKLY_ROTATION else "TargetPosition"

    for i in range(1, len(signals[position_col])):
        curr_pos = signals[position_col].iloc[i]
        prev_pos = signals[position_col].iloc[i - 1]
        if curr_pos != prev_pos:
            signals.iloc[i, signals.columns.get_loc("PositionChange")] = 1

    # Rebalancing day flags
    signals["WeeklyChange"]   = 0
    signals["WeeklyPosition"] = 1
    signals["WeeklyChange"]   = np.where(
        signals["dayofweek"] == 0, 1, signals["WeeklyChange"])
    signals["WeeklyPosition"] = np.where(
        signals["dayofweek"] == 4, 0, signals["WeeklyPosition"])

    return signals
