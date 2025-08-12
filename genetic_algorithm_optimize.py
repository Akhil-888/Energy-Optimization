import os
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from torch import tensor
from dataclasses import dataclass
from pymoo.core.problem import ElementwiseProblem
from pymoo.optimize import minimize
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.termination import get_termination
from pymoo.operators.sampling.lhs import LHS

from basic_functions import objective_function

BASE_DIR = Path(__file__).resolve().parent

hydro_points = pd.read_csv(BASE_DIR / "hydropoints.csv")
solar_points = pd.read_csv(BASE_DIR / "solarpoints.csv")
wind_points = pd.read_csv(BASE_DIR / "windpoints.csv")
energy_summary = pd.read_csv(BASE_DIR / "countries_energy_data.csv")
#intermittency_data = pd.read_csv(BASE_DIR / "fft.csv")
#coal_gas_nuclear = pd.read_csv(BASE_DIR / "coal_gas_nuclear.csv")

#Config
@dataclass
class OptimizerConfig:
    population_size: int = 300
    max_generations: int = 1000
    random_seed: int = 42

# Optimization
class EnergyProblem(ElementwiseProblem):
    def __init__(self, config: OptimizerConfig, country_name: str, total_energy_required: float, energy_dict: dict, land_price_per_m2: float, carbon_price_per_kg: float = 0):
        super().__init__(
            n_var=8,
            n_obj=2,            # cost+land pressure
            n_ieq_constr=2,     # land and hydro constraint
            xl=np.array([0, 0, 0, 0]),
            xu=np.array([1, 1, 1, 1])#power output >= demand , <= 2*demand
        )
        self.config = config
        self.country = country_name
        self.energy_required = total_energy_required
        self.energy_dict = energy_dict
        self.land_price = land_price_per_m2
        self.carbon_price = carbon_price_per_kg

        self.land_area = energy_summary.set_index("Country").loc[country_name]["Land Area (m^2)"]
        self.demand = energy_summary.set_index("Country").loc[country_name]["Annual Consumption (MWh)"] / 365.0

    def _evaluate(self, x, out, *args, **kwargs):
        solar, wind, hydro = x #coal, nuclear, oil, gas
        mix = {"solar": solar, "wind": wind, "hydro": hydro}
"""
Solar = x[0]
Wind = x[1]
model = {“Solar”: x[0], “Wind: x[1], “Nuclear” : x[2], “Coal”: x[3]}
Demand = x[0]
Model = {}
Model  = {‘demand’=x[0], ‘solar’:x[1], … }
"""
        cost = objective_function(
            self.energy_required,
            mix,
            self.country,
            self.energy_dict,
            self.land_price,
            self.carbon_price
        )

        # Intermittency

        # Land pressure
        total_land = sum(
            (self.energy_required * share / (self.energy_dict[source].get("output") or self.energy_dict[source]["output_per_day"])) * self.energy_dict[source]["land_area"]
            for source, share in mix.items()
            if share > 0
        )
        land_pressure = total_land / self.land_area

        # Instability

        # Constraints
        land_constraint = land_pressure - 0.3

        hydro_units = (self.energy_required * hydro) / self.energy_dict["hydro"]["output"]
        hydro_output = hydro_units * self.energy_dict["hydro"]["output"]
        hydro_constraint = 1 - (hydro_output / self.demand)

        out["F"] = [
            # intermittency
            # instability
            cost,
            land_pressure
        ]

        out["G"] = [
            land_constraint,
            hydro_constraint
        ]
