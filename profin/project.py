# -*- coding: utf-8 -*-
"""
Created on Sat Oct 14 10:00:21 2023

@author: j.reul
"""

from .indicators import Indicators
from .risks import Risks

import numpy as np
import yfinance as yf
from datetime import datetime, date, timedelta

class Project(Indicators, Risks):
    
    """
    The class Project initializes the monte-carlo simulation
    of project KPIs for a specific energy project at hand.
    
    Notes on input-definition:
    --------------------------

    - The values of the dictionary ATTR can be defined as int, float or numpy arrays.\n
    If being defined as numpy arrays, they must have the same length as the defined project LIFETIME.

    - The values of the scale-parameter in the dictionary RISK_PARAM can be defined as int, float or numpy arrays.
    If being defined as numpy arrays, they must have the same length as the defined project LIFETIME.
    """
        
    def __init__(self,
                 E_in,
                 E_out,
                 K_E_in,
                 K_E_out,
                 K_INVEST,
                 TERMINAL_VALUE,
                 TECHNICAL_LIFETIME,
                 OPEX,
                 EQUITY_SHARE,
                 COUNTRY_RISK_PREMIUM,
                 INTEREST,
                 CORPORATE_TAX_RATE,
                 RISK_PARAM,
                 **kwargs
                 ):
        """
        This method initializes an instance of class "Project"

        Parameters
        ----------
        E_in : int, float, array
            This is the annual energy input of the project.
        E_out : int, float, array
            This is the annual energy output of the project.
        K_E_in : int, float, array
            This is the cost of the energy input per kWh.
        K_E_out : int, float, array
            This is the cost of the energy output per kWh - Determines the revenue with E_out.
        K_INVEST : int, float, array
            This is the annual investment into the project.
        TERMINAL_VALUE : int, float, array
            This is the final sales value.
        TECHNICAL_LIFETIME : int
            This is the analyzed lifetime of the project. All cashflows are calculated for this lifetime.
        OPEX : int, float, array
            Annual operational expenditure.
        EQUITY_SHARE : float, array #why array -> we should have a look together
            Share of equity investment compared to total capital structure (debt + equity).
        COUNTRY_RISK_PREMIUM : int, float, array
            This is the additional expected return of equity investors, when facing the investments in the respective country.
        INTEREST : int, float, array
            Interest rate to be paid on the debt capital (e.g. bank loan).
        CORPORATE_TAX_RATE : int, float, array
            This is the tax rate the project must pay within the country of operation.
        RISK_PARAM : dict
            This dictionary is essential for the class "Risks".
            Example: 
                RISK_PARAM = {
                    "K_INVEST" : {
                        "distribution" : "normal",
                        "scale_start" : 20000,
                        "scale_end" : 10000,
                        "correlation" : {
                            "MSCI" : 0.9,
                            "K_E_in" : 0.5
                            }
                        }
                    }
            For each parameter, stochastic distribution functions can be
            defined, which determine the fluctuation around the mean values
            within the Monte-Carlo simulation.

        **kwargs
            DEPRECIATION_PERIOD : int
                This parameter is the repayment period for bank loans and the
                depreciation period for equity capital.
                It defaults to the LIFETIME of the project.
            SUBSIDY : float, int, array
                This parameter defined the annual subsidy for the project.
                Defaults to 0.
            CRP_EXPOSURE : float
                This parameter defines how much the project is exposed to
                country risk. It varies between 0-1 and defaults to 1.
            BETA_UNLEVERED : float
                This parameter defines the unlevered BETA factor of the project
                and defaults to 0.54.
            ENDOGENOUS_PROJECT_RISK : boolean
                This parameter defines, whether an additional, project-specific
                risk shall be calculated from RISK_PARAM.
                REFERENCE: Deloitte (2024): "Financing the Green Energy Transition:
                Innovative financing for a just transition"
            OBSERVE_PAST : int
                Specifies the number of days to extend the observation period beyond today,
                effectively moving the start of the 10-year window for historical data retrieval further into the past.

        Raises
        ------
        Warning
            "Repayment period is longer than the analyzed project period. - Consider an open PRINCIPAL in the definition of the TERMINAL_VALUE"
        Warning
            "No risks have been defined."
        ValueError
            "Not enough data to observe the chosen point in history. Decrease parameter -OBSERVE_PAST-"
        ValueError
            "The defined dict RISK_PARAM includes unknown parameters (check spelling)"
        ValueError
            "Attribute LIFETIME cannot be randomized."
        ValueError
            "Attribute LIFETIME must be constant."
        ValueError
            "Length of given attribute values must be equal to LIFETIME for attribute:", attr
         ValueError
            "Unknown input format provided for attribute:", attr, ". Allowed formats are -int-, -float-, and numpy arrays."
        AttributeError
            "The risk", check_risk, "must be defined with a correlation to the MSCI (World)."
        AttributeError
            "Given correlations of risk", risk_x, "and risk", risk_y, "are not equal. Please check the input."

        Returns
        -------
        None.

        """
        
        self.ATTR = {}
        
        #______PROJECT INDICATORS______
        # Yearly energy inflow [kWh/year]
        self.ATTR["E_in"] = E_in
        # Yearly energy outflow [kWh/year]
        self.ATTR["E_out"] = E_out
        # Yearly price of energy inflow [US$/kWh]
        self.ATTR["K_E_in"] = K_E_in
        # Yearly price of energy outflow [US$/kWh]
        self.ATTR["K_E_out"] = K_E_out
        # Total initial upfront investment costs of the energy project [US$]
        self.ATTR["K_INVEST"] = K_INVEST
        # The "TERMINAL_VALUE" of the project is the value of the project after depreciation over the LIFETIME.
        self.ATTR["TERMINAL_VALUE"] = TERMINAL_VALUE
        # Expected lifetime of the project [a] - This can also be a sub-period of the project.
        self.ATTR["TECHNICAL_LIFETIME"] = TECHNICAL_LIFETIME
        # Average repayment period of all debts [a] - Can differ from LIFETIME, but defaults to LIFETIME.
        self.ATTR["DEPRECIATION_PERIOD"] = kwargs.get("DEPRECIATION_PERIOD", TECHNICAL_LIFETIME) #change everywhere and life time to technical lifetime
        # Yearly capital expenditure [US$/year]
        self.ATTR["CAPEX"] = K_INVEST / TECHNICAL_LIFETIME
        # Yearly operational expenses, excluding energy inflow costs [US$/year]
        self.ATTR["OPEX"] = OPEX
        # Subsidy in an annual resolution.
        self.ATTR["SUBSIDY"] = kwargs.get("SUBSIDY", 0)
               
        if self.ATTR["DEPRECIATION_PERIOD"] > self.ATTR["TECHNICAL_LIFETIME"]:
            raise Warning("Repayment period is longer than the analyzed project period. - Consider an open PRINCIPAL in the definition of the TERMINAL_VALUE")
            
        #______FINANCIAL INDICATORS______
        # Share of equity in financing the project
        self.ATTR["EQUITY_SHARE"] = EQUITY_SHARE
        # Share of external capital (debts), financing the project
        self.ATTR["DEBT_SHARE"] = 1-EQUITY_SHARE
        # Country-specific risk premium according to Damodaran
        self.ATTR["CRP"] = COUNTRY_RISK_PREMIUM
        # Country risk exposure of the project. Defaults to 1.
        self.ATTR["CRP_EXPOSURE"] = kwargs.get("CRP_EXPOSURE", 1)
        
        # Country specific interest rate for a company
        self.ATTR["INTEREST"] = INTEREST
        # Country specific corporate tax rate
        self.ATTR["CORPORATE_TAX_RATE"] = CORPORATE_TAX_RATE
        
        #____INTERNAL CALCULATION OF R_FREE AND ERP_MATURE
        # Get times
        observe_past = kwargs.get("OBSERVE_PAST", 0)
        today = datetime.now()
        yesterday = today - timedelta(days=1+observe_past)
        ten_years_ago = today - timedelta(days=365.25*10+observe_past)
        # Get dates
        yesterday_date = yesterday.date()
        END_DATE = yesterday_date.strftime("%Y-%m-%d")
        ten_years_ago_date = ten_years_ago.date()
        START_DATE = ten_years_ago_date.strftime("%Y-%m-%d")
        
        #Retrieve historical data of S&P500, MSCI ACWI and 10y US GOV.-BONDS
        #get treasury data - 10 year US Gov. Bonds
        treasury_data = yf.download("^TNX", start=START_DATE, end=END_DATE)
        #get data of S&P500
        SP500_data = yf.download("^GSPC", start=START_DATE, end=END_DATE)
        SP500_daily_returns = SP500_data['Adj Close'].pct_change()
        SP500_annual_returns = SP500_daily_returns.resample('Y').sum()[1:-1]
        #get data of MSCI ACWI
        MSCI_ACWI_data = yf.download("ACWI", start=START_DATE, end=END_DATE)
        MSCI_first_data_point = date(2008, 3, 28)
        #Check, whether historical data exists.
        if ten_years_ago_date < MSCI_first_data_point:
            raise ValueError("Not enough data to observe the chosen point in history. Decrease parameter -OBSERVE_PAST-")
        MSCI_ACWI_daily_returns = MSCI_ACWI_data['Adj Close'].pct_change()
        MSCI_ACWI_annual_returns = MSCI_ACWI_daily_returns.resample('Y').sum()[1:-1]
        self.ATTR["MSCI"] = MSCI_ACWI_annual_returns.mean()
        
        # Risk free rate, e.g. national government bonds
        RISK_FREE_RATE_EXT = kwargs.get("R_FREE", -1)
        if RISK_FREE_RATE_EXT == -1:
            #No risk free rate externally defined.
            RISK_FREE_RATE = treasury_data['Adj Close'].iloc[-1] / 100
        else:
            #Risk free rate externally defined.
            RISK_FREE_RATE = RISK_FREE_RATE_EXT
        self.ATTR["R_FREE"] = RISK_FREE_RATE
        # Equity risk premium of mature market (US-market)
        CORR_SP500_MSCIW = np.corrcoef(SP500_daily_returns[1:], MSCI_ACWI_daily_returns[1:])[0,1]
        ERP_MATURE_EXT = kwargs.get("ERP_MATURE", -1)
        if ERP_MATURE_EXT == -1:
            self.ATTR["ERP_MATURE"] = (SP500_annual_returns.mean() - RISK_FREE_RATE) / CORR_SP500_MSCIW
        else:
            self.ATTR["ERP_MATURE"] = np.float64(ERP_MATURE_EXT)
            
        # Derived from balance sheets and income statements of H2Global donors
        self.ATTR["BETA_UNLEVERED"] = kwargs.get("BETA_UNLEVERED", 0.54) #0.54 for damodaran green & renewables sector; 0.47 for H2Global donors
        self.ATTR["ENDOGENOUS_PROJECT_RISK"] = kwargs.get("ENDOGENOUS_PROJECT_RISK", False)
                    
        # Indication of risks
        self.RANDOM_DRAWS = kwargs.get("RANDOM_DRAWS", 2000)
        self.RISK_PARAM = RISK_PARAM
        '''#add historical analysis of MSCI World to risk parameters
        self.RISK_PARAM["MSCI"] = {
            "distribution" : "normal",
            "scale" : MSCI_ACWI_annual_returns.std(),
            "correlation" : {}
            }'''
        
        #check if all risks are correctly named.
        check_risk_names = all(item in list(self.ATTR) for item in list(self.RISK_PARAM))
        if check_risk_names == False:
            raise ValueError("The defined dict RISK_PARAM includes unknown parameters (check spelling)")
        
        #Iterate over all attributes and expand them to full random spectrum, 
        #if they are given as arrays over the LIFETIME or defined as risks.
        for a, attr in enumerate(self.ATTR):
            random_shape = np.zeros(shape=(TECHNICAL_LIFETIME,self.RANDOM_DRAWS))
            if isinstance(self.ATTR[attr], int) or isinstance(self.ATTR[attr], float):
                if attr in list(self.RISK_PARAM): #attribute is defined as a risk
                    if attr == "TECHNICAL_LIFETIME":
                        raise ValueError("Attribute LIFETIME cannot be randomized.")
                    elif attr == "K_INVEST":
                        #K_INVEST is not an annually constant value. It's a one-time value (initial investment).
                        constant_mean = self.ATTR[attr] #this is a float value
                        random_shape[0] = constant_mean
                        self.ATTR[attr] = random_shape
                    elif attr == "TERMINAL_VALUE":
                        #TERMINAL_VALUE is not an annually constant value. It's a one-time value (initial investment).
                        constant_mean = self.ATTR[attr] #this is a float value
                        random_shape[-1] = constant_mean
                        self.ATTR[attr] = random_shape
                    else:
                        #populate random_shape with one entry over the whole lifetime.
                        constant_mean = self.ATTR[attr] #this is a float value
                        random_shape[:] = constant_mean
                        self.ATTR[attr] = random_shape
                else: #attribute is not defined as a risk or given as an array.
                    if attr in ["INTEREST", "TECHNICAL_LIFETIME", "DEPRECIATION_PERIOD",
                                "EQUITY_SHARE", "CRP", "CRP_EXPOSURE", 
                                "CORPORATE_TAX_RATE", "DEBT_SHARE", "R_FREE",
                                "MSCI", "ERP_MATURE", "BETA_UNLEVERED", "ENDOGENOUS_PROJECT_RISK",
                                ]:
                        #exclude some attributes from conversion to matrix form.
                        continue
                    elif attr == "K_INVEST":
                        #K_INVEST is not an annually constant value. It's a one-time value (initial investment).
                        constant_mean = self.ATTR[attr] #this is a float value
                        random_shape[0] = constant_mean
                        self.ATTR[attr] = random_shape
                    elif attr == "TERMINAL_VALUE":
                        #TERMINAL_VALUE is not an annually constant value. It's a one-time value (initial investment).
                        constant_mean = self.ATTR[attr] #this is a float value
                        random_shape[-1] = constant_mean
                        self.ATTR[attr] = random_shape
                    else:
                        #populate random_shape with one entry over the whole lifetime.
                        constant_mean = self.ATTR[attr] #this is a float value
                        random_shape[:] = constant_mean
                        self.ATTR[attr] = random_shape
                        #keep the value as an int or float.
            elif isinstance(self.ATTR[attr], np.ndarray): #attribute is given as a numpy array.
                if attr == "TECHNICAL_LIFETIME":
                    raise ValueError("Attribute LIFETIME must be constant.")
                #in this case, the mean value changes over the lifetime.
                #____check, if enough values are given (#of values == LIFETIME)
                if len(self.ATTR[attr]) == self.ATTR["TECHNICAL_LIFETIME"]:
                    changing_mean = self.ATTR[attr].copy() #this is an array
                    random_shape[:,:] = changing_mean[:, np.newaxis]
                    self.ATTR[attr] = random_shape
                else:
                    raise ValueError("Length of given attribute values must be equal to TECHNICAL_LIFETIME for attribute:", attr)
            else:
                raise ValueError("Unknown input format provided for attribute:", attr, ". Allowed formats are -int-, -float-, and numpy arrays.")
                
        '''#Check the definition of RISK_PARAM for correlation to MSCI
        for check_risk in list(self.RISK_PARAM):
            if check_risk == "MSCI":
                continue
            elif "MSCI" in list(self.RISK_PARAM[check_risk]["correlation"]):
                MSCI_corr_temp = self.RISK_PARAM[check_risk]["correlation"]["MSCI"]
                self.RISK_PARAM["MSCI"]["correlation"][check_risk] = MSCI_corr_temp 
            else:
                raise AttributeError("The risk", check_risk, "must be defined with a correlation to the MSCI (World).")'''
        
        #convert correlation-matrix into covariance-matrix
        #cov(x,y) = corr(x,y) * std(x) * std(y)
        #____Initialize matrix
        self.RISK_CORR = np.identity(len(self.RISK_PARAM))
        #____iterate over each risk and calculate correlation
        for x, risk_x in enumerate(self.RISK_PARAM):
            for y, risk_y in enumerate(self.RISK_PARAM):
                if x == y:
                    continue
                else:
                    corr_x_y = self.RISK_PARAM[risk_x]["correlation"][risk_y]
                    corr_y_x = self.RISK_PARAM[risk_y]["correlation"][risk_x]
                    if corr_x_y == corr_y_x:
                        self.RISK_CORR[x][y] = corr_x_y
                    else:
                        raise AttributeError("Given correlations of risk", risk_x, "and risk", risk_y, "are not equal. Please check the input.")
                    
        # Calculate risks, if RISK_PARAM is given.
        if len(self.RISK_PARAM):
            #Define risks for each time step (year) in lifetime.
            for t in range(self.ATTR["TECHNICAL_LIFETIME"]):
                TIMESTEP_RISKS = self.get_risks(t)
                #iteration of each risk within a time step t.
                for r, risk in enumerate(self.RISK_PARAM):
                    TIMESTEP_RISKS_IND = TIMESTEP_RISKS[risk]
                    #filter for negative values
                    TIMESTEP_RISKS_IND[TIMESTEP_RISKS_IND < 0] = 0
                    #assign risk array
                    self.ATTR[risk][t] = TIMESTEP_RISKS_IND
                    
        else:
            print("No risks have been defined.")