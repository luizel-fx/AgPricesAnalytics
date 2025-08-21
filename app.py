import pandas as pd
import numpy as np
from price_loaders.tradingview import load_asset_price
import streamlit as st

from PLOT_TYPES.basis import basisSidebar, basisPlot
from PLOT_TYPES.basisDiff import basisDiffSidebar, basisDiffPlot
from PLOT_TYPES.calendarSpreads import calendarSpreadSidebar, calendarSpreadPlot

run_button = False

st.set_page_config(page_title="AgriVisor", page_icon=':corn:', layout='wide')

with st.sidebar:
    st.markdown(
f"""
    <div style="display: flex; justify-content: center;">
        <img src="https://chatgpt.com/backend-api/public_content/enc/eyJpZCI6Im1fNjhhNWUwMThmMGE0ODE5MTg3OWI2Y2VjMTQ2MWZiYmQ6ZmlsZV8wMDAwMDAwMDFjN2M2MWY0YjEwOGJjOTlkYmYzYjEwNCIsInRzIjoiNDg3Njk0IiwicCI6InB5aSIsInNpZyI6ImMyZDY0NTBhZGE2OTM0MWY3ZmU5NWRiNzliZjA1ZDcxOGUzOTRhYWNiZDU2NmE0MTg4YjBjNjgwMmViY2RkZmYiLCJ2IjoiMCIsImdpem1vX2lkIjpudWxsfQ=="; width="150">
    </div>
""", unsafe_allow_html=True)

        #st.image("IMAGES/logo.png", width=250)

    plotType = st.selectbox(
        "Plot type",
        [
            "Basis",
            "Diferencial de Base",
            "Calendar Spreads",
            "Ratios",
            "Preço relativo",
            "Sazonalidade"
        ],
        index = None
    )

    if plotType == "Basis" or plotType == "Diferencial de Base":
        commodity = st.selectbox(
        "Commmodity",
        [
            "Milho",
            "Soja",
            "Boi Gordo"
        ],
        index = None)
    elif plotType=="Calendar Spreads" or plotType == None:
        pass
    else:
        commodity = st.selectbox(
        "Commmodity",
        [
            "Milho",
            "Soja",
            "Boi Gordo"
        ],
        index = None)

    if plotType == "Basis":
        base, futName, convertUnit, expMonth, expYear, convertFactor, lookback = basisSidebar(commodity)
        run_button = st.button("Gerar")
    if plotType == "Diferencial de Base":
        fstBase, scdBase, lookback = basisDiffSidebar(commodity)
        run_button = st.button("Gerar")
    if plotType == "Calendar Spreads":
        asset, longMonth, longExpYear, shortMonth, shortExpYear, lookback = calendarSpreadSidebar()
        run_button = st.button("Gerar")


if run_button and plotType == "Basis":
    basisPlot(commodity, base, futName, convertUnit, expMonth, expYear, convertFactor, lookback)
elif run_button and plotType == "Diferencial de Base":
    basisDiffPlot(commodity, fstBase, scdBase, lookback)
elif run_button and plotType == "Calendar Spreads":
    calendarSpreadPlot(asset, longMonth, longExpYear, shortMonth, shortExpYear, lookback)
elif run_button == False:
    st.markdown(
    """
    # Bem vindo!

    AgriVisor é um projeto, ainda em desenvolvimento, de uma plataforma online, simples e intuitiva para análise de preços das principais commodities agrícolas.

    Até o momento, a plataforma permite analisar diferenciais de base, basis de soja e milho, e Calendar Spreads dos contratos de milho e boi gordo na B3, e soja em CBOT, a qual é operada na B3 através de contratos espelho.
"""
)