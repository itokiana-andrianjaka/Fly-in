from typing import Optional
from model import Zone, Connection, ZoneType


# Représente l'état en transit d'un drone vers une zone restricted (2 tours)
class DroneInTransit:
    """Drone actuellement sur une connexion vers une zone restricted."""

    def __init__(self, drone_id: int, destination: str, conn_name: str) -> None:
        self.drone_id: int = drone_id
        # Nom de la connexion (ex: "hub-roof1") utilisé dans l'output
        self.conn_name: str = conn_name
        # Zone de destination (arrivée au prochain tour)
        self.destination: str = destination


class SimulationEngine:
    """
    Moteur de simulation principal.
    Gère le déplacement de tous les drones tour par tour
    en respectant toutes les règles du sujet.
    """

    def __init__(
        self,
        zones: dict[str, Zone],
        connections: list[Connection],
        nb_drones: int,
        start: str,
        end: str,
        drone_paths: list[list[str]],
    ) -> None:
        self.zones = zones
        self.connections = connections
        self.nb_drones = nb_drones
        self.start = start
        self.end = end
        # Chemin assigné à chaque drone (index = drone_id - 1)
        self.drone_paths = drone_paths

        # Position actuelle de chaque drone (None = arrivé à destination)
        self.drone_positions: list[Optional[str]] = [start] * nb_drones

        # Étape courante dans le chemin de chaque drone
        self.drone_step: list[int] = [0] * nb_drones

        # Drones en transit vers une zone restricted (2 tours)
        self.in_transit: list[Optional[DroneInTransit]] = [
            None
        ] * nb_drones

        # Drones ayant atteint la destination finale
        self.delivered: set[int] = set()

        # Log complet de la simulation (une entrée par tour)
        self.turn_logs: list[str] = []

        # Construction de la map des connexions pour accès rapide
        self._conn_map: dict[tuple[str, str], Connection] = {}
        for conn in connections:
            self._conn_map[(conn.first_zone, conn.second_zone)] = conn
            self._conn_map[(conn.second_zone, conn.first_zone)] = conn

    def _get_connection(
        self, z1: str, z2: str
    ) -> Optional[Connection]:
        """Retourne la connexion entre deux zones, ou None si inexistante."""
        return self._conn_map.get((z1, z2))

    def _zone_occupancy(
        self,
        zone_name: str,
        exclude_drones: Optional[set[int]] = None,
    ) -> int:
        """
        Compte le nombre de drones actuellement dans une zone donnée,
        en excluant optionnellement certains drones (ex : ceux qui partent).
        """
        count = 0
        for i, pos in enumerate(self.drone_positions):
            if exclude_drones and i in exclude_drones:
                continue
            if pos == zone_name and i not in self.delivered:
                count += 1
        return count

    def _conn_usage(
        self,
        z1: str,
        z2: str,
        planned_moves: dict[int, str],
    ) -> int:
        """
        Compte combien de drones utilisent déjà la connexion z1-z2
        dans les mouvements déjà planifiés ce tour.
        """
        conn = self._get_connection(z1, z2)
        if conn is None:
            return 0
        count = 0
        for drone_id, dest in planned_moves.items():
            src = self.drone_positions[drone_id]
            if src is None:
                continue
            c = self._get_connection(src, dest)
            if c is not None and (
                (c.first_zone == z1 and c.second_zone == z2)
                or (c.first_zone == z2 and c.second_zone == z1)
            ):
                count += 1
        return count

    def _make_conn_name(self, z1: str, z2: str) -> str:
        """
        Génère le nom de connexion pour l'output des zones restricted.
        Format : zone1-zone2 (ordre alphanumérique pour cohérence)
        """
        conn = self._get_connection(z1, z2)
        if conn is None:
            return f"{z1}-{z2}"
        return f"{conn.first_zone}-{conn.second_zone}"

    def run(self) -> list[str]:
        """
        Lance la simulation complète et retourne la liste des logs par tour.
        Chaque log est une ligne du format :
            D1-roof1 D2-corridorA
        """
        max_turns = 10000  # Sécurité anti-boucle infinie

        for turn in range(max_turns):
            if len(self.delivered) == self.nb_drones:
                break

            turn_moves: list[str] = []

            # ---- Étape 1 : Arrivée des drones en transit (restricted, tour 2)
            arriving: dict[int, str] = {}
            for i, transit in enumerate(self.in_transit):
                if transit is not None:
                    arriving[i] = transit.destination
                    self.in_transit[i] = None

            # ---- Étape 2 : Planification des nouveaux mouvements ----
            # planned_moves : drone_id -> zone_destination (ce tour)
            planned_moves: dict[int, str] = {}
            # Drones qui partent d'une zone (libèrent leur place)
            departing: set[int] = set()

            for i in range(self.nb_drones):
                if i in self.delivered:
                    continue
                if i in arriving:
                    # Ce drone arrive depuis transit, on le gère plus bas
                    continue
                if self.in_transit[i] is not None:
                    # Ne devrait pas arriver (géré au-dessus), sécurité
                    continue

                current_pos = self.drone_positions[i]
                if current_pos is None:
                    continue

                path = self.drone_paths[i]
                step = self.drone_step[i]

                # Trouver la prochaine étape dans le chemin
                next_zone_name: Optional[str] = None
                for j in range(step, len(path) - 1):
                    if path[j] == current_pos:
                        next_zone_name = path[j + 1]
                        break

                if next_zone_name is None:
                    # Drone déjà à la fin ou bloqué sans suite
                    continue

                next_zone = self.zones[next_zone_name]

                # Vérifier la connexion
                conn = self._get_connection(current_pos, next_zone_name)
                if conn is None:
                    continue

                # Vérifier la capacité de la connexion
                conn_used = self._conn_usage(
                    current_pos, next_zone_name, planned_moves
                )
                if conn_used >= conn.max_link_capacity:
                    # Connexion saturée ce tour : le drone attend
                    continue

                # Vérifier la capacité de la zone destination
                # (les drones qui partent libèrent de la place)
                if next_zone_name != self.end:
                    incoming_count = sum(
                        1
                        for d, dest in planned_moves.items()
                        if dest == next_zone_name
                    ) + sum(1 for d, dest in arriving.items()
                            if dest == next_zone_name)
                    occupancy = self._zone_occupancy(
                        next_zone_name, exclude_drones=departing
                    )
                    if (
                        occupancy + incoming_count
                        >= next_zone.max_drones
                    ):
                        # Zone pleine : le drone attend
                        continue

                # Le mouvement est possible : on le planifie
                if next_zone.zone_type == ZoneType.RESTRICTED:
                    # Restricted : 2 tours, le drone passe par la connexion
                    conn_name = self._make_conn_name(
                        current_pos, next_zone_name
                    )
                    self.in_transit[i] = DroneInTransit(
                        i, next_zone_name, conn_name
                    )
                    turn_moves.append(f"D{i + 1}-{conn_name}")
                    departing.add(i)
                    self.drone_positions[i] = None  # En transit
                else:
                    planned_moves[i] = next_zone_name
                    departing.add(i)

            # ---- Étape 3 : Application des mouvements planifiés ----
            for drone_id, dest in planned_moves.items():
                self.drone_positions[drone_id] = dest
                # Avancer dans le chemin
                path = self.drone_paths[drone_id]
                for j in range(len(path) - 1):
                    if path[j + 1] == dest:
                        self.drone_step[drone_id] = j + 1
                        break
                turn_moves.append(f"D{drone_id + 1}-{dest}")
                if dest == self.end:
                    self.delivered.add(drone_id)

            # ---- Étape 4 : Application des arrivées depuis transit ----
            for drone_id, dest in arriving.items():
                self.drone_positions[drone_id] = dest
                path = self.drone_paths[drone_id]
                for j in range(len(path) - 1):
                    if path[j + 1] == dest:
                        self.drone_step[drone_id] = j + 1
                        break
                turn_moves.append(f"D{drone_id + 1}-{dest}")
                if dest == self.end:
                    self.delivered.add(drone_id)

            # ---- Étape 5 : Enregistrement du log du tour ----
            if turn_moves:
                # Trie par numéro de drone pour un output lisible
                turn_moves.sort(key=lambda s: int(s.split("-")[0][1:]))
                self.turn_logs.append(" ".join(turn_moves))

        return self.turn_logs

    def print_results(self) -> None:
        """Affiche le résultat de la simulation dans le terminal."""
        print("\n=== Simulation Results ===")
        for line in self.turn_logs:
            print(line)
        total_turns = len(self.turn_logs)
        print(f"\nTotal turns: {total_turns}")
        print(f"Drones delivered: {len(self.delivered)}/{self.nb_drones}")
