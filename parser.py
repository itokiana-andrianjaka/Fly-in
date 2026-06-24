from error import print_error
import re
from typing import Optional
from model import Zone, Connection, ZoneType

try:
    from pydantic import BaseModel, Field, ValidationError
except ModuleNotFoundError as err:
    print_error(f"{err}. Please install it using 'pip install pydantic'.")


class MapParser(BaseModel):
    nb_drones: int = Field(default=0)
    zones: dict[str, Zone] = {}
    connections: list[Connection] = []
    start_zone_name: str = Field(default="")
    end_zone_name: str = Field(default="")

    def _process_nb_drones(self, value: str, line_num: int) -> None:
        try:
            val_int = int(value)
            if val_int <= 0:
                raise ValueError()
            self.nb_drones = val_int
        except ValueError:
            raise ValueError(
                f"Line {line_num}: 'nb_drones' must be "
                "a positive integer (received: '{value}')."
            )

    def _process_hub(self, key: str, value: str, line_num: int) -> None:
        metadata_str = ""
        metadata_match = re.search(r"\[(.*)\]", value)

        if metadata_match:
            metadata_str = metadata_match.group(1)
            value = value.split("[")[0].strip()

        tokens = value.split()
        if len(tokens) != 3:
            raise ValueError(
                f"Line {line_num}: A hub must have a name and XY coordinates."
            )

        name, x_str, y_str = tokens

        if name in self.zones:
            raise ValueError(
                f"Line {line_num}: The '{name}' area is already defined."
            )

        try:
            x = int(x_str)
            y = int(y_str)
        except ValueError:
            raise ValueError(
                f"Line {line_num}: X and Y coordinates must be integers."
            )

        zone_type = ZoneType.NORMAL
        color: Optional[str] = None

        # Si c'est le départ ou l'arrivée,
        # la capacité par défaut s'adapte au nombre de drones
        if key in ("start_hub", "end_hub"):
            max_drones = self.nb_drones if self.nb_drones > 0 else 1
        else:
            max_drones = 1

        if metadata_str:
            tags = metadata_str.split()
            for tag in tags:
                if "=" not in tag:
                    raise ValueError(
                        f"Line {line_num}: Invalid metadata '{tag}'."
                    )

                info_key, info_val = tag.split("=", 1)
                info_key, info_val = info_key.strip(), info_val.strip()

                if info_key == "zone":
                    try:
                        zone_type = ZoneType(info_val)
                    except ValueError:
                        raise ValueError(
                            f"Line {line_num}: Unknown zone type '{info_val}'."
                        )
                elif info_key == "color":
                    color = info_val
                elif info_key == "max_drones":
                    try:
                        max_drones = int(info_val)
                    except ValueError:
                        raise ValueError(
                            f"Line {line_num}: "
                            "'max_drones' must be a positive integer."
                        )

        if key == "start_hub":
            if self.start_zone_name:
                raise ValueError(
                    f"Line {line_num}: 'start_hub' can only be defined once."
                )
            self.start_zone_name = name
        elif key == "end_hub":
            if self.end_zone_name:
                raise ValueError(
                    f"Line {line_num}: 'end_hub' can only be defined once."
                )
            self.end_zone_name = name

        # Interception des erreurs de contraintes de Pydantic (ex: ge=0, gt=1)
        try:
            self.zones[name] = Zone(
                name=name, coordinate_x=x, coordinate_y=y,
                zone_type=zone_type, color=color, max_drones=max_drones
            )
        except ValidationError as e:
            # Récupère le message d'erreur simplifié de Pydantic
            raw_msg = e.errors()[0]['msg']
            raise ValueError(
                f"Line {line_num}: "
                f"Validation failed for Hub '{name}' -> {raw_msg}"
            )

    def _process_connection(self, value: str, line_num: int) -> None:
        metadata_str = ""
        metadata_match = re.search(r"\[(.*)\]", value)
        if metadata_match:
            metadata_str = metadata_match.group(1)
            value = value.split("[")[0].strip()

        if "-" not in value:
            raise ValueError(
                f"Line {line_num}: Invalid connection "
                "(must use a hyphen, e.g.: zoneA-zoneB)."
            )

        parts = value.split("-")
        if len(parts) != 2:
            raise ValueError(
                f"Line {line_num}: Connection must have exactly one hyphen."
            )

        z1, z2 = parts[0].strip(), parts[1].strip()

        if z1 not in self.zones or z2 not in self.zones:
            raise ValueError(
                f"Line {line_num}: Connection impossible, "
                f"one or both of the zones ('{z1}' or '{z2}') does not exist."
            )

        max_link_capacity = 1
        if metadata_str:
            tags = metadata_str.split()
            for tag in tags:
                if "=" not in tag:
                    raise ValueError(
                        f"Line {line_num}: "
                        f"Invalid connection metadata '{tag}'."
                    )

                info_key, info_val = tag.split("=", 1)
                if info_key.strip() == "max_link_capacity":
                    try:
                        max_link_capacity = int(info_val.strip())
                    except ValueError:
                        raise ValueError(
                            f"Line {line_num}: "
                            "'max_link_capacity' must be a positive integer."
                        )

        try:
            self.connections.append(Connection(
                first_zone=z1, second_zone=z2,
                max_link_capacity=max_link_capacity
                )
            )
        except ValidationError as e:
            raw_msg = e.errors()[0]['msg']
            raise ValueError(
                f"Line {line_num}: "
                f"Validation failed for connection -> {raw_msg}"
            )

    def parsing_file(self, file_path: str) -> None:
        try:
            with open(file_path, "r") as file:
                done_first_line = 0
                for line_number, line in enumerate(file, 1):
                    if not line.strip() or line.strip()[0] == '#':
                        continue

                    if ":" not in line:
                        raise ValueError(f"Line {line_number}: missing ':'")

                    parts = line.split(":")
                    if len(parts) != 2:
                        raise ValueError(
                            f"Line {line_number}: ':' syntax error"
                        )

                    key = parts[0].strip()
                    value = parts[1].strip()

                    if key == "nb_drones" and not done_first_line:
                        self._process_nb_drones(value, line_number)
                        done_first_line = 1
                    elif (
                        key in ("start_hub", "end_hub", "hub")
                        and done_first_line
                    ):
                        self._process_hub(key, value, line_number)
                    elif key == "connection" and done_first_line:
                        self._process_connection(value, line_number)
                    else:
                        if key == "nb_drones":
                            raise ValueError(
                                f"Line {line_number}: The number of drones is "
                                "defined several times."
                            )

                        elif done_first_line:
                            raise ValueError(
                                f"Line {line_number}: Unknown prefix '{key}'"
                            )
                        else:
                            raise ValueError(
                                "The first line must be the number of drone"
                            )

            # Validations globales de fin de fichier
            if self.nb_drones <= 0:
                raise ValueError(
                    "Global configuration error: "
                    "'nb_drones' configuration is missing or invalid."
                )
            if not self.start_zone_name:
                raise ValueError(
                    "Global configuration error: "
                    "'start_hub' configuration is missing."
                )
            if not self.end_zone_name:
                raise ValueError(
                    "Global configuration error: "
                    "'end_hub' configuration is missing."
                )

            # Vérification de sécurité croisée :
            # nb_drones vs max_drones de départ
            if self.zones[self.start_zone_name].max_drones < self.nb_drones:
                raise ValueError(
                    "Global logic error: The start_hub "
                    f"'{self.start_zone_name}' capacity "
                    f"({self.zones[self.start_zone_name].max_drones}) is lower"
                    f" than the total number of drones ({self.nb_drones})."
                )

        except FileNotFoundError:
            print_error(f"The '{file_path}' file could not be found.")
        except ValueError as e:
            print_error(f"Parsing - {e}")
