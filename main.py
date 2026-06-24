import sys
from pathlib import Path

from get_conf import get_conf
from model import WINDOW_SIZE, Zone
from error import print_error
from view import View
from drone import Drone
from draw import draw_connections, create_drone_drawer, create_zones_drawer
from pathfinder import assign_paths_to_drones
from simulation import SimulationEngine

try:
    import pygame
except ModuleNotFoundError as er:
    print_error(str(er))
    sys.exit(1)


# Nombre de frames pygame entre chaque tour de simulation
FRAMES_PER_TURN: int = 80


def parse_turn_log(
    log_line: str,
    zones: dict[str, Zone],
) -> dict[int, tuple[float, float]]:
    """
    Lit une ligne de log de simulation et retourne
    un dictionnaire {drone_id: (x, y)} pour les drones qui bougent ce tour.
    Les drones en transit (connexion vers restricted) gardent
    une position interpolée entre départ et destination.
    """
    moves: dict[int, tuple[float, float]] = {}
    if not log_line.strip():
        return moves

    for token in log_line.strip().split():
        # Format : D<id>-<zone_ou_connexion>
        parts = token.split("-", 1)
        if len(parts) != 2:
            continue
        drone_id = int(parts[0][1:]) - 1  # "D1" -> index 0
        target = parts[1]

        if target in zones:
            z = zones[target]
            moves[drone_id] = (float(z.coordinate_x), float(z.coordinate_y))
        else:
            # Transit vers restricted : on affiche au milieu de la connexion
            conn_parts = target.split("-")
            if len(conn_parts) == 2:
                z1_name, z2_name = conn_parts
                if z1_name in zones and z2_name in zones:
                    z1 = zones[z1_name]
                    z2 = zones[z2_name]
                    mid_x = (z1.coordinate_x + z2.coordinate_x) / 2.0
                    mid_y = (z1.coordinate_y + z2.coordinate_y) / 2.0
                    moves[drone_id] = (mid_x, mid_y)
    return moves


