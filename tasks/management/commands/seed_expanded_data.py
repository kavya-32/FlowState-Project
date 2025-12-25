"""
Expand existing database with additional realistic data.
Creates more tasks, workspaces, and execution history.
Usage: python manage.py seed_expanded_data
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from tasks.models import Tenant, Task, TaskResult


class Command(BaseCommand):
    help = 'Seed expanded realistic data for testing and demo purposes'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== SEEDING EXPANDED DATA ===\n'))

        # ============ NEW WORKSPACES ============
        self.create_new_workspaces()

        # ============ EXPAND EXISTING WORKSPACES ============
        self.expand_existing_workspaces()

        # ============ ADD MORE EXECUTION HISTORY ============
        self.add_execution_history()

        self.stdout.write(self.style.SUCCESS('\n=== EXPANSION COMPLETE ===\n'))
        self.print_summary()

    def create_new_workspaces(self):
        """Create 3 additional production workspaces"""
        self.stdout.write('📁 Creating new workspaces...\n')

        # ========== MACHINE LEARNING PIPELINE ==========
        ws_ml, created = Tenant.objects.get_or_create(
            key='ml_training_pipeline',
            defaults={'name': 'ML Model Training Pipeline'}
        )
        if created:
            self.stdout.write(f'  ✓ ML Training Pipeline created')

            # Data preparation phase
            prepare_data = Task.objects.create(
                title='Prepare Training Data',
                description='Load, clean, and normalize raw data from data warehouse',
                workspace=ws_ml,
                status=Task.STATUS_DONE,
                started_at=timezone.now() - timedelta(hours=6),
                completed_at=timezone.now() - timedelta(hours=5, minutes=30)
            )

            split_data = Task.objects.create(
                title='Split Train/Test Sets',
                description='Partition data into 80/20 train/test split with stratification',
                workspace=ws_ml,
                status=Task.STATUS_DONE,
                started_at=timezone.now() - timedelta(hours=5, minutes=30),
                completed_at=timezone.now() - timedelta(hours=5, minutes=15)
            )
            split_data.dependencies.add(prepare_data)

            # Feature engineering
            feature_eng = Task.objects.create(
                title='Feature Engineering',
                description='Generate new features, handle missing values, encode categoricals',
                workspace=ws_ml,
                status=Task.STATUS_DONE,
                started_at=timezone.now() - timedelta(hours=5, minutes=15),
                completed_at=timezone.now() - timedelta(hours=4, minutes=45)
            )
            feature_eng.dependencies.add(split_data)

            # Parallel model training
            model_xgb = Task.objects.create(
                title='Train XGBoost Model',
                description='Train XGBoost classifier with hyperparameter tuning',
                workspace=ws_ml,
                status=Task.STATUS_DONE,
                started_at=timezone.now() - timedelta(hours=4, minutes=45),
                completed_at=timezone.now() - timedelta(hours=3, minutes=30)
            )
            model_xgb.dependencies.add(feature_eng)

            model_rf = Task.objects.create(
                title='Train Random Forest Model',
                description='Train Random Forest classifier with cross-validation',
                workspace=ws_ml,
                status=Task.STATUS_DONE,
                started_at=timezone.now() - timedelta(hours=4, minutes=45),
                completed_at=timezone.now() - timedelta(hours=3, minutes=15)
            )
            model_rf.dependencies.add(feature_eng)

            model_lr = Task.objects.create(
                title='Train Logistic Regression',
                description='Train baseline logistic regression model',
                workspace=ws_ml,
                status=Task.STATUS_RUNNING,
                started_at=timezone.now() - timedelta(hours=3, minutes=15)
            )
            model_lr.dependencies.add(feature_eng)

            # Model evaluation
            eval_models = Task.objects.create(
                title='Evaluate Models',
                description='Compare model performance (AUC, F1, precision, recall)',
                workspace=ws_ml,
                status=Task.STATUS_PENDING
            )
            eval_models.dependencies.add(model_xgb, model_rf, model_lr)

            # Hyperparameter tuning
            hyperopt = Task.objects.create(
                title='Hyperparameter Optimization',
                description='Use Bayesian optimization to tune best model',
                workspace=ws_ml,
                status=Task.STATUS_PENDING
            )
            hyperopt.dependencies.add(eval_models)

            # Final evaluation and export
            final_eval = Task.objects.create(
                title='Final Evaluation on Test Set',
                description='Evaluate selected model on held-out test data',
                workspace=ws_ml,
                status=Task.STATUS_PENDING
            )
            final_eval.dependencies.add(hyperopt)

            export_model = Task.objects.create(
                title='Export Model to Production',
                description='Serialize and push model to model registry',
                workspace=ws_ml,
                status=Task.STATUS_PENDING
            )
            export_model.dependencies.add(final_eval)

            self.stdout.write(f'     └─ 9 tasks created\n')

        # ========== MOBILE APP RELEASE ==========
        ws_mobile, created = Tenant.objects.get_or_create(
            key='mobile_app_release',
            defaults={'name': 'Mobile App Release Pipeline'}
        )
        if created:
            self.stdout.write(f'  ✓ Mobile App Release created')

            # Development phase
            dev_complete = Task.objects.create(
                title='Development Freeze',
                description='Lock main branch, all features must be complete',
                workspace=ws_mobile,
                status=Task.STATUS_DONE,
                started_at=timezone.now() - timedelta(days=1),
                completed_at=timezone.now() - timedelta(days=1, hours=12)
            )

            # QA testing
            qa_ios = Task.objects.create(
                title='QA Test iOS Build',
                description='Functional and regression testing on iPhone/iPad',
                workspace=ws_mobile,
                status=Task.STATUS_DONE,
                started_at=timezone.now() - timedelta(days=1, hours=12),
                completed_at=timezone.now() - timedelta(days=1, hours=6)
            )
            qa_ios.dependencies.add(dev_complete)

            qa_android = Task.objects.create(
                title='QA Test Android Build',
                description='Testing on Pixel/Samsung devices, Android 10+',
                workspace=ws_mobile,
                status=Task.STATUS_DONE,
                started_at=timezone.now() - timedelta(days=1, hours=12),
                completed_at=timezone.now() - timedelta(days=1, hours=5)
            )
            qa_android.dependencies.add(dev_complete)

            # Bug fixes
            fix_bugs = Task.objects.create(
                title='Fix Critical Bugs',
                description='Address and verify fixes for blocker issues',
                workspace=ws_mobile,
                status=Task.STATUS_PENDING
            )
            fix_bugs.dependencies.add(qa_ios, qa_android)

            # Store submissions
            submit_ios = Task.objects.create(
                title='Submit to Apple App Store',
                description='Upload build and complete app review checklist',
                workspace=ws_mobile,
                status=Task.STATUS_PENDING
            )
            submit_ios.dependencies.add(fix_bugs)

            submit_android = Task.objects.create(
                title='Submit to Google Play Store',
                description='Upload APK and configure release notes',
                workspace=ws_mobile,
                status=Task.STATUS_PENDING
            )
            submit_android.dependencies.add(fix_bugs)

            # Store review monitoring
            monitor_review = Task.objects.create(
                title='Monitor Store Reviews',
                description='Track app store review progress and user feedback',
                workspace=ws_mobile,
                status=Task.STATUS_PENDING
            )
            monitor_review.dependencies.add(submit_ios, submit_android)

            self.stdout.write(f'     └─ 7 tasks created\n')

        # ========== MARKETING CAMPAIGN ==========
        ws_marketing, created = Tenant.objects.get_or_create(
            key='marketing_campaign',
            defaults={'name': 'Product Launch Campaign'}
        )
        if created:
            self.stdout.write(f'  ✓ Product Launch Campaign created')

            # Parallel preparation
            social_prep = Task.objects.create(
                title='Prepare Social Media Content',
                description='Create graphics, videos, copy for all platforms',
                workspace=ws_marketing,
                status=Task.STATUS_DONE,
                started_at=timezone.now() - timedelta(days=2),
                completed_at=timezone.now() - timedelta(days=1, hours=12)
            )

            email_prep = Task.objects.create(
                title='Design Email Campaign',
                description='Create email templates and segment audience',
                workspace=ws_marketing,
                status=Task.STATUS_DONE,
                started_at=timezone.now() - timedelta(days=2),
                completed_at=timezone.now() - timedelta(days=1, hours=14)
            )

            press_release = Task.objects.create(
                title='Write Press Release',
                description='Craft announcement for tech media outlets',
                workspace=ws_marketing,
                status=Task.STATUS_DONE,
                started_at=timezone.now() - timedelta(days=2),
                completed_at=timezone.now() - timedelta(days=1, hours=16)
            )

            # Influencer outreach
            influencer_reach = Task.objects.create(
                title='Influencer Outreach',
                description='Contact and secure 15+ micro/macro influencers',
                workspace=ws_marketing,
                status=Task.STATUS_RUNNING,
                started_at=timezone.now() - timedelta(hours=6)
            )

            # Ad campaign setup
            ads_setup = Task.objects.create(
                title='Setup Ad Campaigns',
                description='Configure Facebook, Google, LinkedIn ad campaigns',
                workspace=ws_marketing,
                status=Task.STATUS_PENDING
            )
            ads_setup.dependencies.add(social_prep)

            # Execution
            launch_social = Task.objects.create(
                title='Launch Social Posts',
                description='Post across Twitter, LinkedIn, Instagram, TikTok',
                workspace=ws_marketing,
                status=Task.STATUS_PENDING
            )
            launch_social.dependencies.add(social_prep)

            send_emails = Task.objects.create(
                title='Send Email Campaign',
                description='Send campaign to 50K+ subscriber list',
                workspace=ws_marketing,
                status=Task.STATUS_PENDING
            )
            send_emails.dependencies.add(email_prep)

            publish_pr = Task.objects.create(
                title='Publish Press Release',
                description='Distribute via PR Newswire to media',
                workspace=ws_marketing,
                status=Task.STATUS_PENDING
            )
            publish_pr.dependencies.add(press_release)

            # Monitoring
            monitor_metrics = Task.objects.create(
                title='Monitor Campaign Metrics',
                description='Track engagement, clicks, conversions, ROI',
                workspace=ws_marketing,
                status=Task.STATUS_PENDING
            )
            monitor_metrics.dependencies.add(launch_social, send_emails, ads_setup)

            self.stdout.write(f'     └─ 9 tasks created\n')

    def expand_existing_workspaces(self):
        """Add more tasks to existing workspaces"""
        self.stdout.write('\n📈 Expanding existing workspaces...\n')

        # Expand E-Commerce with customer support workflow
        try:
            ws_ecom = Tenant.objects.get(key='ecommerce_pipeline')
            if ws_ecom.tasks.count() < 12:
                self.stdout.write(f'  ✓ E-Commerce expanded')

                # Add customer support tasks
                notify_support = Task.objects.create(
                    title='Notify Support Team',
                    description='Alert support team of order for proactive outreach',
                    workspace=ws_ecom,
                    status=Task.STATUS_PENDING
                )

                upsell = Task.objects.create(
                    title='Trigger Upsell Campaign',
                    description='Send personalized product recommendations',
                    workspace=ws_ecom,
                    status=Task.STATUS_PENDING
                )

                track_delivery = Task.objects.create(
                    title='Setup Delivery Tracking',
                    description='Enable customer to track package in real-time',
                    workspace=ws_ecom,
                    status=Task.STATUS_PENDING
                )

                collect_feedback = Task.objects.create(
                    title='Schedule Feedback Survey',
                    description='Queue survey for 48 hours after delivery',
                    workspace=ws_ecom,
                    status=Task.STATUS_PENDING
                )

                self.stdout.write(f'     └─ 4 additional tasks added\n')
        except Tenant.DoesNotExist:
            pass

        # Expand Data Pipeline with data quality checks
        try:
            ws_data = Tenant.objects.get(key='data_pipeline')
            if ws_data.tasks.count() < 16:
                self.stdout.write(f'  ✓ Data Pipeline expanded')

                # Add quality assurance
                data_quality = Task.objects.create(
                    title='Data Quality Checks',
                    description='Validate data completeness, uniqueness, range',
                    workspace=ws_data,
                    status=Task.STATUS_PENDING
                )

                anomaly_detect = Task.objects.create(
                    title='Detect Anomalies',
                    description='Identify outliers and unusual patterns',
                    workspace=ws_data,
                    status=Task.STATUS_PENDING
                )

                reconcile = Task.objects.create(
                    title='Reconcile Sources',
                    description='Compare counts and values across all sources',
                    workspace=ws_data,
                    status=Task.STATUS_PENDING
                )

                archive = Task.objects.create(
                    title='Archive Raw Data',
                    description='Compress and backup extracted raw files to S3',
                    workspace=ws_data,
                    status=Task.STATUS_PENDING
                )

                self.stdout.write(f'     └─ 4 additional tasks added\n')
        except Tenant.DoesNotExist:
            pass

        # Expand DevOps with security scanning
        try:
            ws_devops = Tenant.objects.get(key='devops_deploy')
            if ws_devops.tasks.count() < 16:
                self.stdout.write(f'  ✓ DevOps Pipeline expanded')

                security_scan = Task.objects.create(
                    title='Security Scanning',
                    description='Run SAST/DAST and vulnerability scans',
                    workspace=ws_devops,
                    status=Task.STATUS_PENDING
                )

                perf_test = Task.objects.create(
                    title='Performance Testing',
                    description='Load testing and benchmark against baseline',
                    workspace=ws_devops,
                    status=Task.STATUS_PENDING
                )

                canary_deploy = Task.objects.create(
                    title='Canary Deployment',
                    description='Deploy to 10% of prod, monitor for issues',
                    workspace=ws_devops,
                    status=Task.STATUS_PENDING
                )

                rollback_ready = Task.objects.create(
                    title='Prepare Rollback Plan',
                    description='Document rollback procedure and pre-stage scripts',
                    workspace=ws_devops,
                    status=Task.STATUS_PENDING
                )

                self.stdout.write(f'     └─ 4 additional tasks added\n')
        except Tenant.DoesNotExist:
            pass

    def add_execution_history(self):
        """Add more TaskResult records (execution history)"""
        self.stdout.write('\n⏱️  Adding execution history...\n')

        tasks_for_results = Task.objects.filter(status=Task.STATUS_DONE)[:30]
        created_count = 0

        for task in tasks_for_results:
            if random.random() > 0.4:  # 60% of done tasks get results
                # Previous successful executions
                for attempt in range(random.randint(1, 3)):
                    success = random.random() > 0.15  # 85% success rate

                    if task.started_at and task.completed_at:
                        offset_hours = (attempt + 1) * random.randint(4, 24)
                        started = task.started_at - timedelta(hours=offset_hours)
                        completed = started + timedelta(
                            seconds=random.randint(30, 600)
                        )
                    else:
                        started = timezone.now() - timedelta(
                            hours=random.randint(2, 72)
                        )
                        completed = started + timedelta(
                            seconds=random.randint(30, 600)
                        )

                    error_msg = None
                    if not success:
                        errors = [
                            'Database connection timeout',
                            'API rate limit exceeded',
                            'Invalid input format',
                            'External service unavailable',
                            'File permission denied',
                            'Memory allocation failed'
                        ]
                        error_msg = random.choice(errors)
                    else:
                        error_msg = ''

                    result = TaskResult.objects.create(
                        task=task,
                        status='success' if success else 'failure',
                        output=f'Execution {"completed successfully" if success else "failed"}',
                        error_message=error_msg,
                        started_at=started,
                        completed_at=completed if success else None,
                        retry_count=attempt
                    )
                    created_count += 1

        self.stdout.write(f'  ✓ {created_count} execution records added\n')

    def print_summary(self):
        """Print summary of expanded data"""
        self.stdout.write(self.style.SUCCESS('\n📊 EXPANDED DATA SUMMARY\n'))

        workspaces = Tenant.objects.all()
        total_tasks = Task.objects.count()
        total_results = TaskResult.objects.count()

        self.stdout.write(f'Total Workspaces: {workspaces.count()}')
        self.stdout.write(f'Total Tasks: {total_tasks}')
        self.stdout.write(f'Total Executions: {total_results}\n')

        self.stdout.write('Workspaces:')
        for ws in workspaces.order_by('name'):
            tasks_count = ws.tasks.count()
            self.stdout.write(f'  • {ws.name}: {tasks_count} tasks')

        # Status distribution
        self.stdout.write('\nTask Status Distribution:')
        for status in [Task.STATUS_PENDING, Task.STATUS_RUNNING, Task.STATUS_DONE, Task.STATUS_FAILED]:
            count = Task.objects.filter(status=status).count()
            pct = (count / total_tasks * 100) if total_tasks > 0 else 0
            self.stdout.write(
                self.style.SUCCESS(
                    f'  {status:10} {count:3} ({pct:5.1f}%)'
                )
            )

        self.stdout.write('\n✅ Ready to test with expanded dataset!')
        self.stdout.write('  • Dashboard will show more tasks across more workspaces')
        self.stdout.write('  • Execute DAGs with larger task dependencies')
        self.stdout.write('  • More execution history for analytics\n')
