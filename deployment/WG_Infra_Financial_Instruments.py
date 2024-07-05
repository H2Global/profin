# -*- coding: utf-8 -*-
"""
Created on Fri Mar 22 09:41:20 2024

@author: JulianReul
"""

import numpy as np
import matplotlib.pyplot as plt
import profin as pp
from terminal_config import Terminal
import terminal_model as tm
import Country_Risk
import pandas as pd

#%% INPUT PARAMETERS

#Iterate the following scenario parameters manually
INFRASTRUCTURE = "Pipeline" # "Pipeline", "Terminal", "Storage"
Terminal_Type = "LOHC" #NH3, LH2, SNG, LOHC
Conversion_Terminal = True
Storage_Type = "Multi-turn" #Single-turn

#Initialize storage dicts
SUBSIDY_DICT = {}
CASHFLOW_DICT = {}
STORE_RESULTS = True
FILE_PATH = "C:\\Users\\JulianReul.AzureAD\\H2Global\Outreach - General\\Working Groups\\01_WG Infrastructure\\05_Report\\Simulation_Results.xlsx"
DICT_RESULTS = {}

for t_scale in [1, 2, 4]:
    DICT_RESULTS["t_scale_" + str(t_scale)] = {}
    for Utilization in ["Low", "Ramp-up"]: #, "Ramp-up"
        DICT_RESULTS["t_scale_" + str(t_scale)][Utilization] = {}
        for ENDOGENOUS_PROJECT_RISK in [True, False]:
            DICT_RESULTS["t_scale_" + str(t_scale)][Utilization][str(ENDOGENOUS_PROJECT_RISK)] = {}
            
            SUBSIDY_DICT["t_scale_" + str(t_scale)] = {}
            CASHFLOW_DICT["t_scale_" + str(t_scale)] = {}
        
            print("__________________________")
            print("__________________________")
            print("SCALE OF FUNDING TARIFF: ", t_scale)
            print("__________________________")
            print("__________________________")
        
            #GENERAL PROJECT DATA
            #____Tariff: Same tariff for all infrastructures
            TARIFF = 0.00525 * t_scale  #€/kWh-transported or -stored (=0.175 €/kg H2, which is ~5% of future price of green H2, assuming 3.5 €/kg H2)
        
            #____Start of operations
            START_YEAR = 2030
            #____Depreciation period (Target year: ca. 2055, in line with the German proposal for "Armortisationskonten")
            DEPRECIATION_PERIOD = 30
            #____Averaged technical lifetime of plant components
            TECHNICAL_LIFETIME = 30
        
            #____Terminal value at the end of life
            TERMINAL_VALUE = 0
        
            #____Linear increase of capacity bookings
            #references for utilization:
            #____RMI (2024): "Oceans of opportunity", annex
            #____chrome-extension://efaidnbmnnnibpcajpcglclefindmkaj/https://energy.ec.europa.eu/system/files/2023-05/Quarterly%20Report%20on%20European%20Gas%20Markets%20report%20Q4%202022.pdf
            if Utilization == "Ramp-up":
                PEAK_UTILIZATION = 0.80
                START_UP_PHASE = 5  #in years
                utilization_curve_startup = np.linspace(0.5, PEAK_UTILIZATION, START_UP_PHASE)
                utilization_curve_constant = np.linspace(PEAK_UTILIZATION, PEAK_UTILIZATION, DEPRECIATION_PERIOD - START_UP_PHASE)
                utilization_curve = np.append(utilization_curve_startup, utilization_curve_constant)
            elif Utilization == "Low":
                utilization_curve = np.linspace(0.2, 0.2, DEPRECIATION_PERIOD)
            else:
                raise AttributeError("Unknown utilization argument.")
        
            if INFRASTRUCTURE == "Pipeline":
        
                #CAPEX and OPEX
                K_INVEST = np.zeros(shape=DEPRECIATION_PERIOD)
                #Initial investment costs for 1500 km of pipeline - chrome-extension://efaidnbmnnnibpcajpcglclefindmkaj/https://ehb.eu/files/downloads/EHB-2023-20-Nov-FINAL-design.pdf
                K_INVEST[0] = 4.488 * 1e+9 + 1.280 * 1e+9  #48"-Pipeline (60% new, 40% repurposed) + 2 x 160 MW compressor
                #Potential second-stage investment --> Discuss this option during on-site event!
                #K_INVEST[10] = 3.2*1e+9 + 320*1e+6 #36"-Pipeline (100% new) + 1 x 80 MW compressor    
        
                #O&M costs, including labour costs - https://ehb.eu/page/estimated-investment-cost
                OPEX = 67 * 1e+6
        
                #UTILIZATION
                #Khan, M.A., Young, C. and Layzell, D.B. (2021). The Techno-Economics of Hydrogen Pipelines. Transition Accelerator Technical Briefs Vol. 1, Issue 2, Pg. 1-40. ISSN 2564-1379.
        
                #____Max. pipeline throughput: 307.8*1e+6 kWh/day OR 9235 tons/day
                E_max = 307.8*1e+6*365
                E_in = E_max * utilization_curve #kWh hydrogen throughput
                #____Electricity price USD/kWh = No costs.
                K_E_in = 0
                #____Pipeline thoughput
                E_out = E_max * utilization_curve
                #____Hydrogen price in USD/kWh --> Service cost to transport hydrogen for 1000 km. --> Derived from SCENARIO: CAPACITY BOOKINGS = 80% constantly
                K_E_out = TARIFF
        
            elif INFRASTRUCTURE == "Terminal":
        
                #COST VALIDATION WITH MODEL FROM Tintemann (2023)
                #Terminal type: NH3, LH2, SNG
                energycarrier = Terminal_Type
                #Yearly energy import in TWh
                energysupply = 5  # TWh/year
                #Assuming ~37 tank turn per year (a ship load every 6 days and a capacity factor of 1.64) --> Derived from LNG-Brunsbüttel & Stade
                #____Brunsbüttel: Tank volume - 330.000 m³, Capacity - 10 Billion m³/year
                #____Stade: Tank volume (LNG) - 480.000 m³, Capacity (Natural gas, with lower density) - 13.3 Billion m³/year
                
                if energycarrier != "LOHC":
                    terminal_ella = tm.Core(energycarrier, energysupply)
                terminal_data = Terminal(energycarrier, energysupply)
                
                #COST CALCULATIONS
                if energycarrier == "LOHC":
                    #USE H2Global model for CAPEX/OPEX calculation
                    CAPEX_Terminal_no_conversion = terminal_data.get_capex_terminal()
                    OPEX_Terminal_no_conversion = terminal_data.get_opex_terminal()
                    CAPEX_conversion = terminal_data.get_capex_conversion()
                    OPEX_conversion = terminal_data.get_opex_conversion()
                    
                    CAPEX_with_conversion = CAPEX_Terminal_no_conversion + CAPEX_conversion
                    OPEX_with_conversion = OPEX_Terminal_no_conversion + OPEX_conversion
                    
                    tank_size = terminal_data.calculate_tank_volume()
                    print("Terminal tank size:", round(tank_size, 2), " m³")
                else:
                    #USE Ella Tintemanns model for CAPEX/OPEX calculation
                    CAPEX_with_conversion = terminal_ella.get_capex_terminal()
                    OPEX_with_conversion = terminal_ella.get_opex_terminal()
                    
                    if energycarrier == "SNG":
                        CAPEX_conversion = terminal_ella.reformer_.get_capex()
                        OPEX_conversion = terminal_ella.reformer_.get_e_costs() + terminal_ella.reformer_.get_co2_shipping_costs()
                    elif energycarrier == "NH3":
                        CAPEX_conversion = terminal_ella.cracker_.get_capex()
                        OPEX_conversion = terminal_ella.cracker_.get_e_costs() 
                    elif energycarrier == "LH2":
                        CAPEX_conversion = 0
                        OPEX_conversion = 0
                    else:
                        raise AttributeError("No such carrier defined.")
                     
                    tank_size = terminal_ella.tank_.volume
                    print("Terminal tank size:", round(tank_size, 2), " m³")
                
                
                if Conversion_Terminal:
                    CAPEX_temp = CAPEX_with_conversion
                    OPEX_temp = OPEX_with_conversion
                    print("Terminal CAPEX:", round(CAPEX_temp*1e-6, 2), " Million €")
                    print("Terminal OPEX:", round(OPEX_temp*1e-6, 2), " Million €")
                else:
                    CAPEX_temp = CAPEX_with_conversion - CAPEX_conversion
                    OPEX_temp = OPEX_with_conversion - OPEX_conversion
                    print("Terminal CAPEX without conversion:", round(CAPEX_temp*1e-6, 2), " Million €")
                    print("Terminal OPEX without conversion:", round(OPEX_temp*1e-6, 2), " Million €")
        
                
                #CAPEX and OPEX
                K_INVEST = np.zeros(shape=DEPRECIATION_PERIOD)
                K_INVEST[0] = CAPEX_temp
        
                #____Operational Costs
                OPEX = OPEX_temp
        
                #UTILIZATION
                #____Max. storage capacity: Tank volume * maximum tank turns per year
                #REVENUE MODEL: Selling a maximum amount of feed-in energy, 
                #which can be stored a maximum of 9 days.
                E_max = energysupply * 1e+9
        
                E_in = E_max * utilization_curve  #kWh throughput
                #____Electricity price USD/kWh = No costs.
                K_E_in = 0
                #____Pipeline thoughput
                E_out = E_max * utilization_curve
                #____Storage price in €/kWh
                K_E_out = TARIFF  #€/kWh-stored for a maximum duration of ~9 days (=40 tank turns)
        
            elif INFRASTRUCTURE == "Storage":
                
                #DOI: doi.org/10.1016/j.ijhydene.2023.07.074
                
                if Storage_Type == "Single-turn":
                    max_tank_turns = 1  #Seasonal storage
                    specific_investment_costs = 450 #€/MWh for depleted gas fields/aquifers
                    capacity = 145 #GWh working gas
                    CAPEX = capacity*1e+3 * specific_investment_costs
                    
                elif Storage_Type == "Multi-turn":
                    max_tank_turns = 3.5  #Seasonal storage
                    specific_investment_costs = 900 #€/MWh for salt cavern project
                    capacity = 25 #GWh working gas
                    CAPEX = capacity*1e+3 * specific_investment_costs
                
                else:
                    raise AttributeError("Unknown storage type")
                
                #CAPEX and OPEX
                #REFERENCE: Gas Infrastructure Europe, 04.2024, Why European Underground Hydrogen Storage Needs Should Be Fulfilled
                K_INVEST = np.zeros(shape=DEPRECIATION_PERIOD)
                K_INVEST[0] = CAPEX
                OPEX = CAPEX*0.04
        
                #UTILIZATION
                #____Max. storage capacity
                E_max = (capacity * max_tank_turns) * 1e+6  #in kWh
                E_in = E_max * utilization_curve  #kWh hydrogen throughput
                #____Electricity price USD/kWh = No costs.
                K_E_in = 0
                #____Pipeline throughput
                E_out = E_max * utilization_curve
                #____Storage price in €/kWh-stored for a maximum duration of ~1 month
                K_E_out = TARIFF  #€/kWh-stored
        
            else:
                raise ValueError("Unknown infrastructure type.")
        
            #FINANCIAL METRICS
            #____Equity: Reference: RMI (2024): "Oceans of opportunity", annex
            EQUITY_SHARE = 0.3
            #____Country risk (see Damodaran)
            #COUNTRY_RISK_PREMIUM=0 # Europe
            #____Interest
            INTEREST = 0.04 #can be derived from return on corporate bonds (e.g. BBB-rated bonds)
            #____Tax rate
            #CORPORATE_TAX_RATE=0.2
        
            #DEFINE NO RISK PARAMETERS
            E_out_max_array = np.zeros(shape=DEPRECIATION_PERIOD)
            E_out_max_array[:] = E_max
        
            country = "INFRASTRUCTURE"
            # "Morocco", "Kenya", "Chile", "Italy", "Spain", "Australia", "Austria", "France", "Japan", "South Africa", "INFRASTRUCTURE"
        
            country_risk = Country_Risk.country_parameters[country]
        
            # Definisci le variabili con i valori specifici del paese
            COUNTRY_RISK_PREMIUM = country_risk["COUNTRY_RISK_PREMIUM"]
            CORPORATE_TAX_RATE = country_risk["CORPORATE_TAX_RATE"]
            R_FREE = 0.045  # This one was the one used in the Infrastructure
            ERP_MATURE = 0.065  # This one was the one used in the Infrastructure
        
            RISK_PARAM = {
                "K_INVEST": {
                    "distribution": "normal",
                    "scale": K_INVEST * 0.1,
                    "limit": {
                        "min": K_INVEST * 0.5,
                        "max": K_INVEST * 3
                    },
                    "correlation": {
                        "E_out" : 0.5,
                        "OPEX" : 0.5
                    }
                },
                "OPEX" : {
                    "distribution": "normal",
                    "scale": OPEX * 0.2,
                    "limit": {
                        "min": OPEX * 0.5,
                        "max": OPEX * 3
                    },
                    "correlation": {
                        "K_INVEST" : 0.5,
                        "E_out" : 0.5
                    }
                },
                "E_out": {
                    "distribution": "normal",
                    "scale": E_out * 0.1,
                    "limit": {
                        "min": E_out * 0.5,
                        "max": E_out_max_array
                    },
                    "correlation": {
                        "K_INVEST" : 0.5,
                        "OPEX" : 0.5
                    }
                }
            }
        
            # Scenario calculations
        
            #Initialize Project-object
            p_example = pp.Project(
                E_in=E_in,
                E_out=E_out,
                K_E_in=K_E_in,
                K_E_out=K_E_out,
                K_INVEST=K_INVEST,
                TERMINAL_VALUE=TERMINAL_VALUE,
                TECHNICAL_LIFETIME=TECHNICAL_LIFETIME,
                OPEX=OPEX,
                EQUITY_SHARE=EQUITY_SHARE,
                COUNTRY_RISK_PREMIUM=COUNTRY_RISK_PREMIUM,
                INTEREST=INTEREST,
                CORPORATE_TAX_RATE=CORPORATE_TAX_RATE,
                RISK_PARAM=RISK_PARAM,
                OBSERVE_PAST=0,
                ENDOGENOUS_PROJECT_RISK=ENDOGENOUS_PROJECT_RISK,
                REPAYMENT_PERIOD=DEPRECIATION_PERIOD,
                R_FREE=R_FREE,
                ERP_MATURE=ERP_MATURE,
            )
        
            #CALCULATION OF FINANCIAL METRICS
        
            # Calculate WACC for further calculations.
            WACC = p_example.get_WACC()
            print("____WACC:", WACC.mean())
        
            # Calculate net present value (NPV)
            NPV = p_example.get_NPV(WACC)
            print("____mean NPV:", round(NPV.mean() * 1e-6, 2), " Million €")
        
            LCOE = p_example.get_LCOE(WACC)
            print("____LCOE:", LCOE.mean())
        
            try:
                IRR = p_example.get_IRR(INITIAL_VALUE=0.05)
                print("____IRR:", IRR.mean())
        
                # Calculate the value-at-risk (VaR)
                VaR = p_example.get_VaR(IRR)
                print("____VaR:", VaR)
            except:
                print("____IRR and VaR cannot be determined. - Probably too low.")
        
        
            # Calculate subsidy demand for each instrument
            if NPV.mean() > 0:
                SUBSIDY_DICT["t_scale_" + str(t_scale)]["CAPEX"] = 0
                SUBSIDY_DICT["t_scale_" + str(t_scale)]["Fixed_Premium"] = 0
                SUBSIDY_DICT["t_scale_" + str(t_scale)]["Anchor_A"] = 0
                SUBSIDY_DICT["t_scale_" + str(t_scale)]["Anchor_B"] = 0
                SUBSIDY_DICT["t_scale_" + str(t_scale)]["CFD"] = 0
                
            else:
                # Calculate subsidy demand for each instrument
                #CAPEX Funding
                subsidy_CAPEX = p_example.get_subsidy(npv_target=0, depreciation_target=DEPRECIATION_PERIOD,
                                                      subsidy_scheme="INITIAL", WACC=WACC)
                SUBSIDY_DICT["t_scale_" + str(t_scale)]["CAPEX"] = subsidy_CAPEX.mean()
        
                print("CAPEX")
                print("____TOTAL CAPEX:", round(subsidy_CAPEX.mean() * 1e-6, 1), " Million €")
        
                #FIXED_PREMIUM FUNDING
                subsidy_FIXED_PREMIUM = p_example.get_subsidy(npv_target=0, depreciation_target=DEPRECIATION_PERIOD,
                                                              subsidy_scheme="FIXED_PREMIUM", WACC=WACC)
                SUBSIDY_DICT["t_scale_" + str(t_scale)]["Fixed_Premium"] = subsidy_FIXED_PREMIUM.mean() * E_out
        
                print("FIXED PREMIUM")
                print("____TOTAL FP:", round((subsidy_FIXED_PREMIUM.mean() * E_out).sum() * 1e-6, 3), " Million €")
                print("____FP amount:", round(subsidy_FIXED_PREMIUM.mean(), 3), " €/kWh")
                #print("____Mean fixed premium:", round(subsidy_FIXED_PREMIUM.mean()*33.33, 3), " €/kg-H2")
        
                #ANNUALLY CONSTANT Funding --> Can be used to derive H2Global mechanism or any kind of long-term offtake agreement + subsidy
                subsidy_ANNUALLY_CONSTANT = p_example.get_subsidy(npv_target=0, depreciation_target=DEPRECIATION_PERIOD,
                                                                  subsidy_scheme="ANNUALLY_CONSTANT", WACC=WACC)
                ANCHOR_CAPACITY_BOOKING = p_example.get_subsidy(npv_target=0, depreciation_target=DEPRECIATION_PERIOD,
                                                                subsidy_scheme="ANCHOR_CAPACITY", WACC=WACC, E_OUT_MAX=E_max)
                subsidy_ANCHOR_CAPACITY_BOOKING = ANCHOR_CAPACITY_BOOKING[0].copy()
                ratio_ANCHOR_CAPACITY_BOOKING = ANCHOR_CAPACITY_BOOKING[1].copy()
        
                subsidy_ANNUALLY_CONSTANT_ARRAY = np.zeros(shape=DEPRECIATION_PERIOD)
                subsidy_ANNUALLY_CONSTANT_ARRAY[:] = subsidy_ANNUALLY_CONSTANT.mean()
                SUBSIDY_DICT["t_scale_" + str(t_scale)]["Anchor_A"] = subsidy_ANNUALLY_CONSTANT_ARRAY
                SUBSIDY_DICT["t_scale_" + str(t_scale)]["Anchor_B"] = ANCHOR_CAPACITY_BOOKING[0].mean(axis=1)
        
                print("ANCHOR_CAPACITY")
                #print("_____Mean annually constant funding (offtake-agreement like subsidy):", round(subsidy_ANNUALLY_CONSTANT.mean()*1e-6, 1), " Million €")
                print("_____ACB-A:", round(subsidy_ANNUALLY_CONSTANT.mean() * DEPRECIATION_PERIOD * 1e-6, 1), " Million €")
                print("_____ACB-B:", round(subsidy_ANCHOR_CAPACITY_BOOKING.sum(axis=0).mean() * 1e-6, 2), " Million €")
                print("_____ACB-B_RATIO",
                      round(ratio_ANCHOR_CAPACITY_BOOKING[ratio_ANCHOR_CAPACITY_BOOKING > 0].mean() * 100, 1), " %")
        
                #CFD Funding
                print("CFD")
                subsidy_CFD = p_example.get_subsidy(npv_target=0, depreciation_target=DEPRECIATION_PERIOD, subsidy_scheme="CFD",
                                                    WACC=WACC)
                #print("Mean annual subsidy over full project period under CfD (considering repayments, if there are any):", round(subsidy_CFD.mean()*1e-6, 1), " Million €")
                print("____TOTAL CDF:", round(subsidy_CFD.sum() * 1e-6, 1), " Million €")
                SUBSIDY_DICT["t_scale_" + str(t_scale)]["CFD"] = subsidy_CFD
        
                #calculate cashflows
                CASHFLOWS = p_example.get_cashflows(WACC)
                SUMMED_CASHFLOW = CASHFLOWS[0] + CASHFLOWS[2]  #operating + non-operating cashflow
                CASHFLOW_DICT["t_scale_" + str(t_scale)]["NO_SUBSIDY"] = SUMMED_CASHFLOW
        
                for s in list(SUBSIDY_DICT["t_scale_" + str(t_scale)]):
                    if s == "CAPEX":
                        K_INVEST_SUBSIDY = K_INVEST - SUBSIDY_DICT["t_scale_" + str(t_scale)][s]
                        #CAPEX subsidy must be analyzed separately, because it's not an OPEX subsidy.
                        p_CAPEX_subsidy = pp.Project(
                            E_in=E_in,
                            E_out=E_out,
                            K_E_in=K_E_in,
                            K_E_out=K_E_out,
                            K_INVEST=K_INVEST_SUBSIDY,
                            TERMINAL_VALUE=TERMINAL_VALUE,
                            TECHNICAL_LIFETIME=TECHNICAL_LIFETIME,
                            OPEX=OPEX,
                            EQUITY_SHARE=EQUITY_SHARE,
                            COUNTRY_RISK_PREMIUM=COUNTRY_RISK_PREMIUM,
                            INTEREST=INTEREST,
                            CORPORATE_TAX_RATE=CORPORATE_TAX_RATE,
                            RISK_PARAM=RISK_PARAM,
                            OBSERVE_PAST=0,
                            ENDOGENOUS_PROJECT_RISK=False,
                            REPAYMENT_PERIOD=DEPRECIATION_PERIOD,
                            R_FREE=R_FREE,
                            ERP_MATURE=ERP_MATURE,
                        )
        
                        WACC_CAPEX_SUBSIDY = p_CAPEX_subsidy.get_WACC()
                        CASHFLOWS_CAPEX_SUBSIDY = p_CAPEX_subsidy.get_cashflows(WACC_CAPEX_SUBSIDY)
                        SUMMED_CASHFLOW_CAPEX_SUBSIDY = CASHFLOWS_CAPEX_SUBSIDY[0] + CASHFLOWS_CAPEX_SUBSIDY[
                            2]  #operating + non-operating cashflow
                        CASHFLOW_DICT["t_scale_" + str(t_scale)][s] = SUMMED_CASHFLOW_CAPEX_SUBSIDY
                    else:
                        CASHFLOW_NO_SUBSIDY = CASHFLOW_DICT["t_scale_" + str(t_scale)]["NO_SUBSIDY"]
                        SUBSIDY = SUBSIDY_DICT["t_scale_" + str(t_scale)][s]
                        CASHFLOW_DICT["t_scale_" + str(t_scale)][s] = CASHFLOW_NO_SUBSIDY + SUBSIDY
            
            DICT_RESULTS["t_scale_" + str(t_scale)][Utilization][str(ENDOGENOUS_PROJECT_RISK)] = {
                "WACC": WACC,
                "NPV": NPV.mean(),
                "LCOE": LCOE.mean(),
                "IRR": IRR.mean(),
                "VaR": VaR,
                "Tariff": TARIFF,
                "Subsidy_CAPEX": SUBSIDY_DICT["t_scale_" + str(t_scale)]["CAPEX"],
                "Subsidy_Fixed_Premium": SUBSIDY_DICT["t_scale_" + str(t_scale)]["Fixed_Premium"],
                "Subsidy_ANCHOR_A": SUBSIDY_DICT["t_scale_" + str(t_scale)]["Anchor_A"],
                "Subsidy_ANCHOR_B": SUBSIDY_DICT["t_scale_" + str(t_scale)]["Anchor_B"],
                "Subsidy_CFD": SUBSIDY_DICT["t_scale_" + str(t_scale)]["CFD"],
                }
    

