# FlowState — Real-time Collaborative Task Orchestrator

Think "Trello meets Zapier" — tasks are modeled as a **Directed Acyclic Graph (DAG)** with automatic topological ordering, real-time WebSocket updates, and background Celery execution. This advanced scaffold demonstrates production-ready patterns:

- **DAG & Topological Sort**: Kahn's algorithm ensures dependency-respecting execution order
- **Real-time Updates**: Django Channels broadcasts WebSocket events per workspace
- **Background Processing**: Celery with Redis for distributed task execution
- **Retry Logic**: Exponential backoff on failures with result persistence
- **Performance Metrics**: Track execution duration, success/failure rates, retry counts
- **Logical Sharding**: Demo DB router showing tenant isolation (production-ready)
- **REST API**: Full CRUD with filtering, search, and execution control
- **Interactive Dashboard**: Real-time DAG visualization with metrics and live logs

## Quick Start (Local Dev)

**Prerequisites:**
- Docker & Docker Compose (for Redis + Postgres, or use SQLite for demo)
- Python 3.10+
- Git

**Setup (3 minutes):**

```bash
# Clone and enter project
cd FlowState

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Seed demo data (creates demo_workspace with 4 interconnected tasks)
python manage.py seed_demo

# Terminal 1: Start Celery worker
celery -A core worker -l info

# Terminal 2: Start Django dev server
python manage.py runserver

# Terminal 3: Open browser
# http://localhost:8000  ← Real-time dashboard
# http://localhost:8000/admin  ← Django admin
# http://localhost:8000/api/tasks/  ← REST API
```

## Key Features

### 1. Task DAG Model
- **Task model** with self-referential `dependencies` (ManyToMany)
- **Status tracking**: pending → running → done / failed
- **Execution timing**: `started_at`, `completed_at` fields
- **TaskResult model**: Persists execution outcomes, errors, retry counts

### 2. Topological Sort Utility
Located in `tasks/utils.py`, implements **Kahn's algorithm**:
```python
from tasks.utils import topological_sort
from tasks.models import Task

ordered_tasks = topological_sort(Task.objects.all())  # Returns sorted list
```
Detects cycles and raises `ValueError` on invalid DAGs.

### 3. Celery Worker with Retry Logic
`tasks/tasks.py` provides `execute_task(task_id)`:
- Runs with **max_retries=3**, exponential backoff
- Simulates work (2s) with 10% random failure for demo
- Broadcasts **WebSocket updates** to workspace channel on status change
- Records **TaskResult** with output, errors, and retry counts

### 4. Real-time WebSocket Broadcast
`tasks/consumers.py` / `tasks/routing.py`:
- Channels consumer groups per workspace: `workspace_<key>`
- Broadcasts task status updates instantly to all connected clients
- Dashboard auto-updates without polling

### 5. REST API (Django REST Framework)

**Endpoints:**

| Method | URL | Description |
|--------|-----|-------------|
| GET    | `/api/tasks/` | List all tasks (filter: `?workspace=key`, `?status=pending`, `?search=title`) |
| POST   | `/api/tasks/` | Create new task |
| GET    | `/api/tasks/{id}/` | Task details + results |
| POST   | `/api/tasks/execute/` | Execute single task |
| POST   | `/api/tasks/execute_dag/` | Topologically sort & enqueue all pending tasks |
| GET    | `/api/tasks/metrics/` | Metrics: success/failure counts, total duration, avg task time |

**Example: Execute DAG**
```bash
curl -X POST http://localhost:8000/api/tasks/execute_dag/ \
  -H "Content-Type: application/json" \
  -d '{"workspace_key": "demo_workspace"}'
```

### 6. Advanced Dashboard
Located at `/` (home):
- **Real-time metrics**: Total tasks, success/failure counts, duration
- **Live task list**: Color-coded by status with dependency info
- **Search & filter**: By status or keyword
- **Execution log**: Real-time WebSocket-driven event stream
- **One-click DAG execution**: Triggers topological-sorted Celery jobs
- **Manual task trigger**: Run individual pending tasks

### 7. Logical Sharding Demo
`tasks/db_router.py`:
- Routes read/write to tenant-specific DBs using `SHARD_MAP`
- Configured in `core/settings.py`:
  ```python
  SHARD_MAP = {
      'workspace_alpha': 'shard_1',
      'workspace_beta': 'shard_2',
  }
  ```
- Currently using SQLite; ready for production PostgreSQL multi-instance setup

### 8. Admin Panel
- Full CRUD for Tenants, Tasks, TaskResults
- View execution history with error messages
- Filter by workspace, status, date
- Search by task title/description

