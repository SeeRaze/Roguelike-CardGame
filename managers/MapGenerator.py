import random

FLOORS_PER_ACT = 20

NODE_WEIGHTS = {
    "COMBAT":   50,
    "CAMPFIRE": 15,
    "SHOP":     10,
    "CHEST":    12,
    "EVENT":    8,
    "ELITE":    5,
}

ROW_OVERRIDES = {
    0:                    "COMBAT",
    1:                    "COMBAT",                          # второй этаж тоже бой (не элита сразу)
    FLOORS_PER_ACT - 1:  "BOSS",
    FLOORS_PER_ACT - 2:  lambda: random.choice(["CAMPFIRE", "SHOP"]),
}


class MapNode:
    """Один узел на карте: тип комнаты + список соединений вниз."""
    def __init__(self, node_type: str, col: int, row: int):
        self.node_type   = node_type
        self.col         = col
        self.row         = row
        self.connections = []


def _pick_node_type(row: int) -> str:
    """Выбирает тип узла по правилам баланса."""
    override = ROW_OVERRIDES.get(row)
    if override is not None:
        return override() if callable(override) else override
    return random.choices(
        list(NODE_WEIGHTS.keys()),
        weights=list(NODE_WEIGHTS.values()),
        k=1
    )[0]


def generate_map() -> list:
    """Генерирует сетку 20×3 узлов. Возвращает map_grid."""
    map_grid = []

    for row in range(FLOORS_PER_ACT):
        row_nodes = [MapNode(_pick_node_type(row), col, row) for col in range(3)]
        map_grid.append(row_nodes)

    for row in range(FLOORS_PER_ACT - 1):
        for col in range(3):
            node = map_grid[row][col]
            targets = {col}
            if col > 0 and random.random() < 0.4:
                targets.add(col - 1)
            if col < 2 and random.random() < 0.4:
                targets.add(col + 1)
            node.connections = sorted(targets)

    for col in range(3):
        map_grid[FLOORS_PER_ACT - 2][col].connections = [1]

    return map_grid