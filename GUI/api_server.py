import sys
import os
import copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify, send_from_directory
from greedy_select import greedy_selection
from delivery_optimizer import plan_all_trucks as greedy_plan_trucks, deg_to_km
from algorithms import (
    priority_queue_selection,
    plan_all_trucks as pq_plan_trucks,
    decay_urgency,
    reveal_fog_zones,
    compute_scores,
)

app = Flask(__name__, static_folder=".")

SCENARIOS = {
    "aleppo": {
        "label": "Aleppo Siege",
        "description": "Urban siege — high risk corridors, critical medical need",
        "depot": {"lat": 36.35, "lng": 37.10, "label": "Gaziantep Base"},
        "truck_capacity_kg": 14000,
        "num_trucks": 4,
        "fog_zones": ["C", "E"],
        "zones": [
            {"id": "A", "name": "Sheikh Maqsood", "lat": 36.24, "lng": 37.13, "demand_kg": 12000, "urgency": 10, "risk": 5, "supply_types": {"food": 5000, "medicine": 5000, "shelter": 2000}},
            {"id": "B", "name": "Salaheddine",    "lat": 36.18, "lng": 37.14, "demand_kg": 8000,  "urgency": 9,  "risk": 5, "supply_types": {"food": 3000, "medicine": 3500, "shelter": 1500}},
            {"id": "C", "name": "Bustan al-Qasr", "lat": 36.20, "lng": 37.16, "demand_kg": 6000,  "urgency": 8,  "risk": 4, "supply_types": {"food": 2000, "medicine": 3000, "shelter": 1000}},
            {"id": "D", "name": "Hanano",         "lat": 36.23, "lng": 37.18, "demand_kg": 9000,  "urgency": 7,  "risk": 3, "supply_types": {"food": 4000, "medicine": 2000, "shelter": 3000}},
            {"id": "E", "name": "Masaken Hanano", "lat": 36.25, "lng": 37.20, "demand_kg": 7000,  "urgency": 9,  "risk": 4, "supply_types": {"food": 3000, "medicine": 2500, "shelter": 1500}},
            {"id": "F", "name": "Helluk",         "lat": 36.21, "lng": 37.11, "demand_kg": 5000,  "urgency": 6,  "risk": 3, "supply_types": {"food": 2500, "medicine": 1500, "shelter": 1000}},
        ],
    },
    "idlib": {
        "label": "Idlib Displacement",
        "description": "Mass displacement along border — shelter demand critical",
        "depot": {"lat": 36.60, "lng": 36.70, "label": "Bab al-Hawa Crossing"},
        "truck_capacity_kg": 18000,
        "num_trucks": 3,
        "fog_zones": ["D"],
        "zones": [
            {"id": "A", "name": "Maarat al-Numan", "lat": 35.64, "lng": 36.67, "demand_kg": 15000, "urgency": 10, "risk": 3, "supply_types": {"food": 6000, "medicine": 3000, "shelter": 6000}},
            {"id": "B", "name": "Kafr Nabl",       "lat": 35.61, "lng": 36.56, "demand_kg": 10000, "urgency": 8,  "risk": 2, "supply_types": {"food": 4000, "medicine": 2000, "shelter": 4000}},
            {"id": "C", "name": "Saraqib",         "lat": 35.86, "lng": 36.80, "demand_kg": 12000, "urgency": 9,  "risk": 3, "supply_types": {"food": 5000, "medicine": 2500, "shelter": 4500}},
            {"id": "D", "name": "Taftanaz",        "lat": 35.99, "lng": 36.79, "demand_kg": 8000,  "urgency": 7,  "risk": 4, "supply_types": {"food": 3500, "medicine": 2500, "shelter": 2000}},
            {"id": "E", "name": "Ariha",           "lat": 35.80, "lng": 36.60, "demand_kg": 9000,  "urgency": 6,  "risk": 2, "supply_types": {"food": 4000, "medicine": 1500, "shelter": 3500}},
        ],
    },
    "bekaa": {
        "label": "Bekaa Valley Flood",
        "description": "Flash flooding — roads unstable, food and shelter urgent",
        "depot": {"lat": 33.85, "lng": 35.90, "label": "Zahle Hub"},
        "truck_capacity_kg": 20000,
        "num_trucks": 3,
        "fog_zones": ["B", "F"],
        "zones": [
            {"id": "A", "name": "Bar Elias",    "lat": 33.76, "lng": 35.94, "demand_kg": 18000, "urgency": 10, "risk": 2, "supply_types": {"food": 8000, "medicine": 2000, "shelter": 8000}},
            {"id": "B", "name": "Taanayel",     "lat": 33.77, "lng": 35.88, "demand_kg": 11000, "urgency": 8,  "risk": 2, "supply_types": {"food": 5000, "medicine": 1500, "shelter": 4500}},
            {"id": "C", "name": "Saadnayel",    "lat": 33.79, "lng": 35.98, "demand_kg": 9000,  "urgency": 7,  "risk": 1, "supply_types": {"food": 4000, "medicine": 1000, "shelter": 4000}},
            {"id": "D", "name": "Qaraaoun",     "lat": 33.55, "lng": 35.70, "demand_kg": 14000, "urgency": 9,  "risk": 3, "supply_types": {"food": 6000, "medicine": 2000, "shelter": 6000}},
            {"id": "E", "name": "Yohmor",       "lat": 33.62, "lng": 35.75, "demand_kg": 7000,  "urgency": 5,  "risk": 2, "supply_types": {"food": 3000, "medicine": 1500, "shelter": 2500}},
            {"id": "F", "name": "Lala",         "lat": 33.67, "lng": 35.82, "demand_kg": 10000, "urgency": 8,  "risk": 3, "supply_types": {"food": 4500, "medicine": 2000, "shelter": 3500}},
        ],
    },
    "mosul": {
        "label": "Mosul Post-Conflict",
        "description": "Post-conflict reconstruction — mixed risk, high demand",
        "depot": {"lat": 36.40, "lng": 43.00, "label": "Erbil Logistics Hub"},
        "truck_capacity_kg": 16000,
        "num_trucks": 5,
        "fog_zones": ["A", "C"],
        "zones": [
            {"id": "A", "name": "Old City",       "lat": 36.34, "lng": 43.13, "demand_kg": 14000, "urgency": 10, "risk": 5, "supply_types": {"food": 4000, "medicine": 6000, "shelter": 4000}},
            {"id": "B", "name": "Dawasa",         "lat": 36.35, "lng": 43.15, "demand_kg": 9000,  "urgency": 8,  "risk": 4, "supply_types": {"food": 4000, "medicine": 2500, "shelter": 2500}},
            {"id": "C", "name": "Al-Zanjili",     "lat": 36.36, "lng": 43.11, "demand_kg": 11000, "urgency": 9,  "risk": 5, "supply_types": {"food": 3500, "medicine": 5000, "shelter": 2500}},
            {"id": "D", "name": "Karama",         "lat": 36.37, "lng": 43.17, "demand_kg": 7000,  "urgency": 6,  "risk": 2, "supply_types": {"food": 3000, "medicine": 1500, "shelter": 2500}},
            {"id": "E", "name": "Nabi Yunus",     "lat": 36.36, "lng": 43.16, "demand_kg": 8000,  "urgency": 7,  "risk": 3, "supply_types": {"food": 3500, "medicine": 2000, "shelter": 2500}},
            {"id": "F", "name": "Hay al-Barid",   "lat": 36.33, "lng": 43.10, "demand_kg": 10000, "urgency": 8,  "risk": 4, "supply_types": {"food": 4000, "medicine": 3000, "shelter": 3000}},
            {"id": "G", "name": "Al-Muthanna",    "lat": 36.32, "lng": 43.12, "demand_kg": 6000,  "urgency": 5,  "risk": 2, "supply_types": {"food": 2500, "medicine": 1500, "shelter": 2000}},
        ],
    },
}

