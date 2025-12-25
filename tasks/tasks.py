import time
import random
from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

from .models import Task, TaskResult


@shared_task(bind=True, max_retries=3)
def execute_task(self, task_id):
	"""Execute a task with retry logic and result persistence."""
	try:
		task = Task.objects.get(pk=task_id)
	except Task.DoesNotExist:
		return {'error': f'Task {task_id} not found'}

	task.status = Task.STATUS_RUNNING
	task.started_at = timezone.now()
	task.save()

	channel_layer = get_channel_layer()
	async_to_sync(channel_layer.group_send)(f'workspace_{task.workspace.key}', {
		'type': 'task_update',
		'payload': {'id': task.id, 'status': task.status},
	})

	try:
		# Simulate work with random chance of failure for demo
		time.sleep(2)
		if random.random() < 0.1:  # 10% failure rate
			raise Exception('Simulated random failure')

		output = f'Task {task.id} completed successfully'
		task.status = Task.STATUS_DONE
		task.completed_at = timezone.now()
		task.save()

		# Record successful result
		TaskResult.objects.create(
			task=task,
			status=TaskResult.STATUS_SUCCESS,
			output=output,
			completed_at=timezone.now(),
			retry_count=self.request.retries
		)

		async_to_sync(channel_layer.group_send)(f'workspace_{task.workspace.key}', {
			'type': 'task_update',
			'payload': {'id': task.id, 'status': task.status, 'output': output},
		})

		return {'task_id': task.id, 'status': 'success', 'output': output}

	except Exception as exc:
		if self.request.retries < self.max_retries:
			# Retry with exponential backoff
			raise self.retry(exc=exc, countdown=2 ** self.request.retries)
		else:
			# Max retries exceeded
			task.status = Task.STATUS_FAILED
			task.completed_at = timezone.now()
			task.save()

			error_msg = str(exc)
			TaskResult.objects.create(
				task=task,
				status=TaskResult.STATUS_FAILURE,
				error_message=error_msg,
				completed_at=timezone.now(),
				retry_count=self.request.retries
			)

			async_to_sync(channel_layer.group_send)(f'workspace_{task.workspace.key}', {
				'type': 'task_update',
				'payload': {'id': task.id, 'status': task.status, 'error': error_msg},
			})

			return {'task_id': task.id, 'status': 'failed', 'error': error_msg}
