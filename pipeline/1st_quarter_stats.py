import rasterio
import numpy as np
import glob
import re

for path in sorted(glob.glob("data/mumbai_LST_*.tif")):
    quarter = re.search(r"(\d{4}_Q\d)", path).group(1)
    with rasterio.open(path) as src:
        data = src.read(1)
    valid = data[~np.isnan(data)]
    print(f"{quarter}: mean={np.nanmean(valid):.2f}, "
          f"p2={np.nanpercentile(valid,2):.2f}, "
          f"p98={np.nanpercentile(valid,98):.2f}")