from rlcard.games.base import Card

class CribbagePlayer:
    def __init__(self, player_id, np_random):
        self.np_random = np_random
        self.player_id = player_id
        self.hand: list[Card] = []
        self.crib: list[Card] = []  # Specific to cribbage
        self.score = 0
        self.status = 'alive'

    def get_player_id(self):
        return self.player_id