# AGENT.md

Telegraph style. Root rules only. Read scoped `AGENT.md` before touching a subtree.

## Start

- Repo: `https://github.com/wjt0321/myagent`
- Replies: repo-root file refs only, e.g. `src/myagent/engine/query_engine.py:80`. No absolute paths, no `~/`.
- First pass: read `docs/INDEX.md` for document navigation, then read only relevant docs.
- Missing deps: run `pip install -e ".[dev]"`, rerun once, then report first actionable error.

## Repo Map

- Core Python: `src/myagent/`
- CLI entry: `src/myagent/cli.py`
- Web UI: `src/myagent/web/` (FastAPI + static files)
- TUI: `src/myagent/tui/` (Textual)
- Gateway: `src/myagent/gateway/` (multi-platform adapters, session persistence)
- Engine: `src/myagent/engine/` (QueryEngine, context compression)
- LLM providers: `src/myagent/llm/providers/` (23 providers: Anthropic, OpenAI, DeepSeek, Gemini, xAI, Zhipu/Zhipu-CN, Moonshot/Moonshot-CN, MiniMax/MiniMax-CN, Alibaba/Alibaba-CN, HuggingFace, NVIDIA, Arcee, Xiaomi, Ollama, OpenRouter, Baidu, Spark, Doubao, Hunyuan)
- Tools: `src/myagent/tools/` (Bash, CodeInterpreter, Read, Write, Edit, Glob, Grep, Git, WebFetch, etc.)
- Memory: `src/myagent/memory/extractor.py` — MemoryExtractor, MemoryRAG
- Deploy: `deploy/` — Helm Chart, Grafana Dashboard, Prometheus alerts
- Workspace: `src/myagent/workspace/` (manager, templates, project)
- Memory: `src/myagent/memory/` (manager, collection)
- Tasks: `src/myagent/tasks/` (models, engine)
- Teams: `src/myagent/teams/` (models, orchestrator)
- Codebase: `src/myagent/codebase/` (indexer, search)
- Agents: `src/myagent/agents/` (definitions, loader)
- Plugins: `src/myagent/plugins/` (loader, manifest, registry, discovery, api)
- MCP: `src/myagent/mcp/` (client, config, types)
- Config: `src/myagent/config/` (settings, hot_reload)
- Web Auth: `src/myagent/web/auth.py` (JWT authentication)
- Docs: `docs/` (structured documentation)
- Tests: `tests/`

Scoped guides:

- `docs/architecture/` — system architecture docs
- `docs/design/` — UI/UX design docs
- `docs/reference/` — reference docs (getting started, config, production, concept references)
- `docs/plans/` — iteration plans and roadmaps

## Architecture

- Core must stay extension-agnostic. No core special cases for bundled plugin/provider ids when manifest/registry/capability contracts can express it.
- Extensions cross into core only via plugin SDK contract, manifest metadata, injected runtime helpers.
- Extension production code must not import core `src/**` internals directly.
- Core code/tests must not deep-import plugin internals. Use plugin public API / generic contract.
- New seams: backwards-compatible, documented, versioned.
- Config contract: keep exported types, schema/help, generated metadata, baselines, docs aligned.
- Plugin architecture direction: manifest-first control plane; targeted runtime loaders.

## Commands

- Runtime: Python 3.11+
- Install: `pip install -e ".[dev]"`
- Dev CLI: `python -m myagent ...`
- Build: `python -m build`
- Lint: `ruff check src/`
- Format: `ruff format src/`
- Typecheck: `mypy src/`
- Tests: `pytest`
- Coverage: `pytest --cov=myagent`

## Gates

- Pre-commit: run `ruff check` and `mypy src/` before committing.
- Do not land related failing format/lint/type/tests.
- If failures are unrelated on latest `origin/main`, say so and give scoped proof.
- Gateway adapters: Telegram/Discord/Slack/Feishu all support inline permission requests via `send_permission_request()`. Discord supports slash commands (`/ask`, `/reset`, `/agent`), message editing, and thread creation. Slack supports Block Kit messages. Feishu supports WebSocket mode.
- Web UI auth: JWT-based, optional password protection via `myagent.web.auth`.
- Session isolation: Web UI sessions are scoped per-user via `user_id` field.

## Code Style

- Python 3.11+. Type hints required.
- No `Any` unless necessary; prefer real types / `object` / narrow adapters.
- External boundaries: prefer Pydantic models.
- Runtime branching: prefer discriminated unions / closed enums over freeform strings.
- Avoid magic sentinels like `?? 0`, empty object/string when semantics change.
- Dynamic import: do not mix static and dynamic import for same module in prod path.
- Cycles: keep import cycles minimal.
- Classes: no prototype mixins/mutations. Use explicit inheritance/composition.
- Comments: brief only for non-obvious logic.
- File size: split around ~700 LOC when it improves clarity/testability.
- Product naming: **MyAgent** product/docs; `myagent` CLI/package/path/config.

## Tests

- pytest. Tests colocated in `tests/`.
- Clean up timers/env/globals/mocks/sockets/temp dirs/module state.
- Keep tests at seam depth: unit-test pure helpers/contracts; one integration smoke per boundary.
- Mock expensive runtime seams directly: filesystem crawls, provider SDKs, network.
- Prefer injected deps over module mocks.
- Share fixtures/builders; do not recreate temp dirs in every case.
- Delete duplicate assertions when another test owns the boundary.

## Docs

- Update docs when behavior/API changes.
- Changelog: user-facing only. Pure test/internal changes usually no entry.

## Git

- Commits: conventional-ish, concise/action-oriented. Group related changes.
- Commit message in Simplified Chinese, technical terms may use English.
- Author: `wjt0321 <email@wxbfnnas.asia>`
- No manual stash/autostash unless explicitly requested. No branch/worktree changes unless requested.
- Do not delete/rename unexpected files; ask if it blocks.

## Security

- Never commit real credentials, live config.
- Secrets: API keys under `~/.myagent/.env` or environment variables.
- Env keys: check `~/.profile` or system env.
- Dependency changes require explicit approval.

## Acknowledgments

- **Claude Code** — Memory system, TUI interaction, tool pluginization
- **Hermes Agent** — Gateway pattern, multi-platform adapters, Plan→Execute→Review workflow
- **OpenClaw** — Plugin system, identity layering, context management
- **OpenHarness** — Workspace structure, Agent definitions, Swarm collaboration
