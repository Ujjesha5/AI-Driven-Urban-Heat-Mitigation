"""
Compares InVEST's predicted T_air (land only, water excluded) against real
observed LST for the same quarter -- both computed live from their source
rasters, so this stays correct if either file is ever reprocessed.

Water pixels are excluded from the InVEST side because the ocean sits directly
on the unbuffered AOI boundary and suffers a known convolution edge-effect
artifact (appears artificially hot). Land pixels (vegetation + built-up) are
unaffected by this specific issue and give a much more trustworthy comparison.

Note: T_air/LULC live on the UTM-reprojected InVEST grid, while the raw LST
pull is in EPSG:4326 at native Landsat resolution (see pipeline/pull_lst.py).
The two rasters are NOT on a shared grid, so this script reports each side's
own summary stats (mean / 2nd / 98th percentile) for comparison -- it does
NOT attempt a pixel-by-pixel correlation, which would require reprojecting
one onto the other's grid first (that's a separate, heavier step -- ask if
you want that built too).
"""
import numpy as np
import rasterio
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

WORKSPACE = "model/invest_output/baseline"
QUARTER = "2026_Q1"  # must match the quarter mumbai_LULC_utm.tif was built from
REAL_LST_PATH = f"data/mumbai_LST_{QUARTER}.tif"


def load_and_clean(path, nodata_override=None):
    """Same cleaning approach used elsewhere in the project: drop NaN, drop the
    raster's declared nodata (with a tolerance, since some nodata sentinels
    like -3.4028e38 don't survive exact float equality), and clip to sane
    physical bounds for a temperature raster."""
    with rasterio.open(path) as src:
        data = src.read(1)
        nodata = nodata_override if nodata_override is not None else src.nodata

    valid = ~np.isnan(data)
    if nodata is not None:
        valid &= ~np.isclose(data, nodata, rtol=1e-3)
    valid &= (data > -50) & (data < 100)
    return data, valid


def summarize(values, label):
    print(f"{label}")
    print(f"  Pixels used: {values.size:,}")
    print(f"  Mean:            {np.nanmean(values):.2f} °C")
    print(f"  2nd percentile:  {np.nanpercentile(values, 2):.2f} °C")
    print(f"  98th percentile: {np.nanpercentile(values, 98):.2f} °C")


# ---- InVEST T_air, land only ----
t_air, t_air_valid = load_and_clean(f"{WORKSPACE}/T_air_baseline.tif")

with rasterio.open("data/mumbai_LULC_utm.tif") as src:
    lulc = src.read(1)

assert lulc.shape == t_air.shape, f"Shape mismatch: LULC {lulc.shape} vs T_air {t_air.shape}"

land_mask = (lulc != 1) & t_air_valid
land_t_air = t_air[land_mask]

print(f"=== InVEST T_air — LAND ONLY, {QUARTER} (water excluded, avoids AOI edge artifact) ===")
print(f"Land pixels used: {land_t_air.size:,} / {t_air.size:,} ({100 * land_t_air.size / t_air.size:.1f}%)")
print(f"Mean: {np.nanmean(land_t_air):.2f} °C")
print(f"2nd percentile: {np.nanpercentile(land_t_air, 2):.2f} °C")
print(f"98th percentile: {np.nanpercentile(land_t_air, 98):.2f} °C")

# ---- Real observed LST, same quarter, computed live ----
print(f"\n=== Real observed LST — {QUARTER} (computed live from {REAL_LST_PATH}) ===")
try:
    real_lst, real_lst_valid = load_and_clean(REAL_LST_PATH)
    real_lst_values = real_lst[real_lst_valid]
    print(f"Valid pixels used: {real_lst_values.size:,} / {real_lst.size:,} "
          f"({100 * real_lst_values.size / real_lst.size:.1f}%)")
    print(f"Mean: {np.nanmean(real_lst_values):.2f} °C")
    print(f"2nd percentile: {np.nanpercentile(real_lst_values, 2):.2f} °C")
    print(f"98th percentile: {np.nanpercentile(real_lst_values, 98):.2f} °C")
    real_lst_mean = float(np.nanmean(real_lst_values))
except FileNotFoundError:
    print(f"WARNING: {REAL_LST_PATH} not found -- skipping live comparison.")
    real_lst_mean = None

# ---- Side-by-side summary ----
print(f"\n=== Side-by-side, {QUARTER} ===")
print(f"{'':20} {'InVEST (land)':>15} {'Real LST':>15} {'Diff':>10}")
if real_lst_mean is not None:
    invest_mean = float(np.nanmean(land_t_air))
    diff = invest_mean - real_lst_mean
    print(f"{'Mean °C':20} {invest_mean:>15.2f} {real_lst_mean:>15.2f} {diff:>10.2f}")
else:
    print("  (real LST unavailable, see warning above)")

# ---- Preview, water masked to transparent ----
cmap = plt.colormaps["RdYlBu_r"].copy()
cmap.set_bad(color=(0, 0, 0, 0))
t_air_land_only = np.where(land_mask, t_air, np.nan)
vmin, vmax = np.nanpercentile(land_t_air, 2), np.nanpercentile(land_t_air, 98)
norm = mcolors.Normalize(vmin=vmin, vmax=vmax, clip=True)
rgba = cmap(norm(t_air_land_only))
plt.imsave("data/_invest_tair_land_only.png", rgba)
print("\nSaved -> data/_invest_tair_land_only.png (water masked out)")