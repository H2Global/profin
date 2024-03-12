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

    def get_BETA(self, GLOBAL_MARKET_RETURN, ASSET_RETURN):
        """
        This method calculates beta from the simulated distribution of 
        market and asset returns.

        Parameters
        ----------
        MARKET_RETURN : array
            Simulated array of market returns.
        ASSET_RETURN : array
            Simulated array of returns on the asset.

        Returns
        -------
        BETA : float
            Measure of project risk relative to market risk.

        """
        
        #get the index[0][1], as np.cov return cov-matrix.
        BETA = np.cov(GLOBAL_MARKET_RETURN, ASSET_RETURN)[0][1] / np.var(GLOBAL_MARKET_RETURN)
        
        return BETA

    def get_WACC(self):
        """
        This methods calculates the weighted average cost of capital,
        including country-specific risk premiums.

        Returns
        -------
        WACC : np.array

        """
        if self.ATTR["ENDOGENOUS_BETA"]:
            print("BETA is not given and, thus, is calculated internally.")
            
            #Internal rate of return (NPV == 0) serves as return estimate.
            ASSET_RETURN = self.get_IRR() #np.random.normal(0.08, 0.01, 1000)
            if ASSET_RETURN.mean() > 0.5:
                raise Warning("Internal rate of return >50%. Please check your assumptions.")
            #The return of the reference market is averaged over lifetime
            GLOBAL_MARKET_RETURN_MEAN = self.ATTR["MSCI"].mean(axis=0)

            self.ATTR["BETA_UNLEVERED"] = self.get_BETA(GLOBAL_MARKET_RETURN_MEAN, ASSET_RETURN)
            print("Unlevered BETA is calculated to:", self.ATTR["BETA_UNLEVERED"])
            Debt_to_Equity = self.ATTR["DEBT_SHARE"] / (1-self.ATTR["DEBT_SHARE"])
            LEVER = 1+((1-self.ATTR["CORPORATE_TAX_RATE"])*Debt_to_Equity)
            self.ATTR["BETA"] = self.ATTR["BETA_UNLEVERED"] * LEVER
            print("Levered BETA is calculated to:", self.ATTR["BETA"])

            #unsystemic risk - this is calculated, but not further processed.
            #This type of risk can be erased by diversification on the side of
            #the equity investor.
            self.ATTR["UNSYSTEMIC_RISK"] = np.std(ASSET_RETURN)

        else:
            print("Unlevered BETA is exogenously defined to:", self.ATTR["BETA_UNLEVERED"])
            Debt_to_Equity = self.ATTR["DEBT_SHARE"] / (1-self.ATTR["DEBT_SHARE"])
            LEVER = 1+((1-self.ATTR["CORPORATE_TAX_RATE"])*Debt_to_Equity)
            self.ATTR["BETA"] = self.ATTR["BETA_UNLEVERED"] * LEVER
            print("Levered BETA is calculated to:", self.ATTR["BETA"])
        
        self.ATTR["COST_OF_EQUITY"] = (
            self.ATTR["R_FREE"] + 
            self.ATTR["BETA"] * self.ATTR["ERP_MATURE"] + 
            self.ATTR["CRP"] * self.ATTR["CRP_EXPOSURE"]
            )
        
        self.ATTR["COST_OF_DEBT"] = self.ATTR["INTEREST"] * (1-self.ATTR["CORPORATE_TAX_RATE"])
        
        WACC = self.ATTR["EQUITY_SHARE"] * self.ATTR["COST_OF_EQUITY"] + self.ATTR["DEBT_SHARE"] * self.ATTR["COST_OF_DEBT"]

