import sys
from pathlib import Path
import random

from get_conf import get_conf
from model import WINDOW_SIZE
from error import print_error
from view import View
from drone import Drone
from draw import draw_connections, create_drone_drawer, draw_zones
from pathfinder import get_all_existing_paths

try:
    import pygame
except ModuleNotFoundError as er:
    print_error(str(er))
    sys.exit(1)


# Combien de pixels représente "1" unité de position dans le fichier de config.
# Exemple : la zone "hub 3 4" sera dessinée en (3*SCALE, 4*SCALE) pixels.
# On peux changer cette valeur pour zoomer / dézoomer.


def base_pygame() -> None:
    """Initialise pygame, charge les images et lance la boucle d'affichage."""
    pygame.init()

    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Fly-in")
    clock = pygame.time.Clock()

    base_dir = Path(__file__).resolve().parent

    # --- Chargement des images ---
    # On vérifie que chaque fichier existe avant de tenter de le charger
    image_files = {
        "background": base_dir / "background.png",
        "first_drone": base_dir / "first_drone.png",
        "second_drone": base_dir / "second_drone.png",
        "zone": base_dir / "zone.png",
        "text_edge": base_dir / "text_edge.png",
    }

    for name, path in image_files.items():
        if not path.exists():
            print_error(f"Image file not found: '{path}'")

    # Ici on est sûr que les fichiers existent
    sky = pygame.image.load(str(image_files["background"]))
    drone_img = pygame.image.load(
        str(image_files[random.choice(["first_drone", "second_drone"])])
    )
    zone_img = pygame.image.load(str(image_files["zone"]))
    edge_img = pygame.image.load(str(image_files["text_edge"]))

    background_sky = pygame.transform.scale(sky, WINDOW_SIZE)
    small_drone = pygame.transform.scale(drone_img, (95, 95))
    small_zone = pygame.transform.scale(zone_img, (100, 70))
    edge_img = pygame.transform.scale(edge_img, (WINDOW_SIZE[0], 300))

    # font = pygame.font.SysFont(None, 20)

    # --- Lecture du fichier de configuration ---
    conf = get_conf()
    zones = conf["zones"]
    connections = conf["connections"]

    start_zone = zones[conf["start_zone"]]
    # end_zone = zones[conf["end_zone"]]

    # --- Création de la caméra ---
    view = View()
    pos: list[tuple[int, int]] = []
    for zone_name, zone_obj in conf["zones"].items():
        # On récupère directement les vraies coordonnées
        pos.append((zone_obj.coordinate_x, zone_obj.coordinate_y))
    view.best_view(pos, (start_zone.coordinate_x, start_zone.coordinate_y))

    # --- Création d'un drone de démonstration ---
    # Il part de la zone de départ et va vers la zone d'arrivée
    demo_drone = Drone(
        position=(
            float(start_zone.coordinate_x),
            float(start_zone.coordinate_y),
        ),
    )

    # from pathfinder import pathfinder

    # print(pathfinder(demo_drone))

    connections = conf["connections"]

    # demo_drone.start_move((end_zone.coordinate_x, end_zone.coordinate_y))

    # --- Boucle principale ---
    running = True
    animation = False
    draw_drone = create_drone_drawer()
    path_found = []
    # 1. INITIALISATION PAR DÉFAUT (En dehors et avant le try)

    try:
        paths_found = get_all_existing_paths()
        for path_f in paths_found:
            print(len(path_f))
        if paths_found:
            path_found = paths_found[0]
    except Exception as e:
        # On affiche la vraie erreur dans la console pour savoir ce qui cloche
        print(f"Error: {e}")

    while running:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            view.handle_event(event)

            # Avance l'animation du drone d'un pas
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    animation = not animation

        view.camera()

        if animation and not demo_drone.is_moving:
            # 1. On cherche le nom de la zone où se trouve le drone
            zone_name = ""
            for name in zones:
                zone = zones[name]
                if (
                    zone.coordinate_x,
                    zone.coordinate_y,
                ) == demo_drone.position:
                    zone_name = name
                    break

            target_zone_name = None

            # Ajout du -1 indispensable pour éviter
            # le crash de l'IndexError à la fin du chemin
            for i in range(len(path_found) - 1):
                if path_found[i] == zone_name:
                    target_zone_name = path_found[i + 1]
                    break

            if target_zone_name:
                target_zone = zones[target_zone_name]
                demo_drone.start_move(
                    (target_zone.coordinate_x, target_zone.coordinate_y)
                )

        if animation:
            demo_drone.update()

        # Dessin de la frame
        screen.blit(background_sky, (0, 0))
        draw_connections(screen, view, zones, connections)
        draw_zones(screen, view, zones, small_zone)
        draw_drone(screen, view, demo_drone, small_drone)
        # draw_edge(screen, view, edge_img)

        clock.tick(60)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    base_pygame()
