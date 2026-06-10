# core/cards/decomp.py
# Стихия ДЕКОМПИЛЯЦИЯ (С58): мета-модификатор над графом. Анти-щит (глушит генерацию
# X ходов + −50% текущего) + «окно эксплойта» (реакции по цели бьют сильнее). Узкий
# РАСХОДУЕМЫЙ амп (vs широкий пассив Кофе). Поглотил роль Раскола (анти-броня).
from core.cards.base import Card, DecompEffect
from core.rarity import Rarity


def create_disassembler():
    """«Дизассемблер» — пол-applier «окна эксплойта»."""
    return Card(
        name="Дизассемблер",
        cost=1,
        card_type="skill",
        description="Декомпиляция 2(3) х.: генерация щита заглушена, текущий щит −50%.",
        effects=[
            DecompEffect(2, 3),
        ],
    )


def create_reverse_engineer():
    """«Реверс-инжиниринг» — тяжёлый applier: длинное окно эксплойта без долгого розыгрыша."""
    return Card(
        name="Реверс-инжиниринг",
        cost=2,
        card_type="skill",
        description="Декомпиляция 4(5) х.: генерация щита заглушена, текущий щит −50%.",
        effects=[
            DecompEffect(4, 5),
        ],
        rarity=Rarity.UNCOMMON,
    )
