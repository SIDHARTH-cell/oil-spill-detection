from pathlib import Path
import json

import pandas as pd

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

OUTPUTS = ROOT / "outputs"
AIS = ROOT / "ais"


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Oil Spill Detection API",
    version="1.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# HELPER
# ============================================================

def read_csv_records(path):

    if not path.exists():
        return []

    df = pd.read_csv(path)

    # Convert NaN values into JSON-compatible null values
    return json.loads(
        df.to_json(orient="records")
    )


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "message": "Oil Spill Detection Backend is running"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health():

    return {
        "status": "online",
        "system": "Oil Spill Detection & Source Analysis",
        "backend": "FastAPI"
    }


# ============================================================
# DASHBOARD DATA
# ============================================================

@app.get("/api/dashboard")
def dashboard_data():

    # IMPORTANT:
    # result is created BEFORE anything else happens.

    result = {
        "status": "success",

        "spill": {
            "geojson": None
        },

        "source": {
            "uncertainty": [],
            "backward_drift": []
        },

        "vessels": [],

        "ais": []
    }


    # ========================================================
    # OIL SPILL GEOJSON
    # ========================================================

    geojson_path = (
        OUTPUTS /
        "oil_spill_regions.geojson"
    )

    if geojson_path.exists():

        with open(
            geojson_path,
            "r",
            encoding="utf-8"
        ) as file:

            result["spill"]["geojson"] = json.load(file)


    # ========================================================
    # BACKWARD DRIFT
    # ========================================================

    drift_path = (
        OUTPUTS /
        "backward_drift.csv"
    )

    result["source"]["backward_drift"] = (
        read_csv_records(drift_path)
    )


    # ========================================================
    # SOURCE UNCERTAINTY
    # ========================================================

    uncertainty_path = (
        OUTPUTS /
        "source_uncertainty.csv"
    )

    result["source"]["uncertainty"] = (
        read_csv_records(uncertainty_path)
    )


    # ========================================================
    # CANDIDATE VESSEL RANKING
    # ========================================================

    ranking_path = (
        OUTPUTS /
        "final_candidate_ranking_v2.csv"
    )

    result["vessels"] = (
        read_csv_records(ranking_path)
    )


    # ========================================================
    # AIS DATA
    # ========================================================

    ais_path = (
        AIS /
        "synthetic_ais.csv"
    )

    result["ais"] = (
        read_csv_records(ais_path)
    )


    # ========================================================
    # RETURN EVERYTHING
    # ========================================================

    return result