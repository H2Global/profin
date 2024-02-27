# -*- coding: utf-8 -*-
"""
Created on Tue Feb 13 15:53:05 2024

@author: JulianReul
"""

import numpy as np
import matplotlib.pyplot as plt
import pyproject as pp

#%%
#Scenario definition
scenarios = {
    "No offtake-agreement": {
        "OFFTAKE_RATIO" : 0,
        "Equity_Share" : 0.3, #JPM
        "Corporate_Tax" : 0.25, #USA
        "Interest_Rate" : 0.0474, #Moody's Seasoned Aaa Corporate Bond Yield
        "CRP" : 0 #Country risk premium for USA - Damodaran 01/2024
       },
    "Offtake-agreement": {
        "OFFTAKE_RATIO" : 0.99,
        "Equity_Share" : 0.3, #JPM
        "Corporate_Tax" : 0.25, #USA
        "Interest_Rate" : 0.0474, #Moody's Seasoned Aaa Corporate Bond Yield
        "CRP" : 0 #Country risk premium for USA - Damodaran 01/2024
       },
    }
#%%

PATH_SAVE = "C:\\Users\\JulianReul.AzureAD\\OneDrive - H2Global\\Desktop\\H2Global\\1_Model\\pyproject_package\\media\\"
STORE_RESULTS = {}

