# -*- coding: utf-8 -*-
"""
Created on Sun Nov 19 17:10:28 2023

@author: JulianReul
"""

import numpy as np
import matplotlib.pyplot as plt
import pyproject as pp

#%%
#Scenario definition
scenarios = {
    "No offtake agreement": {
        "OFFTAKE_RATIO" : 0,
        "Equity_Share" : 0.4, #https://courses.renewablesvaluationinstitute.com/pages/academy/renewable-energy-financing-mastering-the-art-of-asset-structuring
        "Corporate_Tax" : 0.3, #DAMODARAN
        "Interest_Rate" : 0.0474, #Moody's Seasoned Aaa Corporate Bond Yield. 3.843%, if we consider H2Global donors
        "CRP" : 0.0951 #Country risk premium for Kenya: 9.51% - Damodaran 01/2024
       },
    "Offtake-agreement for 90% of production and 10% tax reduction": {
        "OFFTAKE_RATIO" : 0.9,
        "Equity_Share" : 0.4, #https://courses.renewablesvaluationinstitute.com/pages/academy/renewable-energy-financing-mastering-the-art-of-asset-structuring
        "Corporate_Tax" : 0.2, #tax exemption zone in Kenya
        "Interest_Rate" : 0.0474, #Moody's Seasoned Aaa Corporate Bond Yield
        "CRP" : 0.0951 #Country risk premium for Kenya: 9.51% - Damodaran 01/2024
       },
    "Offtake-agreement for 90% of production, 30% tax reduction, \nreduced CRP, increased debt-ratio": {
        "OFFTAKE_RATIO" : 0.9,
        "Equity_Share" : 0.2, #https://courses.renewablesvaluationinstitute.com/pages/academy/renewable-energy-financing-mastering-the-art-of-asset-structuring
        "Corporate_Tax" : 0, #tax exemption zone in Kenya
        "Interest_Rate" : 0.0474, #Moody's Seasoned Aaa Corporate Bond Yield
        "CRP" : 0.044 #Country risk premium for South Africa: 4.40% - Damodaran 01/2024
       },
    }

#____KENYA CASE STUDY: https://www.buyrentkenya.com/discover/kenyas-first-green-hydrogen-project-hdf-energy

STORE_RESULTS = {}

