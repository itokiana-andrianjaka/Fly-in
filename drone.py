"""Module used to manipulate drones."""

import random

from error import print_error

try:
    from pydantic import BaseModel, Field
except ModuleNotFoundError as er:
    print_error(str(er))


class Drone(BaseModel):
    """Represents a drone with autonomous movement and animation."""

    # Position actuelle du drone en coordonnées logiques (pas en pixels)
    position: tuple[float, float] = Field(default=(0.0, 0.0))

    # Position de départ du mouvement en cours
    start_pos: tuple[float, float] = Field(default=(0.0, 0.0))

    # Position d'arrivée visée
    target_pos: tuple[float, float] = Field(default=(0.0, 0.0))

    # Progression du trajet de 0.0 (départ) à 1.0 (arrivée)
    progress: float = Field(default=1.0)

    # Vitesse de l'animation linéaire
    animation_speed: float = Field(default=0.05, gt=0.0, le=1.0)

    # --- Itinéraire propre à ce drone ---
    path: list[str] = Field(default_factory=list)

    # --- État de l'animation verticale propre à chaque drone ---
    current_height: float = Field(
        default_factory=lambda: random.uniform(38.0, 48.0)
    )
    move: float = Field(
        default_factory=lambda: random.choice([0.08, 0.1, 0.12])
        * random.choice([-1.0, 1.0])
    )

    # Décalage aléatoire fixe pour éviter que les drones forment une queue
    # Généré une seule fois à la création, jamais modifié ensuite
    offset_x: float = Field(default_factory=lambda: random.uniform(-0.1, 0.1))
    offset_y: float = Field(default_factory=lambda: random.uniform(-0.1, 0.1))

    @property
    def is_moving(self) -> bool:
        """Validation if the drone is still moving.

        Returns:
            bool: Returns True if the drone is moving between two zones.
        """
        return self.progress < 1.0

    def start_move(self, target: tuple[float, float]) -> None:
        """Start a move animation to target.

        Args:
            target (tuple[float, float]):
                Destination position in logical coordinates
        """
        self.start_pos = self.position
        self.target_pos = (float(target[0]), float(target[1]))
        self.progress = 0.0

    def update(self) -> None:
        """Advance the drone animation one step at each frame."""
        # 1. Gestion du rebond de la chauve-souris autonome
        self.current_height += self.move
        if self.current_height >= 48.0:
            self.move = -0.1
        elif self.current_height <= 38.0:
            self.move = 0.1

        # 2. Gestion du déplacement linéaire (interpolation)
        if self.progress < 1.0:
            self.progress = min(1.0, self.progress + self.animation_speed)
            start_x, start_y = self.start_pos
            target_x, target_y = self.target_pos
            new_x = start_x + (target_x - start_x) * self.progress
            new_y = start_y + (target_y - start_y) * self.progress
            self.position = (new_x, new_y)
