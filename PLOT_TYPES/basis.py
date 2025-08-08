import pandas as pd
import numpy as np
from price_loaders.tradingview import load_asset_price
import streamlit as st
from datetime import date
import plotly.express as px
import plotly.graph_objects as go

def basisSidebar(commodity):
    with st.sidebar:
        base = ''
        convertFactor=0
        futName = ''
        convertUnit = ''
        convertFactor = ""
        expMonth = ""
        expYear = ""
        lookback=0
        if commodity == "Corn":
            bases = pd.read_excel("DATA/milho.xlsx", sheet_name="PRAÇAS")['Descrição']
            base = st.selectbox(
                "Base",
                bases
            )

            col1, col2 = st.columns(2)

            with col1:
                futures = st.selectbox(
                    "Futures exchange", ['B3', 'CBOT']
                )
            
            with col2:
                if futures == 'B3':
                    futName = "CCM"
                    convertUnit = False
                else:
                    futName = "ZC"
                    convertUnit = True
                    convertFactor = 2.2362074
                expMonth = st.text_input("Expire Month", placeholder="1! for front month")
                
                if expMonth != "1!":
                    expYear = st.text_input("Expire Year")
                else:
                    expYear = None

            lookback = st.number_input("Lookback", step = 1)
        elif commodity=="Soybean":

            bases = pd.read_excel("DATA/soja.xlsx", sheet_name="PRAÇAS")['Descrição']

            base = st.selectbox(
                "Base",
                bases
            )

            col1, col2 = st.columns(2)

            with col1:
                futures = st.selectbox(
                    "Futures exchange", ['CBOT']
                )
            
            with col2:
                futName = "ZS"
                convertUnit = True
                convertFactor = 2.2046226
                expMonth = st.text_input("Expire Month", placeholder="1! for front month")
                
                if expMonth != "1!":
                    expYear = st.number_input("Expire Year", step = 1)
                else:
                    expYear = None
            
            lookback = st.number_input("Lookback", step = 1)

    return base, futName, convertUnit, expMonth, expYear, convertFactor, lookback

def basisPlot(commodity, base, futName, convertUnit, expMonth, expYear, convertFactor, lookback):
    fig = go.Figure()

    if commodity == "Corn":
        path = "DATA/milho.xlsx"
        bases = pd.read_excel(path, sheet_name="PRAÇAS")
    else:
        path = "DATA/soja.xlsx"
        bases = pd.read_excel(path, sheet_name="PRAÇAS")
    
    baseCode = bases[bases['Descrição'] == base]['Praças'].values[0]
    del bases

    spotPrices = pd.read_excel(path, sheet_name=baseCode, skiprows=[0,1,2], header=None)
    spotPrices.columns = ['DRF', 'FEC']
    spotPrices['DRF'] = spotPrices['DRF'].apply(lambda x: pd.Timestamp(x.year, x.month, x.day))
    
    currYear = max(spotPrices['DRF']).year

    if convertUnit:
        dol = pd.read_excel('DATA/dolar.xlsx', sheet_name='dol', skiprows=[0,1], header=None)
        dol.columns=["DRF", "R$", "US$", "USD"]

        dol['DRF'] = dol['DRF'].apply(lambda x: pd.Timestamp(x.year, x.month, x.day))

        spotPrices = spotPrices.merge(dol, how = 'left', on='DRF')
        spotPrices['FEC'] = ((spotPrices['FEC']/spotPrices['USD'])/convertFactor)*100

        spotPrices.dropna()

    for i in range(0,lookback+1):
        if expMonth == "1!":
            futuresPrices = load_asset_price(f'{futName}{expMonth}', 10000, 'D')
            futuresPrices['DRF'] = futuresPrices['time'].dt.tz_convert("America/Sao_Paulo").apply(lambda x: pd.Timestamp(x.year, x.month, x.day))
            basis = spotPrices.merge(futuresPrices, on = 'DRF', how = 'left')[['DRF', 'FEC', 'close']].ffill()
            basis['basis'] = basis['FEC'] - basis['close']

            yearlySelection = basis[basis['DRF'].dt.year == currYear - i]
            try: yearlySelection = yearlySelection[~((yearlySelection['DRF'].dt.month == 2) & (yearlySelection['DRF'].dt.day == 29))] # # Dropping the 29-Feb of the leap year.
            except: pass
            yearlySelection['DRF'] = yearlySelection['DRF'].apply(lambda x: pd.Timestamp(x.year+i, x.month, x.day))
            if i != 0:
                fig.add_trace(go.Scatter(x=yearlySelection['DRF'], y=yearlySelection['basis'], name=f'{currYear - i}',line=dict(width=1)))
            else: 
                fig.add_trace(go.Scatter(x=yearlySelection['DRF'], y=yearlySelection['basis'], name=f'{currYear - i}',line=dict(width=3)))
        else: 
            futuresPrices = load_asset_price(f'{futName}{expMonth}{int(expYear) - i}', 10000,'D')
            futuresPrices['DRF'] = futuresPrices['time'].dt.tz_convert("America/Sao_Paulo").apply(lambda x: pd.Timestamp(x.year, x.month, x.day))
            basis = futuresPrices.merge(
                spotPrices,
                on = 'DRF',
                how = 'left'
            )[['DRF', 'FEC', 'close']].ffill()

            basis['basis'] = basis['FEC'] - basis['close']
            yearlySelection = basis

            try: yearlySelection = yearlySelection[~((yearlySelection['DRF'].dt.month == 2) & (yearlySelection['DRF'].dt.day == 29))] # # Dropping the 29-Feb of the leap year.
            except: pass

            yearlySelection['DRF'] = yearlySelection['DRF'].apply(lambda x: pd.Timestamp(x.year+i, x.month, x.day))

            if i != 0:
                fig.add_trace(go.Scatter(x=yearlySelection['DRF'], y=yearlySelection['basis'], name=f'{currYear - i}',line=dict(width=1)))
            else: 
                fig.add_trace(go.Scatter(x=yearlySelection['DRF'], y=yearlySelection['basis'], name=f'{currYear - i}',line=dict(width=3)))

    st.markdown(
        f"""
        ### BASIS | {commodity.upper()}
        #### {base} - {futName}{expMonth}
        """
    )
    st.plotly_chart(fig, theme = 'streamlit')