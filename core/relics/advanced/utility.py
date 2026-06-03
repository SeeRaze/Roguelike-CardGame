# core/relics/advanced/utility.py
# Реликвии темы «утилита и экономика».
from core.relics.base import Relic
from core.rarity import Rarity


class СчастливаяМонетка(Relic):
    """При открытии обычного сундука +10 золота."""

    def __init__(self):
        super().__init__(
            "Счастливая Монетка",
            "При открытии обычного сундука получаете +10 золота.",
            Rarity.COMMON,
        )

    def on_chest_opened(self, chest_type: str, game_manager):
        if chest_type == "common":
            game_manager.player_gold += 10
            print(f"[Реликвия] '{self.name}': +10 золота!")
