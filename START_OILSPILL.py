from pathlib import Path
import subprocess
import time
import os

ROOT = Path(r"D:\NewWork (2)\AI")
WEBROOT = ROOT / "Revisions" / "Revisions"
VENV = ROOT / "venv"
PYTHON = VENV / "Scripts" / "python.exe"
STREAMLIT = VENV / "Scripts" / "streamlit.exe"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

FASTAPI_TARGET = "backend.api:app"
STREAMLIT_APP = ROOT / "dashboard" / "app.py"
WEB_FILE = WEBROOT / "oilspill.html"

print("=" * 55)
print("       OIL SPILL DETECTION SYSTEM")
print("=" * 55)
print()

if not ROOT.exists():
    print("ERROR: Project folder not found:")
    print(ROOT)
    input("Press Enter to close...")
    raise SystemExit(1)

if not PYTHON.exists():
    print("ERROR: Python virtual environment not found:")
    print(PYTHON)
    input("Press Enter to close...")
    raise SystemExit(1)

if not STREAMLIT.exists():
    print("ERROR: Streamlit executable not found:")
    print(STREAMLIT)
    input("Press Enter to close...")
    raise SystemExit(1)

if not STREAMLIT_APP.exists():
    print("ERROR: Streamlit app not found:")
    print(STREAMLIT_APP)
    input("Press Enter to close...")
    raise SystemExit(1)

if not WEB_FILE.exists():
    print("ERROR: oilspill.html not found:")
    print(WEB_FILE)
    input("Press Enter to close...")
    raise SystemExit(1)

print("[1/3] Starting FastAPI...")
subprocess.Popen(
    [
        str(PYTHON), "-m", "uvicorn",
        FASTAPI_TARGET,
        "--host", "127.0.0.1",
        "--port", "8000",
    ],
    cwd=str(ROOT),
    creationflags=subprocess.CREATE_NEW_CONSOLE,
)

print("[2/3] Starting Streamlit...")
env = os.environ.copy()
env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

subprocess.Popen(
    [
        str(STREAMLIT), "run", str(STREAMLIT_APP),
        "--server.headless", "true",
        "--server.address", "127.0.0.1",
        "--server.port", "8501",
    ],
    cwd=str(ROOT),
    env=env,
    creationflags=subprocess.CREATE_NEW_CONSOLE,
)

print("[3/3] Starting website server...")
subprocess.Popen(
    [
        str(PYTHON), "-m", "http.server",
        "5500",
        "--bind", "127.0.0.1",
    ],
    cwd=str(WEBROOT),
    creationflags=subprocess.CREATE_NEW_CONSOLE,
)

print()
print("Waiting for the local services...")
time.sleep(5)

url = "http://127.0.0.1:5500/oilspill.html"

print("Opening:")
print(url)

if CHROME.exists():
    subprocess.Popen([str(CHROME), url])
else:
    print("Chrome executable not found at:")
    print(CHROME)
    print("Opening with the Windows default browser instead.")
    os.startfile(url)

print()
print("=" * 55)
print("SYSTEM STARTED")
print("Website : http://127.0.0.1:5500/oilspill.html")
print("FastAPI : http://127.0.0.1:8000")
print("Streamlit: http://127.0.0.1:8501")
print("=" * 55)
print()
input("Press Enter to close this launcher window...")
