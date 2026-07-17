"""Spatio-temporal path search algorithm with reservation table."""

from collections import deque
from model import Zone, Connection, ZoneType


class SpaceTimeReservation:
    """Maintains a reservation table for zones and connections over time."""

    def __init__(self) -> None:
        """Initialize the reservation table."""
        # Clé: (zone_name, turn) -> Valeur: nombre de drones
        self.zone_bookings: dict[tuple[str, int], int] = {}
        # Clé: (frozenset_liaison, turn) -> Valeur: nombre de drones
        self.link_bookings: dict[tuple[frozenset[str], int], int] = {}

    def is_zone_free(self, zone: str, turn: int, max_cap: int) -> bool:
        """Check if a zone has available capacity at a given turn.

        Args:
            zone (str): The name of the zone to check.
            turn (int): The turn number to check for availability.
            max_cap (int): The maximum capacity of the zone.

        Returns:
            bool: True if the zone has available capacity, False otherwise.
        """
        current_occupancy = self.zone_bookings.get((zone, turn), 0)
        if current_occupancy < max_cap:
            return True
        return False

    def is_link_free(
        self, zone_a: str, zone_b: str, turn: int, max_cap: int
    ) -> bool:
        """Check if a connection has available capacity at a given turn.

        Args:
            zone_a (str): The name of the first zone.
            zone_b (str): The name of the second zone.
            turn (int): The turn number to check for availability.
            max_cap (int): The maximum capacity of the connection.

        Returns:
            bool:
                True if the connection has available capacity, False otherwise.
        """
        key = frozenset((zone_a, zone_b))
        current_occupancy = self.link_bookings.get((key, turn), 0)
        if current_occupancy < max_cap:
            return True
        return False

    def reserve_zone(self, zone: str, turn: int) -> None:
        """Reserve a zone for a specific turn.

        Args:
            zone (str): The name of the zone to reserve.
            turn (int): The turn number to reserve the zone for.
        """
        key = (zone, turn)
        current = self.zone_bookings.get(key, 0)
        self.zone_bookings[key] = current + 1

    def reserve_link(self, zone_a: str, zone_b: str, turn: int) -> None:
        """Reserve a link for a specific turn.

        Args:
            zone_a (str): The name of the first zone.
            zone_b (str): The name of the second zone.
            turn (int): The turn number to reserve the link for.
        """
        key = (frozenset((zone_a, zone_b)), turn)
        current = self.link_bookings.get(key, 0)
        self.link_bookings[key] = current + 1


