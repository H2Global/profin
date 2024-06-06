# -*- coding: utf-8 -*-
"""
Created on Thu Mar  7 11:47:43 2024

@author: JulianReul
"""

import numpy as np
import matplotlib.pyplot as plt
import profin as pp

#%% INPUT PARAMETERS

#PROJECT DATA
#____Investment costs
K_INVEST=np.zeros(shape=30)
K_INVEST[0] = 3e+9 # K_INVEST[0] is the investment at year 1
K_INVEST[10] = 3e+9*0.1 # K_INVEST[t] is an additional investment happening at year t+1
#____Terminal value at the end of life
TERMINAL_VALUE=K_INVEST[0]*0.1
# ____Depreciation period -> I would put a Warning between depreciation period and terminal value and lifetime or
# there is no connection
DEPRECIATION_PERIOD=20
#____Averaged technical lifetime of plant components
TECHNICAL_LIFETIME=30
#O&M costs, including labour costs
OPEX=K_INVEST[0]*0.02 #2% of CAPEX


#ELECTRICITY
#____Electricity demand in kWh per year. 2 GW, 4000 full load hours --> 8 TWh
E_in=2*4000*1e+6 # should it be calculated by the code?
#____Electricity price USD/kWh
K_E_in=0.02


#HYDROGEN
#____Hydrogen output. 0.1 Mt/year --> 3.333 TWh H2 # should it be calculated by the code?
E_out=0.1*1e+9*33.33
#____Hydrogen price in USD/kWh. 6 USD/kg --> 0.18 USD/kWh
K_E_out=0.18


#FINANCIAL METRICS
#____Equity
EQUITY_SHARE=0.4
#____Country risk (see Damodaran)
COUNTRY_RISK_PREMIUM=0.04
#____Interest
INTEREST=0.04
#____Tax rate
CORPORATE_TAX_RATE=0.2


#DEFINE RISK PARAMETERS (random distribution and covariance matrix)
RISK_PARAM = {
                "K_E_out" : {
                    "distribution" : "normal",
                    "scale" : 0.2*K_E_out, #50% of hydrogen price
                    "correlation" : {
                        "MSCI" : 0.1,
                        }
                    }
                }

#%% DEFINITION OF PROJECT

#Initialize Project-object
p_example = pp.Project(
                 E_in=E_in, #Electricity demand in kWh per year
                 E_out=E_out, #Cesaro et al. H2-production * 70% HB-efficiency
                 K_E_in=K_E_in, #electricity price
                 K_E_out=K_E_out,
                 K_INVEST=K_INVEST, #Cesaro et al.
                 TERMINAL_VALUE=TERMINAL_VALUE,
                 LIFETIME=TECHNICAL_LIFETIME,
                 OPEX=OPEX, #1.5% of CAPEX
                 EQUITY_SHARE=EQUITY_SHARE,
                 COUNTRY_RISK_PREMIUM=COUNTRY_RISK_PREMIUM, #Damodaran CRP for Kenya: 9.86%
                 INTEREST=INTEREST,
                 CORPORATE_TAX_RATE=CORPORATE_TAX_RATE, #Damodaran for Kenya: 30%
                 RISK_PARAM=RISK_PARAM,
                 OBSERVE_PAST=0,
                 ENDOGENOUS_BETA=False,
                 REPAYMENT_PERIOD=DEPRECIATION_PERIOD
                 )

#%%CALCULATION OF FINANCIAL METRICS

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
Offtake_Value = 0

STORE_RESULTS = {
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
LIFETIME_TEMP = STORE_RESULTS["ATTR"]["LIFETIME"]
start_year = 2030
years = np.arange(start_year, LIFETIME_TEMP+start_year)

#OPERATING CASHFLOW
OCF = STORE_RESULTS["OCF"]
OCF_std = STORE_RESULTS["OCF_std"]
#NON-OPERATING CASHFLOW
NOCF = STORE_RESULTS["NOCF"]
NOCF_std = STORE_RESULTS["NOCF_std"]
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
plt.legend(loc="lower right")
plt.grid(True)

plt.show()


print("____IRR:", round(STORE_RESULTS["IRR"].mean()*100, 2), "%")
print("____WACC:", round(STORE_RESULTS["WACC"]*100, 2), "%")
print("____NPV:", round(STORE_RESULTS["NPV"].mean()*1e-6,2), " USD Million")
print("____VaR:", round(STORE_RESULTS["VaR"]*1e-6,2), " USD Million")
print("____LCOE:", round(STORE_RESULTS["LCOE"].mean(),3), " USD/kWh")
print("____Offtake_Value:", round(STORE_RESULTS["Offtake_Value"]*1e-9,2), " USD Billion")
    
#%% Visualize development of NPV over project lifetime
    
LIFETIME_TEMP = STORE_RESULTS["ATTR"]["LIFETIME"]
WACC_TEMP = STORE_RESULTS["WACC"]

years = np.arange(LIFETIME_TEMP+1)

#CASHFLOW
OCF = STORE_RESULTS["OCF"]
OCF_std = STORE_RESULTS["OCF_std"]
#____discounting cashflows
CF_discounted = OCF.copy()
CF_std_discounted = OCF_std.copy()
for t in range(LIFETIME_TEMP):
    CF_discounted[t] = OCF[t] / (1+WACC_TEMP)**t
    CF_std_discounted[t] = OCF_std[t] / (1+WACC_TEMP)**t

#ANNUAL NPV
NPV = np.zeros(LIFETIME_TEMP+1)
#____initial invest in year "0"
for t in range(LIFETIME_TEMP):
    NPV[t] -= STORE_RESULTS["ATTR"]["K_INVEST"][t].mean()
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
REPAYMENT_PERIOD = STORE_RESULTS["ATTR"]["REPAYMENT_PERIOD"]
INVEST_TEMP = STORE_RESULTS["ATTR"]["K_INVEST"].mean()
if REPAYMENT_PERIOD > LIFETIME_TEMP:
    RATIO_OPEN_PRINCIPAL = 1-(LIFETIME_TEMP / REPAYMENT_PERIOD)
    OPEN_PRINCIPAL = INVEST_TEMP * STORE_RESULTS["ATTR"]["DEBT_SHARE"] * RATIO_OPEN_PRINCIPAL
else:
    OPEN_PRINCIPAL = 0
terminal_value = (STORE_RESULTS["ATTR"]["TERMINAL_VALUE"].mean()-OPEN_PRINCIPAL) / (1+WACC_TEMP)**LIFETIME_TEMP
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
ax.legend(loc="lower right")
ax.grid(True)
xtick_position = [1, 6, 11, 16, 21, 26, 31]
xtick_label = [2030, 2035, 2040, 2045, 2050, 2055, 2060]
plt.xticks(xtick_position, xtick_label)
plt.show()


print("____IRR:", round(STORE_RESULTS["IRR"].mean()*100, 2), "%")
print("____WACC:", round(STORE_RESULTS["WACC"]*100, 2), "%")
print("____NPV:", round(STORE_RESULTS["NPV"].mean()*1e-6,2), " USD Million")
print("____VaR:", round(STORE_RESULTS["VaR"]*1e-6,2), " USD Million")
print("____LCOE:", round(STORE_RESULTS["LCOE"].mean(),3), " USD/kWh")
print("____Offtake_Value:", round(STORE_RESULTS["Offtake_Value"]*1e-9,2), " USD Billion")

