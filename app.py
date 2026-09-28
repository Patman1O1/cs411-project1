# ── Imports ──────────────────────────────────────────────────────────────────
# Builtin Imports
import argparse
from collections.abc import Callable
import json
import os
from typing import Any, Final, TypeAlias

# Third-Party Imports
from flask import Flask, Response, jsonify, render_template, request
from flask.typing import ResponseReturnValue

# Local Imports
from informed import DEFAULT_MEMORY_LIMIT, astar, greedy_best_first
from uninformed import bfs, dfs, ids, ucs

# ── Aliases ──────────────────────────────────────────────────────────────────
MapData: TypeAlias = dict[str, Any]
Graph: TypeAlias = dict[str, dict[str, float]]
Coordinates: TypeAlias = dict[str, float]
Locations: TypeAlias = dict[str, Coordinates]
SearchResult: TypeAlias = dict[str, Any]
SearchOptions: TypeAlias = dict[str, int]
Runner: TypeAlias = Callable[[str, str, SearchOptions], SearchResult]

# ── Constants ────────────────────────────────────────────────────────────────
BASE_DIR: Final[str] = os.path.dirname(os.path.abspath(__file__))
MAP_DATA_FILE: Final[str] = os.path.join(BASE_DIR, "map_data.json")
DEFAULT_PORT: Final[int] = 5_000
MIN_PORT: Final[int] = 1
MAX_PORT: Final[int] = 65_535
MIN_MEMORY_LIMIT: Final[int] = 1
MAX_MEMORY_LIMIT: Final[int] = 10_000

# ── Map Data ─────────────────────────────────────────────────────────────────
def load_map_data() -> MapData:
    if os.path.exists(MAP_DATA_FILE):
        try:
            with open(MAP_DATA_FILE, "r") as f:
                data: MapData = json.load(f)
                return data
        except Exception as e:
            print(f"Error loading {MAP_DATA_FILE}: {e}")

    return {
        "region": "State / Metro Area",
        "total_cities": 0,
        "total_edges": 0,
        "locations": {},
        "graph": {}
    }

# ── Constants ────────────────────────────────────────────────────────────────
MAP_DATA: Final[MapData] = load_map_data()
GRAPH: Final[Graph] = MAP_DATA.get("graph", {})
LOCATIONS: Final[Locations] = MAP_DATA.get("locations", {})
ALGORITHMS: Final[dict[str, Runner]] = {
    "bfs": lambda s, g, opts: bfs(GRAPH, s, g),
    "dfs": lambda s, g, opts: dfs(GRAPH, s, g),
    "ucs": lambda s, g, opts: ucs(GRAPH, s, g),
    "ids": lambda s, g, opts: ids(GRAPH, s, g),
    "greedy": lambda s, g, opts: greedy_best_first(GRAPH, LOCATIONS, s, g),
    "astar": lambda s, g, opts: astar(GRAPH, LOCATIONS, s, g)
}
ALGORITHMS["sma"] = ALGORITHMS["memory_bounded"]
ALGORITHMS["smastar"] = ALGORITHMS["memory_bounded"]

ALGORITHM_NAMES: Final[dict[str, str]] = {
    "bfs": "Breadth-First Search",
    "dfs": "Depth-First Search",
    "ucs": "Uniform-Cost Search",
    "ids": "Iterative Deepening Search",
    "greedy": "Greedy Best-First Search",
    "astar": "A* Search"
}

# ── Flask App ────────────────────────────────────────────────────────────────
app: Final[Flask] = Flask(__name__)

# ── Routes ───────────────────────────────────────────────────────────────────
@app.route("/")
def index() -> str: return render_template("index.html")

@app.route("/api/map", methods=["GET"])
def get_map() -> Response: return jsonify(MAP_DATA)

@app.route("/api/search", methods=["POST"])
def search() -> ResponseReturnValue:
    payload: dict[str, Any] = request.get_json(silent=True) or {}
    start: str = payload.get("start", "")
    goal: str = payload.get("goal", "")
    algorithm: str = (payload.get("algorithm") or "").lower()

    def error(msg: str, code: int = 400) -> tuple[Response, int]:
        return jsonify({
            "status": "error",
            "message": msg,
            "path": [],
            "cost": 0,
            "nodes_expanded": 0
        }), code

    if algorithm not in ALGORITHMS:
        return error(
            f"Unknown algorithm '{algorithm}'. "
            f"Choose one of: {', '.join(ALGORITHM_NAMES)}."
        )
    if start not in GRAPH: return error(f"Unknown start city '{start}'.")
    if goal not in GRAPH: return error(f"Unknown destination city '{goal}'.")

    memory_limit: int
    try:
        memory_limit = int(payload.get("memory_limit", DEFAULT_MEMORY_LIMIT))
    except (TypeError, ValueError):
        return error("memory_limit must be an integer.")

    if not MIN_MEMORY_LIMIT <= memory_limit <= MAX_MEMORY_LIMIT:
        return error(
            f"memory_limit must be between {MIN_MEMORY_LIMIT} "
            f"and {MAX_MEMORY_LIMIT}."
        )

    result: SearchResult = ALGORITHMS[algorithm](
        start,
        goal,
        {"memory_limit": memory_limit}
    )

    response: dict[str, Any] = {
        "status": "ok" if result["path"] else "no_path",
        "algorithm": algorithm,
        "algorithm_name": ALGORITHM_NAMES.get(algorithm, algorithm),
        "start": start,
        "goal": goal,
        **result
    }

    if result["path"]:
        response.setdefault(
            "message",
            f"{len(result['path']) - 1} road(s), {result['cost']} miles."
        )
    else:
        response.setdefault(
            "message",
            f"No path found from {start} to {goal}."
        )

    return jsonify(response)

# ── Command Line ─────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Run the search visualizer development server."
    )

    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"port to listen on (default: {DEFAULT_PORT})"
    )

    args: argparse.Namespace = parser.parse_args()
    if not MIN_PORT <= args.port <= MAX_PORT:
        parser.error(f"port must be between {MIN_PORT} and {MAX_PORT}")

    return args

# ── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    args: argparse.Namespace = parse_args()
    app.run(host="0.0.0.0", port=args.port, debug=True)
