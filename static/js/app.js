// ── Aliases ─────────────────────────────────────────────────────────────────
/** @typedef {{ lat: number, lon: number }} Coordinates */
/** @typedef {Record<string, Coordinates>} Locations */
/** @typedef {Record<string, Record<string, number>>} Graph */
/** @typedef {{ main: string, selection: string, info: string }} Concept */

/**
 * @typedef {object} MapData
 * @property {string} [region]
 * @property {number} [total_cities]
 * @property {number} [total_edges]
 * @property {Locations} [locations]
 * @property {Graph} [graph]
 */

/**
 * @typedef {object} SearchRequest
 * @property {string} start
 * @property {string} goal
 * @property {string} algorithm
 * @property {number} [memory_limit]
 */

/**
 * @typedef {object} SearchResponse
 * @property {string} [status]
 * @property {string} [message]
 * @property {string[]} [path]
 * @property {number} [cost]
 * @property {number | string[]} [nodes_expanded]
 * @property {string[]} [expanded_order]
 * @property {number} [depth_limit]
 * @property {number} [memory_limit]
 * @property {number} [nodes_forgotten]
 * @property {number} [max_nodes_in_memory]
 */

// ── Constants ───────────────────────────────────────────────────────────────
/** @type {Readonly<Record<string, Concept>>} */
const ALGO_CONCEPTS = Object.freeze({
    "bfs": {
        main:
            "Explores the graph layer by layer: every city 1 road away, " +
            "then every city 2 roads away, and so on, using a FIFO queue.",
        selection:
            "Expands the shallowest frontier node first " +
            "(first in, first out).",
        info:
            "Depth only (number of roads). Road miles are ignored, so it " +
            "finds the path with the fewest roads, not the fewest miles."
    },
    "dfs": {
        main:
            "Follows one route as deep as possible before backtracking to " +
            "try another, using a LIFO stack.",
        selection:
            "Expands the deepest (most recently generated) frontier " +
            "node first.",
        info:
            "Depth/order of generation only. No path cost or heuristic, " +
            "so the path it returns is usually not optimal."
    },
    "ucs": {
        main:
            "Grows outward from the start in order of total miles driven, " +
            "using a priority queue on g(n).",
        selection:
            "Expands the frontier node with the lowest cumulative path " +
            "cost g(n).",
        info:
            "Path cost g(n) only (actual road miles from the start). " +
            "Optimal because all road distances are positive."
    },
    "ids": {
        main:
            "Runs depth-limited DFS with limits 0, 1, 2, ... until the goal " +
            "is found, combining DFS's small memory with BFS's " +
            "shallowest-goal guarantee.",
        selection:
            "Within each iteration, expands the deepest node first, but " +
            "never beyond the current depth limit L.",
        info:
            "Depth only (the current depth limit). Finds the fewest-roads " +
            "path, which is not necessarily the fewest miles."
    },
    "greedy": {
        main:
            "Heads straight for the goal by always expanding the city that " +
            "looks closest to the destination.",
        selection:
            "Expands the frontier node with the lowest heuristic value h(n).",
        info:
            "Heuristic h(n) only: straight-line (haversine) miles to the " +
            "goal. Ignores miles already driven, so it is fast but not " +
            "optimal."
    },
    "astar": {
        main:
            "Balances miles already driven against the estimated miles " +
            "remaining to find the shortest road route efficiently.",
        selection:
            "Expands the frontier node with the lowest f(n) = g(n) + h(n).",
        info:
            "Path cost g(n) plus straight-line heuristic h(n). Optimal " +
            "because h never overestimates road distance (admissible and " +
            "consistent)."
    },
    "memory_bounded": {
        main:
            "Runs A* with a fixed cap on stored nodes. When memory is full " +
            "it forgets the worst leaf, but saves that leaf's f-value in " +
            "its parent so the branch can be regenerated later.",
        selection:
            "Expands the deepest node with the lowest f(n) = g(n) + h(n); " +
            "when memory is full, drops the shallowest node with the " +
            "highest f(n).",
        info:
            "Path cost g(n), heuristic h(n), backed-up f-values of " +
            "forgotten nodes, and the memory limit. Optimal only if the " +
            "optimal path fits in memory."
    }
});

