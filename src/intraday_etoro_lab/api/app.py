from __future__ import annotations

import secrets
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, Literal, Protocol

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field

UI_DIR = Path(__file__).resolve().parent.parent / "ui"


class Command(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal[
        "demo-offline",
        "fixture-start",
        "fixture-close",
        "backtest",
        "pause-entries",
        "reconcile",
        "arm-demo",
        "flatten-owned-demo",
        "cancel-pending-entries",
    ]
    confirm: str = ""
    budget: str | None = None


class ControlService(Protocol):
    def snapshot(self) -> dict[str, Any]: ...

    def command(
        self, action: str, confirm: str = "", budget: str | None = None
    ) -> dict[str, Any]: ...


class ControlSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    host: Literal["127.0.0.1"] = "127.0.0.1"
    port: int = Field(default=8765, ge=1024, le=65535)

    @property
    def origin(self) -> str:
        return f"http://{self.host}:{self.port}"


def create_app(
    service: ControlService, token: str, settings: ControlSettings | None = None
) -> FastAPI:
    if len(token) < 32:
        raise ValueError("Se requiere un token local aleatorio de al menos 32 caracteres")
    settings = settings or ControlSettings()
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def local_boundary(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.headers.get("host") != f"127.0.0.1:{settings.port}":
            return JSONResponse({"error": "HOST_REJECTED"}, status_code=400)
        if any(h in request.headers for h in ("forwarded", "x-forwarded-host", "x-forwarded-for")):
            return JSONResponse({"error": "PROXY_REJECTED"}, status_code=400)
        origin = request.headers.get("origin")
        if origin is not None and origin != settings.origin:
            return JSONResponse({"error": "ORIGIN_REJECTED"}, status_code=403)
        if request.url.query:
            return JSONResponse({"error": "QUERY_REJECTED"}, status_code=400)
        if request.method not in {"GET", "HEAD"} and origin != settings.origin:
            return JSONResponse({"error": "ORIGIN_REQUIRED"}, status_code=403)
        if request.headers.get("sec-fetch-site") == "cross-site":
            return JSONResponse({"error": "CROSS_SITE_REJECTED"}, status_code=403)
        if request.url.path.startswith("/api/"):
            provided = request.headers.get("authorization", "")
            if not secrets.compare_digest(provided, f"Bearer {token}"):
                return JSONResponse({"error": "AUTH_REQUIRED"}, status_code=401)
        response = await call_next(request)
        response.headers.update(
            {
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
                "Content-Security-Policy": "default-src 'self'; script-src 'self'; "
                "style-src 'self'; "
                "object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
            }
        )
        return response

    @app.get("/")
    def dashboard() -> FileResponse:
        return FileResponse(UI_DIR / "index.html")

    @app.get("/assets/app.js")
    def javascript() -> FileResponse:
        return FileResponse(UI_DIR / "app.js", media_type="text/javascript")

    @app.get("/assets/style.css")
    def stylesheet() -> FileResponse:
        return FileResponse(UI_DIR / "style.css", media_type="text/css")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"process": "OK", "meaning": "Salud del proceso; no habilita trading"}

    @app.get("/api/state")
    def state() -> dict[str, Any]:
        return service.snapshot()

    @app.post("/api/commands")
    def commands(command: Command) -> dict[str, Any]:
        if command.action in {"arm-demo", "flatten-owned-demo"} and command.confirm != "DEMO_ONLY":
            raise HTTPException(400, "Confirmación DEMO_ONLY requerida")
        try:
            return service.command(command.action, command.confirm, command.budget)
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(409, str(exc)) from exc

    return app
