from collections import deque, defaultdict


def topological_sort(tasks):
    """Return a list of Task model instances in topological order.

    Raises ValueError if a cycle is detected.
    Expects `tasks` to be an iterable of Task instances (prefetch dependencies for efficiency).
    """
    nodes = {t.id: t for t in tasks}
    indegree = defaultdict(int)
    adj = defaultdict(list)

    for t in tasks:
        deps = [d.id for d in t.dependencies.all()]
        indegree[t.id] += len(deps)
        for d in deps:
            adj[d].append(t.id)

    q = deque([nid for nid in nodes if indegree[nid] == 0])
    result_ids = []

    while q:
        n = q.popleft()
        result_ids.append(n)
        for m in adj[n]:
            indegree[m] -= 1
            if indegree[m] == 0:
                q.append(m)

    if len(result_ids) != len(nodes):
        raise ValueError('Cycle detected in task dependencies')

    return [nodes[i] for i in result_ids]
