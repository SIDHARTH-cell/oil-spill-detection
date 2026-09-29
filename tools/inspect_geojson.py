import json

path = r"D:\NewWork (2)\AI\oilspill-detection-dataset\RASTER\LABELS-VECTOR\GEOJSON\IMG_07_TILE_001.geojson"

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

print("=== GEOJSON TYPE ===")
print(data.get("type"))

print("\n=== FEATURES ===")

for i, feature in enumerate(data.get("features", []), 1):

    print(f"\nFeature {i}")

    print("Geometry:")
    print(feature.get("geometry", {}).get("type"))

    print("\nProperties:")
    properties = feature.get("properties", {})

    if properties:
        for key, value in properties.items():
            print(f"{key} = {value}")
    else:
        print("No properties")

print("\n=== TOP LEVEL PROPERTIES ===")

for key, value in data.items():
    if key not in ["features", "geometry"]:
        print(f"{key} = {value}")