def base_pygame() -> None:
    """
    Initialise pygame, lance la simulation en arrière-plan,
    puis affiche l'animation tour par tour.
    """
    pygame.init()

    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Fly-in")
    clock = pygame.time.Clock()

    base_dir = Path(__file__).resolve().parent

    # --- Vérification et chargement des fichiers graphiques ---
    image_files = {
        "background": base_dir / "background.png",
        "first_drone": base_dir / "first_drone.png",
        "zone": base_dir / "zone.png",
        "text_edge": base_dir / "text_edge.png",
    }
    for name, path in image_files.items():
        if not path.exists():
            print_error(f"Missing image file: {path.name}")

    background_ = pygame.image.load(
        str(image_files["background"])
    ).convert_alpha()
    zone_img = pygame.image.load(str(image_files["zone"])).convert_alpha()
    drone_img = pygame.image.load(
        str(image_files["first_drone"])
    ).convert_alpha()
    edge_img = pygame.image.load(str(image_files["text_edge"])).convert_alpha()

    background_ = pygame.transform.scale(background_, WINDOW_SIZE)
    small_drone = pygame.transform.scale(drone_img, (95, 95))
    small_zone = pygame.transform.scale(zone_img, (100, 70))
    edge_img = pygame.transform.scale(edge_img, (WINDOW_SIZE[0], 300))

    # --- Lecture de la configuration ---
    conf = get_conf()
    zones: dict[str, Zone] = conf["zones"]
    connections = conf["connections"]
    nb_drones: int = conf["nb_drones"]
    start_name: str = conf["start_zone"]
    end_name: str = conf["end_zone"]

    # --- Calcul des chemins et lancement de la simulation ---
    drone_paths = assign_paths_to_drones(
        nb_drones, zones, connections, start_name, end_name
    )
    if not drone_paths:
        print_error("No valid path found from start to end.")
        return

    engine = SimulationEngine(
        zones=zones,
        connections=connections,
        nb_drones=nb_drones,
        start=start_name,
        end=end_name,
        drone_paths=drone_paths,
    )
    turn_logs = engine.run()

    # Affichage du résultat dans le terminal dès que la simulation est prête
    engine.print_results()

    # --- Initialisation des drones à la zone de départ ---
    start_zone = zones[start_name]
    drones: list[Drone] = [
        Drone(
            position=(
                float(start_zone.coordinate_x),
                float(start_zone.coordinate_y),
            )
        )
        for _ in range(nb_drones)
    ]

    # --- Initialisation de la caméra ---
    view = View()
    zones_positions = [
        (z.coordinate_x, z.coordinate_y) for z in zones.values()
    ]
    view.best_view(
        zones_positions,
        (start_zone.coordinate_x, start_zone.coordinate_y),
    )

    draw_zones = create_zones_drawer()
    draw_drone = create_drone_drawer()

    # --- Variables de contrôle de l'animation ---
    current_turn: int = 0  # tour de simulation en cours
    frame_counter: int = 0  # frames écoulées depuis le début du tour
    paused: bool = True
    running: bool = True

    # Font pour afficher le numéro de tour et les infos
    font = pygame.font.SysFont("impact", 40)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    running = False
                elif event.key == pygame.K_a:
                    # Pause / reprise de l'animation
                    paused = not paused
                elif event.key == pygame.K_n:
                    # Avancer d'un tour manuellement
                    if current_turn < len(turn_logs):
                        current_turn += 1
                        frame_counter = 0
            view.handle_event(event)

        view.camera()

        # --- Avancement automatique des tours ---
        if not paused and current_turn < len(turn_logs):
            frame_counter += 1
            if frame_counter >= FRAMES_PER_TURN:
                current_turn += 1
                frame_counter = 0

        # --- Mise à jour des positions des drones selon le tour actuel ---
        if current_turn > 0 and current_turn <= len(turn_logs):
            log_line = turn_logs[current_turn - 1]
            moves = parse_turn_log(log_line, zones)
            for drone_id, target_pos in moves.items():
                if drone_id < len(drones):
                    drone = drones[drone_id]
                    if drone.target_pos != target_pos:
                        drone.start_move(target_pos)

        # Mise à jour de l'animation de chaque drone (rebond + interpolation)
        for drone in drones:
            drone.update()

        # --- Rendu graphique ---
        screen.fill(pygame.Color("lightblue"))
        screen.blit(background_, (0, 0))
        draw_connections(screen, view, zones, connections)
        draw_zones(screen, view, zones, small_zone)

        # Affichage des drones avec un léger décalage visuel entre eux
        for index, drone in enumerate(drones):
            old_pos = drone.position
            drone.position = (
                old_pos[0] + drone.offset_x,
                old_pos[1] + drone.offset_y,
            )
            draw_drone(screen, view, drone, small_drone, index)
            drone.position = old_pos

        # --- HUD : infos en bas de l'écran ---
        screen.blit(edge_img, (0, WINDOW_SIZE[1] - 80))
        total_turns = len(turn_logs)
        hud_turn = font.render(
            f"Turn: {current_turn}/{total_turns}  "
            f"[A] Go/Pause  |  [N] Next  |  [ESC/S] Quit",
            True,
            pygame.Color("black"),
        )
        screen.blit(hud_turn, (300, WINDOW_SIZE[1] - 50))

        # Message de fin quand tous les drones sont arrivés
        if current_turn >= total_turns:
            done_surf = font.render(
                f"Simulation complete! {nb_drones} drones delivered "
                f"in {total_turns} turns.",
                True,
                pygame.Color("yellow"),
            )
            screen.blit(done_surf, (20, WINDOW_SIZE[1] - 35))

        clock.tick(200)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_error("Usage: python main.py <map_file>")
    try:
        base_pygame()
    except Exception as e:
        print_error(f"Runtime error: {e}")
