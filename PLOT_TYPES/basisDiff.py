import pandas as pd
import numpy as np
from price_loaders.tradingview import load_asset_price
import streamlit as st
from datetime import date, datetime


import plotly.figure_factory as ff
import plotly.express as px
import plotly.graph_objects as go

def basisDiffSidebar(commodity):
    with st.sidebar:
        lookback = 0
        fstBase = ''
        scdBase = ''
        if commodity == "Milho":
            path = "DATA/milho.xlsx"
            bases = pd.read_excel("DATA/milho.xlsx", sheet_name="PRAÇAS")['Descrição']
        elif commodity == "Soja":
            path = "DATA/soja.xlsx"
            bases = pd.read_excel("DATA/soja.xlsx", sheet_name="PRAÇAS")['Descrição']
        elif commodity == "Boi Gordo":
            path = "DATA/boi.xlsx"
            bases = pd.read_excel(path, sheet_name="PRAÇAS")['Descrição']

        fstBase = st.selectbox(
            "Primeira praça",
            bases
        )

        scdBase = st.selectbox(
            "Segunda praça",
            bases
        )

        lookback = st.number_input("Histórico", step = 1)

    return fstBase, scdBase, lookback

def basisDiffPlot(commodity, fstBase, scdBase, lookback):
    linePlot = go.Figure()

    if commodity == "Milho":
        path = "DATA/milho.xlsx"
        bases = pd.read_excel(path, sheet_name="PRAÇAS")
    elif commodity == "Soja":
        path = "DATA/soja.xlsx"
        bases = pd.read_excel(path, sheet_name="PRAÇAS")
    elif commodity == "Boi Gordo":
        path = "DATA/boi.xlsx"
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

    mergedPrices['boxplot_flag'] = np.where(
        mergedPrices['year'] == currYear, str(currYear), "Histórico"
    )

    mergedPrices['forcedData'] = mergedPrices['DRF'].apply(lambda x: pd.Timestamp(currYear, x.month, x.day))

    mergedPricesPivoted = pd.pivot_table(
        data = mergedPrices,
        values = 'diff',
        index = 'forcedData',
        columns = 'year'
        )

    pastYears = mergedPricesPivoted.columns[:-2]
    mergedPricesPivoted = mergedPricesPivoted.bfill()

    mergedPricesPivoted['mean'] =  mergedPricesPivoted[pastYears].mean(axis = 1)

    # The following code generates a line plot with stacked years and the seasonal average
    
    linePlot.add_trace(
        go.Scatter(
            x=mergedPricesPivoted.index,
            y=mergedPricesPivoted['mean'],
            name=f'Média ({lookback} years)',
            line=dict(
                width=5,
                dash = 'dash',
                color = "#000000"
                )
            )
        )

    linePlot.add_trace(
        go.Scatter(
            x=mergedPricesPivoted.index,
            y=mergedPricesPivoted[currYear],
            name=f'{currYear}',
            line=dict(
                width=3,
                color = "#0031FF"
                )
            )
        )
    linePlot.add_trace(
        go.Scatter(
            x=mergedPricesPivoted.index,
            y=mergedPricesPivoted[currYear-1],
            name=f'{currYear-1}',
            line=dict(
                width=3,
                color = "#CC0000"
                )
            )
        )

    for y in pastYears.sort_values(ascending=False):
        linePlot.add_trace(go.Scatter(x=mergedPricesPivoted.index, y=mergedPricesPivoted[y], name=f'{y}',line=dict(width=3, color = "rgba(125, 125, 125, 0.25)")))
    
    linePlot.update_layout(
        legend = dict(
            orientation = "h",
            yanchor = "middle",
            y = 1.02,
            xanchor = "left",
            x = 0.01
        )
    )

    # Creating the displot
    mergedPrices['month'] = [date(datetime.now().year, m, 1) for m in mergedPrices['DRF'].dt.month]


    df_cleaned = mergedPrices.replace([np.inf, -np.inf], np.nan)
    df_cleaned = df_cleaned.dropna()

    disPlot = ff.create_distplot(
        [df_cleaned['diff'], df_cleaned[df_cleaned['month'] == date(datetime.now().year, max(df_cleaned['DRF'].dt.month), 1)]['diff']],
        group_labels=["Ano interno", "Mês atual"],
        show_rug=False,
        show_hist=False
    )

    disPlot.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0.01
        )
    )

    # =========== #
    # = Boxplot = #
    # =========== #
    boxplot = px.box(mergedPrices, y = 'diff', x='month', color = 'boxplot_flag')

    # ================================================= # 
    # = Ploting the generated graphs on the dashboard = #
    # ================================================= #

    fstRowCol1, fstRowCol2 = st.columns([2,1])

    with fstRowCol1: st.plotly_chart(linePlot, theme = 'streamlit') # Plot the lineplot in the dashboard
    with fstRowCol2: st.plotly_chart(disPlot,  theme = 'streamlit') # 

    scdRowCol1, scdRowCol2 = st.columns([2,1])

    with scdRowCol1: st.plotly_chart(boxplot, theme = 'streamlit')
    with scdRowCol2:
        st.subheader("Tabela Resumo")
        # Calculate summary statistics for the current year
        current_year_data = mergedPrices[mergedPrices['boxplot_flag'] == str(currYear)]
        current_year_stats = current_year_data.groupby('month')['diff'].agg(['min', 'mean', 'max'])

        # Calculate summary statistics for the historical data
        historical_data = mergedPrices[mergedPrices['boxplot_flag'] == 'Histórico']
        historical_stats = historical_data.groupby('month')['diff'].agg(['min', 'mean', 'max'])
        
        # Combine the dataframes
        summary_table = pd.concat([current_year_stats, historical_stats], axis=1)
        
        # Define multi-level columns
        summary_table.columns = pd.MultiIndex.from_product([['Ano Atual', 'Histórico'], ['Mínima', 'Média', 'Máxima']])

        # Rename index to month names in Portuguese
        month_mapping = {
            date(currYear, 1, 1): 'Janeiro',
            date(currYear, 2, 1): 'Fevereiro',
            date(currYear, 3, 1): 'Março',
            date(currYear, 4, 1): 'Abril',
            date(currYear, 5, 1): 'Maio',
            date(currYear, 6, 1): 'Junho',
            date(currYear, 7, 1): 'Julho',
            date(currYear, 8, 1): 'Agosto',
            date(currYear, 9, 1): 'Setembro',
            date(currYear, 10, 1): 'Outubro',
            date(currYear, 11, 1): 'Novembro',
            date(currYear, 12, 1): 'Dezembro'
        }
        summary_table = summary_table.rename(index=month_mapping)

        # Display the summary table
        st.dataframe(summary_table)

    
    
