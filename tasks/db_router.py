from django.conf import settings


class TenantShardRouter:
    """A simple DB router that demonstrates logical sharding by tenant key.

    It only routes when a hint `workspace` (string key) is explicitly provided.
    Otherwise it returns None to fall back to the default DB.
    This avoids recursive issues with lazy relationship loading.
    """

    def _db_for_workspace(self, workspace_key):
        if not workspace_key:
            return None
        return settings.SHARD_MAP.get(workspace_key)

    def db_for_read(self, model, **hints):
        if model._meta.app_label != 'tasks':
            return None
        workspace = hints.get('workspace')
        return self._db_for_workspace(workspace)

    def db_for_write(self, model, **hints):
        return self.db_for_read(model, **hints)

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Allow migrations on all DBs for demo purposes.
        return True
