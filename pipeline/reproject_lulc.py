"""
Reprojects the LULC raster from EPSG:4326 (degrees) to EPSG:32643 (UTM Zone 43N, meters).
InVEST's Urban Cooling Model requires a projected, meter-based CRS since its cooling-distance
parameters are specified in meters — running it directly on geographic (lat/lon) data causes
wildly incorrect internal distance-to-pixel conversions.

Uses NEAREST-neighbor resampling deliberately: LULC is categorical data (1=Water, 2=Vegetation,
3=Built-up), so any smoother resampling method (bilinear/cubic) would invent invalid fractional
class values between categories, which would corrupt the classification.
"""
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling

SRC_PATH = "data/mumbai_LULC.tif"
DST_PATH = "data/mumbai_LULC_utm.tif"
DST_CRS = "EPSG:32643"  # UTM Zone 43N — correct projected zone for Mumbai

with rasterio.open(SRC_PATH) as src:
    transform, width, height = calculate_default_transform(
        src.crs, DST_CRS, src.width, src.height, *src.bounds
    )
    profile = src.profile.copy()
    profile.update({
        "crs": DST_CRS,
        "transform": transform,
        "width": width,
        "height": height,
    })

    with rasterio.open(DST_PATH, "w", **profile) as dst:
        reproject(
            source=rasterio.band(src, 1),
            destination=rasterio.band(dst, 1),
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform,
            dst_crs=DST_CRS,
            resampling=Resampling.nearest,  # required for categorical data
        )

with rasterio.open(DST_PATH) as check:
    print(f"Saved reprojected LULC -> {DST_PATH}")
    print(f"New CRS: {check.crs}")
    print(f"New dimensions: {check.width} x {check.height}")
    print(f"Pixel size: {check.res}")  # should now show meters, e.g. ~(10.0, 10.0)