# =============================================================================
#         if isinstance(WACC, int) or isinstance(WACC, float):
#             WACC_MATRIX = np.zeros(shape=(self.ATTR["LIFETIME"],self.RANDOM_DRAWS))
#             WACC_MATRIX[:] = WACC
#         elif isinstance(WACC, np.ndarray):
#             WACC_MATRIX = np.zeros(shape=(self.ATTR["LIFETIME"],self.RANDOM_DRAWS))
#             WACC_MATRIX[:,:] = WACC[:, np.newaxis]
# 
#         if WACC_MATRIX.shape != (self.ATTR["LIFETIME"],self.RANDOM_DRAWS):
#             raise AttributeError("WACC_MATRIX does not have the right shape. Shape is:", WACC_MATRIX.shape)
# 
# =============================================================================

        return WACC
    

    def get_energy_efficiency(self):
        """
        This methods calculates the energy efficiency of the energy-project.

        Returns
        -------
        EFFICIENCY : float

        """
        EFFICIENCY = self.ATTR["E_out"] / self.ATTR["E_in"]
        
        return EFFICIENCY


    def get_NPV(self, WACC):
        """
        This methods calculates the net present value of the energy project in US$,
        considering future developments of interest rates and country-specific
        developments.

        Returns
        -------
        NPV : int

        """
                              
        NPV = 0
        
        #Calculate the matrix for all timesteps and random distributions.
        OPERATING_CASHFLOW = (
            self.ATTR["K_E_out"]*self.ATTR["E_out"] - 
            self.ATTR["OPEX"] - 
            self.ATTR["K_E_in"]*self.ATTR["E_in"]
            ) * (1-self.ATTR["CORPORATE_TAX_RATE"])
         
        #Discounting of annual cashflows and investments
        for t in range(self.ATTR["LIFETIME"]):
            NPV += (OPERATING_CASHFLOW[t] - self.ATTR["K_INVEST"][t]) / (1+WACC)**t
                
        #Accounting for terminal value and open principals.
        LAST_YEAR = self.ATTR["LIFETIME"]        
        NPV += self.ATTR["TERMINAL_VALUE"].mean(axis=0) / (1+WACC)**(LAST_YEAR-1)
            
        OPEN_PRINCIPAL = 0
        for t in range(self.ATTR["LIFETIME"]):
            INVEST_T = self.ATTR["K_INVEST"][t]
            TIME_TO_END = self.ATTR["LIFETIME"] - t
            RATIO_OPEN_PRINCIPAL = 1-(TIME_TO_END / self.ATTR["REPAYMENT_PERIOD"])            
            OPEN_PRINCIPAL_T = INVEST_T*self.ATTR["DEBT_SHARE"]*RATIO_OPEN_PRINCIPAL
            OPEN_PRINCIPAL += OPEN_PRINCIPAL_T
            
        NPV -= OPEN_PRINCIPAL / (1+WACC)**(LAST_YEAR-1)
        
        return NPV


    def get_IRR(self):
        """
        This methods calculates the IRR (Internal rate of return).

        Returns
        -------
        None.

        """
        
        x_init = np.full(self.RANDOM_DRAWS, 0.05)
        IRR = so.fsolve(self.get_NPV, x_init)
        
        if IRR.mean() > 0.5:
            raise Warning("Internal rate of return >50%. Please check your assumptions.")
        
        return IRR        


    def get_LCOE(self, WACC):
        """
        This methods calculates the levelized cost of energy in US$, 
        which is the cost of energy at the output stream of the energy project,
        including cost of input energy streams, CAPEX, OPEX, profit 
        and country-specific taxation.

        Returns
        -------
        LCOE : int
        
        """
        
        #Initialize TOTAL_COSTS with initial investment costs at t = 0
        TOTAL_COSTS = 0
        #Initialize TOTAL_ENERGY with 0.
        TOTAL_ENERGY = 0
                
        for t in range(self.ATTR["LIFETIME"]):
            # Add discounted energy purchase and operating costs
            TOTAL_COSTS += (self.ATTR["K_INVEST"][t] + self.ATTR["K_E_in"][t]*self.ATTR["E_in"][t] + self.ATTR["OPEX"][t]) / (1+WACC)**t
            # Add discounted energy production        
            TOTAL_ENERGY += self.ATTR["E_out"][t] / (1+WACC)**t
                
        LCOE = TOTAL_COSTS / TOTAL_ENERGY
        
        return LCOE


    def get_VaR(self, NPV, **kwargs):
        """
        This method calculates the value-at-risk from the array of 
        simulated net present values of the project.
        
        Parameters
        ----------
        keyword-argument PERCENTILE: 
            The percentile indicates the probability with which the
            negative event will occur. Defaults to 1% (Gatti, 2008: Project Finance in Theory and Practice).
            
        Returns
        -------
        Value-at-risk: The maximum expected loss with a confidence of 1-PERCENTILE.

        """
        PERCENTILE = kwargs.get("PERCENTILE", 1)
        
        return np.percentile(NPV, PERCENTILE)
    
    
    def get_cashflows(self, WACC, **kwargs):
        """
        This methods calculates the mean and standard deviation of cashflows in each year.

        Returns
        -------
        PP : int

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
        for t in range(self.ATTR["LIFETIME"]):
            OPERATING_CASHFLOW_DISCOUNTED[t] = OPERATING_CASHFLOW[t] / (1+WACC.mean())**t
            OPERATING_CASHFLOW_STD_DISCOUNTED[t] = OPERATING_CASHFLOW_STD_DISCOUNTED[t] / (1+WACC.mean())**t
        
        # NON-OPERATING CASHFLOW
        #____Annual non-operating cashflow (interest, principal, dividends)
        NON_OPERATING_CASHFLOW = np.zeros(self.ATTR["LIFETIME"])
        #____interest on debt, principal payments and dividends
        K_INTEREST_CUMSUM = self.ATTR["K_INVEST"].cumsum(axis=0)
        ANNUAL_INTEREST = (K_INTEREST_CUMSUM.T*self.ATTR["DEBT_SHARE"]*self.ATTR["COST_OF_DEBT"]).T #assuming constant and linear interest payments
        ANNUAL_PRINCIPAL = (K_INTEREST_CUMSUM.T*self.ATTR["DEBT_SHARE"] / self.ATTR["REPAYMENT_PERIOD"]).T #assuming constant and linear principal payments
        if self.ATTR["REPAYMENT_PERIOD"] < self.ATTR["LIFETIME"]:
            YEARS_WITHOUT_PRINCIPAL = self.ATTR["LIFETIME"] - self.ATTR["REPAYMENT_PERIOD"]
            ANNUAL_PRINCIPAL[-YEARS_WITHOUT_PRINCIPAL:] = 0
            ANNUAL_INTEREST[-YEARS_WITHOUT_PRINCIPAL:] = 0
        
        ANNUAL_DIVIDENDS = (K_INTEREST_CUMSUM.T*self.ATTR["EQUITY_SHARE"]*self.ATTR["COST_OF_EQUITY"]).T #assuming constant and linear dividents
        ANNUAL_SUM = -(ANNUAL_INTEREST + ANNUAL_PRINCIPAL + ANNUAL_DIVIDENDS)
        NON_OPERATING_CASHFLOW = ANNUAL_SUM.mean(axis=1)
        NON_OPERATING_CASHFLOW_STD = ANNUAL_SUM.std(axis=1)
        
        # Discount capital payments
        NON_OPERATING_CASHFLOW_DISCOUNTED = NON_OPERATING_CASHFLOW.copy()
        NON_OPERATING_CASHFLOW_STD_DISCOUNTED = NON_OPERATING_CASHFLOW_STD.copy()
        for t in range(self.ATTR["LIFETIME"]):
            NON_OPERATING_CASHFLOW_DISCOUNTED[t] = NON_OPERATING_CASHFLOW[t] / (1+WACC.mean())**t
            NON_OPERATING_CASHFLOW_STD_DISCOUNTED[t] = NON_OPERATING_CASHFLOW_STD[t] / (1+WACC.mean())**t        
        
        if DISCOUNT:
            return OPERATING_CASHFLOW_DISCOUNTED, OPERATING_CASHFLOW_STD_DISCOUNTED, NON_OPERATING_CASHFLOW_DISCOUNTED, NON_OPERATING_CASHFLOW_STD_DISCOUNTED
        else:
            return OPERATING_CASHFLOW, OPERATING_CASHFLOW_STD, NON_OPERATING_CASHFLOW, NON_OPERATING_CASHFLOW_STD