def build_truck_data(assignments, zones, routes, km_list, hours_list):
    zone_dict = {z["id"]: z for z in zones}
    truck_data = []
    for t, (route, km, hours) in enumerate(zip(routes, km_list, hours_list)):
        assigned_ids = assignments[t]
        load_kg = sum(zone_dict[zid]["demand_kg"] for zid in assigned_ids if zid in zone_dict)
        supply_breakdown = {"food": 0, "medicine": 0, "shelter": 0}
        for zid in assigned_ids:
            z = zone_dict.get(zid)
            if z and "supply_types" in z:
                for k in supply_breakdown:
                    supply_breakdown[k] += z["supply_types"].get(k, 0)
        truck_data.append({
            "truck_num":        t + 1,
            "assigned_ids":     assigned_ids,
            "route":            [z["id"] for z in route],
            "route_coords":     [{"lat": z["lat"], "lng": z["lng"], "id": z["id"]} for z in route],
            "km":               round(km, 1),
            "hours":            round(hours, 1),
            "load_kg":          load_kg,
            "supply_breakdown": supply_breakdown,
        })
    return truck_data

def build_zone_table(zones, assignments, depot):
    zone_dict = {z["id"]: z for z in zones}
    result = []
    for z in sorted(zones, key=lambda x: x.get("score", 0), reverse=True):
        assigned_truck = None
        for t, ids in enumerate(assignments):
            if z["id"] in ids:
                assigned_truck = t + 1
                break
        result.append({
            "id":             z["id"],
            "name":           z.get("name", z["id"]),
            "lat":            z["lat"],
            "lng":            z["lng"],
            "demand_kg":      z["demand_kg"],
            "urgency":        z["urgency"],
            "risk":           z["risk"],
            "dist_km":        round(deg_to_km(z.get("distance", 0)), 1),
            "score":          round(z.get("score", 0), 3),
            "assigned":       assigned_truck is not None,
            "assigned_truck": assigned_truck,
            "supply_types":   z.get("supply_types", {}),
        })
    return result

