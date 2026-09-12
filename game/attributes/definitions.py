from dataclasses import dataclass


VALOR = "valor"
INSTINCT = "instinct"
WILL = "will"
FORTITUDE = "fortitude"


@dataclass(frozen=True)
class AttributeDefinition:
    key: str
    title: str
    short_title: str
    introduced_in_act: int
    summary: str
    effect_lines: tuple[str, ...]


ATTRIBUTE_DEFINITIONS = {
    VALOR: AttributeDefinition(
        key=VALOR,
        title="Valor",
        short_title="VAL",
        introduced_in_act=1,
        summary="Offensive force and courage under pressure.",
        effect_lines=(
            "Increases physical damage.",
            "Increases critical damage.",
            "Contributes a smaller amount to maximum health.",
        ),
    ),
    INSTINCT: AttributeDefinition(
        key=INSTINCT,
        title="Instinct",
        short_title="INS",
        introduced_in_act=1,
        summary="Awareness, precision, and reaction speed.",
        effect_lines=(
            "Increases critical chance.",
            "Contributes to dodge chance.",
        ),
    ),
    WILL: AttributeDefinition(
        key=WILL,
        title="Will",
        short_title="WIL",
        introduced_in_act=2,
        summary="Mental focus and control over supernatural power.",
        effect_lines=(
            "Determines the power of Mage attacks.",
            "Increases critical chance.",
            "Increases critical damage.",
        ),
    ),
    FORTITUDE: AttributeDefinition(
        key=FORTITUDE,
        title="Fortitude",
        short_title="FOR",
        introduced_in_act=1,
        summary="The strength to endure injury and exhaustion.",
        effect_lines=(
            "Increases maximum health.",
            "Contributes a smaller amount to dodge chance.",
        ),
    ),
}


ATTRIBUTE_ORDER = (
    VALOR,
    INSTINCT,
    WILL,
    FORTITUDE,
)


ACT_ATTRIBUTE_ORDER = {
    1: (
        VALOR,
        INSTINCT,
        FORTITUDE,
    ),
    2: ATTRIBUTE_ORDER,
    3: ATTRIBUTE_ORDER,
}


def get_attribute_definition(
    attribute: str,
) -> AttributeDefinition:
    return ATTRIBUTE_DEFINITIONS[attribute]


def get_attribute_order(
    act: int,
) -> tuple[str, ...]:
    return ACT_ATTRIBUTE_ORDER.get(
        act,
        ATTRIBUTE_ORDER,
    )


def attribute_is_available(
    attribute: str,
    act: int,
) -> bool:
    definition = ATTRIBUTE_DEFINITIONS.get(
        attribute
    )
    return (
        definition is not None
        and definition.introduced_in_act <= act
    )


def get_attribute_tooltip_lines(
    attribute: str,
) -> tuple[str, ...]:
    definition = get_attribute_definition(attribute)
    return (
        definition.summary,
        *definition.effect_lines,
    )
