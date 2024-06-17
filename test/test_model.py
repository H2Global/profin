# -*- coding: utf-8 -*-
"""
Created on Sat Jun 13 2024

@author: mattemassera
"""
import os
import sys
import unittest
import numpy as np


import profin as pp



class TestProfin(unittest.TestCase):

    def setUp(self):

        self.p_example = pp.Project(
                     E_in=2*4000*1e+6, #Electricity demand in kWh per year
                     E_out=0.1*1e+9*33.33, #Cesaro et al. H2-production * 70% HB-efficiency
                     K_E_in=0.02, #electricity price
                     K_E_out=0.18,
                     K_INVEST=3e+9, #Cesaro et al.
                     TERMINAL_VALUE=0,
                     TECHNICAL_LIFETIME=30,
                     OPEX=3e+9 * 0.02,
                     EQUITY_SHARE=0.4,
                     COUNTRY_RISK_PREMIUM=0.04,
                     INTEREST=0.04,
                     CORPORATE_TAX_RATE=0.2,
                     RISK_PARAM={},
                     OBSERVE_PAST=0,
                     ENDOGENOUS_BETA=False,
                     REPAYMENT_PERIOD=20,
                     R_FREE=0.02,
                     ERP_MATURE=0.06
                     )


    def test_WACC(self):
        result_WACC  = self.p_example.get_WACC()
        self.assertAlmostEqual(result_WACC,0.09091199999999999, places=20)

    def test_IRR(self):
        result_IRR = self.p_example.get_IRR()
        self.assertAlmostEqual(result_IRR.mean(), 0.10679517359047987, places=20)

    def test_NPV(self):
        result_WACC = self.p_example.get_WACC()
        result_NPV = self.p_example.get_NPV(result_WACC)
        self.assertAlmostEqual(result_NPV.mean(), 379226192.8872226, places=20)

    def test_LCOE(self):
        result_WACC = self.p_example.get_WACC()
        result_LCOE = self.p_example.get_LCOE(result_WACC)
        self.assertAlmostEqual(result_LCOE.mean(), 0.1469671942396542, places=20)

    def test_cash_flow(self):
        result_WACC = self.p_example.get_WACC()
        operating_cashflow, operating_cashflow_std, non_operating_cashflow, non_operating_cashflow_std = self.p_example.get_cashflows(result_WACC)

        expected_operating_cashflow =  np.full(30, 303952000.0)
        expected_operating_cashflow_std  = np.full(30, 0)
        expected_non_operating_cashflow =  np.full(30, -332736000.0)
        expected_non_operating_cashflow_std = np.full(30, 0)

        # Use unittest to compare arrays
        self.assertEqual(len(operating_cashflow), len(expected_operating_cashflow))
        self.assertEqual(len(operating_cashflow_std), len(expected_operating_cashflow_std))
        self.assertEqual(len(non_operating_cashflow), len(expected_non_operating_cashflow))
        self.assertEqual(len(non_operating_cashflow_std), len(expected_non_operating_cashflow_std))

        for i in range(len(expected_operating_cashflow)):
            self.assertAlmostEqual(operating_cashflow[i], expected_operating_cashflow[i], places=20)
            self.assertAlmostEqual(operating_cashflow_std[i], expected_operating_cashflow_std[i], places=20)
            self.assertAlmostEqual(non_operating_cashflow[i], expected_non_operating_cashflow[i], places=20)
            self.assertAlmostEqual(non_operating_cashflow_std[i], expected_non_operating_cashflow_std[i], places=20)


if __name__ == '__main__':
    unittest.main()




