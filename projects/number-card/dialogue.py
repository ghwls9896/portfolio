# ===================== dialogue.py =====================
from collections import deque

class Dialogue:
    def __init__(self, max_lines=50):
        self.lines = deque(maxlen=max_lines)
        self.prompt = None
        self.awaiting = False
        self.scroll = 0
        self.typing = ""    # ← 현재 키보드 입력(예: "12")

    def say(self, text:str):
        self.lines.append(text)

    def ask(self, text:str, choices:list[str]):
        self.prompt = {"text": text, "choices": choices}
        self.awaiting = True

    def answer(self, key:str):
        if not self.awaiting: return None
        up = key.upper()
        for c in self.prompt["choices"]:
            if up == c.upper():
                self.lines.append(f"> {up}")
                self.awaiting = False
                p = self.prompt
                self.prompt = None
                return up
        return None
