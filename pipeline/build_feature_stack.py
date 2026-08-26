import rasterio
import numpy as np
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

quarters = generate_quarters(start_year=2023)

# Static layers, aligned once in Step 4, reused for every quarter
static_paths = ["data/processed/dem_aligned.tif", "data/processed/slope_aligned.tif", "data/processed/building_height_aligned.tif"]

for q in quarters:
    label = q["label"]
    ndvi_path = f"data/processed/ndvi_aligned/ndvi_aligned_{label}.tif"
    ndbi_path = f"data/processed/ndbi_aligned/ndbi_aligned_{label}.tif"

    if not os.path.exists(ndvi_path):
        print(f"{label}: no aligned NDVI, skipping feature stack")
        continue

    layers = [ndvi_path]
    if os.path.exists(ndbi_path):
        layers.append(ndbi_path)
    layers += [p for p in static_paths if os.path.exists(p)]

    arrays = []
    profile = None
    for path in layers:
        with rasterio.open(path) as src:
            arrays.append(src.read(1))
            if profile is None:
                profile = src.profile

    stack = np.stack(arrays)
    profile.update(count=len(layers))
    with rasterio.open(f"data/processed/feature_stack/feature_stack_{label}.tif", "w", **profile) as dst:
        dst.write(stack)

    print(f"{label}: feature stack built ({len(layers)} layers)")

print("\nDone -- feature stacks built for all available quarters")