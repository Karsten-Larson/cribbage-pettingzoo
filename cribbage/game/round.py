from rlcard.games.base import Card

from typing import Literal

class CribbageRound:
    def __init__(self, np_random):
        self.np_random = np_random
        self.current_player = 0
        self.pegging_total = 0
        self.is_over = False
        self.phase: Literal['discard', 'pegging'] = 'discard'
        self.pegging_history: list[Card] = []
        self.passed: set[int] = set()

    def proceed_round(self, players, action):
        """
        Process the action, which might be discarding to the crib, 
        or playing a card during the pegging phase.
        """
        # action is expected to be a card index string like 'SA'
        # Phase: Discard to crib -> each player discards down to 4 cards
        current = self.current_player
        player = players[current]

        if self.phase == 'discard':
            # remove the card from player's hand and add to their crib
            card_to_discard = None
            for c in player.hand:
                if c.get_index() == action:
                    card_to_discard = c
                    break
            if card_to_discard is not None:
                player.hand.remove(card_to_discard)
                player.crib.append(card_to_discard)

            # advance turn
            self.current_player = (self.current_player + 1) % len(players)

            # if all players have 4 cards now, move to pegging
            if all(len(p.hand) == 4 for p in players):
                self.phase = 'pegging'
                self.pegging_history = []
                self.pegging_total = 0
                self.passed = set()

            return

        # Pegging phase: players play cards (or implicitly 'go' if none playable)
        if self.phase == 'pegging':
            # find playable card
            card_to_play = None
            for c in player.hand:
                if c.get_index() == action:
                    # map ranks to values
                    value_map = {"A": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "T": 10, "J": 10, "Q": 10, "K": 10}
                    v = value_map.get(c.rank, 0)
                    if self.pegging_total + v <= 31:
                        card_to_play = c
                    break

            if card_to_play is None:
                # player cannot play -> mark passed
                self.passed.add(current)
                # if all players passed, end pegging for this round
                if len(self.passed) >= len(players):
                    self.is_over = True
                else:
                    # advance to next player
                    self.current_player = (self.current_player + 1) % len(players)
                return

            # play the card
            player.hand.remove(card_to_play)
            self.pegging_history.append(card_to_play)
            value_map = {"A": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "T": 10, "J": 10, "Q": 10, "K": 10}
            self.pegging_total += value_map.get(card_to_play.rank, 0)

            # reset passes because a card was played
            self.passed = set()

            # advance turn
            self.current_player = (self.current_player + 1) % len(players)

            # if all players have empty hands, end round
            if all(len(p.hand) == 0 for p in players):
                self.is_over = True
            return