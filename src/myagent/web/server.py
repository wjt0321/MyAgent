"""FastAPI server for MyAgent Web UI."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from myagent.web.engine_manager import WebEngineManager
from myagent.web.health import router as health_router
from myagent.web.session import SessionStore
from myagent.memory.manager import MemoryEntry, MemoryManager, MemoryType
from myagent.workspace.manager import WorkspaceManager, get_workspace_dir


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager."""
    app.state.session_store = SessionStore()
    app.state.engine_manager = WebEngineManager()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="MyAgent Web UI",
        version="0.6.0",
        lifespan=lifespan,
    )

    # Include health check router
    app.include_router(health_router)

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

    @app.get("/api/workspace")
    async def get_workspace() -> dict[str, Any]:
        """Get workspace information."""
        ws_dir = get_workspace_dir()
        wm = WorkspaceManager(ws_dir)

        workspace_info: dict[str, Any] = {
            "path": str(ws_dir),
            "initialized": wm.exists(),
            "soul": None,
            "user": None,
            "identity": None,
            "memories": [],
            "projects": wm.list_projects(),
        }

        if wm.exists():
            soul = wm.read_soul()
            if soul:
                workspace_info["soul"] = soul[:500]
            user = wm.read_user_profile()
            if user:
                workspace_info["user"] = user[:500]
            identity = wm.read_identity()
            if identity:
                workspace_info["identity"] = identity[:500]

            for mem_path in wm.get_memory_files():
                try:
                    text = mem_path.read_text(encoding="utf-8")
                    # Parse frontmatter
                    import re
                    frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n+(.*)$', text, re.DOTALL)
                    if frontmatter_match:
                        frontmatter = frontmatter_match.group(1)
                        content = frontmatter_match.group(2).strip()
                        fields = {}
                        for line in frontmatter.strip().split('\n'):
                            if ':' in line:
                                key, value = line.split(':', 1)
                                fields[key.strip()] = value.strip()
                        workspace_info["memories"].append({
                            "name": fields.get("name", mem_path.stem),
                            "description": fields.get("description", ""),
                            "type": fields.get("type", "user"),
                            "filename": mem_path.name,
                            "content_preview": content[:200],
                        })
                    else:
                        workspace_info["memories"].append({
                            "name": mem_path.stem,
                            "description": "",
                            "type": "unknown",
                            "filename": mem_path.name,
                            "content_preview": text[:200],
                        })
                except Exception:
                    continue

        return workspace_info

    def _get_memory_manager() -> MemoryManager | None:
        """Get memory manager if workspace is initialized."""
        ws_dir = get_workspace_dir()
        memory_dir = ws_dir / "memory"
        if memory_dir.exists():
            return MemoryManager(memory_dir)
        return None

    @app.get("/api/memories")
    async def list_memories() -> list[dict[str, Any]]:
        """List all memories."""
        mm = _get_memory_manager()
        if mm is None:
            return []
        return [
            {
                "name": e.name,
                "description": e.description,
                "type": e.type.value,
                "filename": e.path.name if e.path else None,
                "content": e.content,
            }
            for e in mm.list_memories()
        ]

    @app.post("/api/memories", status_code=201)
    async def create_memory(request: dict[str, Any]) -> dict[str, Any]:
        """Create or update a memory."""
        mm = _get_memory_manager()
        if mm is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Workspace not initialized")

        entry = MemoryEntry(
            name=request["name"],
            description=request.get("description", ""),
            type=MemoryType(request.get("type", "user")),
            content=request["content"],
        )
        path = mm.save_memory(entry)
        return {
            "status": "saved",
            "name": entry.name,
            "filename": path.name,
        }

    @app.delete("/api/memories/{name}")
    async def delete_memory(name: str) -> dict[str, str]:
        """Delete a memory by name."""
        mm = _get_memory_manager()
        if mm is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Workspace not initialized")

        if mm.delete_memory(name):
            return {"status": "deleted"}
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Memory not found")

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

    @app.get("/api/files")
    async def list_files(path: str = ".") -> dict[str, Any]:
        """List files in a directory."""
        target = Path(path).resolve()
        if not target.exists():
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Path not found")

        entries = []
        try:
            for item in sorted(target.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                entries.append({
                    "name": item.name,
                    "path": str(item),
                    "is_dir": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else 0,
                })
        except PermissionError:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Permission denied")

        return {"path": str(target), "entries": entries}

    @app.get("/api/files/read")
    async def read_file(path: str) -> dict[str, Any]:
        """Read a file's content."""
        target = Path(path).resolve()
        if not target.exists() or not target.is_file():
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="File not found")

        try:
            content = target.read_text(encoding="utf-8")
            return {
                "path": str(target),
                "name": target.name,
                "content": content,
                "size": len(content),
            }
        except UnicodeDecodeError:
            return {
                "path": str(target),
                "name": target.name,
                "content": "[Binary file]",
                "size": target.stat().st_size,
            }
        except PermissionError:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Permission denied")

    @app.websocket("/ws/{session_id}")
    async def websocket_endpoint(websocket: WebSocket, session_id: str) -> None:
        """WebSocket endpoint for real-time chat."""
        await websocket.accept()
        store: SessionStore = app.state.session_store
        engine_manager: WebEngineManager = app.state.engine_manager
        session = store.get(session_id)

        if session is None:
            await websocket.send_json({"type": "error", "message": "Session not found"})
            await websocket.close()
            return

        if not engine_manager.is_configured():
            await websocket.send_json({
                "type": "error",
                "message": "LLM provider not configured. Set ZHIPU_API_KEY environment variable.",
            })
            await websocket.close()
            return

        engine = engine_manager.create_engine(session.agent)
        if engine is None:
            await websocket.send_json({"type": "error", "message": "Failed to create query engine"})
            await websocket.close()
            return

        try:
            while True:
                data = await websocket.receive_json()
                message = data.get("message", "").strip()
                action = data.get("action", "")

                if action == "approve_permission":
                    tool_use_id = data.get("tool_use_id", "")
                    approved = data.get("approved", False)
                    async for event in engine.continue_with_permission(tool_use_id, approved):
                        await _send_event(websocket, event)
                    continue

                if not message:
                    continue

                session.add_message("user", message)
                store._save(session)

                await websocket.send_json({
                    "type": "user",
                    "message": message,
                })

                await websocket.send_json({"type": "assistant_start"})

                response = await engine_manager.process_message(
                    engine,
                    message,
                    send_callback=websocket.send_json,
                )

                # Save assistant response to session
                if response:
                    session.add_message("assistant", response)
                    store._save(session)

                    # Trigger memory collection in background
                    import asyncio
                    asyncio.create_task(
                        engine_manager.collect_memory(message, response)
                    )

        except WebSocketDisconnect:
            pass

    async def _send_event(websocket: WebSocket, event: Any) -> None:
        """Send a stream event through WebSocket."""
        from myagent.engine.stream_events import (
            AssistantTextDelta,
            AssistantTurnComplete,
            ErrorEvent,
            PermissionRequestEvent,
            PermissionResultEvent,
            ToolExecutionCompleted,
            ToolExecutionStarted,
        )

        if isinstance(event, AssistantTextDelta):
            await websocket.send_json({"type": "assistant_delta", "text": event.text})
        elif isinstance(event, ToolExecutionStarted):
            await websocket.send_json({
                "type": "tool_call",
                "tool_name": event.tool_name,
                "arguments": event.arguments,
            })
        elif isinstance(event, ToolExecutionCompleted):
            await websocket.send_json({
                "type": "tool_result",
                "result": event.result,
                "is_error": event.is_error,
            })
        elif isinstance(event, AssistantTurnComplete):
            await websocket.send_json({"type": "assistant_done"})
        elif isinstance(event, PermissionRequestEvent):
            await websocket.send_json({
                "type": "permission_request",
                "tool_name": event.tool_name,
                "arguments": event.arguments,
                "reason": event.reason,
            })
        elif isinstance(event, PermissionResultEvent):
            await websocket.send_json({
                "type": "permission_result",
                "approved": event.approved,
                "reason": event.reason,
            })
        elif isinstance(event, ErrorEvent):
            await websocket.send_json({
                "type": "error",
                "message": f"{type(event.error).__name__}: {event.error}",
            })

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
