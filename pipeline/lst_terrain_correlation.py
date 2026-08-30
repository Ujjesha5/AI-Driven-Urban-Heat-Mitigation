import rasterio
import numpy as np
from scipy.stats import pearsonr

with rasterio.open("data/mumbai_LST_2026_Q1.tif") as src:
    lst = src.read(1)
with rasterio.open("data/mumbai_DEM.tif") as src:
    dem = src.read(1)
with rasterio.open("data/mumbai_slope.tif") as src:
    slope = src.read(1)

# Only use pixels where all three have valid data
mask = ~np.isnan(lst) & ~np.isnan(dem) & ~np.isnan(slope)

lst_valid = lst[mask]
dem_valid = dem[mask]
slope_valid = slope[mask]

r_dem, p_dem = pearsonr(lst_valid, dem_valid)
r_slope, p_slope = pearsonr(lst_valid, slope_valid)

print(f"Valid pixels used: {mask.sum()}")
print(f"LST vs Elevation: r={r_dem:.3f}, p={p_dem:.2e}")
print(f"LST vs Slope: r={r_slope:.3f}, p={p_slope:.2e}")