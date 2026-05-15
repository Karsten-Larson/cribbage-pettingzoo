import numpy as np
from collections import OrderedDict

from rlcard.envs.env import Env
from cribbage.game.game import CribbageGame

class CribbageEnv(Env):
    """ 
    Cribbage Environment
    """

    def __init__(self, config):
        self.name = 'cribbage'
        self.default_game_config = {
            'allow_step_back': False,
            'seed': None,
        }
        self.game = CribbageGame()
        super().__init__(config)
        
        # Action shape: 52 possible cards to play or discard
        self.action_shape = [52] 
        
        # State shape: 
        # Example representation: 52 bits for hand, 52 bits for crib, 
        # 1 integer for pegging total, 2 integers for scores
        # Total = 52 + 52 + 1 + 2 = 107
        self.state_shape = [[107], [107]] 
        
        # A dictionary mapping card strings (e.g., 'SA', 'H7') to action IDs (0-51)
        self.action_dict = self._get_action_dict()

    def _extract_state(self, state):
        """ Extract the state representation from the raw state dictionary.
        
        Args:
            state (dict): The raw state dictionary from the game.
            
        Returns:
            dict: A dictionary containing the extracted state (numpy array) 
                  and the legal actions for the current player.
        """
        # Create a zeroed-out observation array
        obs = np.zeros(107, dtype=float)
        
        # 1. Encode Hand (Indices 0-51)
        for card_str in state['hand']:
            idx = self.action_dict[card_str]
            obs[idx] = 1.0
            
        # 2. Encode Crib/Pegging history (Indices 52-103)
        # Note: You would add 'pegging_cards' to your game.get_state() dictionary
        if 'pegging_cards' in state:
            for card_str in state['pegging_cards']:
                idx = self.action_dict[card_str]
                obs[52 + idx] = 1.0
                
        # 3. Encode Pegging Total (Index 104)
        obs[104] = state['pegging_total']
        
        # 4. Encode Scores (Indices 105, 106)
        obs[105] = state['scores'][0]
        obs[106] = state['scores'][1]

        extracted_state = {}
        extracted_state['obs'] = obs
        extracted_state['legal_actions'] = self._get_legal_actions()
        extracted_state['raw_obs'] = state
        extracted_state['raw_legal_actions'] = [a for a in self._get_legal_actions().keys()]
        
        return extracted_state

    def _get_legal_actions(self):
        """ Get all legal actions for current state.
        
        Returns:
            OrderedDict: A dictionary mapping action IDs to their string representations.
        """
        current_player = self.game.players[self.game.get_player_id()]
        legal_actions = self.game.judger.get_legal_actions(current_player, self.game.round.phase, self.game.round.pegging_total)
        legal_action_dict = OrderedDict()
        for action in legal_actions:
            if action in self.action_dict:
                action_id = self.action_dict[action]
                legal_action_dict[action_id] = action
        return legal_action_dict

    def _decode_action(self, action_id):
        """ Decode the action ID to the actual action string.
        
        Args:
            action_id (int): The action id given by the agent.
            
        Returns:
            str: The string representation of the action (e.g., 'SA' for Spades Ace)
        """
        legal_actions = self._get_legal_actions()
        if action_id in legal_actions:
            return legal_actions[action_id]
        # Fallback if the agent picks an illegal action
        if legal_actions:
            return next(iter(legal_actions.values()))
        return None

    def get_payoffs(self):
        """ Calculate the payoffs of the players at the end of the game.
        
        Returns:
            numpy array: The payoffs of the players (-1 for loss, 1 for win)
        """
        payoffs = np.zeros(self.num_players)
        for i in range(self.num_players):
            # Win condition: Score is 121 or greater
            if self.game.players[i].score >= 121:
                payoffs[i] = 1.0
            else:
                payoffs[i] = -1.0
                
            # Optional: Implement "Skunk" logic (if loser is < 90 points, payoff could be -2)
            # if payoffs[i] == -1.0 and self.game.players[i].score < 90:
            #     payoffs[i] = -2.0
                
        return payoffs
        
    def _get_action_dict(self):
        """ Generate a dictionary mapping card strings to action IDs.
        """
        action_dict = {}
        suits = ['S', 'H', 'D', 'C']
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K']
        
        idx = 0
        for suit in suits:
            for rank in ranks:
                # RLCard usually formats cards as "SuitRank", e.g., "SA" or "H7"
                action_dict[suit + rank] = idx 
                idx += 1
        return action_dict