/** @type {string} */
const DEFAULT_ALGORITHM = "bfs";
/** @type {string} */
const MEMORY_BOUNDED_ALGORITHM = "memory_bounded";
/** @type {number} */
const DEFAULT_MEMORY_LIMIT = 12;

/** @type {L.LatLngTuple} */
const DEFAULT_CENTER = [40.0, -89.0];
/** @type {number} */
const DEFAULT_ZOOM = 7;
/** @type {number} */
const MAX_ZOOM = 18;
/** @type {L.PointTuple} */
const FIT_PADDING = [30, 30];
/** @type {string} */
const TILE_URL = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
/** @type {string} */
const TILE_ATTRIBUTION = "Map data &copy; OpenStreetMap contributors";

/** @type {string} */
const COLOR_DEFAULT = "#2563eb";
/** @type {string} */
const COLOR_EXPANDED = "#f59e0b";
/** @type {string} */
const COLOR_START = "#16a34a";
/** @type {string} */
const COLOR_GOAL = "#dc2626";
/** @type {string} */
const COLOR_EDGE = "#64748b";
/** @type {string} */
const COLOR_PATH = "#16a34a";
/** @type {string} */
const COLOR_MARKER_BORDER = "#ffffff";

/** @type {number} */
const RADIUS_DEFAULT = 5;
/** @type {number} */
const RADIUS_EXPANDED = 6;
/** @type {number} */
const RADIUS_ENDPOINT = 8;

/** @type {number} */
const EDGE_WEIGHT = 2;
/** @type {number} */
const EDGE_OPACITY = 0.6;
/** @type {number} */
const PATH_WEIGHT = 5;
/** @type {number} */
const MARKER_BORDER_WEIGHT = 1.5;
/** @type {number} */
const MARKER_FILL_OPACITY = 1.0;

// ── DOM Elements ────────────────────────────────────────────────────────────
/**
 * @param {string} id
 * @returns {HTMLElement}
 */
function el(id) {
    /** @type {HTMLElement | null} */
    const element = document.getElementById(id);
    if (!element) throw new Error(`Missing element #${id}`);

    return element;
}

/** @type {HTMLSelectElement} */
const startSelect = /** @type {HTMLSelectElement} */ (el("startSelect"));
/** @type {HTMLSelectElement} */
const goalSelect = /** @type {HTMLSelectElement} */ (el("goalSelect"));
/** @type {HTMLSelectElement} */
const algoSelect = /** @type {HTMLSelectElement} */ (el("algoSelect"));
/** @type {HTMLInputElement} */
const memoryInput = /** @type {HTMLInputElement} */ (el("memoryInput"));

/** @type {HTMLElement} */
const pageTitle = el("pageTitle");
/** @type {HTMLElement} */
const memoryGroup = el("memoryGroup");
/** @type {HTMLElement} */
const conceptMain = el("conceptMain");
/** @type {HTMLElement} */
const conceptSelection = el("conceptSelection");
/** @type {HTMLElement} */
const conceptInfo = el("conceptInfo");
/** @type {HTMLElement} */
const statCost = el("statCost");
/** @type {HTMLElement} */
const statEdges = el("statEdges");
/** @type {HTMLElement} */
const statExpanded = el("statExpanded");
/** @type {HTMLElement} */
const statExtra = el("statExtra");
/** @type {HTMLElement} */
const pathDisplay = el("pathDisplay");
/** @type {HTMLElement} */
const btnRun = el("btnRun");
/** @type {HTMLElement} */
const btnReset = el("btnReset");

// ── State ───────────────────────────────────────────────────────────────────
/** @type {MapData | null} */
let mapData = null;
/** @type {Record<string, L.CircleMarker>} */
const markers = {};
/** @type {L.Polyline | null} */
let activePath = null;

// ── Map Setup ───────────────────────────────────────────────────────────────
/** @type {L.Map} */
const map = L.map("map").setView(DEFAULT_CENTER, DEFAULT_ZOOM);

L.tileLayer(TILE_URL, {
    maxZoom: MAX_ZOOM,
    attribution: TILE_ATTRIBUTION
}).addTo(map);

