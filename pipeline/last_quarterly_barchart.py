import rasterio
import numpy as np
import glob
import re
import matplotlib.pyplot as plt

quarter_files = sorted(glob.glob("data/mumbai_LST_*.tif"))

quarters = []
means = []

for path in quarter_files:
    match = re.search(r"(\d{4}_Q\d)", path)
    if not match:
        continue
    quarter = match.group(1)
    with rasterio.open(path) as src:
        data = src.read(1)
    valid = data[~np.isnan(data)]
    quarters.append(quarter.replace("_", " "))
    means.append(np.nanmean(valid))

# Color pre-monsoon (Q2) bars differently to visually highlight the seasonal peak
colors = ["#d62728" if "Q2" in q else "#4a7fb5" for q in quarters]

plt.figure(figsize=(8, 4.5))
bars = plt.bar(quarters, means, color=colors)

for bar, mean in zip(bars, means):
    plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
              f"{mean:.1f}", ha="center", fontsize=9)

plt.ylabel("Mean LST (°C)")
plt.title("Mean Land Surface Temperature by Quarter — Mumbai Metropolitan Region")
plt.ylim(0, max(means) + 5)
plt.xticks(rotation=30, ha="right")
plt.tight_layout()

plt.savefig("data/lst_quarterly_barchart.png", dpi=200)
print("Saved to data/lst_quarterly_barchart.png")