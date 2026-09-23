"""
Reprojects real observed LST onto InVEST's exact output grid, then computes the Pearson
correlation between InVEST's predicted air temperature and real satellite-observed LST,
on land pixels only (water excluded per the AOI edge-effect finding).
"""
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from scipy.stats import pearsonr

WORKSPACE = "model/invest_output/baseline"

# ---- Load InVEST's T_air (defines the target grid) ----
with rasterio.open(f"{WORKSPACE}/T_air_baseline.tif") as src:
    t_air = src.read(1)
    t_air_transform = src.transform
    t_air_crs = src.crs
    t_air_shape = src.shape
    t_air_nodata = src.nodata

# ---- Reproject real LST onto InVEST's grid (bilinear — LST is continuous, not categorical) ----
with rasterio.open("data/mumbai_LST_2026_Q1.tif") as src:
    lst_reprojected = np.empty(t_air_shape, dtype=np.float32)
    reproject(
        source=rasterio.band(src, 1),
        destination=lst_reprojected,
        src_transform=src.transform, src_crs=src.crs,
        dst_transform=t_air_transform, dst_crs=t_air_crs,
        resampling=Resampling.bilinear,
    )

# ---- Load LULC (same grid as T_air already) for the water mask ----
with rasterio.open("data/mumbai_LULC_utm.tif") as src:
    lulc = src.read(1)

# ---- Build the combined valid mask ----
valid = ~np.isnan(t_air) & ~np.isnan(lst_reprojected)
if t_air_nodata is not None:
    valid &= ~np.isclose(t_air, t_air_nodata, rtol=1e-3)
valid &= (t_air > -50) & (t_air < 100)
valid &= (lst_reprojected > -50) & (lst_reprojected < 100)
valid &= (lulc != 1)  # exclude water (AOI edge artifact)

t_air_valid = t_air[valid]
lst_valid = lst_reprojected[valid]
print(f"Matched valid land pixels: {t_air_valid.size:,}")

# ---- Subsample for speed/memory (500k points is more than enough for a stable correlation) ----
rng = np.random.default_rng(seed=42)
n_sample = min(500_000, t_air_valid.size)
idx = rng.choice(t_air_valid.size, size=n_sample, replace=False)

r, p = pearsonr(t_air_valid[idx], lst_valid[idx])

print(f"\n=== InVEST T_air vs. Real LST — Pearson correlation (land only, n={n_sample:,}) ===")
print(f"r = {r:.3f}")
print(f"p-value = {p:.2e}")
print(f"\nInVEST T_air (this sample): mean={t_air_valid[idx].mean():.2f}, "
      f"min={t_air_valid[idx].min():.2f}, max={t_air_valid[idx].max():.2f}")
print(f"Real LST (this sample):     mean={lst_valid[idx].mean():.2f}, "
      f"min={lst_valid[idx].min():.2f}, max={lst_valid[idx].max():.2f}")