"""Local HTTP interface. Startup loads saved models; requests never train/download."""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from dataclasses import dataclass, field
import json
import logging
import os
from pathlib import Path
import platform
import sqlite3
import threading
from typing import Annotated, Literal
from uuid import uuid4

import numpy as np
from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from starlette.exceptions import HTTPException

from .algorithms import analyze
from .comparison import compare
from .evaluation import binary_metrics
from .model import ModelBundle, sha256
from .reports import csv_report, html_report, json_report, select_report
from .sequence import MAX_SEQUENCE_LENGTH, parse_sequence
from .storage import RunStore

ROOT = Path(__file__).resolve().parents[2]
MAX_BODY_BYTES = 1_000_000
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120, pattern=r"^[^\x00-\x1f\x7f]+$")]


@dataclass
class Settings:
    model_dir: Path = field(default_factory=lambda: Path(os.getenv("ECOSPLICE_MODEL_DIR", ROOT / "models/ecosplice-v1")))
    db_path: Path = field(default_factory=lambda: Path(os.getenv("ECOSPLICE_DB_PATH", ROOT / "data/local/runs.sqlite3")))
    samples_path: Path = ROOT / "data/processed/demo_samples.json"
    results_dir: Path = ROOT / "results"
    origins: tuple = ("http://127.0.0.1:5173", "http://localhost:5173", "http://127.0.0.1:5188", "http://localhost:5188")


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sequence: str | None = Field(default=None, max_length=300_000)
    sample_id: str | None = Field(default=None, max_length=40)
    method: Literal["exhaustive", "filtered", "adaptive"] = "filtered"
    batch_size: int = Field(default=512, ge=1, le=8192, strict=True)
    name: Name | None = None
    assumed_power_watts: float = Field(default=15., ge=0, le=500, allow_inf_nan=False)
    client_request_id: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def one_input(self):
        if (self.sequence is None) == (self.sample_id is None):
            raise ValueError("Provide either sequence text or one built-in sample_id.")
        return self


class RenameRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Name


class ComparisonRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    repeats: int = Field(default=5, ge=3, le=7, strict=True)


