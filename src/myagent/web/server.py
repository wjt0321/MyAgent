"""FastAPI server for MyAgent Web UI."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from myagent.web.session import SessionStore


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager."""
    app.state.session_store = SessionStore()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="MyAgent Web UI",
        version="0.1.0",
        lifespan=lifespan,
    )

    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def root() -> str:
        """Serve the main HTML page."""
        index_path = static_dir / "index.html"
        if index_path.exists():
            return index_path.read_text(encoding="utf-8")
        return _fallback_html()

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "ok", "version": "0.1.0"}

    @app.get("/api/sessions")
    async def list_sessions() -> list[dict[str, Any]]:
        """List all sessions."""
        store: SessionStore = app.state.session_store
        return [s.to_dict() for s in store.list_all()]

    @app.post("/api/sessions", status_code=201)
    async def create_session(request: dict[str, Any]) -> dict[str, Any]:
        """Create a new session."""
        store: SessionStore = app.state.session_store
        agent = request.get("agent", "general")
        model = request.get("model", "glm-4.7")
        session = store.create(agent=agent, model=model)
        return session.to_dict()

    @app.get("/api/sessions/{session_id}")
    async def get_session(session_id: str) -> dict[str, Any]:
        """Get a session by ID."""
        store: SessionStore = app.state.session_store
        session = store.get(session_id)
        if session is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Session not found")
        return session.to_dict()

    @app.delete("/api/sessions/{session_id}")
    async def delete_session(session_id: str) -> dict[str, str]:
        """Delete a session."""
        store: SessionStore = app.state.session_store
        if store.delete(session_id):
            return {"status": "deleted"}
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Session not found")

    @app.websocket("/ws/{session_id}")
    async def websocket_endpoint(websocket: WebSocket, session_id: str) -> None:
        """WebSocket endpoint for real-time chat."""
        await websocket.accept()
        store: SessionStore = app.state.session_store
        session = store.get(session_id)

        if session is None:
            await websocket.send_json({"type": "error", "message": "Session not found"})
            await websocket.close()
            return

        try:
            while True:
                data = await websocket.receive_json()
                message = data.get("message", "").strip()

                if not message:
                    continue

                session.add_message("user", message)
                store._save(session)

                await websocket.send_json({
                    "type": "user",
                    "message": message,
                })

                await websocket.send_json({
                    "type": "assistant_start",
                })

                response_text = f"Echo: {message}"
                session.add_message("assistant", response_text)
                store._save(session)

                await websocket.send_json({
                    "type": "assistant_delta",
                    "text": response_text,
                })

                await websocket.send_json({
                    "type": "assistant_done",
                })

        except WebSocketDisconnect:
            pass

    return app


def _fallback_html() -> str:
    """Fallback HTML when static files are not available."""
    return """<!DOCTYPE html>
<html>
<head><title>MyAgent Web UI</title></head>
<body>
    <h1>MyAgent Web UI</h1>
    <p>Static files not found. Please build the frontend.</p>
</body>
</html>"""
