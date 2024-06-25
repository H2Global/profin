# -*- coding: utf-8 -*-
"""
Created on Sat Oct 14 10:07:44 2023

@author: j.reul
"""

import numpy as np
import scipy.optimize as so

class Indicators():
    
    """
    The class Indicators holds the functionality to calculate project-related
    KPIs.
    """
    
    def __init__(self):
        pass

    def get_WACC(self):
        """
        This method calculates the weighted average cost of capital,
        including country-specific risk premiums.

        Returns
        -------
        float
            WACC: Weighted Average Cost of Capital for the project.

        """
        print("Unlevered BETA is exogenously defined to:", self.ATTR["BETA_UNLEVERED"])
        Debt_to_Equity = self.ATTR["DEBT_SHARE"] / (1-self.ATTR["DEBT_SHARE"])
        LEVER = 1+((1-self.ATTR["CORPORATE_TAX_RATE"])*Debt_to_Equity)
        self.ATTR["BETA"] = self.ATTR["BETA_UNLEVERED"] * LEVER
        print("Levered BETA is calculated to:", self.ATTR["BETA"])
        
        if self.ATTR["ENDOGENOUS_PROJECT_RISK"]:
            print("Project risks are calculated endogenously.")
            #Internal rate of return (NPV == 0) serves as return estimate.
            IRR = self.get_IRR()
            self.ATTR["SP"] = np.percentile(IRR, 0.5)-np.percentile(IRR, 0.1)
            print("Project-specific risk:", round(self.ATTR["SP"]*100, 2), "%")

        else:
            #Project-specific risk is assumed to be zero.
            self.ATTR["SP"] = 0
        
        self.ATTR["COST_OF_EQUITY"] = (
            self.ATTR["R_FREE"] + 
            self.ATTR["BETA"] * self.ATTR["ERP_MATURE"] + 
            self.ATTR["CRP"] * self.ATTR["CRP_EXPOSURE"] + 
            self.ATTR["SP"]
            )
        
        self.ATTR["COST_OF_DEBT"] = (self.ATTR["INTEREST"]+self.ATTR["CRP"]) * (1-self.ATTR["CORPORATE_TAX_RATE"])
        
        WACC = self.ATTR["EQUITY_SHARE"] * self.ATTR["COST_OF_EQUITY"] + self.ATTR["DEBT_SHARE"] * self.ATTR["COST_OF_DEBT"]

        return WACC
    

    def get_energy_efficiency(self):
        """
        This method calculates the energy efficiency of the energy-project.

        Returns
        -------
        float
            EFFICIENCY : define as the ratio of the produced energy over the used energy.

        """
        EFFICIENCY = self.ATTR["E_out"] / self.ATTR["E_in"]
        
        return EFFICIENCY


    def get_NPV(self, WACC, **kwargs):
        """
        This method calculates the net present value of the energy project in US$,
        considering future developments of interest rates and country-specific
        developments.

        Parameters
        ----------
        WACC : float
            The Weighted Average Cost of Capital.
        **kwargs : dict
            Additional keyword arguments that can specify various parameters like
            cash flows, number of periods, etc.

        Returns
        -------
        float
            NPV : value of future cash flow over an investment's entire life discounted to the present.

        """
        
        period_to_analyze = kwargs.get("PERIOD", self.ATTR["TECHNICAL_LIFETIME"])
        
        #Calculate the matrix for all timesteps and random distributions.
        OPERATING_CASHFLOW = (
            self.ATTR["K_E_out"]*self.ATTR["E_out"] -
            self.ATTR["OPEX"] - 
            self.ATTR["K_E_in"]*self.ATTR["E_in"]
            ) * (1-self.ATTR["CORPORATE_TAX_RATE"])
         
        SUBSIDY = self.ATTR["SUBSIDY"].copy()

        TERMINAL_VALUE = self.ATTR["TERMINAL_VALUE"].copy()

        K_INVEST = self.ATTR["K_INVEST"].copy()
                
        RELEVANT_CASHFLOWS = (
            OPERATING_CASHFLOW + 
            SUBSIDY + 
            TERMINAL_VALUE -
            K_INVEST
            )
        
        #Discounting of annual cashflows and investments
        NPV = 0
        for t in range(period_to_analyze):
            NPV += RELEVANT_CASHFLOWS[t] / (1+WACC)**t
        
        return NPV


    def get_IRR(self, **kwargs):
        """
        This method calculates the IRR (Internal rate of return).

        Returns
        -------
        float
            IRR: the discount rate that makes the net present value (NPV) of all cash flows equal to zero.

        """
        
        INITIAL = kwargs.get("INITIAL_VALUE", 0.05)
        x_init = np.full(self.RANDOM_DRAWS, INITIAL)
        IRR = so.fsolve(self.get_NPV, x_init)
        
        if IRR.mean() > 0.5:
            print("IRR Mean: ", IRR.mean())
            raise Warning("Internal rate of return >50%. Please check your assumptions.")
        
        return IRR        


    def get_LCOE(self, WACC):
        """
        This method calculates the levelized cost of energy in US$,
        which is the cost of energy at the output stream of the energy project,
        including cost of input energy streams, CAPEX, OPEX, profit 
        and country-specific taxation.

        Parameters
        ----------
        WACC : float
            The Weighted Average Cost of Capital.

        Returns
        -------
        float
            LCOE : minimum price at which the output energy by the project is required to be sold in order to offset the
            total costs of production over the studied period.
        
        """
        
        #Initialize TOTAL_COSTS with initial investment costs at t = 0
        TOTAL_COSTS = 0
        #Initialize TOTAL_ENERGY with 0.
        TOTAL_ENERGY = 0
                
        for t in range(self.ATTR["TECHNICAL_LIFETIME"]):
            # Add discounted energy purchase and operating costs
            TOTAL_COSTS += (self.ATTR["K_INVEST"][t] + self.ATTR["K_E_in"][t]*self.ATTR["E_in"][t] + self.ATTR["OPEX"][t]) / (1+WACC)**t
            # Add discounted energy production        
            TOTAL_ENERGY += self.ATTR["E_out"][t] / (1+WACC)**t
                
        LCOE = TOTAL_COSTS / TOTAL_ENERGY
        
        return LCOE


    def get_VaR(self, IRR, **kwargs):
        """
        This method calculates the value-at-risk from the array of 
        simulated net present values of the project.
        
        Parameters
        ----------
        IRR : array_like
            An array of simulated Internal Rates of Return for the project.

        keyword-argument PERCENTILE: 
            The percentile indicates the probability with which the
            negative event will occur. Defaults to 1% (Gatti, 2008: Project Finance in Theory and Practice).
            
        Returns
        -------
        float
            Value-at-risk: The maximum expected loss with a confidence of 1-PERCENTILE.
        """
        VaR = np.percentile(IRR, 0.5)-np.percentile(IRR, 0.1)
        
        return VaR
    
    
    def get_sharpe(self, IRR):
        
        return (IRR.mean() - self.ATTR["R_FREE"]) / IRR.std()
    
    
    def get_cashflows(self, WACC, **kwargs):
        """
        This method calculates the mean and standard deviation of cashflows in each year.

        Parameters
        ----------
        WACC : float
            The Weighted Average Cost of Capital.

        Returns
        -------
        tuple
            - OPERATING_CASHFLOW (float): Non-discounted operating cash flow.
            - OPERATING_CASHFLOW_STD (float): Standard deviation of the non-discounted operating cash flow.
            - NON_OPERATING_CASHFLOW (float): Non-discounted non-operating cash flow.
            - NON_OPERATING_CASHFLOW_STD (float): Standard deviation of the non-discounted non-operating cash flow.
        """
        
        #FOR THE FUTURE: Introduce different distributions over time 
        #for interest rate, dividend payouts and principal settlements.
        
        DISCOUNT = kwargs.get("DISCOUNT", False)
        
        # OPERATING CASHFLOW        
        #____Annual operating cashflows, non-discounted
        OPERATING_CASHFLOW = (
            self.ATTR["K_E_out"]*self.ATTR["E_out"] -
            self.ATTR["OPEX"] - 
            self.ATTR["K_E_in"]*self.ATTR["E_in"]
            ).mean(axis=1) * (1-self.ATTR["CORPORATE_TAX_RATE"])
        
        OPERATING_CASHFLOW_STD = (
                (
                self.ATTR["K_E_out"]*self.ATTR["E_out"] -
                self.ATTR["OPEX"] - 
                self.ATTR["K_E_in"]*self.ATTR["E_in"]
                ) * (1-self.ATTR["CORPORATE_TAX_RATE"])
            ).std(axis=1)

        #____Discount annual operating cashflows
        OPERATING_CASHFLOW_DISCOUNTED = OPERATING_CASHFLOW.copy()
        OPERATING_CASHFLOW_STD_DISCOUNTED = OPERATING_CASHFLOW_STD.copy()
        for t in range(self.ATTR["TECHNICAL_LIFETIME"]):
            OPERATING_CASHFLOW_DISCOUNTED[t] = OPERATING_CASHFLOW[t] / (1+WACC.mean())**t
            OPERATING_CASHFLOW_STD_DISCOUNTED[t] = OPERATING_CASHFLOW_STD_DISCOUNTED[t] / (1+WACC.mean())**t
        
        # NON-OPERATING CASHFLOW
        #____Annual non-operating cashflow (interest, principal, dividends)
        NON_OPERATING_CASHFLOW = np.zeros(self.ATTR["TECHNICAL_LIFETIME"])
        #____interest on debt, principal payments and dividends
        K_INVEST_CUMSUM = self.ATTR["K_INVEST"].cumsum(axis=0)
        ANNUAL_INTEREST = (K_INVEST_CUMSUM.T*self.ATTR["DEBT_SHARE"]*self.ATTR["COST_OF_DEBT"]).T #assuming constant and linear interest payments
        ANNUAL_PRINCIPAL = (K_INVEST_CUMSUM.T*self.ATTR["DEBT_SHARE"] / self.ATTR["DEPRECIATION_PERIOD"]).T #assuming constant and linear principal payments
        if self.ATTR["DEPRECIATION_PERIOD"] < self.ATTR["TECHNICAL_LIFETIME"]:
            YEARS_WITHOUT_PRINCIPAL = self.ATTR["TECHNICAL_LIFETIME"] - self.ATTR["DEPRECIATION_PERIOD"]
            ANNUAL_PRINCIPAL[-YEARS_WITHOUT_PRINCIPAL:] = 0
            ANNUAL_INTEREST[-YEARS_WITHOUT_PRINCIPAL:] = 0
        
        ANNUAL_DIVIDENDS = (K_INVEST_CUMSUM.T*self.ATTR["EQUITY_SHARE"]*self.ATTR["COST_OF_EQUITY"]).T #assuming constant and linear dividents
        ANNUAL_SUBSIDY = self.ATTR["SUBSIDY"].copy()
        ANNUAL_SUM = ANNUAL_SUBSIDY-(ANNUAL_INTEREST + ANNUAL_PRINCIPAL + ANNUAL_DIVIDENDS)
        NON_OPERATING_CASHFLOW = ANNUAL_SUM.mean(axis=1)
        NON_OPERATING_CASHFLOW_STD = ANNUAL_SUM.std(axis=1)
        
        # Discount capital payments
        NON_OPERATING_CASHFLOW_DISCOUNTED = NON_OPERATING_CASHFLOW.copy()
        NON_OPERATING_CASHFLOW_STD_DISCOUNTED = NON_OPERATING_CASHFLOW_STD.copy()
        for t in range(self.ATTR["TECHNICAL_LIFETIME"]):
            NON_OPERATING_CASHFLOW_DISCOUNTED[t] = NON_OPERATING_CASHFLOW[t] / (1+WACC.mean())**t
            NON_OPERATING_CASHFLOW_STD_DISCOUNTED[t] = NON_OPERATING_CASHFLOW_STD[t] / (1+WACC.mean())**t        
        
        if DISCOUNT:
            return OPERATING_CASHFLOW_DISCOUNTED, OPERATING_CASHFLOW_STD_DISCOUNTED, NON_OPERATING_CASHFLOW_DISCOUNTED, NON_OPERATING_CASHFLOW_STD_DISCOUNTED
        else:
            return OPERATING_CASHFLOW, OPERATING_CASHFLOW_STD, NON_OPERATING_CASHFLOW, NON_OPERATING_CASHFLOW_STD
        
        
    def get_NPV_Subsidy_Annually_Constant(self, ANNUAL_SUBSIDY, npv_target, WACC, PERIOD):
        """
        This method calculates the net present value of the energy project in US dollars,
        considering future developments of interest rates and country-specific
        developments.

        Parameters
        ----------
        ANNUAL_SUBSIDY : float
            The annual subsidy amount in US dollars that the project will receive.
        npv_target : float
            The target NPV that the project aims to achieve.
        WACC : float
            The Weighted Average Cost of Capital.
        PERIOD : int
            The total period over which the NPV is calculated, typically expressed in years.

        Returns
        -------
        float
            NPV: the calculated NPV of the project, after accounting for the annual subsidy over the specified period.
        """
                        
        period_to_analyze = PERIOD
        
        #Calculate the matrix for all timesteps and random distributions.
        OPERATING_CASHFLOW = (
            self.ATTR["K_E_out"]*self.ATTR["E_out"] -
            self.ATTR["OPEX"] - 
            self.ATTR["K_E_in"]*self.ATTR["E_in"]
            ) * (1-self.ATTR["CORPORATE_TAX_RATE"])
         
        TERMINAL_VALUE = self.ATTR["TERMINAL_VALUE"].copy()

        K_INVEST = self.ATTR["K_INVEST"].copy()
                
        RELEVANT_CASHFLOWS = (
            OPERATING_CASHFLOW + 
            ANNUAL_SUBSIDY + 
            TERMINAL_VALUE -
            K_INVEST
            )
        
        #Discounting of annual cashflows and investments
        NPV = -npv_target
        for t in range(period_to_analyze):
            NPV += RELEVANT_CASHFLOWS[t] / (1+WACC)**t
        
        return NPV
    
    def get_NPV_Subsidy_Anchor_Capacity(self, ANCHOR_CAPACITY, npv_target, WACC, PERIOD, E_OUT_MAX):
        """
        This method calculates the net present value of the energy project in US dollars,
        considering future developments of interest rates and country-specific
        developments.

        Parameters
        ----------
        ANCHOR_CAPACITY : float
            TO BE DEFINED.
        npv_target : float
            The target NPV that the project aims to achieve.
        WACC : float
            The Weighted Average Cost of Capital.
        PERIOD : int
            The total period over which the NPV is calculated.
        E_OUT_MAX : float
            The maximum energy output capacity of the project.


        Returns
        -------
        float
            NPV:The calculated NPV of the project, after considering the anchor capacity and the specified economic factors over the given period.
        """
        
        period_to_analyze = PERIOD
        
        #Calculate, whether the anchor capacity bookings would exceed the revenues from actual capacity bookings.
        SUBSIDY = self.ATTR["K_E_out"]*E_OUT_MAX*ANCHOR_CAPACITY-self.ATTR["K_E_out"]*self.ATTR["E_out"]
        SUBSIDY[SUBSIDY<0] = 0
                
        #Calculate the matrix for all timesteps and random distributions.
        OPERATING_CASHFLOW = (
            self.ATTR["K_E_out"]*self.ATTR["E_out"] +
            SUBSIDY -
            self.ATTR["OPEX"] - 
            self.ATTR["K_E_in"]*self.ATTR["E_in"]
            ) * (1-self.ATTR["CORPORATE_TAX_RATE"])
         
        TERMINAL_VALUE = self.ATTR["TERMINAL_VALUE"].copy()

        K_INVEST = self.ATTR["K_INVEST"].copy()
                
        RELEVANT_CASHFLOWS = (
            OPERATING_CASHFLOW + 
            TERMINAL_VALUE -
            K_INVEST
            )
        
        #Discounting of annual cashflows and investments
        NPV = -npv_target
        for t in range(period_to_analyze):
            NPV += RELEVANT_CASHFLOWS[t] / (1+WACC)**t
        
        return NPV
    
    def get_NPV_Subsidy_Fixed_Premium(self, FIXED_PREMIUM, npv_target, WACC, PERIOD):
        """
        This method calculates the net present value of the energy project in US$,
        considering future developments of interest rates and country-specific
        developments.

        Parameters
        ----------
        FIXED_PREMIUM : float
            The fixed premium amount in US dollars that will be added annually to the cash flows.
        npv_target : float
            The target NPV that the project aims to achieve. This acts as a benchmark for financial planning.
        WACC : float
            The Weighted Average Cost of Capital, used as the discount rate for computing the present value of future cash flows.
        PERIOD : int
            The duration over which the NPV is calculated.


        Returns
        -------
        float
            NPV: The calculated NPV of the project, adjusted for the fixed premium over the specified period.
        """
        
        period_to_analyze = PERIOD
        
        #Calculate the matrix for all timesteps and random distributions.
        OPERATING_CASHFLOW = (
            (self.ATTR["K_E_out"]+FIXED_PREMIUM)*self.ATTR["E_out"] -
            self.ATTR["OPEX"] - 
            self.ATTR["K_E_in"]*self.ATTR["E_in"]
            ) * (1-self.ATTR["CORPORATE_TAX_RATE"])
         
        TERMINAL_VALUE = self.ATTR["TERMINAL_VALUE"].copy()

        K_INVEST = self.ATTR["K_INVEST"].copy()
                
        RELEVANT_CASHFLOWS = (
            OPERATING_CASHFLOW + 
            TERMINAL_VALUE -
            K_INVEST
            )
        
        #Discounting of annual cashflows and investments
        NPV = -npv_target
        for t in range(period_to_analyze):
            NPV += RELEVANT_CASHFLOWS[t] / (1+WACC)**t
        
        return NPV

    
    
    def get_subsidy(self, npv_target, depreciation_target, subsidy_scheme, WACC, **kwargs):
        """
        This method returns the required subsidy to reach the defined
        net present value target after a given depreciation period and
        for a given subsidy scheme. 
        Available subsidy schemes: 1) Initial subsidy (e.g. CAPEX), 
        2) annually constant subsidy (e.g. H2Global), 3) CFD, 4) Fixed Premium

        Parameters
        ----------
        npv_target : float
            The NPV target that the project aims to achieve.
        depreciation_target : int
            The number of years over which the asset will be depreciated.
        subsidy_scheme : str
            The type of subsidy scheme to be applied. Valid options include:
            - 'initial' for initial subsidy (e.g., CAPEX),
            - 'annual' for annually constant subsidy (e.g., H2Global),
            - 'CFD' for Contracts for Difference,
            - 'fixed' for Fixed Premium.
        WACC : float
            The Weighted Average Cost of Capital.

        Returns
        -------
        float
            The calculated subsidy amount required to meet the NPV target after depreciation and considering the selected subsidy scheme.

        """
        
        if subsidy_scheme == "INITIAL":
            npv_temp = self.get_NPV(WACC, PERIOD=depreciation_target)
            subsidy = npv_target - npv_temp
            
        elif subsidy_scheme == "ANNUALLY_CONSTANT":
            x_init = np.full(self.RANDOM_DRAWS, 1e+6)
            subsidy = so.fsolve(self.get_NPV_Subsidy_Annually_Constant, x_init, args=(npv_target,WACC,depreciation_target))

        elif subsidy_scheme == "ANCHOR_CAPACITY":
            E_OUT_MAX = kwargs.get("E_OUT_MAX", 0)
            if E_OUT_MAX == 0:
                raise ValueError("-E_OUT_MAX- must be given for this subsidy calculation.")
            x_init = np.full(self.RANDOM_DRAWS, 0.8)
            anchor_capacity_ratio = so.fsolve(self.get_NPV_Subsidy_Anchor_Capacity, x_init, args=(npv_target,WACC,depreciation_target,E_OUT_MAX))
            funding = self.ATTR["K_E_out"]*E_OUT_MAX*anchor_capacity_ratio-self.ATTR["K_E_out"]*self.ATTR["E_out"]
            funding[funding<0] = 0
            
            subsidy = (funding, anchor_capacity_ratio)

        elif subsidy_scheme == "FIXED_PREMIUM":
            x_init = np.full(self.RANDOM_DRAWS, 0.001)
            subsidy = so.fsolve(self.get_NPV_Subsidy_Fixed_Premium, x_init, args=(npv_target,WACC,depreciation_target))

        elif subsidy_scheme == "DYNAMIC_PREMIUM":
            OPERATING_CASHFLOW, OPERATING_CASHFLOW_STD, NON_OPERATING_CASHFLOW, NON_OPERATING_CASHFLOW_STD = self.get_cashflows(WACC)
            TOTAL_CASHFLOW = OPERATING_CASHFLOW + NON_OPERATING_CASHFLOW
            subsidy = -(TOTAL_CASHFLOW / self.ATTR["E_in"].mean(axis=1))

        elif subsidy_scheme == "CFD":
            OPERATING_CASHFLOW, OPERATING_CASHFLOW_STD, NON_OPERATING_CASHFLOW, NON_OPERATING_CASHFLOW_STD = self.get_cashflows(WACC)
            subsidy = -(OPERATING_CASHFLOW + NON_OPERATING_CASHFLOW)
            #print("WARNING: Given NPV-target might not be achieved, since CfD-funding only balances out cashflows! For NPV = 0 align the depreciation_target with the depreciation-period for the whole projects.")
        
        else:
            raise AttributeError("No such subsidy scheme defined.") 

        return subsidy
    
    
    
    
    
    
    
    
    
    
    
    