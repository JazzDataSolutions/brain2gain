# Brain2Gain Production Monitoring Stack

## Overview

This monitoring stack provides comprehensive observability for the Brain2Gain production environment, including metrics collection, visualization, alerting, and log aggregation.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Application   │    │    Monitoring    │    │   Alerting      │
│                 │    │                  │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │  Backend    │ │───▶│ │  Prometheus  │ │───▶│ │AlertManager │ │
│ │  Frontend   │ │    │ │              │ │    │ │             │ │
│ │  Database   │ │    │ └──────────────┘ │    │ └─────────────┘ │
│ │  Cache      │ │    │                  │    │                 │
│ └─────────────┘ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│                 │    │ │   Grafana    │ │    │ │   Email     │ │
│ ┌─────────────┐ │    │ │              │ │    │ │   Slack     │ │
│ │    Logs     │ │───▶│ └──────────────┘ │    │ │ PagerDuty   │ │
│ │             │ │    │                  │    │ └─────────────┘ │
│ └─────────────┘ │    └──────────────────┘    └─────────────────┘
└─────────────────┘              │
                                 │
┌─────────────────────────────────▼─────────────────────────────────┐
│                          ELK Stack                                │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐              │
│  │  Filebeat   │─▶│   Logstash   │─▶│Elasticsearch│              │
│  │             │  │              │  │             │              │
│  └─────────────┘  └──────────────┘  └─────────────┘              │
│                                           │                       │
│                    ┌──────────────────────▼──────────────────────┐│
│                    │              Kibana                         ││
│                    └───────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

## Components

### Metrics Collection (Prometheus Stack)

#### Core Services
- **Prometheus**: Time-series database and monitoring system
- **Grafana**: Visualization and dashboarding
- **AlertManager**: Alert routing and notification management

#### Exporters
- **Node Exporter**: System-level metrics (CPU, memory, disk, network)
- **cAdvisor**: Container metrics and resource usage
- **PostgreSQL Exporter**: Database performance metrics
- **Redis Exporter**: Cache metrics and performance
- **Nginx Exporter**: Web server metrics
- **Blackbox Exporter**: External service monitoring and uptime

### Log Management (ELK Stack)

- **Elasticsearch**: Log storage and search engine
- **Logstash**: Log processing and transformation
- **Kibana**: Log visualization and analysis
- **Filebeat**: Log shipping from containers and files

## Quick Start

### 1. Deploy Monitoring Stack

```bash
# Deploy complete monitoring infrastructure
./deploy-monitoring.sh deploy

# Check deployment status
./deploy-monitoring.sh status

# View service logs
./deploy-monitoring.sh logs prometheus
```

### 2. Access Monitoring Services

| Service | URL | Credentials |
|---------|-----|-------------|
| Grafana | http://localhost:3001 | admin/admin123! |
| Prometheus | http://localhost:9090 | No auth |
| AlertManager | http://localhost:9093 | No auth |
| Kibana | http://localhost:5601 | No auth |
| Elasticsearch | http://localhost:9200 | No auth |

### 3. Configure Alerts

Edit `monitoring/alertmanager/alertmanager.yml` to configure notification channels:

```yaml
# Example Slack configuration
slack_configs:
  - api_url: 'YOUR_SLACK_WEBHOOK_URL'
    channel: '#alerts'
    title: 'Brain2Gain Alert'
    text: '{{ .CommonAnnotations.summary }}'
```

## Monitoring Metrics

### Application Metrics

#### Backend API
- **Request Rate**: `rate(http_requests_total[5m])`
- **Response Time**: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
- **Error Rate**: `rate(http_requests_total{status=~"5.."}[5m])`
- **Active Connections**: `http_connections_active`

#### Database
- **Connection Count**: `pg_stat_database_numbackends`
- **Query Performance**: `pg_stat_statements_mean_time`
- **Database Size**: `pg_database_size_bytes`
- **Replication Lag**: `pg_replication_lag`

#### Cache
- **Memory Usage**: `redis_memory_used_bytes`
- **Hit Rate**: `rate(redis_keyspace_hits_total[5m])`
- **Connected Clients**: `redis_connected_clients`
- **Commands/sec**: `rate(redis_commands_processed_total[5m])`

### System Metrics

#### Resource Usage
- **CPU Usage**: `100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)`
- **Memory Usage**: `(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100`
- **Disk Usage**: `(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100`
- **Network I/O**: `rate(node_network_receive_bytes_total[5m])`

#### Container Metrics
- **Container CPU**: `rate(container_cpu_usage_seconds_total[5m])`
- **Container Memory**: `container_memory_working_set_bytes`
- **Container Network**: `rate(container_network_receive_bytes_total[5m])`
- **Container Disk I/O**: `rate(container_fs_reads_bytes_total[5m])`

## Alerting Rules

### Critical Alerts
- **Service Down**: Any core service unavailable for > 1 minute
- **High Error Rate**: Error rate > 5% for > 2 minutes
- **Database Down**: PostgreSQL unavailable for > 1 minute
- **Cache Down**: Redis unavailable for > 1 minute

### Warning Alerts
- **High CPU Usage**: > 85% for > 5 minutes
- **High Memory Usage**: > 90% for > 5 minutes
- **Low Disk Space**: > 85% usage for > 5 minutes
- **High Response Time**: 95th percentile > 1 second for > 5 minutes

