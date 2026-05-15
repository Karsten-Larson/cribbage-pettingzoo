from __future__ import annotations

from rlcard.games.base import Card
from typing import List, Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from .player import CribbagePlayer
    from .game import CribbageGame

class CribbageJudger:
    def __init__(self, np_random):
        self.np_random = np_random

    def judge_game(self, game: CribbageGame):
        """ Determine if a player has won (reached 121 points) """
        for i, player in enumerate(game.players):
            if player.score >= 121:
                game.winner = i
                return i
        return None
        
    def score_pegging(self, play_history: List[Card]) -> int:
        """ Calculate pegging score (e.g. 15s, 31s, pairs, runs) """
        points = 0
        if not play_history:
            return 0

        # value mapping for counting to 15/31
        value_map = {"A": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "T": 10, "J": 10, "Q": 10, "K": 10}

        # running total
        total = sum(value_map.get(card.rank, 0) for card in play_history) # type: ignore
        if total == 15:
            points += 2
        if total == 31:
            points += 2

        # check for pairs (consecutive equal ranks at end)
        last_rank = play_history[-1].rank
        pair_count = 1
        for c in reversed(play_history[:-1]):
            if c.rank == last_rank:
                pair_count += 1
            else:
                break
        if pair_count == 2:
            points += 2
        elif pair_count == 3:
            points += 6
        elif pair_count >= 4:
            points += 12

        # check for runs in the last N cards: look for the longest run ending at the last card
        # map ranks to numeric order for run detection
        rank_order = {r: i + 1 for i, r in enumerate(['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K'])}

        n = len(play_history)
        for k in range(n, 2, -1):
            window = play_history[-k:]
            ranks = [rank_order.get(c.rank) for c in window] # type: ignore
            if None in ranks:
                continue
            # runs ignore order in pegging: check if unique and consecutive when sorted
            ranks_sorted = sorted(ranks) # type: ignore
            # duplicates break runs
            if len(set(ranks_sorted)) != len(ranks_sorted):
                continue
            is_consecutive = all(ranks_sorted[i] + 1 == ranks_sorted[i + 1] for i in range(len(ranks_sorted) - 1))
            if is_consecutive:
                points += k
                break

        return points
    
    def score_hand(self, hand: List[Card], cut_card: Card, is_crib: bool = False) -> int:
        """ Calculate hand score (e.g. 15s, pairs, runs, flushes) """
        from itertools import combinations

        points = 0

        # combine hand (4 cards) with cut card -> 5 cards
        cards = list(hand) + [cut_card]

        # value for 15s: face cards count as 10, ace as 1
        value_map = {"A": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "T": 10, "J": 10, "Q": 10, "K": 10}

        # --- Fifteens ---
        for r in range(1, len(cards) + 1):
            for combo in combinations(cards, r):
                s = sum(value_map.get(c.rank, 0) for c in combo) # type: ignore
                if s == 15:
                    points += 2

        # --- Pairs / kind ---
        rank_counts = {}
        for c in cards:
            rank_counts[c.rank] = rank_counts.get(c.rank, 0) + 1
        for cnt in rank_counts.values():
            if cnt >= 2:
                # each pair counts 2 points; number of pairs = nC2
                pairs = cnt * (cnt - 1) // 2
                points += 2 * pairs

        # --- Runs ---
        # map ranks to numeric for ordering
        rank_order = {r: i + 1 for i, r in enumerate(['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K'])}
        counts_by_rank = {}
        numeric_ranks = []
        for r in rank_counts:
            idx = rank_order.get(r)
            if idx is not None:
                counts_by_rank[idx] = rank_counts[r]
                numeric_ranks.append(idx)

        if numeric_ranks:
            min_r, max_r = min(numeric_ranks), max(numeric_ranks)
            # find consecutive segments where counts_by_rank has entries
            segments = []
            seg_start = None
            for v in range(min_r, max_r + 2):
                if v in counts_by_rank:
                    if seg_start is None:
                        seg_start = v
                else:
                    if seg_start is not None:
                        segments.append((seg_start, v - 1))
                        seg_start = None
            max_run_len = 0
            for a, b in segments:
                max_run_len = max(max_run_len, b - a + 1)

            if max_run_len >= 3:
                # for each segment of length equal to max_run_len, compute multiplicity
                for a, b in segments:
                    seg_len = b - a + 1
                    if seg_len < max_run_len:
                        continue
                    # sliding windows of size max_run_len inside this segment (usually one)
                    for start in range(a, b - max_run_len + 2):
                        mul = 1
                        for rr in range(start, start + max_run_len):
                            mul *= counts_by_rank.get(rr, 0)
                        points += max_run_len * mul

        # --- Flush ---
        hand_suits = [c.suit for c in hand]
        if all(s == hand_suits[0] for s in hand_suits):
            # four-card flush in hand
            if cut_card.suit == hand_suits[0]:
                points += 5
            else:
                if not is_crib:
                    points += 4

        # --- Nobs (jack of same suit as cut) ---
        for c in hand:
            if c.rank == 'J' and c.suit == cut_card.suit:
                points += 1
                break

        return points
    
    def get_legal_actions(self, player: CribbagePlayer, phase: Literal['pegging', 'discard'], pegging_total: int = 0) -> List[str]:
        """ Return a list of legal actions for the current player.

        - If `phase` is not 'pegging' (e.g., 'discard'), return all cards in hand (for discarding).
        - If `phase` is 'pegging', return only cards that don't push `pegging_total` over 31.
        If no cards are playable during pegging, return an empty list (the round logic treats this as a 'Go').
        """
        # Counting values for 15/31. NOTE: this mapping is only for sum checks;
        # the card.rank values are preserved for pair/run detection elsewhere.
        value_map = {"A": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "T": 10, "J": 10, "Q": 10, "K": 10}

        # If not pegging phase, any card in hand is a legal discard/play
        if phase != 'pegging':
            return [card.get_index() for card in player.hand]

        legal: List[str] = []
        for card in player.hand:
            v = value_map.get(card.rank, 0)  # type: ignore
            if pegging_total + v <= 31:
                legal.append(card.get_index())

        return legal

        