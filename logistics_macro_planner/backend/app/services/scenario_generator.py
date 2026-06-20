import itertools
from ..utils.geo_utils import haversine_km

def cluster_deliveries(deliveries: list[dict], max_cluster_size: int = 6) -> list[list[dict]]:
    # Start with each delivery as a separate cluster
    clusters = [[d] for d in deliveries]
    
    while True:
        best_pair = None
        min_dist = float('inf')
        
        # Find the two closest clusters that can be merged
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                if len(clusters[i]) + len(clusters[j]) > max_cluster_size:
                    continue
                
                # Calculate distance between centroids of clusters i and j
                c1_lat = sum(d['lat'] for d in clusters[i]) / len(clusters[i])
                c1_lon = sum(d['lon'] for d in clusters[i]) / len(clusters[i])
                c2_lat = sum(d['lat'] for d in clusters[j]) / len(clusters[j])
                c2_lon = sum(d['lon'] for d in clusters[j]) / len(clusters[j])
                
                dist = haversine_km(c1_lat, c1_lon, c2_lat, c2_lon)
                if dist < min_dist:
                    min_dist = dist
                    best_pair = (i, j)
                    
        if best_pair is None:
            break
            
        i, j = best_pair
        # Merge cluster j into cluster i
        clusters[i].extend(clusters[j])
        clusters.pop(j)
        
    return clusters

def generate_scenarios(deliveries: list[dict], max_stops_per_route: int = 6) -> list[list[dict]]:
    """
    Generates combinations of deliveries.
    Uses geographical clustering to prevent combinatorial explosion when N is large.
    """
    if not deliveries:
        return []
        
    # Group deliveries into clusters of max size 6
    clusters = cluster_deliveries(deliveries, max_cluster_size=max_stops_per_route)
    
    scenarios = []
    for cluster in clusters:
        # Generate combinations within each cluster
        for r in range(1, len(cluster) + 1):
            for combo in itertools.combinations(cluster, r):
                scenarios.append(list(combo))
                
    return scenarios