class Pathfinder:
    """Implement a spatio-temporal pathfinding algorithm for drones."""

    def __init__(
        self, zones: dict[str, Zone], connections: list[Connection]
    ) -> None:
        """Initialize the Pathfinder with zones and connections.

        Args:
            zones (dict[str, Zone]):
                A dictionary mapping zone names to Zone objects.
            connections (list[Connection]):
                A list of Connection objects representing the connections
                between zones.
        """
        self.zones = zones
        self.connections = connections
        self.adjacency_list: dict[str, list[str]] = {}
        self.connections_map: dict[frozenset[str], Connection] = {}
        self._build_graph()

    def _build_graph(self) -> None:
        """Build the adjacency list and connection mapping for the graph."""
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

    def _get_zone_capacity(
        self, zone_name: str, start_zone: str, end_zone: str, total_drones: int
    ) -> int:
        """Return the maximum capacity of a zone.

        Args:
            zone_name (str): The name of the zone to check.
            start_zone (str): The name of the starting zone.
            end_zone (str): The name of the ending zone.
            total_drones (int): The total number of drones in the simulation.
        """
        if zone_name == start_zone or zone_name == end_zone:
            return total_drones
        return self.zones[zone_name].max_drones

    def _get_link_capacity(self, zone_a: str, zone_b: str) -> int:
        """Return the maximum capacity of a connecting link.

        Args:
            zone_a (str): The name of the first zone.
            zone_b (str): The name of the second zone.
        """
        key = frozenset((zone_a, zone_b))
        conn = self.connections_map.get(key)
        if conn is not None:
            return conn.max_link_capacity
        return 1

    def find_space_time_path(
        self,
        start: str,
        end: str,
        total_drones: int,
        reservation: SpaceTimeReservation,
    ) -> list[tuple[int, str, str | None]]:
        """Find a spatio-temporal path from the start zone to the end zone.

        Args:
            start (str): The name of the starting zone.
            end (str): The name of the destination zone.
            total_drones (int): The total number of drones in the simulation.
            reservation (SpaceTimeReservation):
                The reservation table to check for zone and link availability.

        Returns:
            list[tuple[int, str, str | None]]:
                A list of tuples representing the spatio-temporal path.
        """
        # Queue contient des éléments:
        # (current_zone, current_turn, path_history)
        queue: deque[tuple[str, int, list[tuple[int, str, str | None]]]] = (
            deque()
        )
        queue.append((start, 0, [(0, start, None)]))

        # Pour éviter les boucles redondantes dans l'espace-temps
        visited: set[tuple[str, int]] = set()
        visited.add((start, 0))

        max_search_turns = 200

        while len(queue) > 0:
            curr_zone, curr_turn, curr_path = queue.popleft()

            if curr_zone == end:
                return curr_path

            if curr_turn >= max_search_turns:
                continue

            # Option 1: Rester sur place
            # (attente stratégique dans la zone actuelle)
            next_turn = curr_turn + 1
            z_cap = self._get_zone_capacity(
                curr_zone, start, end, total_drones
            )

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
                if not reservation.is_link_free(
                    curr_zone, neighbor, next_turn, l_cap
                ):
                    continue

                if neighbor_zone.zone_type == ZoneType.RESTRICTED:
                    # Mouvement en 2 tours vers une zone restreinte
                    arrival_turn = curr_turn + 2
                    dest_cap = self._get_zone_capacity(
                        neighbor, start, end, total_drones
                    )

                    # Vérification de la disponibilité de
                    # la destination au moment de l'arrivée
                    if reservation.is_zone_free(
                        neighbor, arrival_turn, dest_cap
                    ):
                        if (neighbor, arrival_turn) not in visited:
                            visited.add((neighbor, arrival_turn))
                            new_path = list(curr_path)
                            # Au tour next_turn, le drone est sur la connexion
                            connection_name = f"{curr_zone}-{neighbor}"
                            new_path.append(
                                (next_turn, neighbor, connection_name)
                            )
                            # Au tour arrival_turn,
                            # le drone arrive dans la zone
                            new_path.append((arrival_turn, neighbor, None))
                            queue.append((neighbor, arrival_turn, new_path))
                else:
                    # Mouvement en 1 tour (zone normale ou prioritaire)
                    dest_cap = self._get_zone_capacity(
                        neighbor, start, end, total_drones
                    )
                    if reservation.is_zone_free(neighbor, next_turn, dest_cap):
                        if (neighbor, next_turn) not in visited:
                            visited.add((neighbor, next_turn))
                            new_path = list(curr_path)
                            new_path.append((next_turn, neighbor, None))
                            queue.append((neighbor, next_turn, new_path))

        return []

    def assign_paths(
        self, start: str, end: str, nb_drones: int
    ) -> list[list[tuple[int, str, str | None]]]:
        """Assign spatio-temporal paths to multiple drones.

        Args:
            start (str): The name of the starting zone.
            end (str): The name of the destination zone.
            nb_drones (int): The number of drones to assign paths to.

        Returns:
            list[list[tuple[int, str, str | None]]]:
                A list of spatio-temporal paths for each drone.
        """
        reservation = SpaceTimeReservation()
        all_drones_paths: list[list[tuple[int, str, str | None]]] = []

        for _ in range(nb_drones):
            path = self.find_space_time_path(
                start, end, nb_drones, reservation
            )
            all_drones_paths.append(path)

            # Enregistrer les réservations de ce drone pour bloquer les places
            # aux suivants. On compare deux étapes consécutives pour savoir
            # si le drone a bougé (mouvement normal) ou attendu sur place.
            for step_idx in range(1, len(path)):
                prev_step = path[step_idx - 1]
                curr_step = path[step_idx]

                turn = curr_step[0]
                zone_name = curr_step[1]
                connection_name = curr_step[2]
                prev_zone_name = prev_step[1]

                if connection_name is not None:
                    # Transit restricted : réserve la connexion traversée
                    # (les noms de zones n'ont pas de tiret, le split est sûr)
                    parts = connection_name.split("-")
                    reservation.reserve_link(parts[0], parts[1], turn)
                else:
                    # Présence normale dans la zone : réserve la zone
                    reservation.reserve_zone(zone_name, turn)

                    # Si le drone a réellement bougé (pas une attente),
                    # réserve aussi la connexion traversée ce tour.
                    # Cela respecte max_link_capacity pour
                    # les mouvements normaux.
                    if zone_name != prev_zone_name:
                        reservation.reserve_link(
                            prev_zone_name, zone_name, turn
                        )

        return all_drones_paths
