import requests
import pandas as pd
from pathlib import Path
from io import StringIO
from urllib.parse import quote


# ============================================================
# DEMO SPILL
# ============================================================

SPILL_LAT = 19.6880496
SPILL_LON = -92.0787825

ACQUISITION_TIME = "2020-07-27T00:15:46Z"


# ============================================================
# SEARCH AREA
# ============================================================

LAT_MIN = 19.0
LAT_MAX = 20.5

LON_MIN = -93.0
LON_MAX = -91.0

TIME_START = "2020-07-27T00:00:00Z"
TIME_END = "2020-07-28T00:00:00Z"


# ============================================================
# NOAA ERDDAP
# ============================================================

BASE_URL = (
    "https://data.pmel.noaa.gov/"
    "pmel/erddap/tabledap/AIS2020_AIS.csv"
)


def fetch_ais():

    print("=" * 60)
    print("AUTOMATIC AIS SEARCH")
    print("=" * 60)

    print(f"\nSpill latitude : {SPILL_LAT}")
    print(f"Spill longitude: {SPILL_LON}")

    print(f"\nSAR acquisition:")
    print(ACQUISITION_TIME)

    print("\nAIS time window:")
    print(TIME_START)
    print(TIME_END)

    # --------------------------------------------------------
    # Variables
    # --------------------------------------------------------

    variables = (
        "MMSI,time,Lat,Lon,SOG,COG,"
        "Heading,VesselName,IMO,CallSign,VesselType"
    )

    # --------------------------------------------------------
    # Build ERDDAP query correctly
    # --------------------------------------------------------

    query = variables

    constraints = [
        ("time>=", TIME_START),
        ("time<=", TIME_END),
        ("Lat>=", str(LAT_MIN)),
        ("Lat<=", str(LAT_MAX)),
        ("Lon>=", str(LON_MIN)),
        ("Lon<=", str(LON_MAX)),
    ]

    for operator, value in constraints:
        query += "&" + operator + quote(
            value,
            safe=""
        )

    url = BASE_URL + "?" + query

    print("\nRequesting NOAA AIS data...")
    print("Please wait...")

    try:

        response = requests.get(
            url,
            timeout=180
        )

        print("\nHTTP status:", response.status_code)

        if response.status_code != 200:

            print("\nNOAA returned an error:")
            print(response.text[:2000])

            return

        # ----------------------------------------------------
        # Convert response to DataFrame
        # ----------------------------------------------------

        df = pd.read_csv(
            StringIO(response.text)
        )

        print("\nAIS records received:", len(df))

        if df.empty:

            print("\nNo AIS records found.")
            return

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)

        output_file = output_dir / "ais_vessels.csv"

        df.to_csv(
            output_file,
            index=False
        )

        print("\nSaved:")
        print(output_file)

        # ----------------------------------------------------
        # Display
        # ----------------------------------------------------

        print("\nColumns:")
        print(df.columns.tolist())

        print("\nFirst 10 records:")

        print(
            df.head(10).to_string(index=False)
        )

    except requests.exceptions.Timeout:

        print("\nRequest timed out.")

    except requests.exceptions.RequestException as e:

        print("\nNetwork error:")
        print(e)

    except Exception as e:

        print("\nUnexpected error:")
        print(e)


if __name__ == "__main__":
    fetch_ais()