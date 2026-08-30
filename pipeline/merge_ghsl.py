import rasterio
from rasterio.merge import merge
import glob

# Point this at wherever you saved both downloaded GHSL tiles
tile_paths = glob.glob("C:/Users/vishw/Downloads/ghsl/*.tif")  # adjust folder/pattern to match your files
print(f"Found {len(tile_paths)} tiles:", tile_paths)

datasets = [rasterio.open(p) for p in tile_paths]
merged_array, merged_transform = merge(datasets)

out_profile = datasets[0].profile.copy()
out_profile.update({
    "height": merged_array.shape[1],
    "width": merged_array.shape[2],
    "transform": merged_transform
})

with rasterio.open("data/raw/ghsl/ghsl_building_height_merged.tif", "w", **out_profile) as dst:
    dst.write(merged_array)

for ds in datasets:
    ds.close()

print("Merged tile saved to data/raw/ghsl/ghsl_building_height_merged.tif")