from dataclasses import dataclass

from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType


DROPPED_ITEM_FLIGHT_MS = 340

ITEM_NAMES = {
    "potion": "Healing potion",
    "fire_bomb": "Fire bomb",
    "key": "Key",
    "guild_seal": "Guild seal",
    "gold": "Gold",
    "scroll_of_stoneflesh": "Scroll of Stoneflesh",
    "scroll_of_binding": "Scroll of Binding",
    "healing_scroll": "Healing Scroll",
    "scroll_of_arcane_impulse": "Scroll of Arcane Impulse",
}


@dataclass(frozen=True)
class GroundItem:
    source: str
    index: int
    position: tuple[int, int]
    kind: str
    amount: int = 1

    @property
    def name(self):
        name = ITEM_NAMES.get(self.kind, self.kind)
        if self.kind == "gold":
            return f"{name} x{self.amount}"
        return name

    @property
    def sprite_name(self):
        if self.kind == "gold":
            return "coin_pile" if self.amount > 1 else "coin"
        return self.kind


@dataclass(frozen=True)
class GroundItemRules:
    store_item: object
    locked_chest_gold: int = 1
    effect_prefix: str | None = None
    use_window: bool = True
    extra_items: object | None = None
    collect_special: object | None = None
    after_pickup: object | None = None


def store_counted_item(player, kind, potion_limit=None):
    if kind == "potion":
        if (
            potion_limit is not None
            and player.potion_count >= potion_limit
        ):
            return False
        player.potion_count += 1
        return True

    if kind == "key":
        player.key_count += 1
        return True

    return False


def ground_items(game_state, current_time, rules):
    floor = game_state.floor
    items = []

    for index, position in enumerate(floor.dropped_gold):
        items.append(
            GroundItem("gold", index, position, "gold")
        )

    for index, position in enumerate(floor.dropped_keys):
        items.append(
            GroundItem("key", index, position, "key")
        )

    for index, potion in enumerate(floor.potions):
        items.append(
            GroundItem(
                "potion",
                index,
                (potion.column, potion.row),
                "potion",
            )
        )

    for index, crate in enumerate(floor.breakable_crates):
        if not (
            crate.is_broken
            and crate.loot_available
            and crate.loot_kind in ("potion", "gold")
        ):
            continue

        items.append(
            GroundItem(
                "crate",
                index,
                (crate.column, crate.row),
                crate.loot_kind,
            )
        )

    for index, chest in enumerate(floor.chests):
        if not (chest.is_open and chest.loot_available):
            continue

        kind = (
            chest.contains
            if chest.contains in ITEM_NAMES
            else "gold"
        )
        amount = (
            rules.locked_chest_gold
            if kind == "gold" and chest.requires_key
            else 1
        )

        items.append(
            GroundItem(
                "chest",
                index,
                (chest.column, chest.row),
                kind,
                amount,
            )
        )

    for index, dropped in enumerate(floor.dropped_consumables):
        if current_time - dropped.thrown_at < DROPPED_ITEM_FLIGHT_MS:
            continue

        items.append(
            GroundItem(
                "dropped",
                index,
                dropped.destination,
                dropped.kind,
            )
        )

    if rules.extra_items is not None:
        items.extend(rules.extra_items(game_state))

    return tuple(items)


def ground_items_at_player(game_state, current_time, rules):
    floor = game_state.floor
    position = (floor.player_column, floor.player_row)

    return tuple(
        item
        for item in ground_items(game_state, current_time, rules)
        if item.position == position
    )


def pick_up_ground_item(game_state, item, current_time, rules):
    if item not in ground_items_at_player(
        game_state,
        current_time,
        rules,
    ):
        return False

    floor = game_state.floor
    player = game_state.player

    if rules.collect_special is not None:
        result = rules.collect_special(game_state, item)
        if result is not None:
            if result and rules.after_pickup is not None:
                rules.after_pickup(game_state)
            return result

    if item.kind == "gold":
        player.gold_count += item.amount
        game_state.run_stats.gold_earned += item.amount
    elif not rules.store_item(player, item.kind):
        add_log_message(
            game_state.combat_log,
            "There is no room for this item.",
            category="warning",
        )
        return False

    if item.source == "gold":
        floor.dropped_gold.pop(item.index)
    elif item.source == "key":
        floor.dropped_keys.pop(item.index)
    elif item.source == "potion":
        floor.potions.pop(item.index)
    elif item.source == "dropped":
        floor.dropped_consumables.pop(item.index)
    elif item.source == "crate":
        crate = floor.breakable_crates[item.index]
        crate.loot_available = False
        crate.loot_fire_turns_remaining = None
    elif item.source == "chest":
        floor.chests[item.index].loot_available = False

    effect_kind = (
        "gold_pile"
        if item.kind == "gold" and item.amount > 1
        else item.kind
    )

    if rules.effect_prefix is not None:
        setattr(
            player,
            f"{rules.effect_prefix}_pickup_kind",
            effect_kind,
        )
        setattr(
            player,
            f"{rules.effect_prefix}_pickup_origin",
            item.position,
        )
        setattr(
            player,
            f"{rules.effect_prefix}_pickup_started_at",
            current_time,
        )

    game_state.emit(
        GameEvent(
            type=GameEventType.PICKUP,
            actor="hero",
            destination=item.position,
            data={"kind": effect_kind},
        )
    )
    add_log_message(
        game_state.combat_log,
        f"Hero picks up {item.name}.",
        category="loot",
    )

    if rules.after_pickup is not None:
        rules.after_pickup(game_state)

    return True


def collect_ground_gold(game_state, current_time, rules):
    collected = False

    while True:
        item = next(
            (
                candidate
                for candidate in ground_items_at_player(
                    game_state,
                    current_time,
                    rules,
                )
                if candidate.kind == "gold"
            ),
            None,
        )
        if item is None:
            return collected

        if not pick_up_ground_item(
            game_state,
            item,
            current_time,
            rules,
        ):
            return collected

        collected = True
