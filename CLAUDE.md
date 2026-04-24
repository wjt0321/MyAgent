# CLAUDE.md

MyAgent project instructions for Claude Code / AI assistants.

## Project Overview

MyAgent is an autonomous AI agent platform with multi-channel gateway support. It provides:

- **Gateway**: Multi-platform messaging (Feishu, Slack, Discord, Telegram, etc.)
- **Web UI**: Real-time WebSocket chat interface (FastAPI + vanilla JS, JWT auth, session isolation)
- **TUI**: Rich terminal interface (Textual)
- **Engine**: LLM query engine with tool calling
- **Workspace**: Agent "home" with persistent memory and configuration
- **Memory**: Auto-collection and manual editing of agent memory
- **Task Engine**: Plan → Execute → Review workflow (with auto-execution on approval)
- **Agent Teams**: Multi-agent collaboration with role-based assignment
- **Codebase**: Automatic code scanning, indexing, and search
- **Security**: File API path restriction, WebSocket token validation, GitHub webhook server-side secret validation

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

- `src/myagent/cli.py` — CLI entry point
- `src/myagent/engine/query_engine.py` — Core query engine
- `src/myagent/web/server.py` — Web UI server (FastAPI + JWT auth)
- `src/myagent/web/auth.py` — JWT authentication module
- `src/myagent/gateway/bot.py` — Gateway bot with session persistence
- `src/myagent/gateway/adapters/telegram.py` — Telegram adapter with inline permissions
- `src/myagent/gateway/adapters/discord.py` — Discord Gateway WebSocket adapter with slash commands, message editing, thread creation
- `src/myagent/gateway/adapters/slack.py` — Slack Socket Mode adapter with Block Kit support
- `src/myagent/gateway/adapters/feishu.py` — Feishu Webhook + WebSocket adapter with signature verification
- `src/myagent/gateway/adapters/github.py` — GitHub webhook adapter
- `src/myagent/workspace/manager.py` — Workspace management
- `src/myagent/memory/manager.py` — Memory system
- `src/myagent/memory/extractor.py` — Memory auto-extraction and RAG retrieval
- `src/myagent/tasks/engine.py` — Task engine
- `src/myagent/teams/orchestrator.py` — Team orchestration
- `src/myagent/codebase/indexer.py` — Codebase indexing
- `src/myagent/tools/git.py` — Git operations tool
- `src/myagent/tools/code_interpreter.py` — Sandboxed Python code execution
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
