"""Function to retrieve configuration from a map file."""

import sys
from pathlib import Path
from typing import Any

from parser import MapParser
from error import print_error


def get_conf() -> dict[str, Any]:
    """Backward-compatible helper for simple scripts.

    Reads the map file passed as the first CLI argument and returns a dict
    with keys used by other modules.

    Returns:
        dict [str, Any]:
            A dictionary containing the configuration parameters:
            - "nb_drones": Number of drones to simulate.
            - "zones": Dictionary of zones with their coordinates.
            - "connections": List of connections between zones.
            - "start_zone": Name of the starting zone.
            - "end_zone": Name of the ending zone.
    """
    # Protection contre l'absence d'argument en ligne de commande
    if len(sys.argv) != 2:
        print_error(
            "Usage: uv run main.py <map_file> or When using "
            "the Makefile, the map file must be specified as `MAPS=<file>`."
            "\nmake run MAPS=<map_file>"
        )

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
