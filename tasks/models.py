from django.db import models
from django.utils import timezone


class Tenant(models.Model):
	"""Represents a workspace/tenant. Used for logical sharding and grouping."""
	key = models.CharField(max_length=100, unique=True)
	name = models.CharField(max_length=200, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.key


class Task(models.Model):
	STATUS_PENDING = 'pending'
	STATUS_RUNNING = 'running'
	STATUS_DONE = 'done'
	STATUS_FAILED = 'failed'

	STATUS_CHOICES = [
		(STATUS_PENDING, 'Pending'),
		(STATUS_RUNNING, 'Running'),
		(STATUS_DONE, 'Done'),
		(STATUS_FAILED, 'Failed'),
	]

	title = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	workspace = models.ForeignKey(Tenant, related_name='tasks', on_delete=models.CASCADE)
	dependencies = models.ManyToManyField('self', symmetrical=False, related_name='dependents', blank=True)
	status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	started_at = models.DateTimeField(null=True, blank=True)
	completed_at = models.DateTimeField(null=True, blank=True)

	def __str__(self):
		return f"{self.title} ({self.pk})"

	def dependent_ids(self):
		return list(self.dependencies.values_list('id', flat=True))

	def duration_seconds(self):
		"""Return execution duration in seconds."""
		if self.started_at and self.completed_at:
			return (self.completed_at - self.started_at).total_seconds()
		return None


class TaskResult(models.Model):
	"""Persist task execution results with error tracking."""
	STATUS_SUCCESS = 'success'
	STATUS_FAILURE = 'failure'
	STATUS_RETRY = 'retry'

	STATUS_CHOICES = [
		(STATUS_SUCCESS, 'Success'),
		(STATUS_FAILURE, 'Failure'),
		(STATUS_RETRY, 'Retry'),
	]

	task = models.ForeignKey(Task, related_name='results', on_delete=models.CASCADE)
	status = models.CharField(max_length=16, choices=STATUS_CHOICES)
	output = models.TextField(blank=True)
	error_message = models.TextField(blank=True)
	retry_count = models.IntegerField(default=0)
	started_at = models.DateTimeField(auto_now_add=True)
	completed_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		ordering = ['-started_at']

	def __str__(self):
		return f"Task {self.task.id} - {self.status} (Attempt {self.retry_count + 1})"

	def duration_seconds(self):
		if self.completed_at:
			return (self.completed_at - self.started_at).total_seconds()
		return None

