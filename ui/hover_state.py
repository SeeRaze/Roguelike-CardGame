# ui/hover_state.py
# Всё hover-состояние кадра в одном объекте. Сбрасывается в начале update().
from dataclasses import dataclass
from typing import Optional


@dataclass
class HoverState:
    """Всё hover-состояние за один кадр. Сбрасывается в update()."""
    card_index:   int              = -1
    card_rect:    Optional[object] = None
    card_obj:     Optional[object] = None
    status_key:   Optional[str]    = None
    status_val:   int              = 0
    end_turn:     bool             = False
    map_col:      Optional[int]    = None
    relic_obj:    Optional[object] = None
    pile_type:    Optional[str]    = None  # "draw" | "discard" | None

    def reset(self):
        self.card_index  = -1
        self.card_rect   = None
        self.card_obj    = None
        self.status_key  = None
        self.status_val  = 0
        self.end_turn    = False
        self.map_col     = None
        self.relic_obj   = None
        self.pile_type   = None
