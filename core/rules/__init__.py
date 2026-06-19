# core/rules/ — слой «правок правил» (RuleStack), фундамент «слома игры».
# Спека: _rulestack_design.md (корень репо).
from core.rules.RuleStack import RuleMod, RuleStack, Scope
from core.rules.stakes import Stake, STAKES, is_hardcore_active

__all__ = ["Scope", "RuleMod", "RuleStack", "Stake", "STAKES", "is_hardcore_active"]