#%%
#STORING RESULTS TO FILE
if STORE_RESULTS:
    # File path to the existing Excel file
    if INFRASTRUCTURE == "Terminal":
        sheet_name = INFRASTRUCTURE + "_"  + Terminal_Type + "_" + str(Conversion_Terminal) + "_" + Utilization
    elif INFRASTRUCTURE == "Storage":
        sheet_name = INFRASTRUCTURE + "_"  + Storage_Type + "_" + Utilization
    else:
        sheet_name = INFRASTRUCTURE + "_"  + Utilization
    
    index_df = []
    #iterate over the SCALE of the tariff
    for s in list(DICT_RESULTS):
        #iterate over the UTILIZATION scenario
        for u in list(DICT_RESULTS["t_scale_" + str(t_scale)]):
            #iterate over the endogenous project risk
            for e in list(DICT_RESULTS["t_scale_" + str(t_scale)][Utilization]):
                index_df.append(s + "_" + u + "_" + e)
    
    
    columns_df = list(DICT_RESULTS["t_scale_" + str(1)][Utilization][str(ENDOGENOUS_PROJECT_RISK)])
    
    RESULTS_DF = pd.DataFrame(
        columns=columns_df,
        index=index_df
        )
    
    for s in list(DICT_RESULTS):
        #iterate over the UTILIZATION scenario
        for u in list(DICT_RESULTS["t_scale_" + str(t_scale)]):
            #iterate over the endogenous project risk
            for e in list(DICT_RESULTS["t_scale_" + str(t_scale)][Utilization]):
                row = s + "_" + u + "_" + e
                for col in RESULTS_DF.columns:
                    RESULTS_DF.loc[row, col] = DICT_RESULTS[s][u][e][col]
       
    # Write the new data to the Excel file, overwriting the existing data
    with pd.ExcelWriter(FILE_PATH, engine='openpyxl', mode='a') as writer:
        RESULTS_DF.to_excel(writer, sheet_name=sheet_name, index=True)