for s in list(scenarios):
    print("Scenario:", s)
    
    #DEFINE PARAMETERS FOR THE FUTURE DEVELOPMENT OF MEAN VALUES
    LIFETIME_TEMP = 10   
    TECHNICAL_LIFETIME = 30
    
    if s == "No offtake agreement":
        # ____Define the sigmoid function with parameters a and b
        def sigmoid(x, a, b):
            return 1 / (1 + np.exp(-a * (x - b)))
    
        # Generate an array of x values
        x_values = np.linspace(0,LIFETIME_TEMP, LIFETIME_TEMP)
        # Adjustable parameters to control the shape of the S-curve
        slope_parameter = 0.5
        position_parameter = LIFETIME_TEMP/4 #ramp-up to full capacity after half of lifetime (5 years).
        E_out_MAX = 3028*1e6
    
        # Apply the sigmoid function to calculate s-curve shaped market offtake
        E_out_ARRAY = sigmoid(x_values, slope_parameter, position_parameter)*E_out_MAX    
        E_out_ARRAY_STD = E_out_ARRAY*0.1
        K_E_out_ARRAY = np.linspace(0.22, 0.22, LIFETIME_TEMP) #EEX 01/24: https://www.eex-transparency.com/de/wasserstoff/deutschland
    else:        
        #offtake agreement X% of production:
        E_out_MAX = 3028*1e6
        SHARE_SECURED_OFFTAKE = scenarios[s]["OFFTAKE_RATIO"]

        #SHARE WITHOUT OFFTAKE AGREEMENT
        # ____Define the sigmoid function with parameters a and b
        def sigmoid(x, a, b):
            return 1 / (1 + np.exp(-a * (x - b)))
    
        # Generate an array of x values
        x_values = np.linspace(0,LIFETIME_TEMP, LIFETIME_TEMP)
        # Adjustable parameters to control the shape of the S-curve
        slope_parameter = 0.5
        position_parameter = LIFETIME_TEMP/4
        E_out_MAX_I = E_out_MAX*(1-SHARE_SECURED_OFFTAKE)
        # Apply the sigmoid function to calculate s-curve shaped market offtake
        E_out_ARRAY_I = sigmoid(x_values, slope_parameter, position_parameter)*E_out_MAX_I    
        E_out_ARRAY_STD_I = E_out_ARRAY_I*0.1
        
        #SHARE WITH OFFTAKE AGREEMENT
        E_out_MAX_II = E_out_MAX*SHARE_SECURED_OFFTAKE
        E_out_ARRAY_II = np.linspace(E_out_MAX_II, E_out_MAX_II, LIFETIME_TEMP)

        #Calculate the combined offtake and offtake price
        E_out_ARRAY = E_out_ARRAY_I + E_out_ARRAY_II
        E_out_ARRAY_STD = E_out_ARRAY_STD_I
        K_E_out_ARRAY = np.linspace(0.22, 0.22, LIFETIME_TEMP) #EEX 01/24: https://www.eex-transparency.com/de/wasserstoff/deutschland
        

    #DEFINE RISK PARAMETERS (random distribution and covariance matrix)
    RISK_PARAM_EXAMPLE = {
                    "E_out" : {
                        "distribution" : "normal",
                        "scale" : E_out_ARRAY_STD, #10% of expected yearly output, not under offtake agreement
                        "correlation" : {
                            "MSCI" : 0.1,
                            "K_E_out" : 0.8,
                            "K_INVEST" : 0.1,
                            },
                        },
                    "K_E_out" : {
                        "distribution" : "normal",
                        "scale" : 0.022*(1-scenarios[s]["OFFTAKE_RATIO"]), #10% of expected hydrogen costs
                        "correlation" : {
                            "MSCI" : 0.1,
                            "E_out" : 0.8,
                            "K_INVEST" : 0.1,
                            },
                        },
                    "K_INVEST" : {
                        "distribution" : "positive-normal", #truncated normal distribution
                        "scale" : 2082000000*0.2, #20% of expected CAPEX
                        "correlation" : {
                            "MSCI" : -0.5,
                            "E_out" : 0.1,
                            "K_E_out" : 0.1,
                            },
                        },
                    }

    #Initialize Project-object
    #   1 GW     Electrolysis, 750 USD / kW-installed, OPEX: 15 USD / kW*anno, Lifetime: 30 years
    #   1.9 GW   PV, 650 USD / kW-installed, OPEX: 13 USD / kW*anno, lifetime: 30 years
    #   39000 m³ H2 intermediate storage: CAPEX: 2100 USD/m³, OPEX: 1% of CAPEX, lifetime: 40 years   
    #   ?        Desalination: CAPEX: 1640 USD/m³*d, OPEX: 128 USD/m³*d, lifetime: 30 years
    #   ?         ASU/DAC   
    #   979 tpd  Ammonia synthesis: CAPEX: , OPEX: 4%
    #Output: 1689*1e6 kWh ammonia per year --> 323.6 million tons ammonia
    #Lower heating value ammonia: 5.22 kWh / kg  
    p_example = pp.Project(
                     E_in=3028*1e6,
                     E_out=E_out_ARRAY, #kWh hydrogen per year from ISE study
                     K_E_in=0, #renewable energy
                     K_E_out=K_E_out_ARRAY,
                     K_INVEST=2082000000, #From ISE Study
                     TERMINAL_VALUE=2082000000*(1-LIFETIME_TEMP/TECHNICAL_LIFETIME),
                     LIFETIME=LIFETIME_TEMP,
                     OPEX=2082000000*0.03, #3% of CAPEX (=INVEST/LIFETIME).
                     EQUITY_SHARE=scenarios[s]["Equity_Share"],
                     COUNTRY_RISK_PREMIUM=scenarios[s]["CRP"], #Damodaran CRP for Kenya: 9.86%
                     INTEREST=scenarios[s]["Interest_Rate"],
                     CORPORATE_TAX_RATE=scenarios[s]["Corporate_Tax"], #Damodaran for Kenya: 30%
                     RISK_PARAM=RISK_PARAM_EXAMPLE,
                     OBSERVE_PAST=0,
                     ENDOGENOUS_BETA=False
                     )

    
    # Calculate Internal Rate of Return (IRR)
    IRR = p_example.get_IRR()
    
    # Calculate WACC for further calculations.
    WACC = p_example.get_WACC()
    print("____WACC:", WACC)
    
    # Calculate net present value (NPV)
    NPV = p_example.get_NPV(WACC)
    print("____mean NPV:", NPV.mean())
    
    # Calculate the value-at-risk (VaR)
    VaR = p_example.get_VaR(NPV)
    print("____VaR:", VaR)
    
    # Non-Discounted Cashflows before capital service, and capital service
    Cashflow_before_CS, Cashflow_before_CS_std, CS, CS_std = p_example.get_cashflows(WACC)
    
    # Calculate offtake value
    if s == "No offtake agreement":
        Offtake_Value = 0
    else:
        Offtake_Value = (E_out_MAX_II*K_E_out_ARRAY).sum()

    
    STORE_RESULTS[s] = {
        "IRR" : IRR,
        "WACC" : WACC,
        "NPV" : NPV,
        "VaR" : VaR, 
        "ATTR" : p_example.ATTR,
        "CF" : Cashflow_before_CS,
        "CF_std" : Cashflow_before_CS_std,
        "CS" : CS,
        "CS_std" : CS_std,  
        "Offtake_Value" : Offtake_Value
        }
    
