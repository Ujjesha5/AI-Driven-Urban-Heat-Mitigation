import rasterio
import numpy as np

def inspect(path):
    with rasterio.open(path) as src:
        print(f"\n--- {path} ---")
        print("CRS:", src.crs)
        print("Bounds:", src.bounds)
        print("Width x Height:", src.width, src.height)
        print("Number of bands:", src.count)
        data = src.read(1)
        valid = data[~np.isnan(data)]
        print("Total pixels:", data.size)
        print("Valid (non-NaN) pixels:", valid.size)
        print("Min value (ignoring NaN):", np.nanmin(data) if valid.size > 0 else "ALL NaN")
        print("Max value (ignoring NaN):", np.nanmax(data) if valid.size > 0 else "ALL NaN")
        print("NoData value:", src.nodata)

inspect("data/mumbai_LST_2026_Q1.tif")
inspect("data/mumbai_LST_2026_Q2.tif")
inspect("data/mumbai_DEM.tif")
inspect("data/mumbai_slope.tif")