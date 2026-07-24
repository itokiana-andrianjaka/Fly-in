"""Main entry point for the Fly-in simulation and visualization program."""

from pathlib import Path
import sys

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
    drone_paths, reservation = pathfinder.assign_paths(
        start=conf["start_zone"],
        end=conf["end_zone"],
        nb_drones=conf["nb_drones"],
    )

    if not drone_paths or len(drone_paths[0]) == 0:
        raise Exception("No valid path could be found to the destination.")

    simulator = Simulator(
        start_zone=conf["start_zone"],
        end_zone=conf["end_zone"],
        drone_paths=drone_paths,
        reservation=reservation,
        zones=conf["zones"],
        connections=conf["connections"],
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

    base_dir = Path(__file__).resolve().parent
    image_files = {
        "background": base_dir / "background.png",
        "drone": base_dir / "drone.png",
        "zone": base_dir / "zone.png",
    }

    for name, path in image_files.items():
        if not path.exists():
            raise Exception(f"Missing image file: {path.name}")

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

    pathfinder = Pathfinder(zones=zones, connections=connections)
    drone_paths, reservation = pathfinder.assign_paths(
        start=start_name,
        end=conf["end_zone"],
        nb_drones=nb_drones,
    )

    if not drone_paths or len(drone_paths[0]) == 0:
        raise Exception("No valid path could be found to the destination.")

    simulator = Simulator(
        start_zone=start_name,
        end_zone=conf["end_zone"],
        drone_paths=drone_paths,
        reservation=reservation,
    )
    logs = simulator.run()

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

    drone_zone_tracking: list[str] = [start_name] * nb_drones

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
                    animation_started = not animation_started
            view.camera_mouse(event)

        view.camera_keyboard()

        if animation_started and current_log_index < len(logs):
            any_moving = any(drone.is_moving for drone in drones)

            if not any_moving:
                log = logs[current_log_index]

                for drone_index, drone in enumerate(drones):
                    move = next(
                        (
                            m
                            for m in log.moves
                            if m.drone_id == drone_index + 1
                        ),
                        None,
                    )

                    if move is None:
                        continue

                    destination = move.target

                    if destination not in zones:
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

                            mid_x = (
                                float(current_zone_obj.coordinate_x)
                                + float(target_zone_obj.coordinate_x)
                            ) / 2.0
                            mid_y = (
                                float(current_zone_obj.coordinate_y)
                                + float(target_zone_obj.coordinate_y)
                            ) / 2.0

                            drone.start_move((mid_x, mid_y))

                            drone_zone_tracking[drone_index] = next_zone_name

                    else:
                        target = zones[destination]
                        drone.start_move(
                            (
                                float(target.coordinate_x),
                                float(target.coordinate_y),
                            )
                        )
                        drone_zone_tracking[drone_index] = destination

                current_log_index += 1

        screen.fill(pygame.Color("lightblue"))
        screen.blit(background, (0, 0))
        draw_connections(screen, view, zones, connections)
        draw_zones(screen, view, zones, small_zone)

        for index, drone in enumerate(drones):
            draw_drone(screen, view, drone, small_drone, index)

        clock.tick(60)
        pygame.display.flip()

    pygame.quit()


def main() -> None:
    """Dispatch the program according to the command-line arguments."""
    if len(sys.argv) == 2:
        run_simulation()
        run_pygame()
        return

    if len(sys.argv) == 3:
        mode = sys.argv[2]

        if mode == "text_output":
            run_simulation()
            return

        if mode == "visual":
            run_pygame()
            return

        raise ValueError(
            f"Unknown mode {mode}. Expected 'text_output' or 'visual'."
        )

    raise Exception(
        "Usage: uv run main.py <map_file> [text_output|visual]\n\n"
        "Makefile: the map file must be specified as `MAP=<file>`."
        "\nmake [run|visual|text_output] MAP=<map_file>"
    )


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        print_error(f"Runtime error: {e}")
