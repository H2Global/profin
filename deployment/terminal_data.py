# -*- coding: utf-8 -*-
"""
Created on Jun 18 2024

@author: MatteoMassera
"""

import numpy as np
import matplotlib.pyplot as plt


class Core:
    class Tank:
        def __init__(self, volume):
            self.volume = volume

    def __init__(self, energycarrier, energysupply):
        self.energycarrier = energycarrier
        self.energysupply = energysupply
        self.tank_ = Core.Tank(volume=self.calculate_tank_volume())
        self.tank_volume = None
        self.tank_needed = None
        self.CAPEX = None
        self.OPEX = None
        self.Conv_CAPEX = None
        self.Conv_OPEX = None

    def calculate_tank_volume(self):
        if self.energycarrier == "LOHC":
            self.tank_volume = 31600  # ton_carrier/tank
            self.tank_needed = self.energysupply / 33.33 * 1e6 / 0.9 * 1000 / 54 * (6/365) * 1.6 #m3
            # TWh / (kWh/kgH2) * (kWh/TWh) * (ton/kg) / (kgH2/m3LOHC) * (kgLOHC/m3LOHC) / (tonLOHC/tank)
            # LHV_H2 = 33.33 kWh/kg_H2
            # 0.9 Swing factor LOHC re-conversion
            #LOHC contains 54 kg of hydrogen per cubic metre
            # Arrival frequency ship = 6 days
            # Dimension factor = 1.6
            return self.tank_volume

    def get_capex_terminal(self):
        if self.energycarrier == "LOHC":
            if self.tank_needed is None:
                self.calculate_tank_volume()
            # option 1: 416.92 €/m3_LOHC for tank
            self.CAPEX = self.tank_needed * 416.92 # €
            return self.CAPEX


    def get_opex_terminal(self):
        if self.energycarrier == "LOHC":
            if self.CAPEX is None:
                self.get_capex_terminal()
            self.OPEX = self.CAPEX * 0.03
            return self.OPEX

    def get_capex_conversion(self):
        if self.energycarrier == "LOHC":
            H2_output = self.energysupply / 33.33 * 1e6 / 365
            self.Conv_CAPEX = H2_output * 0.5214 * 1e6 # €
            # 0.5214 M€/ton_h2/day
            return self.Conv_CAPEX

    def get_opex_conversion(self):
        if self.energycarrier == "LOHC":
            energy_consumption = self.energysupply / 33.33 * 1e6 * 13.6 # kWh_fuel/year
            # 11 kWh/kgH2  for reconversion according to Hydrogenious
            bop_consumption = self.energysupply / 33.33 * 1e6 * 1.5 #kWh_e/year
            # 1.6 kWh/kgH2 for BoP of reconversion according Hydrogenious
            electricity_cost = 0.10 # €/kWh_H2
            self.Conv_OPEX = (energy_consumption + bop_consumption) * electricity_cost # €/year
            return self.Conv_OPEX






