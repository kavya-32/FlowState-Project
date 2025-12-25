from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from tasks.models import Tenant, Task, TaskResult


class Command(BaseCommand):
	help = 'Seed realistic production-like data with multiple workspaces and complex DAGs'

	def handle(self, *args, **options):
		self.stdout.write(self.style.SUCCESS('=== Seeding Realistic Data ===\n'))

		# ========== WORKSPACE 1: E-Commerce Order Processing ==========
		ws1, _ = Tenant.objects.get_or_create(
			key='ecommerce_pipeline',
			defaults={'name': 'E-Commerce Order Pipeline'}
		)
		Task.objects.filter(workspace=ws1).delete()
		self.stdout.write(f'Created workspace: {ws1.name}')

		# Order processing DAG: Validate → Payment → Inventory → Notification → Shipping
		order_validate = Task.objects.create(
			title='Validate Order',
			description='Check order for validity (items in stock, valid address)',
			workspace=ws1,
			status=Task.STATUS_DONE,
			started_at=timezone.now() - timedelta(minutes=5),
			completed_at=timezone.now() - timedelta(minutes=4)
		)

		order_payment = Task.objects.create(
			title='Process Payment',
			description='Charge customer credit card via Stripe',
			workspace=ws1,
			status=Task.STATUS_DONE,
			started_at=timezone.now() - timedelta(minutes=4),
			completed_at=timezone.now() - timedelta(minutes=3, seconds=30)
		)
		order_payment.dependencies.add(order_validate)

		order_inventory = Task.objects.create(
			title='Reserve Inventory',
			description='Lock inventory in warehouse management system',
			workspace=ws1,
			status=Task.STATUS_DONE,
			started_at=timezone.now() - timedelta(minutes=3, seconds=30),
			completed_at=timezone.now() - timedelta(minutes=3)
		)
		order_inventory.dependencies.add(order_payment)

		order_notify = Task.objects.create(
			title='Send Confirmation Email',
			description='Email customer with order details and tracking link',
			workspace=ws1,
			status=Task.STATUS_PENDING
		)
		order_notify.dependencies.add(order_inventory)

		order_ship = Task.objects.create(
			title='Generate Shipping Label',
			description='Create FedEx label and send to warehouse',
			workspace=ws1,
			status=Task.STATUS_PENDING
		)
		order_ship.dependencies.add(order_inventory)

		order_warehouse = Task.objects.create(
			title='Notify Warehouse',
			description='Send picking list to warehouse system',
			workspace=ws1,
			status=Task.STATUS_PENDING
		)
		order_warehouse.dependencies.add(order_ship)

		# Add result records for completed tasks
		TaskResult.objects.create(
			task=order_validate,
			status=TaskResult.STATUS_SUCCESS,
			output='Order validated: 1 item in stock, address verified',
			completed_at=timezone.now() - timedelta(minutes=4)
		)
		TaskResult.objects.create(
			task=order_payment,
			status=TaskResult.STATUS_SUCCESS,
			output='Payment processed: $149.99 charged to card ending in 4242',
			completed_at=timezone.now() - timedelta(minutes=3, seconds=30)
		)
		TaskResult.objects.create(
			task=order_inventory,
			status=TaskResult.STATUS_SUCCESS,
			output='Inventory reserved: SKU-12345 (qty: 1)',
			completed_at=timezone.now() - timedelta(minutes=3)
		)

		self.stdout.write(f'  ✓ E-Commerce pipeline: 6 tasks (3 completed, 3 pending)')

		# ========== WORKSPACE 2: Data Pipeline / ETL ==========
		ws2, _ = Tenant.objects.get_or_create(
			key='data_pipeline',
			defaults={'name': 'Data ETL Pipeline'}
		)
		Task.objects.filter(workspace=ws2).delete()
		self.stdout.write(f'Created workspace: {ws2.name}')

		# ETL DAG: Extract (parallel) → Validate (parallel) → Transform → Load → Notify
		extract_db = Task.objects.create(
			title='Extract Data from PostgreSQL',
			description='Query production database for customer records',
			workspace=ws2,
			status=Task.STATUS_DONE,
			started_at=timezone.now() - timedelta(hours=1),
			completed_at=timezone.now() - timedelta(hours=1, minutes=5)
		)

		extract_api = Task.objects.create(
			title='Extract Data from API',
			description='Fetch data from third-party REST API',
			workspace=ws2,
			status=Task.STATUS_DONE,
			started_at=timezone.now() - timedelta(hours=1),
			completed_at=timezone.now() - timedelta(hours=1, minutes=3)
		)

		extract_csv = Task.objects.create(
			title='Extract Data from CSV',
			description='Download and parse CSV files from S3',
			workspace=ws2,
			status=Task.STATUS_FAILED,
			started_at=timezone.now() - timedelta(hours=1),
			completed_at=timezone.now() - timedelta(hours=1, minutes=2)
		)

		validate_db = Task.objects.create(
			title='Validate PostgreSQL Extract',
			description='Check schema, data types, null values',
			workspace=ws2,
			status=Task.STATUS_DONE,
			started_at=timezone.now() - timedelta(hours=1, minutes=5),
			completed_at=timezone.now() - timedelta(hours=1, minutes=4)
		)
		validate_db.dependencies.add(extract_db)

		validate_api = Task.objects.create(
			title='Validate API Extract',
			description='Verify API response format and completeness',
			workspace=ws2,
			status=Task.STATUS_DONE,
			started_at=timezone.now() - timedelta(hours=1, minutes=3),
			completed_at=timezone.now() - timedelta(hours=1, minutes=1)
		)
		validate_api.dependencies.add(extract_api)

		transform = Task.objects.create(
			title='Transform & Merge Data',
			description='Normalize formats and merge all sources',
			workspace=ws2,
			status=Task.STATUS_PENDING
		)
		transform.dependencies.add(validate_db, validate_api)

		load_warehouse = Task.objects.create(
			title='Load to Data Warehouse',
			description='Insert into Redshift analytics cluster',
			workspace=ws2,
			status=Task.STATUS_PENDING
		)
		load_warehouse.dependencies.add(transform)

		notify = Task.objects.create(
			title='Send Completion Alert',
			description='Slack notification to analytics team',
			workspace=ws2,
			status=Task.STATUS_PENDING
		)
		notify.dependencies.add(load_warehouse)

		# Add failure result
		TaskResult.objects.create(
			task=extract_csv,
			status=TaskResult.STATUS_FAILURE,
			error_message='ConnectionError: S3 bucket not accessible (credentials expired)',
			retry_count=2,
			completed_at=timezone.now() - timedelta(hours=1, minutes=2)
		)
		TaskResult.objects.create(
			task=extract_db,
			status=TaskResult.STATUS_SUCCESS,
			output='Extracted 50,000 records in 5 minutes',
			completed_at=timezone.now() - timedelta(hours=1, minutes=5)
		)
		TaskResult.objects.create(
			task=extract_api,
			status=TaskResult.STATUS_SUCCESS,
			output='Fetched 25,000 API records',
			completed_at=timezone.now() - timedelta(hours=1, minutes=3)
		)

		self.stdout.write(f'  ✓ ETL pipeline: 8 tasks (1 failed, 2 completed, rest pending)')

		# ========== WORKSPACE 3: DevOps Deployment ==========
		ws3, _ = Tenant.objects.get_or_create(
			key='devops_deploy',
			defaults={'name': 'DevOps Deployment Pipeline'}
		)
		Task.objects.filter(workspace=ws3).delete()
		self.stdout.write(f'Created workspace: {ws3.name}')

		# CI/CD DAG: Test (parallel) → Build → Push Registry → Deploy Staging → Deploy Prod → Smoke Test
		unit_test = Task.objects.create(
			title='Unit Tests',
			description='Run pytest suite (coverage > 80%)',
			workspace=ws3,
			status=Task.STATUS_RUNNING,
			started_at=timezone.now() - timedelta(minutes=2)
		)

		integration_test = Task.objects.create(
			title='Integration Tests',
			description='Run Docker Compose integration suite',
			workspace=ws3,
			status=Task.STATUS_PENDING
		)

		lint = Task.objects.create(
			title='Code Linting',
			description='flake8, black, mypy checks',
			workspace=ws3,
			status=Task.STATUS_DONE,
			started_at=timezone.now() - timedelta(minutes=5),
			completed_at=timezone.now() - timedelta(minutes=4)
		)

		build = Task.objects.create(
			title='Build Docker Image',
			description='Build and tag Docker image',
			workspace=ws3,
			status=Task.STATUS_PENDING
		)
		build.dependencies.add(unit_test, integration_test, lint)

		push = Task.objects.create(
			title='Push to ECR',
			description='Push image to AWS ECR registry',
			workspace=ws3,
			status=Task.STATUS_PENDING
		)
		push.dependencies.add(build)

		staging_deploy = Task.objects.create(
			title='Deploy to Staging',
			description='Deploy to staging cluster (k8s)',
			workspace=ws3,
			status=Task.STATUS_PENDING
		)
		staging_deploy.dependencies.add(push)

		prod_deploy = Task.objects.create(
			title='Deploy to Production',
			description='Blue-green deploy to prod cluster',
			workspace=ws3,
			status=Task.STATUS_PENDING
		)
		prod_deploy.dependencies.add(staging_deploy)

		smoke_test = Task.objects.create(
			title='Run Smoke Tests',
			description='Verify critical endpoints respond (prod)',
			workspace=ws3,
			status=Task.STATUS_PENDING
		)
		smoke_test.dependencies.add(prod_deploy)

		TaskResult.objects.create(
			task=lint,
			status=TaskResult.STATUS_SUCCESS,
			output='All files passed linting (0 warnings)',
			completed_at=timezone.now() - timedelta(minutes=4)
		)

		self.stdout.write(f'  ✓ CI/CD pipeline: 8 tasks (1 running, 1 done, 6 pending)')

		# ========== WORKSPACE 4: Report Generation ==========
		ws4, _ = Tenant.objects.get_or_create(
			key='reporting_system',
			defaults={'name': 'Monthly Reporting System'}
		)
		Task.objects.filter(workspace=ws4).delete()
		self.stdout.write(f'Created workspace: {ws4.name}')

		# Report DAG: Collect Metrics → Generate Sections (parallel) → Compile → Send
		collect_metrics = Task.objects.create(
			title='Collect Metrics',
			description='Query metrics DB for monthly aggregates',
			workspace=ws4,
			status=Task.STATUS_DONE,
			started_at=timezone.now() - timedelta(days=1, hours=1),
			completed_at=timezone.now() - timedelta(days=1, minutes=30)
		)

		sales_report = Task.objects.create(
			title='Generate Sales Report',
			description='Create sales summary with charts',
			workspace=ws4,
			status=Task.STATUS_DONE,
			started_at=timezone.now() - timedelta(days=1, minutes=30),
			completed_at=timezone.now() - timedelta(days=1, minutes=20)
		)
		sales_report.dependencies.add(collect_metrics)

		expense_report = Task.objects.create(
			title='Generate Expense Report',
			description='Compile expense summaries',
			workspace=ws4,
			status=Task.STATUS_PENDING
		)
		expense_report.dependencies.add(collect_metrics)

		forecast_report = Task.objects.create(
			title='Generate Forecast',
			description='ML model-based revenue forecast',
			workspace=ws4,
			status=Task.STATUS_PENDING
		)
		forecast_report.dependencies.add(collect_metrics)

		compile_report = Task.objects.create(
			title='Compile Report PDF',
			description='Merge all sections into PDF',
			workspace=ws4,
			status=Task.STATUS_PENDING
		)
		compile_report.dependencies.add(sales_report, expense_report, forecast_report)

		send_email = Task.objects.create(
			title='Send Report via Email',
			description='Email PDF to stakeholders',
			workspace=ws4,
			status=Task.STATUS_PENDING
		)
		send_email.dependencies.add(compile_report)

		upload_s3 = Task.objects.create(
			title='Upload to Archive (S3)',
			description='Store report in S3 for long-term retention',
			workspace=ws4,
			status=Task.STATUS_PENDING
		)
		upload_s3.dependencies.add(compile_report)

		TaskResult.objects.create(
			task=collect_metrics,
			status=TaskResult.STATUS_SUCCESS,
			output='Collected 15,000 metric records from past 30 days',
			completed_at=timezone.now() - timedelta(days=1, minutes=30)
		)
		TaskResult.objects.create(
			task=sales_report,
			status=TaskResult.STATUS_SUCCESS,
			output='Sales report generated: $2.5M in revenue',
			completed_at=timezone.now() - timedelta(days=1, minutes=20)
		)

		self.stdout.write(f'  ✓ Reporting pipeline: 8 tasks (2 done, 6 pending)')

		# ========== Summary ==========
		self.stdout.write(self.style.SUCCESS('\n=== Seeding Complete ==='))
		self.stdout.write(f'Total workspaces: 4')
		self.stdout.write(f'Total tasks: {Task.objects.count()}')
		self.stdout.write(f'Total results: {TaskResult.objects.count()}')
		self.stdout.write('\nWorkspaces ready for testing:')
		self.stdout.write('  1. ecommerce_pipeline - E-Commerce Order Processing')
		self.stdout.write('  2. data_pipeline - Data ETL Pipeline')
		self.stdout.write('  3. devops_deploy - DevOps Deployment Pipeline')
		self.stdout.write('  4. reporting_system - Monthly Reporting System')
		self.stdout.write('\nVisit: http://localhost:8000 to see dashboard')
