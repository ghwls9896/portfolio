# ===================== player.py =====================
from collections import Counter
from card import Card

class Player:
    def __init__(self, name:str, is_human:bool=True):
        self.name = name
        self.is_human = is_human
        self.picks:list[Card] = []

    def reset(self):
        self.picks.clear()

    def add_card(self, c:Card):
        self.picks.append(c)

    # player.py의 score 함수 전체 교체
    def score(self, max_number:int):
        last_joker = -1
        for i, c in enumerate(self.picks):
            if c.is_joker:
                last_joker = i
        nums = [c.number for c in self.picks[last_joker+1:] if not c.is_joker]
        cnt = Counter(nums)
        total = 0
        pair = {n for n,k in cnt.items() if k>=2}
        for n in nums:
            total += (n*3 if n in pair else n)
        return total