class ServiceError(Exception):
    def __init__(self, status, code, message):
        self.status, self.code, self.message = status, code, message


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class BodyLimit:
    """Limit streamed bodies too, before JSON parsing or allocating model inputs."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        chunks, size = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > MAX_BODY_BYTES:
                response = JSONResponse({"error": {"code": "request_too_large", "message": "Request exceeds the 1 MB limit."}}, status_code=413)
                return await response(scope, receive, send)
            chunks.append(message)
            if not message.get("more_body", False):
                break
        index = 0
        async def replay():
            nonlocal index
            if index < len(chunks):
                message = chunks[index]
                index += 1
                return message
            return await receive()
        await self.app(scope, replay, send)


def create_app(settings=None):
    settings = settings or Settings()
    store = RunStore(settings.db_path)
    compute_lock = threading.Lock()

    @asynccontextmanager
    async def lifespan(app):
        app.state.bundle = None
        app.state.model_error = None
        app.state.storage_error = None
        app.state.samples = {}
        app.state.samples_error = None
        try:
            store.initialize()
        except (OSError, sqlite3.Error, ValueError) as error:
            logging.exception("History initialization failed")
            app.state.storage_error = str(error)
        try:
            bundle = ModelBundle.load(settings.model_dir)
            # Warm both inference paths before reporting ready. Loading/warm-up
            # is excluded from each run's measured computation.
            for scorer in (bundle.preliminary, bundle.detailed):
                scorer.score(["A" * 50 + "GT" + "A" * 50, "C" * 50 + "AG" + "C" * 50])
            app.state.model_manifest_sha256 = sha256(settings.model_dir / "manifest.json")
            app.state.algorithm_sha256 = sha256(Path(__file__).with_name("algorithms.py"))
            app.state.bundle = bundle
        except Exception as error:
            logging.exception("Saved model initialization failed")
            app.state.model_error = str(error)
        try:
            samples = json.loads(settings.samples_path.read_text(encoding="utf-8"))
            manifest = json.loads((ROOT / "data/processed/manifest.json").read_text(encoding="utf-8"))
            expected = manifest["files"]["demo_samples.json"]
            if sha256(settings.samples_path) != expected:
                raise ValueError("Demonstration sample checksum does not match the frozen dataset.")
            app.state.samples = {sample["id"]: sample for sample in samples}
        except (OSError, ValueError, KeyError, TypeError) as error:
            app.state.samples_error = str(error)
        yield

    app = FastAPI(title="EcoSplice local analysis", version="1.0.0", lifespan=lifespan,
                  docs_url=None, redoc_url=None)
    app.add_middleware(BodyLimit)
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.origins),
                       allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["Content-Type"])

    @app.exception_handler(ServiceError)
    async def service_error(request, error):
        return JSONResponse({"error": {"code": error.code, "message": error.message}}, status_code=error.status)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, error):
        # Do not echo DNA inputs or internal exception objects in an error.
        return JSONResponse({"error": {"code": "invalid_request", "message": "Check the request fields.",
                                       "details": [{"field": ".".join(map(str, item["loc"])), "message": item["msg"]}
                                                   for item in error.errors()]}}, status_code=422)

    @app.exception_handler(HTTPException)
    async def http_error(request, error):
        return JSONResponse({"error": {"code": "http_error", "message": str(error.detail)}}, status_code=error.status_code)

    @app.exception_handler(Exception)
    async def unexpected(request, error):
        logging.exception("Request failed", exc_info=error)
        return JSONResponse({"error": {"code": "internal_error", "message": "The local service could not complete the request. Check its terminal log."}}, status_code=500)

    def require_model():
        if app.state.bundle is None:
            raise ServiceError(503, "model_unavailable", "Saved model is missing or invalid. Check the backend terminal and model directory, then restart.")
        return app.state.bundle

    def storage_call(operation, *args):
        if app.state.storage_error:
            raise ServiceError(503, "history_unavailable", "Local history could not be opened. Check the database path and restart.")
        try:
            return operation(*args)
        except KeyError:
            raise ServiceError(404, "run_not_found", "This saved run does not exist.")
        except (OSError, sqlite3.Error):
            logging.exception("History operation failed")
            raise ServiceError(503, "history_unavailable", "Local history could not be read or written. Check disk space and file access.")

    @app.get("/api/health")
    def health():
        ready = app.state.bundle is not None and app.state.storage_error is None
        return {"status": "ready" if ready else "degraded", "model_ready": app.state.bundle is not None,
                "history_ready": app.state.storage_error is None, "samples_ready": bool(app.state.samples),
                "model_id": app.state.bundle.identity if app.state.bundle else None,
                "max_sequence_length": MAX_SEQUENCE_LENGTH, "max_request_bytes": MAX_BODY_BYTES}

    @app.get("/api/model")
    def model():
        return require_model().metadata

    @app.get("/api/samples")
    def samples():
        if app.state.samples_error:
            raise ServiceError(503, "samples_unavailable", "Bundled demonstration samples are missing or invalid.")
        return {"samples": [{**{key: value for key, value in sample.items() if key not in ("sequence", "annotations")},
                             "length": len(sample["sequence"]), "annotated_boundaries": len(sample["annotations"])}
                            for sample in app.state.samples.values()]}

    def get_sample(sample_id):
        if app.state.samples_error:
            raise ServiceError(503, "samples_unavailable", "Bundled demonstration samples are missing or invalid.")
        if sample_id not in app.state.samples:
            raise ServiceError(404, "sample_not_found", "Choose a bundled sample from /api/samples.")
        return app.state.samples[sample_id]

    @app.get("/api/samples/{sample_id}")
    def sample(sample_id: str):
        return get_sample(sample_id)

    @app.get("/api/samples/{sample_id}/fasta")
    def sample_fasta(sample_id: str):
        sample = get_sample(sample_id)
        sequence = sample["sequence"]
        # DNA comes from the integrity-checked demonstration manifest. This
        # download carries sequence only; uploading it does not assign labels.
        text = f">{sample_id} EcoSplice demonstration; supplied orientation\n"
        text += "\n".join(sequence[index:index + 80] for index in range(0, len(sequence), 80)) + "\n"
        return Response(text, media_type="text/plain", headers={
            "Content-Disposition": f'attachment; filename="ecosplice-{sample_id}.fasta"',
            "X-Content-Type-Options": "nosniff",
        })

    @app.get("/api/evaluation")
    def evaluation():
        bundle = require_model()
        path = settings.results_dir / "model-evaluation.json"
        try:
            artifact = json.loads(path.read_text(encoding="utf-8"))
            if artifact["model_id"] != bundle.identity or artifact["dataset_fingerprint"] != bundle.metadata["dataset_fingerprint"]:
                raise ValueError("Evaluation identity mismatch")
        except (OSError, ValueError, KeyError):
            raise ServiceError(503, "evaluation_unavailable", "Matching held-out evaluation artifact is missing or invalid.")
        return {"artifact_sha256": sha256(path), "evaluation": artifact}

    @app.post("/api/analyses", status_code=201)
    def perform(body: AnalyzeRequest):
        bundle = require_model()
        if app.state.storage_error:
            raise ServiceError(503, "history_unavailable", "History is unavailable; analysis cannot be saved.")
        chosen = get_sample(body.sample_id) if body.sample_id is not None else None
        raw = ">" + chosen["name"] + "\n" + chosen["sequence"] if chosen else body.sequence
        try:
            parsed = parse_sequence(raw)
        except ValueError as error:
            raise ServiceError(422, "invalid_sequence", str(error))
        # Serialize computation so concurrent laptop requests do not distort
        # each other's timings. Clients can retry after the active run finishes.
        if not compute_lock.acquire(blocking=False):
            raise ServiceError(503, "analysis_busy", "Another analysis is running. Wait for it to finish and retry.")
        try:
            result = analyze(raw, bundle, body.method, body.batch_size)
        except Exception:
            logging.exception("Prediction failed")
            raise ServiceError(500, "analysis_failed", "Analysis failed. Check the backend terminal; no run was saved.")
        finally:
            compute_lock.release()
        now = utc_now()
        source = {key: value for key, value in chosen.items() if key != "sequence"} if chosen else {
            "source": "User supplied DNA/FASTA; no accompanying ground-truth labels", "annotations": None}
        counts = {base: parsed["sequence"].count(base) for base in "ACGTN"}
        run = {"schema_version": 1, "id": str(uuid4()), "name": body.name or parsed["name"][:120],
               "created_at": now, "updated_at": now, "client_request_id": body.client_request_id,
               "input_sequence": parsed["sequence"], "input_provenance": source,
               "quality": {"base_counts": counts, "unknown_bases": counts["N"],
                           "gc_fraction_called": (counts["G"] + counts["C"]) / sum(counts[base] for base in "ACGT")},
               "analysis": result, "model_manifest": bundle.metadata,
               "measurement": {"os": platform.platform(), "cpu": platform.processor(), "logical_cpu_count": os.cpu_count(),
                               "python": platform.python_version(), "numpy": np.__version__, "model_warmed": True,
                               "model_manifest_sha256": app.state.model_manifest_sha256,
                               "algorithm_sha256": app.state.algorithm_sha256,
                               "repetitions": 1, "scope": "Single measured analysis-engine computation, not a repeated benchmark; excludes startup, HTTP request validation, JSON encoding, transfer and SQLite persistence."},
               "energy": {"label": "Estimated energy", "assumed_power_watts": body.assumed_power_watts,
                          "measured_runtime_ms": result["timing_ms"]["total_ms"],
                          "estimated_joules": body.assumed_power_watts * result["timing_ms"]["total_ms"] / 1000,
                          "formula": "assumed watts × measured computation milliseconds / 1000",
                          "assumption": "Constant assumed active power; not a laptop power measurement."},
               "evaluation": None}
        if chosen:
            run["evaluation"] = {"scope": chosen["annotation_scope"], "unscorable_annotated_boundaries": sum(not site["scorable"] for site in chosen["annotations"])}
            for kind in ("donor", "acceptor"):
                known = {site["position1"] for site in chosen["annotations"] if site["type"] == kind}
                sites = [site for site in result["candidates"] if site["type"] == kind]
                run["evaluation"][kind] = binary_metrics([site["position1"] in known for site in sites], [site["predicted"] for site in sites])
        storage_call(store.save, run)
        return run

    @app.get("/api/benchmarks")
    def benchmarks():
        bundle = require_model()
        path = settings.results_dir / "algorithm-verification.json"
        try:
            artifact = json.loads(path.read_text(encoding="utf-8"))
            if (artifact["model_id"] != bundle.identity
                    or artifact["dataset_fingerprint"] != bundle.metadata["dataset_fingerprint"]
                    or artifact["model_manifest_sha256"] != app.state.model_manifest_sha256
                    or artifact["code_sha256"]["backend/ecosplice/algorithms.py"] != app.state.algorithm_sha256):
                raise ValueError("Benchmark identity mismatch")
        except (OSError, ValueError, KeyError):
            raise ServiceError(503, "benchmarks_unavailable", "Matching measured reference experiment is missing or invalid.")
        return {"artifact_sha256": sha256(path), "benchmark": artifact}

    @app.post("/api/runs/{run_id}/comparison")
    def comparison(run_id: str, body: ComparisonRequest):
        bundle = require_model()
        run = storage_call(store.get, run_id)
        if (run["analysis"]["model_id"] != bundle.identity
                or run["measurement"]["model_manifest_sha256"] != app.state.model_manifest_sha256
                or run["measurement"]["algorithm_sha256"] != app.state.algorithm_sha256):
            raise ServiceError(409, "comparison_model_mismatch", "This run used different model/algorithm artifacts. Analyse it as a new run before measuring a comparison.")
        if not compute_lock.acquire(blocking=False):
            raise ServiceError(503, "analysis_busy", "Another analysis or comparison is running. Wait and retry.")
        try:
            measured = compare(run, bundle, body.repeats)
            measured["model_manifest_sha256"] = app.state.model_manifest_sha256
        except Exception:
            logging.exception("Comparison failed")
            raise ServiceError(500, "comparison_failed", "Comparison failed. Original predictions remain saved; no partial measurement was attached.")
        finally:
            compute_lock.release()
        return storage_call(store.attach_comparison, run_id, measured, utc_now())

    @app.get("/api/runs")
    def runs(limit: int = Query(default=50, ge=1, le=100), offset: int = Query(default=0, ge=0)):
        return storage_call(store.list, limit, offset)

    @app.get("/api/runs/{run_id}")
    def get_run(run_id: str):
        return storage_call(store.get, run_id)

    @app.patch("/api/runs/{run_id}")
    def rename(run_id: str, body: RenameRequest):
        return storage_call(store.rename, run_id, body.name, utc_now())

    @app.delete("/api/runs/{run_id}", status_code=204)
    def delete(run_id: str):
        storage_call(store.delete, run_id)
        return Response(status_code=204)

    @app.api_route("/api/runs/{run_id}/export", methods=["GET", "HEAD"])
    def export(run_id: str, request: Request, format: Literal["json", "csv", "html"] = "json",
               scope: Literal["all", "filtered"] = "all", type: Literal["donor", "acceptor"] | None = None,
               min_score: float | None = Query(default=None, ge=0, le=1, allow_inf_nan=False), predicted_only: bool = False,
               query: str = Query(default="", max_length=120)):
        if scope == "all" and (type is not None or min_score is not None or predicted_only or query.strip()):
            raise ServiceError(422, "invalid_export_scope", "Use scope=filtered when applying export filters.")
        run = storage_call(store.get, run_id)
        renderer, media = {"json": (json_report, "application/json"), "csv": (csv_report, "text/csv"),
                           "html": (html_report, "text/html")}[format]
        headers = {"Content-Disposition": f'attachment; filename="ecosplice-{run["id"]}-{scope}.{format}"'}
        if format == "html":
            headers["Content-Disposition"] = headers["Content-Disposition"].replace("attachment", "inline", 1)
            headers["Content-Security-Policy"] = "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"
        headers["X-Content-Type-Options"] = "nosniff"
        if request.method == "HEAD":
            return Response(media_type=media, headers=headers)
        report = select_report(run, scope, type, min_score, predicted_only, query)
        return Response(renderer(report), media_type=media, headers=headers)

    return app
