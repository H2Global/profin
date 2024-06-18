# -*- coding: utf-8 -*-
"""
Created on Mon Feb 26 11:44:03 2024

@author: JulianReul
"""

import numpy as np
import matplotlib.pyplot as plt
import profin as pp

#%%
#Scenario definition
scenarios = {
    "Preisobergrenze 2021": {
        "OFFTAKE_RATIO" : 0,
        "Equity_Share" : 0.2, #https://courses.renewablesvaluationinstitute.com/pages/academy/renewable-energy-financing-mastering-the-art-of-asset-structuring
        "Corporate_Tax" : 0.2, #tax global average
        "Interest_Rate" : 0.0474, #Moody's Seasoned Aaa Corporate Bond Yield
        "CRP" : 0, #Country risk premium for Kenya: 9.51% - Damodaran 01/2024
        "Year" : 2021
        },
    }

STORE_RESULTS = {}

for s in list(scenarios):
    print("Scenario:", s)
    
    #ENERGY INPUT AND OUTPUT
    E_in = 0
    #Elektrolyse: 1 GWel, Strom: 1.43 GW, Vollaststunden Elektrolyseur: 4000h
    E_out = 4*1e9 #kWh Wasserstoff
        
    #CAPEX and OPEX
    K_E_in = 0 #renewable energy
    K_E_out = 0.1 #Sales price per kWh hydrogen
    #Investment costs
    #__2021
    #____Renewables: 1,119 €/kWel
    #____Electrolysis: 1,800 €/kWel
    #__2023
    #____Renewables: 1,075 €/kWel
    #____Electrolysis: 2,100 €/kWel
    
    if scenarios[s]["Year"] == 2021:
        K_INVEST_Renewable_Energy = 1119 * 1.43 * 1e+6
        K_INVEST_Electroylsis = 1800
        K_INVEST = K_INVEST_Renewable_Energy + K_INVEST_Electroylsis
    elif scenarios[s]["Year"] == 2023:
        K_INVEST_Renewable_Energy = 1075 * 1.43 * 1e+6 
        K_INVEST_Electroylsis = 2100
        K_INVEST = K_INVEST_Renewable_Energy + K_INVEST_Electroylsis
    else:
        pass
    
    #DEFINE PARAMETERS FOR THE FUTURE DEVELOPMENT OF MEAN VALUES
    LIFETIME_TEMP = 10   
    TECHNICAL_LIFETIME = 20
    
    #DEFINE RISK PARAMETERS (random distribution and covariance matrix)
    RISK_PARAM_EXAMPLE = {
                    "E_out" : {
                        "distribution" : "normal",
                        "scale" : E_out*0.1, #10% of expected yearly output, not under offtake agreement
                        "correlation" : {
                            "MSCI" : 0.1,
                            "K_E_out" : 0.8,
                            "K_INVEST" : 0.1,
                            },
                        },
                    "K_E_out" : {
                        "distribution" : "normal",
                        "scale" : 0.022, #10% of expected hydrogen costs
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
                     E_in=E_in,
                     E_out=E_out, #kWh hydrogen per year from ISE study
                     K_E_in=0, #renewable energy
                     K_E_out=K_E_out,
                     K_INVEST=K_INVEST, #From ISE Study
                     TERMINAL_VALUE=K_INVEST*(1-LIFETIME_TEMP/TECHNICAL_LIFETIME),
                     TECHNICAL_LIFETIME=LIFETIME_TEMP,
                     OPEX=K_INVEST*0.03, #3% of CAPEX (=INVEST/LIFETIME).
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
    
    Offtake_Value = 0
    
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
    
    LIFETIME_TEMP = STORE_RESULTS[s]["ATTR"]["TECHNICAL_LIFETIME"]
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
    
    LIFETIME_TEMP = STORE_RESULTS[s]["ATTR"]["TECHNICAL_LIFETIME"]
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
   