#%% Visualize annual non-discounted cashflows
for s in list(scenarios):
    print(s)
    
    LIFETIME_TEMP = STORE_RESULTS[s]["ATTR"]["LIFETIME"]
    years = np.arange(1, LIFETIME_TEMP+1)
    
    #CASHFLOW
    CF = STORE_RESULTS[s]["CF"]
    CF_std = STORE_RESULTS[s]["CF_std"]
    #CAPITAL SERVICE
    CS = STORE_RESULTS[s]["CS"]
    CS_std = STORE_RESULTS[s]["CS_std"]
        
    plt.errorbar(years, CF, yerr=CF_std, fmt='o', label='Cashflow before capital service')
    plt.errorbar(years, CS, yerr=CS_std, fmt='^', label="Capital service (equity & debt)")
    
    plt.xlabel('Years')
    plt.ylabel('Annual cashflows [US$]')
    plt.ylim(0,)
    plt.title(s)
    plt.legend(loc="lower right")
    plt.grid(True)
    
    plt.show()
    
    print("____IRR:", round(STORE_RESULTS[s]["IRR"].mean()*100, 2), "%")
    print("____WACC:", round(STORE_RESULTS[s]["WACC"]*100, 2), "%")
    print("____NPV:", round(STORE_RESULTS[s]["NPV"].mean()*1e-6,2), " USD Million")
    print("____VaR:", round(STORE_RESULTS[s]["VaR"]*1e-6,2), " USD Million")
    print("____Offtake_Value:", round(STORE_RESULTS[s]["Offtake_Value"]*1e-9,2), " USD Billion")
    
