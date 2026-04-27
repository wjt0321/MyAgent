# CLAUDE.md

MyAgent project instructions for Claude Code / AI assistants.

## Project Overview

MyAgent is an autonomous AI agent platform with multi-channel gateway support. It provides:

- **Gateway**: Multi-platform messaging (Telegram, Discord, Slack, Feishu, QQ, Weixin, GitHub Webhook)
- **Web UI**: Workbench-style browser UI (FastAPI + vanilla JS, JWT auth, session isolation, command palette, tool cards, task timeline, Codex-style minimal design, toast notifications)
- **TUI**: Rich terminal interface (Textual) with status sidebar, slash commands, modal approvals
- **Engine**: LLM query engine with tool calling and context compression
- **Workspace**: Agent "home" with persistent memory and configuration
- **Memory**: Auto-extraction and RAG retrieval with persistent memory files
- **Task Engine**: Plan → Execute → Review workflow with snapshots, retry, restore
- **Agent Teams**: Multi-agent collaboration with Planner, Explorer, Executor, Reviewer roles
- **Codebase**: Automatic code scanning, indexing, and semantic search
- **Security**: File API path restriction, WebSocket token validation, GitHub webhook server-side secret validation, JWT authentication

## Key Concepts

### Workspace Structure

```
~/.myagent/
├── soul.md              # Agent personality/persona
├── user.md              # User profile
├── identity.md          # Agent identity
├── memory/              # Persistent memory files (Markdown + YAML Frontmatter)
│   ├── user/            # User preferences
│   ├── feedback/        # User feedback
│   ├── project/         # Project context
│   └── reference/       # External references
├── skills/              # Agent skills
├── projects/            # Project workspaces
├── sessions/            # Conversation history
└── logs/                # Log files
```

### Memory System

Memory files use Markdown with YAML Frontmatter:

```markdown
---
type: user
tags: [preference, coding-style]
created: 2026-04-23
updated: 2026-04-23
---

# User Preference

User prefers concise responses without summaries.
```

Four memory types: `user`, `feedback`, `project`, `reference`.

### Task Engine States

```
pending → planning → planned → executing → executed → reviewing → done
                    ↑___________________________________________|
                    (loop until review passes)
```

States: `pending`, `planning`, `planned`, `executing`, `executed`, `reviewing`, `done`, `failed`, `cancelled`.

### Agent Teams

Default team roles:

| Role | Agent | Responsibility |
|------|-------|---------------|
| Planner | `plan` | Create execution plan |
| Explorer | `explore` | Investigate codebase |
| Executor | `worker` | Implement features |
| Reviewer | `reviewer` | Review code |

## Development Guidelines

### When modifying code:

1. Check `docs/INDEX.md` for relevant architecture docs
2. Follow existing code style (Python 3.11+, type hints, Pydantic models)
3. Update tests if behavior changes
4. Update docs if API changes

### Key files to know:

- `src/myagent/cli.py` — CLI entry point (init, doctor, web, gateway, tui)
- `src/myagent/engine/query_engine.py` — Core query engine with context compression
- `src/myagent/engine/context_compression.py` — Context compression with dynamic threshold
- `src/myagent/web/server.py` — Web UI server (FastAPI + JWT auth + WebSocket)
- `src/myagent/web/auth.py` — JWT authentication module
- `src/myagent/web/engine_manager.py` — Web engine manager
- `src/myagent/tui/app.py` — TUI application with status sidebar and task panel
- `src/myagent/tui/screens.py` — TUI screens and modals
- `src/myagent/gateway/bot.py` — Gateway bot with session persistence
- `src/myagent/gateway/adapters/telegram.py` — Telegram adapter with inline permissions
- `src/myagent/gateway/adapters/discord.py` — Discord adapter with slash commands, message editing, thread creation
- `src/myagent/gateway/adapters/slack.py` — Slack Socket Mode adapter with Block Kit support
- `src/myagent/gateway/adapters/feishu.py` — Feishu Webhook + WebSocket adapter with signature verification
- `src/myagent/gateway/adapters/github.py` — GitHub webhook adapter
- `src/myagent/gateway/adapters/qq.py` — QQ adapter
- `src/myagent/gateway/adapters/weixin.py` — Weixin adapter
- `src/myagent/workspace/manager.py` — Workspace management
- `src/myagent/memory/manager.py` — Memory system
- `src/myagent/memory/extractor.py` — Memory auto-extraction and RAG retrieval
- `src/myagent/tasks/engine.py` — Task engine with snapshots and retry
- `src/myagent/tasks/models.py` — Task models and status definitions
- `src/myagent/teams/orchestrator.py` — Team orchestration
- `src/myagent/teams/models.py` — Team models
- `src/myagent/codebase/indexer.py` — Codebase indexing
- `src/myagent/codebase/search.py` — Codebase semantic search
- `src/myagent/tools/git.py` — Git operations tool
- `src/myagent/tools/code_interpreter.py` — Sandboxed Python code execution
- `src/myagent/tools/web_search.py` — Web search tool
- `src/myagent/tools/web_fetch.py` — Web fetch tool
- `src/myagent/tools/image_analyze.py` — Image analysis tool
- `src/myagent/tools/text_to_speech.py` — Text-to-speech tool
- `src/myagent/tools/todo.py` — Todo tracking tool
- `src/myagent/init/wizard.py` — Setup wizard
- `src/myagent/init/doctor.py` — Setup diagnostics
- `src/myagent/init/status.py` — Setup status detection
- `src/myagent/config/settings.py` — Configuration settings
- `src/myagent/config/hot_reload.py` — Config hot-reload watcher
- `src/myagent/llm/registry.py` — LLM provider registry
- `src/myagent/llm/stream_parser.py` — LLM stream parser
- `src/myagent/mcp/client.py` — MCP client
- `src/myagent/plugins/registry.py` — Plugin registry
- `src/myagent/monitoring/metrics.py` — Prometheus metrics
- `deploy/helm/myagent/` — Kubernetes Helm Chart
- `deploy/grafana/dashboard.json` — Grafana Dashboard
- `deploy/prometheus/alerts.yaml` — Prometheus Alert Rules

### Reference Projects

This project draws concepts from:

- **Claude Code** (`d:\源码库\claude-code-source-code`) — Memory system, TUI, tool design
- **Hermes Agent** (`d:\源码库\hermes-agent`) — Gateway pattern, Plan→Execute→Review
- **OpenClaw** (`d:\源码库\openclaw`) — Plugin system, identity layering
- **OpenHarness** (`d:\源码库\OpenHarness`) — Workspace structure, Agent definitions

See `docs/reference/04-concept-references.md` for detailed mapping.

## Commands

```bash
# Development
pip install -e ".[dev]"
python -m myagent web --port 8000
python -m myagent --tui

# Quality
ruff check src/
ruff format src/
mypy src/
pytest
```

## Notes

- Commit messages in Simplified Chinese, technical terms may use English
- Author: `wjt0321 <email@wxbfnnas.asia>`
- Never commit `.env` or API keys