#%% Print out cashflow analysis
for t_scale in [1, 2, 4]:
    if len(list(CASHFLOW_DICT["t_scale_" + str(t_scale)])) == 0:
        continue
    print("TARIFF_SCENARIO: ", str(t_scale))
    CASHFLOW_NEG_NO_SUBSIDY = CASHFLOW_DICT["t_scale_" + str(t_scale)]["NO_SUBSIDY"].copy()
    CASHFLOW_NEG_NO_SUBSIDY[CASHFLOW_NEG_NO_SUBSIDY > 0] = 0
    CASHFLOW_NEG_NO_SUBSIDY_SUM = CASHFLOW_NEG_NO_SUBSIDY.sum()
    for s in list(CASHFLOW_DICT["t_scale_" + str(t_scale)]):
        print("____SUBSIDY: ", s)
        print("________RATIO NEGATIVE CASHFLOW:")
        CASHFLOW_NEG = CASHFLOW_DICT["t_scale_" + str(t_scale)][s].copy()
        CASHFLOW_NEG[CASHFLOW_NEG > 0] = 0
        CASHFLOW_NEG_SUM = CASHFLOW_NEG.sum()
        RATIO_NEG_CASHFLOW = CASHFLOW_NEG_SUM / CASHFLOW_NEG_NO_SUBSIDY_SUM
        print("        ", round(RATIO_NEG_CASHFLOW * 100, 0), "%")

