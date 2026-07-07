# Fichier: main.py
"""
Point d'entrée principal pour l'exécution
graphique et textuelle du projet Fly-in.
"""

import sys
from pathlib import Path

from get_conf import get_conf
from model import WINDOW_SIZE
from error import print_error
from view import View
from drone import Drone
from draw import draw_connections, create_drone_drawer, create_zones_drawer
from pathfinder import Pathfinder
from simulator import Simulator

try:
    import pygame
except ModuleNotFoundError as er:
    print_error(str(er))
    sys.exit(1)


def run_simulation() -> None:
    """
    Calcule les chemins spatio-temporels et affiche les lignes de log requises.
    """
    conf = get_conf()

    pathfinder = Pathfinder(
        zones=conf["zones"],
        connections=conf["connections"],
    )
    drone_paths = pathfinder.assign_paths(
        start=conf["start_zone"],
        end=conf["end_zone"],
        nb_drones=conf["nb_drones"],
    )

    if not drone_paths or len(drone_paths[0]) == 0:
        print_error("No valid path could be found to the destination.")
        return

    simulator = Simulator(
        start_zone=conf["start_zone"],
        end_zone=conf["end_zone"],
        drone_paths=drone_paths,
    )
    logs = simulator.run()

    for log in logs:
        print(log.render())

    print(f"\nTotal turns: {len(logs)}")


def run_pygame() -> None:
    """Gère l'interface d'affichage graphique animée de Pygame."""
    pygame.init()

    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Fly-in")
    clock = pygame.time.Clock()

    # --- Chargement des images ---
    base_dir = Path(__file__).resolve().parent
    image_files = {
        "background": base_dir / "background.png",
        "drone": base_dir / "first_drone.png",
        "zone": base_dir / "zone.png",
    }

    for name, path in image_files.items():
        if not path.exists():
            print_error(f"Missing image file: {path.name}")

    background = pygame.transform.scale(
        pygame.image.load(str(image_files["background"])).convert_alpha(),
        WINDOW_SIZE,
    )
    small_drone = pygame.transform.scale(
        pygame.image.load(str(image_files["drone"])).convert_alpha(), (95, 95)
    )
    small_zone = pygame.transform.scale(
        pygame.image.load(str(image_files["zone"])).convert_alpha(), (100, 70)
    )

    conf = get_conf()
    zones = conf["zones"]
    connections = conf["connections"]
    nb_drones = conf["nb_drones"]
    start_name = conf["start_zone"]
    start_zone = zones[start_name]

    # --- Initialisation des trajectoires de simulation ---
    pathfinder = Pathfinder(zones=zones, connections=connections)
    drone_paths = pathfinder.assign_paths(
        start=start_name,
        end=conf["end_zone"],
        nb_drones=nb_drones,
    )

    if not drone_paths or len(drone_paths[0]) == 0:
        print_error("No valid path could be found to the destination.")
        return

    simulator = Simulator(
        start_zone=start_name,
        end_zone=conf["end_zone"],
        drone_paths=drone_paths,
    )
    logs = simulator.run()

    # --- Initialisation des drones visuels Pygame ---
    drones: list[Drone] = []
    for _ in range(nb_drones):
        drones.append(
            Drone(
                position=(
                    float(start_zone.coordinate_x),
                    float(start_zone.coordinate_y),
                )
            )
        )

    # Suivi logique de la position des drones pour l'affichage Pygame
    drone_zone_tracking: list[str] = [start_name] * nb_drones

    # --- Configuration caméra ---
    view = View()
    coordinates_list = []
    for z in zones.values():
        coordinates_list.append((z.coordinate_x, z.coordinate_y))

    view.best_view(
        coordinates_list,
        (start_zone.coordinate_x, start_zone.coordinate_y),
    )

    draw_zones = create_zones_drawer()
    draw_drone = create_drone_drawer()

    running = True
    animation_started = False
    current_log_index = 0

    # ==========================================================================
    # BOUCLE PRINCIPALE PYGAME
    # ==========================================================================
    while running:
        for drone in drones:
            drone.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_a:
                    animation_started = not animation_started
            view.handle_event(event)

        view.camera()

        # --- Interprétation et animation pas à pas du log de simulation ---
        if animation_started and current_log_index < len(logs):
            any_moving = any(drone.is_moving for drone in drones)

            # On attend l'arrêt complet de
            # tous les drones avant de lire le tour suivant
            if not any_moving:
                log = logs[current_log_index]

                for drone_index, drone in enumerate(drones):
                    drone_id = f"D{drone_index + 1}"

                    # Chercher s'il y a une action pour ce drone sur ce tour
                    move = next(
                        (m for m in log.moves if m.startswith(drone_id + "-")),
                        None,
                    )

                    if move is None:
                        continue

                    # Récupération de la cible brute
                    # (soit une zone, soit un lien)
                    destination = move.split("-")[1]

                    # 1. CAS DU TOUR 1 DE ZONE RESTREINTE
                    # (Exemple de log : D1-A_B)
                    if destination not in zones:
                        drone_path = drone_paths[drone_index]
                        current = drone_zone_tracking[drone_index]

                        # Retrouver la vraie zone de destination finale
                        # dans son chemin théorique
                        next_zone_name: str | None = None
                        for j, step in enumerate(drone_path):
                            zone_name = step[1]
                            if (
                                zone_name == current
                                and j + 1 < len(drone_path)
                            ):
                                next_zone_name = drone_path[j + 1][1]
                                break

                        if (
                            next_zone_name is not None
                            and next_zone_name in zones
                        ):
                            current_zone = zones[current]
                            target_zone = zones[next_zone_name]

                            # Calcul des coordonnées géométriques du
                            # milieu du lien
                            mid_x = (
                                float(current_zone.coordinate_x)
                                + float(target_zone.coordinate_x)
                            ) / 2.0
                            mid_y = (
                                float(current_zone.coordinate_y)
                                + float(target_zone.coordinate_y)
                            ) / 2.0

                            # On envoie le drone s'arrêter au milieu
                            # pour ce premier tour
                            drone.start_move((mid_x, mid_y))

                            # On met à jour son tracking pour que le
                            # Tour 2 connaisse sa provenance
                            drone_zone_tracking[drone_index] = next_zone_name

                    # 2. CAS DU TOUR 2 DE ZONE RESTREINTE OU
                    # ZONE STANDARD (1 tour direct)
                    else:
                        if destination in zones:
                            target = zones[destination]
                            drone.start_move(
                                (
                                    float(target.coordinate_x),
                                    float(target.coordinate_y),
                                )
                            )
                            drone_zone_tracking[drone_index] = destination

                # Passage au tour de log suivant
                current_log_index = current_log_index + 1

        # --- Phase de rendu graphique ---
        screen.fill(pygame.Color("lightblue"))
        screen.blit(background, (0, 0))
        draw_connections(screen, view, zones, connections)
        draw_zones(screen, view, zones, small_zone)

        for index, drone in enumerate(drones):
            saved_pos = drone.position
            offset = index - (nb_drones / 2)
            drone.position = (
                saved_pos[0] + offset / view.scale,
                saved_pos[1] + offset / view.scale,
            )
            draw_drone(screen, view, drone, small_drone, index)
            drone.position = saved_pos

        clock.tick(60)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    try:
        run_simulation()
        run_pygame()
    except Exception as e:
        print_error(f"Runtime error: {e}")