// ── UI Helpers ──────────────────────────────────────────────────────────────
/**
 * @param {string} val
 * @returns {void}
 */
function showConcept(val) {
    /** @type {Concept} */
    const concept = ALGO_CONCEPTS[val] || ALGO_CONCEPTS[DEFAULT_ALGORITHM];

    conceptMain.textContent = concept.main;
    conceptSelection.textContent = concept.selection;
    conceptInfo.textContent = concept.info;

    memoryGroup.style.display =
        val === MEMORY_BOUNDED_ALGORITHM ? "flex" : "none";
}


/**
 * @param {string | null} start
 * @param {string | null} goal
 * @param {string[] | undefined} expanded
 * @returns {void}
 */
function styleMarkers(start, goal, expanded) {
    /** @type {Set<string>} */
    const expandedSet = new Set(expanded || []);

    for (const [city, marker] of Object.entries(markers)) {
        /** @type {string} */
        let color = COLOR_DEFAULT;
        /** @type {number} */
        let radius = RADIUS_DEFAULT;

        if (expandedSet.has(city)) {
            color = COLOR_EXPANDED;
            radius = RADIUS_EXPANDED;
        }
        if (city === start) {
            color = COLOR_START;
            radius = RADIUS_ENDPOINT;
        }
        if (city === goal) {
            color = COLOR_GOAL;
            radius = RADIUS_ENDPOINT;
        }

        marker.setStyle({ fillColor: color });
        marker.setRadius(radius);
    }
}


/**
 * @param {string} message
 * @returns {void}
 */
function showError(message) {
    pathDisplay.textContent = message;
    pathDisplay.classList.add("error");
}


/** @returns {void} */
function clearResults() {
    if (activePath) {
        map.removeLayer(activePath);
        activePath = null;
    }

    statCost.textContent = "--";
    statEdges.textContent = "--";
    statExpanded.textContent = "--";
    statExtra.textContent = "";

    pathDisplay.textContent = "None";
    pathDisplay.classList.remove("error");

    styleMarkers(null, null, []);
}

// ── Map Loading ─────────────────────────────────────────────────────────────
/**
 * @param {HTMLSelectElement} select
 * @param {string} city
 * @returns {void}
 */
function addCityOption(select, city) {
    /** @type {HTMLOptionElement} */
    const option = document.createElement("option");
    option.value = city;
    option.textContent = city;
    select.appendChild(option);
}


/**
 * @param {Graph} graph
 * @param {Locations} locs
 * @returns {void}
 */
function drawEdges(graph, locs) {
    /** @type {Set<string>} */
    const drawn = new Set();

    for (const [city, neighbors] of Object.entries(graph)) {
        for (const neighbor of Object.keys(neighbors)) {
            /** @type {string} */
            const edgeKey = [city, neighbor].sort().join("<->");
            if (drawn.has(edgeKey) || !locs[city] || !locs[neighbor]) continue;

            drawn.add(edgeKey);
            L.polyline(
                [
                    [locs[city].lat, locs[city].lon],
                    [locs[neighbor].lat, locs[neighbor].lon]
                ],
                {
                    color: COLOR_EDGE,
                    weight: EDGE_WEIGHT,
                    opacity: EDGE_OPACITY
                }
            ).addTo(map);
        }
    }
}


/**
 * @param {Locations} locs
 * @returns {L.LatLngTuple[]}
 */
function drawMarkers(locs) {
    /** @type {L.LatLngTuple[]} */
    const bounds = [];

    for (const [city, coords] of Object.entries(locs)) {
        bounds.push([coords.lat, coords.lon]);

        /** @type {L.CircleMarker} */
        const marker = L.circleMarker([coords.lat, coords.lon], {
            radius: RADIUS_DEFAULT,
            fillColor: COLOR_DEFAULT,
            color: COLOR_MARKER_BORDER,
            weight: MARKER_BORDER_WEIGHT,
            fillOpacity: MARKER_FILL_OPACITY
        }).addTo(map);

        marker.bindPopup(`<b>${city}</b>`);
        markers[city] = marker;
    }

    return bounds;
}


