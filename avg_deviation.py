import xarray as xr
import numpy as np
import geopandas as gpd
import regionmask

ds = xr.open_dataset('pppp.nc')

# wind speed
def calculate_wind_speed(ds):
    return np.sqrt(ds['u_component']**2 + ds['v_component']**2)

ds['wind_speed'] = calculate_wind_speed(ds)

# Example: Load country boundaries (Natural Earth, level 1)
countries = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

# Create a regionmask for countries
country_mask = regionmask.Regions_cls(
    name='countries',
    numbers=list(range(len(countries))),
    names=countries['name'].tolist(),
    outlines=countries['geometry'].values
)

# Apply the mask to your dataset (assumes lat/lon coordinates)
mask = country_mask.mask(ds, lat_name='latitude', lon_name='longitude')

# Prepare results dictionary
results = {}

for i, country in enumerate(countries['name']):
    region = (mask == i)
    # solar irradiance
    solar_vals = ds['surface_solar_radiation_downwards'].where(region)
    solar_mean = solar_vals.mean(dim=['time', 'latitude', 'longitude'], skipna=True).item()
    solar_std = solar_vals.std(dim=['time', 'latitude', 'longitude'], skipna=True).item()
    # wind speed
    wind_vals = ds['wind_speed'].where(region)
    wind_mean = wind_vals.mean(dim=['time', 'latitude', 'longitude'], skipna=True).item()
    wind_std = wind_vals.std(dim=['time', 'latitude', 'longitude'], skipna=True).item()
    # results
    results[country] = {
        'solar_mean': solar_mean,
        'solar_std': solar_std,
        'wind_mean': wind_mean,
        'wind_std': wind_std
    }

# results
for country, stats in results.items():
    print(f"{country}: Solar Mean={stats['solar_mean']}, Solar Std={stats['solar_std']}, "f"Wind Mean={stats['wind_mean']}, Wind Std={stats['wind_std']}")
