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
os.makedirs("data/processed", exist_ok=True)

for q in quarters:
    label = q["label"]
    s2_path = f"data/raw/s2_SENTINEL2/mumbai_S2_{label}.tif"  # adjust to match your actual folder name

    if not os.path.exists(s2_path):
        print(f"{label}: S2 file not found, skipping")
        continue

    with rasterio.open(s2_path) as src:
        bands = src.read()  # order: B2 blue, B3 green, B4 red, B8 NIR, B11 SWIR
        profile = src.profile

    if bands.shape[0] < 5:
        print(f"{label}: only {bands.shape[0]} bands found, expected 5 -- NDBI skipped for this quarter")
        blue, green, red, nir = bands[0], bands[1], bands[2], bands[3]
        swir = None
    else:
        blue, green, red, nir, swir = bands[0], bands[1], bands[2], bands[3], bands[4]

    # NDVI = (NIR - Red) / (NIR + Red) -- vegetation index
    ndvi = (nir.astype(float) - red.astype(float)) / (nir + red + 1e-6)

    out_profile = profile.copy()
    out_profile.update(count=1, dtype="float32")
    with rasterio.open(f"data/processed/ndvi_{label}.tif", "w", **out_profile) as dst:
        dst.write(ndvi.astype("float32"), 1)

    if swir is not None:
        # NDBI = (SWIR - NIR) / (SWIR + NIR) -- built-up index
        ndbi = (swir.astype(float) - nir.astype(float)) / (swir + nir + 1e-6)
        with rasterio.open(f"data/processed/ndbi_{label}.tif", "w", **out_profile) as dst:
            dst.write(ndbi.astype("float32"), 1)

    print(f"{label}: NDVI{' + NDBI' if swir is not None else ''} computed")

print("\nDone -- NDVI/NDBI computed for all available quarters")