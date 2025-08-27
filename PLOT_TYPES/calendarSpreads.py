import pandas as pd
import numpy as np
from price_loaders.tradingview import load_asset_price
import streamlit as st
from datetime import date
from plotly.subplots import make_subplots

import plotly.colors as pc
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

import scipy.stats as stt

def calendarSpreadPlot(asset, longMonth, longExpYear, shortMonth, shortExpYear, lookback):
    mainPlot = make_subplots(
        rows=2,
        shared_xaxes=True,
        vertical_spacing=0,
        row_heights=[0.7, 0.3]
    )

    colors = pc.qualitative.D3
    volatilityModelDF = concatedSpread = pd.DataFrame()
    last_vol = None  # <- vamos armazenar a vol mais recente do i=0
    last_spread = None

    for i in range(0, lookback+1):
        longContract = asset + longMonth + str(longExpYear - i)
        shortContract = asset + shortMonth + str(shortExpYear - i)

        longContractData = load_asset_price(longContract, 10000, 'D')
        shortContractData = load_asset_price(shortContract, 10000, 'D')

        longContractData['time'] = pd.to_datetime(longContractData['time'])
        shortContractData['time'] = pd.to_datetime(shortContractData['time'])

        longContractData['log_returns'] = np.log(longContractData['close']).diff()
        longContractData['var'] = longContractData['log_returns'].rolling(90).var()

        shortContractData['log_returns'] = np.log(shortContractData['close']).diff()
        shortContractData['var'] = shortContractData['log_returns'].rolling(90).var()

        fstDate = max(longContractData['time'].min(), shortContractData['time'].min())
        lstDate = min(longContractData['time'].max(), shortContractData['time'].max())

        # renomear somente as colunas de interesse
        longContractData = longContractData.rename(
            columns={
                "close": f"close{longMonth}{longExpYear}",
                "log_returns": f"log_returns{longMonth}{longExpYear}",
                "var": f"var{longMonth}{longExpYear}"
            }
        )

        shortContractData = shortContractData.rename(
            columns={
                "close": f"close{shortMonth}{shortExpYear}",
                "log_returns": f"log_returns{shortMonth}{shortExpYear}",
                "var": f"var{shortMonth}{shortExpYear}"
            }
        )

        spreadDF = pd.merge(
            longContractData[['time', f'close{longMonth}{longExpYear}', f'log_returns{longMonth}{longExpYear}', f'var{longMonth}{longExpYear}']],
            shortContractData[['time', f'close{shortMonth}{shortExpYear}', f'log_returns{shortMonth}{shortExpYear}', f'var{shortMonth}{shortExpYear}']],
            on="time",
            how="inner"
        )

        # cálculo de correlação rolling
        spreadDF['rolling_corr'] = (
            spreadDF[f'log_returns{longMonth}{longExpYear}']
            .rolling(90)
            .corr(spreadDF[f'log_returns{shortMonth}{shortExpYear}'])
        )

        # variância do spread
        spreadDF['spreadVar'] = (
            spreadDF[f'var{longMonth}{longExpYear}'] + spreadDF[f'var{shortMonth}{shortExpYear}'] 
            - 2 * np.sqrt(spreadDF[f'var{longMonth}{longExpYear}']) * spreadDF['rolling_corr'] * np.sqrt(spreadDF[f'var{shortMonth}{shortExpYear}'])
        )
        spreadDF['vol'] = np.sqrt(spreadDF['spreadVar'])


        n_lags = 22
        volDF = pd.concat([
            spreadDF['vol'].shift(1) for i in range(n_lags + 1)
        ], axis=1)

        volDF.columns = [f"t-{i}" if i > 0 else "t" for i in range(n_lags + 1)]
        volDF = volDF.dropna()

        volatilityModelDF = pd.concat([volatilityModelDF, volDF])
        spreadDF['time'] = spreadDF['time'].apply(lambda x: pd.Timestamp(date(x.year, x.month, x.day)))

        try:
            spreadDF = spreadDF[~((spreadDF['time'].dt.month == 2) & (spreadDF['time'].dt.day == 29))]
        except:
            pass

        spreadDF['spread'] = spreadDF[f'close{longMonth}{longExpYear}'] - spreadDF[f'close{shortMonth}{shortExpYear}']
        spreadDF['time'] = spreadDF['time'].apply(lambda x: pd.Timestamp(date(x.year + i, x.month, x.day)))

        color = colors[i % len(colors)]
        width = 5 if i == 0 else 2
        spreadDF['pairFlag'] = legend_name = f'{longMonth}{longExpYear-i} - {shortMonth}{shortExpYear-i}'

        # Linha de spread
        mainPlot.add_trace(
            go.Scatter(x=spreadDF['time'], y=spreadDF['spread'], 
                       name=legend_name, line=dict(width=width, color=color)),
            row=1, col=1
        )

        # Linha de vol
        mainPlot.add_trace(
            go.Scatter(x=spreadDF['time'], y=spreadDF['vol'], 
                       name=legend_name, line=dict(width=width, color=color), 
                       showlegend=False),
            row=2, col=1
        )

        concatedSpread = pd.concat([concatedSpread, spreadDF])

        # --- Guardar a última vol e spread apenas quando i==0 ---
        if i == 0:
            last_vol = spreadDF['vol'].iloc[-1]
            last_spread = spreadDF['spread'].iloc[-1]

    # Layout do gráfico
    mainPlot.update_layout(
        title=dict(
            text=f"Calendar Spread | {asset}{longMonth} - {asset}{shortMonth}",
            font=dict(size=30)
        ),
        xaxis2=dict(tickfont=dict(size=15, color="#000000")),
        yaxis=dict(tickfont=dict(size=15, color="#000000")),
        yaxis2=dict(tickfont=dict(size=15, color="#000000")),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    # --- Cálculo do VaR ---
    from scipy.stats import norm
    # Exibir no Streamlit
    fstRowCol1, fstRowCol2 = st.columns([3,1])
    with fstRowCol1: 
        st.plotly_chart(mainPlot, theme='streamlit')
    with fstRowCol2:
        stats, view = st.tabs(['Estatísticas', 'Visualização'])
                # Nível de confiança
        alpha = 0.05   # 5% -> 95% confiança

        # Última volatilidade (quando i = 0)
        #last_vol = spreadDF['vol'].iloc[-1]

        # Quantil normal
        z_alpha = norm.ppf(alpha)

        # VaR paramétrico (1 dia, assumindo média zero)
        VaR = -z_alpha * last_vol

        # CVaR (Expected Shortfall)
        CVaR = last_vol * norm.pdf(z_alpha) / alpha

        with stats:
            st.metric(f"Volatilidade", f"{last_vol:.2%}")
            st.metric(f"VaR (95%)", f"{VaR:.2%}")
            st.metric(f"CVaR (95%)", f"{CVaR:.2%}")

