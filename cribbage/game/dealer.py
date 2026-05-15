from __future__ import annotations

import numpy as np
from rlcard.utils import init_standard_deck
from rlcard.games.base import Card

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .player import CribbagePlayer

class CribbageDealer:
    def __init__(self, np_random):
        self.np_random = np_random
        self.deck = init_standard_deck()
        self.shuffle()
        self.cut_card: Card | None = None

    def shuffle(self) -> None:
        shuffle_deck = np.array(self.deck)
        self.np_random.shuffle(shuffle_deck)
        self.deck = list(shuffle_deck)

    def deal_card(self, player: CribbagePlayer) -> None:
        card = self.deck.pop()
        player.hand.append(card)
        
    def cut(self) -> Card:
        """ Draw the cut card for the round """
        cut_card = self.deck.pop()

        if not isinstance(cut_card, Card):
            raise ValueError("Cut card must be an instance of Card")

        self.cut_card = cut_card
        return cut_card