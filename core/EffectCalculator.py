class EffectCalculator:

    # Бонус урона за один заряд Шока, расходуемый при ударе (см. шаг 6).
    SHOCK_DAMAGE_PER_STACK = 3

    # Множитель урона по цели с Расколом, ПОКА у неё есть щит (см. шаг 4b).
    SHATTER_MULT = 3.0

    # НЕСТАБИЛЬНОСТЬ Мага (ступень «Гни»): при Мастерстве ≥ порога «контекст
    # переполняется» — флат-бонус Мастерства усиливается ×MULT (перегруз мощи).
    # Цена перегруза — глитч-урон в начале хода (Mage.on_turn_start_passive).
    MASTERY_INSTABILITY_THRESHOLD = 5
    MASTERY_INSTABILITY_MULT = 1.5

    @staticmethod
    def calculate_damage(attacker, target, base_damage,
                         game_manager=None, combat_manager=None,
                         dry_run: bool = False,
                         include_reactions: bool = True,
                         include_forge: bool = True,
                         card_override=None, snapshot_override=None,
                         breakdown=None):
        """Единый источник правды по урону. И боевой удар, и превью на карте, и
        проекция на HP-баре зовут ЕЁ — расхождений «показано vs нанесётся» нет.

        `dry_run` управляет ТОЛЬКО побочками (логи / расход зарядов Шока и стаков
        комбо / запись статистики). Все ДЕТЕРМИНИРОВАННЫЕ множители считаются всегда
        — поэтому превью (dry_run=True) с реальным контекстом даёт ровно то число,
        что нанесёт удар.

        Флаги для «гарантированного» превью (число на карте, _upgrade_design / решение
        юзера: условные реакции/ковка идут отдельными чипами, а не в основном числе):
          • `include_reactions=False` — убрать стихийные комбо (ComboRegistry);
          • `include_forge=False`     — убрать условные forge-теги (ForgeRegistry).
        `card_override`/`snapshot_override` — контекст ковки для превью БЕЗ живых
        транзиентов розыгрыша (combat_manager._card_being_played/_play_snapshot).
        `breakdown` (list) — если задан, заполняется кортежами (label, kind, value)
        для тултипа-разбора, где kind '+' = аддитивный, '×' = множитель."""
        player = None
        if combat_manager:
            player = getattr(combat_manager, 'player', None)
        is_player_attack = (player is not None and attacker is player)

        def _rec(label, kind, value):
            if breakdown is not None:
                breakdown.append((label, kind, value))

        # 1. ТРИГГЕР РЕЛИКВИЙ. dry_run прокидывается — реликвии с одноразовым
        #    зарядом (Заточенный Осколок) показывают бонус в превью, не тратя его.
        if game_manager and hasattr(game_manager, 'relics'):
            for relic in game_manager.relics:
                before = base_damage
                base_damage = relic.on_damage_calculated(
                    base_damage, is_player_attack, dry_run
                )
                if base_damage != before:
                    _rec(getattr(relic, 'name', 'Реликвия'), '+', base_damage - before)

        # 2. ЯРОСТЬ атакующего
        if attacker.strength > 0:
            if not dry_run:
                print(f" [ЯРОСТЬ] {attacker.name} добавляет "
                      f"+{attacker.strength} к урону!")
            base_damage += attacker.strength
            _rec("Сила", "+", attacker.strength)

        # 2c. МАСТЕРСТВО СТИХИЙ (Маг): +N к урону за каждое комбо в этом бою.
        # НЕСТАБИЛЬНОСТЬ (ступень «Гни»): на пороге (mastery≥THRESHOLD) контекст
        # «переполняется» — бонус усиливается ×MULT (перегруз). Цена — глитч-урон в
        # начале хода (Mage.on_turn_start_passive). Чистый множитель → считается и в превью.
        if is_player_attack:
            mastery = getattr(attacker, 'mastery', 0)
            if mastery > 0:
                bonus = mastery
                unstable = mastery >= EffectCalculator.MASTERY_INSTABILITY_THRESHOLD
                if unstable:
                    bonus = int(mastery * EffectCalculator.MASTERY_INSTABILITY_MULT)
                base_damage += bonus
                _rec("Мастерство", "+", bonus)
                if not dry_run:
                    tail = " [НЕСТАБИЛЬНОСТЬ: перегруз]" if unstable else ""
                    print(f" [МАСТЕРСТВО] +{bonus} к урону "
                          f"(стихийный резонанс).{tail}")

        # 2d. ДИСЦИПЛИНА (Воин «Соблюдай») — +N к урону за каждый стак. Накопитель
        # яруса 1 (стабильная ступень лестницы): растёт, когда Воин держит строй
        # (начал ход со щитом, см. on_turn_start_passive). Защита→дисциплина→атака —
        # формализует «защита=атака». Гейт is_player_attack; флат, как Мастерство/Сила.
        if is_player_attack:
            discipline = getattr(attacker, 'discipline', 0)
            if discipline > 0:
                base_damage += discipline
                _rec("Дисциплина", "+", discipline)
                if not dry_run:
                    print(f" [ДИСЦИПЛИНА] +{discipline} к урону (строй держится).")

        # 2b. (Передел Берсерка, этап 1) Старый плоский пассив «Ярость крови» (бонус от
        # недостатка HP) УБРАН — единственный движок урона Берсерка теперь HP-долг
        # множитель (шаг 8-ter, только в МИНУСЕ): награда за НЫРОК в красную зону, без
        # двойного счёта. Концепт «Отрицание Смерти».

        # 3. Слабость атакующего
        if attacker.weak > 0:
            base_damage = int(base_damage * 0.75)
            _rec("Слабость", "×", 0.75)

        final_damage = base_damage

        # 4. Уязвимость цели
        if target.vulnerable > 0:
            final_damage = int(final_damage * 1.5)
            _rec("Уязвимость", "×", 1.5)

        # 4b. РАСКОЛ цели — контра броне: пока у цели есть щит, урон ×SHATTER_MULT.
        # Множитель-ЧТЕНИЕ (заряды не тратятся, статус тикает по ходам). Условие
        # на щит проверяется в момент удара: при мульти-хите как только щит сбит,
        # последующие удары идут без бонуса.
        if target.shatter > 0 and target.shield > 0:
            final_damage = int(final_damage * EffectCalculator.SHATTER_MULT)
            _rec("Раскол", "×", EffectCalculator.SHATTER_MULT)
            if not dry_run and combat_manager:
                combat_manager.add_log_message(
                    f"[РАСКОЛ] Броня крошится: урон ×{EffectCalculator.SHATTER_MULT}!"
                )

        # 5. СТИХИЙНЫЕ КОМБО — data-driven реестр (core/ComboRegistry.py).
        # Множительные комбо (ПАР и т.п.) — условная «реакция», показываемая
        # отдельным чипом, поэтому в «гарантированное» число не входят
        # (include_reactions=False). Расход стаков/лог — только в реальном ударе.
        if include_reactions:
            from core.ComboRegistry import all_combos
            from core.ReactionOrder import ReactionPriority, order_keyed
            # Порядок комбо — из единого реестра приоритетов (ReactionOrder), а не
            # из неявного dict-порядка ComboRegistry: детерминирован и стабилен.
            for combo_key, combo in order_keyed(all_combos(),
                                                ReactionPriority.COMBO):
                if all(getattr(target, req, 0) > 0
                       for req in combo["requires"]):
                    final_damage = int(final_damage * combo["multiplier"])
                    _rec(combo["name"], "×", combo["multiplier"])
                    if not dry_run:
                        for req in combo["requires"]:
                            current = getattr(target, req, 0)
                            setattr(target, req, max(0, current - combo["consume"]))
                        if combat_manager:
                            combat_manager.add_log_message(combo["log"])
                            combat_manager._combo_triggered = True

        # 6. ШОК цели — флатовый разряд: +SHOCK_DAMAGE_PER_STACK за удар, −1 заряд.
        # Добавляется ПОСЛЕ множителей (уязвимость/комбо), чтобы оставаться плоским
        # и предсказуемым. Каждый отдельный удар (каждый DamageEffect карты) дренит
        # один заряд — отсюда синергия с мульти-хит/микро-атаками.
        if target.shock > 0:
            final_damage += EffectCalculator.SHOCK_DAMAGE_PER_STACK
            _rec("Шок", "+", EffectCalculator.SHOCK_DAMAGE_PER_STACK)
            if not dry_run:
                target.shock = max(0, target.shock - 1)
                if combat_manager:
                    combat_manager.add_log_message(
                        f"[ШОК] Разряд: +{EffectCalculator.SHOCK_DAMAGE_PER_STACK} "
                        f"урона (зарядов осталось: {target.shock})."
                    )

        # 7. УСЛОВНЫЕ ТЕГИ ПРОКАЧКИ (Сессия 39, _upgrade_design.md §4-5).
        # Локальный компаунд кат.4: множитель карты от её тегов, читаемых по СНИМКУ
        # состояния (§10.6, null-safe). Условная «реакция» → отдельный чип, в
        # «гарантированное» число не входит (include_forge=False). Множитель не имеет
        # побочек → считается и в превью (dry_run), если есть карта+снимок (живые
        # транзиенты розыгрыша ИЛИ overrides для превью). Без ковки шаг ИНЕРТЕН.
        if is_player_attack and include_forge:
            card = (card_override if card_override is not None
                    else getattr(combat_manager, "_card_being_played", None))
            snapshot = (snapshot_override if snapshot_override is not None
                        else getattr(combat_manager, "_play_snapshot", None))
            if card is not None and snapshot is not None:
                from core.ForgeRegistry import (
                    resolve_forge_record, forge_damage_multiplier,
                )
                rec = resolve_forge_record(card, player)
                if rec is not None and rec.get("slots"):
                    mult = forge_damage_multiplier(rec["slots"], snapshot)
                    if mult != 1.0:
                        final_damage = int(final_damage * mult)
                        _rec("Ковка", "×", mult)

        # 8. ЗАТОЧКА (Сессия 39.4) — player-level компаунд-множитель на ВСЕ атаки
        # игрока (player.atk_mult). Без побочек → считается и в превью (dry_run).
        # Инертно без ковки (atk_mult=1.0).
        if is_player_attack:
            atk_mult = getattr(player, "atk_mult", 1.0)
            if atk_mult != 1.0:
                final_damage = int(final_damage * atk_mult)
                _rec("Заточка", "×", atk_mult)

        # 8-bis. ДОЛГ ЭНЕРГИИ (§7) — овердрафт: глубже минус энергии → больше урон
        # (power now, pay later; гашение HP в end_turn_phase). Инертно при energy>=0
        # (нормальная игра без овердрафта). Линейная кривая по умолчанию, экспонента —
        # рубильником в core/debt. Pure → считается и в превью (показывает заём силы).
        if is_player_attack:
            energy = getattr(player, "energy", 0)
            if energy < 0:
                from core.debt import energy_debt_multiplier
                debt_mult = energy_debt_multiplier(-energy)
                if debt_mult != 1.0:
                    final_damage = int(final_damage * debt_mult)
                    _rec("Долг", "×", debt_mult)

        # 8-ter. ДОЛГ HP (§7, С49, субстрат Берсерка «Отрицание Смерти») — HP в МИНУСЕ →
        # больше урон (глубина минуса = заём силы у жизни). Инертно при hp>=0 (HP уходит
        # ниже 0 только при флаге hp_overdraft → клампы Creature). Композируется с энерго-
        # долгом. Pure → считается и в превью (показывает заём силы кровью).
        if is_player_attack:
            hp = getattr(player, "hp", 0)
            if hp < 0:
                from core.debt import hp_debt_multiplier
                hp_mult = hp_debt_multiplier(-hp)
                if hp_mult != 1.0:
                    final_damage = int(final_damage * hp_mult)
                    _rec("Долг HP", "×", hp_mult)

        # 9. RULESTACK (DAMAGE-scope) — глобальные правки урона от активных «правил»
        # (Ставки/парадоксы). Внешний слой: после всех боевых множителей; считается и
        # в превью (детерминированно, без побочек). Инертно при пустом стеке / отсутствии
        # rulestack у gm (симулятор-стаб, базовый забег без правил).
        rulestack = getattr(game_manager, "rulestack", None)
        if rulestack is not None:
            from core.rules import Scope
            ctx = {"damage": final_damage, "is_player_attack": is_player_attack,
                   "attacker": attacker, "target": target, "player": player,
                   "dry_run": dry_run}
            before = final_damage
            rulestack.apply(Scope.DAMAGE, ctx)
            final_damage = int(ctx["damage"])
            if final_damage != before:
                _rec("Правило", "+", final_damage - before)

        if not dry_run and game_manager and hasattr(game_manager, 'stats'):
            if final_damage > game_manager.stats.get("max_damage_dealt", 0):
                game_manager.stats["max_damage_dealt"] = final_damage

        return final_damage

    @staticmethod
    def preview(player, target, base_damage,
                combat_manager=None, game_manager=None, card=None):
        """Разбор урона для UI — БЕЗ побочек (dry_run). Возвращает dict:
          • guaranteed — число БЕЗ комбо-реакций и forge-тегов (основное на карте);
          • full       — урон со ВСЕМИ модификаторами (для проекции на HP-баре);
          • reactions  — [{'name','mult'}] стихийных комбо, что сработают на цели;
          • forge_mult — итоговый множитель forge-тегов карты (1.0 если нет);
          • forge_tags — [label] активных тегов (для тултипа);
          • steps      — [(label, kind, value)] полного разбора (для тултипа).
        Единый расчёт через calculate_damage → числа совпадают с боевым ударом."""
        # Снимок ковки для произвольной (наведённой) карты — без установки живых
        # транзиентов розыгрыша на combat_manager.
        snapshot = None
        if combat_manager is not None and card is not None \
                and hasattr(combat_manager, "build_preview_snapshot"):
            snapshot = combat_manager.build_preview_snapshot(card, target)

        common = dict(game_manager=game_manager, combat_manager=combat_manager,
                      dry_run=True, card_override=card, snapshot_override=snapshot)

        guaranteed = EffectCalculator.calculate_damage(
            player, target, base_damage,
            include_reactions=False, include_forge=False, **common)

        steps = []
        full = EffectCalculator.calculate_damage(
            player, target, base_damage,
            include_reactions=True, include_forge=True, breakdown=steps, **common)

        # Чип комбо: какие стихийные комбо готовы на цели (имя + множитель).
        reactions = []
        if target is not None:
            from core.ComboRegistry import all_combos
            for combo in all_combos().values():
                if all(getattr(target, req, 0) > 0 for req in combo["requires"]):
                    reactions.append({"name": combo["name"],
                                      "mult": combo["multiplier"]})

        # Чип ковки: множитель урон-канала тегов карты по снимку + их подписи.
        forge_mult, forge_tags = 1.0, []
        if card is not None and snapshot is not None:
            from core.ForgeRegistry import (
                resolve_forge_record, forge_damage_multiplier, TAGS,
            )
            rec = resolve_forge_record(card, player)
            if rec is not None and rec.get("slots"):
                forge_mult = forge_damage_multiplier(rec["slots"], snapshot)
                for slot in rec["slots"]:
                    spec = TAGS.get(slot.get("tag_id"))
                    if spec and spec.get("channel", "damage") == "damage":
                        forge_tags.append(spec["label"])

        return {
            "guaranteed": guaranteed,
            "full":       full,
            "reactions":  reactions,
            "forge_mult": forge_mult,
            "forge_tags": forge_tags,
            "steps":      steps,
        }
