import rasterio
import numpy as np
import matplotlib.pyplot as plt

with rasterio.open("data/mumbai_S2_2026_Q1.tif") as src:
    blue = src.read(1).astype(np.float32)
    green = src.read(2).astype(np.float32)
    red = src.read(3).astype(np.float32)
    nir = src.read(4).astype(np.float32)
    swir = src.read(5).astype(np.float32)
    profile = src.profile
    transform = src.transform
    crs = src.crs

# NDVI: vegetation index
ndvi = (nir - red) / (nir + red + 1e-6)

# MNDWI: water index (Green vs SWIR)
mndwi = (green - swir) / (green + swir + 1e-6)

# Classification: 1 = water, 2 = vegetation, 3 = built-up/bare
lulc = np.full(ndvi.shape, 3, dtype=np.uint8)  # default: built-up/bare
lulc[ndvi > 0.3] = 2                            # vegetation
lulc[mndwi > 0.0] = 1                           # water (overrides veg if both true)

# Save the classified raster
out_profile = profile.copy()
out_profile.update(dtype=rasterio.uint8, count=1, nodata=0)
with rasterio.open("data/mumbai_LULC.tif", "w", **out_profile) as dst:
    dst.write(lulc, 1)

print("Saved data/mumbai_LULC.tif")
print("Class breakdown:")
total = lulc.size
for cls, name in [(1, "Water"), (2, "Vegetation"), (3, "Built-up/bare")]:
    count = (lulc == cls).sum()
    print(f"  {name}: {count:,} pixels ({100*count/total:.1f}%)")

# Quick visual sanity check
colors = {1: [0.29, 0.56, 0.77], 2: [0.18, 0.49, 0.42], 3: [0.85, 0.38, 0.23]}
rgb = np.zeros((*lulc.shape, 3))
for cls, color in colors.items():
    mask = lulc == cls
    for ch in range(3):
        rgb[:, :, ch][mask] = color[ch]
plt.imsave("data/_lulc_preview.png", rgb)
print("\nSaved visual preview to data/_lulc_preview.png — open it and check:")
print("  - Blue areas should match the Arabian Sea / coastline")
print("  - Green areas should match known parks (e.g. Sanjay Gandhi National Park, north Mumbai)")
print("  - Orange/coral areas should match the dense urban core")