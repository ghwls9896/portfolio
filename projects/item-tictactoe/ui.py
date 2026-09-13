# tictactok/ui.py
"""
UI/렌더링:
- 폰트 초기화(이모지 폴백), 텍스트 안전 렌더(render_mix)
- Button 위젯
- HUD/보드/토스트/배너 렌더
- 좌표 변환(point_to_cell), 보드 사각형 계산 등
"""

import pygame
from config import *
from rules import neighbors4

# ── 폰트/이모지 폴백 ──
font_text = font_small = font_big = font_emoji = None

ZERO_WIDTH = {0xFE0F, 0x200D, 0x200C, 0x2060, 0x034F}

def init_fonts():
    global font_text, font_small, font_big, font_emoji
    font_text  = pygame.font.SysFont("malgungothic,applegothic,arial,pretendard", 22)
    font_small = pygame.font.SysFont("malgungothic,applegothic,arial,pretendard", 18)
    font_big   = pygame.font.SysFont("malgungothic,applegothic,arial,pretendard", 32, bold=True)
    font_emoji = pygame.font.SysFont("Segoe UI Emoji, Apple Color Emoji, Noto Color Emoji", 26)

def is_emoji_cp(cp:int)->bool:
    return (0x1F000<=cp<=0x1FAFF) or (0x1F300<=cp<=0x1F5FF) or (0x1F600<=cp<=0x1F64F) or (0x1F680<=cp<=0x1F6FF) or (0x2600<=cp<=0x27BF)

def safe_render_char(ch:str,color,ftxt,femj):
    cp=ord(ch)
    if cp in ZERO_WIDTH: return None
    surf=None
    if is_emoji_cp(cp):
        try:
            s=femj.render(ch,True,color)
            if s.get_width()>0: surf=s
        except: pass
    if surf is None:
        try:
            s=ftxt.render(ch,True,color)
            if s.get_width()>0: surf=s
        except: pass
    return surf

def render_mix(text:str,*,small=False,big=False,color=(255,255,255)):
    ftxt = font_small if small else (font_big if big else font_text)
    femj = font_emoji
    lines=text.split("\n"); parts=[]; max_w=0; total_h=0
    for line in lines:
        x=0; h=0; seg=[]
        for ch in line:
            s=safe_render_char(ch,color,ftxt,femj)
            if s is None: continue
            seg.append((s,x)); x+=s.get_width(); h=max(h,s.get_height())
        sline=pygame.Surface((max(1,x), max(1,h)), pygame.SRCALPHA)
        for s,px in seg: sline.blit(s,(px,0))
        parts.append(sline); max_w=max(max_w,sline.get_width()); total_h+=sline.get_height()
    total_h+=max(0,len(parts)-1)*4
    out=pygame.Surface((max(1,max_w), max(1,total_h)), pygame.SRCALPHA)
    y=0
    for s in parts: out.blit(s,(0,y)); y+=s.get_height()+4
    return out

