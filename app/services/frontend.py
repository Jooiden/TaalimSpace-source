"""Optional single-origin hosting of the compiled UI; never serve workspace files."""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse


def mount_frontend(app: FastAPI, directory: Path) -> None:
    root = directory.resolve()
    if not (root / "index.html").is_file():
        raise RuntimeError("Build the frontend before enabling SERVE_FRONTEND")

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str) -> FileResponse:
        if path == "api" or path.startswith("api/") or any(part.startswith(".") for part in path.split("/")):
            raise HTTPException(404)
        file = (root / path).resolve()
        if not file.is_relative_to(root):
            raise HTTPException(404)
        if file.is_file():
            return FileResponse(file, headers={"Cache-Control": "no-cache"})
        if Path(path).suffix or path.startswith("assets/"):
            raise HTTPException(404)
        return FileResponse(root / "index.html", headers={"Cache-Control": "no-cache"})
