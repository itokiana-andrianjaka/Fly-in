import sys

from error import print_error

try:
    from pydantic import BaseModel, Field
except ModuleNotFoundError as er:
    print_error(str(er))
    sys.exit(1)


class Drone(BaseModel):
    """
    Représente un drone capable de se déplacer en douceur entre deux positions.

    Comment fonctionne l'animation (interpolation linéaire) :
    --------------------------------------------------------
    Au lieu de faire x += 1 (qui ne fonctionne que pour les axes),
    on utilise cette formule à chaque frame :

        position = depart + (arrivee - depart) * progression

    "progression" va de 0.0 (tout au début du trajet) à 1.0 (arrivée).
    Comme on calcule x et y séparément avec la même progression,
    le drone suit une ligne droite parfaite entre les deux points,
    peu importe l'angle (horizontal, vertical, diagonal, ou autre).

    Exemple concret avec move((0,0), (3,4)) :
        - progression = 0.0  -> position = (0, 0)   (départ)
        - progression = 0.5  -> position = (1.5, 2) (milieu du trajet)
        - progression = 1.0  -> position = (3, 4)   (arrivée)
    """

    # Position actuelle du drone en coordonnées logiques (pas en pixels)
    position: tuple[float, float] = Field(default=(0.0, 0.0))

    # Position de départ du mouvement en cours
    start_pos: tuple[float, float] = Field(default=(0.0, 0.0))

    # Position d'arrivée du mouvement en cours
    target_pos: tuple[float, float] = Field(default=(0.0, 0.0))

    # Progression du trajet : 0.0 = début, 1.0 = arrivée
    # On démarre à 1.0 car il n'y a pas de mouvement en cours au départ
    # ge=0.0 et le=1.0 -> Pydantic refuse toute valeur hors de [0.0, 1.0]
    progress: float = Field(default=1.0, ge=0.0, le=1.0)

    # Vitesse de l'animation : augmente "progression" de
    # cette valeur à chaque frame.

    # 0.02 = 50 frames pour faire le trajet complet (à 60fps = ~0.8 secondes)
    # gt=0.0 -> Pydantic refuse une vitesse nulle ou négative
    animation_speed: float = Field(default=0.05, gt=0.0, le=1.0)

    def start_move(self, target: tuple[int, int]) -> None:
        """
        Démarre une animation de déplacement vers `target`.

        `target` est en coordonnées logiques (celles du fichier config).

        Exemple :
            drone = Drone(position=(0.0, 0.0))
            drone.move((3, 4))
            # Le drone se déplace maintenant de (0,0) vers (3,4)
            # à chaque appel de drone.update()
        """
        self.start_pos = self.position
        self.target_pos = (float(target[0]), float(target[1]))
        self.progress = 0.0

    def update(self) -> None:
        """
        Avance l'animation d'un pas.
        À appeler une fois par frame dans la boucle principale.
        """
        if self.progress >= 1.0:
            return

        # On avance la progression sans jamais dépasser 1.0
        self.progress = min(1.0, self.progress + self.animation_speed)

        start_x, start_y = self.start_pos
        target_x, target_y = self.target_pos

        # Interpolation linéaire sur x et y séparément
        # -> ligne droite parfaite pour n'importe quel angle
        new_x = start_x + (target_x - start_x) * self.progress
        new_y = start_y + (target_y - start_y) * self.progress

        self.position = (new_x, new_y)

    @property
    def is_moving(self) -> bool:
        """Retourne True si une animation est en cours,
        False si le drone est arrêté."""
        return self.progress < 1.0