# ── 좌표/보드 영역 ──
def get_board_rect(area: pygame.Rect, N: int):
    sz = min(area.w, area.h)
    return pygame.Rect(area.x, area.y + (area.h - sz)//2, sz, sz)

def point_to_cell(pos, N, area: pygame.Rect):
    grid = get_board_rect(area, N)
    if not grid.collidepoint(pos): return None
    cw = grid.w / N; ch = grid.h / N
    cx = int((pos[0] - grid.x) // cw); cy = int((pos[1] - grid.y) // ch)
    if 0 <= cx < N and 0 <= cy < N: return (cy, cx)
    return None

# ── 위젯 & 렌더 ──
class Button:
    def __init__(self,rect,text,toggle_values=None,initial=None):
        self.rect=pygame.Rect(rect); self.text=text
        self.toggle=toggle_values; self.value=initial if initial is not None else (toggle_values[0] if toggle_values else None)
        self.enabled=True
    def draw(self,surf):
        pygame.draw.rect(surf,PANEL_BG,self.rect,border_radius=12)
        pygame.draw.rect(surf,BORDER if self.enabled else (70,70,78),self.rect,1,border_radius=12)
        label=f"{self.text}: {self.value}" if self.toggle else self.text
        s=render_mix(label,color=(TEXT if self.enabled else DISABLED))
        surf.blit(s, s.get_rect(center=self.rect.center))
    def handle(self,ev):
        if not self.enabled: return False
        if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1 and self.rect.collidepoint(ev.pos):
            if self.toggle:
                i=self.toggle.index(self.value)
                self.value=self.toggle[(i+1)%len(self.toggle)]
            return True
        return False

def actor_tag(actor):
    if actor=="X": return render_mix("[X] ", color=ACCENT), ACCENT
    if actor=="O": return render_mix("[O] ", color=WARN), WARN
    return render_mix("", color=TEXT), TEXT

def draw_item_legend(screen, panel_rect):
    x=panel_rect.x+20; y=panel_rect.y+290
    lines=[
        ("아이템 안내",TEXT,True,12),
        ("🔗 수갑: 상대 다음 턴 스킵",SUBTLE,False,8),
        ("🛡️ 방패: 수갑/스왑 자동차단(최대2)",SUBTLE,False,8),
        ("🦘 더블턴: 인접칸 한 번 더",SUBTLE,False,8),
        ("🔒 락: 빈칸 3턴 잠금",SUBTLE,False,8),
        ("♻️ 스왑: 내 돌↔상대 돌 교환",SUBTLE,False,8),
        ("💣 폭탄: 중심+십자 비움",SUBTLE,False,8),
    ]
    cy=y
    for text,col,is_title,gap in lines:
        s=render_mix(text,big=is_title,small=not is_title,color=col)
        screen.blit(s,(x,cy)); cy+=s.get_height()+gap

def draw_toasts(screen, state):
    base_x=WINDOW_W-560; base_y=WINDOW_H-40
    for i,(actor,msg,ttl,col) in enumerate(state.toasts):
        tag,_=actor_tag(actor); txt=render_mix(msg,color=col)
        surf=pygame.Surface((tag.get_width()+txt.get_width()+8, max(tag.get_height(),txt.get_height())), pygame.SRCALPHA)
        surf.blit(tag,(0,0)); surf.blit(txt,(tag.get_width()+4,0))
        screen.blit(surf,(base_x, base_y - i*34))

def draw_banner(screen, state, area):
    if not state.last_banner: return
    actor,msg,color=state.last_banner
    tag,_=actor_tag(actor); txt=render_mix(msg,color=color)
    pad=10; w=tag.get_width()+txt.get_width()+pad*3; h=max(tag.get_height(),txt.get_height())+pad*2
    grid=get_board_rect(area,state.N)
    rect=pygame.Rect(grid.x, max(MARGIN, grid.y- h - 16), w, h)
    pygame.draw.rect(screen,(40,40,48),rect,border_radius=10)
    pygame.draw.rect(screen,(80,80,95),rect,1,border_radius=10)
    screen.blit(tag,(rect.x+pad, rect.y+pad)); screen.blit(txt,(rect.x+pad+tag.get_width()+8, rect.y+pad))

def draw_game(screen, state, cfg, area):
    grid=get_board_rect(area,state.N)
    turn_label=render_mix(f"턴: {state.turn}", big=True, color=(ACCENT if state.turn=="X" else WARN))
    meta_label=render_mix(f"🛡️ X:{state.shield['X']}  O:{state.shield['O']}   🔒 잠금:{len(state.locks)}   아이템전:{'ON' if state.items_on else 'OFF'}", color=TEXT)
    screen.blit(turn_label,(grid.x, max(MARGIN, grid.y-78)))
    screen.blit(meta_label,(grid.x+turn_label.get_width()+16, max(MARGIN, grid.y-64)))

    pygame.draw.rect(screen,PANEL_BG,grid,border_radius=18)
    pygame.draw.rect(screen,BORDER,grid,1,border_radius=18)
    N=state.N; cw=grid.w/N; ch=grid.h/N
    hover=point_to_cell(pygame.mouse.get_pos(),N,area)

    for r in range(N):
        for c in range(N):
            rect=pygame.Rect(grid.x+c*cw+2, grid.y+r*ch+2, cw-4, ch-4)
            base=(35,35,42) if hover!=(r,c) else (46,46,56)
            pygame.draw.rect(screen,base,rect,border_radius=12)
            if (r,c) in state.locks:
                pygame.draw.rect(screen,LOCK_COL,rect,2,border_radius=12)
                s=render_mix(f"🔒{state.locks[(r,c)]}",small=True,color=LOCK_COL)
                screen.blit(s, s.get_rect(center=(rect.centerx, rect.y+12)))
            mk=state.board[r][c]
            if mk:
                col=ACCENT if mk=="X" else WARN
                lbl=render_mix(mk,big=True,color=col)
                screen.blit(lbl,lbl.get_rect(center=rect.center))

    if state.last_move and not state.game_over:
        lr,lc=state.last_move
        rect=pygame.Rect(grid.x+lc*cw+2, grid.y+lr*ch+2, cw-4, ch-4)
        pygame.draw.rect(screen,HL_LAST,rect,3,border_radius=12)

    if state.winning_cells:
        for (r,c) in state.winning_cells:
            rect=pygame.Rect(grid.x+c*cw+2, grid.y+r*ch+2, cw-4, ch-4)
            pygame.draw.rect(screen,(255,255,255),rect,4,border_radius=12)

    if state.double_stage==1 and state.last_move and not state.game_over:
        r,c=state.last_move
        for rr,cc in neighbors4(state.N,r,c):
            from rules import in_bounds
            if (0<=rr<state.N and 0<=cc<state.N) and state.board[rr][cc]=="" and (rr,cc) not in state.locks:
                rect=pygame.Rect(grid.x+cc*cw+2, grid.y+rr*ch+2, cw-4, ch-4)
                pygame.draw.rect(screen,(120,200,255),rect,2,border_radius=12)
