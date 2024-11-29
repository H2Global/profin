# -*- coding: utf-8 -*-
"""
Created on Fri Mar 22 09:41:20 2024

@author: JulianReul
"""

import time
import numpy as np
import profin as pp
from terminal_config import Terminal
import terminal_model as tm
import pandas as pd
import scipy.optimize as so


#%% INPUT PARAMETERS

#Iterate the following scenario parameters manually
INFRASTRUCTURE = "Storage" # "Pipeline", "Terminal", "Storage", "Conversion"
Terminal_Type = "LH2" #NH3, LH2, SNG, LOHC
Storage_Type = "Multi-turn" #Single-turn
Storage_Tech = "Depleted-field" #Depleted-field; Salt-cavern
#____Country risk (see Damodaran)
COUNTRY_RISK_PREMIUM=0 # Europe: 0%, Moody's B1-countries: 6.5%, Damodaran
METHOD_PROJECT_RISK = "Deloitte" # #Reference

#Initialize storage dicts
SUBSIDY_DICT = {}
CASHFLOW_DICT = {}
STORE_RESULTS = True
FILE_PATH = "C:\\Users\\JulianReul.AzureAD\\H2Global\Outreach - General\\Working Groups\\01_WG Infrastructure\\05_Report\\Simulation_Results_FINAL.xlsx"
DICT_RESULTS = {}

print("INFRASTRUCTURE: ", INFRASTRUCTURE)
print("Terminal_Type: ", Terminal_Type)
print("Storage_Type: ", Storage_Type)
print("Storage_Tech: ", Storage_Tech)

NEUTRAL_TARIFF_DICT = {
    "Pipeline" : 0.0115,
    "Terminal" : {
        "NH3" : 0.0120,
        "LH2" : 0.0240,
        "SNG" : 0.0205,
        "LOHC" : 0.0017
        },
    "Conversion" : {
        "NH3" : 0.0420,
        "SNG" : 0.1660,
        "LOHC" : 0.0520
        },
    "Storage" : {
        "Single-turn" : {
            "Salt-cavern" : 0.2250,
            "Depleted-field" : 0.1145
            },
        "Multi-turn" : {
            "Salt-cavern" : 0.0880,
            "Depleted-field" : 0.0440
            },
        } 
    }

