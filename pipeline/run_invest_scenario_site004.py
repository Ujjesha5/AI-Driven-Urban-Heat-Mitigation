"""
Models the "Cool roofs" intervention at SITE-004 (BKC Commercial Hub):
  1. Reclassifies a ~300x300m footprint around the site's real coordinates from
     Built-up (class 3) to a new class "Cool-roof built-up" (class 4) — same
     shade/ET as regular built-up, but higher albedo (reflective coating).
  2. Writes an updated biophysical table including this new class.
  3. Runs InVEST on the modified LULC.
"""
import numpy as np
import rasterio
from pyproj import Transformer
from natcap.invest import urban_cooling_model

LULC_PATH = "data/mumbai_LULC_utm.tif"
SITE_LAT, SITE_LON = 19.07546, 72.87062  # SITE-004, BKC Commercial Hub
FOOTPRINT_METERS = 1000  # ~300x300m intervention area

# ---- Step 1: convert site's real-world lat/lon into a pixel location on the LULC grid ----
with rasterio.open(LULC_PATH) as src:
    lulc = src.read(1)
    transform = src.transform
    crs = src.crs
    profile = src.profile.copy()

transformer = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
site_x, site_y = transformer.transform(SITE_LON, SITE_LAT)
site_row, site_col = rasterio.transform.rowcol(transform, site_x, site_y)
print(f"Site pixel location: row={site_row}, col={site_col}")

# ---- Step 2: reclassify a footprint square around that pixel ----
pixel_size = transform[0]  # meters per pixel
footprint_px = int(FOOTPRINT_METERS / pixel_size / 2)  # half-width in pixels
r0, r1 = site_row - footprint_px, site_row + footprint_px
c0, c1 = site_col - footprint_px, site_col + footprint_px

scenario_lulc = lulc.copy()
footprint = scenario_lulc[r0:r1, c0:c1]
was_builtup = (footprint == 3)
footprint[was_builtup] = 4  # reclassify only built-up pixels within the footprint
scenario_lulc[r0:r1, c0:c1] = footprint
n_changed = was_builtup.sum()
print(f"Reclassified {n_changed:,} built-up pixels to cool-roof (class 4) "
      f"within a {FOOTPRINT_METERS}x{FOOTPRINT_METERS}m footprint")

scenario_lulc_path = "data/mumbai_LULC_utm_scenario_site004.tif"
with rasterio.open(scenario_lulc_path, "w", **profile) as dst:
    dst.write(scenario_lulc, 1)
print(f"Saved -> {scenario_lulc_path}")

# ---- Step 3: write a biophysical table including the new cool-roof class ----
biophysical_scenario_path = "data/biophysical_table_scenario_site004.csv"
with open(biophysical_scenario_path, "w") as f:
    f.write("lucode,lulc_name,shade,albedo,kc,green_area\n")
    f.write("1,Water,0,0.06,1.05,1\n")
    f.write("2,Vegetation,0.6,0.18,0.85,1\n")
    f.write("3,Built-up/bare,0.05,0.12,0.2,0\n")
    f.write("4,Cool-roof built-up,0.05,0.5,0.2,0\n")  # same as built-up, higher albedo only
print(f"Saved -> {biophysical_scenario_path}")

# ---- Step 4: run InVEST on the modified LULC (reusing baseline et0/AOI/t_ref/uhi_max) ----
import json
with open("data/invest_inputs/invest_params.json") as f:
    params = json.load(f)

args = {
    "workspace_dir": "model/invest_output/scenario_site004",
    "results_suffix": "site004",
    "t_ref": params["t_ref"],
    "lulc_raster_path": scenario_lulc_path,
    "ref_eto_raster_path": params["et0_raster_path"],
    "aoi_vector_path": params["aoi_vector_path"],
    "biophysical_table_path": biophysical_scenario_path,
    "green_area_cooling_distance": 450,
    "t_air_average_radius": 500,
    "uhi_max": params["uhi_max"],
    "cc_method": "factors",
    "cc_weight_shade": 0.6,
    "cc_weight_albedo": 0.2,
    "cc_weight_eti": 0.2,
    "do_energy_valuation": False,
    "do_productivity_valuation": False,
}

print("\nRunning InVEST on the cool-roofs scenario...")
urban_cooling_model.execute(args)
print("Done. Check model/invest_output/scenario_site004/")