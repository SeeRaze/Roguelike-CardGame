"""Поражение игрока: фиксация конца забега + запись результата (С49).

check_player_defeat — единственная точка «игрок умер»: local-first запись забега на
диск (SaveManager) ДО сети (send_run_record), затем переход в лидерборд. Изолирует
I/O-тяжёлый концерн (диск/сеть/лидерборд) от чистой боевой логики прочих миксинов.
"""
from managers import SaveManager
from managers.network_manager import send_run_record


class DefeatMixin:
    """Конец игры по смерти игрока. Опирается на self.player/gm + статы gm."""

    def check_player_defeat(self) -> bool:
        """Проверка смерти игрока и запуск конца игры.
        Вызывается в конце хода И после активной способности
        (Берсерк бьёт себя сквозь щит и может умереть в свой ход).

        HP-долг (§4, С49): при HP-овердрафте пол смерти СДВИНУТ в минус
        (_hp_floor() = -HP_DEBT_MAX_OVERDRAFT) — игрок ВЫЖИВАЕТ в минусе (долг жизни даёт
        множитель урона), смерть наступает лишь на ДНЕ долга. Без флага пол = 0 → байт-в-байт."""
        if self.player.hp > self.player._hp_floor():
            return False

        self.player.hp = 0
        print("[СИСТЕМА] Здоровье игрока упало до 0!")

        current_floor = self.gm.current_floor if self.gm else 1
        monsters = self.gm.stats["monsters_killed"] if self.gm else 0
        bosses   = self.gm.stats["bosses_killed"]   if self.gm else 0
        kills_count = monsters + bosses
        max_dmg = self.gm.stats["max_damage_dealt"] if self.gm else 0
        player_class = type(self.player).__name__

        # Локальная мета-прогрессия (local-first): пишем итог забега на диск ДО сети,
        # чтобы лидерборд и «игра помнит тебя» работали даже офлайн (сеть — обогащение).
        from managers.network_manager import _get_username
        SaveManager.record_run({
            "username":   _get_username(),
            "class":      player_class,
            "max_floor":  current_floor,
            "kills":      kills_count,
            "bosses":     bosses,
            "max_damage": max_dmg,
        })

        print("[СЕТЬ] Отправляем рекорд напрямую в Google...")
        send_run_record(
            max_floor=current_floor, kills=kills_count,
            max_damage=max_dmg, player_class=player_class,
        )

        if self.gm:
            from ui.LeaderboardView import LeaderboardView
            LeaderboardView.load_data()
            self.gm.current_state = "LEADERBOARD"
        return True
