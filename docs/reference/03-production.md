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
```

### 4.2 指标

- 请求数
- 响应时间
- 错误率
- Token 使用量
- 成本

---

## 5. 备份

### 5.1 备份内容

```bash
# Workspace
tar czf myagent-backup.tar.gz ~/.myagent/

# 或仅备份配置
cp ~/.myagent/config.yaml backup/
cp ~/.myagent/gateway.yaml backup/
cp ~/.myagent/.env backup/
```

### 5.2 恢复

```bash
tar xzf myagent-backup.tar.gz -C ~/
```
