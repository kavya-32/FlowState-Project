#!/usr/bin/env python
"""
Verification script to display seeded data and statistics.
Usage: python verify_data.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tasks.models import Tenant, Task, TaskResult
from collections import defaultdict

print("\n" + "="*70)
print("FLOWSTATE DATA VERIFICATION")
print("="*70 + "\n")

# ========== WORKSPACE SUMMARY ==========
print("📊 WORKSPACE SUMMARY\n")
workspaces = Tenant.objects.all()
print(f"Total Workspaces: {workspaces.count()}\n")

for ws in workspaces:
    tasks = ws.tasks.all()
    results = TaskResult.objects.filter(task__workspace=ws)
    
    status_counts = defaultdict(int)
    for task in tasks:
        status_counts[task.status] += 1
    
    print(f"  🏢 {ws.name} ({ws.key})")
    print(f"     Tasks: {tasks.count()} | Results: {results.count()}")
    for status, count in status_counts.items():
        emoji = {'pending': '⏳', 'running': '▶️', 'done': '✓', 'failed': '✗'}.get(status, '•')
        print(f"       {emoji} {status}: {count}")
    print()

# ========== TASK DAG VISUALIZATION ==========
print("\n" + "="*70)
print("📈 SAMPLE DAG: E-Commerce Pipeline")
print("="*70 + "\n")

ecommerce = Tenant.objects.get(key='ecommerce_pipeline')
tasks = ecommerce.tasks.all().order_by('id')

for task in tasks:
    deps = list(task.dependencies.values_list('title', flat=True))
    deps_str = f" ← {', '.join(deps)}" if deps else ""
    
    status_emoji = {
        'pending': '⏳',
        'running': '▶️',
        'done': '✓',
        'failed': '✗'
    }.get(task.status, '•')
    
    duration = f" ({task.duration_seconds():.1f}s)" if task.duration_seconds() else ""
    
    print(f"{status_emoji} Task {task.id}: {task.title}{duration}")
    print(f"   └─ {task.description}{deps_str}\n")

# ========== EXECUTION HISTORY ==========
print("\n" + "="*70)
print("📋 EXECUTION HISTORY")
print("="*70 + "\n")

results = TaskResult.objects.all().order_by('-started_at')[:10]
for result in results:
    status_emoji = {
        'success': '✓',
        'failure': '✗',
        'retry': '⟳'
    }.get(result.status, '•')
    
    duration = f"{result.duration_seconds():.2f}s" if result.duration_seconds() else "—"
    
    print(f"{status_emoji} Task {result.task.id}: {result.task.title}")
    print(f"   Status: {result.status} | Duration: {duration} | Attempt: {result.retry_count + 1}")
    if result.error_message:
        print(f"   Error: {result.error_message[:60]}...")
    print()

# ========== STATISTICS ==========
print("\n" + "="*70)
print("📊 STATISTICS")
print("="*70 + "\n")

total_tasks = Task.objects.count()
total_results = TaskResult.objects.count()

task_stats = Task.objects.values('status').distinct()
result_stats = TaskResult.objects.values('status').distinct()

print(f"Total Tasks: {total_tasks}")
print(f"Total Executions: {total_results}")
print()

print("Task Status Distribution:")
for status in ['pending', 'running', 'done', 'failed']:
    count = Task.objects.filter(status=status).count()
    pct = (count / total_tasks * 100) if total_tasks > 0 else 0
    bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
    print(f"  {status:10} {count:3} [{bar}] {pct:5.1f}%")

print("\nExecution Result Distribution:")
success = TaskResult.objects.filter(status='success').count()
failure = TaskResult.objects.filter(status='failure').count()
retry = TaskResult.objects.filter(status='retry').count()

print(f"  Success: {success}")
print(f"  Failure: {failure}")
print(f"  Retry:   {retry}")

# Calculate success rate
if total_results > 0:
    success_rate = (success / total_results) * 100
    print(f"\n  Success Rate: {success_rate:.1f}%")

print("\n" + "="*70)
print("\n✅ Data verification complete!")
print("\nNext steps:")
print("  1. Start Celery worker: celery -A core worker -l info")
print("  2. Start Django dev server: python manage.py runserver")
print("  3. Visit dashboard: http://localhost:8000")
print("  4. Switch workspaces using the dropdown")
print("  5. Click 'Execute DAG' to trigger task execution")
print("\n" + "="*70 + "\n")
