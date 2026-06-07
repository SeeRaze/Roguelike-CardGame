"""Позиционка боя: авто-таргетинг с перехватом + расстановка строя (С47/С48).

Тонкие обёртки над `core/positioning.py`, добавляющие гейт `positioning_enabled`
(opt-in, паттерн debt/stakes → baseline зелёный) и лог. Чистая геометрия живёт в
`core/positioning.py`; здесь — связь с живым боем (enemies/allies/player через self).
"""


class PositioningMixin:
    """Авто-цель одиночной атаки (перехват врага) + расстановка партии и врагов на
    2D-сетке РАНГ×ЛИНИЯ. NO-OP без флага positioning_enabled (ранги/линии = None →
    перехват ведёт себя как до позиционки, baseline зелёный)."""

    def get_target_enemy(self):
        """Первый ДОПУСТИМЫЙ живой враг — авто-таргетинг одиночной атаки С УЧЁТОМ
        перехвата врага (С48 §8, зеркало v1): пока жив ФРОНТ врага — цель только
        фронт; фронт пал → открывается тыл. Без рангов у врагов (позиционка off)
        intercept_targets вернёт всех живых → первый живой, байт-в-байт как раньше
        (baseline зелёный). Канал для авто-цели карт/реликвий/способностей."""
        from core.positioning import intercept_targets
        candidates = intercept_targets(self.enemies)
        return candidates[0] if candidates else None

    def _resolve_attack_target(self, target):
        """Цель ОДИНОЧНОЙ атаки игрока с учётом перехвата врага (С48 §8).
        None → авто (get_target_enemy, уже перехват-aware). ЯВНАЯ цель, прикрытая
        живым фронтом → СНАП на допустимую (фронт), чтобы клик в тыл не обходил
        перехват. Позиционка off / нет рангов у врагов → цель как есть (baseline).
        AoE-карты игнорируют target (бьют всех напрямую) → снап для них безвреден."""
        if target is None:
            return self.get_target_enemy()
        from core.positioning import has_positions, intercept_targets
        if not has_positions(self.enemies):
            return target
        candidates = intercept_targets(self.enemies)
        if target in candidates or not candidates:
            return target
        self.add_log_message(
            f"[ПОЗИЦИЯ] {getattr(target, 'name', 'Цель')} прикрыт(а) фронтом "
            f"— удар уходит по фронту."
        )
        return candidates[0]

    def _apply_positioning(self) -> None:
        """Расставить партию по рангам, ЕСЛИ позиционка включена (флаг
        player.positioning_enabled). Иначе NO-OP → ранги остаются None → перехват
        ведёт себя как раньше (baseline зелёный, паттерн opt-in как debt/stakes).

        Идемпотентно: переустанавливает ранги каждый вызов, поэтому новые саммоны,
        призванные посреди боя, получают ранг союзника, а протухшие — заменяются.
        Зовётся ботом после призыва (on_turn_begin); живая игра подключает вызов в
        __init__ (_init_positioning). Строй берётся из РАНТАЙМ player.formation_mirrored
        (тоггл Тактического Манёвра), с фолбэком на классовый mirrored_layout."""
        if not getattr(self.player, 'positioning_enabled', False):
            return
        from core.positioning import assign_party_ranks
        mirrored = getattr(self.player, 'formation_mirrored', None)
        if mirrored is None:
            mirrored = getattr(self.player, 'mirrored_layout', False)
        assign_party_ranks(self.player, self.allies, mirrored=mirrored)

    def _init_positioning(self) -> None:
        """Инициализация строя на СТАРТЕ боя: сброс рантайм-строя к классовому
        дефолту (флип Тактического Манёвра НЕ переносится между боями) + первичная
        расстановка. NO-OP без флага positioning_enabled (baseline/сим-baseline зелёный)."""
        if not getattr(self.player, 'positioning_enabled', False):
            return
        self.player.formation_mirrored = getattr(self.player, 'mirrored_layout', False)
        self._apply_positioning()
        # Враги тоже на сетке (§8): ранги фронт/тыл → симметричный перехват игрок→враг.
        from core.positioning import assign_enemy_ranks
        assign_enemy_ranks(self.enemies)

    def flip_formation(self) -> None:
        """Атомарный переворот строя партии — эффект [Tactical_Move] (карта/реликвия/
        босс). Тогглит рантайм formation_mirrored и переназначает ранги: фронт↔тыл.
        NO-OP без позиционки (положенный гард, как _apply_positioning)."""
        if not getattr(self.player, 'positioning_enabled', False):
            return
        cur = getattr(self.player, 'formation_mirrored', None)
        if cur is None:
            cur = getattr(self.player, 'mirrored_layout', False)
        self.player.formation_mirrored = not cur
        self._apply_positioning()
        self.add_log_message(" -> [МАНЁВР] Строй партии перевёрнут!")
