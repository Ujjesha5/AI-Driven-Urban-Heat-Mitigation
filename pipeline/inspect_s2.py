import rasterio
import numpy as np

with rasterio.open("data/mumbai_S2_2026_Q1.tif") as src:
    print("Bands:", src.count)
    print("Dtype:", src.dtypes[0])
    print("CRS:", src.crs)
    print("Width x Height:", src.width, src.height)
    print("NoData value:", src.nodata)

    for i in range(1, src.count + 1):
        band = src.read(i)
        total = band.size
        valid = band[~np.isnan(band)]
        valid_count = valid.size
        print(f"\nBand {i}:")
        print(f"  Valid pixels: {valid_count:,} / {total:,} ({100*valid_count/total:.1f}%)")
        if valid_count > 0:
            print(f"  Min (valid): {np.nanmin(band):.4f}")
            print(f"  Max (valid): {np.nanmax(band):.4f}")
            print(f"  Mean (valid): {np.nanmean(band):.4f}")
        else:
            print("  ALL PIXELS ARE NaN — band appears empty")