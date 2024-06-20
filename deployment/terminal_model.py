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

    def calculate_tank_volume(self):
        if self.energycarrier == "LOHC":
            self.tank_volume = 3300.00 #ton_carrier/tank
            self.tank_needed = self.energysupply / 33.33 * 1e6 / 57 * 1040 / self.tank_volume # TWh / (kWh/kgH2) * (kWh/TWh) * (ton/kg) / (kgH2/m3LOHC) * (kgLOHC/m3LOHC) / (tonLOHC/tank)
            #LOHC contains 54 kg of hydrogen per cubic metre
            #LOHC weighs 871 kg per cubic metre
            return self.tank_volume
    def get_capex_terminal(self):
        if self.energycarrier == "LOHC":
            if self.tank_needed is None:
                self.calculate_tank_volume()
            self.CAPEX = self.tank_needed * 85 * 1e6 # USD
            return self.CAPEX

    def get_opex_terminal(self):
        if self.energycarrier == "LOHC":
            if self.CAPEX is None:
                self.get_capex_terminal()
            self.OPEX = self.CAPEX * 0.03

            return self.OPEX

