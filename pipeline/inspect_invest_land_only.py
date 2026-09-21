"""
Recomputes T_air stats and preview EXCLUDING water pixels, since the ocean sits directly
on the unbuffered AOI boundary and suffers a known convolution edge-effect artifact
(appears artificially hot). Land pixels (vegetation + built-up) are unaffected by this
specific issue and give a much more trustworthy comparison against real LST.
"""
import numpy as np
import rasterio
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

WORKSPACE = "model/invest_output/baseline"

with rasterio.open(f"{WORKSPACE}/T_air_baseline.tif") as src:
    t_air = src.read(1)
    t_air_transform = src.transform
    t_air_shape = t_air.shape
    t_air_nodata = src.nodata

with rasterio.open("data/mumbai_LULC_utm.tif") as src:
    lulc = src.read(1)

# LULC and T_air should already share the same grid (T_air was computed FROM this LULC file),
# but confirm shapes match before masking.
assert lulc.shape == t_air_shape, f"Shape mismatch: LULC {lulc.shape} vs T_air {t_air_shape}"

# Exclude water, NaN, the raster's declared nodata value, AND anything physically
# implausible as a safety net (nodata sentinels are sometimes not caught by exact
# equality due to float precision, e.g. -3.4028e38).
valid = ~np.isnan(t_air)
if t_air_nodata is not None:
    valid &= ~np.isclose(t_air, t_air_nodata, rtol=1e-3)
valid &= (t_air > -50) & (t_air < 100)  # sane physical bounds for air temperature

land_mask = (lulc != 1) & valid
land_t_air = t_air[land_mask]

print("=== T_air — LAND ONLY (water excluded, avoids AOI edge artifact) ===")
print(f"Land pixels used: {land_t_air.size:,} / {t_air.size:,} ({100*land_t_air.size/t_air.size:.1f}%)")
print(f"Mean: {np.nanmean(land_t_air):.2f} °C")
print(f"2nd percentile: {np.nanpercentile(land_t_air, 2):.2f} °C")
print(f"98th percentile: {np.nanpercentile(land_t_air, 98):.2f} °C")

print("\n=== For comparison — real observed 2026 Q1 LST ===")
print("Mean: 29.22 °C | 2nd pct: 24.73 °C | 98th pct: 36.64 °C")

# Preview with water masked to transparent, so the artifact doesn't dominate the image
cmap = plt.colormaps["RdYlBu_r"].copy()
cmap.set_bad(color=(0, 0, 0, 0))
t_air_land_only = np.where(land_mask, t_air, np.nan)
vmin, vmax = np.nanpercentile(land_t_air, 2), np.nanpercentile(land_t_air, 98)
norm = mcolors.Normalize(vmin=vmin, vmax=vmax, clip=True)
rgba = cmap(norm(t_air_land_only))
plt.imsave("data/_invest_tair_land_only.png", rgba)
print("\nSaved -> data/_invest_tair_land_only.png (water masked out this time)")