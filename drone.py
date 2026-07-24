"""Module used to manipulate drones."""

import random

from error import print_error

try:
    from pydantic import BaseModel, Field
except ModuleNotFoundError as er:
    print_error(str(er))


class Drone(BaseModel):
    """Represents a drone with autonomous movement and animation."""

    position: tuple[float, float] = Field(default=(0.0, 0.0))

    start_pos: tuple[float, float] = Field(default=(0.0, 0.0))

    target_pos: tuple[float, float] = Field(default=(0.0, 0.0))

    progress: float = Field(default=1.0)

    animation_speed: float = Field(default=0.05, gt=0.0, le=1.0)

    path: list[str] = Field(default_factory=list)

    current_height: float = Field(
        default_factory=lambda: random.uniform(38.0, 48.0)
    )
    move: float = Field(
        default_factory=lambda: random.choice([0.08, 0.1, 0.12])
        * random.choice([-1.0, 1.0])
    )

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
        self.current_height += self.move
        if self.current_height >= 48.0:
            self.move = -0.1
        elif self.current_height <= 38.0:
            self.move = 0.1

        if self.progress < 1.0:
            self.progress = min(1.0, self.progress + self.animation_speed)
            start_x, start_y = self.start_pos
            target_x, target_y = self.target_pos
            new_x = start_x + (target_x - start_x) * self.progress
            new_y = start_y + (target_y - start_y) * self.progress
            self.position = (new_x, new_y)