### Business Alerts
- **High Order Failure Rate**: > 5% order failures
- **Payment Processing Issues**: Payment service unavailable
- **Low Inventory**: Stock below minimum threshold

## Dashboards

### 1. Brain2Gain Overview
- Service status indicators
- Request rate and response time
- Error rate monitoring
- System resource usage

### 2. Application Performance
- Detailed API metrics
- Database performance
- Cache hit rates
- Business metrics

### 3. Infrastructure Monitoring
- System metrics
- Container performance
- Network statistics
- Disk I/O patterns

### 4. Logs Analysis
- Application logs by service
- Error log aggregation
- Security event monitoring
- Performance troubleshooting

## Log Management

### Log Sources
- **Application Logs**: Backend API, Frontend server
- **System Logs**: OS logs, Docker container logs
- **Database Logs**: PostgreSQL query logs, slow queries
- **Cache Logs**: Redis operations and errors
- **Load Balancer Logs**: HAProxy access and error logs

### Log Processing
Logstash processes logs with:
- JSON parsing for structured logs
- Grok patterns for unstructured logs
- GeoIP enrichment for access logs
- Field normalization and cleanup
- Sensitive data removal

### Log Retention
- **Hot data**: 7 days (fast SSD storage)
- **Warm data**: 30 days (standard storage)
- **Cold data**: 90 days (slow storage)
- **Archive**: 1 year (compressed backup)

## Maintenance

### Daily Tasks
- Review alert notifications
- Check service health dashboards
- Monitor resource usage trends
- Verify backup completions

### Weekly Tasks
- Analyze performance trends
- Review and tune alert thresholds
- Check log retention policies
- Update monitoring documentation

### Monthly Tasks
- Review and optimize dashboards
- Audit alert configurations
- Performance capacity planning
- Security monitoring review

## Troubleshooting

### Common Issues

#### Prometheus Not Scraping Targets
```bash
# Check target status
curl http://localhost:9090/api/v1/targets

# Check network connectivity
docker exec brain2gain-prometheus wget -qO- http://target:port/metrics
```

#### Grafana Dashboard Not Loading
```bash
# Check Grafana logs
docker logs brain2gain-grafana

# Verify Prometheus datasource
curl http://localhost:3001/api/datasources
```

#### Elasticsearch Cluster Issues
```bash
# Check cluster health
curl http://localhost:9200/_cluster/health

# Check node status
curl http://localhost:9200/_cat/nodes?v
```

#### High Memory Usage
```bash
# Check container memory usage
docker stats

# Analyze memory by service
docker exec brain2gain-prometheus \
  promtool query instant 'container_memory_working_set_bytes'
```

### Performance Tuning

#### Prometheus Optimization
- Adjust `scrape_interval` based on requirements
- Configure retention policies for disk space
- Use recording rules for complex queries
- Enable compression for remote storage

#### Elasticsearch Optimization
- Tune JVM heap size (50% of available memory)
- Configure index templates and mappings
- Set up index lifecycle management
- Optimize shard size and count

#### Grafana Optimization
- Use query caching for dashboards
- Optimize panel queries with time ranges
- Configure alert evaluation intervals
- Use template variables for efficiency

## Security

### Access Control
- Network segmentation for monitoring services
- Authentication for Grafana and Kibana
- API key management for external integrations
- Regular credential rotation

### Data Protection
- Encryption in transit (TLS)
- Sensitive data masking in logs
- Secure secret management
- Backup encryption

### Monitoring Security
- Failed authentication alerts
- Unusual access pattern detection
- Security event correlation
- Compliance monitoring

## Backup and Recovery

### Monitoring Data Backup
```bash
# Prometheus data backup
docker exec brain2gain-prometheus \
  tar czf /backup/prometheus-$(date +%Y%m%d).tar.gz /prometheus

# Grafana configuration backup
docker exec brain2gain-grafana \
  tar czf /backup/grafana-$(date +%Y%m%d).tar.gz /var/lib/grafana

# Elasticsearch data backup
curl -X PUT "localhost:9200/_snapshot/backup/snapshot_$(date +%Y%m%d)" \
  -H 'Content-Type: application/json' \
  -d '{"indices": "brain2gain-logs-*"}'
```

### Disaster Recovery
1. **Service Recovery**: Restore from container images
2. **Data Recovery**: Restore from backups
3. **Configuration Recovery**: Restore from version control
4. **Alert Verification**: Test all alerting channels

## Monitoring Best Practices

### Metrics
- Monitor the "Four Golden Signals": Latency, Traffic, Errors, Saturation
- Use appropriate metric types (counters, gauges, histograms)
- Implement proper labeling strategies
- Avoid high cardinality metrics

### Alerts
- Alert on symptoms, not causes
- Set appropriate thresholds based on SLIs
- Implement alert fatigue prevention
- Test alert channels regularly

### Dashboards
- Design for different audiences (dev, ops, business)
- Use consistent color schemes and layouts
- Include relevant time ranges and filters
- Document dashboard purposes and usage

### Logs
- Use structured logging (JSON format)
- Include correlation IDs for tracing
- Log at appropriate levels
- Implement log sampling for high-volume services

---

For support or questions about the monitoring stack, please refer to the main project documentation or contact the infrastructure team.