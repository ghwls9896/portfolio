# ===================== game.py =====================
import pygame, sys, json, os
from config import *
from deck import Deck
from player import Player
from ui import UI, Button
from dialogue import Dialogue
from save_load import save_options, load_options

def lerp(a, b, t): return a + (b - a) * t
def ease_out_cubic(t): 
    t = max(0.0, min(1.0, t)); 
    return 1 - (1 - t) ** 3

class MoveFlipAnim:
    def __init__(self, card, start_rect, end_rect, duration_ms):
        self.card = card
        self.start = start_rect.copy(); self.end = end_rect.copy()
        self.ms = duration_ms; self.elapsed = 0; self.done=False
    def update(self, dt):
        self.elapsed += dt
        if self.elapsed >= self.ms: self.elapsed=self.ms; self.done=True
        t = self.elapsed/self.ms; mt = ease_out_cubic(t)
        rx = lerp(self.start.x, self.end.x, mt); ry = lerp(self.start.y, self.end.y, mt)
        rw = lerp(self.start.w, self.end.w, mt); rh = lerp(self.start.h, self.end.h, mt)
        if t>=0.5: self.card.face_up = True
        return pygame.Rect(int(rx),int(ry),int(rw),int(rh)), t

class FanAnim:
    def __init__(self, start_rect, end_rects, duration_ms):
        self.start = start_rect.copy()
        self.ends  = [r.copy() for r in end_rects]
        self.ms = duration_ms; self.elapsed=0; self.done=False
    def update(self, dt):
        self.elapsed += dt
        if self.elapsed >= self.ms: self.elapsed=self.ms; self.done=True
        t = ease_out_cubic(self.elapsed/self.ms)
        rects = []
        for er in self.ends:
            rx = lerp(self.start.x, er.x, t); ry = lerp(self.start.y, er.y, t)
            rw = lerp(self.start.w, er.w, t); rh = lerp(self.start.h, er.h, t)
            rects.append(pygame.Rect(int(rx),int(ry),int(rw),int(rh)))
        return rects

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.ui = UI(screen)
        self.state = "menu"  # menu | play | result
        self.view  = "stack" # stack | shuffling | fan
        self.opts = {
            "num_players": 3,
            "use_ai": True,
            "standard_mode": True,  # 수업 모드
            "use_jokers": True,
            "mode": "classic",      # "classic" | "dialogue"
        }
        self.buttons: list[Button] = []
        self._build_menu_buttons()
        self.clock = pygame.time.Clock()
        self.deck:Deck|None = None
        self.players:list[Player] = []
        self.turn_idx = 0
        self.max_number = 12
        self.anim:MoveFlipAnim|None = None; self.anim_card=None
        self.fan_anim:FanAnim|None = None;  self.fan_rects=None
        self.hover_idx=None
        self.ai_wakeup_ms=None
        self.dlg = Dialogue()
        # 펼친 카드 스크롤 한계
        self.max_scroll = 0

    def _build_menu_buttons(self):
        bx = SCREEN_W-320
        self.buttons = [
            Button((bx,110,140,44), "플레이어-", ("num_players",-1)),
            Button((bx+150,110,140,44), "플레이어+", ("num_players",+1)),
            Button((bx,164,140,44), "AI 토글", ("use_ai",None)),
            Button((bx+150,164,140,44), "규격 모드", ("standard_mode",None)),
            Button((bx,218,140,44), "조커 포함", ("use_jokers",None)),
            Button((bx+150,218,140,44), "게임 모드", ("mode_toggle",None)),
            Button((bx,272,290,48), "게임 시작", ("start",None)),
            Button((bx,330,140,44), "저장", ("save",None)),
            Button((bx+150,330,140,44), "불러오기", ("load",None)),
            Button((bx,388,290,48), "종료", ("quit",None)),
        ]

    def init_match(self):
        # config.STANDARD_MODE 동기화
        import config as CFG
        CFG.STANDARD_MODE = self.opts["standard_mode"]

        n = max(2, min(5, self.opts["num_players"]))
        self.max_number = (4*n) if self.opts["standard_mode"] else min(4*n, 13)

        # 플레이어 구성
        self.players = []
        if self.opts["use_ai"]:
            self.players.append(Player("You", True))
            for i in range(2, n+1):
                self.players.append(Player(f"CPU{i}", False))
        else:
            for i in range(1, n+1):
                self.players.append(Player(f"Player{i}", True))

        # 덱
        self.deck = Deck(n, include_jokers=self.opts["use_jokers"], standard_mode=self.opts["standard_mode"])
        for c in self.deck.cards: c.face_up=False

        self.turn_idx=0; self.state="play"; self.view="stack"
        for p in self.players: p.reset()
        self.anim=None; self.fan_anim=None; self.fan_rects=None; self.hover_idx=None
        self.ai_wakeup_ms=None
        self.ui.grid_scroll = 0
        self.max_scroll = 0

        if self.opts["mode"] == "dialogue":
            self.dlg.lines.clear()
            self.dlg.typing = ""
            self.dlg.scroll = 0
            self.dlg.say("게임을 시작합니다.")
            self.dlg.say(f"{len(self.players)}명이 참여합니다. 각자 4장을 뽑으세요.")
            self.dlg.say("덱을 펼칠까요?")
            self.dlg.ask("셔플/펼치기 진행(Y/N)", ["Y","N"])

    def _target_hand_slot_rect(self, player_index:int):
        # UI가 계산한 타일부터 시작
        tile = None
        if hasattr(self.ui, "player_tiles") and self.ui.player_tiles and player_index < len(self.ui.player_tiles):
            tile = self.ui.player_tiles[player_index]
        if tile is None:
            x = MARGIN + 12 + player_index*292
            y = SCREEN_H - 230 + 56
        else:
            x = tile.x + 14
            y = tile.y + 54
        p = self.players[player_index]
        idx = min(len(p.picks), 3)
        x += idx * (HAND_W + 8)
        return pygame.Rect(x, y, HAND_W, HAND_H)

    def _start_pick_anim(self, card, start_rect, player_index:int):
        end_rc = self._target_hand_slot_rect(player_index)
        self.anim = MoveFlipAnim(card, start_rect, end_rc, ANIM_FLIP_MOVE_MS)
        self.anim_card = card

    def _finish_anim_into_hand(self, player_index:int):
        self.players[player_index].add_card(self.anim_card)
        self.anim=None; self.anim_card=None

    def _schedule_ai(self):
        if not self.players[self.turn_idx].is_human and self.ai_wakeup_ms is None:
            self.ai_wakeup_ms = pygame.time.get_ticks() + AI_PICK_DELAY_MS

    def _maybe_ai_act(self):
        if self.anim or self.state!="play" or self.view!="fan": return
        if self.players[self.turn_idx].is_human: return
        if self.ai_wakeup_ms is None or pygame.time.get_ticks() < self.ai_wakeup_ms: return
        if not self.deck.cards: return
        idx = 0
        start_rc = self.fan_rects[idx].move(0, self.ui.grid_scroll).copy()
        card = self.deck.take_at(idx)
        if card:
            self._start_pick_anim(card, start_rc, self.turn_idx)
            # ★ 레이아웃/스크롤 갱신 추가
            self.fan_rects = self.ui.fan_layout(self.deck.count())
            self._recalc_scroll_limit()
        self.ai_wakeup_ms=None

    def _advance_turn_or_result(self):
        self.turn_idx = (self.turn_idx + 1) % len(self.players)
        if all(len(p.picks) >= 4 for p in self.players):
            self.state="result"
        else:
            self._schedule_ai()

    def _save_game(self):
    # 설정만 저장
        save_options(self)

    def _load_game(self):
    # 설정만 불러와서 옵션에 반영 (현재 라운드는 그대로)
        load_options(self)
    # 펼친 카드 전체 높이에 따른 스크롤 한계 계산
    def _recalc_scroll_limit(self):
        if not self.fan_rects:
            self.max_scroll = 0; 
            self.ui.grid_scroll = 0
            return
        content_bottom = max(r.bottom for r in self.fan_rects)
        view_top = 120
        view_h = SCREEN_H - 120 - 230
        overflow = content_bottom - (view_top + view_h)
        self.max_scroll = max(0, overflow)
        self.ui.grid_scroll = max(-self.max_scroll, min(0, self.ui.grid_scroll))

    def run(self):
        running=True
        while running:
            dt = self.clock.tick(FPS)
            self.screen.fill(BG_COLOR)
            mouse = pygame.mouse.get_pos()

            for e in pygame.event.get():
                if e.type==pygame.QUIT: 
                    running=False

                # ── 마우스 이동: 팬 뷰 호버(스크롤 반영)
                if e.type == pygame.MOUSEMOTION:
                    if self.state=="menu":
                        for b in self.buttons: 
                            b.hover = b.hit(mouse)
                    elif self.state=="play" and self.view=="fan" and self.fan_rects and not self.anim:
                        self.hover_idx=None
                        for i,rc in enumerate(self.fan_rects):
                            if rc.move(0, self.ui.grid_scroll).collidepoint(e.pos): 
                                self.hover_idx=i; break

                # ── 마우스 휠: 카드 그리드 스크롤 / 대화 로그 스크롤
                if e.type == pygame.MOUSEWHEEL:
                    if self.state=="play" and self.view=="fan" and self.max_scroll>0:
                        self.ui.grid_scroll += e.y * 40  # 위로 굴리면 y>0
                        self.ui.grid_scroll = max(-self.max_scroll, min(0, self.ui.grid_scroll))
                    if self.state=="play" and self.opts["mode"]=="dialogue":
                        if hasattr(self.ui, "dialog_rect") and self.ui.dialog_rect.collidepoint(mouse):
                            max_scroll = max(0, len(self.dlg.lines) - getattr(self.ui, "dialog_max_rows", 0))
                            # 위로(+1) 스크롤 = 과거 보기 : dlg.scroll 증가
                            self.dlg.scroll = max(0, min(max_scroll, self.dlg.scroll - e.y))

                # ── 키 입력: 대화 모드(두 자리 숫자 + Y/N 고정 처리)
                if e.type==pygame.KEYDOWN and self.state=="play" and self.opts["mode"]=="dialogue":
                    key_up = (e.unicode or "").upper()
                    # IME/유니코드 없는 환경 보정
                    if e.key == pygame.K_y: key_up = "Y"
                    if e.key == pygame.K_n: key_up = "N"

                    if self.dlg.awaiting:
                        ans = self.dlg.answer(key_up)
                        if ans == "Y":
                            self.dlg.say("카드를 펼칩니다. 숫자를 입력하거나 클릭하세요.")
                            end_rects = self.ui.fan_layout(self.deck.count())
                            self.fan_rects = end_rects
                            self.fan_anim = FanAnim(self.ui.deck_rect, end_rects, 500)
                            self.view = "shuffling"
                            self.dlg.typing = ""
                        elif ans == "N":
                            self.dlg.say("언제든지 Space 키로 펼칠 수 있어요.")
                    else:
                        if self.view == "fan":
                            # Enter = 현재 버퍼 확정
                            if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                                if self.dlg.typing.isdigit():
                                    idx = int(self.dlg.typing) - 1
                                    self.dlg.typing = ""
                                    if 0 <= idx < len(self.deck.cards) and not self.anim and self.players[self.turn_idx].is_human:
                                        start_rc = self.fan_rects[idx].move(0, self.ui.grid_scroll).copy()
                                        card = self.deck.take_at(idx)
                                        if card:
                                            self._start_pick_anim(card, start_rc, self.turn_idx)
                                            self.fan_rects = self.ui.fan_layout(self.deck.count())
                                            self._recalc_scroll_limit()
                            elif e.key == pygame.K_BACKSPACE:
                                self.dlg.typing = self.dlg.typing[:-1]
                            elif e.unicode.isdigit():
                                # 0도 허용(10~13 입력 위해), 최대 2자리면 충분
                                if len(self.dlg.typing) < 2:
                                    self.dlg.typing += e.unicode
                        # Space = 스택 상태에서 펼치기
                        if e.key == pygame.K_SPACE and self.view=="stack":
                            end_rects = self.ui.fan_layout(self.deck.count())
                            self.fan_rects = end_rects
                            self.fan_anim = FanAnim(self.ui.deck_rect, end_rects, 500)
                            self.view = "shuffling"
                            self._recalc_scroll_limit()

                # ── 마우스 클릭
                if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                    if self.state=="menu":
                        for b in self.buttons:
                            if b.hit(e.pos):
                                key, val = b.key
                                if key=="num_players":
                                    self.opts[key] = max(2, min(5, self.opts[key]+val))
                                elif key=="use_ai":
                                    self.opts[key] = not self.opts[key]
                                elif key=="standard_mode":
                                    self.opts[key] = not self.opts[key]
                                elif key=="use_jokers":
                                    self.opts[key] = not self.opts[key]
                                elif key=="mode_toggle":
                                    self.opts["mode"] = ("dialogue" if self.opts["mode"]=="classic" else "classic")
                                elif key=="start":
                                    self.init_match()
                                elif key=="save":
                                    self._save_game()
                                elif key=="load":
                                    self._load_game()
                                elif key=="quit":
                                    running=False

                    elif self.state=="play":
                        if self.view=="stack" and not self.anim and self.ui.deck_rect.collidepoint(e.pos):
                            end_rects = self.ui.fan_layout(self.deck.count())
                            self.fan_rects = end_rects
                            self.fan_anim = FanAnim(self.ui.deck_rect, end_rects, 500)
                            self.view = "shuffling"
                            self._recalc_scroll_limit()
                        elif self.view=="fan" and not self.anim and self.fan_rects:
                            if self.players[self.turn_idx].is_human:
                                for i,rc in enumerate(self.fan_rects):
                                    if rc.move(0, self.ui.grid_scroll).collidepoint(e.pos):
                                        start_rc = rc.move(0, self.ui.grid_scroll).copy()
                                        card = self.deck.take_at(i)
                                        if card:
                                            self._start_pick_anim(card, start_rc, self.turn_idx)
                                            self.fan_rects = self.ui.fan_layout(self.deck.count())
                                            self._recalc_scroll_limit()
                                        break

                    elif self.state=="result":
                        self.state = "menu"

            # ---- DRAW ----
            if self.state=="menu":
                self.ui.draw_menu(self.opts, self.buttons)

            elif self.state=="play":
                if self.view=="stack":
                    title = f"숫자 카드 게임 — 덱 {self.deck.count()}장"
                    self.ui.draw_game_stack(title, self.deck.count(), self.players, self.turn_idx, self.max_number)

                elif self.view=="shuffling":
                    title = f"숫자 카드 게임 — 셔플 중..."
                    end_rects = self.ui.fan_layout(self.deck.count()) if not self.fan_rects else self.fan_rects
                    if self.fan_rects is None: self.fan_rects = end_rects
                    cur_rects = self.fan_anim.update(dt) if self.fan_anim else end_rects
                    self.ui.draw_header(title, "곧 카드가 펼쳐집니다")
                    for i,(c,rc) in enumerate(zip(self.deck.cards, cur_rects)):
                        face_backup=c.face_up; c.face_up=False
                        # 셔플 연출은 스크롤 적용 없이 중앙 영역에만
                        c.draw(self.screen, self.ui.font_big, self.ui.font_small, move_rect=rc)
                        c.face_up=face_backup
                    self.ui.draw_side_panel(self.players, self.turn_idx, self.max_number)
                    if self.fan_anim and self.fan_anim.done:
                        self.view="fan"; self._schedule_ai(); self._recalc_scroll_limit()

                elif self.view=="fan":
                    title = f"숫자 카드 게임 — 남은 카드 {self.deck.count()}장"
                    self.ui.draw_game_fanned(title, self.deck.cards, self.fan_rects, self.players, self.turn_idx, self.max_number, self.hover_idx)

                # 픽 애니
                if self.anim:
                    anim_rect, flip_t = self.anim.update(dt)
                    self.anim.card.draw(self.screen, self.ui.font_big, self.ui.font_small, flip_t=flip_t, move_rect=anim_rect)
                    if self.anim.done:
                        cur = self.turn_idx
                        self._finish_anim_into_hand(cur)
                        self._advance_turn_or_result()

                # AI
                if not self.anim and self.view=="fan":
                    self._maybe_ai_act()

                # 대화창
                if self.opts["mode"]=="dialogue":
                    self.ui.draw_dialogue(self.dlg)

            elif self.state=="result":
                self.ui.draw_result_screen(self.players, self.max_number)
                # 결과 화면에서는 대화창을 숨깁니다.

            pygame.display.flip()
