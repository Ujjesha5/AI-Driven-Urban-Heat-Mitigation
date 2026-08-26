import rasterio
from rasterio.warp import reproject, Resampling
import datetime
import os

def generate_quarters(start_year=2023, end_date=None):
    if end_date is None:
        end_date = datetime.date.today()
    quarters = []
    year = start_year
    while True:
        for i, q_start_month in enumerate([1, 4, 7, 10], start=1):
            q_start = datetime.date(year, q_start_month, 1)
            if q_start > end_date:
                return quarters
            q_end_month = q_start_month + 2
            q_end = (datetime.date(year, 12, 31) if q_end_month == 12
                      else datetime.date(year, q_end_month + 1, 1) - datetime.timedelta(days=1))
            q_end = min(q_end, end_date)
            quarters.append({"start": q_start.isoformat(), "end": q_end.isoformat(), "label": f"{year}_Q{i}"})
        year += 1

def resample_to_match(src_path, ref_path, out_path):
    with rasterio.open(ref_path) as ref:
        ref_transform, ref_crs = ref.transform, ref.crs
        ref_width, ref_height = ref.width, ref.height

    with rasterio.open(src_path) as src:
        kwargs = src.meta.copy()
        kwargs.update({"crs": ref_crs, "transform": ref_transform, "width": ref_width, "height": ref_height})
        with rasterio.open(out_path, "w", **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform, src_crs=src.crs,
                    dst_transform=ref_transform, dst_crs=ref_crs,
                    resampling=Resampling.bilinear
                )

quarters = generate_quarters(start_year=2023)

# Per-quarter: align that quarter's NDVI/NDBI to that quarter's LST grid
for q in quarters:
    label = q["label"]
    lst_path = f"data/raw/lst_LANDSAT/mumbai_LST_{label}.tif"
    ndvi_path = f"data/processed/ndvi_s2/ndvi_{label}.tif"
    ndbi_path = f"data/processed/ndbi_s2/ndbi_{label}.tif"

    if not os.path.exists(lst_path) or not os.path.exists(ndvi_path):
        print(f"{label}: missing LST or NDVI, skipping alignment")
        continue

    resample_to_match(ndvi_path, lst_path, f"data/processed/ndvi_aligned/ndvi_aligned_{label}.tif")
    print(f"{label}: NDVI aligned")

    if os.path.exists(ndbi_path):
        resample_to_match(ndbi_path, lst_path, f"data/processed/ndbi_aligned/ndbi_aligned_{label}.tif")
        print(f"{label}: NDBI aligned")

# Static layers -- align ONCE using any quarter's LST as the reference grid
reference_lst = f"data/raw/lst_LANDSAT/mumbai_LST_{quarters[0]['label']}.tif"
static_layers = {
    "dem": "data/raw/dem/mumbai_DEM.tif",       # adjust paths to match your actual folders
    "slope": "data/raw/dem/mumbai_slope.tif",
    "building_height": "data/raw/morphology/ghsl/ghsl_building_height_merged.tif",
    # add building height path once downloaded from GHSL, e.g. "building_height": "data/raw/ghsl/height.tif"
}

for name, path in static_layers.items():
    if os.path.exists(path):
        resample_to_match(path, reference_lst, f"data/processed/{name}_aligned.tif")
        print(f"{name}: aligned (one-time, applies to all quarters)")
    else:
        print(f"{name}: file not found at {path} -- update the path or skip for now")

print("\nAlignment complete")