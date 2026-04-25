# Production Deployment Guide

This guide reflects the current `Dockerfile`, `docker-compose.yml`, and runtime behavior in the repository.

---

## 1. Deployment Model

Current deployment roles:

- `Web UI`: default container entrypoint, listens on `8000`
- `Gateway Bot`: optional compose profile
- `TUI`: local terminal entry, not a long-running container process
- `MYAGENT_HOME`: defaults to `/app/data` inside containers

Recommended mental model:

```text
browser -> Web UI -> MyAgent Core -> LLM / Workspace / Memory
gateway -> Bot    -> MyAgent Core -> LLM / Workspace / Memory
terminal -> TUI   -> MyAgent Core -> LLM / Workspace / Memory
```

---

## 2. Docker Image

Key facts about the current `Dockerfile`:

- Multi-stage build
- Runtime image based on `python:3.12-slim`
- Installs `.[web,gateway]`
- Default command:

```bash
myagent web --host 0.0.0.0 --port 8000 --json-log
```

- Health check:

```bash
myagent --version
```

So the image is optimized for the Web UI path, not for launching TUI by default.

---

## 3. Docker Compose

Current services in `docker-compose.yml`:

| Service | Purpose | Default |
|---------|---------|---------|
| `web` | Web UI | Yes |
| `bot` | Gateway Bot | No, requires `bot` profile |
| `redis` | Optional cache/dependency | No, requires `full` profile |

Recommended commands:

```bash
# Web only
docker compose up -d web

# Web + Bot
docker compose --profile bot up -d

# Full stack
docker compose --profile bot --profile full up -d
```

Volumes:

- `myagent-data:/app/data`
- `redis-data:/data`

---

## 4. Setup and Configuration

Recommended first boot:

```bash
myagent init --quick
myagent doctor
```

Use the full wizard when needed:

```bash
myagent init
```

Example environment variables:

```bash
# LLM Providers
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...
ZHIPU_API_KEY=...
ZHIPU_CN_API_KEY=...
MOONSHOT_API_KEY=...
MINIMAX_API_KEY=...
GEMINI_API_KEY=...
XAI_API_KEY=...
DASHSCOPE_API_KEY=...
DASHSCOPE_CN_API_KEY=...
BAIDU_API_KEY=...
SPARK_API_KEY=...
DOUBAO_API_KEY=...
HUNYUAN_API_KEY=...
OPENROUTER_API_KEY=...
SILICONFLOW_API_KEY=...
QWEN_API_KEY=...
COHERE_API_KEY=...
AZURE_API_KEY=...

# Gateway
FEISHU_APP_ID=cli_...
FEISHU_APP_SECRET=...
SLACK_BOT_TOKEN=xoxb-...
TELEGRAM_BOT_TOKEN=...
DISCORD_BOT_TOKEN=...
WEIXIN_TOKEN=...
QQ_APP_ID=...

# GitHub Integration
GITHUB_TOKEN=ghp_...
GITHUB_WEBHOOK_SECRET=...

# MyAgent
MYAGENT_HOME=/app/data
MYAGENT_DEFAULT_PROVIDER=zhipu
MYAGENT_DEFAULT_MODEL=glm-4
```

---

## 5. Health Checks

Useful probes:

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
curl http://localhost:8000/health/metrics
curl http://localhost:8000/api/setup/status
```

Notes:

- `/api/setup/status` shows whether the deployment is ready
- when setup is incomplete, the Web UI enters a `Setup Required` state

---

## 6. Logging and Monitoring

Recommended production command:

```bash
myagent web --json-log --log-level INFO
```

Built-in monitoring assets:

- `/health/metrics` for Prometheus metrics
- `deploy/grafana/dashboard.json` for Grafana
- `deploy/prometheus/alerts.yaml` for alert rules

---

## 7. Security Baseline

Minimum recommendations:

- enable authentication for the Web UI
- expose Web ports only in controlled environments
- use server-side `GITHUB_WEBHOOK_SECRET`
- run `myagent doctor` regularly to catch setup drift
- never commit `.env` or real secrets

---

## 8. Summary

For containerized deployment:

- treat `Web UI` as the default entrypoint
- treat `Bot` as an optional add-on service
- treat `TUI` as a local operator/developer workflow

That matches the repository's current Docker behavior.
