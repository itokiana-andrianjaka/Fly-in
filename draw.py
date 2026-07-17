"""all the functions used to draw for visualization."""

from error import print_error
from view import View
from model import Zone, Connection
from collections.abc import Callable
from drone import Drone

try:
    import pygame
except ModuleNotFoundError as er:
    print_error(str(er))


def draw_connections(
    screen: pygame.Surface,
    view: View,
    zones: dict[str, Zone],
    connections: list[Connection],
) -> None:
    """Draw a line between each pair of connected zones.

    Args:
        screen (pygame.Surface):
            Surface on which the connections are drawn.
        view (View):
            View used to convert world coordinates to screen coordinates.
        zones (dict[str, Zone]):
            Mapping of zone names to their corresponding Zone objects.
        connections (list[Connection]): List of Connection objects
            representing the connections between zones.
    """
    for connection in connections:
        first_zone = zones[connection.first_zone]
        second_zone = zones[connection.second_zone]

        point1 = view.world_to_screen(
            first_zone.coordinate_x, first_zone.coordinate_y
        )
        point2 = view.world_to_screen(
            second_zone.coordinate_x, second_zone.coordinate_y
        )

        pygame.draw.line(screen, pygame.Color("black"), point1, point2, 2)


def create_zones_drawer() -> (
    Callable[[pygame.Surface, View, dict[str, Zone], pygame.Surface], None]
):
    """Create a zone drawing function.

    The returned function keeps an internal state to cycle through the
    predefined rainbow colors whenever a zone uses the special
    ``"rainbow"`` color.

    Returns:
        Callable
            [[pygame.Surface, View, dict[str, Zone], pygame.Surface], None]:
            A function that draws all zones into the screen.
    """
    color_rainbow = [
        "Red",
        "Orange",
        "Blue",
        "Yellow",
        "Purple",
        "Indigo",
        "Green",
    ]
    last_color_rainbow = 0

    def draw_zones(
        screen: pygame.Surface,
        view: View,
        zones: dict[str, Zone],
        zone_picture: pygame.Surface,
    ) -> None:
        """Draw all zones on the screen.

        Each zone is positioned according to the current view and tinted
        with its configured color. If the zone color is ``"rainbow"``,
        the color cycles through a predefined list at each draw call.

        Args:
            screen (pygame.Surface):
                Surface on which the zones are drawn.
            view (View):
                View used to convert world coordinates to screen coordinates.
            zones (dict[str, Zone]):
                Mapping of zone names to their corresponding Zone objects.
            zone_picture (pygame.Surface):
                Base image used to render each zone.

        Raises:
            ValueError: If a zone specifies an unknown color.
        """
        half_w = zone_picture.get_width() // 2
        half_h = zone_picture.get_height() // 2

        for zone in zones.values():
            cx, cy = view.world_to_screen(zone.coordinate_x, zone.coordinate_y)
            picture = zone_picture.copy()

            try:
                if zone.color:
                    color = pygame.Color(zone.color)
                else:
                    color = pygame.Color("white")

            except ValueError:
                if zone.color == "rainbow":
                    nonlocal last_color_rainbow
                    if last_color_rainbow >= 180:
                        last_color_rainbow = 0
                    else:
                        last_color_rainbow += 1
                    color = pygame.Color(
                        color_rainbow[last_color_rainbow // 30]
                    )
                else:
                    raise ValueError(f"Unknown color: {zone.color}")

            picture.fill(color, special_flags=pygame.BLEND_RGB_MULT)
            screen.blit(picture, (cx - half_w, cy - half_h))

    return draw_zones


def create_drone_drawer() -> (
    Callable[[pygame.Surface, View, Drone, pygame.Surface, int], None]
):
    """
    Create a graphics manager capable of drawing all drones.

    Each drone is assigned a distinct color based on its index.

    Returns:
        Callable [[pygame.Surface, View, Drone, pygame.Surface, int], None]:
            A function that draws all drones into the screen.
    """
    drone_colors = [
        "white",
        "red",
        "saddlebrown",
        "sienna",
        "brown",
        "dimgray",
        "cyan",
        "magenta",
        "orange",
        "lime",
    ]

    drone_offsets = [
        (0, 0),
        (6, -4),
        (-6, 4),
        (8, 5),
        (-8, -5),
        (12, -2),
        (-12, 2),
        (4, 10),
        (-4, -10),
        (10, 8),
    ]

    def draw_drone(
        screen: pygame.Surface,
        view: View,
        drone: Drone,
        drone_picture: pygame.Surface,
        drone_index: int,
    ) -> None:
        """Draw a drone on the screen with its animation and unique color.

        Args:
            screen (pygame.Surface):
                Surface where the drone is rendered.
            view (View):
                Used to convert world coordinates to screen coordinates.
            drone (Drone):
                Drone instance containing its position and animation state.
            drone_picture (pygame.Surface):
                Base image used to render the drone.
            drone_index (int):
                Index of the drone, used to assign a unique color
        """
        half_w = drone_picture.get_width() // 2
        half_h = drone_picture.get_height() // 2

        # Évolution de la hauteur à chaque frame de l'instance du drone actuel
        drone.current_height += drone.move

        # Inversion de la direction si on atteint les limites (38 et 48)
        if drone.current_height >= 48.0:
            drone.move = -0.1
        elif drone.current_height <= 38.0:
            drone.move = 0.1

        cx, cy = view.world_to_screen(drone.position[0], drone.position[1])
        picture = drone_picture.copy()

        # Couleur unique par drone grâce à son index dans la flotte
        color_name = drone_colors[drone_index % len(drone_colors)]
        color = pygame.Color(color_name)

        offset_x, offset_y = drone_offsets[drone_index % len(drone_offsets)]

        tint = picture.copy()
        tint.fill(color, special_flags=pygame.BLEND_RGBA_ADD)
        picture.blit(
            tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT
        )
        screen.blit(
            picture,
            (
                cx - half_w + offset_x,
                cy - half_h - int(drone.current_height) + 10 + offset_y,
            ),
        )

    return draw_drone
