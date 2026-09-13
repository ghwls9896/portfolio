# ===================== card.py =====================
import pygame
from config import CARD_W, CARD_H, HAND_W, HAND_H, TEXT_COLOR
import config as CFG  # ★ 런타임 참조를 위해 모듈 자체를 가져온다

# 문자→기호 매핑
SUIT_ALIASES = {'H': '♥', 'D': '♦', 'C': '♣', 'S': '♠'}

class SuitPainter:
    @staticmethod
    def heart(surf, cx, cy, scale, color):
        r = scale
        pygame.draw.circle(surf, color, (cx - r//2, cy - r//4), r//2)
        pygame.draw.circle(surf, color, (cx + r//2, cy - r//4), r//2)
        pygame.draw.polygon(surf, color, [(cx - r, cy - r//6), (cx + r, cy - r//6), (cx, cy + r)])
    @staticmethod
    def diamond(surf, cx, cy, scale, color):
        r = scale
        pygame.draw.polygon(surf, color, [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)])
    @staticmethod
    def club(surf, cx, cy, scale, color):
        r = scale//2
        pygame.draw.circle(surf, color, (cx, cy - r), r)
        pygame.draw.circle(surf, color, (cx - r, cy + r//4), r)
        pygame.draw.circle(surf, color, (cx + r, cy + r//4), r)
        pygame.draw.rect(surf, color, (cx - r//4, cy + r, r//2, r))
    @staticmethod
    def spade(surf, cx, cy, scale, color):
        r = scale
        pygame.draw.polygon(surf, color, [(cx, cy - r), (cx + r, cy), (cx, cy + r//3), (cx - r, cy)])
        pygame.draw.rect(surf, color, (cx - r//6, cy + r//3, r//3, r//2))

SUIT_DRAWERS = {"♥": SuitPainter.heart, "♦": SuitPainter.diamond, "♣": SuitPainter.club, "♠": SuitPainter.spade}
SUIT_COLORS  = {"♥": (232, 77, 91),    "♦": (232, 77, 91),       "♣": (240, 240, 245),  "♠": (240, 240, 245)}

def number_label(n:int)->str:
    if n is None:
        return "J"  # 조커 라벨

    if CFG.STANDARD_MODE:
        # 규격 모드: 1..(4×N) 숫자 그대로
        return str(n)

    # 확장 모드: A(1), 2..9, J(10), Q(11), K(12)
    if n == 1:   return "A"
    if 2 <= n <= 9:  return str(n)
    if n == 10:  return "J"
    if n == 11:  return "Q"
    if n == 12:  return "K"
    # 방어적 처리: 범위를 벗어나면 숫자 그대로
    return str(n)

class Card:
    __slots__ = ("number","suit","is_joker","rect","highlight","face_up")
    def __init__(self, number:int|None, suit:str|None, is_joker:bool=False):
        self.number = number
        self.suit   = suit
        self.is_joker = is_joker
        self.rect = pygame.Rect(0,0,CARD_W,CARD_H)
        self.highlight = False
        self.face_up   = False

    def _draw_back(self, base:pygame.Surface, w:int, h:int):
        bg = (38,38,46); border = (80,82,94)
        pygame.draw.rect(base, border, pygame.Rect(0,0,w,h), border_radius=16)
        pygame.draw.rect(base, bg,    pygame.Rect(0,0,w,h).inflate(-8,-8), border_radius=14)
        for y in range(10, h-10, 14):
            for x in range(10, w-10, 14):
                pygame.draw.rect(base, (60,62,74), (x, y, 6, 6), border_radius=2)

    def _blit_text_with_outline(self, surf, text_surf, center):
        for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            s = text_surf.copy()
            s.fill((0,0,0,255), special_flags=pygame.BLEND_RGBA_MIN)
            surf.blit(s, (center[0]-s.get_width()//2+dx, center[1]-s.get_height()//2+dy))
        surf.blit(text_surf, (center[0]-text_surf.get_width()//2, center[1]-text_surf.get_height()//2))

    def _draw_front(self, base:pygame.Surface, w:int, h:int, font_big:pygame.font.Font, font_small:pygame.font.Font):
        border = (68,70,80); inner  = (38,38,46)
        pygame.draw.rect(base, border, pygame.Rect(0,0,w,h), border_radius=16)
        pygame.draw.rect(base, inner,  pygame.Rect(0,0,w,h).inflate(-8,-8), border_radius=14)

        if self.is_joker:
            gold  = (255, 210, 90); label = "JOKER"
            t_raw = font_big.render(label, True, gold)
            max_w = int(w * 0.62)
            if t_raw.get_width() > max_w:
                scale = max_w / t_raw.get_width()
                t = pygame.transform.smoothscale(t_raw, (int(t_raw.get_width()*scale), int(t_raw.get_height()*scale)))
            else:
                t = t_raw
            self._blit_text_with_outline(base, t, (w//2, 24))
            cx, cy = w // 2, int(h * 0.64); brim_w, brim_h = 44, 8
            pygame.draw.ellipse(base, gold, (cx - brim_w // 2, cy, brim_w, brim_h), 2)
            tip1 = (cx - 24, cy - 14); tip2 = (cx, cy - 22); tip3 = (cx + 24, cy - 14)
            pygame.draw.line(base, gold, (cx - 16, cy), tip1, 2)
            pygame.draw.line(base, gold, (cx,      cy), tip2, 2)
            pygame.draw.line(base, gold, (cx + 16, cy), tip3, 2)
            pygame.draw.circle(base, gold, tip1, 3); pygame.draw.circle(base, gold, tip2, 3); pygame.draw.circle(base, gold, tip3, 3)
            return

        num = number_label(self.number)
        t = font_big.render(num, True, TEXT_COLOR)
        sym = SUIT_ALIASES.get(self.suit, self.suit)
        color  = SUIT_COLORS.get(sym, (240,240,245))
        drawer = SUIT_DRAWERS.get(sym, SuitPainter.spade)

        if CFG.STANDARD_MODE:
            t = pygame.transform.smoothscale(t, (int(t.get_width()*0.88), int(t.get_height()*0.88)))
            self._blit_text_with_outline(base, t, (w//2, 22))
            drawer(base, w//2, int(h*0.70), 16, color)
        else:
            t = pygame.transform.smoothscale(t, (int(t.get_width()*0.82), int(t.get_height()*0.82)))
            self._blit_text_with_outline(base, t, (w//2, 18))
            drawer(base, w//2, int(h*0.76), 13, color)

    def draw(self, surf:pygame.Surface, font_big:pygame.font.Font, font_small:pygame.font.Font, *,
             flip_t:float|None=None, move_rect:pygame.Rect|None=None):
        rect = move_rect if move_rect else self.rect
        w, h = rect.w, rect.h
        temp = pygame.Surface((w, h), pygame.SRCALPHA)

        if flip_t is None:
            if self.face_up: self._draw_front(temp, w, h, font_big, font_small)
            else:            self._draw_back(temp,  w, h)
            surf.blit(temp, rect); return

        t = max(0.0, min(1.0, flip_t))
        shrinking = t < 0.5
        scale = 1.0 - (t*2 if shrinking else (1.0 - t)*2)
        scale = max(0.001, scale)

        if shrinking: self._draw_back(temp, w, h)
        else:         self._draw_front(temp, w, h, font_big, font_small)

        scaled = pygame.transform.smoothscale(temp, (max(1, int(w*scale)), h))
        dx = (w - scaled.get_width())//2
        surf.blit(scaled, (rect.x + dx, rect.y))
