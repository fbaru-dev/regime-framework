"""
Matplotlib visualisations for the regime framework.

Three charts:
  plot_results() : 6-panel performance dashboard
                   (cumulative returns, regime, position, drawdown,
                    monthly heatmap, metrics table)
  plot_spy()     : SPY price with SMA(200) overlay
  plot_vix()     : VIX vs VIX3M time series
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def _save_figure(fig: plt.Figure, save_path: str, filename: str) -> None:
    """Save a matplotlib figure as .png at 300 dpi."""
    os.makedirs(save_path, exist_ok=True)
    path = os.path.join(save_path, f"{filename}.png")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    print(f"  Saved: {path}")


def plot_results(
    backtest_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
    signals: pd.DataFrame,
    metrics: dict,
    config,
    save_path: str = ".",
    filename: str = "regime_strategy_performance",
) -> plt.Figure:
    """
    6-panel performance dashboard.

    Panels (top to bottom):
      1. Cumulative returns: strategy vs benchmark
      2. Market regime detection (Risk ON / OFF / Cautious)
      3. Position sizing over time
      4. Drawdown comparison: strategy vs benchmark
      5. Monthly returns heatmap
      6. Key metrics table

    Parameters
    ----------
    backtest_df  : output of run_backtest()
    benchmark_df : output of run_benchmark()
    signals      : output of generate_signals()
    metrics      : output of calculate_metrics()
    config       : StrategyConfig instance (used for composition row in table)
    save_path    : directory for saved file
    filename     : base filename without extension
    """
    fig = plt.figure(figsize=(16, 12))
    gs  = fig.add_gridspec(5, 2, hspace=0.3, wspace=0.3)

    # ── 1. Cumulative returns ──────────────────────────────────────────────────
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(backtest_df.index, backtest_df["Cumulative_Returns"],
             label=f'Framework (Return: {metrics["Total Return"]:.2%})',
             linewidth=2, color="darkblue")
    ax1.plot(benchmark_df.index, benchmark_df["Cumulative_Returns"],
             label=f'Benchmark (Return: {metrics["Benchmark Return"]:.2%})',
             linewidth=2, color="gray", alpha=0.7)
    ax1.set_title("Cumulative Returns: Framework vs Benchmark",
                  fontsize=14, fontweight="bold")
    ax1.set_ylabel("Cumulative Return", fontsize=11)
    ax1.legend(loc="best", fontsize=10)
    ax1.grid(True, alpha=0.3)

    # ── 2. Regime detection ───────────────────────────────────────────────────
    ax4 = fig.add_subplot(gs[1, :])
    ax4.axhline(y=0.5, color="black", linestyle="--", linewidth=1, alpha=0.5)
    ax4.fill_between(signals.index, 0, 1,
                     where=(signals["Regime"] == 1),
                     alpha=0.2, color="green", label="Risk ON")
    ax4.fill_between(signals.index, 0, 1,
                     where=(signals["Regime"] == 0),
                     alpha=0.2, color="red", label="Risk OFF")
    ax4.fill_between(signals.index, 0, 1,
                     where=(signals["Regime"] == 2),
                     alpha=0.2, color="orange", label="Cautions")
    ax4.set_title("Market Regime Detection", fontsize=12, fontweight="bold")
    ax4.set_ylabel("Regime", fontsize=10)
    ax4.set_ylim([0, 1])
    ax4.legend(loc="best", fontsize=9)
    ax4.grid(True, alpha=0.3)

    # ── 3. Position sizing ────────────────────────────────────────────────────
    ax2 = fig.add_subplot(gs[2, :])
    ax2.fill_between(backtest_df.index, 0, backtest_df["TargetPosition"],
                     alpha=0.3, color="green", label="Position Size")
    ax2.plot(backtest_df.index, backtest_df["TargetPosition"],
             color="darkgreen", linewidth=1)
    ax2.set_title("Position Sizing Over Time", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Position (%)", fontsize=10)
    ax2.set_ylim([0, 1.1])
    ax2.grid(True, alpha=0.3)

    # ── 4. Drawdown ───────────────────────────────────────────────────────────
    ax3 = fig.add_subplot(gs[3, :])
    strategy_cum = backtest_df["Cumulative_Returns"]
    strategy_dd  = (strategy_cum - strategy_cum.expanding().max()) / strategy_cum.expanding().max()
    bench_cum    = benchmark_df["Cumulative_Returns"]
    bench_dd     = (bench_cum - bench_cum.expanding().max()) / bench_cum.expanding().max()

    ax3.fill_between(backtest_df.index, 0, strategy_dd,
                     alpha=0.3, color="red", label="Strategy DD")
    ax3.plot(benchmark_df.index, bench_dd,
             color="gray", linewidth=1.5, alpha=0.7, label="Benchmark DD")
    ax3.set_title("Drawdown Comparison", fontsize=12, fontweight="bold")
    ax3.set_ylabel("Drawdown", fontsize=10)
    ax3.legend(loc="best", fontsize=9)
    ax3.grid(True, alpha=0.3)

    # ── 5. Monthly returns heatmap ────────────────────────────────────────────
    ax5 = fig.add_subplot(gs[4, 0])
    monthly_returns = (
        backtest_df["Strategy_Returns"]
        .resample("M")
        .apply(lambda x: (1 + x).prod() - 1) * 100
    )
    monthly_returns.index = pd.to_datetime(monthly_returns.index)
    pivot_data = (
        monthly_returns
        .groupby([monthly_returns.index.year, monthly_returns.index.month])
        .first()
        .unstack()
    )
    sns.heatmap(
        pivot_data, annot=True, fmt=".1f", cmap="RdYlGn", center=0,
        cbar_kws={"label": "Return (%)"}, ax=ax5, linewidths=0.5,
    )
    ax5.set_title("Monthly Returns Heatmap (%)", fontsize=12, fontweight="bold")
    ax5.set_xlabel("Month", fontsize=10)
    ax5.set_ylabel("Year", fontsize=10)

    # ── 6. Metrics table ──────────────────────────────────────────────────────
    ax6 = fig.add_subplot(gs[4, 1])
    ax6.axis("off")

    metrics_display = [
        ["Metric",        "Strategy",                                         "Benchmark"],
        ["Composition",
         f"{config.POSITION_SIZE_RISK_OFF:.0%} / "
         f"{config.POSITION_SIZE_CAUTIONS:.0%} / "
         f"{config.POSITION_SIZE_RISK_ON:.0%}",
         f"{config.POSITION_SIZE_BH:.0%}"],
        ["Annual Return", f"{metrics['Annual Return']:.2%}",                  f"{metrics['Benchmark Annual Return']:.2%}"],
        ["Max Drawdown",  f"{metrics['Max Drawdown']:.2%}",                   f"{metrics['Benchmark Max DD']:.2%}"],
        ["Volatility",    f"{metrics['Volatility']:.2%}",                     f"{metrics['Benchmark Volatility']:.2%}"],
        ["Sharpe Ratio",  f"{metrics['Sharpe Ratio']:.2f}",                   f"{metrics['Benchmark Sharpe']:.2f}"],
        ["Calmar Ratio",  f"{metrics['Calmar Ratio']:.2f}",                   f"{metrics['Benchmark Calmar']:.2f}"],
        ["Win Rate",      f"{metrics['Win Rate']:.2%}",                       "-"],
        ["Alpha",         f"{metrics['Alpha']:.2%}",                          "-"],
    ]

    table = ax6.table(
        cellText=metrics_display, cellLoc="center",
        bbox=[0, 0, 1, 1], colWidths=[0.4, 0.3, 0.3],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)

    for j in range(3):
        table[(0, j)].set_facecolor("#40466e")
        table[(0, j)].set_text_props(weight="bold", color="white")

    plt.suptitle(
        "Regime-Based Trading Strategy - Performance Report",
        fontsize=16, fontweight="bold", y=0.995,
    )

    _save_figure(fig, save_path, filename)
    return fig


def plot_spy(
    data: pd.DataFrame,
    save_path: str = ".",
    filename: str = "spy",
) -> None:
    """
    SPY price chart with SMA(200) overlay.

    Parameters
    ----------
    data      : DataFrame with columns 'Close' and 'SMA200', DatetimeIndex
    save_path : directory for saved file
    filename  : base filename without extension
    """
    fig, ax = plt.subplots(figsize=(13, 6))

    ax.plot(data.index, data["Close"],
            label="Close Price", linewidth=2, color="blue")
    ax.plot(data.index, data["SMA200"],
            label="SMA200", linewidth=2, color="orange", alpha=0.7)

    ax.set_title("SPDR S&P 500 ETF -- SPY", fontsize=14)
    ax.set_ylabel("Price (USD)", fontsize=11)
    ax.set_xlabel("Year", fontsize=11)
    ax.legend()
    ax.grid(True)

    _save_figure(fig, save_path, filename)
    plt.show()


def plot_vix(
    vix: pd.Series,
    vix3m: pd.Series,
    save_path: str = ".",
    filename: str = "vix",
) -> None:
    """
    VIX vs VIX3M time series chart.

    Parameters
    ----------
    vix     : pd.Series of VIX values with DatetimeIndex
    vix3m   : pd.Series of VIX3M values with DatetimeIndex
    save_path : directory for saved file
    filename  : base filename without extension
    """
    fig, ax = plt.subplots(figsize=(13, 6))

    ax.plot(vix.index,   vix.values,
            label="VIX",   linewidth=2, color="blue")
    ax.plot(vix3m.index, vix3m.values,
            label="VIX3M", linewidth=2, color="orange", alpha=0.7)

    ax.set_title("CBOE Volatility Index -- VIX vs VIX3M", fontsize=14)
    ax.set_ylabel("VIX Level", fontsize=11)
    ax.set_xlabel("Year", fontsize=11)
    ax.legend()
    ax.grid(True)

    _save_figure(fig, save_path, filename)
    plt.show()


# ==============================================================================
# FABIOBARUFFA.COM COLOR THEME
# ==============================================================================
# Dark navy/slate background palette with teal accent and warm amber highlights.
# Designed to match the personal brand color scheme at fabiobaruffa.com.
 
 
 
# ==============================================================================
# FABIOBARUFFA.COM COLOR THEME
# ==============================================================================
# White background, dark navy text, teal accent — extracted from the
# fabiobaruffa.com screenshot.
#
#   Background    : #FFFFFF (page) / #F5F5F5 (panel/card)
#   Border        : #E0E0E0
#   Primary text  : #1A1A2E (near-black navy)
#   Secondary text: #6B7280 (medium grey)
#   Muted text    : #9CA3AF (light grey)
#   Teal accent   : #2B7A9E (links, nav, checkmarks, CTA outline)
#   Teal dark     : #1E6080 (CTA button fill)
#   Teal light    : #4A9FC4 (lighter highlights)
 
 
FB_THEME = {
    # Backgrounds
    "bg":          "#FFFFFF",   # page background
    "bg_panel":    "#FAFAFA",   # axes background (near-white, not grey)
    "bg_card":     "#F5F5F5",   # legend / annotation background
 
    # Text
   # "text":        "#1A1A2E",   # primary — near-black navy
   # "text_sec":    "#6B7280",   # secondary — medium grey
   # "text_muted":  "#9CA3AF",   # muted — light grey tick labels
 
    "text":        "#000000",   # primary — near-black navy
    "text_sec":    "#000000",   # secondary — medium grey
    "text_muted":  "#000000",   # muted — light grey tick labels    
 
    # Borders and grid
    "border":      "#E0E0E0",   # axis spines, legend border
    "grid":        "#F0F0F0",   # subtle gridlines
 
    # Teal accent family
    "teal":        "#2B7A9E",   # strategy line, positive mark
    "teal_dark":   "#1E6080",   # CTA / emphasis
    "teal_light":  "#4A9FC4",   # lighter teal for fills
    "teal_fill":   "#2B7A9E18", # very light teal area fill
 
    # Benchmark / neutral
    "slate":       "#9CA3AF",   # benchmark line
    "slate_dark":  "#6B7280",   # benchmark legend text
 
    # Regime bands (very light tints — white background, so keep alpha low)
    "risk_on":     "#2B7A9E12", # Risk ON  — faint teal wash
    "risk_off":    "#D9534F18", # Risk OFF — faint red wash
    "caution":     "#F0A04B18", # Cautious — faint amber wash
 
    # Regime legend marker colours (solid, for legend patches)
    "risk_on_leg": "#2B7A9E",
    "risk_off_leg":"#D9534F",
    "caution_leg": "#E8943A",
 
    # Drawdown
    "dd_fill":     "#D9534F22", # strategy drawdown fill (light red)
    "dd_line":     "#D9534F",   # strategy drawdown line
    "dd_bench":    "#9CA3AF",   # benchmark drawdown line
 
    # Spine
    "spine":       "#E0E0E0",
} 
 
def _apply_fb_style(fig, axes) -> None:
    """Apply the fabiobaruffa.com light theme to a figure and its axes."""
    fig.patch.set_facecolor(FB_THEME["bg"])
    for ax in (axes if hasattr(axes, "__iter__") else [axes]):
        ax.set_facecolor(FB_THEME["bg_panel"])
        ax.tick_params(colors=FB_THEME["text_muted"], labelsize=9)
        ax.xaxis.label.set_color(FB_THEME["text_sec"])
        ax.yaxis.label.set_color(FB_THEME["text_sec"])
        ax.title.set_color(FB_THEME["text"])
        for spine in ax.spines.values():
            spine.set_edgecolor(FB_THEME["spine"])
            spine.set_linewidth(0.6)
        ax.grid(True, color=FB_THEME["grid"], linewidth=0.6, alpha=1.0)
        ax.set_axisbelow(True)
 
 
def _fb_save(fig, save_path: str, filename: str) -> None:
    """Save a figure with the white background preserved."""
    os.makedirs(save_path, exist_ok=True)
    path = os.path.join(save_path, f"{filename}.png")
    fig.savefig(path, dpi=300, bbox_inches="tight",
                facecolor=FB_THEME["bg"])
    print(f"  Saved: {path}")
 
 
# ==============================================================================
# PLOT 1 — CUMULATIVE RETURN WITH REGIME OVERLAY
# ==============================================================================
 
def plot_returns_with_regime(
    backtest_df,
    benchmark_df,
    signals,
    metrics: dict,
    save_path: str = ".",
    filename: str = "returns_with_regime",
) -> None:
    """
    Single panel: cumulative returns (strategy and benchmark) with market
    regime shaded directly on the price chart.
 
    Regime bands (shaded background):
      Teal  = Risk ON
      Red   = Risk OFF
      Amber = Cautious
 
    Parameters
    ----------
    backtest_df  : output of run_backtest()
    benchmark_df : output of run_benchmark()
    signals      : output of generate_signals() — must contain 'Regime' column
    metrics      : output of calculate_metrics()
    save_path    : directory for saved file
    filename     : base filename without extension
    """
    import matplotlib.dates as mdates
    import matplotlib.patches as mpatches
    import matplotlib.ticker as mticker
 
    
         # Desired pixel size
    width_px, height_px = 1280, 853
    dpi = 120  # dots per inch
    
    # Convert pixels to inches
    width_in = width_px / dpi
    height_in = height_px / dpi
    
    # Create pin risk visualization
    fig, ax = plt.subplots(figsize=(width_in, height_in), dpi=dpi)

    
    #fig, ax = plt.subplots(figsize=(14, 6))
    _apply_fb_style(fig, [ax])
 
    # ── Regime background shading ─────────────────────────────────────────────
    regime_colors = {
        1: FB_THEME["risk_on"],
        0: FB_THEME["risk_off"],
        2: FB_THEME["caution"],
    }
    regime_labels = {1: "Risk ON", 0: "Risk OFF", 2: "Cautious"}
    regime_leg_colors = {
        1: FB_THEME["risk_on_leg"],
        0: FB_THEME["risk_off_leg"],
        2: FB_THEME["caution_leg"],
    }
 
    plotted_regimes = set()
    idx = signals.index
    for i in range(len(idx) - 1):
        r = int(signals["Regime"].iloc[i])
        ax.axvspan(idx[i], idx[i + 1],
                   color=regime_colors[r], linewidth=0, zorder=1)
        plotted_regimes.add(r)
 
    # ── Return lines ──────────────────────────────────────────────────────────
    ax.plot(backtest_df.index, backtest_df["Cumulative_Returns"],
            color=FB_THEME["teal_dark"], linewidth=2.0, zorder=4,
            label=f'Strategy  {metrics["Total Return"]:+.1%}')
    ax.plot(benchmark_df.index, benchmark_df["Cumulative_Returns"],
            color=FB_THEME["slate"], linewidth=1.5, zorder=3,
            linestyle="--",
            label=f'Benchmark {metrics["Benchmark Return"]:+.1%}')
 
    # Subtle teal fill above the 1.0 baseline for strategy
    ax.fill_between(
        backtest_df.index, 1.0, backtest_df["Cumulative_Returns"],
        where=backtest_df["Cumulative_Returns"] >= 1.0,
        color=FB_THEME["teal"], alpha=0.06, zorder=2,
    )
 
    # Baseline
    ax.axhline(1.0, color=FB_THEME["border"], linewidth=0.8,
               linestyle=":", zorder=2)
 
    # ── Legend ────────────────────────────────────────────────────────────────
    regime_patches = [
        mpatches.Patch(
            facecolor=regime_leg_colors[r], alpha=0.5,
            edgecolor=regime_leg_colors[r],
            label=regime_labels[r],
        )
        for r in sorted(plotted_regimes)
    ]
    line_handles, line_labels = ax.get_legend_handles_labels()
    ax.legend(
        handles=line_handles + regime_patches,
        labels=line_labels + [p.get_label() for p in regime_patches],
        loc="upper left", fontsize=12,
        facecolor=FB_THEME["bg_card"],
        edgecolor=FB_THEME["border"],
        labelcolor=FB_THEME["text"],
        framealpha=0.95,
    )
 
    # ── Axes formatting ───────────────────────────────────────────────────────
    ax.tick_params(axis='both', labelsize=11)
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda y, _: f"{y:.2f}"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=0, ha="center",
             color=FB_THEME["text_muted"])
 
    ax.set_title("Cumulative returns with regime overlay",
                 fontsize=13, fontweight="500", pad=12,
                 color=FB_THEME["text"])
    ax.set_ylabel("Cumulative return", fontsize=12,
                  color=FB_THEME["text_sec"])
 
    fig.tight_layout()
    _fb_save(fig, save_path, filename)
    plt.show()
 
 
# ==============================================================================
# PLOT 2 — CUMULATIVE RETURN + DRAWDOWN (dual panel)
# ==============================================================================
 
def plot_returns_and_drawdown(
    backtest_df,
    benchmark_df,
    metrics: dict,
    save_path: str = ".",
    filename: str = "returns_and_drawdown",
) -> None:
    """
    Two stacked panels sharing the x-axis:
      Top    : cumulative returns — strategy (teal) vs benchmark (grey dashed)
      Bottom : drawdown — strategy fill (red) and benchmark line (grey)
 
    Parameters
    ----------
    backtest_df  : output of run_backtest()
    benchmark_df : output of run_benchmark()
    metrics      : output of calculate_metrics()
    save_path    : directory for saved file
    filename     : base filename without extension
    """
    import matplotlib.dates as mdates
    import matplotlib.ticker as mticker
 
    
         # Desired pixel size
    width_px, height_px = 1280, 853
    dpi = 120  # dots per inch
    
    # Convert pixels to inches
    width_in = width_px / dpi
    height_in = height_px / dpi

    
    fig, (ax_ret, ax_dd) = plt.subplots(
        2, 1, figsize=(14, 8), dpi=dpi, sharex=True,
        gridspec_kw={"height_ratios": [2, 1], "hspace": 0.05},
    )
    _apply_fb_style(fig, [ax_ret, ax_dd])
 
    # ── Top: cumulative returns ───────────────────────────────────────────────
    ax_ret.plot(
        backtest_df.index, backtest_df["Cumulative_Returns"],
        color=FB_THEME["teal_dark"], linewidth=2.0, zorder=4,
        label=f'Strategy  {metrics["Total Return"]:+.1%}',
    )
    ax_ret.plot(
        benchmark_df.index, benchmark_df["Cumulative_Returns"],
        color=FB_THEME["slate"], linewidth=1.5, zorder=3,
        linestyle="--",
        label=f'Benchmark {metrics["Benchmark Return"]:+.1%}',
    )
    ax_ret.fill_between(
        backtest_df.index, 1.0, backtest_df["Cumulative_Returns"],
        where=backtest_df["Cumulative_Returns"] >= 1.0,
        color=FB_THEME["teal"], alpha=0.07, zorder=2,
    )
    ax_ret.axhline(1.0, color=FB_THEME["border"], linewidth=0.8,
                   linestyle=":", zorder=2)
 
    ax_ret.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda y, _: f"{y:.2f}"))
    ax_ret.set_ylabel("Cumulative return", fontsize=10,
                      color=FB_THEME["text_sec"])
    ax_ret.set_title("Cumulative returns and drawdown",
                     fontsize=13, fontweight="500", pad=12,
                     color=FB_THEME["text"])
    ax_ret.legend(
        loc="upper left", fontsize=9,
        facecolor=FB_THEME["bg_card"],
        edgecolor=FB_THEME["border"],
        labelcolor=FB_THEME["text"],
        framealpha=0.95,
    )
 
    # ── Bottom: drawdown ──────────────────────────────────────────────────────
    strat_cum = backtest_df["Cumulative_Returns"]
    strat_dd  = (strat_cum - strat_cum.expanding().max()) / strat_cum.expanding().max()
    bench_cum = benchmark_df["Cumulative_Returns"]
    bench_dd  = (bench_cum - bench_cum.expanding().max()) / bench_cum.expanding().max()
 
    ax_dd.fill_between(
        backtest_df.index, 0, strat_dd,
        color=FB_THEME["dd_line"], alpha=0.18, zorder=2,
        label=f'Strategy DD  {metrics["Max Drawdown"]:.1%}',
    )
    ax_dd.plot(
        backtest_df.index, strat_dd,
        color=FB_THEME["dd_line"], linewidth=1.2, zorder=4,
    )
    ax_dd.plot(
        benchmark_df.index, bench_dd,
        color=FB_THEME["slate"], linewidth=1.2, zorder=3,
        linestyle="--",
        label=f'Benchmark DD  {metrics["Benchmark Max DD"]:.1%}',
    )
    ax_dd.axhline(0, color=FB_THEME["border"], linewidth=0.8,
                  linestyle=":", zorder=2)
 
    ax_dd.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda y, _: f"{y:.0%}"))
    ax_dd.set_ylabel("Drawdown", fontsize=10, color=FB_THEME["text_sec"])
    ax_dd.legend(
        loc="lower left", fontsize=9,
        facecolor=FB_THEME["bg_card"],
        edgecolor=FB_THEME["border"],
        labelcolor=FB_THEME["text"],
        framealpha=0.95,
    )
 
    # ── Shared x-axis ─────────────────────────────────────────────────────────
    ax_dd.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax_dd.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.setp(ax_dd.xaxis.get_majorticklabels(), rotation=0, ha="center",
             color=FB_THEME["text_muted"])
 
    fig.tight_layout()
    _fb_save(fig, save_path, filename)
    plt.show()
 
 
# ==============================================================================
# PLOT 3 — MONTHLY RETURNS HEATMAP
# ==============================================================================
 
def plot_monthly_heatmap(
    backtest_df,
    save_path: str = ".",
    filename: str = "monthly_heatmap",
) -> None:
    """
    Monthly returns heatmap in the fabiobaruffa.com light theme.
 
    Rows = years, columns = months (Jan–Dec).
    Diverging colormap: teal for positive, red for negative, white at zero.
    Cells with no data are left blank.
 
    Parameters
    ----------
    backtest_df : output of run_backtest()
    save_path   : directory for saved file
    filename    : base filename without extension
    """
    import matplotlib.ticker as mticker
    from matplotlib.colors import LinearSegmentedColormap
    import numpy as np
 
    # ── Build year × month pivot ──────────────────────────────────────────────
    monthly = (
        backtest_df["Strategy_Returns"]
        .resample("ME")
        .apply(lambda x: (1 + x).prod() - 1) * 100
    )
    monthly.index = pd.to_datetime(monthly.index)
    pivot = (
        monthly
        .groupby([monthly.index.year, monthly.index.month])
        .first()
        .unstack(level=1)
    )
    pivot.columns = [int(c) for c in pivot.columns]
    for m in range(1, 13):
        if m not in pivot.columns:
            pivot[m] = float("nan")
    pivot = pivot[[m for m in range(1, 13)]]
 
    n_years = len(pivot)
    fig_h   = max(3.0, n_years * 1.0 + 2.0)
    fig, ax = plt.subplots(figsize=(14, fig_h))
    _apply_fb_style(fig, [ax])
 
    # ── Diverging colormap: red → white → teal ────────────────────────────────
    cmap = LinearSegmentedColormap.from_list(
        "fb_diverg",
        [FB_THEME["risk_off_leg"], "#FFFFFF", FB_THEME["teal"]],
        N=256,
    )
 
    abs_max = float(np.nanmax(np.abs(pivot.values)))
    vmax    = max(abs_max, 3.0)
 
    im = ax.imshow(
        pivot.values,
        cmap=cmap, vmin=-vmax, vmax=vmax,
        aspect="auto", interpolation="nearest",
    )
 
    # ── Cell annotations ──────────────────────────────────────────────────────
    for row_i, year in enumerate(pivot.index):
        for col_j in range(1, 13):
            val = pivot.loc[year, col_j]
            if not pd.isna(val):
                # Use dark text on light cells, white on strongly coloured cells
                intensity = abs(val) / vmax
                text_color = FB_THEME["bg"] if intensity > 0.55 else FB_THEME["text"]
                ax.text(
                    col_j - 1, row_i, f"{val:+.1f}",
                    ha="center", va="center",
                    fontsize=9, fontweight="500",
                    color=text_color,
                )
 
    # ── Axes ──────────────────────────────────────────────────────────────────
    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    ax.set_xticks(range(12))
    ax.set_xticklabels(month_labels, fontsize=9,
                       color=FB_THEME["text_sec"])
    ax.set_yticks(range(n_years))
    ax.set_yticklabels([str(y) for y in pivot.index], fontsize=9,
                       color=FB_THEME["text_sec"])
    ax.tick_params(length=0)
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
 
    # ── Colorbar ──────────────────────────────────────────────────────────────
    cbar = fig.colorbar(im, ax=ax, pad=0.02, fraction=0.03)
    cbar.ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda y, _: f"{y:+.1f}%"))
    cbar.ax.tick_params(colors=FB_THEME["text_muted"], labelsize=8)
    cbar.outline.set_edgecolor(FB_THEME["border"])
 
    ax.set_title("Monthly returns (%)",
                 fontsize=13, fontweight="500", pad=12,
                 color=FB_THEME["text"])
 
    fig.tight_layout()
    _fb_save(fig, save_path, filename)
    plt.show()