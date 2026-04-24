# MyAgent Helm Chart

## Prerequisites

- Kubernetes 1.24+
- Helm 3.12+
- Prometheus Operator (optional, for ServiceMonitor and PrometheusRule)

## Install

```bash
helm install myagent ./deploy/helm/myagent \
  --set myagent.apiKeys.anthropic="your-api-key" \
  --set myagent.provider="anthropic" \
  --set myagent.model="claude-sonnet-4"
```

## Upgrade

```bash
helm upgrade myagent ./deploy/helm/myagent
```

## Uninstall

```bash
helm uninstall myagent
```

## Configuration

See [values.yaml](values.yaml) for all available options.

### Key Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `myagent.provider` | LLM provider | `anthropic` |
| `myagent.model` | Model name | `claude-sonnet-4` |
| `myagent.apiKeys.anthropic` | Anthropic API key | `""` |
| `myagent.apiKeys.openai` | OpenAI API key | `""` |
| `myagent.gateway.enabled` | Enable gateway | `true` |
| `myagent.web.enabled` | Enable web UI | `true` |
| `myagent.monitoring.enabled` | Enable metrics | `true` |
| `persistence.enabled` | Enable persistent storage | `true` |
| `persistence.size` | Storage size | `1Gi` |

### Gateway Configuration

```bash
helm install myagent ./deploy/helm/myagent \
  --set myagent.gateway.telegram.enabled=true \
  --set myagent.gateway.telegram.token="your-telegram-token"
```

### Monitoring

Requires Prometheus Operator installed:

```bash
helm install myagent ./deploy/helm/myagent \
  --set myagent.monitoring.enabled=true
```

This will create:
- ServiceMonitor for metrics scraping
- PrometheusRule for alerting

## Persistence

Data is stored in a PersistentVolumeClaim at `/app/data`:
- Session history
- Configuration files
- Memory entries

## Security

- Runs as non-root user (UID 1000)
- Read-only root filesystem
- API keys stored as Kubernetes Secrets
- JWT secret auto-generated if not provided