for s in list(scenarios):
    print("Scenario:", s)
    
    #DEFINE KEY PARAMETERS
    #   1 GW     Electrolysis, 750 USD / kW-installed, OPEX: 15 USD / kW*anno, Lifetime: 30 years
    #   39000 m³ H2 intermediate storage: CAPEX: 2100 USD/m³, OPEX: 1% of CAPEX, lifetime: 40 years   
    #   ?        Desalination: CAPEX: 1640 USD/m³*d, OPEX: 128 USD/m³*d, lifetime: 30 years
    #   ?        ASU/DAC   
    #   979 tpd  Ammonia synthesis: CAPEX: , OPEX: 4%
    #Output: 1689*1e6 kWh ammonia per year --> 323.6 million tons ammonia
    #Lower heating value ammonia: 5.22 kWh / kg 

    LIFETIME_TEMP = 20   
    TECHNICAL_LIFETIME = 20
    K_E_in_temp = 0 #USD/kWh
    #Calculating investment costs JPM assumption: 6.6 USD/Liter SAF or 25 USD/gallon SAF; 3.78 L / Gallon
    liter_per_gallon = 3.78
    LHV_SAF = 9.6 #kWh/L
    #34.5 MJ/L = 9.6 kWh/L --> CAPEX costs of 6.6 USD / 9.6 kWh = 0.6875 USD / kWh SAF / year
    K_INVEST_temp = 75*1e9
        
    print("K_INVEST:", round(K_INVEST_temp*1e-6, 1), "Million USD")
    E_out_temp = 1.08864*1e+11 #3 Billion Gallons of SAF per year = 1.08864*1e+11 kWh / year
    E_in_temp=0 #Electricity demand in kWh per year

    #SAF Prices
    offtake_SAF = 8/liter_per_gallon/LHV_SAF #USD/Gallon
    green_SAF = 5/liter_per_gallon/LHV_SAF # = 5 USD/Gallon #average current price for grey 2-3 USD per Gallon
    
    #SHARE WITHOUT OFFTAKE AGREEMENT
    K_E_out_ARRAY_I = np.linspace(green_SAF, green_SAF, LIFETIME_TEMP) # grey to green            
    #Accounting for inflation
    for t in range(LIFETIME_TEMP):
        K_E_out_ARRAY_I[t] = K_E_out_ARRAY_I[t]*1.02**t
    
    #SHARE WITH OFFTAKE AGREEMENT 
    K_E_out_ARRAY_II = np.linspace(offtake_SAF, offtake_SAF, LIFETIME_TEMP) #EEX 01/24: https://www.eex-transparency.com/de/wasserstoff/deutschland
    for t in range(LIFETIME_TEMP):
        K_E_out_ARRAY_II[t] = K_E_out_ARRAY_II[t]*1.02**t
    
    #offtake agreement X% of production:
    SHARE_SECURED_OFFTAKE = scenarios[s]["OFFTAKE_RATIO"]
        
    #Calculate the combined offtake and offtake price
    K_E_out_ARRAY = K_E_out_ARRAY_I.copy()
    for t in range(LIFETIME_TEMP):
        K_E_out_ARRAY[t] = K_E_out_ARRAY_I[t]*(1-SHARE_SECURED_OFFTAKE) + K_E_out_ARRAY_II[t]*SHARE_SECURED_OFFTAKE


    #DEFINE RISK PARAMETERS (random distribution and covariance matrix)
    RISK_PARAM_EXAMPLE = {
                    "K_E_out" : {
                        "distribution" : "normal",
                        "scale" : 0.2*green_SAF*(1-scenarios[s]["OFFTAKE_RATIO"]), #50% of expected mean green ammonia price
                        "correlation" : {
                            "MSCI" : 0.1,
                            "E_out" : 0.8,
                            "K_INVEST" : 0.1,
                            },
                        },                   
# =============================================================================
#                     "K_INVEST" : {
#                         "distribution" : "positive-normal", #truncated normal distribution
#                         "scale" : K_INVEST_temp*0.2, #20% of expected CAPEX
#                         "correlation" : {
#                             "MSCI" : -0.5,
#                             "E_out" : 0.1,
#                             "K_E_out" : 0.1,
#                             },
#                         },
#                     
# =============================================================================
                    }

    #Initialize Project-object
    p_example = pp.Project(
                     E_in=E_in_temp, #Electricity demand in kWh per year
                     E_out=E_out_temp, #Cesaro et al. H2-production * 70% HB-efficiency
                     K_E_in=K_E_in_temp, #electricity price
                     K_E_out=K_E_out_ARRAY,
                     K_INVEST=K_INVEST_temp, #Cesaro et al.
                     TERMINAL_VALUE=K_INVEST_temp*(1-LIFETIME_TEMP/TECHNICAL_LIFETIME),
                     LIFETIME=LIFETIME_TEMP,
                     OPEX=K_INVEST_temp*0.015, #1.5% of CAPEX
                     EQUITY_SHARE=scenarios[s]["Equity_Share"],
                     COUNTRY_RISK_PREMIUM=scenarios[s]["CRP"], #Damodaran CRP for Kenya: 9.86%
                     INTEREST=scenarios[s]["Interest_Rate"],
                     CORPORATE_TAX_RATE=scenarios[s]["Corporate_Tax"], #Damodaran for Kenya: 30%
                     RISK_PARAM=RISK_PARAM_EXAMPLE,
                     OBSERVE_PAST=0,
                     ENDOGENOUS_BETA=False,
                     REPAYMENT_PERIOD=20
                     )
    
    # Calculate Internal Rate of Return (IRR)
    IRR = p_example.get_IRR()
    print("____IRR:", IRR.mean())
    
    # Calculate WACC for further calculations.
    WACC = p_example.get_WACC()
    print("____WACC:", WACC.mean())
    
    # Calculate net present value (NPV)
    NPV = p_example.get_NPV(WACC)
    print("____mean NPV:", NPV.mean())
    
    # Calculate the value-at-risk (VaR)
    VaR = p_example.get_VaR(NPV)
    print("____VaR:", VaR)
    
    LCOE = p_example.get_LCOE(WACC)
    print("____LCOE:", LCOE.mean())

    
    # Operating and non-operating cashflows
    operating_cashflow, operating_cashflow_std, non_operating_cashflow, non_operating_cashflow_std = p_example.get_cashflows(WACC)
    
    # Calculate offtake value
    if s == "No offtake agreement":
        Offtake_Value = 0
    else:
        Offtake_Value = (E_out_temp*K_E_out_ARRAY_II*scenarios[s]["OFFTAKE_RATIO"]).sum()
    
    STORE_RESULTS[s] = {
        "IRR" : IRR,
        "WACC" : WACC,
        "NPV" : NPV,
        "VaR" : VaR, 
        "LCOE" : LCOE,
        "ATTR" : p_example.ATTR,
        "OCF" : operating_cashflow,
        "OCF_std" : operating_cashflow_std,
        "NOCF" : non_operating_cashflow,
        "NOCF_std" : non_operating_cashflow_std,  
        "Offtake_Value" : Offtake_Value
        }
    
