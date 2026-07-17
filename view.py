"""View module for managing the visual representation of the simulation."""

from error import print_error
from model import WINDOW_SIZE

try:
    import pygame
    from pydantic import BaseModel, Field
except ModuleNotFoundError as er:
    print_error(str(er))


class View(BaseModel):
    """Represents the visual state of the simulation."""

    scale: float = Field(default=60.0, gt=0.0)  # float au lieu de int
    offset_x: float = Field(default=0.0)
    offset_y: float = Field(default=0.0)

    # True si l'utilisateur maintient le clic gauche pour faire glisser la vue
    dragging: bool = Field(default=False)

    # Dernière position connue de la souris (pour calculer le déplacement)
    last_mouse_pos: tuple[int, int] = Field(default=(0, 0))

    def best_view(
        self,
        zones_positions: list[tuple[int, int]],
        start_zone_pos: tuple[int, int],
    ) -> None:
        """Calculate the best scale and offset to fit all zones on the screen.

        Args:
            zones_positions (list[tuple[int, int]]):
                List of (x, y) coordinates for all zones.
            start_zone_pos (tuple[int, int]):
                Coordinates of the starting zone for centering the view.
        """
        if not zones_positions:
            return

        # 1. On trouve les bornes extrêmes de la carte
        min_x = min(pos[0] for pos in zones_positions)
        max_x = max(pos[0] for pos in zones_positions)
        min_y = min(pos[1] for pos in zones_positions)
        max_y = max(pos[1] for pos in zones_positions)

        world_width = max_x - min_x
        world_height = max_y - min_y

        if world_width == 0:
            world_width = 1
        if world_height == 0:
            world_height = 1

        # 2. ÉLOIGNEMENT AUTOMATIQUE : Si les zones sont trop proches
        # (ex: écart total < 5 unités)
        if world_width < 7 or world_height < 7:
            self.scale = 130.0  # On augmente le scale pour forcer un
            # écartement propre en pixels
        else:
            self.scale = 60.0  # scale standard par défaut

        # 3. Calcul de la taille de rendu réelle occupée en pixels
        map_width_pixels = world_width * self.scale
        map_height_pixels = world_height * self.scale

        # 4. CHOIX DU CENTRAGE : Est-ce que la carte déborde de l'écran ?
        if (
            map_width_pixels > WINDOW_SIZE[0]
            or map_height_pixels > WINDOW_SIZE[1]
        ):
            # LA MAP EST TROP GRANDE ->
            # Focus immédiat au centre sur le hub de START
            start_x, start_y = start_zone_pos
            self.offset_x = (WINDOW_SIZE[0] / 2) - (start_x * self.scale) - 400
            self.offset_y = (WINDOW_SIZE[1] / 2) - (start_y * self.scale) - 100
            # decalage pour une meilleur visualisation
        else:
            # LA MAP TIENT DEDANS ->
            # On la centre globalement au milieu de l'écran
            center_world_x = (min_x + max_x) * self.scale / 2
            center_world_y = (min_y + max_y) * self.scale / 2
            self.offset_x = (WINDOW_SIZE[0] / 2) - center_world_x
            self.offset_y = (WINDOW_SIZE[1] / 2) - center_world_y

    def camera_mouse(self, event: pygame.event.Event) -> None:
        """Handle mouse input for view control.

        Mouse: drag with left mouse button to pan the view.

        Args:
            event (pygame.event.Event): pygame event to process.
        """
        # Clic gauche enfoncé -> on commence à "attraper" la vue
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.dragging = True
            self.last_mouse_pos = pygame.mouse.get_pos()

        # Clic gauche relâché -> on arrête de bouger la vue
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False

        # Souris en mouvement pendant le clic -> on déplace la vue
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            last_x, last_y = self.last_mouse_pos

            self.offset_x += mouse_x - last_x
            self.offset_y += mouse_y - last_y

            self.last_mouse_pos = (mouse_x, mouse_y)

    def camera_keyboard(self) -> None:
        """Handle keyboard input for view control.

        Keyboard: arrow keys to scroll (must be called every frame).
        """
        keys = pygame.key.get_pressed()
        scroll_speed_pxl = 10

        if keys[pygame.K_LEFT]:
            self.offset_x += scroll_speed_pxl
        if keys[pygame.K_RIGHT]:
            self.offset_x -= scroll_speed_pxl
        if keys[pygame.K_UP]:
            self.offset_y += scroll_speed_pxl
        if keys[pygame.K_DOWN]:
            self.offset_y -= scroll_speed_pxl

    def world_to_screen(
        self, world_x: float, world_y: float
    ) -> tuple[int, int]:
        """Convert world coordinates to screen coordinates.

        Args:
            world_x (float): Description of the world x-coordinate.
            world_y (float): Description of the world y-coordinate.

        Returns:
            tuple[int, int]: The corresponding screen (x, y) coordinates.
        """
        screen_x = int(world_x * self.scale + self.offset_x)
        screen_y = int(world_y * self.scale + self.offset_y)
        return (screen_x, screen_y)
