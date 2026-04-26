import heapq
import math
import copy

def deg_to_km(deg):
    return deg * 111.0

def compute_scores(zones, depot):
    for zone in zones:
        dx = zone['lng'] - depot[1]
        dy = zone['lat'] - depot[0]
        zone['distance'] = math.hypot(dx, dy) or 0.001
        zone['score'] = zone['urgency'] / (zone['distance'] * zone['risk'])
    return zones

def priority_queue_selection(zones, truck_capacity_kg, num_trucks, depot):
    zones = compute_scores(zones, depot)
    heap = [(-z['score'], i, z) for i, z in enumerate(zones)]
    heapq.heapify(heap)
    remaining_capacity = [truck_capacity_kg] * num_trucks
    assignments = [[] for _ in range(num_trucks)]
    assigned_ids = set()
    while heap:
        neg_score, _, zone = heapq.heappop(heap)
        if zone['id'] in assigned_ids:
            continue
        best_truck = -1
        best_remaining = -1
        for t in range(num_trucks):
            if zone['demand_kg'] <= remaining_capacity[t] and remaining_capacity[t] > best_remaining:
                best_remaining = remaining_capacity[t]
                best_truck = t
        if best_truck >= 0:
            assignments[best_truck].append(zone['id'])
            remaining_capacity[best_truck] -= zone['demand_kg']
            assigned_ids.add(zone['id'])
    selected_zones = [z for z in zones if z['id'] in assigned_ids]
    total_kg = sum(z['demand_kg'] for z in selected_zones)
    total_urgency = sum(z['urgency'] for z in selected_zones)
    return selected_zones, assignments, total_kg, total_urgency

def nearest_neighbor_routing(zones, depot):
    if not zones:
        return [], 0.0, 0.0
    speed_kmh = 50.0
    unvisited = zones.copy()
    route = []
    current = depot
    total_km = 0.0
    while unvisited:
        closest = min(unvisited, key=lambda z: math.hypot(z['lat'] - current[0], z['lng'] - current[1]))
        dist_km = deg_to_km(math.hypot(closest['lat'] - current[0], closest['lng'] - current[1]))
        total_km += dist_km
        route.append(closest)
        current = (closest['lat'], closest['lng'])
        unvisited.remove(closest)
    back_km = deg_to_km(math.hypot(current[0] - depot[0], current[1] - depot[1]))
    total_km += back_km
    return route, total_km, total_km / speed_kmh

def plan_all_trucks(assignments, all_zones, depot):
    zone_dict = {z['id']: z for z in all_zones}
    truck_routes, truck_km, truck_hours = [], [], []
    for truck_zone_ids in assignments:
        if not truck_zone_ids:
            truck_routes.append([])
            truck_km.append(0.0)
            truck_hours.append(0.0)
            continue
        truck_zones = [zone_dict[zid] for zid in truck_zone_ids if zid in zone_dict]
        route, km, hours = nearest_neighbor_routing(truck_zones, depot)
        truck_routes.append(route)
        truck_km.append(km)
        truck_hours.append(hours)
    return truck_routes, truck_km, truck_hours

def decay_urgency(zones, hours_elapsed, served_ids):
    decayed = []
    for z in zones:
        z = z.copy()
        if z['id'] not in served_ids:
            decay_amount = hours_elapsed * 0.3
            z['urgency'] = min(10, round(z['urgency'] + decay_amount, 1))
        decayed.append(z)
    return decayed

def reveal_fog_zones(zones, fog_ids, seed):
    import random
    rng = random.Random(seed)
    results = {}
    for zid in fog_ids:
        results[zid] = rng.random() > 0.35
    return results
