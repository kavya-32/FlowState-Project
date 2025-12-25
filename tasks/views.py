from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Prefetch, Q, Avg, Count
from django.views.generic import TemplateView

from .models import Tenant, Task, TaskResult
from .serializers import TenantSerializer, TaskSerializer, TaskResultSerializer
import json
from .utils import topological_sort
from .tasks import execute_task


class TenantViewSet(viewsets.ModelViewSet):
	queryset = Tenant.objects.all()
	serializer_class = TenantSerializer
	lookup_field = 'key'


class TaskViewSet(viewsets.ModelViewSet):
	serializer_class = TaskSerializer

	def get_queryset(self):
		workspace_key = self.request.query_params.get('workspace')
		status_filter = self.request.query_params.get('status')
		search = self.request.query_params.get('search')

		qs = Task.objects.prefetch_related('dependencies', 'results').all()

		if workspace_key:
			qs = qs.filter(workspace__key=workspace_key)
		if status_filter:
			qs = qs.filter(status=status_filter)
		if search:
			qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))

		return qs

	@action(detail=False, methods=['post'])
	def execute_dag(self, request):
		"""Topologically sort and enqueue all pending tasks in a workspace."""
		workspace_key = request.data.get('workspace_key')
		if not workspace_key:
			return Response({'error': 'workspace_key required'}, status=status.HTTP_400_BAD_REQUEST)

		try:
			workspace = Tenant.objects.get(key=workspace_key)
		except Tenant.DoesNotExist:
			return Response({'error': 'Workspace not found'}, status=status.HTTP_404_NOT_FOUND)

		tasks = list(Task.objects.filter(workspace=workspace, status=Task.STATUS_PENDING))
		if not tasks:
			return Response({'message': 'No pending tasks'}, status=status.HTTP_200_OK)

		try:
			ordered = topological_sort(tasks)
		except ValueError as e:
			return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

		# Enqueue each task in topological order
		for task in ordered:
			execute_task.delay(task.id)

		return Response({
			'message': f'Enqueued {len(ordered)} tasks in DAG order',
			'task_ids': [t.id for t in ordered]
		})

	@action(detail=True, methods=['post'])
	def execute(self, request, pk=None):
		"""Enqueue a single task for execution."""
		task = self.get_object()
		execute_task.delay(task.id)
		return Response({'message': f'Task {task.id} enqueued'})

	@action(detail=False, methods=['get'])
	def metrics(self, request):
		"""Return execution metrics for a workspace."""
		workspace_key = request.query_params.get('workspace')
		if not workspace_key:
			return Response({'error': 'workspace_key required'}, status=status.HTTP_400_BAD_REQUEST)

		try:
			workspace = Tenant.objects.get(key=workspace_key)
		except Tenant.DoesNotExist:
			return Response({'error': 'Workspace not found'}, status=status.HTTP_404_NOT_FOUND)

		tasks = Task.objects.filter(workspace=workspace)
		results = TaskResult.objects.filter(task__workspace=workspace)

		total_duration = sum(
			float(r.duration_seconds() or 0)
			for r in results.filter(completed_at__isnull=False)
		)

		metrics = {
			'total_tasks': tasks.count(),
			'tasks_by_status': {
				'pending': tasks.filter(status=Task.STATUS_PENDING).count(),
				'running': tasks.filter(status=Task.STATUS_RUNNING).count(),
				'done': tasks.filter(status=Task.STATUS_DONE).count(),
				'failed': tasks.filter(status=Task.STATUS_FAILED).count(),
			},
			'execution_results': {
				'success': results.filter(status=TaskResult.STATUS_SUCCESS).count(),
				'failure': results.filter(status=TaskResult.STATUS_FAILURE).count(),
				'retry': results.filter(status=TaskResult.STATUS_RETRY).count(),
			},
			'total_duration_seconds': total_duration,
			'avg_task_duration': float(
				(lambda ds: (sum(ds) / len(ds) if len(ds) else 0))([
					float(r.duration_seconds() or 0) for r in results.filter(completed_at__isnull=False)
				])
			),
			'total_retries': results.aggregate(Count('retry_count')).get('retry_count__count', 0),
		}

		return Response(metrics)


class DashboardView(TemplateView):
	template_name = 'dashboard_v2.html'

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)

		# include workspace list
		workspaces = Tenant.objects.all()
		tenants_data = TenantSerializer(workspaces, many=True).data

		# include tasks (limit to a reasonable amount for initial render)
		tasks_qs = Task.objects.prefetch_related('dependencies', 'results').all()[:500]
		tasks_data = TaskSerializer(tasks_qs, many=True).data

		# compute global metrics (across selected tasks)
		results = TaskResult.objects.filter(task__in=tasks_qs)
		total_duration = sum(float(r.duration_seconds() or 0) for r in results.filter(completed_at__isnull=False))

		metrics = {
			'total_tasks': Task.objects.count(),
			'tasks_by_status': {
				'pending': Task.objects.filter(status=Task.STATUS_PENDING).count(),
				'running': Task.objects.filter(status=Task.STATUS_RUNNING).count(),
				'done': Task.objects.filter(status=Task.STATUS_DONE).count(),
				'failed': Task.objects.filter(status=Task.STATUS_FAILED).count(),
			},
			'execution_results': {
				'success': results.filter(status=TaskResult.STATUS_SUCCESS).count(),
				'failure': results.filter(status=TaskResult.STATUS_FAILURE).count(),
				'retry': results.filter(status=TaskResult.STATUS_RETRY).count(),
			},
			'total_duration_seconds': total_duration,
			'avg_task_duration': float(
				(lambda ds: (sum(ds) / len(ds) if len(ds) else 0))([
					float(r.duration_seconds() or 0) for r in results.filter(completed_at__isnull=False)
				])
			),
		}

		ctx['initial_metrics_json'] = json.dumps(metrics)
		ctx['initial_tasks_json'] = json.dumps(tasks_data)
		ctx['initial_workspaces_json'] = json.dumps(tenants_data)
		return ctx
