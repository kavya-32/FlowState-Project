"""
Seed metrics-focused data with emphasis on:
- Total Tasks
- Successful Executions
- Failed Executions
- Total Duration
Usage: python manage.py seed_metrics_data
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from tasks.models import Tenant, Task, TaskResult


class Command(BaseCommand):
    help = 'Seed metrics-rich execution history and tasks'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== SEEDING METRICS DATA ===\n'))

        # Add more tasks to increase total task count
        new_tasks_added = self.add_more_tasks()
        
        # Add extensive execution history
        execution_records = self.add_extensive_execution_history()

        self.stdout.write(self.style.SUCCESS('\n=== METRICS SEEDING COMPLETE ===\n'))
        self.print_metrics_summary(new_tasks_added, execution_records)

    def add_more_tasks(self):
        """Add 50+ additional tasks across workspaces"""
        self.stdout.write('➕ Adding more tasks...\n')
        
        workspaces = Tenant.objects.all()
        new_count = 0
        
        for ws in workspaces:
            # Add 5-8 more tasks per workspace
            num_tasks = random.randint(5, 8)
            
            for i in range(num_tasks):
                status = random.choices(
                    [Task.STATUS_PENDING, Task.STATUS_DONE, Task.STATUS_RUNNING, Task.STATUS_FAILED],
                    weights=[50, 35, 10, 5],
                    k=1
                )[0]
                
                task = Task.objects.create(
                    title=f'{ws.name} - Task {ws.tasks.count() + i + 1}',
                    description=f'Additional task for {ws.name} workspace',
                    workspace=ws,
                    status=status,
                    started_at=timezone.now() - timedelta(hours=random.randint(1, 72)) if status != Task.STATUS_PENDING else None,
                    completed_at=timezone.now() - timedelta(hours=random.randint(0, 48)) if status in [Task.STATUS_DONE, Task.STATUS_FAILED] else None
                )
                
                # Randomly link some tasks as dependencies
                if ws.tasks.count() > 1 and random.random() > 0.6:
                    existing_tasks = list(ws.tasks.exclude(id=task.id))[:3]
                    if existing_tasks:
                        task.dependencies.add(random.choice(existing_tasks))
                
                new_count += 1
        
        self.stdout.write(f'  ✓ Added {new_count} new tasks\n')
        return new_count

    def add_extensive_execution_history(self):
        """Add 100+ execution records with realistic success/failure distribution"""
        self.stdout.write('⏱️  Adding extensive execution history...\n')
        
        # Get all tasks
        all_tasks = Task.objects.all()
        created_count = 0
        success_count = 0
        failure_count = 0
        total_duration = 0
        
        for task in all_tasks:
            # Create 2-5 execution records per task
            num_executions = random.randint(2, 5)
            
            for attempt in range(num_executions):
                # 85% success rate
                success = random.random() > 0.15
                
                # Generate timestamps
                days_back = random.randint(1, 30)
                started = timezone.now() - timedelta(days=days_back, hours=random.randint(0, 23), minutes=random.randint(0, 59))
                
                # Duration: 10 seconds to 30 minutes
                duration_seconds = random.randint(10, 1800)
                completed = started + timedelta(seconds=duration_seconds)
                
                error_msg = ''
                if not success:
                    errors = [
                        'Connection timeout',
                        'API rate limit exceeded',
                        'Database lock timeout',
                        'Service unavailable',
                        'File not found',
                        'Permission denied',
                        'Out of memory',
                        'Invalid parameter',
                        'Network unreachable',
                        'SSL certificate error'
                    ]
                    error_msg = random.choice(errors)
                    failure_count += 1
                else:
                    success_count += 1
                
                total_duration += duration_seconds
                
                result = TaskResult.objects.create(
                    task=task,
                    status='success' if success else 'failure',
                    output=f'Execution {"completed" if success else "failed"} - Attempt {attempt + 1}',
                    error_message=error_msg,
                    started_at=started,
                    completed_at=completed if success else None,
                    retry_count=attempt
                )
                created_count += 1
        
        self.stdout.write(f'  ✓ Created {created_count} execution records\n')
        self.stdout.write(f'    - {success_count} successful\n')
        self.stdout.write(f'    - {failure_count} failed\n')
        self.stdout.write(f'    - Total duration: {self._format_duration(total_duration)}\n')
        
        return {
            'total': created_count,
            'success': success_count,
            'failure': failure_count,
            'total_duration': total_duration
        }

    def _format_duration(self, seconds):
        """Format seconds to human readable duration"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f'{hours}h {minutes}m {secs}s'

    def print_metrics_summary(self, new_tasks, execution_data):
        """Print comprehensive metrics summary"""
        self.stdout.write(self.style.SUCCESS('\n📊 METRICS DASHBOARD\n'))
        
        # Calculate all metrics
        total_tasks = Task.objects.count()
        total_results = TaskResult.objects.count()
        success_results = TaskResult.objects.filter(status='success').count()
        failure_results = TaskResult.objects.filter(status='failure').count()
        
        # Total duration calculation
        all_results = TaskResult.objects.all()
        total_seconds = sum(
            (r.completed_at - r.started_at).total_seconds() 
            for r in all_results 
            if r.completed_at and r.started_at
        )
        
        # Task duration (sum of all task durations)
        all_tasks = Task.objects.all()
        task_duration_seconds = sum(
            (t.completed_at - t.started_at).total_seconds()
            for t in all_tasks
            if t.completed_at and t.started_at
        )
        
        total_all_seconds = total_seconds + task_duration_seconds
        
        self.stdout.write(f'\n{"─" * 60}')
        self.stdout.write('TOTAL TASKS')
        self.stdout.write(f'{"─" * 60}')
        self.stdout.write(f'{total_tasks:>15} tasks')
        self.stdout.write(f'  ├─ Pending:  {Task.objects.filter(status=Task.STATUS_PENDING).count()}')
        self.stdout.write(f'  ├─ Running:  {Task.objects.filter(status=Task.STATUS_RUNNING).count()}')
        self.stdout.write(f'  ├─ Done:     {Task.objects.filter(status=Task.STATUS_DONE).count()}')
        self.stdout.write(f'  └─ Failed:   {Task.objects.filter(status=Task.STATUS_FAILED).count()}')
        
        self.stdout.write(f'\n{"─" * 60}')
        self.stdout.write('SUCCESSFUL EXECUTIONS')
        self.stdout.write(f'{"─" * 60}')
        self.stdout.write(f'{success_results:>15} executions')
        if total_results > 0:
            success_rate = (success_results / total_results) * 100
            self.stdout.write(f'  └─ Success Rate: {success_rate:.1f}%')
        
        self.stdout.write(f'\n{"─" * 60}')
        self.stdout.write('FAILED EXECUTIONS')
        self.stdout.write(f'{"─" * 60}')
        self.stdout.write(f'{failure_results:>15} executions')
        if total_results > 0:
            failure_rate = (failure_results / total_results) * 100
            self.stdout.write(f'  └─ Failure Rate: {failure_rate:.1f}%')
        
        self.stdout.write(f'\n{"─" * 60}')
        self.stdout.write('TOTAL DURATION')
        self.stdout.write(f'{"─" * 60}')
        self.stdout.write(f'{self._format_duration(int(total_all_seconds)):>15}')
        self.stdout.write(f'  ├─ Execution Time: {self._format_duration(int(total_seconds))}')
        self.stdout.write(f'  ├─ Task Time:      {self._format_duration(int(task_duration_seconds))}')
        self.stdout.write(f'  └─ Average Task:   {self._format_duration(int(task_duration_seconds / max(total_tasks, 1)))}')
        
        self.stdout.write(f'\n{"─" * 60}')
        self.stdout.write('WORKSPACES OVERVIEW')
        self.stdout.write(f'{"─" * 60}')
        
        for ws in Tenant.objects.all().order_by('name'):
            task_count = ws.tasks.count()
            result_count = TaskResult.objects.filter(task__workspace=ws).count()
            success_count = TaskResult.objects.filter(task__workspace=ws, status='success').count()
            
            self.stdout.write(f'\n{ws.name}')
            self.stdout.write(f'  Tasks: {task_count} | Executions: {result_count} | Successful: {success_count}')
        
        self.stdout.write(f'\n{"─" * 60}\n')
        
        self.stdout.write(self.style.SUCCESS('✅ Metrics data seeded successfully!'))
        self.stdout.write('\nYour dashboard now includes:')
        self.stdout.write(f'  ✓ {total_tasks} total tasks')
        self.stdout.write(f'  ✓ {total_results} execution records')
        self.stdout.write(f'  ✓ {success_results} successful executions')
        self.stdout.write(f'  ✓ {failure_results} failed executions')
        self.stdout.write(f'  ✓ {self._format_duration(int(total_all_seconds))} total tracked time')
