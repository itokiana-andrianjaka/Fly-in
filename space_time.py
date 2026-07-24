"""Module for managing space-time reservations for zones and connections."""


class SpaceTimeReservation:
    """Maintains a reservation table for zones and connections over time."""

    def __init__(self) -> None:
        """Initialize the reservation table."""
        self.zone_bookings: dict[tuple[str, int], int] = {}
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
