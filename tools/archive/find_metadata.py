import os

root = r"D:\NewWork (2)\AI\oilspill-detection-dataset"

keywords = [
    "acquisition",
    "timestamp",
    "sentinel",
    "satellite",
    "date",
    "time"
]

for folder, _, files in os.walk(root):

    for file in files:

        if file.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff")):
            continue

        path = os.path.join(folder, file)

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            matches = []

            for line_number, line in enumerate(lines, 1):

                lower = line.lower()

                if any(keyword in lower for keyword in keywords):
                    matches.append(
                        f"  Line {line_number}: {line.strip()}"
                    )

            if matches:
                print("\n" + "=" * 80)
                print("FILE:", path)
                print("=" * 80)

                for match in matches[:30]:
                    print(match)

        except Exception:
            pass