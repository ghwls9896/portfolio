# ===================== ui.py =====================
import pygame
from config import *
from card import number_label

class Button:
    def __init__(self, rect, label, key=None):
        self.rect = pygame.Rect(rect); self.label = label
        self.key = key; self.hover = False
    def draw(self, surf, font):
        bg = (54,57,68) if not self.hover else (64,68,82)
        pygame.draw.rect(surf, bg, self.rect, border_radius=12)
        pygame.draw.rect(surf, (96,100,118), self.rect, 2, border_radius=12)
        txt = font.render(self.label, True, TEXT_COLOR)
        surf.blit(txt, txt.get_rect(center=self.rect.center))
    def hit(self, pos): return self.rect.collidepoint(pos)

class UI:
    def __init__(self, screen):
        self.screen = screen
        self.font, self.font_big, self.font_small = self._load_fonts()
        self.deck_rect = pygame.Rect((SCREEN_W//2-60, 140, CARD_W, CARD_H))
        self.player_tiles = []
        self.grid_scroll = 0
        self.header_bottom = 140   # 헤더 실제 하단 y (draw_header에서 갱신)
        self.panel_h = 230         # 하단 패널 높이 (draw_side_panel에서 갱신)

    # ---------- 폰트 ----------
    def _load_fonts(self):
        name = pygame.font.match_font(PREFERRED_FONTS) or FONT_NAME
        f  = pygame.font.Font(name, 24)
        fb = pygame.font.Font(name, 56)
        fs = pygame.font.Font(name, 18)
        return f, fb, fs

    # ---------- 헤더 ----------
    def draw_header(self, title:str, subtitle:str|None=None):
        t = self.font_big.render(title, True, TEXT_COLOR)
        title_y = 20
        subtitle_y = title_y + t.get_height() + 10
        header_h = max(140, subtitle_y + (self.font.get_height() if subtitle else 0) + 20)

        pygame.draw.rect(self.screen, PANEL_COLOR, (0,0,SCREEN_W,header_h))
        pygame.draw.line(self.screen, (60,64,78), (0, header_h-1), (SCREEN_W, header_h-1), 1)
        self.screen.blit(t, (MARGIN, title_y))
        if subtitle:
            s = self.font.render(subtitle, True, (185,192,205))
            self.screen.blit(s, (MARGIN, subtitle_y))

        # ★ 헤더 하단값 저장 → 그리드 시작/클리핑에 사용
        self.header_bottom = header_h
    # ---------- 덱/펼침 ----------
    def draw_deck_stack(self, count:int):
        x, y = self.deck_rect.x, self.deck_rect.y
        for i in range(3):
            r = pygame.Rect(x+i*6, y+i*4, CARD_W, CARD_H)
            pygame.draw.rect(self.screen, (70,72,82), r, border_radius=16)
            inner = r.inflate(-8,-8)
            pygame.draw.rect(self.screen, (38,38,46), inner, border_radius=14)
        ct = self.font_small.render(f"x{count}", True, (200,210,225))
        self.screen.blit(ct, (x+CARD_W+16, y+8))
        return self.deck_rect

    def fan_layout(self, n:int):
        cols = 9
        rows = max(1, (n + cols - 1)//cols)
        grid_w = cols*CARD_W + (cols-1)*GRID_PADDING
        start_x = (SCREEN_W - grid_w)//2
        start_y = 160
        rects = []
        for i in range(n):
            r = i//cols; c = i%cols
            x = start_x + c*(CARD_W+GRID_PADDING)
            y = start_y + r*(CARD_H+GRID_PADDING)
            rects.append(pygame.Rect(x,y,CARD_W,CARD_H))
        return rects

    def draw_fanned(self, cards, rects, hover_idx=None):
        """펼친 카드 + 번호 배지(스크롤/호버 적용, 헤더/하단 패널로 안전 클리핑)."""
        # ★ 헤더 아래 ~ 패널 위까지만 보이도록 클리핑
        view_rect = pygame.Rect(0, self.header_bottom, SCREEN_W,
                                SCREEN_H - self.header_bottom - self.panel_h)
        prev_clip = self.screen.get_clip()
        self.screen.set_clip(view_rect)

        count = min(len(cards), len(rects))

        # 카드 렌더(뒷면, 스크롤/호버 반영)
        for i in range(count):
            c = cards[i]
            base = rects[i]
            rc = base.move(0, self.grid_scroll)
            draw_rc = rc.move(0, -4 if hover_idx == i else 0)

            c.rect = draw_rc
            c.highlight = (hover_idx == i)

            face_backup = c.face_up
            c.face_up = False
            c.draw(self.screen, self.font_big, self.font_small, move_rect=draw_rc)
            c.face_up = face_backup

        # 번호 배지(카드 수만큼만, 동일 클리핑 영역 유지)
        for i in range(count):
            rc = rects[i].move(0, self.grid_scroll)
            badge = self.font_small.render(str(i + 1), True, (30, 32, 38))
            pad = 6
            bg = pygame.Rect(rc.x + 6, rc.y + 6,
                            badge.get_width() + pad * 2,
                            badge.get_height() + pad * 2)
            pygame.draw.rect(self.screen, (255, 206, 84), bg, border_radius=8)
            self.screen.blit(badge, (bg.x + pad, bg.y + pad))

        self.screen.set_clip(prev_clip)
    # ---------- 하단 플레이어 패널 ----------
    def draw_side_panel(self, players, current_idx, max_num):
        n = len(players)
        GAP = 12

        # 행/열
        if n <= 4:
            rows, cols = 1, n
        elif n == 5:
            rows, cols = 2, 3      # 3 + 2
        else:
            cols = min(4, n)
            rows = 2

        # ★ 하단 패널 높이를 행 수에 맞춰 동적으로
        self.panel_h = 230 if rows == 1 else 280   # 필요시 더 키워도 OK
        panel = pygame.Rect(0, SCREEN_H - self.panel_h, SCREEN_W, self.panel_h)

        pygame.draw.rect(self.screen, PANEL_COLOR, panel)

        usable_w = SCREEN_W - 2*MARGIN
        tile_w = min(260, int((usable_w - (cols-1)*GAP) / cols))

        # 행 수에 맞춰 타일 높이를 패널 안에 딱 맞게
        available_h = panel.height - 20
        tile_h = (available_h - (rows-1)*GAP) // rows
        tile_h = max(140, min(198, tile_h))

        # 각 행의 Y
        row_y = []
        y_cursor = panel.y + 10
        for _ in range(rows):
            row_y.append(y_cursor)
            y_cursor += tile_h + GAP

        # 타일 배치
        tiles = []; placed = 0
        for r in range(rows):
            if n == 5 and rows == 2:
                row_count = 3 if r == 0 else 2
            else:
                remain = n - placed
                row_count = min(cols, remain)
            row_total_w = row_count*tile_w + (row_count-1)*GAP
            rx = (SCREEN_W - row_total_w)//2
            for c in range(row_count):
                rect = pygame.Rect(rx + c*(tile_w+GAP), row_y[r], tile_w, tile_h)
                tiles.append(rect)
            placed += row_count
        self.player_tiles = tiles

        # 2줄일 때 핸드 미리보기 살짝 축소
        hand_h = HAND_H if rows == 1 else int(HAND_H * 0.85)
        hand_w = HAND_W if rows == 1 else int(HAND_W * 0.85)

        for i, (p, box) in enumerate(zip(players, tiles)):
            pygame.draw.rect(self.screen, (44,46,56), box, border_radius=16)
            pygame.draw.rect(self.screen, (60,64,78), box, 1, border_radius=16)

            name = f"{'> ' if i==current_idx else ''}{p.name}"
            t = self.font.render(name, True, ACCENT if i==current_idx else TEXT_COLOR)
            self.screen.blit(t, (box.x+16, box.y+12))

            # 손패
            px = box.x + 14
            py = box.y + 48
            for c in p.picks:
                small = pygame.Rect(px, py, hand_w, hand_h)
                face_backup = c.face_up
                c.face_up = True
                c.draw(self.screen, self.font_big, self.font_small, move_rect=small)
                c.face_up = face_backup
                px += hand_w + 8

            sc = players[i].score(max_num)
            color = OK_COLOR if sc>0 else (200,200,220)
            stext = self.font.render(f"Score: {sc}", True, color)
            self.screen.blit(stext, (box.x+16, box.bottom-36))
    # ---------- 메인 메뉴 ----------
    def draw_menu(self, opts, buttons):
        mode_name = "대화" if opts["mode"]=="dialogue" else "클래식"
        self.draw_header("숫자 카드 게임",
                        f"모드·인원·규칙을 설정하고 시작하세요 — 현재 모드: {mode_name}")

        # 좌/우 컬럼 계산(겹침 방지)
        content_w = SCREEN_W - 2*MARGIN
        gap = 16
        left_w  = int(content_w * 0.62)
        right_w = int(content_w * 0.38) - gap
        left  = pygame.Rect(MARGIN, 140, left_w, 380)
        right = pygame.Rect(MARGIN + left_w + gap, 140, right_w, 380)

        # 왼쪽 설명 카드
        pygame.draw.rect(self.screen, (34,36,44), left,  border_radius=16)
        pygame.draw.rect(self.screen, (60,64,78), left,  1, border_radius=16)

        pad = 20
        x = left.x + pad; y = left.y + pad
        def line(txt, col=TEXT_COLOR, font=None, add=36):
            nonlocal y
            f = font or self.font
            t = f.render(txt, True, col)
            self.screen.blit(t, (x, y)); y += add

        line(f"플레이어 수 : {opts['num_players']}")
        line(f"컴퓨터 참여 : {'예' if opts['use_ai'] else '아니오'}")
        line(f"게임 모드 : {mode_name}")
        # 용어 명확화
        line(f"규격 모드(1~4×N 숫자) : {'예' if opts['standard_mode'] else '아니오'}")
        line(f"조커 포함 : {'예' if opts['use_jokers'] else '아니오'}", add=42)

        line("규칙", (210,215,225), add=30)
        if opts["standard_mode"]:
            rules = [
                "• 각자 4장 선택, 합이 큰 사람이 승리",
                "• 같은 숫자 2장(페어)은 그 숫자 카드 3배",
                "• 숫자 범위: 1..(4×플레이어 수), 각 숫자 2장",
                "• (선택) 조커를 뽑으면 해당 플레이어의 점수는 0점",
                "• 셔플: Fisher–Yates (균등 무작위)",
            ]
        else:
            rules = [
                "• 각자 4장 선택, 합이 큰 사람이 승리",
                "• 같은 숫자 2장(페어)은 그 숫자 카드 3배",
                "• 숫자 범위: 1..min(4×플레이어 수, 13), 각 숫자 2장",
                "• 표기: A=1, 2..10, J=11, Q=12, K=13",
                "• (선택) 조커=0점, 셔플: Fisher–Yates",
            ]
        for r in rules:
            line(r, (185,192,205), add=30)

        # 오른쪽 버튼 패널
        pygame.draw.rect(self.screen, (34,36,44), right, border_radius=16)
        pygame.draw.rect(self.screen, (60,64,78), right, 1, border_radius=16)

        # 오른쪽 버튼들(표시명 매핑)
        label_map = {"수업 모드": "규격 모드", "모드 전환": "게임 모드"}
        order = [
            "플레이어-","플레이어+",
            "AI 토글","규격 모드","조커 포함","게임 모드",
            "게임 시작","저장","불러오기","종료"
        ]

        # ——— 반응형 배치 로직 ———
        top_pad = 20; side_pad = 20; bottom_pad = 20
        avail_h = right.height - (top_pad + bottom_pad)

        # 기본 버튼 크기(줄임)
        bh = 44      # 기존 52 → 44
        gap_v = 10   # 간격 줄임

        # 필요한 행 수
        n_btn = sum(1 for b in buttons if (label_map.get(b.label, b.label) in order))
        rows_fit_one_col = max(1, (avail_h + gap_v) // (bh + gap_v))

        # 1) 한 열로 다 안 들어가면 2열로 변경
        cols = 1
        if n_btn > rows_fit_one_col:
            cols = 2

        # 2) 2열이어도 넘치면 버튼 높이를 더 줄여서 맞춤 (최소 36)
        if cols == 2:
            rows = (n_btn + 1) // 2
            # rows*(bh) + (rows-1)*gap_v <= avail_h 조건을 만족하도록 bh 조정
            max_bh = (avail_h - (rows - 1) * gap_v) // rows
            bh = max(36, min(bh, max_bh))

        # 가로 크기/간격
        col_gap = 12
        if cols == 1:
            bw = right.width - side_pad*2
            x0 = right.x + side_pad
            x_positions = [x0]
        else:
            bw = (right.width - side_pad*2 - col_gap) // 2
            x0 = right.x + side_pad
            x_positions = [x0, x0 + bw + col_gap]

        # 배치
        y_cursor = right.y + top_pad
        col_idx = 0; row_idx = 0
        for b in buttons:
            label = label_map.get(b.label, b.label)
            if label not in order:
                continue
            b.label = label
            # 2열이면 좌우 번갈아 채우기
            if cols == 1:
                bx = x_positions[0]; by = y_cursor
                y_cursor += bh + gap_v
            else:
                bx = x_positions[col_idx]
                by = right.y + top_pad + row_idx * (bh + gap_v)
                col_idx += 1
                if col_idx >= 2:
                    col_idx = 0
                    row_idx += 1
            b.rect.update(bx, by, bw, bh)
            b.draw(self.screen, self.font)

    # ---------- 플레이 화면 ----------
    def draw_game_stack(self, title, deck_count, players, turn_idx, max_num):
        self.draw_header(title, "덱을 클릭하면 셔플 후 펼쳐집니다")
        self.draw_deck_stack(deck_count)
        self.draw_side_panel(players, turn_idx, max_num)

    def draw_game_fanned(self, title, cards, rects, players, turn_idx, max_num, hover_idx=None):
        self.draw_header(title, "원하는 카드를 클릭하거나 숫자(1..N)로 뽑기")
        self.draw_fanned(cards, rects, hover_idx)
        self.draw_side_panel(players, turn_idx, max_num)

    # ---------- 대화창 ----------
    def draw_dialogue(self, dlg):
        box_h = 160
        y = SCREEN_H - 230 - box_h - 10
        rect = pygame.Rect(MARGIN, y, SCREEN_W - MARGIN*2, box_h)
        s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        s.fill((20, 22, 28, 190))
        self.screen.blit(s, rect.topleft)
        pygame.draw.rect(self.screen, (80,84,98), rect, 1, border_radius=12)

        # 글줄 간격/표시 가능한 최대 줄수 계산
        line_h = self.font.get_height() + 4
        usable_h = box_h - 46                 # 하단 프롬프트 영역 여유분
        max_rows = max(1, usable_h // line_h)

        # 스크롤 반영해서 보일 범위 결정
        lines = list(dlg.lines)
        start = max(0, len(lines) - max_rows - dlg.scroll)
        end   = start + max_rows
        visible = lines[start:end]

        # 로그 출력
        ly = rect.y + 12
        for line in visible:
            t = self.font.render(line, True, (220,225,235))
            self.screen.blit(t, (rect.x+14, ly))
            ly += line_h

        # 프롬프트(질문/선택지)
        if dlg.awaiting and dlg.prompt:
            q = self.font.render(dlg.prompt["text"], True, (255,206,84))
            self.screen.blit(q, (rect.x+14, rect.bottom-34))
            c = ", ".join(dlg.prompt["choices"])
            cc = self.font_small.render(f"[{c}] 입력", True, (185,192,205))
            self.screen.blit(cc, (rect.right-14-cc.get_width(), rect.bottom-30))

        # 현재 숫자 타이핑 상태(예: '입력: 12')
        if getattr(dlg, "typing", ""):
            ti = self.font_small.render(f"입력: {dlg.typing}", True, (200,210,225))
            self.screen.blit(ti, (rect.right-14-ti.get_width(), rect.y+12))

        # 게임 루프에서 휠 처리할 수 있도록 저장
        self.dialog_rect = rect
        self.dialog_max_rows = max_rows

    # ---------- 결과 화면 ----------
    def draw_result_screen(self, players, max_num):
        self.draw_header("결과", "아무 곳이나 클릭하면 메뉴로 돌아갑니다")
        panel = pygame.Rect(MARGIN, 160, SCREEN_W - MARGIN*2, 360)
        pygame.draw.rect(self.screen, (34,36,44), panel, border_radius=16)
        pygame.draw.rect(self.screen, (60,64,78), panel, 1, border_radius=16)
        rows = [(p.name, p.score(max_num)) for p in players]
        rows.sort(key=lambda x:x[1], reverse=True)
        y = panel.y + 24
        for rank, (name, sc) in enumerate(rows, 1):
            line = f"{rank}. {name}"
            t = self.font.render(line, True, TEXT_COLOR)
            s = self.font.render(f"{sc}", True, OK_COLOR if sc>0 else (220,220,230))
            self.screen.blit(t, (panel.x+24, y))
            self.screen.blit(s, (panel.right-24 - s.get_width(), y))
            y += 44
        tip = self.font_small.render("다시 시작: 메뉴에서 ‘게임 시작’", True, (185,192,205))
        self.screen.blit(tip, (panel.x+24, panel.bottom-36))
