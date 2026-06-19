from get_conf import get_conf
from model import Connection


def all_connection(list_connex: list[Connection]) -> dict[str, list[str]]:
    all_connection_map: dict[str, list[str]] = {}
    for connex in list_connex:
        if connex.first_zone not in all_connection_map:
            all_connection_map[connex.first_zone] = [
                connex.second_zone
            ]
        else:
            all_connection_map[connex.first_zone].append(connex.second_zone)
    return all_connection_map


def get_all_existing_paths() -> list[list[str]]:
    all_connection_map = all_connection(get_conf()["connections"])
    start_node: str = get_conf()["start_zone"]
    end_node: str = get_conf()["end_zone"]

    all_paths: list[list[str]] = []

    current_path: list[str] = [start_node]

    def find_paths(current_node: str) -> None:
        if current_node == end_node:
            all_paths.append(list(current_path))
            return
        else:
            neighbor = all_connection_map.get(current_node, [])
            for hub in neighbor:
                if hub in current_path:
                    continue
                current_path.append(hub)
                find_paths(hub)
                current_path.pop()

    find_paths(start_node)

    return sorted(
        all_paths, key=len
    )