def run_scenario(sc, blocked_ids, n_trucks, capacity, revealed_fog):
    depot_dict = sc["depot"]
    depot = (depot_dict["lat"], depot_dict["lng"])
    fog_ids = set(sc.get("fog_zones", []))
    active_fog = fog_ids - set(revealed_fog.keys())
    visible_zones = [
        z.copy() for z in sc["zones"]
        if z["id"] not in blocked_ids and z["id"] not in active_fog
    ]
    total_demand = sum(z["demand_kg"] for z in sc["zones"])

    g_zones = [z.copy() for z in visible_zones]
    g_selected, g_assignments, g_kg, g_urgency = greedy_selection(g_zones, capacity, n_trucks, depot)
    g_routes, g_km, g_hours = greedy_plan_trucks(g_assignments, g_zones, depot)
    g_trucks = build_truck_data(g_assignments, g_zones, g_routes, g_km, g_hours)
    g_zone_table = build_zone_table(g_zones, g_assignments, depot)
    g_coverage = round(g_kg / total_demand * 100, 1) if total_demand else 0

    p_zones = [z.copy() for z in visible_zones]
    p_selected, p_assignments, p_kg, p_urgency = priority_queue_selection(p_zones, capacity, n_trucks, depot)
    p_routes, p_km, p_hours = pq_plan_trucks(p_assignments, p_zones, depot)
    p_trucks = build_truck_data(p_assignments, p_zones, p_routes, p_km, p_hours)
    p_zone_table = build_zone_table(p_zones, p_assignments, depot)
    p_coverage = round(p_kg / total_demand * 100, 1) if total_demand else 0

    fog_zone_data = []
    for z in sc["zones"]:
        if z["id"] in active_fog:
            fog_zone_data.append({"id": z["id"], "lat": z["lat"], "lng": z["lng"], "name": z.get("name", z["id"]), "status": "unknown"})
        elif z["id"] in revealed_fog:
            accessible = revealed_fog[z["id"]]
            fog_zone_data.append({"id": z["id"], "lat": z["lat"], "lng": z["lng"], "name": z.get("name", z["id"]), "status": "accessible" if accessible else "blocked_fog"})

    return {
        "depot":        {"lat": depot[0], "lng": depot[1], "label": depot_dict.get("label", "Depot")},
        "fog_zones":    fog_zone_data,
        "blocked_zones": list(blocked_ids),
        "total_demand_kg": total_demand,
        "greedy": {
            "zones":   g_zone_table,
            "trucks":  g_trucks,
            "metrics": {
                "coverage_pct":   g_coverage,
                "total_kg":       g_kg,
                "total_urgency":  g_urgency,
                "total_hours":    round(sum(g_hours), 1),
                "trucks_used":    sum(1 for t in g_trucks if t["assigned_ids"]),
                "zones_served":   len(g_selected),
                "zones_total":    len(sc["zones"]),
            },
        },
        "priority_queue": {
            "zones":   p_zone_table,
            "trucks":  p_trucks,
            "metrics": {
                "coverage_pct":   p_coverage,
                "total_kg":       p_kg,
                "total_urgency":  p_urgency,
                "total_hours":    round(sum(p_hours), 1),
                "trucks_used":    sum(1 for t in p_trucks if t["assigned_ids"]),
                "zones_served":   len(p_selected),
                "zones_total":    len(sc["zones"]),
            },
        },
    }

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/api/scenarios", methods=["GET"])
def get_scenarios():
    return jsonify([{"id": k, "label": v["label"], "description": v["description"]} for k, v in SCENARIOS.items()])

@app.route("/api/run", methods=["POST"])
def run():
    body          = request.get_json(force=True)
    scenario_id   = body.get("scenario", "aleppo")
    blocked_ids   = set(body.get("blocked_zones", []))
    n_trucks      = body.get("num_trucks", None)
    capacity      = body.get("truck_capacity_kg", None)
    revealed_fog  = body.get("revealed_fog", {})

    sc = SCENARIOS.get(scenario_id, SCENARIOS["aleppo"])
    if n_trucks is None:
        n_trucks = sc["num_trucks"]
    if capacity is None:
        capacity = sc["truck_capacity_kg"]

    result = run_scenario(sc, blocked_ids, n_trucks, capacity, revealed_fog)
    result["scenario"] = scenario_id
    return jsonify(result)

@app.route("/api/reveal-fog", methods=["POST"])
def reveal_fog():
    body        = request.get_json(force=True)
    scenario_id = body.get("scenario", "aleppo")
    fog_ids     = body.get("fog_ids", [])
    seed        = body.get("seed", 42)
    results     = reveal_fog_zones(None, fog_ids, seed)
    return jsonify({"revealed": results})

@app.route("/api/tick", methods=["POST"])
def tick():
    body          = request.get_json(force=True)
    scenario_id   = body.get("scenario", "aleppo")
    zones         = body.get("zones", [])
    served_ids    = set(body.get("served_ids", []))
    hours_elapsed = body.get("hours_elapsed", 24)

    decayed = decay_urgency(zones, hours_elapsed, served_ids)
    return jsonify({"zones": decayed})

if __name__ == "__main__":
    import webbrowser
    port = 8000
    print(f"\n  EAOPT running at  http://localhost:{port}\n")
    webbrowser.open(f"http://localhost:{port}")
    app.run(debug=False, port=port)

