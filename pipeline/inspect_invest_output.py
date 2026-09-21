"""
Inspects InVEST's baseline T_air output: reads InVEST's own AOI-wide summary stats,
computes pixel-level stats directly from the raster, and renders a colored preview
image for visual comparison against your real 2026 Q1 LST map.
"""
import pickle
import numpy as np
import rasterio
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

WORKSPACE = "model/invest_output/baseline"

# ---- InVEST's own precomputed AOI-wide stats ----
print("=== InVEST's own AOI-wide summary stats ===")
with open(f"{WORKSPACE}/intermediate/t_air_aoi_stats_baseline.pickle", "rb") as f:
    t_air_stats = pickle.load(f)
print("T_air stats:", t_air_stats)

with open(f"{WORKSPACE}/intermediate/cc_ref_aoi_stats_baseline.pickle", "rb") as f:
    cc_stats = pickle.load(f)
print("Cooling Capacity (CC) stats:", cc_stats)

# ---- Pixel-level stats computed directly from the raster ----
print("\n=== T_air_baseline.tif — pixel-level stats ===")
with rasterio.open(f"{WORKSPACE}/T_air_baseline.tif") as src:
    t_air = src.read(1)
    nodata = src.nodata
    crs = src.crs
    bounds = src.bounds

valid_mask = ~np.isnan(t_air)
if nodata is not None:
    valid_mask &= (t_air != nodata)
valid = t_air[valid_mask]

print(f"CRS: {crs}")
print(f"Valid pixels: {valid.size:,} / {t_air.size:,} ({100*valid.size/t_air.size:.1f}%)")
print(f"Mean: {np.nanmean(valid):.2f} °C")
print(f"2nd percentile: {np.nanpercentile(valid, 2):.2f} °C")
print(f"98th percentile: {np.nanpercentile(valid, 98):.2f} °C")

print("\n=== For comparison — real observed 2026 Q1 LST (from earlier script) ===")
print("Mean: 29.22 °C | 2nd pct: 24.73 °C | 98th pct: 36.64 °C")

# ---- Visual preview, same style as the Hotspot Map, for a side-by-side look ----
cmap = plt.colormaps["RdYlBu_r"].copy()
cmap.set_bad(color=(0, 0, 0, 0))
t_air_display = np.where(valid_mask, t_air, np.nan)
vmin, vmax = np.nanpercentile(valid, 2), np.nanpercentile(valid, 98)
norm = mcolors.Normalize(vmin=vmin, vmax=vmax, clip=True)
rgba = cmap(norm(t_air_display))
plt.imsave("data/_invest_tair_preview.png", rgba)
print(f"\nSaved visual preview -> data/_invest_tair_preview.png")
print("Compare this against your earlier 2026 Q1 Hotspot Map screenshot:")
print("do the hot/cool zones (bright red vs. blue) fall in roughly the same places?")