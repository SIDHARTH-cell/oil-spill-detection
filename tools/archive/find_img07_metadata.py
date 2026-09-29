import os
import re

root = r"D:\NewWork (2)\AI\oilspill-detection-dataset"
target = "IMG_07_TILE_001"

date_pattern = r"\b20\d{2}-\d{2}-\d{2}\b"
time_pattern = r"\b\d{2}\s+\d{2}\s+\d{2}\b"

for folder, _, files in os.walk(root):

    for file in files:

        if file.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff")):
            continue

        path = os.path.join(folder, file)

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

            lower = text.lower()
            target_lower = target.lower()

            start = 0

            while True:

                pos = lower.find(target_lower, start)

                if pos == -1:
                    break

                # Take only nearby metadata
                section = text[max(0, pos - 3000):pos + 3000]

                dates = re.findall(date_pattern, section)
                times = re.findall(time_pattern, section)

                # Look for Sentinel information
                sentinel = re.findall(
                    r".{0,50}SENTINEL-1.{0,100}",
                    section,
                    re.IGNORECASE
                )

                print("\n" + "=" * 70)
                print("FILE:", path)
                print("=" * 70)

                print("DATES FOUND:")
                for d in sorted(set(dates)):
                    print(" ", d)

                print("\nTIMES FOUND:")
                for t in sorted(set(times)):
                    print(" ", t)

                print("\nSENTINEL INFORMATION:")
                for s in sentinel:
                    print(" ", s.strip())

                start = pos + len(target)

        except Exception:
            pass