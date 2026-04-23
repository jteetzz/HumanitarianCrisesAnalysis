import math
from greedy_select import greedy_selection
from delivery_optimizer import plan_all_trucks, deg_to_km

def explain_priority(zones):
    print("Affected zones Sorted by Priority:")
    print("Zone | Demand (kg) | Urgency (1-10) | Risk (1-5) | Distance (km) | Priority Score")
    print("-----|-------------|----------------|------------|---------------|---------------")
    for z in sorted(zones, key=lambda x: x.get('score', 0), reverse=True):
        dist_km = deg_to_km(z['distance'])
        print(
            f" {z['id']:3} | {z['demand_kg']:11} | {z['urgency']:14} | {z['risk']:10} | {dist_km:13.1f} | {z['score']:.3f}")
    print("")

def explain_assignments(assignments, zones, truck_capacity_kg):
    zone_dict = {z['id']: z for z in zones}
    print("\nTruck Zone Assignment reasoning")
    for t, zone_ids in enumerate(assignments):
        if not zone_ids:
            print(f"Truck {t + 1}: No zones assigned (all remaining zones exceeded capacity or no zones left)")
            continue
        print(f"\nTruck {t + 1}:")
        remaining_cap = truck_capacity_kg
        for zid in zone_ids:
            zone = zone_dict[zid]
            print(f"  - Zone {zid}: priority score {zone['score']:.3f}, demand {zone['demand_kg']} kg")
            print(f"    Fit within remaining capacity ({remaining_cap} kg)")
            remaining_cap -= zone['demand_kg']
        print(f"    Remaining capacity after loading: {remaining_cap} kg")
    print("")

def explain_routes(routes, km_list, hours_list, assignments, zones):
    zone_dict = {z['id']: z for z in zones}
    print("Truck Route details - ")
    for t, (route, km, hours) in enumerate(zip(routes, km_list, hours_list)):
        if not route:
            print(f"Truck {t + 1}: No route")
            continue
        print(f"\nTruck {t + 1}: assigned zones {assignments[t]}")
        print(f"  Route order: start at depot")
        cumulative_km = 0
        prev = (0.0, 0.0)  #depot
        for idx, zone in enumerate(route):
            dist_deg = math.hypot(zone['lat'] - prev[0], zone['lng'] - prev[1])
            seg_km = deg_to_km(dist_deg)
            cumulative_km += seg_km
            print(f"    {idx + 1}. Go to Zone {zone['id']} – {seg_km:.1f} km, arrival total {cumulative_km:.1f} km")
            prev = (zone['lat'], zone['lng'])
        dist_back_deg = math.hypot(prev[0] - 0.0, prev[1] - 0.0)
        back_km = deg_to_km(dist_back_deg)
        cumulative_km += back_km
        print(f"    Then return to depot – {back_km:.1f} km, total route {cumulative_km:.1f} km")
        print(f"  Total travel distance: {km:.1f} km, estimated time: {hours:.1f} hours (at 50 km/h)")
    print("")

if __name__ == "__main__":
    depot = (0.0, 0.0)

    zones = [
        {'id': 'A', 'lat': 1.0, 'lng': 1.0, 'demand_kg': 12000, 'urgency': 10, 'risk': 5},
        {'id': 'B', 'lat': 2.0, 'lng': 2.0, 'demand_kg': 8000, 'urgency': 8, 'risk': 4},
        {'id': 'C', 'lat': 3.0, 'lng': 3.0, 'demand_kg': 15000, 'urgency': 7, 'risk': 3},
        {'id': 'D', 'lat': 4.0, 'lng': 4.0, 'demand_kg': 6000, 'urgency': 6, 'risk': 4},
        {'id': 'E', 'lat': -1.0, 'lng': -1.0, 'demand_kg': 10000, 'urgency': 9, 'risk': 5}, ]

    truck_capacity_kg = 18000
    num_trucks = 3

    print("Emergency Aid Distribution Optimizer - ")
    print("")

    selected, assignments, total_kg, total_urgency = greedy_selection(zones, truck_capacity_kg, num_trucks, depot)
    explain_priority(zones)
    explain_assignments(assignments, zones, truck_capacity_kg)

    routes, km_list, hours_list = plan_all_trucks(assignments, zones, depot)
    explain_routes(routes, km_list, hours_list, assignments, zones)

    total_demand = sum(z['demand_kg'] for z in zones)
    total_time_all_trucks = sum(hours_list)  #sum of estimated hours taken for delivery of aid for all trucks
    print("Summary")
    print(f"Total aid delivered: {total_kg} kg ({total_kg / 1000:.1f} metric tons)")
    print(f"Requested aid amount: {total_demand} kg")
    print(f"Coverage: {total_kg / total_demand * 100:.1f}% of requested aid")
    print(f"Total urgency sum (sum of urgencies of delivered zones): {total_urgency}")
    print(f"Total delivery time for all trucks (combined): {total_time_all_trucks:.1f} hours")
    print("")

    print("Realtime re-planning example")
    print("Scenario: Zone A becomes inaccessible due to security incident")
    original_total_demand = total_demand  #store original requested aid before blocking zones
    remaining_zones = [z for z in zones if z['id'] != 'A']
    selected2, assignments2, total_kg2, total_urgency2 = greedy_selection(remaining_zones, truck_capacity_kg, num_trucks, depot)
    routes2, km_list2, hours_list2 = plan_all_trucks(assignments2, remaining_zones, depot)

    print("Remaining zones after blocking zone A:")
    explain_priority(remaining_zones)
    explain_assignments(assignments2, remaining_zones, truck_capacity_kg)
    explain_routes(routes2, km_list2, hours_list2, assignments2, remaining_zones)

    total_demand2 = sum(z['demand_kg'] for z in remaining_zones)
    total_time_all_trucks2 = sum(hours_list2)
    print("New summary")
    print(f"Total aid delivered: {total_kg2} kg ({total_kg2 / 1000:.1f} metric tons)")
    print(f"Requested aid amount (original, before blocking A): {original_total_demand} kg")
    print(f"Requested aid amount (after blocking A, remaining zones): {total_demand2} kg")
    print(f"Coverage of remaining demand: {total_kg2 / total_demand2 * 100:.1f}%")
    print(f"Coverage of original requested aid: {total_kg2 / original_total_demand * 100:.1f}%")
    print(f"Total urgency sum: {total_urgency2}")
    print(f"Total delivery time for all trucks (combined): {total_time_all_trucks2:.1f} hours")