#%% Visualize development of NPV aver project lifetime
for s in list(scenarios):
    print(s)
    
    LIFETIME_TEMP = STORE_RESULTS[s]["ATTR"]["LIFETIME"]
    WACC_TEMP = STORE_RESULTS[s]["WACC"]
    
    years = np.arange(LIFETIME_TEMP+1)
    
    #CASHFLOW
    CF = STORE_RESULTS[s]["CF"]
    CF_std = STORE_RESULTS[s]["CF_std"]
    #____discounting cashflows
    CF_discounted = CF.copy()
    CF_std_discounted = CF_std.copy()
    for t in range(LIFETIME_TEMP):
        CF_discounted[t] = CF[t] / (1+WACC_TEMP)**t
        CF_std_discounted[t] = CF_std[t] / (1+WACC_TEMP)**t
    
    #ANNUAL NPV
    NPV = np.zeros(LIFETIME_TEMP+1)
    #____initial invest in year "0"
    NPV[0] -= STORE_RESULTS[s]["ATTR"]["K_INVEST"].mean()
    #____positive cashflows to equity
    NPV[1:] = CF_discounted
    #____cumulate cashflows
    NPV_cum = NPV.cumsum()
    
    #PLOTTING
    fig, ax = plt.subplots()
        
    line_width = 0.8
    #____derive first plot (initial invest)
    plot_invest = NPV_cum.copy()
    plot_invest[1:] = 0
    ax.bar(years, plot_invest, color='orange', width=line_width, label="Invest")
    
    # Get the x-axis limits
    delta_x = LIFETIME_TEMP+1
    ax.set_xlim(-0.5, LIFETIME_TEMP+0.5)
    offset_zero = 0.5 / delta_x
    #offset_years = (delta_x-offset_zero*2)/LIFETIME_TEMP
    
    #____derive second plot (positive cashflows)
    for year_temp in range(1, LIFETIME_TEMP+1):
        x_position = year_temp/delta_x
        ax.axhline(y=NPV_cum[year_temp], 
                    color='black', 
                    xmin=x_position - (1/delta_x)*0.4 + offset_zero, 
                    xmax=x_position + (1/delta_x)*0.4 + offset_zero, 
                    linestyle='-')
    
    #____derive third and fourth plot (terminal values)
    terminal_value = STORE_RESULTS[s]["ATTR"]["TERMINAL_VALUE"]
    plot_terminal_value = np.zeros(LIFETIME_TEMP+1)
    plot_npv = np.zeros(LIFETIME_TEMP+1)

    if NPV_cum[-1] < 0:
        if terminal_value+NPV_cum[-1] > 0:
            #plot positive NPV in green
            plot_npv[-1] = terminal_value+NPV_cum[-1]
            ax.bar(years, plot_npv, color='green', width=line_width, label="Positive NPV")
            #plot terminal value add on until NPV=0
            plot_terminal_value[-1] = -NPV_cum[-1]
            ax.bar(years, plot_terminal_value, bottom=NPV_cum[-1], color='grey', width=line_width, label="Terminal value-NPV")
        else:
            #plot negative NPV in red
            plot_npv[-1] = -(terminal_value+NPV_cum[-1])
            ax.bar(years, plot_npv, bottom=NPV_cum[-1]+terminal_value, color='red', width=line_width, label="Negative NPV")
            #plot terminal value add on until NPV=0
            plot_terminal_value[-1] = terminal_value
            ax.bar(years, plot_terminal_value, bottom=NPV_cum[-1], color='grey', width=line_width, label="Terminal value")
    else:
        #plot terminal value on top of positive NPV in green 
        plot_npv[-1] = terminal_value
        ax.bar(years, plot_npv, bottom=NPV_cum[-1], color='green', width=line_width, label="Terminal value")
                
    ax.set_xlabel('Years')
    ax.set_ylabel('Net present value [US$]')
    #ax.ylim(0, 4*1e8)
    ax.set_title(s)
    ax.legend(loc="lower right")
    ax.grid(True)
    
    plt.show()
    
    print("____IRR:", round(STORE_RESULTS[s]["IRR"].mean()*100, 2), "%")
    print("____WACC:", round(STORE_RESULTS[s]["WACC"]*100, 2), "%")
    print("____NPV:", round(STORE_RESULTS[s]["NPV"].mean()*1e-6,2), " USD Million")
    print("____VaR:", round(STORE_RESULTS[s]["VaR"]*1e-6,2), " USD Million")
    print("____Offtake_Value:", round(STORE_RESULTS[s]["Offtake_Value"]*1e-9,2), " USD Billion")
    
#%%Financial data
import yfinance as yf

