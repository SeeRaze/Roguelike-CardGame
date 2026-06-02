import random

FLOORS_PER_ACT = 20

NODE_WEIGHTS = {
    "COMBAT":   55,
    "CAMPFIRE": 15,
    "SHOP":     10,
    "CHEST":    12,
    "EVENT":    8,
}


class MapNode:
    """Один узел на карте: тип комнаты + список соединений вниз."""
    def __init__(self, node_type: str, col: int, row: int):
        self.node_type   = node_type   # COMBAT / CAMPFIRE / SHOP / CHEST / EVENT / BOSS
        self.col         = col         # 0, 1, 2 — колонка
        self.row         = row         # 0..19 — строка
        self.connections = []          # индексы колонок узлов СЛЕДУЮЩЕЙ строки


def _pick_node_type(row: int) -> str:
    """Выбирает тип узла по правилам баланса."""
    if row == 0:
        return "COMBAT"
    if row == FLOORS_PER_ACT - 1:
        return "BOSS"
    if row == FLOORS_PER_ACT - 2:
        return random.choice(["CAMPFIRE", "SHOP"])
    types   = list(NODE_WEIGHTS.keys())
    weights = list(NODE_WEIGHTS.values())
    return random.choices(types, weights=weights, k=1)[0]


def generate_map() -> list:
    """Генерирует сетку 20×3 узлов. Возвращает map_grid."""
    map_grid = []

    for row in range(FLOORS_PER_ACT):
        row_nodes = []
        for col in range(3):
            row_nodes.append(MapNode(_pick_node_type(row), col, row))
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