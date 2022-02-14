from enum import Enum


class SignedArrow(Enum):
    PLUS_MINUS = "+-"
    MORE_LESS = "><"
    UP_DOWN = "^v"
    AYE_LEI = "i!"
    STAR_HOLES = "*%"
    HIGH_LOW = "AV"
    HOOK_SINKER = "un"
    ARC_BOW = "UD"
    MIGHTY_WEAK = "MW"


SIGN_BY_ARROW = {}
for arrow in SignedArrow:
    SIGN_BY_ARROW[arrow.value[0]] = (1, arrow)
    SIGN_BY_ARROW[arrow.value[1]] = (-1, arrow)
