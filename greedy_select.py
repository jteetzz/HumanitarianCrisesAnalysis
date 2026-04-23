import math

def greedy_selection(zones, truck_capacity_kg, num_trucks, depot):
    #zones: list of dictionaries with 'id', 'lat', 'lng', 'demand_kg', 'urgency' and 'risk'
    #depot: tuple (lat, lng)
    #Returns (selected_zones, assignments, total_kg, total_urgency)
    for zone in zones:
        dx = zone['lng'] - depot[1]
        dy = zone['lat'] - depot[0]
        zone['distance'] = math.hypot(dx, dy)
        if zone['distance'] == 0:
            zone['distance'] = 0.001
        zone['score'] = zone['urgency'] / (zone['distance'] * zone['risk'])

    sorted_zones = sorted(zones, key=lambda z: z['score'], reverse=True)
    remaining_capacity = [truck_capacity_kg] * num_trucks
    assignments = [[] for _ in range(num_trucks)]

    for zone in sorted_zones:
        for t in range(num_trucks):
            if zone['demand_kg'] <= remaining_capacity[t]:
                assignments[t].append(zone['id'])
                remaining_capacity[t] -= zone['demand_kg']
                break

    selected_ids = set()
    for truck_list in assignments:
        selected_ids.update(truck_list)
    selected_zones = [z for z in zones if z['id'] in selected_ids]

    total_kg = sum(z['demand_kg'] for z in selected_zones)
    total_urgency = sum(z['urgency'] for z in selected_zones)
    return selected_zones, assignments, total_kg, total_urgency