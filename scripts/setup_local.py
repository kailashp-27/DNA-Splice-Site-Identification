"""One-time setup of a private environment and the production frontend."""
from pathlib import Path
import argparse
import shutil
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]


def execute(arguments):
    print("Running: " + " ".join(map(str, arguments)), flush=True)
    subprocess.run(list(map(str, arguments)), cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser(description="Install pinned local runtime dependencies. Internet is needed once, unless caches are complete.")
    parser.add_argument("--offline", action="store_true", help="Use cached Python wheels and npm packages only.")
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 12):
        raise SystemExit("Use Python 3.12 for the tested release: py -3.12 scripts/setup_local.py")
    environment = ROOT / ".venv"
    python = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    try:
        if not python.is_file():
            print("Creating project .venv", flush=True)
            venv.EnvBuilder(with_pip=True).create(environment)
        wheels = ROOT / ".cache/wheels"
        wheels.mkdir(parents=True, exist_ok=True)
        if not args.offline:
            execute([python, "-m", "pip", "download", "-r", ROOT / "backend/requirements-lock.txt", "--dest", wheels])
        execute([python, "-m", "pip", "install", "--no-index", "--find-links", wheels, "-r", ROOT / "backend/requirements-lock.txt"])
        if (ROOT / "package.json").is_file():
            node = shutil.which("node")
            if not node:
                raise SystemExit("Install Node.js 20.19+ or 22.12+ to build this source checkout, then rerun setup. The release ZIP already includes the build.")
            # Call the JS entry point directly: some Windows npm.cmd installations are broken.
            npm_cli = Path(node).parent / "node_modules/npm/bin/npm-cli.js"
            npm = [node, npm_cli] if npm_cli.is_file() else [shutil.which("npm") or "npm"]
            execute([*npm, "ci", "--cache", ROOT / ".cache/npm", *( ["--offline"] if args.offline else [])])
            execute([node, ROOT / "node_modules/vite/bin/vite.js", "build"])
        execute([python, ROOT / "scripts/start_local.py", "--check"])
    except (OSError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"Setup did not complete: {error}\nCheck the message above and rerun. No DNA data is downloaded and no model is trained.")
    print("Setup complete. Run start-ecosplice.cmd and open the displayed localhost address.")


if __name__ == "__main__":
    main()
