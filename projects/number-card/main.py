# ===================== main.py =====================
import pygame, sys
from config import SCREEN_W, SCREEN_H, BG_COLOR
from game import Game

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("숫자 카드 게임")
    Game(screen).run()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
