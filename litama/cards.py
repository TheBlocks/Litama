from typing import List

from structures import Card, Pos, Player

def card_to_info(c: Card) -> str:
    res = ['0'] * 25
    for p in c.moves:
        res[12 + p.y * 5 + p.x] = '1'
    return {
        "name": c.name,
        "moves": ''.join(res),
        "color": c.color.value
    }

# Original cards
# From https://uploads.johnhqld.com/uploads/20180926171936/Onitama-Cards-1024x576.jpg

RABBIT = Card("rabbit", Player.BLUE, [Pos(-1, -1), Pos(1, 1), Pos(2, 0)])
MONKEY = Card("monkey", Player.BLUE, [Pos(-1, -1), Pos(-1, 1), Pos(1, -1), Pos(1, 1)])
BOAR = Card("boar", Player.RED, [Pos(1, 0), Pos(-1, 0), Pos(0, 1)])
GOOSE = Card("goose", Player.BLUE, [Pos(-1, 0), Pos(-1, 1), Pos(1, 0), Pos(1, -1)])
COBRA = Card("cobra", Player.RED, [Pos(-1, 0), Pos(1, 1), Pos(1, -1)])
CRAB = Card("crab", Player.BLUE, [Pos(0, 1), Pos(-2, 0), Pos(2, 0)])
HORSE = Card("horse", Player.RED, [Pos(0, 1), Pos(-1, 0), Pos(0, -1)])
DRAGON = Card("dragon", Player.RED, [Pos(-1, -1), Pos(1, -1), Pos(-2, 1), Pos(2, 1)])
ROOSTER = Card("rooster", Player.RED, [Pos(-1, 0), Pos(1, 0), Pos(1, 1), Pos(-1, -1)])
CRANE = Card("crane", Player.BLUE, [Pos(-1, -1), Pos(1, -1), Pos(0, 1)])
ELEPHANT = Card("elephant", Player.RED, [Pos(-1, 0), Pos(1, 0), Pos(-1, 1), Pos(1, 1)])
MANTIS = Card("mantis", Player.RED, [Pos(-1, 1), Pos(1, 1), Pos(0, -1)])
TIGER = Card("tiger", Player.BLUE, [Pos(0, 2), Pos(0, -1)])
FROG = Card("frog", Player.RED, [Pos(-1, 1), Pos(1, -1), Pos(-2, 0)])
OX = Card("ox", Player.BLUE, [Pos(0, 1), Pos(0, -1), Pos(1, 0)])
EEL = Card("eel", Player.BLUE, [Pos(1, 0), Pos(-1, 1), Pos(-1, -1)])

ALL_BASE_CARDS: List[Card] = [RABBIT, MONKEY, BOAR, GOOSE, COBRA, CRAB, HORSE, DRAGON, ROOSTER,
                              CRANE, ELEPHANT, MANTIS, TIGER, FROG, OX, EEL]
ALL_BASE_CARD_NAMES: List[str] = [card.name for card in ALL_BASE_CARDS]

ALL_BASE_CARD_INFO: List = [card_to_info(card) for card in ALL_BASE_CARDS]

# Expansion cards
# From https://www.gadgetsville.store/wp-content/uploads/2017/12/16096-c.jpg

FOX = Card("fox", Player.RED, [Pos(1, 1), Pos(1, 0), Pos(1, -1)])
DOG = Card("dog", Player.BLUE, [Pos(-1, 1), Pos(-1, 0), Pos(-1, -1)])
GIRAFFE = Card("giraffe", Player.BLUE, [Pos(-2, 1), Pos(0, -1), Pos(2, 1)])
PANDA = Card("panda", Player.RED, [Pos(-1, -1), Pos(0, 1), Pos(1, 1)])
BEAR = Card("bear", Player.BLUE, [Pos(-1, 1), Pos(0, 1), Pos(1, -1)])
KIRIN = Card("kirin", Player.RED, [Pos(-1, 2), Pos(0, -2), Pos(1, 2)])
SEA_SNAKE = Card("sea_snake", Player.BLUE, [Pos(-1, -1), Pos(0, 1), Pos(2, 0)])
VIPER = Card("viper", Player.RED, [Pos(-2, 0), Pos(0, 1), Pos(1, -1)])
PHOENIX = Card("phoenix", Player.BLUE, [Pos(-2, 0), Pos(-1, 1), Pos(1, 1), Pos(2, 0)])
MOUSE = Card("mouse", Player.BLUE, [Pos(-1, -1), Pos(0, 1), Pos(1, 0)])
RAT = Card("rat", Player.RED, [Pos(-1, 0), Pos(0, 1), Pos(1, -1)])
TURTLE = Card("turtle", Player.RED, [Pos(-2, 0), Pos(-1, -1), Pos(1, -1), Pos(2, 0)])
TANUKI = Card("tanuki", Player.BLUE, [Pos(-1, -1), Pos(0, 1), Pos(2, 1)])
IGUANA = Card("iguana", Player.RED, [Pos(-2, 1), Pos(0, 1), Pos(1, -1)])
SABLE = Card("sable", Player.BLUE, [Pos(-2, 0), Pos(-1, -1), Pos(1, 1)])
OTTER = Card("otter", Player.RED, [Pos(-1, 1), Pos(1, -1), Pos(2, 0)])

ALL_EXPANSION_CARDS: List[Card] = [FOX, DOG, GIRAFFE, PANDA, BEAR, KIRIN, SEA_SNAKE, VIPER,
                                   PHOENIX, MOUSE, RAT, TURTLE, TANUKI, IGUANA, SABLE, OTTER]
ALL_EXPANSION_CARD_NAMES: List[str] = [card.name for card in ALL_EXPANSION_CARDS]

ALL_EXPANSION_CARD_INFO: List = [card_to_info(card) for card in ALL_EXPANSION_CARDS]

# All cards combined

ALL_CARDS: List[Card] = ALL_BASE_CARDS + ALL_EXPANSION_CARDS
ALL_CARD_NAMES: List[str] = ALL_BASE_CARD_NAMES + ALL_EXPANSION_CARD_NAMES
ALL_CARD_INFO = {
    "base": ALL_BASE_CARD_INFO,
    "expansion": ALL_EXPANSION_CARD_INFO
}