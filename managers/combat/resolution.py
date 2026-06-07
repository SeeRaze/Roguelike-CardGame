"""Разрешение исходов боя: смерть врага/союзника, победа, перенос стаи (С49).

Единая точка обработки «кто-то умер» — на килле картой/способностью (через
_process_enemy_deaths) и в фазе врага. Победа обрывает бой немедленно (нет лишней
фазы, С43). Перенос стаи Призывателя (persist) — при поражении последнего врага.
Все реакционные свипы идут под предохранителем глубины (self._guarded_action).
"""


class ResolutionMixin:
    """Смерть/победа/персистентность. Опирается на инфру оркестратора
    (self.gm/enemies/allies/player/add_log_message/_guarded_action) и ручку
    self.MAX_PERSISTENT_ALLIES."""

    def _check_victory(self) -> bool:
        """Немедленный переход в награды, как только ВСЕ враги мертвы.

        Зовётся сразу после любого источника урона игрока (розыгрыш карты, эхо,
        детонации, активная способность) и в конце фазы врага. Раньше победа
        ловилась только по клику в InputHandler → после убийства последнего врага
        у игрока оставалась «лишняя» фаза хода (можно было играть карты/способности).
        Теперь бой обрывается сразу.

        Безопасно для симулятора: bot-`gm` (_StubGM) не имеет distribute_combat_rewards
        и не держит current_state == "COMBAT" → ветка не срабатывает, baseline цел.
        Идемпотентно: distribute_combat_rewards сам выходит, если state != COMBAT."""
        if not self.enemies or any(e.hp > 0 for e in self.enemies):
            return False
        gm = self.gm
        if (gm is not None
                and getattr(gm, "current_state", None) == "COMBAT"
                and hasattr(gm, "distribute_combat_rewards")):
            # Хук победы (Берсерк: |минус HP|→FP) — ДО раздачи наград (пик может изменить
            # состояние игрока). NO-OP для обычных классов. Живой путь победы.
            self.player.on_combat_won(self)
            gm.distribute_combat_rewards()
            return True
        return False

    def _check_enemy_death(self, enemy):
        """Вызывается после каждого источника урона врагу.
        Если враг умер — вызывает on_kill на всех реликвиях и обновляет статистику."""
        if enemy.hp > 0:
            return
        # Уже обработан — не дёргаем повторно
        if getattr(enemy, '_death_processed', False):
            return
        enemy._death_processed = True

        self.add_log_message(f"=== {enemy.name} ПОВЕРЖЕН! ===")

        # Хук on_kill -- реликвии
        if self.gm and hasattr(self.gm, 'relics'):
            for relic in self.gm.relics:
                relic.on_kill(enemy, self)

        # Статистика
        if self.gm and hasattr(self.gm, 'stats'):
            if getattr(enemy, 'is_boss', False):
                self.gm.stats["bosses_killed"] = \
                    self.gm.stats.get("bosses_killed", 0) + 1
            else:
                self.gm.stats["monsters_killed"] = \
                    self.gm.stats.get("monsters_killed", 0) + 1

        # Труп на сетке (субстрат Некроманта): павший враг НЕ исчезает бесследно —
        # помечается тегом [Corpse], сохраняет rank/line, продолжает занимать клетку
        # (блокирует будущие свапы). Инертно: труп = тот же мёртвый объект в self.enemies
        # (victory/таргетинг фильтруют живых) + метка → baseline зелёный. Поглощение/взрыв
        # трупа придут с классом Некроманта. Метим ОДИН раз (внутри death-блока).
        from core.corpse import mark_corpse
        mark_corpse(enemy)

        # Бой выигран (все враги повержены) — сохранить стаю до следующего боя.
        # Единая точка для всех путей победы (карта/союзник/статус добил врага).
        if all(e.hp <= 0 for e in self.enemies):
            self._persist_allies()

    def _process_enemy_deaths(self):
        """Обработать смерть ВСЕХ врагов после действия игрока (розыгрыш карты /
        активная способность). Симметрично фазе врага, где _check_enemy_death
        предшествует проверке победы. AoE-детонации (electro_blast и т.п.) могут
        добить нескольких сразу → свип по всему self.enemies.

        Под _guarded_action: своё событие, сброс глубины гарда, конечность каскада
        (инвариант R2/R3). on_kill срабатывает ПОСЛЕ всех per-play реакций (после
        RELIC_HOOK/ENEMY_HOOK), т.е. в момент убивающего действия, а не в конце хода.
        Идемпотентно: _check_enemy_death помечает enemy._death_processed → повторный
        свип в end_turn_phase no-op."""
        self._guarded_action(
            "обработка смертей врагов",
            lambda: [self._check_enemy_death(e) for e in self.enemies],
        )

    def _check_ally_death(self, ally):
        """Удалить мёртвого союзника из списка."""
        if ally.hp > 0:
            return
        self.add_log_message(f"[СОЮЗНИК] {ally.name} пал в бою!")
        if ally in self.allies:
            self.allies.remove(ally)

    def _restore_persistent_allies(self):
        """Восстановить выживших союзников из прошлого боя (Призыватель).
        Транзиентное боевое состояние (щит/статусы) обнуляем — переносим
        только саму единицу с её текущим HP."""
        carried = getattr(self.player, 'persistent_allies', None)
        if not carried:
            return
        for ally in carried:
            if ally.hp <= 0:
                continue
            ally.shield = 0
            for key in ally.statuses:
                ally.statuses[key] = 0
            self.allies.append(ally)

    def _persist_allies(self):
        """Сохранить выживших союзников до следующего боя (вызывается при
        победе). Переносим не больше MAX_PERSISTENT_ALLIES — сильнейших
        (по HP, затем по атаке), чтобы стая не копилась безгранично."""
        survivors = [a for a in self.allies if a.hp > 0]
        survivors.sort(key=lambda a: (a.hp, a.attack_power), reverse=True)
        self.player.persistent_allies = survivors[:self.MAX_PERSISTENT_ALLIES]
