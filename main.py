"""Main entry point for the Fly-in simulation and visualization program."""

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


def run_simulation() -> None:
    """Calculate spatio-temporal paths and displays the required log lines."""
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
    """Manage Pygame's animated graphical display interface."""
    pygame.init()

    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Fly-in")
    clock = pygame.time.Clock()

    # --- Chargement des images ---
    base_dir = Path(__file__).resolve().parent
    image_files = {
        "background": base_dir / "background.png",
        "drone": base_dir / "drone.png",
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
        pygame.image.load(str(image_files["drone"])).convert_alpha(), (100, 80)
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

    # Suivi logique de la zone actuelle de chaque drone côté visuel.
    # Séparé de drone.position (flottant/décalé) pour rester synchronisé
    # avec les logs du simulateur sans dépendre des coordonnées pixels.
    drone_zone_tracking: list[str] = [start_name] * nb_drones

    # --- Configuration caméra ---
    view = View()
    coordinates_list: list[tuple[int, int]] = []
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
                    # Touche A : démarrer ou mettre en pause l'animation
                    animation_started = not animation_started
            view.camera_mouse(event)

        # Update keyboard input every frame (for continuous key press)
        view.camera_keyboard()

        # --- Interprétation et animation pas à pas du log de simulation ---
        if animation_started and current_log_index < len(logs):
            any_moving = any(drone.is_moving for drone in drones)

            # On attend l'arrêt complet de tous les drones avant
            # le tour suivant
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

                    # On coupe uniquement sur le premier tiret pour préserver
                    # le nom complet de la connexion
                    # (ex: "D1-zoneA-zoneB" → "zoneA-zoneB")
                    destination = move.split("-", 1)[1]

                    # 1. CAS TRANSIT RESTRICTED
                    # (destination = "zoneA-zoneB", pas dans zones)
                    if destination not in zones:
                        # Le nom de connexion est "zoneA-zoneB".
                        # Les noms de zones n'ayant pas de tiret
                        # (validé par le parser),
                        # split("-") donne exactement ["zoneA", "zoneB"].
                        parts = destination.split("-")
                        next_zone_name = parts[1] if len(parts) == 2 else None

                        if (
                            next_zone_name is not None
                            and next_zone_name in zones
                        ):
                            current_zone_obj = zones[
                                drone_zone_tracking[drone_index]
                            ]
                            target_zone_obj = zones[next_zone_name]

                            # Calcul du milieu géométrique du lien pour
                            # l'animation
                            mid_x = (
                                float(current_zone_obj.coordinate_x)
                                + float(target_zone_obj.coordinate_x)
                            ) / 2.0
                            mid_y = (
                                float(current_zone_obj.coordinate_y)
                                + float(target_zone_obj.coordinate_y)
                            ) / 2.0

                            # Le drone s'arrête au milieu ce premier tour
                            drone.start_move((mid_x, mid_y))

                            # On met à jour le tracking pour que le tour 2
                            # sache d'où vient le drone
                            drone_zone_tracking[drone_index] = next_zone_name

                    # 2. CAS ZONE NORMALE / ARRIVÉE EN ZONE RESTRICTED
                    # (1 tour direct)
                    else:
                        target = zones[destination]
                        drone.start_move(
                            (
                                float(target.coordinate_x),
                                float(target.coordinate_y),
                            )
                        )
                        drone_zone_tracking[drone_index] = destination

                # Passage au tour de log suivant
                current_log_index += 1

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