#%% Visualize annual non-discounted cashflows   
LIFETIME_TEMP = TECHNICAL_LIFETIME
years = np.arange(START_YEAR, LIFETIME_TEMP + START_YEAR)
OCF, OCF_std, NOCF, NOCF_std = p_example.get_cashflows(WACC)

#CASHFLOW BALANCE
CF = OCF + NOCF
CF_STD = OCF_std + NOCF_std

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

print("____WACC:", round(WACC, 2), "%")
print("____NPV:", round(NPV.mean() * 1e-6, 2), " USD Million")
print("____VaR:", round(VaR * 1e-6, 2), " USD Million")

#%% Visualize development of NPV over project lifetime

LIFETIME_TEMP = TECHNICAL_LIFETIME
WACC_TEMP = WACC

years = np.arange(LIFETIME_TEMP + 1)

#CASHFLOW
#____discounting cashflows
CF_discounted = OCF.copy()
CF_std_discounted = OCF_std.copy()
for t in range(LIFETIME_TEMP):
    CF_discounted[t] = OCF[t] / (1 + WACC_TEMP) ** t
    CF_std_discounted[t] = OCF_std[t] / (1 + WACC_TEMP) ** t

#ANNUAL NPV
NPV = np.zeros(LIFETIME_TEMP + 1)
#____initial invest in year "0"
for t in range(LIFETIME_TEMP):
    NPV[t] -= K_INVEST[t].mean()
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
delta_x = LIFETIME_TEMP + 1
ax.set_xlim(-0.5, LIFETIME_TEMP + 0.5)
offset_zero = 0.5 / delta_x
#offset_years = (delta_x-offset_zero*2)/LIFETIME_TEMP

