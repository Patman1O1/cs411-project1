# ── Imports ──────────────────────────────────────────────────────────────────
# Builtin Imports
from collections import deque
from collections.abc import Iterator
import heapq
from itertools import count
from typing import Any, Optional, TypeAlias

# ── Aliases ──────────────────────────────────────────────────────────────────
Graph: TypeAlias = dict[str, dict[str, float]]
Parents: TypeAlias = dict[str, Optional[str]]
SearchResult: TypeAlias = dict[str, Any]
DLSResult: TypeAlias = tuple[Optional[list[str]], bool]

# ── Helpers ──────────────────────────────────────────────────────────────────
def neighbors(graph: Graph, state: str) -> list[str]:
    return sorted(graph.get(state, {}).keys())

def path_cost(graph: Graph, path: list[str]) -> float:
    return round(sum(graph[a][b] for a, b in zip(path, path[1:])), 2)

def reconstruct(parents: Parents, goal: str) -> list[str]:
    path: list[str] = [goal]
    parent: Optional[str] = parents[goal]

    while parent is not None:
        path.append(parent)
        parent = parents[parent]

    path.reverse()
    return path

def make_result(
    graph: Graph,
    path: list[str],
    expanded_order: list[str]
) -> SearchResult:
    return {
        "path": path,
        "cost": path_cost(graph, path) if path else 0,
        "nodes_expanded": len(expanded_order),
        "expanded_order": expanded_order,
    }

def _validate(graph: Graph, start: str, goal: str) -> None:
    if start not in graph:
        raise ValueError(f"Unknown start state: {start!r}")

    if goal not in graph:
        raise ValueError(f"Unknown goal state: {goal!r}")

    return None

# ── 1. Breadth-First Search ──────────────────────────────────────────────────
def bfs(graph: Graph, start: str, goal: str) -> SearchResult:
    _validate(graph, start, goal)
    if start == goal: return make_result(graph, [start], [])

    frontier: deque[str] = deque([start])
    parents: Parents = {start: None}
    expanded: list[str] = []

    while frontier:
        node: str = frontier.popleft()
        expanded.append(node)
        nxt: str
        for nxt in neighbors(graph, node):
            if nxt not in parents:
                parents[nxt] = node
                if nxt == goal:
                    return make_result(
                        graph,
                        reconstruct(parents, goal),
                        expanded
                    )
                frontier.append(nxt)

    return make_result(graph, [], expanded)

# ── 2. Depth-First Search ────────────────────────────────────────────────────
def dfs(graph: Graph, start: str, goal: str) -> SearchResult:
    _validate(graph, start, goal)

    stack: list[tuple[str, list[str]]] = [(start, [start])]
    explored: set[str] = set()
    expanded: list[str] = []

    while stack:
        node: str
        path: list[str]
        node, path = stack.pop()

        if node in explored: continue

        explored.add(node)
        expanded.append(node)

        if node == goal: return make_result(graph, path, expanded)

        nxt: str
        for nxt in reversed(neighbors(graph, node)):
            if nxt not in explored:
                stack.append((nxt, path + [nxt]))

    return make_result(graph, [], expanded)

# ── 3. Uniform-Cost Search ───────────────────────────────────────────────────
def ucs(graph: Graph, start: str, goal: str) -> SearchResult:
    _validate(graph, start, goal)

    tie: Iterator[int] = count()
    frontier: list[tuple[float, int, str]] = [(0.0, next(tie), start)]
    best_g: dict[str, float] = {start: 0.0}
    parents: Parents = {start: None}
    explored: set[str] = set()
    expanded: list[str] = []

    while frontier:
        g: float
        node: str
        g, _, node = heapq.heappop(frontier)

        if node in explored: continue

        explored.add(node)
        expanded.append(node)

        if node == goal:
            return make_result(graph, reconstruct(parents, goal), expanded)

        nxt: str
        for nxt in neighbors(graph, node):
            new_g: float = g + graph[node][nxt]
            if nxt not in explored and new_g < best_g.get(nxt, float("inf")):
                best_g[nxt] = new_g
                parents[nxt] = node
                heapq.heappush(frontier, (new_g, next(tie), nxt))

    return make_result(graph, [], expanded)

# ── 3. Iterative Deepening Search ────────────────────────────────────────────
def depth_limited_search(
        graph: Graph,
        start: str,
        goal: str,
        limit: int,
        expanded: list[str]
) -> DLSResult:
    def recurse(node: str, path: list[str], depth: int) -> DLSResult:
        expanded.append(node)

        if node == goal: return path, False

        if depth == limit: return None, True

        cutoff: bool = False
        nxt: str

        for nxt in neighbors(graph, node):
            if nxt in path: continue

            result: Optional[list[str]]
            child_cutoff: bool
            result, child_cutoff = recurse(nxt, path + [nxt], depth + 1)
            if result is not None:
                return result, False
            cutoff = cutoff or child_cutoff
        return None, cutoff

    return recurse(start, [start], 0)


def ids(
    graph: Graph,
    start: str,
    goal: str,
    max_depth: Optional[int] = None
) -> SearchResult:
    _validate(graph, start, goal)
    if max_depth is None: max_depth = len(graph)

    expanded: list[str] = []
    limit: int
    for limit in range(max_depth + 1):
        path: Optional[list[str]]
        cutoff: bool
        path, cutoff = depth_limited_search(
            graph,
            start,
            goal,
            limit,
            expanded
        )
        if path is not None:
            result: SearchResult = make_result(graph, path, expanded)
            result["depth_limit"] = limit
            return result

        if not cutoff: break

    return make_result(graph, [], expanded)
