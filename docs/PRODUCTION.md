# Production Deployment Guide

This guide covers deploying MyAgent in production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Configuration](#configuration)
4. [Docker Deployment](#docker-deployment)
5. [Systemd Service](#systemd-service)
6. [Reverse Proxy](#reverse-proxy)
7. [SSL/TLS](#ssltls)
8. [Monitoring](#monitoring)
9. [Backup](#backup)
10. [Security Hardening](#security-hardening)

---

## Prerequisites

- Python 3.11+
- Docker 24+ (optional)
- Systemd (for Linux service management)
- Nginx or Caddy (for reverse proxy)

## Environment Setup

### 1. Create a dedicated user

```bash
sudo useradd -r -s /bin/false myagent
sudo mkdir -p /opt/myagent
sudo chown myagent:myagent /opt/myagent
```

### 2. Set up the environment

```bash
sudo -u myagent bash
cd /opt/myagent
python3 -m venv venv
source venv/bin/activate
pip install myagent
```

### 3. Initialize configuration

```bash
myagent init
```

This creates `/home/myagent/.myagent/` with all config files.

### 4. Set environment variables

Create `/opt/myagent/.env`:

```bash
# LLM Providers (International)
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...
ZHIPU_API_KEY=...
MOONSHOT_API_KEY=...
MINIMAX_API_KEY=...
XAI_API_KEY=...
GEMINI_API_KEY=...
DASHSCOPE_API_KEY=...
HF_API_KEY=...
NVIDIA_API_KEY=...
ARCEE_API_KEY=...
XIAOMI_API_KEY=...

# LLM Providers (China Domestic - API Key NOT interchangeable)
ZHIPU_CN_API_KEY=...
MOONSHOT_CN_API_KEY=...
MINIMAX_CN_API_KEY=...
DASHSCOPE_CN_API_KEY=...

# Gateway Platforms (enable only what you need)
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx
DISCORD_BOT_TOKEN=...
TELEGRAM_BOT_TOKEN=...

# Webhook Secret (auto-generated during init, rotate regularly)
WEBHOOK_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# MyAgent Settings
MYAGENT_HOME=/home/myagent/.myagent
MYAGENT_MODEL_DEFAULT=anthropic/claude-sonnet-4
```

Set secure permissions:

```bash
chmod 600 /opt/myagent/.env
chown myagent:myagent /opt/myagent/.env
```

---

## Configuration

### Gateway YAML

Edit `~/.myagent/gateway.yaml`:

```yaml
platforms:
  feishu:
    enabled: true
    extra:
      app_id: ${FEISHU_APP_ID}
      app_secret: ${FEISHU_APP_SECRET}
      domain: feishu
      connection_mode: websocket
      auth_mode: tenant

  slack:
    enabled: true
    token: ${SLACK_BOT_TOKEN}

  discord:
    enabled: false

  telegram:
    enabled: false

default_reset_policy:
  mode: both
  at_hour: 4
  idle_minutes: 1440
  notify: true

reset_triggers:
  - /new
  - /reset

sessions_dir: /home/myagent/.myagent/sessions
always_log_local: true
streaming:
  enabled: true
  transport: edit
  edit_interval: 1.0
  buffer_threshold: 40
```

### Agent Config

Edit `~/.myagent/config.yaml`:

```yaml
model:
  default: anthropic/claude-sonnet-4

context:
  auto_compact_threshold: 0.8
  max_turns: 50

memory:
  enabled: true
  scope: project

logging:
  level: info
  trajectory: true
  trajectory_path: /home/myagent/.myagent/trajectories
```

---

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e "."

# Create non-root user
RUN useradd -m -u 1000 myagent

# Copy application
COPY src/ ./src/
RUN pip install --no-cache-dir -e "."

# Set up config directory
RUN mkdir -p /app/.myagent && chown -R myagent:myagent /app/.myagent

USER myagent

ENV MYAGENT_HOME=/app/.myagent
ENV PYTHONUNBUFFERED=1

EXPOSE 8000 18789

CMD ["myagent", "web", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: "3.8"

services:
  myagent:
    build: .
    container_name: myagent
    restart: unless-stopped
    ports:
      - "8000:8000"
      - "18789:18789"
    volumes:
      - myagent-data:/app/.myagent
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - FEISHU_APP_ID=${FEISHU_APP_ID}
      - FEISHU_APP_SECRET=${FEISHU_APP_SECRET}
      - SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}
      - WEBHOOK_SECRET=${WEBHOOK_SECRET}
      - MYAGENT_HOME=/app/.myagent
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  myagent-data:
```

### Deploy

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f myagent

# Update
docker-compose pull
docker-compose up -d
```

---

## Systemd Service

Create `/etc/systemd/system/myagent.service`:

```ini
[Unit]
Description=MyAgent AI Gateway
After=network.target

[Service]
Type=simple
User=myagent
Group=myagent
WorkingDirectory=/opt/myagent
Environment=MYAGENT_HOME=/home/myagent/.myagent
EnvironmentFile=/opt/myagent/.env
ExecStart=/opt/myagent/venv/bin/myagent web --host 0.0.0.0 --port 8000
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=myagent

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/myagent/.myagent
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable myagent
sudo systemctl start myagent
sudo systemctl status myagent
```

View logs:

```bash
sudo journalctl -u myagent -f
```

---

## Reverse Proxy

### Nginx

```nginx
server {
    listen 443 ssl http2;
    server_name myagent.example.com;

    ssl_certificate /etc/letsencrypt/live/myagent.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/myagent.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    location /ws {
        proxy_pass http://127.0.0.1:18789;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

### Caddy

```caddy
myagent.example.com {
    reverse_proxy /ws 127.0.0.1:18789
    reverse_proxy 127.0.0.1:8000
}
```

---

## SSL/TLS

### Let's Encrypt

```bash
sudo certbot --nginx -d myagent.example.com
```

Or with Caddy (automatic):

```bash
caddy run --config /etc/caddy/Caddyfile
```

---

## Monitoring

### Health Checks

MyAgent exposes health endpoints:

```bash
curl http://localhost:8000/health/live   # Liveness
curl http://localhost:8000/health/ready  # Readiness
curl http://localhost:8000/health/metrics # Prometheus metrics
```

### Prometheus Metrics

Key metrics to monitor:

| Metric | Type | Description |
|--------|------|-------------|
| `llm_request_duration_seconds` | Histogram | LLM request latency |
| `tool_execution_duration_seconds` | Histogram | Tool execution latency |
| `query_turns_total` | Counter | Total conversation turns |
| `tool_executions_total` | Counter | Total tool executions |
| `tool_errors_total` | Counter | Tool execution errors |
| `query_errors_total` | Counter | Query errors |
| `myagent_messages_received_total` | Counter | Messages received by platform |
| `myagent_messages_sent_total` | Counter | Messages sent by platform |
| `myagent_sessions_active` | Gauge | Active sessions |

### Grafana Dashboard

Import dashboard ID `myagent` (coming soon) or create custom panels.

### Alerting Rules

```yaml
groups:
  - name: myagent
    rules:
      - alert: MyAgentDown
        expr: up{job="myagent"} == 0
        for: 5m
        annotations:
          summary: "MyAgent is down"

      - alert: HighErrorRate
        expr: rate(myagent_errors_total[5m]) > 0.1
        for: 10m
        annotations:
          summary: "High error rate detected"

      - alert: LLMLatencyHigh
        expr: histogram_quantile(0.95, rate(myagent_llm_latency_seconds_bucket[5m])) > 30
        for: 5m
        annotations:
          summary: "LLM latency is high"
```

---

## Backup

### What to Back Up

| Path | Description | Frequency |
|------|-------------|-----------|
| `~/.myagent/config.yaml` | Agent settings | Daily |
| `~/.myagent/gateway.yaml` | Gateway config | Daily |
| `~/.myagent/.env` | Secrets (encrypt!) | Daily |
| `~/.myagent/sessions/` | Session data | Hourly |
| `~/.myagent/trajectories/` | Conversation logs | Daily |

### Backup Script

```bash
#!/bin/bash
BACKUP_DIR="/backup/myagent/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

cp ~/.myagent/config.yaml "$BACKUP_DIR/"
cp ~/.myagent/gateway.yaml "$BACKUP_DIR/"
cp ~/.myagent/.env "$BACKUP_DIR/"
tar czf "$BACKUP_DIR/sessions.tar.gz" -C ~/.myagent sessions/

# Encrypt secrets
gpg --symmetric --cipher-algo AES256 "$BACKUP_DIR/.env"
rm "$BACKUP_DIR/.env"

# Upload to S3 (optional)
aws s3 sync "$BACKUP_DIR" s3://my-backup-bucket/myagent/
```

---

## Security Hardening

### 1. File Permissions

```bash
chmod 700 ~/.myagent
chmod 600 ~/.myagent/.env
chmod 600 ~/.myagent/config.yaml
chmod 600 ~/.myagent/gateway.yaml
```

### 2. Firewall

```bash
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 22/tcp    # SSH
sudo ufw deny 8000/tcp   # Direct Web UI access
sudo ufw deny 18789/tcp  # Direct Gateway access
sudo ufw enable
```

### 3. Fail2Ban

Create `/etc/fail2ban/jail.local`:

```ini
[myagent]
enabled = true
port = http,https
filter = myagent
logpath = /var/log/myagent/auth.log
maxretry = 5
bantime = 3600
```

### 4. Regular Updates

```bash
# Update MyAgent
pip install -U myagent

# Update system
sudo apt update && sudo apt upgrade -y

# Rotate secrets monthly
myagent init --rotate-secrets
```

### 5. Audit Logging

Enable audit logging in `config.yaml`:

```yaml
logging:
  level: info
  trajectory: true
  trajectory_path: /var/log/myagent/trajectories
  audit: true
  audit_path: /var/log/myagent/audit
```

---

## Troubleshooting Production Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| Gateway disconnects | Network timeout | Increase `proxy_read_timeout` in Nginx |
| High memory usage | Session accumulation | Lower `session_store_max_age_days` |
| Slow responses | LLM latency | Enable streaming, use faster model |
| Webhook 401 | Secret mismatch | Regenerate `WEBHOOK_SECRET` |
| Platform not receiving | Firewall | Open required ports |

---

## Support

- GitHub Issues: https://github.com/myagent/myagent/issues
- Documentation: https://docs.myagent.ai
- Discord: https://discord.gg/myagent
