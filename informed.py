# ── Imports ──────────────────────────────────────────────────────────────────
# Builtin Imports
from collections.abc import Callable, Iterator
import heapq
from itertools import count
import math
from typing import Any, Final, Optional, TypeAlias

# Local Imports
from uninformed import make_result, neighbors, _validate, reconstruct

# ── Aliases ──────────────────────────────────────────────────────────────────
Graph: TypeAlias = dict[str, dict[str, float]]
Coordinates: TypeAlias = dict[str, float]
Locations: TypeAlias = dict[str, Coordinates]
Heuristic: TypeAlias = Callable[[str], float]
SearchResult: TypeAlias = dict[str, Any]

# ── Constants ────────────────────────────────────────────────────────────────
EARTH_RADIUS_MILES: Final[float] = 3_958.8
DEFAULT_MEMORY_LIMIT: Final[int] = 12
MAX_ITERATIONS: Final[int] = 200_000

# ── `_Node` ──────────────────────────────────────────────────────────────────
class _Node:
    # ── Static Variables ─────────────────────────────────────────────────────
    __slots__ = (
        "state",
        "parent",
        "g",
        "f",
        "depth",
        "successors",
        "children",
        "forgotten",
        "next_index",
        "uid"
    )
    state: str
    parent: Optional["_Node"]
    g: float
    f: float
    depth: int
    successors: list[str]
    children: dict[str, "_Node"]
    forgotten: dict[str, float]
    next_index: int
    uid: int

    # ── Constructor ──────────────────────────────────────────────────────────
    def __init__(
        self,
        state: str,
        parent: Optional["_Node"],
        g: float,
        f: float,
        depth: int,
        successors: list[str],
        uid: int
    ) -> None:
        self.state: str = state
        self.parent: Optional["_Node"] = parent
        self.g: float = g
        self.f: float = f
        self.depth: int = depth
        self.successors: list[str] = successors
        self.children: dict[str, "_Node"] = {}
        self.forgotten: dict[str, float] = {}
        self.next_index: int = 0
        self.uid: int = uid

    # ── Methods ──────────────────────────────────────────────────────────────
    def all_generated_once(self) -> bool:
        return self.next_index >= len(self.successors)

    def all_in_memory(self) -> bool:
        return len(self.children) == len(self.successors)

    def path(self) -> list[str]:
        out: list[str] = []
        n: Optional[_Node] = self
        while n is not None:
            out.append(n.state)
            n = n.parent
        return out[::-1]

# ── Heuristic ────────────────────────────────────────────────────────────────
def haversine(locations: Locations, a: str, b: str) -> float:
    lat1: float = locations[a]["lat"]
    lon1: float = locations[a]["lon"]

    lat2: float = locations[b]["lat"]
    lon2: float = locations[b]["lon"]

    phi1: float = math.radians(lat1)
    phi2: float = math.radians(lat2)

    dphi: float = math.radians(lat2 - lat1)
    dlmb: float = math.radians(lon2 - lon1)

    x: float =                        \
        math.sin(dphi / 2.0) ** 2.0 + \
        math.cos(phi1) *              \
        math.cos(phi2) *              \
        math.sin(dlmb / 2) ** 2.0

    return 2.0 *                                       \
           EARTH_RADIUS_MILES *                        \
           math.atan2(math.sqrt(x), math.sqrt(1.0 - x))


def make_heuristic(locations: Locations, goal: str) -> Heuristic:
    cache: dict[str, float] = {}

    def h(n: str) -> float:
        if n not in cache: cache[n] = haversine(locations, n, goal)

        return cache[n]

    return h

# ── 5. Greedy Best-First Search ──────────────────────────────────────────────
def greedy_best_first(
    graph: Graph,
    locations: Locations,
    start: str,
    goal: str
) -> SearchResult:
    _validate(graph, start, goal)
    h: Heuristic = make_heuristic(locations, goal)

    tie: Iterator[int] = count()
    frontier: list[tuple[float, int, str]] = [(h(start), next(tie), start)]
    parents: dict[str, Optional[str]] = {start: None}
    explored: set[str] = set()
    expanded: list[str] = []

    while frontier:
        node: str
        _, _, node = heapq.heappop(frontier)
        if node in explored:
            continue
        explored.add(node)
        expanded.append(node)

        if node == goal:
            return make_result(graph, reconstruct(parents, goal), expanded)

        nxt: str
        for nxt in neighbors(graph, node):
            if nxt not in explored and nxt not in parents:
                parents[nxt] = node
                heapq.heappush(frontier, (h(nxt), next(tie), nxt))

    return make_result(graph, [], expanded)


