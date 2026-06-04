from core.cards.base import Card
from core.cards.basic import create_strike, create_defend, create_heavy_blade, create_iron_wall
from core.cards.fire import create_ignite, create_fire_breath
from core.cards.water import create_splash, create_rain_cloud
from core.cards.poison import create_poison_stab, create_toxic_cloud, create_acid_shield
from core.cards.debuff import create_bash, create_neutralize, create_intimidate
from core.cards.buff import create_flex, create_battle_cry, create_thorn_armor
# Новые механики
from core.cards.heal import create_bandage, create_second_wind, create_elixir
from core.cards.buff.regen import create_regenerate, create_vitality, create_triage
from core.cards.buff.vampirism import create_drain, create_blood_feast, create_life_tap
from core.cards.debuff.bleed import create_lacerate, create_hemorrhage, create_open_wound
from core.cards.summon import create_summon_wolf, create_summon_golem
from core.cards.warrior import create_retribution
from core.cards.mage import create_boil