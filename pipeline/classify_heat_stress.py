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

for q in quarters:
    label = q["label"]
    lst_path = f"data/raw/lst_LANDSAT/mumbai_LST_{label}.tif"

    if not os.path.exists(lst_path):
        print(f"{label}: LST file not found, skipping")
        continue

    with rasterio.open(lst_path) as src:
        lst = src.read(1)
        profile = src.profile

    valid = lst[~np.isnan(lst)]
    p33, p66 = np.percentile(valid, [33, 66])
    categories = np.where(np.isnan(lst), 255, np.digitize(lst, bins=[p33, p66]))  # 0=low, 1=medium, 2=high, 255=nodata

    profile.update(dtype="uint8", count=1, nodata=255)
    with rasterio.open(f"data/processed/heat_stress_lst/heat_stress_class_{label}.tif", "w", **profile) as dst:
        dst.write(categories.astype("uint8"), 1)

    print(f"{label}: classified (thresholds: {p33:.1f}°C / {p66:.1f}°C)")

print("\nDone -- heat stress classification complete for all available quarters")