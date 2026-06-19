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

        pygame.draw.line(screen, pygame.Color("white"), point1, point2, 1)


def draw_zones(
    screen: pygame.Surface,
    view: View,
    zones: dict[str, Zone],
    zone_image: pygame.Surface,
) -> None:
    """
    Dessine chaque zone :
    - L'image de la zone centrée sur sa position
    - Le nom de la zone écrit au-dessus
    """
    half_w = zone_image.get_width() // 2
    half_h = zone_image.get_height() // 2

    for zone in zones.values():
        cx, cy = view.world_to_screen(zone.coordinate_x, zone.coordinate_y)
        image = zone_image.copy()
        if zone.color:
            image.fill(
                pygame.Color(zone.color), special_flags=pygame.BLEND_RGBA_MULT
            )
        screen.blit(image, (cx - half_w, cy - half_h))


def create_drone_drawer() -> (
    Callable[[pygame.Surface, View, Drone, pygame.Surface], None]
):
    """
    Crée et retourne la fonction draw_drone avec un état encapsulé (nonlocal).
    """
    current_height = 40.0
    move = 0.1

    def draw_drone(
        screen: pygame.Surface,
        view: View,
        drone: Drone,
        drone_image: pygame.Surface,
    ) -> None:

        nonlocal current_height, move

        half_w = drone_image.get_width() // 2
        half_h = drone_image.get_height() // 2

        # Évolution de la hauteur à chaque frame
        current_height += move

        # Inversion de la direction si on atteint les limites (38 et 43)
        if current_height >= 48.0:
            move = -0.1
        elif current_height <= 38.0:
            move = 0.1

        cx, cy = view.world_to_screen(drone.position[0], drone.position[1])
        screen.blit(
            drone_image, (cx - half_w, cy - half_h - int(current_height))
        )

    return draw_drone


def draw_edge(
    screen: pygame.Surface, view: View, edge_image: pygame.Surface
) -> None:
    """Dessine le edge pour le texte

    Args:
        screen (pygame.Surface): _description_
        view (view): _description_
        edge_img (pygame.Surface): _description_
    """
    # half_w = edge_image.get_width() // 2
    # half_h = edge_image.get_height() // 2

    screen.blit(
        edge_image, (0, screen.get_height() - edge_image.get_height() + 50)
    )
