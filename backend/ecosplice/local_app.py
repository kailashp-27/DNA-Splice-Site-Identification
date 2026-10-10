"""Serve the built React application and API from one loopback service."""
from pathlib import Path
from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles

from .api import ROOT, create_app


class DashboardFiles(StaticFiles):
    async def get_response(self, path, scope):
        # Missing API routes must remain 404s, never become frontend documents.
        normalized = path.replace("\\", "/").lstrip("/")
        if normalized == "api" or normalized.startswith("api/"):
            raise HTTPException(404, "API endpoint not found")
        response = await super().get_response(path, scope)
        response.headers["X-Content-Type-Options"] = "nosniff"
        # A rebuilt index must point to the current content-hashed assets.
        response.headers["Cache-Control"] = "no-cache" if path in (".", "index.html") else "public, max-age=3600"
        return response


def create_local_app(settings=None, frontend_dir=None):
    directory = Path(frontend_dir) if frontend_dir else ROOT / "dist"
    if not (directory / "index.html").is_file():
        raise FileNotFoundError("Built dashboard missing. Run setup-ecosplice.cmd, or npm run build during development.")
    app = create_app(settings)
    app.mount("/", DashboardFiles(directory=directory, html=True), name="dashboard")
    return app
