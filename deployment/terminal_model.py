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
            #self.tank_volume = 3300.00 #ton_carrier/tank
            self.tank_volume = 61600.00  # ton_carrier/tank
            self.tank_needed = self.energysupply / 33.33 * 1e6 / 57 * 1040 / self.tank_volume # TWh / (kWh/kgH2) * (kWh/TWh) * (ton/kg) / (kgH2/m3LOHC) * (kgLOHC/m3LOHC) / (tonLOHC/tank)
            #LOHC contains 54 kg of hydrogen per cubic metre
            #LOHC weighs 871 kg per cubic metre
            return self.tank_volume
    def get_capex_terminal(self):
        if self.energycarrier == "LOHC":
            if self.tank_needed is None:
                self.calculate_tank_volume()
            #self.CAPEX = self.tank_needed * 85 * 1e6 # USD
            self.CAPEX = self.tank_needed * 35 * 1e6  # USD
            return self.CAPEX

    def get_opex_reconversion(self):
        if self.energycarrier == "LOHC":
            fuel_consumption = self.energysupply / 33.33 * 1e6 * 13.6 # kWh_fuel/year
            # 13.6 kWh_fuel/kgH2  for reconversion according to EIA Global Hydrogen Rewiew 2023
            electricity_consumption = self.energysupply / 33.33 * 1e6 * 1.5 #kWh_e/year
            # 1.5 kWh_electircity/kgH2  for reconversion according to EIA Global Hydrogen Rewiew 2023
            fuel_cost = 0.102 # €/kWh_H2
            electricity_cost = 0.05 # €/kWh_H2
            self.Conv_OPEX = fuel_consumption * fuel_cost + electricity_consumption * electricity_cost # €/year
            return self.Conv_OPEX

    def get_opex_terminal(self):
        if self.energycarrier == "LOHC":
            if self.CAPEX is None:
                self.get_capex_terminal()
                self.get_opex_reconversion()
            self.OPEX = self.CAPEX * 0.03 + self.Conv_OPEX

            return self.OPEX






