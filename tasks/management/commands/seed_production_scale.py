"""
Seed massive production-scale data to demonstrate real-world scale.
Creates 10+ workspaces, 300+ tasks, 2000+ execution records.
Usage: python manage.py seed_production_scale
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from tasks.models import Tenant, Task, TaskResult


class Command(BaseCommand):
    help = 'Seed production-scale data for realistic project demonstration'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('🚀 SEEDING PRODUCTION-SCALE DATA'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

        # Create additional enterprise workspaces
        self.create_enterprise_workspaces()
        
        # Expand all workspaces with more tasks
        self.expand_all_workspaces()
        
        # Add massive execution history
        self.add_massive_execution_history()

        self.print_comprehensive_summary()

    def create_enterprise_workspaces(self):
        """Create 5 additional enterprise-grade workspaces"""
        self.stdout.write('🏢 Creating enterprise workspaces...\n')
        
        enterprise_workspaces = [
            {
                'key': 'financial_reporting',
                'name': 'Financial Reporting System',
                'description': 'End-of-quarter financial consolidation and reporting'
            },
            {
                'key': 'supply_chain',
                'name': 'Supply Chain Management',
                'description': 'Inventory, procurement, and logistics orchestration'
            },
            {
                'key': 'customer_analytics',
                'name': 'Customer Analytics Pipeline',
                'description': 'Real-time customer behavior analysis and segmentation'
            },
            {
                'key': 'fraud_detection',
                'name': 'Fraud Detection System',
                'description': 'Real-time transaction monitoring and anomaly detection'
            },
            {
                'key': 'recommendation_engine',
                'name': 'Recommendation Engine',
                'description': 'Personalized product recommendation computation'
            }
        ]
        
        for ws_data in enterprise_workspaces:
            ws, created = Tenant.objects.get_or_create(
                key=ws_data['key'],
                defaults={'name': ws_data['name']}
            )
            
            if created:
                self.stdout.write(f'  ✓ {ws_data["name"]}')
                # Add 8-12 tasks per new workspace
                for i in range(random.randint(8, 12)):
                    Task.objects.create(
                        title=f'{ws_data["name"]} - Task {i+1}',
                        description=ws_data['description'],
                        workspace=ws,
                        status=random.choices(
                            [Task.STATUS_PENDING, Task.STATUS_DONE, Task.STATUS_RUNNING, Task.STATUS_FAILED],
                            weights=[45, 40, 10, 5],
                            k=1
                        )[0],
                        started_at=timezone.now() - timedelta(days=random.randint(1, 30)) if i % 2 == 0 else None,
                        completed_at=timezone.now() - timedelta(days=random.randint(0, 25)) if i % 3 == 0 else None
                    )
        
        self.stdout.write()

    def expand_all_workspaces(self):
        """Add 30+ more tasks to each existing workspace"""
        self.stdout.write('📈 Expanding all workspaces with additional tasks...\n')
        
        workspaces = Tenant.objects.all()
        total_added = 0
        
        for ws in workspaces:
            # Add 25-35 more tasks per workspace
            num_tasks = random.randint(25, 35)
            
            for i in range(num_tasks):
                status = random.choices(
                    [Task.STATUS_PENDING, Task.STATUS_DONE, Task.STATUS_RUNNING, Task.STATUS_FAILED],
                    weights=[40, 45, 10, 5],
                    k=1
                )[0]
                
                task = Task.objects.create(
                    title=f'{ws.name} - Extended Task {i+1}',
                    description=f'Production task for {ws.name} pipeline',
                    workspace=ws,
                    status=status,
                    started_at=timezone.now() - timedelta(days=random.randint(1, 60)) if status != Task.STATUS_PENDING else None,
                    completed_at=timezone.now() - timedelta(days=random.randint(0, 55)) if status in [Task.STATUS_DONE, Task.STATUS_FAILED] else None
                )
                
                # Link some tasks as dependencies
                if ws.tasks.count() > 2 and random.random() > 0.55:
                    existing = list(ws.tasks.exclude(id=task.id))[:5]
                    if existing:
                        task.dependencies.add(random.choice(existing))
                
                total_added += 1
        
        self.stdout.write(f'  ✓ Added {total_added} expanded tasks\n')

    def add_massive_execution_history(self):
        """Add 1500+ execution records"""
        self.stdout.write('⏱️  Seeding massive execution history...\n')
        
        all_tasks = Task.objects.all()
        total_created = 0
        success_count = 0
        failure_count = 0
        
        # Create 5-10 execution records per task (realistic retry patterns)
        for task in all_tasks:
            num_executions = random.randint(5, 10)
            
            for attempt in range(num_executions):
                # Realistic success distribution: 80% success, 20% failure
                success = random.random() > 0.20
                
                # Generate realistic timestamps (last 90 days)
                days_back = random.randint(1, 90)
                hours_back = random.randint(0, 23)
                started = timezone.now() - timedelta(days=days_back, hours=hours_back, minutes=random.randint(0, 59))
                
                # Execution duration: 5 seconds to 1 hour
                duration_seconds = random.randint(5, 3600)
                completed = started + timedelta(seconds=duration_seconds)
                
                error_msg = ''
                if not success:
                    errors = [
                        'Timeout: Operation exceeded 30s limit',
                        'API rate limit: 429 Too Many Requests',
                        'Database lock: Unable to acquire lock',
                        'Service unavailable: Temporary service outage',
                        'File not found: S3 bucket error',
                        'Permission denied: IAM policy violation',
                        'Memory error: Insufficient heap space',
                        'Network error: Connection reset',
                        'Validation error: Invalid input format',
                        'External API error: Third-party service down'
                    ]
                    error_msg = random.choice(errors)
                    failure_count += 1
                else:
                    success_count += 1
                
                TaskResult.objects.create(
                    task=task,
                    status='success' if success else 'failure',
                    output=f'Attempt {attempt + 1}: {"SUCCESS" if success else "FAILED"}',
                    error_message=error_msg,
                    started_at=started,
                    completed_at=completed if success else None,
                    retry_count=attempt
                )
                total_created += 1
        
        self.stdout.write(f'  ✓ Created {total_created} execution records')
        self.stdout.write(f'    - {success_count} successful ({success_count/total_created*100:.1f}%)')
        self.stdout.write(f'    - {failure_count} failed ({failure_count/total_created*100:.1f}%)\n')

    def print_comprehensive_summary(self):
        """Print comprehensive production statistics"""
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('📊 PRODUCTION-SCALE PROJECT STATISTICS'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        
        # Overall stats
        total_workspaces = Tenant.objects.count()
        total_tasks = Task.objects.count()
        total_results = TaskResult.objects.count()
        
        success_results = TaskResult.objects.filter(status='success').count()
        failure_results = TaskResult.objects.filter(status='failure').count()
        
        # Calculate comprehensive metrics
        all_results = TaskResult.objects.all()
        total_execution_seconds = sum(
            (r.completed_at - r.started_at).total_seconds() 
            for r in all_results 
            if r.completed_at and r.started_at
        )
        
        all_tasks = Task.objects.all()
        task_duration_seconds = sum(
            (t.completed_at - t.started_at).total_seconds()
            for t in all_tasks
            if t.completed_at and t.started_at
        )
        
        total_duration = total_execution_seconds + task_duration_seconds
        
        # Print comprehensive metrics
        self.stdout.write(self.style.SUCCESS('📈 SCALE METRICS'))
        self.stdout.write(f'  Workspaces ........... {total_workspaces}')
        self.stdout.write(f'  Total Tasks ......... {total_tasks}')
        self.stdout.write(f'  Execution Records ... {total_results}')
        self.stdout.write()
        
        # Task distribution
        pending = Task.objects.filter(status=Task.STATUS_PENDING).count()
        running = Task.objects.filter(status=Task.STATUS_RUNNING).count()
        done = Task.objects.filter(status=Task.STATUS_DONE).count()
        failed = Task.objects.filter(status=Task.STATUS_FAILED).count()
        
        self.stdout.write(self.style.SUCCESS('📊 TASK STATUS DISTRIBUTION'))
        self.stdout.write(f'  Pending ............ {pending:4} ({pending/total_tasks*100:5.1f}%)')
        self.stdout.write(f'  Running ............ {running:4} ({running/total_tasks*100:5.1f}%)')
        self.stdout.write(f'  Done ............... {done:4} ({done/total_tasks*100:5.1f}%)')
        self.stdout.write(f'  Failed ............ {failed:4} ({failed/total_tasks*100:5.1f}%)')
        self.stdout.write()
        
        # Execution results
        success_rate = (success_results / total_results * 100) if total_results > 0 else 0
        
        self.stdout.write(self.style.SUCCESS('✅ EXECUTION RESULTS'))
        self.stdout.write(f'  Successful ......... {success_results:4} ({success_rate:5.1f}%)')
        self.stdout.write(f'  Failed ............. {failure_results:4} ({100-success_rate:5.1f}%)')
        self.stdout.write(f'  Total Executions ... {total_results}')
        self.stdout.write()
        
        # Duration metrics
        self.stdout.write(self.style.SUCCESS('⏱️  PERFORMANCE METRICS'))
        self.stdout.write(f'  Total Duration ..... {self._format_duration(int(total_duration))}')
        self.stdout.write(f'  Execution Time ..... {self._format_duration(int(total_execution_seconds))}')
        self.stdout.write(f'  Task Time .......... {self._format_duration(int(task_duration_seconds))}')
        self.stdout.write(f'  Avg Task Time ...... {self._format_duration(int(task_duration_seconds / max(total_tasks, 1)))}')
        self.stdout.write()
        
        # Workspace breakdown
        self.stdout.write(self.style.SUCCESS('🏢 WORKSPACE BREAKDOWN'))
        workspaces_list = sorted(
            Tenant.objects.all(),
            key=lambda x: x.tasks.count(),
            reverse=True
        )
        for ws in workspaces_list:
            tasks_count = ws.tasks.count()
            results_count = TaskResult.objects.filter(task__workspace=ws).count()
            success_in_ws = TaskResult.objects.filter(task__workspace=ws, status='success').count()
            ws_success_rate = (success_in_ws / results_count * 100) if results_count > 0 else 0
            
            self.stdout.write(f'  {ws.name}')
            self.stdout.write(f'    Tasks: {tasks_count:3} | Executions: {results_count:4} | Success Rate: {ws_success_rate:5.1f}%')
        
        self.stdout.write()
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('✅ PRODUCTION-SCALE DATA SEEDING COMPLETE'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        
        self.stdout.write('🎯 Your FlowState Dashboard Now Includes:')
        self.stdout.write(f'   • {total_workspaces} production workspaces')
        self.stdout.write(f'   • {total_tasks} real-world tasks')
        self.stdout.write(f'   • {total_results} execution records')
        self.stdout.write(f'   • {success_rate:.1f}% success rate')
        self.stdout.write(f'   • {self._format_duration(int(total_duration))} total tracked time\n')
        
        self.stdout.write('🚀 Ready for:')
        self.stdout.write('   • Production-level testing')
        self.stdout.write('   • Performance analysis and optimization')
        self.stdout.write('   • Real-world workflow demonstrations')
        self.stdout.write('   • Analytics and reporting')
        self.stdout.write('   • Scaling and load testing\n')

    def _format_duration(self, seconds):
        """Format seconds to human readable duration"""
        if seconds < 0:
            return '—'
        
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        parts = []
        if days > 0:
            parts.append(f'{days}d')
        if hours > 0:
            parts.append(f'{hours}h')
        if minutes > 0:
            parts.append(f'{minutes}m')
        if secs > 0 or not parts:
            parts.append(f'{secs}s')
        
        return ' '.join(parts[:3])
