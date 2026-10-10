"""Run saved models on one DNA/FASTA file locally; never downloads or trains."""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from ecosplice.algorithms import METHODS, analyze
from ecosplice.model import ModelBundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=ROOT / "models/ecosplice-v1")
    parser.add_argument("--method", choices=METHODS, default="filtered")
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    bundle = ModelBundle.load(args.model)
    result = analyze(args.input.read_text(encoding="utf-8-sig"), bundle, args.method, args.batch_size)
    text = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8", newline="\n")
        print(json.dumps({"output": str(args.output), "model_id": bundle.identity, "work": result["work"],
                          "predicted_sites": sum(site["predicted"] for site in result["candidates"]),
                          "runtime_ms": result["timing_ms"]["total_ms"]}, indent=2))
    else:
        print(text, end="")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        raise SystemExit(f"Analysis failed: {error}") from error
