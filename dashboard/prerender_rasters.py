"""
Pre-renders the raw LST (per quarter) and DEM GeoTIFFs into small PNG overlays +
a stats JSON, so the deployed dashboard never needs to open a raw raster, run
rasterio, or touch matplotlib at runtime.

Run this LOCALLY, wherever the full raw GeoTIFFs live (data/mumbai_LST_*.tif,
data/mumbai_DEM.tif) -- typically after pulling them down from the shared Drive
folder per pipeline/README.md. Commit only the output of this script
(data/cache/*.png + data/cache/raster_cache.json) to the repo; keep the raw
tifs out of git, exactly as the README already says.

Safe to re-run as more quarters get downloaded locally: it merges into any
existing data/cache/raster_cache.json rather than overwriting it, so quarters
you rendered earlier (and may have since deleted locally to save disk) aren't
lost just because they're not present on this run.

Usage:
    python dashboard/prerender_rasters.py
"""
import glob
import json
import os
import re

import numpy as np
import rasterio
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt

DATA_DIR = "data"
CACHE_DIR = os.path.join(DATA_DIR, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def render_raster_to_png(data, vmin, vmax, out_path, cmap_name="RdYlBu_r"):
    cmap = plt.colormaps[cmap_name].copy()
    cmap.set_bad(color=(0, 0, 0, 0))
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax, clip=True)
    rgba = cmap(norm(data))
    plt.imsave(out_path, rgba)


def get_available_lst_quarters():
    files = glob.glob(os.path.join(DATA_DIR, "mumbai_LST_*.tif"))
    quarters = []
    for f in files:
        match = re.search(r"mumbai_LST_(\d{4}_Q\d)\.tif", os.path.basename(f))
        if match:
            quarters.append(match.group(1))
    return sorted(quarters)


def prerender_lst(quarter, cache):
    path = os.path.join(DATA_DIR, f"mumbai_LST_{quarter}.tif")
    with rasterio.open(path) as src:
        data = src.read(1)
        bounds = src.bounds

    valid = data[~np.isnan(data)]
    if valid.size == 0:
        print(f"  {quarter}: no valid pixels, skipping")
        return

    vmin = float(np.nanpercentile(valid, 2))
    vmax = float(np.nanpercentile(valid, 98))

    png_name = f"lst_{quarter}.png"
    png_path = os.path.join(CACHE_DIR, png_name)
    render_raster_to_png(data, vmin, vmax, png_path)

    cache["lst_quarters"][quarter] = {
        "png": f"cache/{png_name}",
        "bounds": [[bounds.bottom, bounds.left], [bounds.top, bounds.right]],
        "center": [(bounds.bottom + bounds.top) / 2, (bounds.left + bounds.right) / 2],
        "vmin": round(vmin, 3),
        "vmax": round(vmax, 3),
    }
    print(f"  {quarter}: rendered -> {png_path} (vmin={vmin:.1f}, vmax={vmax:.1f})")


def prerender_dem(cache):
    path = os.path.join(DATA_DIR, "mumbai_DEM.tif")
    if not os.path.exists(path):
        print("  DEM file not found, skipping")
        return

    with rasterio.open(path) as src:
        data = src.read(1)
        bounds = src.bounds

    valid = data[~np.isnan(data)]
    vmin = float(np.nanpercentile(valid, 2))
    vmax = float(np.nanpercentile(valid, 98))

    png_path = os.path.join(CACHE_DIR, "dem.png")
    render_raster_to_png(data, vmin, vmax, png_path, cmap_name="terrain")

    cache["dem"] = {
        "png": "cache/dem.png",
        "bounds": [[bounds.bottom, bounds.left], [bounds.top, bounds.right]],
        "vmin": round(vmin, 3),
        "vmax": round(vmax, 3),
    }
    print(f"  DEM: rendered -> {png_path} (vmin={vmin:.1f}, vmax={vmax:.1f})")


def compute_legend_gradient(cmap_name="RdYlBu_r", n=9):
    """Same colormap/sampling the old runtime legend used -- computed once here
    instead of importing matplotlib on every page load."""
    cmap = plt.colormaps[cmap_name]
    return [mcolors.to_hex(cmap(v)) for v in np.linspace(0, 1, n)]


def main():
    quarters = get_available_lst_quarters()
    if not quarters:
        print(f"No mumbai_LST_*.tif files found under {DATA_DIR}/ -- nothing to render.")
        return

    stats_path = os.path.join(CACHE_DIR, "raster_cache.json")
    if os.path.exists(stats_path):
        with open(stats_path) as f:
            cache = json.load(f)
        cache.setdefault("lst_quarters", {})
        print(f"Loaded existing cache with {len(cache['lst_quarters'])} quarter(s) already rendered.")
    else:
        cache = {"lst_quarters": {}}

    print(f"Found {len(quarters)} local quarter(s) to (re-)render: {', '.join(quarters)}")

    print("\nRendering LST quarters...")
    for q in quarters:
        prerender_lst(q, cache)

    print("\nRendering DEM...")
    prerender_dem(cache)

    cache["legend_gradient_lst"] = compute_legend_gradient()

    with open(stats_path, "w") as f:
        json.dump(cache, f, indent=2)

    print(f"\nSaved cache manifest -> {stats_path}  (total quarters cached: {len(cache['lst_quarters'])})")
    print(f"Commit {CACHE_DIR}/ to git; leave the raw mumbai_LST_*.tif / mumbai_DEM.tif out, per pipeline/README.md.")


if __name__ == "__main__":
    main()