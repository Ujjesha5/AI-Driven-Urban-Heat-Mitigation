"""
Builds the remaining inputs InVEST's Urban Cooling Model needs, using data you already have:
  1. A constant-value ET0 (reference evapotranspiration) raster, matching the LULC extent.
  2. An AOI (area of interest) boundary vector, derived from the LULC raster's own bounds.
  3. t_ref (reference/rural air temperature) and uhi_max (max UHI magnitude), both computed
     directly from your real 2026 Q1 LST data rather than guessed.

Run this once before run_invest_baseline.py.
"""
import json
import numpy as np
import rasterio
from rasterio.transform import from_bounds
import geopandas as gpd
from shapely.geometry import box

LULC_PATH = "data/mumbai_LULC_utm.tif"  # reprojected to EPSG:32643 (meters) — required by InVEST
LST_PATH = "data/mumbai_LST_2026_Q1.tif"  # same quarter as the LULC's Sentinel-2 source
OUT_DIR = "data/invest_inputs"

import os
os.makedirs(OUT_DIR, exist_ok=True)

# ---- 1. Reference evapotranspiration (ET0) raster ----
# We don't have a real ET0 product yet, so this uses a single reasonable constant value
# for tropical coastal Mumbai (~5 mm/day is a common default for this climate).
# This is a known approximation — flagged clearly, worth refining later with real ERA5-derived ET0.
ET0_CONSTANT_MM_PER_DAY = 5.0

with rasterio.open(LULC_PATH) as src:
    lulc_shape = src.shape
    lulc_transform = src.transform
    lulc_crs = src.crs
    lulc_bounds = src.bounds

et0_array = np.full(lulc_shape, ET0_CONSTANT_MM_PER_DAY, dtype=np.float32)
et0_profile = {
    "driver": "GTiff", "height": lulc_shape[0], "width": lulc_shape[1],
    "count": 1, "dtype": "float32", "crs": lulc_crs, "transform": lulc_transform,
}
et0_path = f"{OUT_DIR}/et0_constant.tif"
with rasterio.open(et0_path, "w", **et0_profile) as dst:
    dst.write(et0_array, 1)
print(f"Saved constant ET0 raster ({ET0_CONSTANT_MM_PER_DAY} mm/day) -> {et0_path}")

# ---- 2. AOI boundary vector, from the LULC raster's own extent ----
aoi_geom = box(lulc_bounds.left, lulc_bounds.bottom, lulc_bounds.right, lulc_bounds.top)
aoi_gdf = gpd.GeoDataFrame({"id": [1]}, geometry=[aoi_geom], crs=lulc_crs)
aoi_path = f"{OUT_DIR}/aoi_boundary.shp"
aoi_gdf.to_file(aoi_path)
print(f"Saved AOI boundary -> {aoi_path}")

# ---- 3. t_ref and uhi_max, computed from real LST data ----
with rasterio.open(LST_PATH) as src:
    lst_data = src.read(1)
valid = lst_data[~np.isnan(lst_data)]
p2 = float(np.nanpercentile(valid, 2))
p98 = float(np.nanpercentile(valid, 98))

t_ref = p2                 # coolest observed areas approximate the "rural/baseline" reference temp
uhi_max = p98 - p2         # observed hot-to-cool spread approximates max UHI magnitude

print(f"\nComputed from real 2026 Q1 LST data:")
print(f"  t_ref   (reference/rural temp) = {t_ref:.2f} °C")
print(f"  uhi_max (max UHI magnitude)    = {uhi_max:.2f} °C")

# ---- Save everything InVEST needs as one params file ----
params = {
    "et0_raster_path": et0_path,
    "aoi_vector_path": aoi_path,
    "lulc_raster_path": LULC_PATH,
    "t_ref": round(t_ref, 2),
    "uhi_max": round(uhi_max, 2),
}
with open(f"{OUT_DIR}/invest_params.json", "w") as f:
    json.dump(params, f, indent=2)
print(f"\nSaved all parameters -> {OUT_DIR}/invest_params.json")
print("Ready to run: python pipeline/run_invest_baseline.py")