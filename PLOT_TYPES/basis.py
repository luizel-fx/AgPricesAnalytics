import pandas as pd
import numpy as np
from price_loaders.tradingview import load_asset_price
import streamlit as st
from datetime import date, datetime

import plotly.figure_factory as ff
import plotly.express as px
import plotly.graph_objects as go


def remove_outliers_iqr(df, column):
    """
    Removes outliers from a DataFrame column using the Interquartile Range (IQR) method.
    """
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]

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
        if commodity == "Milho":
            bases = pd.read_excel("DATA/milho.xlsx", sheet_name="PRAÇAS")['Descrição']
            base = st.selectbox(
                "Praça",
                bases
            )

            col1, col2 = st.columns(2)

            with col1:
                futures = st.selectbox(
                    "Bolsa", ['B3', 'CBOT']
                )
            
            with col2:
                if futures == 'B3':
                    futName = "CCM"
                    convertUnit = False
                else:
                    futName = "ZC"
                    convertUnit = True
                    convertFactor = 2.2362074
                expMonth = st.text_input("Mês de vencimento", placeholder="1! para série contínua")
                
                if expMonth != "1!":
                    expYear = st.text_input("Ano de vencimento")
                else:
                    expYear = None

            lookback = st.number_input("Lookback", step = 1)
        elif commodity=="Soja":

            bases = pd.read_excel("DATA/soja.xlsx", sheet_name="PRAÇAS")['Descrição']

            base = st.selectbox(
                "Base",
                bases
            )

            col1, col2 = st.columns(2)

            with col1:
                futures = st.selectbox(
                    "Bolsa", ['CBOT']
                )
            
            with col2:
                futName = "ZS"
                convertUnit = True
                convertFactor = 2.2046226
                expMonth = st.text_input("Mês de vencimento", placeholder="1! para série contínua")
                
                if expMonth != "1!":
                    expYear = st.number_input("Ano de vencimento", step = 1)
                else:
                    expYear = None

        elif commodity=="Boi Gordo":
            bases = pd.read_excel("DATA/boi.xlsx", sheet_name="PRAÇAS")['Descrição']
            base = st.selectbox(
                "Base",
                bases
            )

            col1, col2 = st.columns(2)

            with col1:
                futures = st.selectbox(
                    "Bolsa", ['B3']
                )
            
            with col2:
                futName = "BGI"
                convertUnit = False
                expMonth = st.text_input("Mês de vencimento", placeholder="1! para série contínua")
                
                if expMonth != "1!":
                    expYear = st.number_input("Ano de vencimento", step = 1)
                else:
                    expYear = None

        lookback = st.number_input("Lookback", step = 1)

    return base, futName, convertUnit, expMonth, expYear, convertFactor, lookback

