# -*- coding: utf-8 -*-
"""
Created on Wed Apr 24 16:40:24 2024

@author: JulianReul
"""
import yfinance as yf
import numpy as np
from datetime import datetime, date, timedelta

def get_financial_data():
    # Get times
    observe_past = 0
    today = datetime.now()
    yesterday = today - timedelta(days=1+observe_past)
    ten_years_ago = today - timedelta(days=365.25*10+observe_past)
    # Get dates
    yesterday_date = yesterday.date()
    END_DATE = yesterday_date.strftime("%Y-%m-%d")
    ten_years_ago_date = ten_years_ago.date()
    START_DATE = ten_years_ago_date.strftime("%Y-%m-%d")

    #RISK FREE RATE
    treasury_data = yf.download("^TNX", start=START_DATE, end=END_DATE)
    RISK_FREE_RATE = treasury_data['Adj Close'].iloc[-1] / 100

    #MATURE MARKET
    SP500_data = yf.download("^GSPC", start=START_DATE, end=END_DATE)
    SP500_daily_returns = SP500_data['Adj Close'].pct_change()
    SP500_annual_returns = SP500_daily_returns.resample('Y').sum()[1:-1]
    
    #CORRELATION TO MSCI WORLD
    #get data of MSCI ACWI
    MSCI_ACWI_data = yf.download("ACWI", start=START_DATE, end=END_DATE)
    MSCI_first_data_point = date(2008, 3, 28)
    #Check, whether historical data exists.
    if ten_years_ago_date < MSCI_first_data_point:
        raise ValueError("Not enough data to observe the chosen point in history. Decrease parameter -OBSERVE_PAST-")
    MSCI_ACWI_daily_returns = MSCI_ACWI_data['Adj Close'].pct_change()

    CORR_SP500_MSCIW = np.corrcoef(SP500_daily_returns[1:], MSCI_ACWI_daily_returns[1:])[0,1]

    #EQUITY RISK PREMIUM
    ERP_MATURE = (SP500_annual_returns.mean() - RISK_FREE_RATE) / CORR_SP500_MSCIW
    
    return ERP_MATURE, RISK_FREE_RATE


def get_WACC(DEBT_SHARE, EQUITY_SHARE, CORPORATE_TAX_RATE, BETA_UNLEVERED, INTEREST, R_FREE, ERP_MATURE, CRP, SP):
    """
    This methods calculates the weighted average cost of capital,
    including country-specific risk premiums.

    Returns
    -------
    WACC : np.array

    """
        
    CRP_EXPOSURE=1
    Debt_to_Equity = DEBT_SHARE / (1-DEBT_SHARE)
    LEVER = 1+((1-CORPORATE_TAX_RATE)*Debt_to_Equity)
    BETA = BETA_UNLEVERED * LEVER
    
    COST_OF_EQUITY = (
        R_FREE + 
        BETA * ERP_MATURE + 
        CRP * CRP_EXPOSURE +
        SP
        )
    
    COST_OF_DEBT = INTEREST * (1-CORPORATE_TAX_RATE)
    
    WACC = EQUITY_SHARE * COST_OF_EQUITY + DEBT_SHARE * COST_OF_DEBT
    
    return WACC, COST_OF_EQUITY, COST_OF_DEBT

#%%WACC Analysis

DEBT_SHARE = 0.6 #Stakeholder discussions
EQUITY_SHARE = 1-DEBT_SHARE
CORPORATE_TAX_RATE = 0.3 #Damodaran 01/2024
BETA_UNLEVERED = 1.058 #Lin et al. (2024)
INTEREST = 0.05 #3% long-term swap-rate + 2% credit margin
CRP = 0.0951 #Damodaran 01/2024
ERP_MATURE = 0.065 #Risk-premium of mature market
RISK_FREE_RATE = 0.045 #10y US Government bonds
SP=0

#ERP_MATURE, RISK_FREE_RATE = get_financial_data()
#print("ERP_MATURE:", ERP_MATURE)
#print("RISK_FREE_RATE:", RISK_FREE_RATE)

WACC, COST_OF_EQUITY, COST_OF_DEBT = get_WACC(
    DEBT_SHARE, 
    EQUITY_SHARE, 
    CORPORATE_TAX_RATE, 
    BETA_UNLEVERED, 
    INTEREST, 
    RISK_FREE_RATE, 
    ERP_MATURE, 
    CRP, 
    SP
    )
print("WACC:", WACC)
print("COST_OF_EQUITY:", COST_OF_EQUITY)
print("COST_OF_DEBT:", COST_OF_DEBT)














