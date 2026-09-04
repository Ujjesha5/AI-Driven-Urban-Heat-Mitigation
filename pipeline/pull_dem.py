import ee

ee.Initialize(project="velvety-gearbox-451304-s0")

lon_min, lat_min, lon_max, lat_max = 72.5833, 18.7833, 73.2000, 19.6000
city_bbox = ee.Geometry.Rectangle([lon_min, lat_min, lon_max, lat_max])

# Copernicus DEM GLO-30, 2024_1 release -- 30m global elevation. Uses the updated
# dataset ID (older "COPERNICUS/DEM/GLO30" is deprecated as of this release).
collection = ee.ImageCollection("COPERNICUS/DEM/GLO30_2024_1")

# Set the mosaic's default projection to the DEM's native projection. Without this,
# Earth Engine defaults any computation on a mosaicked collection to a coarse 1-degree
# WGS84 grid -- this was silently producing near-constant, meaningless slope values
# (a teammate's review caught a suspiciously narrow 0.146-0.167 range and flagged it).
# Fix confirmed against Google's own sample code for this dataset:
# https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_DEM_GLO30
native_proj = collection.first().projection()
dem = collection.mosaic().setDefaultProjection(native_proj).select("DEM")

# Reproject to a metric UTM CRS before computing slope -- ee.Terrain.slope needs x/y
# units to match elevation units (meters). Computing it directly on a lat/lon (degree-
# based) grid divides real elevation differences by enormous degree-based horizontal
# spacing, producing near-flat, physically meaningless output.
utm_crs = "EPSG:32643"  # UTM zone 43N, covers Mumbai
dem_utm = dem.reproject(crs=utm_crs, scale=30)
slope = ee.Terrain.slope(dem_utm)

for img, name in [(dem, "DEM"), (slope, "slope")]:
    task = ee.batch.Export.image.toDrive(
        image=img.clip(city_bbox),
        description=f"mumbai_{name}",
        folder="urban_heat_project/raw_DEM",
        region=city_bbox,
        scale=30,
        crs="EPSG:4326"  # export in WGS84 to stay consistent with the rest of the pipeline
    )
    task.start()

print("DEM + slope exports started — check Google Drive in a few minutes")