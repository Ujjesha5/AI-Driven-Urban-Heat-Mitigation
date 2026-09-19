import rasterio

with rasterio.open("data/mumbai_S2_2024_Q2.tif") as src:
    print("Bands:", src.count)
    print("Dtype:", src.dtypes[0])
    print("CRS:", src.crs)
    print("Width x Height:", src.width, src.height)
    for i in range(1, min(src.count, 13) + 1):
        band = src.read(i)
        print(f"Band {i}: min={band.min()}, max={band.max()}")