# MyAgent Deployment Resources

## Overview

This directory contains production deployment resources for MyAgent.

## Contents

| Directory | Description |
|-----------|-------------|
| `helm/` | Helm chart for Kubernetes deployment |
| `grafana/` | Grafana dashboard JSON |
| `prometheus/` | Prometheus alerts and ServiceMonitor |

## Quick Start

### Kubernetes (Helm)

```bash
helm install myagent ./deploy/helm/myagent \
  --set myagent.apiKeys.anthropic="your-api-key" \
  --set myagent.provider="anthropic"
```

### Docker Compose

See root `docker-compose.yml` for local development.

### Monitoring Stack

1. Deploy MyAgent with monitoring enabled:
   ```bash
   helm install myagent ./deploy/helm/myagent \
     --set myagent.monitoring.enabled=true
   ```

2. Import Grafana dashboard:
   - Open Grafana → Dashboards → Import
   - Upload `deploy/grafana/dashboard.json`

3. Alerts are auto-configured via PrometheusRule

## Architecture

```
┌─────────────────────────────────────────┐
│              Ingress                     │
│         (myagent.local)                  │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│           Service                        │
│      Port 8080 (HTTP)                    │
│      Port 9090 (Metrics)                 │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│         Deployment                       │
│    ┌──────────────────────┐             │
│    │   MyAgent Container  │             │
│    │   - Web UI (8080)    │             │
│    │   - Metrics (9090)   │             │
│    │   - Gateway          │             │
│    └──────────────────────┘             │
│              │                           │
│    ┌─────────▼──────────┐               │
│    │   PVC (1Gi)        │               │
│    │   /app/data        │               │
│    └────────────────────┘               │
└─────────────────────────────────────────┘
```
