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

greedy: Final = greedy_best_first
greedy_best_first_search: Final = greedy_best_first
a_star: Final = astar