/** @returns {Promise<void>} */
async function init() {
    try {
        /** @type {Response} */
        const res = await fetch("/api/map");
        if (!res.ok) return;

        /** @type {MapData} */
        const data = await res.json();
        mapData = data;

        if (data.region) {
            pageTitle.textContent = `Search Visualizer - ${data.region}`;
        }

        /** @type {Locations} */
        const locs = data.locations || {};
        /** @type {Graph} */
        const graph = data.graph || {};
        /** @type {string[]} */
        const cities = Object.keys(locs).sort();

        for (const city of cities) {
            addCityOption(startSelect, city);
            addCityOption(goalSelect, city);
        }

        if (cities.length >= 2) {
            startSelect.selectedIndex = 1;
            goalSelect.selectedIndex = cities.length;
        }

        drawEdges(graph, locs);

        /** @type {L.LatLngTuple[]} */
        const bounds = drawMarkers(locs);
        if (bounds.length > 0) map.fitBounds(bounds, { padding: FIT_PADDING });
    } catch (err) {
        console.error("Error loading map:", err);
    }
}

// ── Search ──────────────────────────────────────────────────────────────────
/**
 * @param {SearchResponse} data
 * @returns {string}
 */
function formatExpanded(data) {
    if (data.nodes_expanded === undefined) return "--";
    if (Array.isArray(data.nodes_expanded)) {
        return String(data.nodes_expanded.length);
    }

    return String(data.nodes_expanded);
}


/**
 * @param {SearchResponse} data
 * @returns {string}
 */
function formatExtra(data) {
    /** @type {string[]} */
    const extra = [];

    if (data.depth_limit !== undefined) {
        extra.push(`Found at depth limit L = ${data.depth_limit}`);
    }
    if (data.memory_limit !== undefined) {
        extra.push(
            `Memory limit: ${data.memory_limit} nodes ` +
            `(peak used: ${data.max_nodes_in_memory}), ` +
            `nodes forgotten: ${data.nodes_forgotten}`
        );
    }

    return extra.join(" | ");
}


/** @returns {Promise<void>} */
async function runSearch() {
    /** @type {string} */
    const start = startSelect.value;
    /** @type {string} */
    const goal = goalSelect.value;
    /** @type {string} */
    const algo = algoSelect.value;

    if (!start || !goal) {
        alert("Please select both a start and destination city.");
        return;
    }

    clearResults();

    /** @type {SearchRequest} */
    const body = { start, goal, algorithm: algo };
    if (algo === MEMORY_BOUNDED_ALGORITHM) {
        body.memory_limit =
            parseInt(memoryInput.value, 10) || DEFAULT_MEMORY_LIMIT;
    }

    try {
        /** @type {Response} */
        const res = await fetch("/api/search", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });

        /** @type {SearchResponse} */
        const data = await res.json();

        styleMarkers(start, goal, data.expanded_order);
        statExpanded.textContent = formatExpanded(data);
        statExtra.textContent = formatExtra(data);

        if (!res.ok || !data.path || data.path.length === 0) {
            showError(data.message || "No path found.");
            return;
        }

        /** @type {Locations} */
        const locs = mapData?.locations || {};
        /** @type {L.LatLngTuple[]} */
        const latlngs = data.path.map(c => [locs[c].lat, locs[c].lon]);

        statCost.textContent = `${Number(data.cost).toFixed(2)} miles`;
        statEdges.textContent = String(data.path.length - 1);
        pathDisplay.textContent = data.path.join(" -> ");

        activePath = L.polyline(latlngs, {
            color: COLOR_PATH,
            weight: PATH_WEIGHT
        }).addTo(map);

        Object.values(markers).forEach(m => m.bringToFront());
    } catch (err) {
        console.error("Search failed:", err);
        showError("Search request failed. Check the server logs.");
    }
}

// ── Event Listeners ─────────────────────────────────────────────────────────
algoSelect.addEventListener("change", () => showConcept(algoSelect.value));
btnRun.addEventListener("click", runSearch);
btnReset.addEventListener("click", clearResults);

// ── Entry Point ─────────────────────────────────────────────────────────────
showConcept(algoSelect.value);
init();
