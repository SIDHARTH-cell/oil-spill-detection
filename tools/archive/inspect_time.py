import rasterio

tiff_path = r"D:\NewWork (2)\AI\oilspill-detection-dataset\RASTER\IMG-TIFF\8-BIT\IMG_07_TILE_001.tiff"

with rasterio.open(tiff_path) as src:

    print("CRS:", src.crs)
    print("Size:", src.width, "x", src.height)

    print("\n--- Dataset metadata ---")
    for key, value in src.meta.items():
        print(key, "=", value)

    print("\n--- TIFF tags ---")
    for key, value in src.tags().items():
        print(key, "=", value)

    print("\n--- Band tags ---")
    for i in range(1, src.count + 1):
        print(f"\nBand {i}:")
        for key, value in src.tags(i).items():
            print(key, "=", value)

    print("\n--- File information ---")
    print(src.files)