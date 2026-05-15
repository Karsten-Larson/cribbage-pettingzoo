import numpy as np
from .dealer import CribbageDealer
from .player import CribbagePlayer
from .judger import CribbageJudger
from .round import CribbageRound

from typing import TypedDict

class CribbageState(TypedDict):
    player_id: int
    hand: list[int]  # List of card indices in the player's hand
    pegging_total: int
    pegging_cards: list[str]
    scores: list[int]  # Scores of all players

class CribbageGame:
    def __init__(self, allow_step_back=False):
        self.allow_step_back = allow_step_back
        self.np_random = np.random.RandomState()
        self.num_players = 2
        self.winner: int | None = None

    def init_game(self) -> tuple[CribbageState, int]:
        self.players = [CribbagePlayer(i, self.np_random) for i in range(self.num_players)]
        self.dealer = CribbageDealer(self.np_random)
        self.judger = CribbageJudger(self.np_random)
        self.round = CribbageRound(self.np_random)
        
        # Deal 6 cards to each player
        for player in self.players:
            for _ in range(6):
                self.dealer.deal_card(player)

        state = self.get_state(self.round.current_player)
        return state, self.round.current_player

    def step(self, action) -> tuple[CribbageState, int]:
        """ Advance the game state by one action """
        self.round.proceed_round(self.players, action)
        self.judger.judge_game(self)
        
        next_player_id = self.round.current_player
        is_over = self.is_over()
        state = self.get_state(next_player_id)
        return state, next_player_id

    def get_state(self, player_id: int) -> CribbageState:
        """ Return the raw state dictionary for the current player """
        return {
            'player_id': player_id,
            'hand': [c.get_index() for c in self.players[player_id].hand],
            'pegging_total': self.round.pegging_total,
            'pegging_cards': [c.get_index() for c in self.round.pegging_history],
            'scores': [p.score for p in self.players]
        }

    def get_num_players(self) -> int:
        return self.num_players

    def get_num_actions(self) -> int:
        return 52 # Number of cards in the deck

    def get_player_id(self) -> int:
        return self.round.current_player

    def is_over(self) -> bool:
        return self.winner is not None or self.round.is_over