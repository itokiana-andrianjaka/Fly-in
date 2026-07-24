"""Simulation module for managing drone movements and generating logs."""

from dataclasses import dataclass

from model import Connection
from model import Zone
from space_time import SpaceTimeReservation


@dataclass
class Move:
    """Represents a drone movement with capacity details."""

    drone_id: int
    target: str
    is_connection: bool
    current: int = 1
    max_capacity: int = 1


class TurnLog:
    """Represents the log of drone movements for a single turn."""

    def __init__(self, turn_number: int) -> None:
        """Initialize the turn log with a turn number.

        Args:
            turn_number (int): The current turn number in the simulation.
        """
        self.turn_number = turn_number
        self.moves: list[Move] = []

    def add_move(
        self,
        drone_id: int,
        target: str,
        is_connection: bool,
        current: int = 1,
        max_capacity: int = 1,
    ) -> None:
        """Add a move to the turn log.

        Args:
            drone_id (int): The ID of the drone making the move.
            target (str): The target zone or connection for the move.
            is_connection (bool):
                True if the target is a connection, False if it's a zone
            current (int, optional):
                The current capacity of the drone. Defaults to 1.
            max_capacity (int, optional):
                The maximum capacity of the drone. Defaults to 1.
        """
        self.moves.append(
            Move(
                drone_id=drone_id,
                target=target,
                is_connection=is_connection,
                current=current,
                max_capacity=max_capacity,
            )
        )

    def render(self) -> str:
        """Render the turn log as a string.

        Returns:
            str:
                A string representation of the turn log, formatted as
                "D<drone_id>-<target>" for each move, separated by spaces.
        """
        return " ".join(
            f"D{move.drone_id}-{move.target}" for move in self.moves
        )

    def is_empty(self) -> bool:
        """Check if the turn log is empty.

        Returns:
            bool:
                True if there are no moves recorded for this turn,
                False otherwise.
        """
        return len(self.moves) == 0


class Simulator:
    """Simulate the movement of drones through zones and connections."""

    def __init__(
        self,
        start_zone: str,
        end_zone: str,
        drone_paths: list[list[tuple[int, str, str | None]]],
        reservation: SpaceTimeReservation | None = None,
        zones: dict[str, Zone] | None = None,
        connections: list[Connection] | None = None,
    ) -> None:
        """Initialize the simulator.

        Args:
            start_zone (str): The starting zone for the drones.
            end_zone (str): The ending zone for the drones.
            drone_paths (list[list[tuple[int, str, str | None]]]):
                A list of paths for each drone, where each path is a list of
                tuples containing the turn number, zone, and connection.
            reservation SpaceTimeReservation | None = None):
                An optional reservation system for managing drone movements.
            zones (dict[str, Zone] | None):
                A dictionary mapping zone names to their coordinates.
                Defaults to None.
            connections (list[Connection] | None):
                A list of connections between zones. Defaults to None.
        """
        self.start_zone = start_zone
        self.end_zone = end_zone
        self.drone_paths = drone_paths
        self.turn_logs: list[TurnLog] = []
        self.reservation = reservation
        self.zones = zones or {}
        self.connections_map = {}
        if connections:
            for conn in connections:
                key = frozenset((conn.first_zone, conn.second_zone))
                self.connections_map[key] = conn.max_link_capacity

    def _get_capacities(
        self, target: str, turn: int, total_drones: int
    ) -> tuple[int, int]:
        """Retrieve current occupancy and max capacity for a zone or link.

        Args:
            target (str): The name of the zone or connection.
            turn (int): The current turn number.
            total_drones (int): The total number of drones in the simulation.
        """
        if not self.reservation:
            return 1, 1

        if target in self.zones:
            if target == self.end_zone:
                curr = 0
                for path in self.drone_paths:
                    for curr_t, zone, _ in path:
                        if zone == self.end_zone and curr_t <= turn:
                            curr += 1
                            break
                cap = total_drones
                return curr, cap

            if target == self.start_zone:
                curr = self.reservation.zone_bookings.get((target, turn), 1)
                cap = total_drones
                return curr, cap

            curr = self.reservation.zone_bookings.get((target, turn), 1)
            cap = self.zones[target].max_drones
            return curr, cap

        if "-" in target:
            parts = target.split("-")
            key = frozenset((parts[0], parts[1]))
            curr = self.reservation.link_bookings.get((key, turn), 1)
            cap = self.connections_map.get(key, 1)
            return curr, cap

        return 1, 1

    def run(self) -> list[TurnLog]:
        """Run the simulation and generates logs for each turn.

        Returns:
            list[TurnLog]:
                A list of TurnLog objects representing the movements
                of drones for each turn.
        """
        max_turns = 0
        for path in self.drone_paths:
            if len(path) > 0:
                last_step = path[len(path) - 1]
                if last_step[0] > max_turns:
                    max_turns = last_step[0]

        total_drones = len(self.drone_paths)

        for turn in range(1, max_turns + 1):
            log = TurnLog(turn_number=turn)

            for drone_index in range(total_drones):
                path = self.drone_paths[drone_index]
                drone_id = drone_index + 1

                current_step = None
                previous_step = None

                for step in path:
                    if step[0] == turn:
                        current_step = step
                    elif step[0] == turn - 1:
                        previous_step = step

                if current_step is not None and previous_step is not None:
                    curr_zone = current_step[1]
                    curr_conn = current_step[2]
                    prev_zone = previous_step[1]
                    prev_conn = previous_step[2]

                    target = None
                    is_conn = False

                    if curr_zone != prev_zone or curr_conn != prev_conn:
                        if curr_conn is not None:
                            target = curr_conn
                            is_conn = True
                        else:
                            target = curr_zone
                    elif prev_conn is not None and curr_conn is None:
                        target = curr_zone

                    if target is not None:
                        curr_cap, max_cap = self._get_capacities(
                            target, turn, total_drones
                        )
                        log.add_move(
                            drone_id, target, is_conn, curr_cap, max_cap
                        )

            if not log.is_empty():
                self.turn_logs.append(log)

        return self.turn_logs
