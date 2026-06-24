import heapq
from typing import Optional
from model import Zone, Connection, ZoneType


# Coût de déplacement selon le type de zone de destination
ZONE_COST: dict[ZoneType, int] = {
    ZoneType.NORMAL: 1,
    ZoneType.PRIORITY: 1,       # même coût mais préféré (via heuristique)
    ZoneType.RESTRICTED: 2,     # coûte 2 tours
    ZoneType.BLOCKED: 999,      # inaccessible
}


def build_adjacency(
    connections: list[Connection],
) -> dict[str, list[tuple[str, int]]]:
    """
    Construit une liste d'adjacence bidirectionnelle à partir des connexions.
    Chaque entrée : zone -> [(voisin, capacité_lien), ...]
    """
    graph: dict[str, list[tuple[str, int]]] = {}
    for conn in connections:
        z1, z2 = conn.first_zone, conn.second_zone
        cap = conn.max_link_capacity
        graph.setdefault(z1, []).append((z2, cap))
        graph.setdefault(z2, []).append((z1, cap))
    return graph


def dijkstra(
    zones: dict[str, Zone],
    adjacency: dict[str, list[tuple[str, int]]],
    start: str,
    end: str,
) -> Optional[list[str]]:
    """
    Dijkstra modifié :
    - Ignore les zones BLOCKED
    - Coût selon le type de la zone de DESTINATION
    - Les zones PRIORITY sont légèrement favorisées (coût réduit de 0.1)
      pour qu'elles soient préférées à coût égal
    Retourne le chemin optimal (liste de noms de zones) ou None si impossible.
    """
    # (coût_accumulé, zone_courante, chemin_parcouru)
    heap: list[tuple[float, str, list[str]]] = [(0.0, start, [start])]
    visited: set[str] = set()

    while heap:
        cost, current, path = heapq.heappop(heap)

        if current in visited:
            continue
        visited.add(current)

        if current == end:
            return path

        for neighbor, _ in adjacency.get(current, []):
            if neighbor in visited:
                continue
            zone = zones.get(neighbor)
            if zone is None:
                continue
            # Zones bloquées : on ne peut jamais y entrer
            if zone.zone_type == ZoneType.BLOCKED:
                continue

            base_cost = ZONE_COST[zone.zone_type]
            # Légère réduction pour favoriser les zones PRIORITY
            extra = -0.1 if zone.zone_type == ZoneType.PRIORITY else 0.0
            new_cost = cost + base_cost + extra

            heapq.heappush(heap, (new_cost, neighbor, path + [neighbor]))

    return None


def find_all_paths(
    zones: dict[str, Zone],
    adjacency: dict[str, list[tuple[str, int]]],
    start: str,
    end: str,
    max_paths: int = 10,
) -> list[list[str]]:
    """
    Trouve jusqu'à max_paths chemins distincts via DFS,
    en excluant les zones BLOCKED.
    Trie les résultats par coût total (somme des coûts de zone).
    Utilisé pour distribuer les drones sur plusieurs chemins.
    """
    all_paths: list[list[str]] = []
    current_path: list[str] = [start]

    def dfs(node: str) -> None:
        if len(all_paths) >= max_paths:
            return
        if node == end:
            all_paths.append(list(current_path))
            return
        for neighbor, _ in adjacency.get(node, []):
            if neighbor in current_path:
                continue
            zone = zones.get(neighbor)
            if zone is None or zone.zone_type == ZoneType.BLOCKED:
                continue
            current_path.append(neighbor)
            dfs(neighbor)
            current_path.pop()

    dfs(start)

    # Trie par coût total du chemin
    def path_cost(path: list[str]) -> float:
        total: float = 0.0
        for name in path[1:]:            # on ignore le coût du start
            zone = zones[name]
            base = ZONE_COST[zone.zone_type]
            extra = -0.1 if zone.zone_type == ZoneType.PRIORITY else 0.0
            total += base + extra
        return total

    return sorted(all_paths, key=path_cost)


def assign_paths_to_drones(
    nb_drones: int,
    zones: dict[str, Zone],
    connections: list[Connection],
    start: str,
    end: str,
) -> list[list[str]]:
    """
    Attribue un chemin optimal à chaque drone.
    - Trouve tous les chemins disponibles
    - Distribue les drones en round-robin sur ces chemins
    - Si aucun chemin trouvé, retourne une liste vide
    """
    adjacency = build_adjacency(connections)
    paths = find_all_paths(zones, adjacency, start, end, max_paths=10)

    if not paths:
        return []

    # Distribution round-robin : drone i -> paths[i % len(paths)]
    assigned: list[list[str]] = []
    for i in range(nb_drones):
        assigned.append(paths[i % len(paths)])

    return assigned