# This is a list of all ticker symbols of companies which are 
# donors to the H2G Foundation.
h2global_donors = [
    "2082.SR", #ACWA,
    #"", #Augustus
    "AB9.DE", #Abo Wind
    "AIL.F", #Air Liquide
    "APD", #Air Products
    "MT", #ArcelorMittal
    "BAS.DE", #BASF
    "BP", #BP
    "1COV.DE", #Covestro
    "CYA.F", #Chiyoda
    #"", #CWP Global
    "DTG.DE", #Daimler Truck
    #"", #Deutsche Bank
    #"", #duisport
    #"", #EEX
    #"", #Enertrag
    "EONGY", #eon
    "ENGI.PA", #Engie
    #"", #Eternal Power
    #"", #FEV
    #"", #F. Laeisz
    "FLUX.BR", #Fluxys
    "FMG.AX", #Fortescue Future Industries
    #"", #Gascade
    #"", #Gasunie
    #"", #green enesys
    #"", #HIF
    "HHFA.VI", #HHLA
    #"", #Hydrogenious
    #"", #Hy24
    #"", #KfW
    "LIN", #Linde
    #"", #MAN Energy Solutions
    #"", #Neuman&Esser
    #"", #Nordex
    #"", #NordLb
    "NPI.TO", #Northland Power
    "OCI.AS", #OCI global
    "ORSTED.CO", #Orsted
    #"", #Port of Antwerp Bruges
    #"", #RAG Austria AG
    #"", #Rostock Port
    "RWE.DE", #RWE
    "SZG.DE", #Salzgitter AG
    "SSL", #Sasol
    #"", #SEFE
    "SHEL", #Shell
    "ENR.DE", #Siemens Energy
    #"", #TES
    "NCH2.DE", #ThyssenKrupp Nucera
    #"", #Total Eren
    "UN0.DE", #uniper
    #"", #Viridi
    "VPK.AS", #Vopak
    #"", #VNG
    "YAR.OL", #Yara Clean Ammonia
    #"", #1PointFive
    #"", #Mitsui
    ]

interest_rates = []
for ticker_temp in h2global_donors:
    try:
        corp = yf.Ticker(ticker_temp)
        income_stmt = corp.income_stmt
        balance_sheet = corp.balance_sheet
        timestamps = list(balance_sheet)
        latest_ts = timestamps[0]
        interest_rate = (
            income_stmt[latest_ts]["Interest Expense"] / 
            balance_sheet[latest_ts]["Total Debt"]
            )
        interest_rates.append(interest_rate)
    except:
        print(ticker_temp)

interest_rates_np = np.array(interest_rates)
mean_interest_rate = np.nanmean(interest_rates_np)
#%%BETAS
import pandas as pd

# Step 1: Get leveraged beta
def get_leveraged_beta(ticker):
    stock = yf.Ticker(ticker)
    market = yf.Ticker("ACWI")
    data_stock = stock.history(period="5y")
    data_market = market.history(period="5y")
    
    # Calculate daily returns
    stock_returns = data_stock['Close'].pct_change().dropna()
    stock_returns_df = stock_returns.to_frame()
    stock_returns_df["only_date"] = stock_returns_df.index.date
    
    market_returns = data_market['Close'].pct_change().dropna()
    market_returns_df = market_returns.to_frame()
    market_returns_df["only_date"] = market_returns_df.index.date
    
    merged_df = pd.merge(
        market_returns_df, 
        stock_returns_df, 
        left_on="only_date", 
        right_on="only_date", 
        how='inner')
    
    # Calculate leveraged beta
    cov_matrix = np.cov(merged_df["Close_x"], merged_df["Close_y"])
    beta = cov_matrix[0, 1] / market_returns.var()
    
    return beta

# Step 2: Get debt-to-equity ratio
def get_debt_equity_ratio(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    balance_sheet = stock.balance_sheet
    timestamps = list(balance_sheet)
    latest_ts = timestamps[0]
    
    debt = balance_sheet[latest_ts]["Total Debt"]
    equity = info.get('marketCap', 0)
    
    # Avoid division by zero
    if equity == 0:
        return None
    
    debt_equity_ratio = debt / equity
    return debt_equity_ratio

# Step 3: Calculate unlevered beta
def calculate_unlevered_beta(ticker):
    #Tax Rate For Calcs                                                                                             
    
    leveraged_beta = get_leveraged_beta(ticker)
    debt_equity_ratio = get_debt_equity_ratio(ticker)
    
    # Avoid calculation if debt-equity ratio is not available
    if debt_equity_ratio is None:
        return None
    
    unlevered_beta = leveraged_beta / (1 + (1 - tax_rate) * debt_equity_ratio)
    
    return unlevered_beta

# Assuming a corporate tax rate (you may adjust this value)
tax_rate = 0.3

betas_unlevered = []
for ticker_temp in h2global_donors:
    betas_unlevered.append(calculate_unlevered_beta(ticker_temp))
    
betas_unlevered_np = np.array(betas_unlevered)
beta_unlevered_mean = np.nanmean(betas_unlevered_np)
