"""Production local entry point. No Node, internet, reference download or training."""
from pathlib import Path
import argparse
import os
import socket
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def main():
    parser = argparse.ArgumentParser(description="Start the complete EcoSplice application on this laptop.")
    parser.add_argument("--port", type=int, default=os.getenv("ECOSPLICE_PORT", "8765"))
    parser.add_argument("--check", action="store_true", help="Check release files and dependencies without opening a server.")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        raise SystemExit("Choose a port between 1 and 65535.")
    try:
        import uvicorn
        from ecosplice.api import Settings
        from ecosplice.local_app import create_local_app
        from ecosplice.model import ModelBundle
    except ImportError as error:
        raise SystemExit(f"Missing Python dependency: {error}. Run setup-ecosplice.cmd first.")
    settings = Settings()
    try:
        app = create_local_app(settings)
        # Verify coefficients and their integrity before showing a ready URL.
        ModelBundle.load(settings.model_dir)
        for file in (settings.samples_path, ROOT / "data/processed/manifest.json",
                     settings.results_dir / "model-evaluation.json", settings.results_dir / "algorithm-verification.json"):
            if not file.is_file():
                raise FileNotFoundError(f"Required release file missing: {file}")
        settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    except (OSError, ValueError, KeyError) as error:
        raise SystemExit(f"EcoSplice cannot start: {error}\nRestore the bundled release files or check ECOSPLICE_MODEL_DIR / ECOSPLICE_DB_PATH.")
    if args.check:
        print("Release checks passed: built dashboard, saved model, evaluation, samples and Python dependencies.")
        return
    with socket.socket() as probe:
        try:
            probe.bind(("127.0.0.1", args.port))
        except OSError as error:
            raise SystemExit(f"Port {args.port} is occupied or reserved. Close your previous EcoSplice terminal, or use --port 8766.\n{error}")
    print(f"Open EcoSplice: http://127.0.0.1:{args.port}", flush=True)
    print(f"Local history: {settings.db_path}\nPress Ctrl+C to stop. Startup never downloads or trains.", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=args.port, workers=1)


if __name__ == "__main__":
    main()
