"""
Compares InVEST's predicted cooling at SITE-004 (from the baseline vs. cool-roofs scenario
runs) against the ML model's independently predicted reduction for the same site — the
actual two-methods cross-validation result promised in the paper's Evaluation Metrics section.
"""
import numpy as np
import rasterio
from pyproj import Transformer

SITE_LAT, SITE_LON = 19.07546, 72.87062
FOOTPRINT_METERS = 1000
ML_PREDICTED_REDUCTION = 3.2  # from candidate_intervention_sites.csv, SITE-004


def load_and_clean(path):
    with rasterio.open(path) as src:
        data = src.read(1)
        nodata = src.nodata
        transform = src.transform
        crs = src.crs
    valid = ~np.isnan(data)
    if nodata is not None:
        valid &= ~np.isclose(data, nodata, rtol=1e-3)
    valid &= (data > -50) & (data < 100)
    return data, valid, transform, crs


baseline, baseline_valid, transform, crs = load_and_clean(
    "model/invest_output/baseline/T_air_baseline.tif"
)
scenario, scenario_valid, _, _ = load_and_clean(
    "model/invest_output/scenario_site004/T_air_site004.tif"
)

transformer = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
site_x, site_y = transformer.transform(SITE_LON, SITE_LAT)
site_row, site_col = rasterio.transform.rowcol(transform, site_x, site_y)

pixel_size = transform[0]
footprint_px = int(FOOTPRINT_METERS / pixel_size / 2)
r0, r1 = site_row - footprint_px, site_row + footprint_px
c0, c1 = site_col - footprint_px, site_col + footprint_px

baseline_footprint = baseline[r0:r1, c0:c1]
scenario_footprint = scenario[r0:r1, c0:c1]
mask_footprint = baseline_valid[r0:r1, c0:c1] & scenario_valid[r0:r1, c0:c1]

baseline_mean = np.nanmean(baseline_footprint[mask_footprint])
scenario_mean = np.nanmean(scenario_footprint[mask_footprint])
invest_reduction = baseline_mean - scenario_mean

print("=== SITE-004 (BKC Commercial Hub) — Cool Roofs Intervention ===")
print(f"Valid pixels in footprint: {mask_footprint.sum():,}")
print(f"\nInVEST baseline T_air (footprint mean):  {baseline_mean:.3f} °C")
print(f"InVEST scenario T_air (footprint mean):  {scenario_mean:.3f} °C")
print(f"InVEST predicted reduction:               {invest_reduction:.3f} °C")
print(f"\nML model predicted reduction:             {ML_PREDICTED_REDUCTION:.2f} °C")
print(f"\nDifference between methods:               {abs(invest_reduction - ML_PREDICTED_REDUCTION):.3f} °C")