"""Make a small reproducible local release without user DNA or development caches."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def release_files():
    files = []
    for directory in ("backend/ecosplice", "models/ecosplice-v1", "results", "dist", "data/demo", "docs/submission", "scripts/data", "scripts/models"):
        files.extend(path for path in (ROOT / directory).rglob("*")
                     if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc")
    for name in ("data/processed/manifest.json", "data/processed/demo_samples.json", "data/processed/split_membership.json", "backend/requirements-lock.txt",
                 "scripts/analyze_sequence.py",
                 "scripts/start_local.py", "scripts/setup_local.py", "start-ecosplice.cmd", "setup-ecosplice.cmd",
                 "config.example.ps1", "docs/THIRD_PARTY_NOTICES.md",
                 "docs/LOCAL_RELEASE.md", "docs/DATASET_AND_COORDINATES.md", "docs/MODELS_AND_ALGORITHMS.md"):
        files.append(ROOT / name)
    files.append(ROOT / "docs/MANUAL_TESTING.md")
    return sorted(set(files))


def main():
    if not (ROOT / "dist/index.html").is_file():
        raise SystemExit("Build the frontend before packaging: npm run build")
    paths = release_files()
    for path in paths:
        if not path.is_file():
            raise SystemExit(f"Release file missing: {path}")
    manifest = {"release": "EcoSplice 1.0.0", "model_id": "ecosplice-v1-64223ad070d6",
                "contents": {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
                "excludes": ["user history and DNA", "raw genomic sources", "training windows", "environments", "Git", "QA intermediates"],
                "setup": "setup-ecosplice.cmd", "launch": "start-ecosplice.cmd"}
    destination = ROOT / "releases"
    destination.mkdir(exist_ok=True)
    archive = destination / "EcoSplice-1.0.0.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in paths:
            info = zipfile.ZipInfo("EcoSplice/" + path.relative_to(ROOT).as_posix(), (2026, 10, 9, 0, 0, 0))
            bundle.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
        bundle.writestr("EcoSplice/RELEASE_MANIFEST.json", json.dumps(manifest, indent=2))
    (destination / "release-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Created {archive} ({archive.stat().st_size:,} bytes), {len(paths)} files; no saved user runs.")


if __name__ == "__main__":
    main()
