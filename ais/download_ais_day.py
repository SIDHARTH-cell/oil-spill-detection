import requests
from pathlib import Path

URL = "https://noaaocm.blob.core.windows.net/ais/csv2/csv2020/ais-2020-07-27.csv.zst"

OUTPUT_DIR = Path("ais/data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "ais-2020-07-27.csv.zst"

print("Downloading:")
print(URL)
print()

response = requests.get(URL, stream=True, timeout=120)
response.raise_for_status()

total = int(response.headers.get("content-length", 0))
downloaded = 0

with open(OUTPUT_FILE, "wb") as f:
    for chunk in response.iter_content(chunk_size=1024 * 1024):
        if chunk:
            f.write(chunk)
            downloaded += len(chunk)

            if total:
                percent = downloaded / total * 100
                print(
                    f"\rDownloaded: {percent:.1f}%",
                    end=""
                )

print()
print()
print("Download complete:")
print(OUTPUT_FILE)