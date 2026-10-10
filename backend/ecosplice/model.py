"""Portable linear DNA models. Inference requires NumPy, not sklearn or pickle."""
from pathlib import Path
import hashlib
import json
import numpy as np

from .sequence import CONTEXT_WIDTH, FLANK

CLASSES = ("non_site", "donor", "acceptor")
CLASS_INDEX = {label: index for index, label in enumerate(CLASSES)}
ENCODING = np.full(256, 255, dtype=np.uint8)
for index, letter in enumerate(b"ACGT"):
    ENCODING[letter] = index


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def encode_contexts(contexts):
    if any(len(context) != CONTEXT_WIDTH for context in contexts):
        raise ValueError(f"Every model context must contain {CONTEXT_WIDTH} bases.")
    try:
        letters = np.frombuffer("".join(contexts).encode("ascii"), dtype=np.uint8)
    except UnicodeEncodeError as error:
        raise ValueError("Model contexts must contain A/C/G/T only.") from error
    codes = ENCODING[letters].reshape(len(contexts), CONTEXT_WIDTH)
    if np.any(codes == 255):
        raise ValueError("Model contexts must contain A/C/G/T only.")
    return codes


def feature_indices(codes, flank, pairs):
    if not 0 <= flank <= FLANK:
        raise ValueError("Unsupported feature flank.")
    bases = codes[:, FLANK - flank:FLANK + flank + 2].astype(np.int32)
    width = bases.shape[1]
    single = np.arange(width, dtype=np.int32)[None, :] * 4 + bases
    if not pairs:
        return single, width * 4
    adjacent = width * 4 + np.arange(width - 1, dtype=np.int32)[None, :] * 16 + bases[:, :-1] * 4 + bases[:, 1:]
    return np.concatenate((single, adjacent), axis=1), width * 4 + (width - 1) * 16


class LinearScorer:
    def __init__(self, weights, intercept, flank, pairs, identity):
        self.weights = np.asarray(weights, dtype=np.float64)
        self.intercept = np.asarray(intercept, dtype=np.float64)
        self.flank, self.pairs, self.identity = int(flank), bool(pairs), identity
        _, dimension = feature_indices(np.zeros((1, CONTEXT_WIDTH), dtype=np.uint8), self.flank, self.pairs)
        if self.weights.shape != (3, dimension) or self.intercept.shape != (3,):
            raise ValueError("Model coefficient dimensions do not match preprocessing.")
        if not np.isfinite(self.weights).all() or not np.isfinite(self.intercept).all():
            raise ValueError("Model coefficients must be finite.")

    def score_codes(self, codes):
        indices, _ = feature_indices(codes, self.flank, self.pairs)
        logits = self.weights[:, indices].sum(axis=2).T + self.intercept
        logits -= logits.max(axis=1, keepdims=True)
        exp = np.exp(logits)
        return exp / exp.sum(axis=1, keepdims=True)

    def score(self, contexts):
        if not contexts:
            return np.empty((0, 3), dtype=np.float64)
        return self.score_codes(encode_contexts(contexts))


class ModelBundle:
    def __init__(self, metadata, preliminary, detailed):
        self.metadata, self.preliminary, self.detailed = metadata, preliminary, detailed
        self.thresholds = metadata["thresholds"]
        self.routing = metadata["routing"]
        self.identity = metadata["model_id"]
        for kind in ("donor", "acceptor"):
            for thresholds in self.thresholds.values():
                if not 0 <= thresholds[kind] <= 1:
                    raise ValueError("Invalid prediction threshold.")
            low, high = self.routing[kind]["low"], self.routing[kind]["high"]
            if not 0 <= low <= self.thresholds["preliminary"][kind] <= high <= 1:
                raise ValueError("Invalid adaptive routing boundaries.")

    @classmethod
    def load(cls, directory):
        directory = Path(directory)
        try:
            metadata = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
            if metadata["schema_version"] != 1 or metadata["classes"] != list(CLASSES):
                raise ValueError("Unsupported saved model schema/classes.")
            if metadata["context_width"] != CONTEXT_WIDTH:
                raise ValueError("Saved model has an incompatible context width.")
            scorers = {}
            for name in ("preliminary", "detailed"):
                path = directory / f"{name}.npz"
                spec = metadata["scorers"][name]
                if sha256(path) != spec["sha256"]:
                    raise ValueError(f"Saved {name} model failed its checksum.")
                with np.load(path, allow_pickle=False) as arrays:
                    scorers[name] = LinearScorer(arrays["weights"], arrays["intercept"], spec["flank"], spec["pairs"], spec["id"])
            return cls(metadata, scorers["preliminary"], scorers["detailed"])
        except (OSError, KeyError, json.JSONDecodeError) as error:
            raise ValueError(f"Saved model is unavailable or incomplete: {error}") from error
