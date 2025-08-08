import pandas as pd
import numpy as np
from price_loaders.tradingview import load_asset_price
import streamlit as st

import plotly.express as px
import plotly.graph_objects as go

def basisDiffSidebar(commodity):
    with st.sidebar:
        lookback = 0
        fstBase = ''
        scdBase = ''
        if commodity == "Corn":
            path = "DATA/milho.xlsx"
            bases = pd.read_excel("DATA/milho.xlsx", sheet_name="PRAÇAS")['Descrição']
        else:
            path = "DATA/soja.xlsx"
            bases = pd.read_excel("DATA/soja.xlsx", sheet_name="PRAÇAS")['Descrição']

        fstBase = st.selectbox(
            "First base",
            bases
        )

        scdBase = st.selectbox(
            "Second base",
            bases
        )

        lookback = st.number_input("Lookback", step = 1)

    return fstBase, scdBase, lookback

def basisDiffPlot(commodity, fstBase, scdBase, lookback):
    fig = go.Figure()

    if commodity == "Corn":
        path = "DATA/milho.xlsx"
        bases = pd.read_excel(path, sheet_name="PRAÇAS")
    else:
        path = "DATA/soja.xlsx"
        bases = pd.read_excel(path, sheet_name="PRAÇAS")
    
    fstBaseCode = bases[bases['Descrição'] == fstBase]['Praças'].values[0]
    scdBaseCode = bases[bases['Descrição'] == scdBase]['Praças'].values[0]

    fstBasePrices = pd.read_excel(path, sheet_name=fstBaseCode, skiprows=[0,1,2], header=None)
    fstBasePrices.columns = ['DRF', 'FEC']
    fstBasePrices['DRF'] = fstBasePrices['DRF'].apply(lambda x: pd.Timestamp(x.year, x.month, x.day))

    scdBasePrices = pd.read_excel(path, sheet_name=scdBaseCode, skiprows=[0,1,2], header=None)
    scdBasePrices.columns = ['DRF', 'FEC']
    scdBasePrices['DRF'] = scdBasePrices['DRF'].apply(lambda x: pd.Timestamp(x.year, x.month, x.day))

    currYear = max(fstBasePrices['DRF']).year
    fstBasePrices = fstBasePrices[fstBasePrices['DRF'].dt.year > currYear - lookback]
    scdBasePrices = scdBasePrices[scdBasePrices['DRF'].dt.year > currYear - lookback]

    mergedPrices = fstBasePrices.merge(scdBasePrices, on = 'DRF', how = 'left', suffixes = (f"_{fstBase}", f'_{scdBase}'))
    mergedPrices['diff'] = mergedPrices[f"FEC_{fstBase}"] - mergedPrices[f"FEC_{scdBase}"]
    mergedPrices = mergedPrices[~((mergedPrices['DRF'].dt.month == 2) & (mergedPrices['DRF'].dt.day == 29))]
    del bases

    mergedPrices['year'] = mergedPrices['DRF'].dt.year
    mergedPrices['forcedData'] = mergedPrices['DRF'].apply(lambda x: pd.Timestamp(currYear, x.month, x.day))

    mergedPricesPivoted = pd.pivot_table(
        data = mergedPrices,
        values = 'diff',
        index = 'forcedData',
        columns = 'year'
        )

    pastYears = mergedPricesPivoted.columns[:-1]
    mergedPricesPivoted = mergedPricesPivoted.bfill()

    mergedPricesPivoted['mean'] =  mergedPricesPivoted[pastYears].mean(axis = 1)

    for y in pastYears:
        fig.add_trace(go.Scatter(x=mergedPricesPivoted.index, y=mergedPricesPivoted[y], name=f'{y}',line=dict(width=1)))
    
    fig.add_trace(
        go.Scatter(
            x=mergedPricesPivoted.index,
            y=mergedPricesPivoted[currYear],
            name=f'{currYear}',
            line=dict(
                width=3,
                )
            )
        )
    fig.add_trace(
        go.Scatter(
            x=mergedPricesPivoted.index,
            y=mergedPricesPivoted['mean'],
            name=f'Mean ({lookback} years)',
            line=dict(
                width=3,
                dash = 'dash',
                color = "#000000"
                )
            )
        )
    
    st.plotly_chart(fig, theme = 'streamlit')
    
    
