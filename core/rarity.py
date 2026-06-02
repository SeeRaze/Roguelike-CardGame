from enum import Enum


class Rarity(Enum):
    COMMON    = "common"
    UNCOMMON  = "uncommon"
    RARE      = "rare"
    EPIC      = "epic"
    LEGENDARY = "legendary"


RARITY_COLORS = {
    Rarity.COMMON:    (150, 150, 150),
    Rarity.UNCOMMON:  (80,  200, 120),
    Rarity.RARE:      (80,  140, 240),
    Rarity.EPIC:      (180,  80, 240),
    Rarity.LEGENDARY: (240, 180,  40),
}