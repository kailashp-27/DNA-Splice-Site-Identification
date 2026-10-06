"""Download frozen public inputs only; normal application launch never calls this."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import urllib.request
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RELEASE = "https://www.gencodegenes.org/human/release_49.html"
GENOME = "https://hgdownload.soe.ucsc.edu/goldenPath/hg38/chromosomes/chr22.fa.gz"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url, destination):
    if destination.exists():
        print(f"Using cached {destination.name}", flush=True)
        return
    print(f"Downloading {url}", flush=True)
    temporary = destination.with_suffix(destination.suffix + ".partial")
    # Windows' bundled curl handles large FTP-mirror HTTPS transfers more reliably.
    curl = shutil.which("curl.exe") or shutil.which("curl")
    if curl:
        if urlparse(url).hostname == "ftp.ebi.ac.uk":
            # Some networks stall long mirror transfers. Bounded HTTPS ranges are resumable at source level.
            with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=30) as response:
                length = int(response.headers["Content-Length"])
            part = temporary.with_suffix(".chunk")
            with temporary.open("wb") as output:
                for offset in range(0, length, 4 * 1024 * 1024):
                    end = min(length - 1, offset + 4 * 1024 * 1024 - 1)
                    result = subprocess.run([curl, "--fail", "--location", "--silent", "--show-error",
                                             "--retry", "2", "--max-time", "120", "--range", f"{offset}-{end}",
                                             "--max-filesize", str(end - offset + 1), "--write-out", "%{http_code}",
                                             "--output", str(part), "--url", url], check=True, capture_output=True, text=True)
                    if result.stdout != "206" or part.stat().st_size != end - offset + 1:
                        raise OSError("The reference server returned an incomplete or unsupported range response.")
                    with part.open("rb") as chunk:
                        shutil.copyfileobj(chunk, output)
                    print(f"  {(end + 1) / 1024 / 1024:.0f}/{length / 1024 / 1024:.0f} MiB received", flush=True)
            part.unlink()
        else:
            subprocess.run([curl, "--fail", "--location", "--silent", "--show-error", "--retry", "2",
                            "--speed-limit", "1024", "--speed-time", "30", "--max-time", "900",
                            "--output", str(temporary), "--url", url], check=True)
        temporary.replace(destination)
        return
    request = urllib.request.Request(url, headers={"User-Agent": "EcoSplice educational dataset preparation"})
    with urllib.request.urlopen(request, timeout=120) as response, temporary.open("wb") as output:
        expected_bytes = response.headers.get("Content-Length")
        received = 0
        next_progress = 8 * 1024 * 1024
        for chunk in iter(lambda: response.read(1024 * 1024), b""):
            output.write(chunk)
            received += len(chunk)
            if received >= next_progress:
                print(f"  {received / 1024 / 1024:.0f} MiB received", flush=True)
                next_progress += 8 * 1024 * 1024
        if expected_bytes is not None and received != int(expected_bytes):
            raise OSError(f"Incomplete download: expected {expected_bytes} bytes, received {received}.")
    temporary.replace(destination)


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    # Read the official release page instead of guessing a release filename.
    with urllib.request.urlopen(RELEASE, timeout=60) as response:
        page = response.read().decode("utf-8")
    links = re.findall(r'href=[\"\']([^\"\']+\.gtf\.gz)[\"\']', page)
    annotation = next(url for url in links if url.endswith("/gencode.v49.annotation.gtf.gz"))
    annotation = annotation.replace("ftp://", "https://")
    if urlparse(annotation).hostname != "ftp.ebi.ac.uk" or urlparse(annotation).scheme != "https":
        raise ValueError("The official annotation link does not point to the expected EMBL-EBI HTTPS host.")
    inputs = [(annotation, "gencode.v49.annotation.gtf.gz"), (GENOME, "chr22.fa.gz")]
    records = []
    recorded_path = RAW / "sources.json"
    previous = json.loads(recorded_path.read_text()) if recorded_path.exists() else {"files": []}
    previous_hashes = {record["file"]: record["sha256"] for record in previous["files"]}
    for url, name in inputs:
        path = RAW / name
        download(url, path)
        checksum = sha256(path)
        if name in previous_hashes and checksum != previous_hashes[name]:
            raise ValueError(f"Cached {name} differs from its recorded checksum; investigate before regenerating sources.")
        records.append({"url": url, "file": name, "bytes": path.stat().st_size, "sha256": checksum})
    (RAW / "sources.json").write_text(json.dumps({"release_page": RELEASE, "files": records}, indent=2) + "\n")
    print("Reference files and checksums saved in data/raw.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, StopIteration, subprocess.CalledProcessError) as error:
        raise SystemExit(f"Reference download failed: {error}") from error
