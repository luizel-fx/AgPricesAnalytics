import pandas as pd
import numpy as np
from price_loaders.tradingview import load_asset_price
import streamlit as st

from PLOT_TYPES.basis import basisSidebar, basisPlot
from PLOT_TYPES.basisDiff import basisDiffSidebar, basisDiffPlot
from PLOT_TYPES.calendarSpreads import calendarSpreadSidebar, calendarSpreadPlot

run_button = False

st.set_page_config(page_title="AgriMensor", page_icon=':corn:', layout='wide')

with st.sidebar:
#    st.markdown(
#f"""
#    <div style="display: flex; justify-content: center;">
#        <img src="IMAGES"; width="150">
#    </div>
#""", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([0.5,1.5,1]) # O segundo número é maior para que a coluna do meio seja mais larga
    with col2:
        st.image("IMAGES/logo2.png", width=150)

    plotType = st.selectbox(
        "Plot type",
        [
              "Basis"
            , "Diferencial de Base"
            , "Calendar Spreads"
            #, "Ratios"
            #, "Preço relativo"
            #, "Sazonalidade"
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
        index = 0)
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
#elif run_button == False:
    #st.markdown(
    #"""
    ## Bem vindo!

    #AgriMensor é uma plataforma, ainda em desenvolvimento, para a análise de preços agrícolas, tanto do mercado físico quanto de bolsa.

    #Até o momento, conta com funcionalidades para análise de basis, diferenciais de base e calendar spreads. Cada página é confeccionada pensando em melhor fundamentar as decisões, auxiliando na elaboração de estratégias para hedge e especulação, permitindo análises sazonais livres de outliers, distribuições comparando o comportamento dos preços em determinado mês em relação ao ano.
    
    #Uma feature que será implementada, devido a falta de um contrato de soja na B3, é o comparativo dos preços físicos com vencimento específicos na bolsa de Chicago utilizando a devida cotação do dólar na curva.
    #Para os calendar spreads, calcula-se automaticamente a volatilidade diária e as métricas de risco VaR e cVar.
#"""
#)