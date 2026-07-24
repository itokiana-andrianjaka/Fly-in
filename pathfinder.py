"""Module for implementing spatio-temporal pathfinding algorithms."""

from collections import deque
from model import Zone, Connection, ZoneType

from space_time import SpaceTimeReservation


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
        self._load_info()

    def _load_info(self) -> None:
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
        queue: deque[
            tuple[
                str,
                int,
                list[tuple[int, str, str | None]],
                frozenset[str],
            ]
        ] = deque()
        initial_visited: frozenset[str] = frozenset({start})
        queue.append((start, 0, [(0, start, None)], initial_visited))

        visited: set[tuple[str, int, frozenset[str]]] = set()
        visited.add((start, 0, initial_visited))

        max_search_turns = 200

        while len(queue) > 0:
            curr_zone, curr_turn, curr_path, visited_zones = queue.popleft()

            if curr_zone == end:
                return curr_path

            if curr_turn >= max_search_turns:
                continue

            next_turn = curr_turn + 1
            z_cap = self._get_zone_capacity(
                curr_zone, start, end, total_drones
            )

            if reservation.is_zone_free(curr_zone, next_turn, z_cap):
                wait_state = (curr_zone, next_turn, visited_zones)
                if wait_state not in visited:
                    visited.add(wait_state)
                    new_path = list(curr_path)
                    new_path.append((next_turn, curr_zone, None))
                    queue.append(
                        (curr_zone, next_turn, new_path, visited_zones)
                    )

            neighbors = self.adjacency_list.get(curr_zone, [])

            neighbors = sorted(
                neighbors,
                key=lambda z: self.zones[z].zone_type != ZoneType.PRIORITY,
            )
            for neighbor in neighbors:
                neighbor_zone = self.zones[neighbor]
                if neighbor_zone.zone_type == ZoneType.BLOCKED:
                    continue

                if neighbor in visited_zones:
                    continue

                l_cap = self._get_link_capacity(curr_zone, neighbor)
                if not reservation.is_link_free(
                    curr_zone, neighbor, next_turn, l_cap
                ):
                    continue

                if neighbor_zone.zone_type == ZoneType.RESTRICTED:
                    arrival_turn = curr_turn + 2
                    dest_cap = self._get_zone_capacity(
                        neighbor, start, end, total_drones
                    )

                    if reservation.is_zone_free(
                        neighbor, arrival_turn, dest_cap
                    ):
                        new_visited_zones = set(visited_zones)
                        new_visited_zones.add(neighbor)
                        new_visited_state = (
                            neighbor,
                            arrival_turn,
                            frozenset(new_visited_zones),
                        )
                        if new_visited_state not in visited:
                            visited.add(new_visited_state)
                            new_path = list(curr_path)
                            connection_name = f"{curr_zone}-{neighbor}"
                            new_path.append(
                                (next_turn, neighbor, connection_name)
                            )
                            new_path.append((arrival_turn, neighbor, None))
                            queue.append(
                                (
                                    neighbor,
                                    arrival_turn,
                                    new_path,
                                    frozenset(new_visited_zones),
                                )
                            )
                else:
                    dest_cap = self._get_zone_capacity(
                        neighbor, start, end, total_drones
                    )
                    if reservation.is_zone_free(neighbor, next_turn, dest_cap):
                        new_visited_zones = set(visited_zones)
                        new_visited_zones.add(neighbor)
                        new_visited_state = (
                            neighbor,
                            next_turn,
                            frozenset(new_visited_zones),
                        )
                        if new_visited_state not in visited:
                            visited.add(new_visited_state)
                            new_path = list(curr_path)
                            new_path.append((next_turn, neighbor, None))
                            queue.append(
                                (
                                    neighbor,
                                    next_turn,
                                    new_path,
                                    frozenset(new_visited_zones),
                                )
                            )

        return []

    def assign_paths(
        self, start: str, end: str, nb_drones: int
    ) -> tuple[list[list[tuple[int, str, str | None]]], SpaceTimeReservation]:
        """Assign spatio-temporal paths to multiple drones.

        Args:
            start (str): The name of the starting zone.
            end (str): The name of the destination zone.
            nb_drones (int): The number of drones to assign paths to.

        Returns:
            tuple[list[list[tuple[int, str, str | None]]],
                    SpaceTimeReservation]:
                A tuple containing the list of spatio-temporal paths for
                each drone and the reservation object.
        """
        self.reservation = SpaceTimeReservation()
        all_drones_paths: list[list[tuple[int, str, str | None]]] = []

        for _ in range(nb_drones):
            path = self.find_space_time_path(
                start, end, nb_drones, self.reservation
            )
            all_drones_paths.append(path)

            for step_idx in range(1, len(path)):
                prev_step = path[step_idx - 1]
                curr_step = path[step_idx]

                turn = curr_step[0]
                zone_name = curr_step[1]
                connection_name = curr_step[2]
                prev_zone_name = prev_step[1]

                if connection_name is not None:
                    parts = connection_name.split("-")
                    self.reservation.reserve_link(parts[0], parts[1], turn)
                else:
                    self.reservation.reserve_zone(zone_name, turn)

                    if zone_name != prev_zone_name:
                        self.reservation.reserve_link(
                            prev_zone_name, zone_name, turn
                        )

        return all_drones_paths, self.reservation
