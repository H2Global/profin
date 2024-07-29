# -*- coding: utf-8 -*-
"""
Created on Jun 18 2024

@author: MatteoMassera
"""

class Terminal:
    def __init__(self, energycarrier, energysupply):
        self.energycarrier = energycarrier
        self.energysupply = energysupply
        
        #Key attributes
        self.tank_volume = None
        self.CAPEX_Terminal = None
        self.OPEX_Terminal = None
        self.CAPEX_Conversion = None
        self.OPEX_Conversion = None
        
        #Dimensioning terminal
        self.dimension_factor = 1.6 #volume tank / volume ship tank
        self.arrival_frequency_ships = 6
        self.full_load_hours_conversion = 0.8 * 8760 #80% of the year.
        
        #Physical and chemical properties
        self.lhv_h2 = 33.33 #Lower heating value H2: 33.33 kWh/kg-H2
        self.h2_content_lohc_vol = 54 #kg-h2/m³-carrier LOHC
        self.h2_content_grav = {
            "SNG" : 0.25, #kg-h2/kg-carrier 
            "NH3" : 0.177, #kg-h2/kg-carrier 
            "LH2" : 1, #kg-h2/kg-carrier 
            }        
        self.density = {
            "SNG" : 463.2, #kg/m³
            "NH3" : 680, #kg/m³
            "LH2" : 70.9, #kg/m³
            }

        #Efficiencies
        self.lohc_swing_factor = 0.9
        self.conversion_efficiency = {
            "SNG" : 0.871, #kg-h2-released / kg-h2-carrier
            "NH3" : 0.889, #kg-h2-released / kg-h2-carrier
            "LH2" : 1, #kg-h2-released / kg-h2-carrier
            }
                
        #Cost assumptions
        self.CAPEX_Terminal_Specific = {
            "LOHC" : 416.92 # €/m³-tank
            }
        self.CAPEX_Conversion_Specific_LOHC = 237 #€/kW
        self.electricity_cost = 0.13 # €/kWh_H2

        
    def calculate_tank_volume(self):
        if self.energycarrier == "LOHC":
            h2_energy_density_lohc_vol = self.lhv_h2 * self.lohc_swing_factor * self.h2_content_lohc_vol
            ship_volume = self.energysupply * 1e+9 * (self.arrival_frequency_ships / 365) / h2_energy_density_lohc_vol
            self.tank_volume = ship_volume * self.dimension_factor #m3
            return self.tank_volume
        elif self.energycarrier in ["SNG", "NH3", "LH2"]:
            h2_energy_density_grav = self.h2_content_grav[self.energycarrier] * self.lhv_h2 * self.conversion_efficiency[self.energycarrier]
            ship_volume = self.energysupply * 1e+9 * (self.arrival_frequency_ships / 365) / h2_energy_density_grav / self.density[self.energycarrier]
            self.tank_volume = ship_volume * self.dimension_factor #m3
            return self.tank_volume
        else:
            raise AttributeError("Method not yet defined for this -energycarrier-")


    def get_capex_terminal(self):
        if self.energycarrier == "LOHC":
            if self.tank_volume is None:
                self.calculate_tank_volume()
            self.CAPEX_Terminal = self.tank_volume * self.CAPEX_Terminal_Specific[self.energycarrier]
            return self.CAPEX_Terminal
        else:
            raise AttributeError("Method not yet defined for this -energycarrier-")


    def get_opex_terminal(self):
        if self.energycarrier == "LOHC":
            if self.CAPEX_Terminal is None:
                self.get_capex_terminal()
            self.OPEX_Terminal = self.CAPEX_Terminal * 0.03
            return self.OPEX_Terminal

        else:
            raise AttributeError("Method not yet defined for this -energycarrier-")


    def get_capex_conversion(self):
        if self.energycarrier == "LOHC":
            H2_output_kW = self.energysupply*1e+9 / self.full_load_hours_conversion
            self.CAPEX_Conversion = H2_output_kW * self.CAPEX_Conversion_Specific_LOHC # €
            return self.CAPEX_Conversion
        else:
            raise AttributeError("Method not yet defined for this -energycarrier-")


    def get_opex_conversion(self):
        if self.energycarrier == "LOHC":
            if self.CAPEX_Conversion is None:
                self.get_capex_conversion()
            OPEX_Conversion_Base = self.CAPEX_Conversion * 0.025
            energysupply_h2_mass_kg = self.energysupply*1e+9 / 33.33
            energy_consumption =  energysupply_h2_mass_kg * 11 # kWh_th/year
            # 11 kWh/kgH2  for reconversion according to Hydrogenious
            bop_consumption = energysupply_h2_mass_kg * 1.6 #kWh_e/year
            # 1.6 kWh/kgH2 for BoP of reconversion according Hydrogenious
            self.OPEX_Conversion = OPEX_Conversion_Base + (energy_consumption + bop_consumption) * self.electricity_cost # €/year
            return self.OPEX_Conversion
        else:
            raise AttributeError("Method not yet defined for this -energycarrier-")