# ── 6. A* Search ─────────────────────────────────────────────────────────────
def astar(
    graph: Graph,
    locations: Locations,
    start: str,
    goal: str
) -> SearchResult:
    _validate(graph, start, goal)
    h: Heuristic = make_heuristic(locations, goal)

    tie: Iterator[int] = count()
    frontier: list[tuple[float, int, float, str]] = [(
        h(start),
        next(tie),
        0.0,
        start
    )]
    best_g: dict[str, float] = {start: 0.0}
    parents: dict[str, Optional[str]] = {start: None}
    expanded: list[str] = []

    while frontier:
        g: float
        node: str
        _, _, g, node = heapq.heappop(frontier)

        if g > best_g.get(node, math.inf): continue

        expanded.append(node)

        if node == goal:
            return make_result(graph, reconstruct(parents, goal), expanded)

        nxt: str
        for nxt in neighbors(graph, node):
            new_g: float = g + graph[node][nxt]
            if new_g < best_g.get(nxt, math.inf):
                best_g[nxt] = new_g
                parents[nxt] = node
                heapq.heappush(
                    frontier,
                    (new_g + h(nxt), next(tie), new_g, nxt)
                )

    return make_result(graph, [], expanded)


# ── 7. Simplified Memory-Bounded A* (SMA*) ───────────────────────────────────
def sma_star(
    graph: Graph,
    locations: Locations,
    start: str,
    goal: str,
    memory_limit: int = DEFAULT_MEMORY_LIMIT
) -> SearchResult:
    _validate(graph, start, goal)
    if memory_limit < 1: raise ValueError("memory_limit must be at least 1")

    h: Heuristic = make_heuristic(locations, goal)
    uid: Iterator[int] = count()

    def new_node(
        state: str,
        parent: Optional[_Node],
        g: float,
        f: float
    ) -> _Node:
        depth: int = parent.depth + 1 if parent else 1

        on_path: set[str] = set(parent.path()) if parent else set()
        on_path.add(state)

        succ: list[str] = [
            s for s in neighbors(graph, state) if s not in on_path
        ]

        return _Node(state, parent, g, f, depth, succ, next(uid))

    root: _Node = new_node(start, None, 0.0, h(start))
    open_set: set[_Node] = {root}
    stats: dict[str, int] = {"in_memory": 1, "peak": 1, "forgotten": 0}
    expanded: list[str] = []
    result: Optional[SearchResult] = None

    def backup(node: Optional[_Node]) -> None:
        while node is not None and node.all_generated_once():
            known: list[float] = [
                c.f for c in node.children.values()
            ] + list(node.forgotten.values())

            new_f: float = min(known) if known else math.inf
            if new_f == node.f:
                break
            node.f = new_f
            node = node.parent

    def remove_leaf(leaf: _Node) -> None:
        parent: Optional[_Node] = leaf.parent
        assert parent is not None, "the root is never removed"
        del parent.children[leaf.state]
        parent.forgotten[leaf.state] = leaf.f
        open_set.discard(leaf)
        open_set.add(parent)
        stats["in_memory"] -= 1
        backup(parent)

    for _ in range(MAX_ITERATIONS):
        if not open_set: break

        best: _Node = min(open_set, key=lambda n: (n.f, -n.depth, -n.uid))
        if best.f == math.inf: break
        if best.state == goal:
            result = make_result(graph, best.path(), expanded)
            break

        if not best.successors:
            best.f = math.inf
            if best is root:
                break
            remove_leaf(best)
            continue

        s_state: str
        remembered_f: Optional[float] = None

        if not best.all_generated_once():
            s_state = best.successors[best.next_index]
            best.next_index += 1
        else:
            s_state = min(best.forgotten, key=best.forgotten.__getitem__)
            remembered_f = best.forgotten.pop(s_state)
        expanded.append(best.state)

        g: float = best.g + graph[best.state][s_state]
        f: float

        if s_state != goal and best.depth + 1 >= memory_limit:
            f = math.inf
        else:
            f = max(best.f, g + h(s_state))
            if remembered_f is not None: f = max(f, remembered_f)

        child: _Node = new_node(s_state, best, g, f)

        if stats["in_memory"] >= memory_limit:
            leaves: list[_Node] = [
                n for n in open_set \
                    if not n.children and n is not root and n is not best
            ]

            if leaves:
                remove_leaf(max(leaves, key=lambda n: (n.f, -n.depth, n.uid)))
                stats["forgotten"] += 1
            else:
                best.forgotten[s_state] = f
                backup(best)
                continue

        best.children[s_state] = child
        open_set.add(child)
        stats["in_memory"] += 1
        stats["peak"] = max(stats["peak"], stats["in_memory"])

        if best.all_generated_once():
            backup(best)
        if best.all_in_memory():
            open_set.discard(best)

    if result is None:
        result = make_result(graph, [], expanded)
        result["message"] = (
            f"SMA* found no path within a memory limit of "
            f"{memory_limit} nodes. Try a larger limit."
        )

    result["memory_limit"] = memory_limit
    result["nodes_forgotten"] = stats["forgotten"]
    result["max_nodes_in_memory"] = stats["peak"]
    return result


greedy: Final = greedy_best_first
greedy_best_first_search: Final = greedy_best_first
a_star: Final = astar
smastar: Final = sma_star
