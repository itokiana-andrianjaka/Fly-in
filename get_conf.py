import sys
from pathlib import Path
from typing import Any

from parser import MapParser
from error import print_error


def get_conf() -> dict[str, Any]:
    """Backward-compatible helper for simple scripts.

    Reads `config.txt` located next to this module and returns a dict
    with keys used by other modules (for example: 'nb_drones').
    """
    config_path = Path(__file__).resolve().parent / sys.argv[1]
    parser = MapParser()
    try:
        parser.parsing_file(str(config_path))
    except Exception as e:
        print_error(str(e))

    return {
        "nb_drones": parser.nb_drones,
        "zones": parser.zones,
        "connections": parser.connections,
        "start_zone": parser.start_zone_name,
        "end_zone": parser.end_zone_name,
    }
