# ===================== config.py =====================
import pygame

# 화면/프레임
SCREEN_W, SCREEN_H = 1200, 760
FPS = 60

# 색상
BG_COLOR = (16, 17, 21)
PANEL_COLOR = (27, 29, 35)
TEXT_COLOR = (235, 235, 240)
ACCENT = (255, 206, 84)
ERR_COLOR = (255, 92, 92)
OK_COLOR = (120, 220, 150)

# 카드 / 레이아웃
CARD_W, CARD_H = 100, 148
CARD_RADIUS = 14
GRID_PADDING = 18
MARGIN = 24

# 손패 축소 카드 크기 & 애니메이션
HAND_W, HAND_H = 56, 78
ANIM_FLIP_MOVE_MS = 500
AI_PICK_DELAY_MS = 450

# 폰트 후보(한글/기호 폴백)
PREFERRED_FONTS = [
    "malgungothic", "segoe ui", "arial unicode ms",
    "apple sd gothic neo", "pingfang", "hiragino sans",
    "noto sans cjk kr", "noto sans", "dejavu sans",
]
FONT_NAME = None  # pygame.font.match_font로 탐색

# 수업 모드 기본값(메뉴에서 토글 가능)
STANDARD_MODE = True

# 저장 슬롯
SAVE_PATH = "slot1.json"
