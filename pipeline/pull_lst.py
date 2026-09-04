import ee
import datetime
import csv
import os

ee.Initialize(project="velvety-gearbox-451304-s0")

# Mumbai + surrounding region bounding box (replace with your city's coordinates)
lon_min, lat_min, lon_max, lat_max = 72.5833, 18.7833, 73.2000, 19.6000
city_bbox = ee.Geometry.Rectangle([lon_min, lat_min, lon_max, lat_max])

def generate_quarters(start_year=2023, end_date=None):
    """Builds a list of {start, end, label} dicts for every quarter from start_year to today."""
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

def mask_landsat_clouds(image):
    """Masks Fill, Dilated Cloud, Cirrus, Cloud, and Cloud Shadow -- all 5 relevant
    QA_PIXEL bits, per USGS Collection 2 guidance. An earlier version of this mask only
    checked Cloud + Cloud Shadow, which let thin cloud/cirrus edges through and caused
    physically impossible negative LST readings (verified against a teammate's review
    flagging a -10.46°C minimum in a Mumbai summer quarter -- see
    https://www.usgs.gov/landsat-missions/landsat-collection-2-known-issues)."""
    qa = image.select("QA_PIXEL")
    fill_bit = 1 << 0
    dilated_cloud_bit = 1 << 1
    cirrus_bit = 1 << 2
    cloud_bit = 1 << 3
    cloud_shadow_bit = 1 << 4
    mask = (qa.bitwiseAnd(fill_bit).eq(0)
            .And(qa.bitwiseAnd(dilated_cloud_bit).eq(0))
            .And(qa.bitwiseAnd(cirrus_bit).eq(0))
            .And(qa.bitwiseAnd(cloud_bit).eq(0))
            .And(qa.bitwiseAnd(cloud_shadow_bit).eq(0)))
    return image.updateMask(mask)

quarters = generate_quarters(start_year=2023)
print(f"Processing {len(quarters)} quarters: {quarters[0]['label']} to {quarters[-1]['label']}")

scene_log = []

for q in quarters:
    # Merge Landsat 8 and 9 so you're not missing half your potential scenes
    l8 = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
          .filterBounds(city_bbox).filterDate(q["start"], q["end"])
          .filter(ee.Filter.lt("CLOUD_COVER", 20)))
    l9 = (ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
          .filterBounds(city_bbox).filterDate(q["start"], q["end"])
          .filter(ee.Filter.lt("CLOUD_COVER", 20)))
    collection = l8.merge(l9)
    n = collection.size().getInfo()
    print(f"{q['label']}: {n} candidate scenes")

    if n == 0:
        print(f"  -> no usable scenes (likely monsoon cloud cover), skipping")
        continue

    # Cloud-mask each candidate, then mosaic -- fills the full AOI using the least-cloudy
    # pixels available across all scenes/tiles. A single .first() pick can leave large
    # gaps if your AOI spans more than one Landsat tile, or if the "least cloudy overall"
    # scene is still heavily clouded specifically over your area of interest.
    masked_sorted = collection.map(mask_landsat_clouds).sort("CLOUD_COVER")
    mosaic_image = masked_sorted.mosaic()

    # Representative date = the least-cloudy contributing scene's acquisition time.
    # Note: since the mosaic can draw pixels from more than one scene/date within the
    # quarter, this is an approximation, not an exact per-pixel timestamp -- worth a
    # one-line caveat in your methodology section if this feeds the research paper.
    rep_date = ee.Date(masked_sorted.first().get("system:time_start")).format("YYYY-MM-dd'T'HH:mm:ss").getInfo()
    scene_log.append({"quarter": q["label"], "scene_date_utc": rep_date})

    # Surface temperature band is ST_B10, needs scaling to Kelvin then to Celsius
    lst = mosaic_image.select("ST_B10").multiply(0.00341802).add(149.0).subtract(273.15)
    lst = lst.clip(city_bbox)

    task = ee.batch.Export.image.toDrive(
        image=lst,
        description=f"mumbai_LST_{q['label']}",
        folder="urban_heat_project/raw_LST",
        region=city_bbox,
        scale=30,
        crs="EPSG:4326"
    )
    task.start()
    print(f"  -> export started: mumbai_LST_{q['label']} (representative date: {rep_date})")

os.makedirs("data/processed", exist_ok=True)
with open("data/processed/lst_scene_dates.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["quarter", "scene_date_utc"])
    writer.writeheader()
    writer.writerows(scene_log)

print(f"\n{len(scene_log)} quarters exported and logged to data/processed/lst_scene_dates.csv")
print("Check https://code.earthengine.google.com/tasks for progress")