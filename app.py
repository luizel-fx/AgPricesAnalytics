import pandas as pd
import numpy as np
from price_loaders.tradingview import load_asset_price
import streamlit as st

from PLOT_TYPES.basis import basisSidebar, basisPlot
from PLOT_TYPES.basisDiff import basisDiffSidebar, basisDiffPlot
from PLOT_TYPES.calendarSpreads import calendarSpreadSidebar, calendarSpreadPlot

run_button = False

with st.sidebar:
    st.title("AgPrices Analytics :corn:")

    plotType = st.selectbox(
        "Plot type",
        [
            "Basis",
            "Basis Differential",
            "Calendar Spreads",
            "Ratios",
            "Relative prices",
            "Seazonality"
        ],
        index = None
    )

    if plotType == "Basis" or plotType == "Basis Differential":
        commodity = st.selectbox(
        "Commmodity",
        [
            "Corn",
            "Soybean"
        ],
        index = None)
    elif plotType=="Calendar Spreads" or plotType == None:
        pass
    else:
        commodity = st.selectbox(
        "Commmodity",
        [
            "Corn",
            "Soybean",
            "Live Cattle"
        ],
        index = None)

    if plotType == "Basis":
        base, futName, convertUnit, expMonth, expYear, convertFactor, lookback = basisSidebar(commodity)
        run_button = st.button("Run")
    if plotType == "Basis Differential":
        fstBase, scdBase, lookback = basisDiffSidebar(commodity)
        run_button = st.button("Run")
    if plotType == "Calendar Spreads":
        asset, longMonth, longExpYear, shortMonth, shortExpYear, lookback = calendarSpreadSidebar()
        run_button = st.button("Run")


if run_button and plotType == "Basis":
    basisPlot(commodity, base, futName, convertUnit, expMonth, expYear, convertFactor, lookback)
if run_button and plotType == "Basis Differential":
    basisDiffPlot(commodity, fstBase, scdBase, lookback)
if run_button and plotType == "Calendar Spreads":
    calendarSpreadPlot(asset, longMonth, longExpYear, shortMonth, shortExpYear, lookback)