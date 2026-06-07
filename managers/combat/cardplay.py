"""Розыгрыш карты игроком + снимок контекста для тегов прокачки/превью (С49).

play_card_by_index — главный путь действия игрока: энергия (с овердрафтом долга §7),
перехват цели, apply + Эхо-ретриггеры под предохранителем, post-хуки реликвий/врагов,
сброс в discard/exile, обработка смертей и проверка победы в момент килла.
_build_play_snapshot — заморозка контекста на момент намерения (§10.6), читают
предикаты тегов ForgeRegistry; build_preview_snapshot — тот же снимок для UI-превью.
"""


class CardPlayMixin:
    """Розыгрыш карты и снимок состояния. Опирается на инфру оркестратора
    (deck_manager/player/_trigger_guard/_guarded/_resolve_attack_target/
    _process_enemy_deaths/_check_victory/add_log_message)."""

    def play_card_by_index(self, card_index, target=None):
        """Разыграть карту по индексу в руке.
        Если target передан — используется указанный враг, иначе авто-таргетинг."""
        if card_index < 0 or card_index >= len(self.deck_manager.hand):
            return False

        selected_card = self.deck_manager.hand[card_index]
        effective_cost = getattr(selected_card, 'temp_cost', selected_card.cost)

        overdraft = getattr(self.player, 'energy_overdraft', False)
        if self.player.energy < effective_cost:
            if not overdraft:
                self.add_log_message("[!] Не хватает энергии!")
                return False
            # Долговой движок (§7): уходим в минус, но НЕ глубже жёсткого пола
            # (амплитудный гард-рейл DEBT_MAX_OVERDRAFT).
            from core.debt import DEBT_MAX_OVERDRAFT
            if effective_cost - self.player.energy > DEBT_MAX_OVERDRAFT:
                self.add_log_message("[!] Долг энергии слишком глубок!")
                return False

        self.player.use_energy(effective_cost, allow_debt=overdraft)
        self.add_log_message(f"Вы разыграли: {selected_card.name}")

        self._combo_triggered = False
        target = self._resolve_attack_target(target)
        if target is None or target.hp <= 0:
            self.add_log_message("[!] Нет целей для атаки!")
            return False
        # Транзиентная ссылка на разыгрываемую карту: FlowEffect (стихия Воздух)
        # читает её, чтобы НЕ удешевлять саму себя (она ещё в руке во время apply).
        self._card_being_played = selected_card
        # СНИМОК состояния на момент намерения (§10.6): предикаты тегов прокачки
        # читают ЕГО, а не живое поле — заморожен до того, как apply/эхо/детонации
        # изменят руку/статусы/цель. Считается ОДИН раз за розыгрыш.
        self._play_snapshot = self._build_play_snapshot(target)
        # Сброс предохранителя на новый розыгрыш: детонации/Эхо этой карты считаются
        # с нуля (§10.2). Первичный apply — не триггер, бюджет не тратит.
        self._trigger_guard.depth = 0
        selected_card.apply(self.player, target, self)

        # Эхо (ретриггер): каждый заряд эха на игроке заставляет карту
        # сработать повторно. Заряды снимаются ДО повторов — карта, генерирующая
        # эхо сама, НЕ зациклится (новые заряды лягут уже после всех повторов).
        echo_stacks = self.player.echo
        if echo_stacks > 0:
            self.player.echo = 0
            for i in range(echo_stacks):
                # Каждый ретриггер — событие триггера: предохранитель обрывает
                # цепочку на MAX_TRIGGER_DEPTH (суммарно с детонациями розыгрыша).
                if not self._trigger_guard.enter():
                    self.add_log_message(
                        "[ПРЕДОХРАНИТЕЛЬ] Каскад триггеров оборван (глубина)."
                    )
                    break
                selected_card.apply(self.player, target, self)
                self.add_log_message(
                    f"[ЭХО] {selected_card.name} срабатывает повторно "
                    f"({i + 1}/{echo_stacks})!"
                )

        self._card_being_played = None
        self._play_snapshot = None
        # Карта сыграна — счётчик для предикатов first/nth card (читается ИЗ снимка,
        # инкремент ПОСЛЕ розыгрыша, чтобы первая карта за ход видела play_index=0).
        self.cards_played_this_turn += 1

        self.player.on_card_played_passive(selected_card, self)

        # Post-хуки розыгрыша под предохранителем (R2): реликвии и враги реагируют
        # на сыгранную карту. Сейчас они только меняют состояние (щит/золото/
        # эскалация), но будущий хук, играющий эффект, мог бы рекурсить — гард
        # обрывает каскад. Это ОТДЕЛЬНОЕ событие после полного разрешения розыгрыша
        # (apply+эхо+детонации завершены) → свой бюджет глубины, сброс с нуля, чтобы
        # хуки не наказывались за глубину эхо карты, но были защищены от своей рекурсии.
        self._trigger_guard.depth = 0
        if self.gm and hasattr(self.gm, 'relics'):
            for relic in self.gm.relics:
                self._guarded(
                    f"реликвия {getattr(relic, 'name', '?')}",
                    lambda relic=relic: relic.on_card_played(selected_card, self),
                )

        # Хук боссов/врагов: реакция на розыгрыш карты (Архивариус: +щит за карту).
        for e in self.enemies:
            if e.hp > 0 and hasattr(e, 'on_card_played'):
                self._guarded(
                    f"враг {getattr(e, 'name', '?')}",
                    lambda e=e: e.on_card_played(selected_card, self.player, self),
                )

        if hasattr(selected_card, 'temp_cost'):
            del selected_card.temp_cost

        self.deck_manager.hand.remove(selected_card)
        if getattr(selected_card, 'exile', False):
            self.deck_manager.exile_pile.append(selected_card)
            self.add_log_message(
                f" [ИЗГНАНИЕ] {selected_card.name} изгнана до конца боя."
            )
        else:
            self.deck_manager.discard_pile.append(selected_card)

        # Смерть врага обрабатывается в МОМЕНТ убивающего действия (как в фазе врага):
        # on_kill реликвий, счётчик убийств, перенос стаи. ДО _check_victory, иначе
        # победа картой ушла бы в награды мимо обработки смерти (потеря снежного кома).
        self._process_enemy_deaths()

        # Победа МОГЛА наступить прямо в этом розыгрыше (карта/эхо/детонации добили
        # последнего врага) → обрываем ход немедленно, без «лишней» фазы.
        self._check_victory()
        return True

    def _build_play_snapshot(self, target, card=None) -> dict:
        """Снимок контекста на момент намерения разыграть карту (§10.6). Предикаты
        тегов прокачки (core/ForgeRegistry.py) читают ТОЛЬКО его — заморожен до
        apply/эха/детонаций. Цель тоже заморожена → null-safe (§10.7): даже если
        враг погибнет в каскаде, снимок хранит прежний стак яда/крови. Ключи
        совпадают с тем, что читают предикаты ForgeRegistry. `card` — разыгрываемая
        (или наведённая, для превью) карта; по умолчанию — текущая транзиентная."""
        p = self.player
        card = card if card is not None else self._card_being_played
        max_hp = getattr(p, "max_hp", 0) or 1
        # Рука ПОСЛЕ изъятия текущей карты (для empty_hand): карта ещё в hand на
        # момент снимка, поэтому −1.
        hand_after = max(0, len(self.deck_manager.hand) - 1)
        # Сколько АТАКУЮЩИХ карт осталось бы в руке (для оборонного тега bulwark:
        # «рука только из защиты»). Считаем по наличию DamageEffect, исключая
        # саму разыгрываемую/наведённую карту.
        from core.cards.base import DamageEffect
        hand_attack = sum(
            1 for c in self.deck_manager.hand
            if c is not card
            and any(isinstance(e, DamageEffect) for e in getattr(c, "effects", []))
        )
        return {
            "play_index": self.cards_played_this_turn,   # 0 = первая карта за ход
            "hand_after": hand_after,
            "hand_attack": hand_attack,
            "hp_frac":    p.hp / max_hp,
            "shield":     getattr(p, "shield", 0),
            "barrier":    getattr(p, "barrier", 0),
            "mastery":    getattr(p, "mastery", 0),
            "minions":    sum(1 for a in self.allies if a.hp > 0),
            "tgt_poison": getattr(target, "poison", 0),
            "tgt_bleed":  getattr(target, "bleed", 0),
        }

    def build_preview_snapshot(self, card, target) -> dict:
        """Снимок для ПРЕВЬЮ урона на карте (UI): тот же контент, что у розыгрыша,
        но для произвольной наведённой карты и БЕЗ установки живых транзиентов
        (_card_being_played/_play_snapshot). Используется EffectCalculator.preview."""
        return self._build_play_snapshot(target, card=card)
