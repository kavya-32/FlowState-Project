from django.contrib import admin
from .models import Tenant, Task, TaskResult


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
	list_display = ['key', 'name', 'created_at']
	search_fields = ['key', 'name']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
	list_display = ['id', 'title', 'workspace', 'status', 'duration_display', 'created_at']
	list_filter = ['status', 'workspace', 'created_at']
	search_fields = ['title', 'description']
	filter_horizontal = ['dependencies']
	readonly_fields = ['created_at', 'updated_at', 'started_at', 'completed_at']

	def duration_display(self, obj):
		dur = obj.duration_seconds()
		return f'{dur:.2f}s' if dur else '—'
	duration_display.short_description = 'Duration'


@admin.register(TaskResult)
class TaskResultAdmin(admin.ModelAdmin):
	list_display = ['task', 'status', 'retry_count', 'duration_display', 'started_at']
	list_filter = ['status', 'started_at']
	search_fields = ['task__title', 'error_message']
	readonly_fields = ['task', 'started_at', 'completed_at', 'output', 'error_message']

	def duration_display(self, obj):
		dur = obj.duration_seconds()
		return f'{dur:.2f}s' if dur else '—'
	duration_display.short_description = 'Duration'
