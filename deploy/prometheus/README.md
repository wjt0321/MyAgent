# MyAgent Prometheus Configuration

## Alerts

The `alerts.yaml` file contains Prometheus alerting rules for MyAgent.

### Alert Rules

| Alert | Condition | Severity |
|-------|-----------|----------|
| MyAgentHighErrorRate | Error rate > 10% for 2m | warning |
| MyAgentHighLatency | P95 latency > 10s for 3m | warning |
| MyAgentLLMProviderErrors | Error rate > 0.5/sec for 1m | critical |
| MyAgentToolFailures | Tool failure rate > 30% for 5m | warning |
| MyAgentFrequentCompaction | Compaction rate > 0.1/sec for 5m | info |
| MyAgentGatewayDisconnected | No active sessions for 5m | warning |
| MyAgentHighTokenUsage | Context tokens > 80,000 | info |
| MyAgentCostThreshold | Total cost > $10 | info |

## ServiceMonitor

The `servicemonitor.yaml` configures Prometheus Operator to scrape MyAgent metrics.

### Requirements

- Prometheus Operator installed in cluster
- MyAgent deployed with `myagent.monitoring.enabled=true`

### Apply

```bash
kubectl apply -f deploy/prometheus/servicemonitor.yaml
kubectl apply -f deploy/prometheus/alerts.yaml
```

Or use the Helm chart which includes these resources automatically.
