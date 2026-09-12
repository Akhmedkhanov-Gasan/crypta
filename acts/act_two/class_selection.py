from acts.act_one.settings import (
    PLAYER_STARTING_ATTRIBUTE_RANKS,
    PLAYER_STARTING_STATS,
)
from acts.act_two.progression import (
    transfer_mage_valor_investment,
)
from acts.act_two.settings import (
    CLASS_BASE_ATTRIBUTE_RANKS,
    CLASS_STARTING_STATS,
)
from game.attributes import (
    apply_attribute_rank_transition,
    apply_player_stat_transition,
)


def apply_act_two_class_selection(
    player,
    chosen_class: str,
) -> dict[str, int]:
    previous_ranks = dict(player.attribute_ranks)
    previous_health = player.health

    player.player_class = chosen_class

    apply_player_stat_transition(
        player,
        PLAYER_STARTING_STATS,
        CLASS_STARTING_STATS[chosen_class],
    )
    apply_attribute_rank_transition(
        player,
        PLAYER_STARTING_ATTRIBUTE_RANKS,
        CLASS_BASE_ATTRIBUTE_RANKS[chosen_class],
    )
    transfer_mage_valor_investment(
        player,
        previous_ranks,
    )

    player.health = min(
        previous_health,
        player.max_health,
    )

    return previous_ranks
