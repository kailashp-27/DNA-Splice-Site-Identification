"""Run the local service, with useful dependency and occupied-port messages."""
from pathlib import Path
import argparse
import os
import socket
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def main():
    parser = argparse.ArgumentParser(description="Start EcoSplice on this laptop only.")
    parser.add_argument("--port", type=int, default=os.getenv("ECOSPLICE_PORT", "8765"))
    port = parser.parse_args().port
    if not 1 <= port <= 65535:
        raise SystemExit("Choose a port between 1 and 65535.")
    try:
        import uvicorn
        from ecosplice.api import create_app
    except ImportError as error:
        raise SystemExit(f"Missing Python dependency: {error}.\nRun: python -m pip install -r backend/requirements.txt")
    with socket.socket() as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError as error:
            raise SystemExit(f"Port {port} is unavailable (occupied or reserved by Windows). Choose another with --port or ECOSPLICE_PORT.\n{error}")
    print(f"EcoSplice backend: http://127.0.0.1:{port}/api/health", flush=True)
    print("Saved models load once; no training or download. History: data/local/runs.sqlite3 (or ECOSPLICE_DB_PATH).", flush=True)
    uvicorn.run(create_app(), host="127.0.0.1", port=port, workers=1)


if __name__ == "__main__":
    main()
