"""Simulation module for managing drone movements and generating logs."""


class TurnLog:
    """Represents the log of drone movements for a single turn."""

    def __init__(self, turn_number: int) -> None:
        """Initialize the turn log with a turn number.

        Args:
            turn_number (int): The current turn number in the simulation.
        """
        self.turn_number = turn_number
        self.moves: list[str] = []

    def add_move(self, drone_id: int, target: str) -> None:
        """Add a move to the turn log.

        Args:
            drone_id (int): The ID of the drone making the move.
            target (str): The target zone or connection for the move.
        """
        self.moves.append(f"D{drone_id}-{target}")

    def render(self) -> str:
        """Render the turn log as a string for output.

        Returns:
            str: A string representation of the turn log, with moves
            separated by spaces.
        """
        return " ".join(self.moves)

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
    ) -> None:
        """Initialize the simulator with start/end zones and drone paths.

        Args:
            start_zone (str): The name of the starting zone.
            end_zone (str): The name of the ending zone.
            drone_paths (list[list[tuple[int, str, str | None]]]):
                A list of paths for each drone, where each path is a list of
                tuples containing (turn_number, zone_name, connection_name).
        """
        self.start_zone = start_zone
        self.end_zone = end_zone
        self.drone_paths = drone_paths
        self.turn_logs: list[TurnLog] = []

    def run(self) -> list[TurnLog]:
        """Run the simulation and generates logs for each turn.

        Returns:
            list[TurnLog]:
                A list of TurnLog objects representing the movements
                of drones for each turn.
        """
        # Trouver la durée maximale de la simulation planifiée
        max_turns = 0
        for path in self.drone_paths:
            if len(path) > 0:
                last_step = path[len(path) - 1]
                if last_step[0] > max_turns:
                    max_turns = last_step[0]

        # Générer l'état de chaque tour séquentiellement
        for turn in range(1, max_turns + 1):
            log = TurnLog(turn_number=turn)

            for drone_index in range(len(self.drone_paths)):
                path = self.drone_paths[drone_index]
                drone_id = drone_index + 1

                # Trouver l'état du drone à ce tour précis et au tour précédent
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

                    # Si la zone ou la connexion a changé par rapport
                    # au tour précédent
                    if curr_zone != prev_zone or curr_conn != prev_conn:
                        if curr_conn is not None:
                            log.add_move(drone_id, curr_conn)
                        else:
                            log.add_move(drone_id, curr_zone)
                    elif prev_conn is not None and curr_conn is None:
                        # Fin de transit d'une zone restreinte
                        log.add_move(drone_id, curr_zone)

            if not log.is_empty():
                self.turn_logs.append(log)

        return self.turn_logs
