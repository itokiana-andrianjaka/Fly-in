# Fichier: pathfinder.py
"""Algorithme de recherche de chemins spatio-temporels avec table de réservation."""

from collections import deque
from typing import Optional
from model import Zone, Connection, ZoneType

class SpaceTimeReservation:
    """
    Cette classe existe pour centraliser et suivre les réservations d'occupation
    des zones et des connexions à chaque tour de simulation précis. Elle empêche
    les collisions en s'assurant qu'aucun drone ne dépasse les capacités requises.
    """

    def __init__(self) -> None:
        # Clé: (zone_name, turn) -> Valeur: nombre de drones
        self.zone_bookings: dict[tuple[str, int], int] = {}
        # Clé: (frozenset_liaison, turn) -> Valeur: nombre de drones
        self.link_bookings: dict[tuple[frozenset[str], int], int] = {}

    def is_zone_free(self, zone: str, turn: int, max_cap: int) -> bool:
        """Vérifie si une zone a encore de la capacité disponible à un tour donné."""
        current_occupancy = self.zone_bookings.get((zone, turn), 0)
        if current_occupancy < max_cap:
            return True
        return False

    def is_link_free(self, zone_a: str, zone_b: str, turn: int, max_cap: int) -> bool:
        """Vérifie si une connexion a encore de la capacité disponible à un tour donné."""
        key = frozenset((zone_a, zone_b))
        current_occupancy = self.link_bookings.get((key, turn), 0)
        if current_occupancy < max_cap:
            return True
        return False

    def reserve_zone(self, zone: str, turn: int) -> None:
        """Inscrit une réservation pour une zone à un tour spécifique."""
        key = (zone, turn)
        current = self.zone_bookings.get(key, 0)
        self.zone_bookings[key] = current + 1

    def reserve_link(self, zone_a: str, zone_b: str, turn: int) -> None:
        """Inscrit une réservation pour une connexion à un tour spécifique."""
        key = (frozenset((zone_a, zone_b)), turn)
        current = self.link_bookings.get(key, 0)
        self.link_bookings[key] = current + 1


