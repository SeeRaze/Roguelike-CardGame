from core.rarity import Rarity
from core.relics.base import Relic
from core.relics.starter import LuckyClover, SpikedBracelet, ТочильныйКамень
from core.relics.elemental import ЭнергоЯдро, ДревнееОгниво, НамокшаяРукавица
from core.relics.advanced import (
    ОкровавленныйШприц, СердцеТитана, ГнилойКлык,
    ПроклятаяКорона, ФлаконСЖелчью, СвинцовыйНабалдашник,
    СтараяПиявка, СчастливаяМонетка, ЗасохшийКлевер,
    Заплатка, ЗаточенныйОсколок,
)

RELIC_POOL = {
    Rarity.COMMON: [
        LuckyClover,
        SpikedBracelet,
        ТочильныйКамень,
        СтараяПиявка,
        СчастливаяМонетка,
        ЗасохшийКлевер,
        Заплатка,
        ЗаточенныйОсколок,
    ],
    Rarity.UNCOMMON: [
        ДревнееОгниво,
        НамокшаяРукавица,
        ОкровавленныйШприц,
        ФлаконСЖелчью,
        СвинцовыйНабалдашник,
    ],
    Rarity.RARE: [
        ЭнергоЯдро,
        СердцеТитана,
        ГнилойКлык,
    ],
    Rarity.EPIC:      [],
    Rarity.LEGENDARY: [
        ПроклятаяКорона,
    ],
}

ALL_RELICS = [
    relic
    for relics in RELIC_POOL.values()
    for relic in relics
]