#____derive second plot (positive cashflows)
for year_temp in range(1, LIFETIME_TEMP + 1):
    x_position = year_temp / delta_x
    ax.axhline(y=NPV_cum[year_temp],
               color='black',
               xmin=x_position - (1 / delta_x) * 0.4 + offset_zero,
               xmax=x_position + (1 / delta_x) * 0.4 + offset_zero,
               linestyle='-')

#____derive third and fourth plot (terminal values)
#Accounting for open principal payments.
REPAYMENT_PERIOD = DEPRECIATION_PERIOD
INVEST_TEMP = K_INVEST.mean()
if REPAYMENT_PERIOD > LIFETIME_TEMP:
    RATIO_OPEN_PRINCIPAL = 1 - (LIFETIME_TEMP / REPAYMENT_PERIOD)
    OPEN_PRINCIPAL = INVEST_TEMP * (1 - EQUITY_SHARE) * RATIO_OPEN_PRINCIPAL
else:
    OPEN_PRINCIPAL = 0
terminal_value = (TERMINAL_VALUE.mean() - OPEN_PRINCIPAL) / (1 + WACC_TEMP) ** LIFETIME_TEMP
plot_terminal_value = np.zeros(LIFETIME_TEMP + 1)
plot_npv = np.zeros(LIFETIME_TEMP + 1)

