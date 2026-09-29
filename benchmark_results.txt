#!/usr/bin/env python3

# Builtin Imports
from collections.abc import Callable
import itertools
import json
import statistics
import time
from typing import Any, TypeAlias

# Local Imports
from uninformed import bfs, dfs, ucs, ids
from informed import greedy_best_first, astar

# ── Aliases ──────────────────────────────────────────────────────────────────
Graph: TypeAlias = dict[str, dict[str, float]]
Coordinates: TypeAlias = dict[str, float]
Locations: TypeAlias = dict[str, Coordinates]
SearchResult: TypeAlias = dict[str, Any]
Runner: TypeAlias = Callable[[str, str], SearchResult]

# ── Variables ────────────────────────────────────────────────────────────────
d: dict[str, Any] = json.load(open("map_data.json"))
G: Graph = d["graph"]
L: Locations = d["locations"]

algos: dict[str, Runner] = {
    "BFS": lambda s, g: bfs(G, s, g),
    "DFS": lambda s, g: dfs(G, s, g),
    "UCS": lambda s, g: ucs(G, s, g),
    "IDS": lambda s, g: ids(G, s, g),
    "Greedy": lambda s, g: greedy_best_first(G, L, s, g),
    "A*": lambda s, g: astar(G, L, s, g),
}

pairs: list[tuple[str, str]] = list(itertools.permutations(sorted(G), 2))

name: str
run: Runner
s: str
g: str

# ── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    for name, run in algos.items():
        exp: list[int] = [run(s, g)["nodes_expanded"] for s, g in pairs]
        t: float = time.perf_counter()

        for _ in range(20):
            for s, g in pairs: run(s, g)

        micro_secs: float = \
            (time.perf_counter() - t) / 20.0 / len(pairs) * 1.0e6

        print(
            f"{name:7}" +
            f"avg={statistics.mean(exp):.1f} " +
            f"max={max(exp)} {micro_secs:.1f} µs"
        )
