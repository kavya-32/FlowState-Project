from rest_framework import serializers
from .models import Tenant, Task, TaskResult


class TenantSerializer(serializers.ModelSerializer):
	class Meta:
		model = Tenant
		fields = ['id', 'key', 'name', 'created_at']


class TaskResultSerializer(serializers.ModelSerializer):
	duration = serializers.SerializerMethodField()

	class Meta:
		model = TaskResult
		fields = ['id', 'status', 'output', 'error_message', 'retry_count', 'started_at', 'completed_at', 'duration']

	def get_duration(self, obj):
		return obj.duration_seconds()


class TaskSerializer(serializers.ModelSerializer):
	dependencies = serializers.PrimaryKeyRelatedField(
		many=True, queryset=Task.objects.all(), required=False
	)
	results = TaskResultSerializer(many=True, read_only=True)
	duration = serializers.SerializerMethodField()

	class Meta:
		model = Task
		fields = ['id', 'title', 'description', 'workspace', 'dependencies', 'status', 'created_at', 'updated_at', 'started_at', 'completed_at', 'duration', 'results']

	def to_representation(self, instance):
		"""Return human-readable workspace key instead of ID."""
		ret = super().to_representation(instance)
		ret['workspace_key'] = instance.workspace.key
		return ret

	def get_duration(self, obj):
		return obj.duration_seconds()
