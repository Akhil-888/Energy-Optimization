import numpy as np

# Energy equations

# Solar output/day in MWh - E = A × r × H × PR
def solar_energy(area, irradiance_kwh_day, efficiency, performance_ratio):
    energy = (area * irradiance_kwh_day * efficiency * performance_ratio)/1000
    return energy

# Wind output in MW - P = 0.5 × ρ × A × v³ × cd
def wind_energy(v, rho, r, cp=0.3):
    area = np.pi * r**2
    energy = (0.5 * rho * area * v**3 * cp)/1000000
    return energy

# Hydro output in MW - P = η × ρ × g × Q × h
def hydro_energy(efficiency, rho, g, flow_rate, head_height):
    energy = (efficiency * rho * g * flow_rate * head_height)/1000000
    return energy

# energy distribution
def energy_balance(total_energy_required, mix, energy_outputs):
    units_needed = {}
    for source, share in mix.items():
        target_energy = total_energy_required * share
        units = target_energy / energy_outputs[source]
        units_needed[source] = units
    return units_needed

# --- ENERGY COST FUNCTION ---
def energy_cost(units_needed, energy_costs):
    total_cost = 0
    for source in units_needed:
        total_cost += units_needed[source] * energy_costs[source]
    return total_cost

# energy properties w/ placeholder
energy_dict = {
    "solar": {
        "cost": 500,         #usd per panel
        "output_per_day": 0.004 #MWh/day per panel
    },
    "wind": {
        "cost": 1000000,   #usd per turbine
        "output": 30  # MWh/day per turbine
    },
    "hydro": {
        "cost": 5000000,    #usd per unit
        "output": 10  #MWh/day per hydro unit
      #etc
    }
}