## Architecture Diagram

```
┌─────────────────┐
│  Django Admin   │
│  REST API       │──→ TaskViewSet (execute_dag, execute, metrics)
│  Dashboard      │
└────────┬────────┘
         │ WebSocket
         ↓
┌─────────────────────────────┐
│  Channels Consumer Group     │
│  workspace_demo_workspace   │
└────────┬────────────────────┘
         │ broadcasts to
         ├→ [Client 1 Browser]
         ├→ [Client 2 Browser]
         └→ [Client N Browser]

┌─────────────────────────┐
│  Django ORM (SQLite)    │  ← Task, TaskResult, Tenant models
│  Database              │
└────────┬────────────────┘
         ↑ query
         │
┌────────┴──────────────┐
│  Celery Worker Pool   │  ← execute_task (with retry logic)
│  (Redis broker)       │
└──────────────────────┘
```

## Testing

Run the comprehensive test suite:

```bash
python manage.py test tasks -v 2
```

**Tests cover:**
- Linear dependency chains (A → B → C)
- Diamond patterns (A → B,C → D)
- Cycle detection and error handling
- Task model methods (dependent_ids, duration_seconds)

All tests pass ✓

## Production Deployment

### Docker Compose (with PostgreSQL)

1. **Uncomment shard DBs in `core/settings.py`** and configure:
   ```python
   DATABASES['shard_1'] = {
       'ENGINE': 'django.db.backends.postgresql',
       'NAME': 'flowstate_shard_1',
       'HOST': 'db-shard-1',  # Docker service name
   }
   ```

2. **Extend `docker-compose.yml`** with Django + Gunicorn:
   ```yaml
   web:
     build: .
     ports:
       - "8000:8000"
     depends_on:
       - postgres
       - redis
     environment:
       - DEBUG=False
       - ALLOWED_HOSTS=yourdomain.com
   ```

3. **Deploy with:**
   ```bash
   docker-compose up -d
   ```

### Security Checklist
- [ ] Set `DEBUG=False` in production
- [ ] Use strong `SECRET_KEY` (e.g., `django-admin shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Use HTTPS with `SECURE_SSL_REDIRECT=True`
- [ ] Add authentication to WebSocket consumers (currently open for demo)
- [ ] Set up rate limiting on API endpoints
- [ ] Use managed PostgreSQL service (not on localhost)

## Performance Tuning

1. **DAG Execution**: Pre-fetch dependencies to avoid N+1 queries
   ```python
   from django.db.models import Prefetch
   tasks = Task.objects.prefetch_related(Prefetch('dependencies')).all()
   ```

2. **WebSocket Scaling**: Use channels-redis layer for multi-process deployments

3. **Celery Tuning**:
   ```python
   CELERY_TASK_TIME_LIMIT = 300  # 5 min hard limit
   CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4 min soft limit
   CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
   ```

## Troubleshooting

### "Task not found" errors
- Ensure migrations applied: `python manage.py migrate`
- Check task IDs in database: `python manage.py shell`

### WebSocket connection refused
- Verify Channels is installed: `pip install channels`
- Check ASGI application in `core/asgi.py`
- Ensure dev server is running: `python manage.py runserver`

### Celery tasks not executing
- Start worker: `celery -A core worker -l info`
- Check Redis is accessible: `redis-cli ping`
- Review Celery worker logs for errors

## Next Steps

1. **Authentication**: Add token-based or session auth for REST API
2. **Advanced Scheduling**: Cron-like recurring tasks
3. **Notifications**: Email/Slack alerts on task failure
4. **Monitoring**: Prometheus metrics + Grafana dashboards
5. **Audit Trail**: Track who triggered which executions
6. **Task Timeout**: Auto-cancel long-running tasks
7. **Distributed Tracing**: Integrate OpenTelemetry
8. **Multi-tenant UI**: Switch workspaces in dashboard

## Stack Summary

| Component | Version | Purpose |
|-----------|---------|---------|
| Django | 6.0 | Web framework & ORM |
| Django REST Framework | 3.14+ | REST API |
| Django Channels | 4.0+ | WebSockets |
| Celery | 5.3+ | Distributed task queue |
| Redis | 7+ | Message broker & cache |
| PostgreSQL | 15+ | Production database |
| SQLite | 3.x | Local dev database |

## License

This project is MIT licensed. See LICENSE file for details.

---

**Questions?** Open an issue or check the [Django Channels docs](https://channels.readthedocs.io/), [Celery docs](https://docs.celeryproject.io/), or [Topological Sort](https://en.wikipedia.org/wiki/Topological_sorting).
