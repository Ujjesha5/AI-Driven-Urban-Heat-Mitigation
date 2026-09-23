"""
Runs InVEST's Urban Cooling Model baseline scenario using the inputs prepared by
prepare_invest_inputs.py and the biophysical table you already have.

Output lands in model/invest_output/baseline/ — the key file to check afterward is
intermediate/T_air.tif (predicted air temperature) or similar named output, which we'll
compare against real observed LST in the next step.
"""
import json
from natcap.invest import urban_cooling_model

with open("data/invest_inputs/invest_params.json") as f:
    params = json.load(f)

args = {
    "workspace_dir": "model/invest_output/baseline",
    "results_suffix": "baseline",
    "t_ref": params["t_ref"],
    "lulc_raster_path": params["lulc_raster_path"],
    "ref_eto_raster_path": params["et0_raster_path"],
    "aoi_vector_path": params["aoi_vector_path"],
    "biophysical_table_path": "data/biophysical_table.csv",
    "green_area_cooling_distance": 450,   # standard InVEST default (meters)
    "t_air_average_radius": 500,          # standard InVEST default (meters)
    "uhi_max": params["uhi_max"],
    "cc_method": "factors",
    "cc_weight_shade": 0.6,
    "cc_weight_albedo": 0.2,
    "cc_weight_eti": 0.2,
    "do_energy_valuation": False,
    "do_productivity_valuation": False,
}

print("Running InVEST Urban Cooling Model with:")
for k, v in args.items():
    print(f"  {k}: {v}")

urban_cooling_model.execute(args)

print("\nDone. Check model/invest_output/baseline/ for results.")
print("Look for the predicted air temperature raster (commonly named T_air.tif or similar)")
print("in the workspace or its 'intermediate' subfolder.")