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

        # БЕЗУМИЕ (Берсерк): карта стоит 0 энергии, но берёт HP (стоимость × % max HP,
        # сквозь щит). Для hp_overdraft уходит в МИНУС → множитель урона. Энергия не тронута.
        # С57: цена в ПРОЦЕНТАХ от max HP (масштаб-инвариантно к росту max HP).
        if getattr(self.player, 'madness_active', False):
            pct = getattr(self.player, 'madness_hp_pct_per_cost', 0)
            hp_cost = int(effective_cost * pct * self.player.max_hp)
            if hp_cost > 0:
                self.player.lose_hp(hp_cost)
            self.add_log_message(
                f"[БЕЗУМИЕ] {selected_card.name}: -{hp_cost} HP (0 энергии)")
        else:
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
        # ENGINE: «Диспетчер задач» — следующая карта ×2. Флаг захватываем ДО apply
        # (карта-Диспетчер ставит его в своём apply → сама себя не дублирует).
        double_pending = getattr(self, "_dispatcher_pending", False)
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

        # ENGINE: «Диспетчер задач» ×2 — повтор карты под гардом (как Эхо).
        if double_pending:
            self._dispatcher_pending = False
            if self._trigger_guard.enter():
                selected_card.apply(self.player, target, self)
                self.add_log_message(
                    f"[ДИСПЕТЧЕР] {selected_card.name} срабатывает ×2!"
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

    def fuse_hand_cards(self, index_a: int, index_b: int) -> bool:
        """СЛИЯНИЕ КАРТ (Химик, §2): сплавить две карты руки в одну Глитч-карту
        (`core/fusion.fuse_cards`). Возвращает True при успехе.

        Гейтится `player.fusion_enabled` (ДОСТУП к механизму — как positioning_enabled);
        тормозится ресурсом Реагент (`FUSION_REAGENT_COST` за слияние). Глитч-карта
        ТРАНЗИЕНТНА на бой: ложится в руку на место источников, оригиналы уходят в
        discard (вернутся в пул при reset_deck следующего боя). Эффекты конкатенируются,
        стоимость = max(пол 1), прокачка сброшена.

        Отказывает (False, без побочек) если: доступ закрыт · индексы невалидны/совпадают ·
        не хватает Реагента · суммарный кап эффектов превышен (`can_fuse`). UI/бот обязаны
        заранее свериться; здесь — авторитетный enforcement."""
        from core.fusion import fuse_cards, can_fuse, FUSION_REAGENT_COST

        player = self.player
        if not getattr(player, "fusion_enabled", False):
            return False

        hand = self.deck_manager.hand
        n = len(hand)
        if index_a == index_b or not (0 <= index_a < n) or not (0 <= index_b < n):
            return False

        if getattr(player, "reagent", 0) < FUSION_REAGENT_COST:
            self.add_log_message("[ХИМИК] Не хватает Реагента для слияния!")
            return False

        card_a = hand[index_a]
        card_b = hand[index_b]
        if not can_fuse(card_a, card_b):
            self.add_log_message("[ХИМИК] Слияние превысит кап эффектов!")
            return False

        glitch = fuse_cards(card_a, card_b)
        player.reagent -= FUSION_REAGENT_COST

        # Источники → discard (вернутся в пул следующего боя); Глитч встаёт на меньший
        # из индексов, чтобы место в руке было предсказуемым. Удаляем по объектам
        # (индексы сдвигаются при первом remove).
        self.deck_manager.hand.remove(card_a)
        self.deck_manager.hand.remove(card_b)
        self.deck_manager.discard_pile.append(card_a)
        self.deck_manager.discard_pile.append(card_b)
        insert_at = min(index_a, index_b)
        self.deck_manager.hand.insert(min(insert_at, len(self.deck_manager.hand)), glitch)

        # Пассив «Нестабильность» (этап 3) — хук фьюжна. NO-OP, пока классом не задан.
        on_fuse = getattr(player, "on_fusion", None)
        if callable(on_fuse):
            on_fuse(glitch, self)

        self.add_log_message(
            f"[ХИМИК] Слияние: {card_a.name} + {card_b.name} → {glitch.name} "
            f"(стоимость {glitch.cost}). Реагент: {player.reagent}."
        )
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