class Pathfinder:
    """
    Cette classe existe pour calculer un itinéraire spatio-temporel optimal pour
    chaque drone individuel. Elle utilise une recherche en largeur (BFS) étendue
    au temps, garantissant l'absence de conflits et minimisant le nombre total de tours.
    """

    def __init__(self, zones: dict[str, Zone], connections: list[Connection]) -> None:
        self.zones = zones
        self.connections = connections
        self.adjacency_list: dict[str, list[str]] = {}
        self.connections_map: dict[frozenset[str], Connection] = {}
        self._build_graph()

    def _build_graph(self) -> None:
        """Construit les structures de données du graphe pour faciliter l'accès."""
        for zone_name in self.zones:
            self.adjacency_list[zone_name] = []

        for connection in self.connections:
            z1 = connection.first_zone
            z2 = connection.second_zone
            if z1 in self.adjacency_list and z2 in self.adjacency_list:
                self.adjacency_list[z1].append(z2)
                self.adjacency_list[z2].append(z1)
            
            key = frozenset((z1, z2))
            self.connections_map[key] = connection

    def _get_zone_capacity(self, zone_name: str, start_zone: str, end_zone: str, total_drones: int) -> int:
        """Retourne la capacité maximale d'une zone avec exceptions pour départ/arrivée."""
        if zone_name == start_zone or zone_name == end_zone:
            return total_drones
        return self.zones[zone_name].max_drones

    def _get_link_capacity(self, zone_a: str, zone_b: str) -> int:
        """Retourne la capacité maximale d'une liaison connectrice."""
        key = frozenset((zone_a, zone_b))
        conn = self.connections_map.get(key)
        if conn is not None:
            return conn.max_link_capacity
        return 1

    def find_space_time_path(
        self, start: str, end: str, total_drones: int, reservation: SpaceTimeReservation
    ) -> list[tuple[int, str, Optional[str]]]:
        """
        Trouve le chemin le plus court dans l'espace-temps pour un drone unique.
        Retourne une liste de tuples: (tour, nom_zone, nom_connexion_si_transit).
        """
        # Queue contient des éléments: (current_zone, current_turn, path_history)
        queue = deque()
        queue.append((start, 0, [(0, start, None)]))
        
        # Pour éviter les boucles redondantes dans l'espace-temps
        visited = set()
        visited.add((start, 0))

        max_search_turns = 200

        while len(queue) > 0:
            curr_zone, curr_turn, curr_path = queue.popleft()

            if curr_zone == end:
                return curr_path

            if curr_turn >= max_search_turns:
                continue

            # Option 1: Rester sur place (attente stratégique dans la zone actuelle)
            next_turn = curr_turn + 1
            z_cap = self._get_zone_capacity(curr_zone, start, end, total_drones)
            
            if reservation.is_zone_free(curr_zone, next_turn, z_cap):
                if (curr_zone, next_turn) not in visited:
                    visited.add((curr_zone, next_turn))
                    new_path = list(curr_path)
                    new_path.append((next_turn, curr_zone, None))
                    queue.append((curr_zone, next_turn, new_path))

            # Option 2: Se déplacer vers une zone voisine connectée
            neighbors = self.adjacency_list.get(curr_zone, [])
            for neighbor in neighbors:
                neighbor_zone = self.zones[neighbor]
                if neighbor_zone.zone_type == ZoneType.BLOCKED:
                    continue

                # Vérification de la capacité de la liaison pour ce tour
                l_cap = self._get_link_capacity(curr_zone, neighbor)
                if not reservation.is_link_free(curr_zone, neighbor, next_turn, l_cap):
                    continue

                if neighbor_zone.zone_type == ZoneType.RESTRICTED:
                    # Mouvement en 2 tours vers une zone restreinte
                    arrival_turn = curr_turn + 2
                    dest_cap = self._get_zone_capacity(neighbor, start, end, total_drones)
                    
                    # Vérification de la disponibilité de la destination au moment de l'arrivée
                    if reservation.is_zone_free(neighbor, arrival_turn, dest_cap):
                        if (neighbor, arrival_turn) not in visited:
                            visited.add((neighbor, arrival_turn))
                            new_path = list(curr_path)
                            # Au tour next_turn, le drone est sur la connexion
                            connection_name = f"{curr_zone}-{neighbor}"
                            new_path.append((next_turn, neighbor, connection_name))
                            # Au tour arrival_turn, le drone arrive dans la zone
                            new_path.append((arrival_turn, neighbor, None))
                            queue.append((neighbor, arrival_turn, new_path))
                else:
                    # Mouvement en 1 tour (zone normale ou prioritaire)
                    dest_cap = self._get_zone_capacity(neighbor, start, end, total_drones)
                    if reservation.is_zone_free(neighbor, next_turn, dest_cap):
                        if (neighbor, next_turn) not in visited:
                            visited.add((neighbor, next_turn))
                            new_path = list(curr_path)
                            new_path.append((next_turn, neighbor, None))
                            queue.append((neighbor, next_turn, new_path))

        return []

    def assign_paths(self, start: str, end: str, nb_drones: int) -> list[list[tuple[int, str, Optional[str]]]]:
        """Calcule et planifie les trajectoires de toute la flotte de drones."""
        reservation = SpaceTimeReservation()
        all_drones_paths = []

        for i in range(nb_drones):
            path = self.find_space_time_path(start, end, nb_drones, reservation)
            all_drones_paths.append(path)

            # Enregistrer les réservations de ce drone pour bloquer les places aux suivants
            for step in path:
                turn = step[0]
                zone_name = step[1]
                connection_name = step[2]

                if turn == 0:
                    continue

                if connection_name is not None:
                    # Le drone est en transit sur une connexion
                    parts = connection_name.split("-")
                    reservation.reserve_link(parts[0], parts[1], turn)
                else:
                    # Le drone est présent de manière stable dans une zone
                    reservation.reserve_zone(zone_name, turn)

        return all_drones_paths