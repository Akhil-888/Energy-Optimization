import numpy as np
import pandas as pd
import os

BASE_DIR = Path(__file__).resolve().parent
country_data = pd.read_csv(BASE_DIR / "hydropoints.csv")
country_data = pd.read_csv(BASE_DIR / "solarpoints.csv")
country_data = pd.read_csv(BASE_DIR / "windpoints.csv")
renewables_summary = pd.read_csv(BASE_DIR / "countries_energy_data.csv")
#intermittency_data = pd.read_csv(BASE_DIR / "fft.csv")


# -_________________________
#Energy Output Equations
# _____________________---

def solar_energy(area, irradiance_kwh_day, efficiency, performance_ratio):
    energy = (area * irradiance_kwh_day * efficiency * performance_ratio) / 1000  # MWh/day
    #account for angle incident on solar panel affecting energy
    return energy

def wind_energy(v, rho, r, cp=0.3):
    area = np.pi * r**2
    power = (0.5 * rho * area * v**3 * cp) / 1_000_000  # MW
    return power

def hydro_energy(efficiency, rho, g, flow_rate, head_height):
    power = (efficiency * rho * g * flow_rate * head_height) / 1_000_000  # MW
    return power

# -______________________________-
# Objective Function (Replacing Energy Balance)
# -________________________--------

def objective_function(total_energy_required, mix, country_name, energy_dict, land_price_per_m2, carbon_price_per_kg=0):
    # Get max land area allowed (30%)
    land_data = renewables_summary.set_index("Country")

    max_land_area = 0.3 * land_data.loc[country_name]["Land Area (m^2)"]
    units_needed = {}
    total_land_used = 0
    total_cost = 0
    total_emissions = 0

    for source, share in mix.items():
        # Skip if no intermittency
        if share <= 0:
            continue
            
        target_energy = total_energy_required * share
        output_per_unit = energy_dict[source].get("output") or energy_dict[source].get("output_per_day") # For solar
        if not output_per_unit or output_per_unit <= 0:
            return float("inf")  # Penalize bad data

        units = target_energy / output_per_unit
        units_needed[source] = units

        # Cost calculations
        cap_cost = energy_dict[source]["capital_cost"]
        op_cost = energy_dict[source]["operational_cost"]
        land_area = energy_dict[source]["land_area"]
        emissions = energy_dict[source]["emissions"]

        total_cost += units * (cap_cost + op_cost)
        total_land_used += units * land_area

        if energy_dict[source].get("emissions_mode", "per_energy") == "per_energy":
            # For fossil fuels etc.
            total_emissions += units * output_per_unit * emissions
        elif energy_dict[source]["emissions_mode"] == "per_unit":
            # For wind/solar etc.
            total_emissions += units * emissions
            
    # Land area check constraint
    if total_land_used > max_land_area:
        return float("inf")

    # Add land cost
    total_cost += total_land_used * land_price_per_m2

    # Add carbon cost
    if carbon_price_per_kg > 0:
        total_cost += total_emissions * carbon_price_per_kg

    return total_cost

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

def land_cost(units_needed, energy_dict):
    total = 0
    for source in units_needed:
        area = energy_dict[source]["land_area"]
        total += units_needed[source] * area
    return total  # m²

def carbon_emissions(units_needed, energy_dict):
    total = 0
    for source in units_needed:
        emissions_per_mwh = energy_dict[source]["emissions"]
        output_per_unit = energy_dict[source].get("output") or energy_dict[source].get("output_per_day")
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
        "emissions": 500,  # kg CO2 *per generator* for solar
        "emissions_mode": "per_unit"
    }
    ,
    "wind": {
        "capital_cost": 1_000_000,#$/unit
        "operational_cost": 30_000,#$/unit/day
        "output": 30,#MWh/day
        "land_area": 10_000,#m^2
        "emissions": 500,  # kg CO2 *per generator* for wind
        "emissions_mode": "per_unit"
    }
    ,
    "hydro": {
        "capital_cost": 5_000_000,#$/unit
        "operational_cost": 100_000,#$/unit/day
        "output": 1200,#MWh/day
        "land_area": 100_000,#m^2
        "emissions": 500,  # kg CO2 *per generator* for wind
        "emissions_mode": "per_unit"
    }
    ,
    "coal": {
        "capital_cost": 800_000,#$/unit
        "operational_cost": 70_000,#$/unit/day
        "output": 120,#MWh/day
        "land_area": 5_000,#m^2
        "emissions": 0.9,  # kg CO2 per kWh for coal
        "emissions_mode": "per_energy"
    }
    ,
    "gas": {
        "capital_cost": 600_000,#$/unit
        "operational_cost": 50_000,#$/unit/day
        "output": 150,#MWh/day
        "land_area": 3_000,#m^2
        "emissions": 0.9,  # kg CO2 per kWh for gas
        "emissions_mode": "per_energy"
    }
    ,
    "oil": {
        "capital_cost": 900_000,#$/unit
        "operational_cost": 80_000,#$/unit/day
        "output": 500,#MWh/day
        "land_area": 4_000,#m^2
        "emissions": 0.9,  # kg CO2 per kWh for oil
        "emissions_mode": "per_energy"
    }
    ,
    "nuclear": {
        "capital_cost": 9_000_000,#$/unit
        "operational_cost": 300_000,#$/unit/day
        "output": 20,#MWh/day
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
