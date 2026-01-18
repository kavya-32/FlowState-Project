from django.core.management.base import BaseCommand
from django.utils import timezone
from tasks.models import Tenant, Task
from tasks.utils import topological_sort
from tasks.tasks import execute_task
from datetime import timedelta


class Command(BaseCommand):
    help = 'Seed demo workspace and tasks to demonstrate DAG + Celery execution'

    def handle(self, *args, **options):
        # Create multiple workspaces
        workspaces = [
            ('demo_workspace', 'Demo Workspace'),
            ('project_alpha', 'Project Alpha'),
            ('project_beta', 'Project Beta'),
        ]
        
        for ws_key, ws_name in workspaces:
            ws, created = Tenant.objects.get_or_create(key=ws_key, defaults={'name': ws_name})
            self.stdout.write(f"{'Created' if created else 'Using'} workspace: {ws.key}")
            
            # Clear existing tasks for this workspace
            Task.objects.filter(workspace=ws).delete()
            
            # Create demo tasks with different statuses and descriptions
            if ws_key == 'demo_workspace':
                self._seed_demo_workspace(ws)
            elif ws_key == 'project_alpha':
                self._seed_project_alpha(ws)
            elif ws_key == 'project_beta':
                self._seed_project_beta(ws)

    def _seed_demo_workspace(self, ws):
        """Seed demo_workspace with pending tasks (DAG structure)"""
        # Task graph: A -> B -> D, A -> C -> D (diamond)
        task_a = Task.objects.create(
            title='Task A (Start)',
            description='Initial task that kicks off the workflow',
            workspace=ws,
            status=Task.STATUS_PENDING
        )
        task_b = Task.objects.create(
            title='Task B (Data Processing)',
            description='Process data from Task A',
            workspace=ws,
            status=Task.STATUS_PENDING
        )
        task_c = Task.objects.create(
            title='Task C (Validation)',
            description='Validate results from Task A',
            workspace=ws,
            status=Task.STATUS_PENDING
        )
        task_d = Task.objects.create(
            title='Task D (Finalize)',
            description='Combine results from B and C',
            workspace=ws,
            status=Task.STATUS_PENDING
        )
        
        # Set dependencies
        task_b.dependencies.add(task_a)
        task_c.dependencies.add(task_a)
        task_d.dependencies.add(task_b, task_c)
        
        self.stdout.write(f"✓ Created DAG tasks: {task_a.id}, {task_b.id}, {task_c.id}, {task_d.id}")

    def _seed_project_alpha(self, ws):
        """Seed project_alpha with mixed status tasks"""
        # Create tasks with different statuses
        now = timezone.now()
        
        # Done tasks
        task1 = Task.objects.create(
            title='Deploy to Staging',
            description='Deploy application to staging environment',
            workspace=ws,
            status=Task.STATUS_DONE,
            started_at=now - timedelta(hours=2),
            completed_at=now - timedelta(hours=1.5)
        )
        
        task2 = Task.objects.create(
            title='Run Tests',
            description='Execute all unit and integration tests',
            workspace=ws,
            status=Task.STATUS_DONE,
            started_at=now - timedelta(hours=1.5),
            completed_at=now - timedelta(hours=1)
        )
        
        # Running task
        task3 = Task.objects.create(
            title='Load Testing',
            description='Perform load and stress testing',
            workspace=ws,
            status=Task.STATUS_RUNNING,
            started_at=now - timedelta(minutes=30)
        )
        
        # Pending tasks
        task4 = Task.objects.create(
            title='Deploy to Production',
            description='Deploy to production after approval',
            workspace=ws,
            status=Task.STATUS_PENDING
        )
        
        task5 = Task.objects.create(
            title='Smoke Tests',
            description='Run smoke tests on production',
            workspace=ws,
            status=Task.STATUS_PENDING
        )
        
        # Set dependencies
        task3.dependencies.add(task2)
        task4.dependencies.add(task3)
        task5.dependencies.add(task4)
        
        self.stdout.write(f"✓ Created Project Alpha with mixed statuses: {task1.id}-{task5.id}")

    def _seed_project_beta(self, ws):
        """Seed project_beta with various tasks"""
        now = timezone.now()
        
        # Failed task
        task_fail = Task.objects.create(
            title='Data Migration',
            description='Migrate legacy database to new schema',
            workspace=ws,
            status=Task.STATUS_FAILED,
            started_at=now - timedelta(hours=3),
            completed_at=now - timedelta(hours=2.5)
        )
        
        # Retry task
        task_retry = Task.objects.create(
            title='Data Migration (Retry)',
            description='Re-attempt database migration with fixes',
            workspace=ws,
            status=Task.STATUS_PENDING
        )
        task_retry.dependencies.add(task_fail)
        
        # Pending tasks
        task_email = Task.objects.create(
            title='Send Notifications',
            description='Notify users of system changes',
            workspace=ws,
            status=Task.STATUS_PENDING
        )
        
        task_docs = Task.objects.create(
            title='Update Documentation',
            description='Update API docs and user guides',
            workspace=ws,
            status=Task.STATUS_PENDING
        )
        
        self.stdout.write(f"✓ Created Project Beta with failed/retry tasks: {task_fail.id}-{task_docs.id}")

        # Log completion
        self.stdout.write(self.style.SUCCESS('\n✓ All demo data seeded successfully!'))
        self.stdout.write('Filters available:')
        self.stdout.write('  - workspace: demo_workspace, project_alpha, project_beta')
        self.stdout.write('  - status: pending, running, done, failed')
        self.stdout.write('  - search: by title or description')
