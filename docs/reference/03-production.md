# Production Deployment Guide

> 本文档描述 MyAgent 的生产环境部署方案。

---

## 1. 部署架构

```
┌─────────────────────────────────────────┐
│              Load Balancer               │
└─────────────────────────────────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───┴───┐    ┌────┴────┐   ┌────┴────┐
│ Web UI │    │ Gateway │   │  TUI    │
│ :8000  │    │ :18789  │   │ (CLI)   │
└───┬───┘    └────┬────┘   └─────────┘
    │              │
    └──────────────┘
                   │
         ┌─────────┴──────────┐
         │   MyAgent Core     │
         │  ┌──────────────┐  │
         │  │  QueryEngine │  │
         │  │  AgentLoader │  │
         │  │  ToolRegistry│  │
         │  └──────────────┘  │
         └────────────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───┴───┐    ┌────┴────┐   ┌────┴────┐
│ LLM   │    │ Memory  │   │Workspace│
│ API   │    │ Store   │   │  Files  │
└───────┘    └─────────┘   └─────────┘
```

---

## 2. Docker 部署

### 2.1 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -e ".[dev]"

EXPOSE 8000 18789

CMD ["myagent", "web", "--host", "0.0.0.0", "--port", "8000"]
```

### 2.2 docker-compose.yml

```yaml
version: '3.8'

services:
  myagent:
    build: .
    ports:
      - "8000:8000"
      - "18789:18789"
    volumes:
      - ~/.myagent:/app/.myagent
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - FEISHU_APP_ID=${FEISHU_APP_ID}
      - FEISHU_APP_SECRET=${FEISHU_APP_SECRET}
    restart: unless-stopped
```

### 2.3 启动

```bash
docker-compose up -d
```

---

## 3. 安全建议

### 3.1 API Key 管理

- 使用环境变量或 secrets 管理
- 定期轮换
- 最小权限原则

### 3.2 访问控制

- 启用 pairing_required
- 配置 allowed_users
- 使用 HTTPS

### 3.3 日志管理

```yaml
logging:
  level: INFO
  file: ~/.myagent/logs/myagent.log
  max_size: 10MB
  backup_count: 5
```

---

## 4. 监控

### 4.1 健康检查

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
curl http://localhost:8000/health/metrics
```

### 4.2 Prometheus 指标

MyAgent 内置 Prometheus 风格的指标采集，通过 `/health/metrics` 暴露：

| 指标名 | 类型 | 说明 |
|--------|------|------|
| `llm_request_duration_seconds` | Histogram | LLM 请求延迟 |
| `tool_execution_duration_seconds` | Histogram | 工具执行延迟 |
| `query_turns_total` | Counter | 总对话轮数 |
| `tool_executions_total` | Counter | 总工具执行次数 |
| `tool_errors_total` | Counter | 工具执行错误次数 |
| `query_errors_total` | Counter | 查询错误次数 |

### 4.3 Grafana 配置示例

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'myagent'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/health/metrics'
```

---

## 5. 结构化日志

### 5.1 启用 JSON 日志

```bash
myagent web --json-log --log-level INFO
```

日志输出示例：

```json
{"timestamp": "2026-04-24T10:30:00", "level": "INFO", "logger": "myagent.web", "message": "Request GET /api/sessions", "request_id": "a1b2c3d4", "method": "GET", "path": "/api/sessions"}
```

### 5.2 日志文件

默认日志路径：`~/.myagent/logs/myagent.log`

- 自动轮转：单文件 10MB，保留 5 个备份
- 支持 JSON 格式（生产环境推荐）
- 支持彩色控制台输出（开发环境）

---

## 6. 配置热重载

### 6.1 启用热重载

修改 `~/.myagent/config.yaml` 后，MyAgent 会自动检测并重新加载配置，无需重启服务。

### 6.2 查看热重载状态

```bash
curl http://localhost:8000/api/config/status
```

响应：

```json
{"hot_reload_enabled": true, "watched_files": ["/home/user/.myagent/config.yaml"]}
```

---

## 7. LLM 重试机制

MyAgent 内置指数退避重试，自动处理以下网络异常：

- `asyncio.TimeoutError` — 请求超时
- `ConnectionError` — 连接失败
- `httpx.HTTPStatusError` — HTTP 5xx 错误
- `httpx.ConnectError` — 连接错误
- `httpx.ReadTimeout` — 读取超时

重试策略：
- 最大重试次数：3 次
- 初始延迟：1 秒
- 退避倍数：2x（1s, 2s, 4s）
- 最大延迟：60 秒

---

## 8. Gateway 会话管理

### 8.1 会话持久化

Gateway 自动将用户会话映射持久化到 `~/.myagent/gateway_sessions.yaml`，重启后自动恢复。

### 8.2 LRU 缓存与 TTL 驱逐

```python
from myagent.gateway.session_store import GatewaySessionStore

# 默认配置: 最大 1000 个会话, 7 天 TTL
store = GatewaySessionStore()

# 自定义配置
store = GatewaySessionStore(
    max_sessions=500,      # 最多保留 500 个会话
    ttl_seconds=86400,     # 1 天 TTL
)
```

- **LRU 驱逐**: 当会话数超过 `max_sessions` 时，自动移除最久未使用的会话
- **TTL 驱逐**: 超过 `ttl_seconds` 未活跃的会话自动过期
- **启动清理**: 每次启动时自动清理过期会话

### 8.3 适配器状态

| 适配器 | 状态 | 特性 |
|--------|------|------|
| Telegram | ✅ 完整 | 长轮询、权限内联、消息去重 |
| Discord | ✅ 完整 | Gateway WebSocket、心跳、自动重连、Session Resume |
| Slack | ✅ 完整 | Socket Mode、自动重连、指数退避 |
| Feishu | ✅ 完整 | Webhook、签名验证、Token 刷新、多认证模式 |
| GitHub | ✅ 完整 | Webhook、PR/Issue 分析 |

---

## 9. 备份

### 9.1 备份内容

```bash
# Workspace
tar czf myagent-backup.tar.gz ~/.myagent/

# 或仅备份配置
cp ~/.myagent/config.yaml backup/
cp ~/.myagent/gateway.yaml backup/
cp ~/.myagent/.env backup/
```

### 9.2 恢复

```bash
tar xzf myagent-backup.tar.gz -C ~/
```