#%% Visualize annual non-discounted cashflows
for s in list(scenarios):
    print(s)
    
    LIFETIME_TEMP = STORE_RESULTS[s]["ATTR"]["LIFETIME"]
    start_year = 2030
    years = np.arange(start_year, LIFETIME_TEMP+start_year)
    
    #OPERATING CASHFLOW
    OCF = STORE_RESULTS[s]["OCF"]
    OCF_std = STORE_RESULTS[s]["OCF_std"]
    #NON-OPERATING CASHFLOW
    NOCF = STORE_RESULTS[s]["NOCF"]
    NOCF_std = STORE_RESULTS[s]["NOCF_std"]
    #CASHFLOW BALANCE
    CF = OCF+NOCF
    CF_STD = OCF_std+NOCF_std
        
    fig_0, ax_0 = plt.subplots()

    
    ax_0.plot(years, OCF, marker='o', label="Operating Cashflow", color="Green")
    ax_0.fill_between(years, OCF - OCF_std, OCF + OCF_std, color='Green', alpha=0.3)
    
    ax_0.plot(years, NOCF, marker='o', label="Non-operating Cashflow", color="Orange")
    ax_0.fill_between(years, NOCF - NOCF_std, NOCF + NOCF_std, color='Orange', alpha=0.3)

    ax_0.plot(years, CF, marker='o', label="Summed Cashflow", color="Blue")
    ax_0.fill_between(years, CF - CF_STD, CF + CF_STD, color='Blue', alpha=0.3)
    
    plt.xlabel('Years')
    plt.ylabel('Annual cashflows [US$]')
    #plt.ylim(0,)
    plt.title(s)
    plt.legend(loc="lower right")
    plt.grid(True)
    
    plt.show()
    
    fig_0.savefig(PATH_SAVE + "CASHFLOW_" + s + ".png", dpi=200, bbox_inches='tight')

    
    print("____IRR:", round(STORE_RESULTS[s]["IRR"].mean()*100, 2), "%")
    print("____WACC:", round(STORE_RESULTS[s]["WACC"]*100, 2), "%")
    print("____NPV:", round(STORE_RESULTS[s]["NPV"].mean()*1e-6,2), " USD Million")
    print("____VaR:", round(STORE_RESULTS[s]["VaR"]*1e-6,2), " USD Million")
    print("____LCOE:", round(STORE_RESULTS[s]["LCOE"].mean(),3), " USD/kWh")
    print("____LCOE:", round(STORE_RESULTS[s]["LCOE"].mean()*LHV_SAF,3), " USD/L")
    print("____Offtake_Value:", round(STORE_RESULTS[s]["Offtake_Value"]*1e-9,2), " USD Billion")
    
#%% Visualize development of NPV aver project lifetime
for s in list(scenarios):
    print(s)
    
    LIFETIME_TEMP = STORE_RESULTS[s]["ATTR"]["LIFETIME"]
    WACC_TEMP = STORE_RESULTS[s]["WACC"]
    
    years = np.arange(LIFETIME_TEMP+1)
    
    #CASHFLOW
    OCF = STORE_RESULTS[s]["OCF"]
    OCF_std = STORE_RESULTS[s]["OCF_std"]
    #____discounting cashflows
    CF_discounted = OCF.copy()
    CF_std_discounted = OCF_std.copy()
    for t in range(LIFETIME_TEMP):
        CF_discounted[t] = OCF[t] / (1+WACC_TEMP)**t
        CF_std_discounted[t] = OCF_std[t] / (1+WACC_TEMP)**t
    
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
    #Accounting for open principal payments.
    REPAYMENT_PERIOD = STORE_RESULTS[s]["ATTR"]["REPAYMENT_PERIOD"]
    INVEST_TEMP = STORE_RESULTS[s]["ATTR"]["K_INVEST"].mean()
    if REPAYMENT_PERIOD > LIFETIME_TEMP:
        RATIO_OPEN_PRINCIPAL = 1-(LIFETIME_TEMP / REPAYMENT_PERIOD)
        OPEN_PRINCIPAL = INVEST_TEMP * STORE_RESULTS[s]["ATTR"]["DEBT_SHARE"] * RATIO_OPEN_PRINCIPAL
    else:
        OPEN_PRINCIPAL = 0
    terminal_value = (STORE_RESULTS[s]["ATTR"]["TERMINAL_VALUE"].mean()-OPEN_PRINCIPAL) / (1+WACC_TEMP)**LIFETIME_TEMP
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
        plot_npv[-1] = NPV_cum[-1]+terminal_value
        ax.bar(years, plot_npv, bottom=0, color='green', width=line_width, label="Positive NPV")
        
    ax.set_xlabel('Years')
    ax.set_ylabel('Net present value [US$]')
    #ax.ylim(0, 4*1e8)
    ax.set_title(s)
    ax.legend(loc="lower right")
    ax.grid(True)
    xtick_position = [1, 6, 11, 16, 21]
    xtick_label = [2030, 2035, 2040, 2045, 2050]
    plt.xticks(xtick_position, xtick_label)
    plt.show()
    
    fig.savefig(PATH_SAVE + "NPV_" + s + ".png", dpi=200, bbox_inches='tight')
    
    print("____IRR:", round(STORE_RESULTS[s]["IRR"].mean()*100, 2), "%")
    print("____WACC:", round(STORE_RESULTS[s]["WACC"]*100, 2), "%")
    print("____NPV:", round(STORE_RESULTS[s]["NPV"].mean()*1e-6,2), " USD Million")
    print("____VaR:", round(STORE_RESULTS[s]["VaR"]*1e-6,2), " USD Million")
    print("____LCOE:", round(STORE_RESULTS[s]["LCOE"].mean(),3), " USD/kWh")
    print("____Offtake_Value:", round(STORE_RESULTS[s]["Offtake_Value"]*1e-9,2), " USD Billion")

