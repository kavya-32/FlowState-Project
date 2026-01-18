from django.core.management.base import BaseCommand
from tasks.models import Tenant, Task
from tasks.utils import topological_sort
from tasks.tasks import execute_task


class Command(BaseCommand):
    help = 'Seed demo workspace and tasks to demonstrate DAG + Celery execution'

    def handle(self, *args, **options):
        # Create workspace
        ws, created = Tenant.objects.get_or_create(key='demo_workspace', defaults={'name': 'Demo Workspace'})
        self.stdout.write(f"{'Created' if created else 'Using'} workspace: {ws.key}")

        # Clear existing tasks
        Task.objects.filter(workspace=ws).delete()

        # Create tasks with dependencies
        # Task graph: A -> B -> D, A -> C -> D (diamond)
        task_a = Task.objects.create(title='Task A (Start)', workspace=ws, status=Task.STATUS_PENDING)
        task_b = Task.objects.create(title='Task B (Depends on A)', workspace=ws, status=Task.STATUS_PENDING)
        task_c = Task.objects.create(title='Task C (Depends on A)', workspace=ws, status=Task.STATUS_PENDING)
        task_d = Task.objects.create(title='Task D (Depends on B and C)', workspace=ws, status=Task.STATUS_PENDING)

        # Set dependencies
        task_b.dependencies.add(task_a)
        task_c.dependencies.add(task_a)
        task_d.dependencies.add(task_b, task_c)

        self.stdout.write(f"Created tasks: {task_a.id}, {task_b.id}, {task_c.id}, {task_d.id}")

        # Demonstrate topological sort
        tasks = list(Task.objects.filter(workspace=ws))
        try:
            ordered = topological_sort(tasks)
            self.stdout.write(f"Topological order: {[t.id for t in ordered]}")
        except ValueError as e:
            self.stdout.write(self.style.ERROR(f"Cycle detected: {e}"))
            return

        # Enqueue execution (skip if Redis/Celery not available)
        try:
            for task in ordered:
                execute_task.delay(task.id)
                self.stdout.write(f"Enqueued task {task.id}: {task.title}")
            self.stdout.write(self.style.SUCCESS('Demo setup complete. Check Celery worker logs for execution.'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Celery/Redis not available: {str(e)}'))
            self.stdout.write(self.style.SUCCESS('Demo setup complete (without Celery execution). Tasks created in database.'))
