import sys

from error import print_error
from view import View
from model import Zone, Connection
from collections.abc import Callable
from drone import Drone

try:
    import pygame
except ModuleNotFoundError as er:
    print_error(str(er))
    sys.exit(1)


def draw_connections(
    screen: pygame.Surface,
    view: View,
    zones: dict[str, Zone],
    connections: list[Connection],
) -> None:
    """Dessine une ligne entre chaque paire de zones connectées."""
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
        """
        Dessine chaque zone :
        - L'image de la zone centrée sur sa position
        - Le nom de la zone écrit au-dessus
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
    Crée un gestionnaire graphique capable de dessiner n'importe quel
    drone de la flotte. Chaque drone reçoit une couleur distincte
    basée sur son index dans la flotte.
    """
    drone_colors = [
        "white",
        "brown",
        "saddlebrown",
        "sienna",
        "gray",
        "dimgray",
        "cyan",
        "magenta",
        "orange",
        "lime",
    ]

    def draw_drone(
        screen: pygame.Surface,
        view: View,
        drone: Drone,
        drone_picture: pygame.Surface,
        drone_index: int,
    ) -> None:
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

        picture.fill(color, special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(
            picture,
            (cx - half_w, cy - half_h - int(drone.current_height) + 10),
        )

    return draw_drone


def draw_edge(
    screen: pygame.Surface, view: View, edge_picture: pygame.Surface
) -> None:
    """Dessine le edge pour le texte."""
    pass
