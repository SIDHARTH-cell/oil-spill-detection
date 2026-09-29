import rasterio

tiff_path = r"D:\NewWork (2)\AI\oilspill-detection-dataset\RASTER\IMG-TIFF\8-BIT\IMG_07_TILE_001.tiff"

with rasterio.open(tiff_path) as src:

    print("Width:", src.width)
    print("Height:", src.height)
    print("Number of bands:", src.count)

    print("CRS:", src.crs)

    print("Transform:")
    print(src.transform)

    print("Bounds:")
    print(src.bounds)

    print("Resolution:")
    print(src.res)