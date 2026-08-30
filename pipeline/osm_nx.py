import osmnx as ox

lon_min, lat_min, lon_max, lat_max = 72.5833, 18.7833, 73.2000, 19.6000
bbox = (lon_min, lat_min, lon_max, lat_max)  # (west, south, east, north)

buildings = ox.features_from_bbox(bbox, tags={"building": True})
buildings.to_file("data/raw/osm/osm_buildings.geojson", driver="GeoJSON")
print(f"{len(buildings)} building features saved")