for t_scale in [0.75, 1, 1.25]: 
    DICT_RESULTS["t_scale_" + str(t_scale)] = {}
    SUBSIDY_DICT["t_scale_" + str(t_scale)] = {}
    CASHFLOW_DICT["t_scale_" + str(t_scale)] = {}

    start_time = time.time()

    print("__________________________")
    print("__________________________")
    print("SCALE OF FUNDING TARIFF: ", t_scale)
    print("__________________________")
    print("__________________________")

    for Utilization in ["Ramp-up"]: #, "Ramp-up", "Low", 
    
        DICT_RESULTS["t_scale_" + str(t_scale)][Utilization] = {}
        SUBSIDY_DICT["t_scale_" + str(t_scale)][Utilization] = {}
        CASHFLOW_DICT["t_scale_" + str(t_scale)][Utilization] = {}

        DICT_RESULTS["t_scale_" + str(t_scale)][Utilization] = {}
        SUBSIDY_DICT["t_scale_" + str(t_scale)][Utilization] = {}
        CASHFLOW_DICT["t_scale_" + str(t_scale)][Utilization] = {}
                
        #GENERAL PROJECT DATA
        #____Tariff: Same tariff for all infrastructures
        if INFRASTRUCTURE == "Pipeline":
            NEUTRAL_TARIFF = NEUTRAL_TARIFF_DICT[INFRASTRUCTURE]
        elif INFRASTRUCTURE in ["Terminal", "Conversion"]:
            NEUTRAL_TARIFF = NEUTRAL_TARIFF_DICT[INFRASTRUCTURE][Terminal_Type]
        elif INFRASTRUCTURE == "Storage":
            NEUTRAL_TARIFF = NEUTRAL_TARIFF_DICT[INFRASTRUCTURE][Storage_Type][Storage_Tech]
        else:
            raise AttributeError("Unknown Scenario.")
        TARIFF = NEUTRAL_TARIFF * t_scale  #€/kWh-transported or -stored (=0.175 €/kg H2, which is ~5% of future price of green H2, assuming 3.5 €/kg H2)
    
        #____Start of operations
        START_YEAR = 2030
        #____Depreciation period (Target year: ca. 2050, in line with the German proposal for "Armortisationskonten")
        DEPRECIATION_PERIOD = 25
        
        #____Linear increase of capacity bookings
        #references for utilization:
        #____RMI (2024): "Oceans of opportunity", annex
        #____chrome-extension://efaidnbmnnnibpcajpcglclefindmkaj/https://energy.ec.europa.eu/system/files/2023-05/Quarterly%20Report%20on%20European%20Gas%20Markets%20report%20Q4%202022.pdf
        if Utilization == "Ramp-up":
            PEAK_UTILIZATION = 0.80
            if INFRASTRUCTURE in ["Pipeline", "Storage"]:
                START_UP_PHASE = 8  #in years
            else:
                START_UP_PHASE = 5  #in years
            utilization_curve_startup = np.linspace(0.5, PEAK_UTILIZATION, START_UP_PHASE)
            utilization_curve_constant = np.linspace(PEAK_UTILIZATION, PEAK_UTILIZATION, DEPRECIATION_PERIOD - START_UP_PHASE)
            utilization_curve = np.append(utilization_curve_startup, utilization_curve_constant)
        elif Utilization == "Low":
            utilization_curve = np.linspace(0.2, 0.2, DEPRECIATION_PERIOD)
        else:
            raise AttributeError("Unknown utilization argument.")
    
        if INFRASTRUCTURE == "Pipeline":
    
            #____Averaged technical lifetime of plant components
            TECHNICAL_LIFETIME = 25
    
            #CAPEX and OPEX
            K_INVEST = np.zeros(shape=DEPRECIATION_PERIOD)
            #Initial investment costs for 1500 km of pipeline - chrome-extension://efaidnbmnnnibpcajpcglclefindmkaj/https://ehb.eu/files/downloads/EHB-2023-20-Nov-FINAL-design.pdf
            K_INVEST[0] = 4.488 * 1e+9 + 1.280 * 1e+9  #48"-Pipeline (60% new, 40% repurposed) + 2 x 160 MW compressor
    
            #____Terminal value at the end of life
            SHARE_REST_VALUE = 1 - DEPRECIATION_PERIOD / TECHNICAL_LIFETIME
            TERMINAL_VALUE = K_INVEST[0] * SHARE_REST_VALUE   

    
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
    
            #____Averaged technical lifetime of plant components
            TECHNICAL_LIFETIME = 25
            
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
            terminal_matteo = Terminal(energycarrier, energysupply)
            
            #COST CALCULATIONS
            if energycarrier == "LOHC":
                #USE H2Global model for CAPEX/OPEX calculation
                CAPEX_temp = terminal_matteo.get_capex_terminal()
                OPEX_temp = terminal_matteo.get_opex_terminal()
                                    
                tank_size = terminal_matteo.calculate_tank_volume()
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
                 
                CAPEX_temp = CAPEX_with_conversion - CAPEX_conversion
                OPEX_temp = OPEX_with_conversion - OPEX_conversion
                 
                tank_size = terminal_ella.tank_.volume
                print("Terminal tank size:", round(tank_size, 2), " m³")
            
            print("Terminal CAPEX without conversion:", round(CAPEX_temp*1e-6, 2), " Million €")
            print("Terminal OPEX without conversion:", round(OPEX_temp*1e-6, 2), " Million €")
            
            #CAPEX and OPEX
            K_INVEST = np.zeros(shape=DEPRECIATION_PERIOD)
            K_INVEST[0] = CAPEX_temp
    
            #____Operational Costs
            OPEX = OPEX_temp
    
            #____Terminal value at the end of life
            SHARE_REST_VALUE = 1 - DEPRECIATION_PERIOD / TECHNICAL_LIFETIME
            TERMINAL_VALUE = K_INVEST[0] * SHARE_REST_VALUE   
    
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
    
        elif INFRASTRUCTURE == "Conversion":
            #____Averaged technical lifetime of plant components
            TECHNICAL_LIFETIME = 25
            cost_of_imported_energy = 0.1923 #€/kWh - from 1000 €/ton NH3

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
            terminal_matteo = Terminal(energycarrier, energysupply)
            
            terminal_matteo_LOHC = Terminal("LOHC", energysupply)
            energy_imported_LOHC = terminal_matteo_LOHC.calculate_energy_imported_carrier()
            
            #COST CALCULATIONS
            if energycarrier == "LOHC":
                #USE H2Global model for CAPEX/OPEX calculation
                CAPEX_temp = terminal_matteo.get_capex_conversion()
                OPEX_temp = terminal_matteo.get_opex_conversion()
            else:    
                if energycarrier == "SNG":
                    heat_demand_cracker = 0.49 #kWh SNG / kWh H2 --> Reference: https://www.sciencedirect.com/science/article/abs/pii/S1383586699000210#:~:text=Pressure%20swing%20adsorption%20(PSA)%20processes,the%20range%2070%E2%80%9385%25.
                    surplus_imported_energy = heat_demand_cracker*energysupply*1e+9 #kWh
                    cost_of_surplus_imported_energy = surplus_imported_energy*cost_of_imported_energy
                    print("Cost of surplus imported energy [€ Mio.]:", cost_of_surplus_imported_energy*1e-6)
                    
                    CAPEX_temp = terminal_ella.reformer_.get_capex()
                    OPEX_temp = terminal_ella.reformer_.get_e_costs() + terminal_ella.reformer_.get_co2_shipping_costs() + 0.03*CAPEX_temp + cost_of_surplus_imported_energy
                elif energycarrier == "NH3":
                    heat_demand_cracker = 0.1178 #kWh NH3 / kWh H2 --> Reference from Rouvenhorst (Ammonia Society)
                    surplus_imported_energy = heat_demand_cracker*energysupply*1e+9 #kWh
                    cost_of_surplus_imported_energy = surplus_imported_energy*cost_of_imported_energy
                    print("Cost of surplus imported energy [€ Mio.]:", cost_of_surplus_imported_energy*1e-6)
                    
                    CAPEX_temp = terminal_ella.cracker_.get_capex()
                    OPEX_temp = terminal_ella.cracker_.get_e_costs() + 0.03*CAPEX_temp + cost_of_surplus_imported_energy
                elif energycarrier == "LH2":
                    #No conversion necessary for LH2
                    continue
                else:
                    raise AttributeError("No such carrier defined.")
            
            print("Conversion CAPEX:", round(CAPEX_temp*1e-6, 2), " Million €")
            print("Conversion OPEX:", round(OPEX_temp*1e-6, 2), " Million €")
            
            #CAPEX and OPEX
            K_INVEST = np.zeros(shape=DEPRECIATION_PERIOD)
            K_INVEST[0] = CAPEX_temp
    
            #____Operational Costs
            OPEX = OPEX_temp
    
            #____Terminal value at the end of life
            SHARE_REST_VALUE = 1 - DEPRECIATION_PERIOD / TECHNICAL_LIFETIME
            TERMINAL_VALUE = K_INVEST[0] * SHARE_REST_VALUE   
    
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
            
            #____Averaged technical lifetime of plant components
            TECHNICAL_LIFETIME = 50

            #DOI: doi.org/10.1016/j.ijhydene.2023.07.074
            
            if Storage_Type == "Single-turn":
                
                if Storage_Tech == "Salt-cavern":
                    specific_investment_costs = 900 #€/MWh for salt cavern project
                    capacity = 25 #GWh working gas
                if Storage_Tech == "Depleted-field":
                    specific_investment_costs = 450 #€/MWh for depleted gas fields/aquifers
                    capacity = 145 #GWh working gas
                    
                max_tank_turns = 1  #Seasonal storage
                CAPEX = capacity*1e+3 * specific_investment_costs
                OPEX = CAPEX*0.04 #Frontier study
                
            elif Storage_Type == "Multi-turn":
                
                if Storage_Tech == "Salt-cavern":
                    specific_investment_costs = 900 #€/MWh for salt cavern project
                    capacity = 25 #GWh working gas
                if Storage_Tech == "Depleted-field":
                    specific_investment_costs = 450 #€/MWh for depleted gas fields/aquifers
                    capacity = 145 #GWh working gas
                    
                max_tank_turns = 3.5  #Seasonal storage
                CAPEX = capacity*1e+3 * specific_investment_costs
                OPEX = CAPEX*0.1 #Comment by RAG Austria that OPEX is higher for multi-turn!
            
            else:
                raise AttributeError("Unknown storage type")
            
            #CAPEX and OPEX
            #REFERENCE: Gas Infrastructure Europe, 04.2024, Why European Underground Hydrogen Storage Needs Should Be Fulfilled
            K_INVEST = np.zeros(shape=DEPRECIATION_PERIOD)
            K_INVEST[0] = CAPEX
    
            print("CAPEX: ", CAPEX)
            print("OPEX: ", OPEX)

            #____Terminal value at the end of life
            SHARE_REST_VALUE = 1 - DEPRECIATION_PERIOD / TECHNICAL_LIFETIME
            TERMINAL_VALUE = K_INVEST[0] * SHARE_REST_VALUE   
    
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
        #____Interest
        INTEREST = 0.05 #Long-term SWAP-rate (=3%) + 2% credit margin
        #____Tax rate
        CORPORATE_TAX_RATE=0.2
    
        #DEFINE NO RISK PARAMETERS
        E_out_max_array = np.zeros(shape=DEPRECIATION_PERIOD)
        E_out_max_array[:] = E_max
    
        #country = "INFRASTRUCTURE"
        # "Morocco", "Kenya", "Chile", "Italy", "Spain", "Australia", "Austria", "France", "Japan", "South Africa", "INFRASTRUCTURE"
        #country_risk = Country_Risk.country_parameters[country]
    
        # Definisci le variabili con i valori specifici del paese
        COUNTRY_RISK_PREMIUM = COUNTRY_RISK_PREMIUM
        CORPORATE_TAX_RATE = CORPORATE_TAX_RATE
        R_FREE = 0.045  # This one was the one used in the Infrastructure
        ERP_MATURE = 0.065  # This one was the one used in the Infrastructure
    
        RISK_PARAM = {
            "K_INVEST": {
                "distribution": "normal",
                "scale": K_INVEST * 0.1,
                "limit": {
                    "min": K_INVEST / 100,
                    "max": K_INVEST * 100
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
                    "min": OPEX / 100,
                    "max": OPEX * 100
                },
                "correlation": {
                    "K_INVEST" : 0.5,
                    "E_out" : 0.5
                }
            },
            "E_out": {
                "distribution": "normal",
                "scale": E_out * 0.2,
                "limit": {
                    "min": E_out / 100,
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
            E_in=E_in, #Annual energy consumption in kWh
            E_out=E_out, #Annual production in kWh
            K_E_in=K_E_in, #Average energy purchase price
            K_E_out=K_E_out, #Average energy sales price
            K_INVEST=K_INVEST, #Total investment costs (also provided as an array over depreciation period)
            TERMINAL_VALUE=TERMINAL_VALUE, #Terminal value
            DEPRECIATION_PERIOD=DEPRECIATION_PERIOD, #25 years?
            OPEX=OPEX, #Total operational costs (also possible to provide in array-form)
            EQUITY_SHARE=EQUITY_SHARE,
            COUNTRY_RISK_PREMIUM=COUNTRY_RISK_PREMIUM,
            INTEREST=INTEREST,
            CORPORATE_TAX_RATE=CORPORATE_TAX_RATE,
            RISK_PARAM=RISK_PARAM,
            OBSERVE_PAST=0,
            ENDOGENOUS_PROJECT_RISK=True,
            R_FREE=R_FREE,
            ERP_MATURE=ERP_MATURE,
            TECHNICAL_LIFETIME=TECHNICAL_LIFETIME
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
    
    
        DICT_RESULTS["t_scale_" + str(t_scale)][Utilization] = {
            "CAPEX" : K_INVEST[0],
            "WACC": WACC,
            "NPV": NPV.mean(),
            "LCOE": LCOE.mean(),
            "IRR": IRR.mean(),
            "IRR_MINUS_WACC" : IRR.mean() - WACC,
            "VaR": VaR,
            "Tariff": TARIFF
            }
            
        ######                                                        ######
        ###### CALCULATE FINANCIAL METRICS WITH PRE-DEFINED SUBSIDIES ######
        ######                                                        ######
        if Utilization == "Low":
            continue
        else:
            for s in ["CAPEX", "ACB", "FP", "CFD"]:
                
                print("Subsidy:", s)
                
                RISK_PARAM_SUBSIDY = RISK_PARAM.copy()
                
                if s == "CAPEX":
                    #Assume 40% of CAPEX as subsidy
                    subsidy = K_INVEST*0.4
                    RISK_PARAM_SUBSIDY["K_INVEST"]["scale"] = (K_INVEST-subsidy)*0.1
                    
                elif s == "ACB":
                    #Assume 10% of CAPEX as subsidy, distributed over the depr. period
                    annual_funding = (K_INVEST[0]*0.4)/DEPRECIATION_PERIOD
                    subsidy = np.linspace(annual_funding,annual_funding,DEPRECIATION_PERIOD)
                    
                elif s == "FP":
                    total_funding = K_INVEST[0]*0.4
                    def get_FP(FP, subsidy, E_out):
                        return subsidy-(E_out*FP).sum()
                    x_init = 0.001
                    FP = so.fsolve(get_FP, x_init, args=(total_funding,E_out))
                    subsidy = FP*E_out
                    
                elif s == "CFD":
                    subsidy = p_example.get_subsidy(0, DEPRECIATION_PERIOD, "CFD", WACC)
                    RISK_PARAM_SUBSIDY["K_INVEST"]["scale"] = 0
                    RISK_PARAM_SUBSIDY["OPEX"]["scale"] = 0
                    RISK_PARAM_SUBSIDY["E_out"]["scale"] = 0
                    
                else:
                    raise AttributeError("No such subsidy scheme implemented.")
                            
                # Scenario calculations
            
                #Initialize Project-object
                p_subsidy = pp.Project(
                    E_in=E_in,
                    E_out=E_out,
                    K_E_in=K_E_in,
                    K_E_out=K_E_out,
                    K_INVEST=K_INVEST,
                    TERMINAL_VALUE=TERMINAL_VALUE,
                    DEPRECIATION_PERIOD=DEPRECIATION_PERIOD,
                    OPEX=OPEX,
                    EQUITY_SHARE=EQUITY_SHARE,
                    COUNTRY_RISK_PREMIUM=COUNTRY_RISK_PREMIUM,
                    INTEREST=INTEREST,
                    CORPORATE_TAX_RATE=CORPORATE_TAX_RATE,
                    RISK_PARAM=RISK_PARAM_SUBSIDY,
                    OBSERVE_PAST=0,
                    ENDOGENOUS_PROJECT_RISK=True,
                    TECHNICAL_LIFETIME=TECHNICAL_LIFETIME,
                    R_FREE=R_FREE,
                    ERP_MATURE=ERP_MATURE,
                    SUBSIDY=subsidy
                )
            
                #CALCULATION OF FINANCIAL METRICS
            
                # Calculate WACC for further calculations.
                if METHOD_PROJECT_RISK == "Deloitte":
                    WACC_SUBSIDY = p_subsidy.get_WACC()
                elif METHOD_PROJECT_RISK == "Reference":
                    WACC_SUBSIDY = p_subsidy.get_WACC(IRR_REF=IRR)
                else:
                    raise AttributeError("Method not yet defined.")
                print("____WACC_SUBSIDY:", WACC_SUBSIDY.mean())
            
                # Calculate net present value (NPV)
                NPV_SUBSIDY = p_subsidy.get_NPV(WACC_SUBSIDY)
                print("____mean NPV_SUBSIDY:", round(NPV_SUBSIDY.mean() * 1e-6, 2), " Million €")
            
                LCOE_SUBSIDY = p_subsidy.get_LCOE(WACC_SUBSIDY)
                print("____LCOE_SUBSIDY:", LCOE_SUBSIDY.mean())
            
                try:
                    IRR_SUBSIDY = p_subsidy.get_IRR(INITIAL_VALUE=0.05)
                    print("____IRR_SUBSIDY:", IRR_SUBSIDY.mean())        
                except:
                    print("____IRR cannot be determined. - Probably too low.")
                
                #Discount subsidy:
                subsidy_total = subsidy.sum()
                subsidy_discounted = []
                inflation = 0.03 #long-term SWAP rate
                for t in range(len(subsidy)):
                    annual_sub_discounted = subsidy[t]/(1+inflation)**t
                    subsidy_discounted.append(annual_sub_discounted)
                
                subsidy_discounted_array = np.array(subsidy_discounted)
                subsidy_discounted_total = subsidy_discounted_array.sum()
                
                #UNIT: DELTA per € Billion
                efficiency_IRR = (IRR_SUBSIDY-IRR).mean() / (subsidy_discounted_array.sum()*1e-9)
                efficiency_WACC = (WACC_SUBSIDY-WACC) / (subsidy_discounted_array.sum()*1e-9)
                
                # Calculate subsidy demand for each instrument
                SUBSIDY_DICT["t_scale_" + str(t_scale)][Utilization][s] = {
                    "subsidy" : subsidy_total,
                    "subsidy_dicounted" : subsidy_discounted_total,
                    "efficiency_IRR" : efficiency_IRR,
                    "efficiency_WACC" : efficiency_WACC,
                    "WACC_SUBSIDY" : WACC_SUBSIDY,
                    "NPV_SUBSIDY" : NPV_SUBSIDY.mean(),
                    "LCOE_SUBSIDY" : LCOE_SUBSIDY.mean(),
                    "IRR_SUBSIDY" : IRR_SUBSIDY.mean(),
                    "IRR_MINUS_WACC_SUBSIDY" : IRR_SUBSIDY.mean() - WACC_SUBSIDY
                    }
            
    
    end_time = time.time()
    delta_time = end_time - start_time
    print("______ELAPSED TIME FOR SINGLE CYCLE: ", delta_time, " sec.")


 #%%
#STORING RESULTS TO FILE
if STORE_RESULTS:
    # File path to the existing Excel file
    if INFRASTRUCTURE == "Terminal":
        sheet_name = INFRASTRUCTURE + "_"  + Terminal_Type
    elif INFRASTRUCTURE == "Conversion":
        sheet_name = INFRASTRUCTURE + "_"  + Terminal_Type
    elif INFRASTRUCTURE == "Storage":
        sheet_name = INFRASTRUCTURE + "_"  + Storage_Type + "_" + Storage_Tech
    else:
        sheet_name = INFRASTRUCTURE
    
    index_df = []
    #iterate over the SCALE of the tariff
    for s in list(DICT_RESULTS):
        #iterate over the UTILIZATION scenario
        for u in list(DICT_RESULTS["t_scale_" + str(t_scale)]):
            index_df.append(s + "_" + u)   
    
    #create columns for storing base data (columns_DICT) and subsidy data (columns_SUB)
    columns_DICT = list(DICT_RESULTS["t_scale_" + str(t_scale)][Utilization])
    columns_SUB = []
    columns_df = columns_DICT.copy()
    
    if Utilization == "Ramp-up":
        for sub in ["CAPEX", "ACB", "FP", "CFD"]:
            list_temp = list(SUBSIDY_DICT["t_scale_" + str(t_scale)][Utilization][sub])
            new_cols = [sub + "_" + l for l in list_temp]
            columns_df += new_cols
            columns_SUB += new_cols
        
    RESULTS_DF = pd.DataFrame(
        columns=columns_df,
        index=index_df
        )
    
    #iterature over scale
    for s in list(DICT_RESULTS):
        #iterate over the UTILIZATION scenario
        for u in list(DICT_RESULTS["t_scale_" + str(t_scale)]):
            row = s + "_" + u
            for col_d in columns_DICT:
                RESULTS_DF.loc[row, col_d] = DICT_RESULTS[s][u][col_d]
            if u == "Low":
                #No subsidies are calculated for "Low" utilization scenarios.
                continue
            else:
                for sub in ["CAPEX", "ACB", "FP", "CFD"]:
                    columns_SUB_ind = list(SUBSIDY_DICT[s][u][sub])
                    for col_s in columns_SUB_ind:
                        col_s_write = sub + "_" + col_s
                        RESULTS_DF.loc[row, col_s_write] = SUBSIDY_DICT[s][u][sub][col_s]
       
    # Write the new data to the Excel file, overwriting the existing data
    with pd.ExcelWriter(FILE_PATH, engine='openpyxl', mode='a') as writer:
        RESULTS_DF.to_excel(writer, sheet_name=sheet_name, index=True)
        
#%% Visualize development of NPV aver project lifetime
from matplotlib import pyplot as plt
    
LIFETIME_TEMP = TECHNICAL_LIFETIME
WACC_TEMP = WACC

years = np.arange(DEPRECIATION_PERIOD+1)

operating_cashflow, operating_cashflow_std, non_operating_cashflow, non_operating_cashflow_std = p_example.get_cashflows(WACC)

#CASHFLOW
OCF = operating_cashflow
OCF_std = operating_cashflow_std
#____discounting cashflows
CF_discounted = OCF.copy()
CF_std_discounted = OCF_std.copy()
for t in range(DEPRECIATION_PERIOD):
    CF_discounted[t] = OCF[t] / (1+WACC_TEMP)**t
    CF_std_discounted[t] = OCF_std[t] / (1+WACC_TEMP)**t

#ANNUAL NPV
NPV = np.zeros(DEPRECIATION_PERIOD+1)
#____initial invest in year "0"
NPV[0] -= K_INVEST[0].mean()
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
delta_x = DEPRECIATION_PERIOD+1
ax.set_xlim(-0.5, DEPRECIATION_PERIOD+0.5)
offset_zero = 0.5 / delta_x

#____derive second plot (positive cashflows)
for year_temp in range(1, DEPRECIATION_PERIOD+1):
    x_position = year_temp/delta_x
    ax.axhline(y=NPV_cum[year_temp], 
                color='black', 
                xmin=x_position - (1/delta_x)*0.4 + offset_zero, 
                xmax=x_position + (1/delta_x)*0.4 + offset_zero, 
                linestyle='-')

#____derive third and fourth plot (terminal values)
#Accounting for open principal payments.
REPAYMENT_PERIOD = DEPRECIATION_PERIOD
INVEST_TEMP = K_INVEST[0]
OPEN_PRINCIPAL = 0
terminal_value = TERMINAL_VALUE / (1+WACC_TEMP)**DEPRECIATION_PERIOD
plot_terminal_value = np.zeros(DEPRECIATION_PERIOD+1)
plot_npv = np.zeros(DEPRECIATION_PERIOD+1)

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
xtick_position = [1, 6, 11, 16, 21, 26, 31]
xtick_label = [2030, 2035, 2040, 2045, 2050, 2055, 2060]
plt.xticks(xtick_position, xtick_label)
plt.show()
