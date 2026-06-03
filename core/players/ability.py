# core/players/ability.py
# Базовый класс активных способностей классов.
# Каждый класс игрока имеет player.active_ability = экземпляр подкласса.


class ClassAbility:
    """
    Базовый класс активной способности персонажа.

    Поля:
      name        -- отображаемое имя
      description -- описание для тултипа
      max_charges -- максимум зарядов (заглушка, будет использоваться в будущем)
      charges     -- текущие заряды
      _used       -- использована ли в этом бою (основной gate для большинства)

    Хуки:
      on_combat_start(cm)  -- сброс состояния в начале боя
      on_turn_start(cm)    -- хук начала хода (штрафы, кулдауны и т.д.)
      activate(cm) -> bool -- основное действие; True = успех
      is_ready() -> bool   -- можно ли активировать прямо сейчас
    """

    def __init__(self, name: str, description: str, max_charges: int = 1):
        self.name        = name
        self.description = description
        self.max_charges = max_charges   # заглушка для будущей механики
        self.charges     = max_charges
        self._used       = False

    def on_combat_start(self, combat_manager) -> None:
        """Сброс состояния в начале каждого боя."""
        self._used    = False
        self.charges  = self.max_charges

    def on_turn_start(self, combat_manager) -> None:
        """Хук начала хода -- переопределить для штрафов/кулдаунов."""
        pass

    def is_ready(self) -> bool:
        """Можно ли активировать. Переопределить при необходимости."""
        return not self._used

    def activate(self, combat_manager) -> bool:
        """
        Основное действие способности.
        Возвращает True если активация прошла успешно.
        Переопределить в подклассах.
        """
        return False