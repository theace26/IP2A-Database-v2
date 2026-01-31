# ADR-007: Observability Stack

## Status
Accepted

## Date
2026-01

## Context

IP2A Database needs monitoring and logging:
- Application logs (errors, warnings, info)
- Request tracing (slow requests, errors)
- System metrics (CPU, memory, disk)
- Alerting (when things go wrong)

Requirements:
1. **Portable** - Must work on local server and cloud
2. **Self-hosted** - No external service dependencies
3. **Cost-effective** - Open source, union budget
4. **Docker-based** - Consistent with rest of stack
5. **Industry standard** - Widely used, well-documented

## Decision

Use **Grafana + Loki + Promtail** stack:
- **Grafana** - Visualization and dashboards
- **Loki** - Log aggregation (like Prometheus, but for logs)
- **Promtail** - Log collection agent
- **Prometheus** (optional) - Metrics collection

All running in Docker containers, same as application.

## Consequences

### Positive
- **Unified interface** - Logs and metrics in one place (Grafana)
- **Portable** - Entire stack runs in Docker, works anywhere
- **Scalable** - Can handle significant log volume
- **Cost-effective** - All open source
- **Industry standard** - Large community, good documentation
- **Query language** - LogQL for powerful log queries

### Negative
- **Resource usage** - Adds containers and memory overhead
- **Learning curve** - Need to learn Grafana/Loki query languages
- **Configuration** - Initial setup takes time

### Neutral
- Can start with just logging, add metrics later
- Grafana supports alerting when ready

## Alternatives Considered

### ELK Stack (Elasticsearch, Logstash, Kibana)
- **Rejected:** Higher resource requirements
- **Rejected:** More complex to operate

### Cloud logging (CloudWatch, Stackdriver)
- **Rejected:** Vendor lock-in
- **Rejected:** Ongoing cost for log storage

### No centralized logging (just files)
- **Rejected:** Hard to search across containers
- **Rejected:** No visualization or alerting

### Paid solutions (Datadog, New Relic)
- **Rejected:** Cost prohibitive for union budget
- **Rejected:** External dependency

---

*Start with Loki for logs. Add Prometheus for metrics when needed.*
