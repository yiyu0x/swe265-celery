# Celery Demo 

This repository demonstrates a Celery setup with Docker, including RabbitMQ as message broker, Prometheus for monitoring, and a custom Celery exporter.

## Components

- **RabbitMQ**: Message broker
- **Celery Worker**: Processes tasks
- **Celery Exporter**: Exports Prometheus metrics
- **Prometheus**: Monitors the system

## Commands

### Start the services

```bash
docker-compose up
```

### Stop the services

```bash
docker-compose down
```

### Run test tasks

```bash
docker exec -it celery_worker python test_tasks.py
```

### Check worker stats

```bash
docker exec -it celery_worker python -m celery -A tasks inspect stats
```

## Access Points

- RabbitMQ Management: http://localhost:15672 (user/pass)
- Metrics Endpoint: http://localhost:8888/metrics

## Key Metrics

The Celery exporter provides several important metrics:

1. **celery_total_tasks_executed** - Total number of task executions (both successful and failed).
2. **celery_registered_tasks** - Number of different task types registered in the Celery system.
3. **celery_task_registered** - Individual metrics for each registered task, labeled with task name.

### Retrieving Metrics with curl

You can retrieve these metrics directly using curl:

```bash
# Get all metrics
curl http://localhost:8888/metrics

# Filter for total tasks executed
curl http://localhost:8888/metrics -s | grep celery_total_tasks_executed_total

# Filter for registered tasks count
curl http://localhost:8888/metrics -s | grep celery_registered_tasks

# Filter for individual registered tasks
curl http://localhost:8888/metrics -s | grep celery_task_registered
```
