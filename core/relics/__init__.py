from core.rarity import Rarity
from core.relics.base import Relic
from core.relics.starter import LuckyClover, SpikedBracelet, ТочильныйКамень
from core.relics.elemental import ЭнергоЯдро, ДревнееОгниво, НамокшаяРукавица

# Пул реликвий, сгруппированный по редкостям.
# Добавить реликвию = один импорт + одна строка в нужном списке.
RELIC_POOL = {
    Rarity.COMMON: [
        LuckyClover,
        SpikedBracelet,
        ТочильныйКамень,
    ],
    Rarity.UNCOMMON: [
        ДревнееОгниво,
        НамокшаяРукавица,
    ],
    Rarity.RARE: [
        ЭнергоЯдро,
    ],
    Rarity.EPIC:      [],
    Rarity.LEGENDARY: [],
}

# Плоский список всех реликвий (для обратной совместимости)
ALL_RELICS = [
    relic
    for relics in RELIC_POOL.values()
    for relic in relics
]