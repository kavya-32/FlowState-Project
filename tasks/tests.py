from django.test import TestCase
from tasks.models import Tenant, Task
from tasks.utils import topological_sort


class DAGTests(TestCase):
	"""Test DAG topological sorting and task dependencies."""

	def setUp(self):
		self.workspace = Tenant.objects.create(key='test_workspace', name='Test')

	def test_linear_dependency_chain(self):
		"""Test A -> B -> C linear chain."""
		task_a = Task.objects.create(title='A', workspace=self.workspace)
		task_b = Task.objects.create(title='B', workspace=self.workspace)
		task_c = Task.objects.create(title='C', workspace=self.workspace)

		task_b.dependencies.add(task_a)
		task_c.dependencies.add(task_b)

		tasks = list(Task.objects.filter(workspace=self.workspace))
		ordered = topological_sort(tasks)

		self.assertEqual([t.id for t in ordered], [task_a.id, task_b.id, task_c.id])

	def test_diamond_dependency(self):
		"""Test diamond pattern: A -> B,C -> D."""
		task_a = Task.objects.create(title='A', workspace=self.workspace)
		task_b = Task.objects.create(title='B', workspace=self.workspace)
		task_c = Task.objects.create(title='C', workspace=self.workspace)
		task_d = Task.objects.create(title='D', workspace=self.workspace)

		task_b.dependencies.add(task_a)
		task_c.dependencies.add(task_a)
		task_d.dependencies.add(task_b, task_c)

		tasks = list(Task.objects.filter(workspace=self.workspace))
		ordered = topological_sort(tasks)
		ordered_ids = [t.id for t in ordered]

		self.assertEqual(ordered_ids[0], task_a.id)
		self.assertEqual(ordered_ids[-1], task_d.id)

	def test_cycle_detection(self):
		"""Test that cycles are detected."""
		task_a = Task.objects.create(title='A', workspace=self.workspace)
		task_b = Task.objects.create(title='B', workspace=self.workspace)

		task_a.dependencies.add(task_b)
		task_b.dependencies.add(task_a)

		tasks = list(Task.objects.filter(workspace=self.workspace))

		with self.assertRaises(ValueError):
			topological_sort(tasks)
