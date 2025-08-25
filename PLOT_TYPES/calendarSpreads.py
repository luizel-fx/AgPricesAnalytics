import pandas as pd
import numpy as np
from price_loaders.tradingview import load_asset_price
import streamlit as st
from datetime import date

import plotly.express as px
import plotly.graph_objects as go

def calendarSpreadSidebar():
    with st.sidebar:
        lookback = 0
        asset = st.selectbox(
            "Asset",
            [
                "CCM",
                "ZS",
                "BGI"
            ]
            )

        longMonthCol, longExpYearCol = st.columns(2)

        with longMonthCol: longMonth = st.text_input("Long Month")
        with longExpYearCol: longExpYear = st.number_input("Long Expire Year", step = 1)

        shortMonthCol, shortExpYearCol = st.columns(2)

        with shortMonthCol: shortMonth = st.text_input("Short Month")
        with shortExpYearCol: shortExpYear = st.number_input("Short Expire Year", step = 1)

        lookback = st.number_input("Lookback", step = 1)

        return asset, longMonth, longExpYear, shortMonth, shortExpYear, lookback

def calendarSpreadPlot(asset, longMonth, longExpYear, shortMonth, shortExpYear, lookback):
    fig = go.Figure()

    for i in range(0, lookback+1):
        longContract = asset + longMonth + str(longExpYear - i)
        shortContract = asset + shortMonth + str(shortExpYear - i)

        longContractData = load_asset_price(longContract, 10000, 'D')       # Gets data from TradingView
        shortContractData = load_asset_price(shortContract, 10000, 'D')     # Gets data from TradingView

        # Converting the columns to datetime
        longContractData['time'] = pd.to_datetime(longContractData['time'])
        shortContractData['time'] = pd.to_datetime(shortContractData['time'])

        # These two variables are used to filter the data only when both contracts were open.  
        fstDate = max(longContractData['time'].min(), shortContractData['time'].min())
        lstDate = min(longContractData['time'].max(), shortContractData['time'].max())

        spreadDF = longContractData[(longContractData['time'] >= fstDate) & (longContractData['time'] <= lstDate)][['time', 'close']].merge(
            shortContractData[(shortContractData['time'] >= fstDate) & (shortContractData['time'] <= lstDate)][['time', 'close']], how='inner', on='time', suffixes=(longMonth, shortMonth)
        )

        spreadDF['time'] = spreadDF['time'].apply(lambda x: pd.Timestamp(date(x.year, x.month, x.day)))
        # Time adjustment. To have an adequate plot, we'll have to have all the data in the same year, keeping the month and the day the same.

        try: spreadDF = spreadDF[~((spreadDF['time'].dt.month == 2) & (spreadDF['time'].dt.day == 29))] # # Dropping the 29-Feb of the leap year.
        except: pass

        spreadDF['spread'] = spreadDF[f'close{longMonth}'] - spreadDF[f'close{shortMonth}']
        spreadDF['time'] = spreadDF['time'].apply(lambda x: pd.Timestamp(date(x.year + i, x.month, x.day)))

        if i != 0:
            fig.add_trace(go.Scatter(x=spreadDF['time'], y=spreadDF['spread'], name=f'{longExpYear - i}',line=dict(width=1)))
        else: 
            fig.add_trace(go.Scatter(x=spreadDF['time'], y=spreadDF['spread'], name=f'{longExpYear - i}',line=dict(width=3)))
    
    fig.update_layout(
        xaxis=dict(
            tickfont=dict(
                size=14  # Set the desired font size for x-axis ticks
            )
        ),
        yaxis=dict(
            tickfont=dict(
                size=12  # Set the desired font size for y-axis ticks
            )
        ),
        legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ))
    
    st.plotly_chart(fig, theme = 'streamlit')
