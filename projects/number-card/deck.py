# deck.py
import random
from card import Card

SUITS = ["H", "D", "C", "S"]  # 하트/다이아/클로버/스페이드

class Deck:
    def __init__(self, num_players:int, include_jokers:bool, standard_mode:bool):
        self.num_players = num_players
        self.include_jokers = include_jokers
        self.standard_mode = standard_mode
        self.cards: list[Card] = []
        self._build_deck()

    def _build_deck(self):
        cards = []

        if self.standard_mode:
            # 규격 모드: 1..(4×N) 각 숫자 2장
            max_n = 4 * self.num_players
            for n in range(1, max_n + 1):
                for k in range(2):  # 정확히 두 장
                    suit = SUITS[(n + k) % 4]   # 보기용으로 수트만 다르게
                    cards.append(Card(n, suit, False))
        else:
            # 확장 모드: 1..12(= A..K) 각 2장
            for n in range(1, 13):  # ← 13 미만 => 1..12
                for k in range(2):
                    suit = SUITS[(n + k) % 4]
                    cards.append(Card(n, suit, False))

        if self.include_jokers:
            cards.append(Card(None, None, True))
            cards.append(Card(None, None, True))

        # Fisher–Yates
        for i in range(len(cards)-1, 0, -1):
            j = random.randint(0, i)
            cards[i], cards[j] = cards[j], cards[i]

        self.cards = cards

    def count(self): return len(self.cards)
    def take_at(self, idx:int):
        if 0 <= idx < len(self.cards):
            return self.cards.pop(idx)
        return None