def basisPlot(commodity, base, futName, convertUnit, expMonth, expYear, convertFactor, lookback):
    stacked_TS = go.Figure()

    if commodity == "Milho":
        path = "DATA/milho.xlsx"
        bases = pd.read_excel(path, sheet_name="PRAÇAS")
    elif commodity == "Soja":
        path = "DATA/soja.xlsx"
        bases = pd.read_excel(path, sheet_name="PRAÇAS")
    elif commodity == "Boi Gordo":
        path = "DATA/boi.xlsx"
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

    # Initialize concatedBasis here before the loop
    concatedBasis = pd.DataFrame() 

    for i in range(0,lookback+1):
        if expMonth == "1!":
            futuresPrices = load_asset_price(f'{futName}{expMonth}', 10000, 'D')
            futuresPrices['DRF'] = futuresPrices['time'].dt.tz_convert("America/Sao_Paulo").apply(lambda x: pd.Timestamp(x.year, x.month, x.day))
            basis = spotPrices.merge(futuresPrices, on = 'DRF', how = 'left')[['DRF', 'FEC', 'close']].ffill()
            basis['basis'] = basis['FEC'] - basis['close']

            yearlySelection = basis[basis['DRF'].dt.year == currYear - i]
            try: yearlySelection = yearlySelection[~((yearlySelection['DRF'].dt.month == 2) & (yearlySelection['DRF'].dt.day == 29))]
            except: pass
            yearlySelection['DRF'] = yearlySelection['DRF'].apply(lambda x: pd.Timestamp(x.year+i, x.month, x.day))
            yearlySelection['spot_logreturns'] = np.log(yearlySelection['FEC']/yearlySelection['FEC'].shift(1))
            yearlySelection['fut_logreturns'] = np.log(yearlySelection['close']/yearlySelection['close'].shift(1))
            if i != 0:
                stacked_TS.add_trace(go.Scatter(x=yearlySelection['DRF'], y=yearlySelection['basis'], name=f'{currYear - i}',line=dict(width=1)))
            else: 
                stacked_TS.add_trace(go.Scatter(x=yearlySelection['DRF'], y=yearlySelection['basis'], name=f'{currYear - i}',line=dict(width=3)))
            
            # This logic also needs to be fixed. The '1!' case was not adding to concatedBasis.
            concatedBasis = pd.concat([concatedBasis, yearlySelection], ignore_index=True)

        else: 
            futuresPrices = load_asset_price(f'{futName}{expMonth}{int(expYear) - i}', 10000,'D')
            dol['DRF'] = dol['time'].dt.tz_convert("America/Sao_Paulo").apply(lambda x: pd.Timestamp(x.year, x.month, x.day))
            futuresPrices['DRF'] = futuresPrices['time'].dt.tz_convert("America/Sao_Paulo").apply(lambda x: pd.Timestamp(x.year, x.month, x.day))
            basis = futuresPrices.merge(
                spotPrices,
                on = 'DRF',
                how = 'left'
            )[['DRF', 'FEC', 'close']].ffill()

            basis['basis'] = basis['FEC'] - basis['close']
            yearlySelection = basis

            try: yearlySelection = yearlySelection[~((yearlySelection['DRF'].dt.month == 2) & (yearlySelection['DRF'].dt.day == 29))]
            except: pass

            yearlySelection['DRF'] = yearlySelection['DRF'].apply(lambda x: pd.Timestamp(x.year+i, x.month, x.day))

            if i != 0:
                stacked_TS.add_trace(go.Scatter(x=yearlySelection['DRF'], y=yearlySelection['basis'], name=f'{currYear - i}',line=dict(width=3)))
            else: 
                stacked_TS.add_trace(go.Scatter(x=yearlySelection['DRF'], y=yearlySelection['basis'], name=f'{currYear - i}',line=dict(width=3)))

            # Now, concatenate yearlySelection to concatedBasis regardless of the loop index
            concatedBasis = pd.concat([concatedBasis, yearlySelection], ignore_index=True)
    stacked_TS.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0.01
        )
    )

    st.markdown(
        f"""
        ### BASIS | {commodity.upper()}
        #### {base} - {futName}{expMonth}
        """
    )

    concatedBasis['month'] = [date(datetime.now().year, m, 1) for m in concatedBasis['DRF'].dt.month]

    # Replace infinity values with NaN
    df_cleaned = concatedBasis.replace([np.inf, -np.inf], np.nan)

    # Drop all rows that contain any NaN values
    df_cleaned = df_cleaned.dropna()

    fstRowcol1, fstRowcol2 = st.columns([2,1])

    with fstRowcol1: st.plotly_chart(stacked_TS, theme = 'streamlit')
    with fstRowcol2:
        disPlot = ff.create_distplot(
            [df_cleaned['basis'], df_cleaned[df_cleaned['month'] == date(datetime.now().year, max(df_cleaned['DRF'].dt.month), 1)]['basis']],
            group_labels=["Ano interno", "Mês atual"],
            show_rug=False,
            show_hist=False)
        disPlot.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0.01
        )
    )
        st.plotly_chart(disPlot)


    scdRowCol1,scdRowCol2, = st.columns([3,2])

    with scdRowCol1:
        st.plotly_chart(
            px.box(
                concatedBasis,
                y = 'basis',
                x = 'month'
            )
        )
    with scdRowCol2:
        # Step 1: Remove outliers from 'spot_logreturns'
        concatedBasis_no_outliers = remove_outliers_iqr(concatedBasis, 'spot_logreturns')
        # Step 2: Remove outliers from 'fut_logreturns' on the new, already-filtered dataframe
        concatedBasis_no_outliers = remove_outliers_iqr(concatedBasis_no_outliers, 'fut_logreturns')
        
        st.plotly_chart(
            px.scatter(
                concatedBasis_no_outliers,
                y = 'basis',
                x = 'close',
                trendline='ols'
            )
        )