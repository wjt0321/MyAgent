# Production Deployment Guide

> 本文档描述当前仓库中 `Dockerfile`、`docker-compose.yml` 与运行时行为一致的生产部署方式。

---

## 1. 部署模型

当前仓库的部署模型是：

- `Web UI`：默认的容器入口，监听 `8000`
- `Gateway Bot`：通过 compose profile 单独启动
- `TUI`：本地终端入口，不作为容器默认常驻进程
- `MYAGENT_HOME`：容器内默认目录为 `/app/data`

推荐理解为：

```text
browser -> Web UI -> MyAgent Core -> LLM / Workspace / Memory
gateway -> Bot    -> MyAgent Core -> LLM / Workspace / Memory
terminal -> TUI   -> MyAgent Core -> LLM / Workspace / Memory
```

---

## 2. Docker 镜像

当前 `Dockerfile` 的关键行为：

- 使用多阶段构建
- 运行镜像基于 `python:3.12-slim`
- 依赖安装包含 `.[web,gateway]`
- 默认命令：

```bash
myagent web --host 0.0.0.0 --port 8000 --json-log
```

- 健康检查默认执行：

```bash
myagent --version
```

因此，镜像默认适合提供 `Web UI`，而不是直接跑 `TUI`。

---

## 3. Docker Compose

当前 `docker-compose.yml` 的服务结构如下：

| 服务 | 作用 | 默认启用 |
|------|------|----------|
| `web` | Web UI | 是 |
| `bot` | Gateway Bot | 否，需要 `bot` profile |
| `redis` | 可选缓存/外部依赖 | 否，需要 `full` profile |

推荐命令：

```bash
# 仅启动 Web UI
docker compose up -d web

# 启动 Web UI + Bot
docker compose --profile bot up -d

# 启动完整栈
docker compose --profile bot --profile full up -d
```

数据卷：

- `myagent-data:/app/data`
- `redis-data:/data`

---

## 4. 初始化与配置

首次部署后，建议先完成初始化：

```bash
myagent init --quick
myagent doctor
```

如果需要完整向导：

```bash
myagent init
```

关键环境变量示例：

```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...
ZHIPU_API_KEY=...
DASHSCOPE_API_KEY=...
GITHUB_WEBHOOK_SECRET=...
MYAGENT_HOME=/app/data
```

---

## 5. 运行与健康检查

Web 相关检查：

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
curl http://localhost:8000/health/metrics
curl http://localhost:8000/api/setup/status
```

说明：

- `/api/setup/status` 用于确认当前容器是否已完成 setup
- 当 setup 未完成时，Web UI 会显示 `Setup Required`

---

## 6. 日志与监控

生产环境建议使用：

```bash
myagent web --json-log --log-level INFO
```

当前监控能力包括：

- `/health/metrics` 暴露 Prometheus 指标
- `deploy/grafana/dashboard.json` 提供 Grafana Dashboard
- `deploy/prometheus/alerts.yaml` 提供告警规则

---

## 7. 安全基线

建议至少启用以下策略：

- 为 Web UI 启用认证
- 仅在受控环境中暴露 Web 端口
- 使用服务端 `GITHUB_WEBHOOK_SECRET`
- 通过 `myagent doctor` 定期检查 setup 与配置缺口
- 不要将 `.env` 或真实密钥提交到仓库

---

## 8. 说明

如果你要容器化部署：

- 把 `Web UI` 当成默认入口
- 把 `Bot` 当成可选附加服务
- 把 `TUI` 当成本地运维/开发入口

这样才与当前仓库中的 `Dockerfile` 和 `docker-compose.yml` 保持一致。
