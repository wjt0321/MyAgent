# MyAgent Grafana Dashboard

## Import

1. Open Grafana → Dashboards → Import
2. Upload `dashboard.json` or paste the JSON content
3. Select your Prometheus data source
4. Click Import

## Panels

| Panel | Metric | Description |
|-------|--------|-------------|
| Requests / Second | `rate(query_requests_total[5m])` | Query throughput |
| Error Rate | `rate(query_errors_total) / rate(query_requests_total)` | Error percentage |
| Avg Response Time | `rate(query_duration_seconds_sum) / rate(query_duration_seconds_count)` | Mean latency |
| Active Sessions | `gateway_active_sessions` | Connected gateway sessions |
| Request Latency Distribution | `rate(query_duration_seconds_bucket)` | Latency heatmap |
| Tool Success Rate | `rate(tool_success) / (rate(tool_success) + rate(tool_failure))` | Tool reliability |
| Token Usage | `query_context_tokens` | Context size |
| Context Compactions | `rate(query_compactions_total)` | Compression frequency |
| Gateway Messages | `rate(gateway_messages_received_total)` | Messages by platform |
| Cost Tracking | `cost_tracker_total_cost` | Total cost in USD |

## Requirements

- Prometheus with MyAgent metrics endpoint scraped
- Grafana 9.0+
