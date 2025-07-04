import numpy as np
import pandas as pd

# -_________________________
#Energy Output Equations
# _____________________---

def solar_energy(area, irradiance_kwh_day, efficiency, performance_ratio):
    energy = (area * irradiance_kwh_day * efficiency * performance_ratio) / 1000  # MWh/day
    return energy

def wind_energy(v, rho, r, cp=0.3):
    area = np.pi * r**2
    power = (0.5 * rho * area * v**3 * cp) / 1_000_000  # MW
    return power

def hydro_energy(efficiency, rho, g, flow_rate, head_height):
    power = (efficiency * rho * g * flow_rate * head_height) / 1_000_000  # MW
    return power

# -______________________________-
# Energy Balance
# -________________________--------

def energy_balance(total_energy_required, mix, energy_outputs):
    units_needed = {}
    for source, share in mix.items():
        target_energy = total_energy_required * share
        output_per_unit = energy_outputs[source]
        units = target_energy / output_per_unit
        units_needed[source] = units
    return units_needed

# _________________________-
# Cost & Emissions
# _______________________-

def equipment_cost(units_needed, energy_dict):
    total = 0
    for source in units_needed:
        cap_cost = energy_dict[source]["capital_cost"]
        total += units_needed[source] * cap_cost
    return total

def operational_cost(units_needed, energy_dict):
    total = 0
    for source in units_needed:
        op_cost = energy_dict[source]["operational_cost"]
        total += units_needed[source] * op_cost
    return total

def land_cost(units_needed, land_priceper_m2, energy_dict):
    total = 0
    for source in units_needed:
        area = energy_dict[source]["land_area"]
        total += units_needed[source] * area * land_priceper_m2
    return total

def carbon_emissions(units_needed, energy_dict):
    total = 0
    for source in units_needed:
        emissions_per_mwh = energy_dict[source]["emissions"]
        output_per_unit = energy_dict[source].get("output")#or output per day for solar, bug
        total_output = units_needed[source] * output_per_unit
        total += emissions_per_mwh * total_output
    return total

def total_energy_cost(units_needed, energy_dict, land_price_perm2, carbon_priceper_kg=0):
    cost = 0
    cost += equipment_cost(units_needed, energy_dict)
    cost += operational_cost(units_needed, energy_dict)
    cost += land_cost(units_needed, land_priceper_m2, energy_dict)
    if carbon_priceper_kg > 0:
        cost += carbon_emissions(units_needed, energy_dict) * carbon_price_per_kg
    return cost

# _______________________________-
# Energy Sources Dictionary (all placeholder values)
# _____________________________---

energy_dict = {
    "solar": {
        "capital_cost": 500,#$/unit
        "operational_cost": 5,#$/unit/day
        "output_per_day": 0.004,#MWh/day
        "land_area": 1.6,#m^2
        "emissions": 0 #kgCO2/MWh
    }
    ,
    "wind": {
        "capital_cost": 1_000_000,#$/unit
        "operational_cost": 30_000,#$/unit/day
        "output": 30,#MWh/day
        "land_area": 10_000,#m^2
        "emissions": 0#kgCO2/MWh
    }
    ,
    "hydro": {
        "capital_cost": 5_000_000,#$/unit
        "operational_cost": 100_000,#$/unit/day
        "output": 10,#MWh/day
        "land_area": 100_000,#m^2
        "emissions": 5#kgCO2/MWh
    }
    ,
    "coal": {
        "capital_cost": 800_000,#$/unit
        "operational_cost": 70_000,#$/unit/day
        "output": 120,#MWh/day
        "land_area": 5_000,#m^2
        "emissions": 950#kgCO2/MWh
    }
    ,
    "gas": {
        "capital_cost": 600_000,#$/unit
        "operational_cost": 50_000,#$/unit/day
        "output": 150,#MWh/day
        "land_area": 3_000,#m^2
        "emissions": 550#kgCO2/MWh
    }
    ,
    "oil": {
        "capital_cost": 900_000,#$/unit
        "operational_cost": 80_000,#$/unit/day
        "output": 110,#MWh/day
        "land_area": 4_000,#m^2
        "emissions": 750#kgCO2/MWh
    }
    ,
    "nuclear": {
        "capital_cost": 9_000_000,#$/unit
        "operational_cost": 300_000,#$/unit/day
        "output": 250,#MWh/day
        "land_area": 10_000,#m^2
        "emissions": 15#kgCO2/MWh
    }
}

"""EG: running code with placeholder values
total_energy = 1000  # MWh/day
energy_mix = {
    "solar": 0.2,
    "wind": 0.2,
    "nuclear": 0.3,
    "coal": 0.3
}

TODO: accessing country power output/land area data
country_data = pd.read_csv("======name=====.csv")

# Eg using for a country
country = country_data.loc[country_data['country'] == 'example country'].iloc[0]
total_energy = country['total energy name']
land_area = country['total land area name'] 

*land area has to integrate with rest of code, taking usable land area to calcaulate rest of the values. eg: % land area used for each source, 
impact on energy mix, impact on rest of functions
does energy mix change based on country?*

"""