if NPV_cum[-1] < 0:
    if terminal_value + NPV_cum[-1] > 0:
        #plot positive NPV in green
        plot_npv[-1] = terminal_value + NPV_cum[-1]
        ax.bar(years, plot_npv, color='green', width=line_width, label="Positive NPV")
        #plot terminal value add on until NPV=0
        plot_terminal_value[-1] = -NPV_cum[-1]
        ax.bar(years, plot_terminal_value, bottom=NPV_cum[-1], color='grey', width=line_width,
               label="Terminal value-NPV")
    else:
        #plot negative NPV in red
        plot_npv[-1] = -(terminal_value + NPV_cum[-1])
        ax.bar(years, plot_npv, bottom=NPV_cum[-1] + terminal_value, color='red', width=line_width,
               label="Negative NPV")
        #plot terminal value add on until NPV=0
        plot_terminal_value[-1] = terminal_value
        ax.bar(years, plot_terminal_value, bottom=NPV_cum[-1], color='grey', width=line_width, label="Terminal value")
else:
    #plot terminal value on top of positive NPV in green 
    plot_npv[-1] = NPV_cum[-1] + terminal_value
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

print("____WACC:", round(WACC, 2), "%")
print("____NPV:", round(NPV.mean() * 1e-6, 2), " USD Million")
print("____VaR:", round(VaR * 1e-6, 2), " USD Million")
