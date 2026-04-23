import math

def deg_to_km(deg):
    #Converts the Euclidean distance in degrees to kilometers
    #1 degree latitude = 111 km approximately
    return deg * 111.0

def nearest_neighbor_routing(zones, depot):
    #zones: list of zone dicts with latitude and longitude
    #depot: tuple (lat, lng)
    #Returns (route, total_km, total_hours) where speed is set to 50 km/h
    if not zones:
        return [], 0.0, 0.0

    speed_kmh = 50.0  #average convoy speed for aid distribution
    unvisited = zones.copy()
    route = []
    current = depot
    total_km = 0.0

    while unvisited:
        #find the closest unvisited zone in degrees, then converts its total distance to km
        closest = min(unvisited, key=lambda z: math.hypot(z['lat'] - current[0], z['lng'] - current[1]))
        dist_deg = math.hypot(closest['lat'] - current[0], closest['lng'] - current[1])
        dist_km = deg_to_km(dist_deg)
        total_km += dist_km
        route.append(closest)
        current = (closest['lat'], closest['lng'])
        unvisited.remove(closest)

    #returns truck to depot
    dist_back_deg = math.hypot(current[0] - depot[0], current[1] - depot[1])
    dist_back_km = deg_to_km(dist_back_deg)
    total_km += dist_back_km

    total_hours = total_km / speed_kmh
    return route, total_km, total_hours


def plan_all_trucks(assignments, all_zones, depot):
    zone_dict = {z['id']: z for z in all_zones}
    truck_routes = []
    truck_km = []
    truck_hours = []
    for truck_zones_ids in assignments:
        if not truck_zones_ids:
            truck_routes.append([])
            truck_km.append(0.0)
            truck_hours.append(0.0)
            continue
        truck_zones = [zone_dict[zid] for zid in truck_zones_ids]
        route, km, hours = nearest_neighbor_routing(truck_zones, depot)
        truck_routes.append(route)
        truck_km.append(km)
        truck_hours.append(hours)
    return truck_routes, truck_km, truck_hours