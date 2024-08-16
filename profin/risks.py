# -*- coding: utf-8 -*-
"""
Created on Sat Oct 14 10:07:56 2023

@author: j.reul
"""

import numpy as np
from scipy import stats

class Risks():
    
    def __init__(self):
        pass


    def get_risks(self, timestep):
        """
        This method is a copula function for drawing all risks simultaneously.
        
        distribution : string
            Defines the type of probability distribution. 
            Currently only "normal" distribution possible.
        scale : float or np.array
            Scale parameter for probability distribution (e.g. standard deviation
            for normal distribution). Provide array, if the scale parameter
            varies by year.
        limit : dict
            Defines the minimum and maximum value for the standard deviation.
        correlation : dict
            Dictionary, which indicates the correlation of a risk parameter
            to other risk parameters and the MSCI ACWI. Correlation to 
            MSCI ACWI must be given.
            
        Example of dictionary RISK_PARAM (input to this method):
            RISK_PARAM = {
                "K_INVEST" : {
                    "distribution" : "normal",
                    "scale" : float or np.array,
                    "limit" : {
                        "min" : 0.9,
                        "max" : 0.5
                        },
                    "correlation" : {
                        "K_E_in" : 0.5
                        }
                    }
                }
                
        Returns
        -------
        Disctionary with risks.

        """
        
        # Number of risks
        NO_RISKS = len(self.RISK_PARAM)
                
        if NO_RISKS == 1:
            SINGLE_RISK = list(self.RISK_PARAM)[0]
            #get distribution type
            distribution_temp = self.RISK_PARAM[SINGLE_RISK]["distribution"] 
            #get scale parameter (e.g. standard deviation)
            if isinstance(self.RISK_PARAM[SINGLE_RISK]["scale"] , np.ndarray) or isinstance(self.RISK_PARAM[SINGLE_RISK]["scale"] , list):
                scale_temp = self.RISK_PARAM[SINGLE_RISK]["scale"][timestep]
            else:
                #scale parameter is an int or float
                scale_temp = self.RISK_PARAM[SINGLE_RISK]["scale"]
                
            if "limit" in list(self.RISK_PARAM[SINGLE_RISK]):
                if isinstance(self.RISK_PARAM[SINGLE_RISK]["limit"]["max"] , np.ndarray) or isinstance(self.RISK_PARAM[SINGLE_RISK]["limit"]["max"] , list):
                    max_trunc = self.RISK_PARAM[SINGLE_RISK]["limit"]["max"][timestep]
                    min_trunc = self.RISK_PARAM[SINGLE_RISK]["limit"]["min"][timestep]
                else:
                    #scale parameter is an int or float
                    max_trunc = self.RISK_PARAM[SINGLE_RISK]["limit"]["max"]
                    min_trunc = self.RISK_PARAM[SINGLE_RISK]["limit"]["min"]
                    
            #get mean
            mean_temp = self.ATTR[SINGLE_RISK][timestep].mean()
            
            if scale_temp == 0:
                alpha = np.full(self.RANDOM_DRAWS, mean_temp)
            else:
                if distribution_temp == "normal":
                    if "limit" in list(self.RISK_PARAM[SINGLE_RISK]):
                        max_scale = (max_trunc - mean_temp) / scale_temp
                        min_scale = (min_trunc - mean_temp) / scale_temp
                        
                        #truncated normal distribution
                        normal_dist = stats.truncnorm(
                            a=min_scale, b=max_scale, loc=mean_temp, scale=scale_temp
                            )
                        alpha = normal_dist.rvs(size=self.RANDOM_DRAWS)
                    else:
                        #normal distribution
                        normal_dist = stats.norm(loc=mean_temp, scale=scale_temp)
                        alpha = normal_dist.rvs(size=self.RANDOM_DRAWS)
                elif distribution_temp == "positive-normal":
                    #truncated normal distribution, all values above mean
                    normal_dist = stats.truncnorm(
                        a=0, b=np.inf, loc=mean_temp, scale=scale_temp
                        )
                    alpha = normal_dist.rvs(size=self.RANDOM_DRAWS)
                elif distribution_temp == "negative-normal":
                    #truncated normal distribution, all values below mean
                    normal_dist = stats.truncnorm(
                        a=-np.inf, b=0, loc=mean_temp, scale=scale_temp
                        )
                    alpha = normal_dist.rvs(size=self.RANDOM_DRAWS)
                else:
                    raise AttributeError("Unknown distribution.")
                
            RISKS = {}
            RISKS[SINGLE_RISK] = alpha

        else:
            #DEFINE COPULA
            #____IMPORTANT: Use CORRELATION-MATRIX instead of CORRELATION-MATRIX!
            mu_c = np.zeros(NO_RISKS, dtype=int)
            corr_c = self.RISK_CORR
            
            dist_c = stats.multivariate_normal(mean=mu_c, cov=corr_c)
            #____obtain random sample from copula distribution
            sample_c = dist_c.rvs(size=self.RANDOM_DRAWS)
            #____obtain marginals from copula distribution
            MARGINALS = {}
            for m in range(NO_RISKS):
                MARGINALS[m] = sample_c[:,m]
            UNIFORMS = {}
            for u in range(NO_RISKS):
                UNIFORMS[u] = stats.norm.cdf(MARGINALS[u])
                
            #DEFINE MARGINAL DISTRIBUTIONS
            ALPHA_ARRAY = {}
            for r, risk in enumerate(self.RISK_PARAM):
                #get scale 
                if isinstance(self.RISK_PARAM[risk]["scale"] , np.ndarray) or isinstance(self.RISK_PARAM[risk]["scale"] , list):
                    scale_temp = self.RISK_PARAM[risk]["scale"][timestep]
                else:
                    #scale parameter is an int or float
                    scale_temp = self.RISK_PARAM[risk]["scale"]
                #get loc/mean
                mean_temp = self.ATTR[risk][timestep].mean()

                #get limits for truncated distribution
                if "limit" in list(self.RISK_PARAM[risk]):
                    if isinstance(self.RISK_PARAM[risk]["limit"]["max"], np.ndarray) or isinstance(self.RISK_PARAM[risk]["limit"]["max"], list):
                        max_trunc = self.RISK_PARAM[risk]["limit"]["max"][timestep]
                        min_trunc = self.RISK_PARAM[risk]["limit"]["min"][timestep]
                    else:
                        #scale parameter is an int or float
                        max_trunc = self.RISK_PARAM[risk]["limit"]["max"]
                        min_trunc = self.RISK_PARAM[risk]["limit"]["min"]

                if scale_temp == 0:
                    ALPHA_ARRAY[r] = np.full(self.RANDOM_DRAWS, mean_temp)
                else:
                    if self.RISK_PARAM[risk]["distribution"] == "normal":
                        if "limit" in list(self.RISK_PARAM[risk]):
                            max_scale = (max_trunc - mean_temp) / scale_temp
                            min_scale = (min_trunc - mean_temp) / scale_temp                           
                            #truncated normal distribution
                            DIST = stats.truncnorm(
                                a=min_scale, b=max_scale, loc=mean_temp, scale=scale_temp
                                )
                            ALPHA_ARRAY[r] = DIST.ppf(UNIFORMS[r])
                        else:
                            DIST = stats.norm(loc=mean_temp, scale=scale_temp)
                            ALPHA_ARRAY[r] = DIST.ppf(UNIFORMS[r])
                    elif self.RISK_PARAM[risk]["distribution"] == "positive-normal":
                        #truncated normal distribution, with all values above the mean.
                        DIST = stats.truncnorm(a=0, b=np.inf, loc=mean_temp, scale=scale_temp)
                        ALPHA_ARRAY[r] = DIST.ppf(UNIFORMS[r])
                    elif self.RISK_PARAM[risk]["distribution"] == "negative-normal":
                        #truncated normal distribution, with all values below the mean.
                        DIST = stats.truncnorm(a=-np.inf, b=0, loc=mean_temp, scale=scale_temp)
                        ALPHA_ARRAY[r] = DIST.ppf(UNIFORMS[r])
                    else:
                        raise AttributeError("Unknown distribution.")
                                              
            RISKS = {}
            for r, risk in enumerate(self.RISK_PARAM):
                RISKS[risk] = ALPHA_ARRAY[r]
                
        return RISKS