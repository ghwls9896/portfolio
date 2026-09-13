# tic_tactok_item_edition.py — 완전 개정본 (2025-09-22, lock 마지막칸 & sticky toasts 개선)
# - 정확한 N연속 승리 판정(수평/수직/대각/역대각)
# - 보드: 3/4/5/6
# - 모드: 2인용 / AI(Easy~Very Hard)  ← 2인용 선택 시 난이도 버튼 비활성
# - 아이템전: 즉발(인벤토리 없음), “셀 1회 소모” 규칙 (그 칸에서 한 번 아이템 발동되면 영구 비활성)
# - 아이템: 🛡️, 🦘, 🔒, ♻️, 🔗, 💣
# - 스폰: 25% (수갑↑, 더블턴↓)
# - 더블턴: double_stage=0/1로 강제 소비, 2수째 DOUBLE 금지
# - 타깃 모드 중엔 턴 정지(사람/AI 모두), 완료 직후 같은 턴 마무리
# - AI: 휴리스틱+정렬+TT+깊이 상향, 1·2수 사이 350ms 딜레이
# - 이모지 폴백 렌더링, 다크 UI
import random, sys, pygame
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ───────── Config/UI ─────────
WINDOW_W, WINDOW_H = 1360, 900
FPS = 60
MARGIN = 24
AI_DELAY_MS = 350

DARK_BG   = (18, 18, 22)
PANEL_BG  = (28, 28, 34)
BORDER    = (54, 54, 63)
TEXT      = (232, 232, 238)
SUBTLE    = (160, 160, 170)
ACCENT    = (120, 180, 255)  # X
WARN      = (255, 190, 90)   # O
GOOD      = (100, 220, 150)
BAD       = (255, 110, 110)
LOCK_COL  = (180, 130, 255)
DISABLED  = (110, 110, 120)
HL_LAST   = (90, 160, 250)

BOARD_CHOICES = [3,4,5,6]
MODES = ["2인용","AI"]
DIFFS = ["Easy","Medium","Hard","Very Hard"]

# 아이템 확률/가중치
ITEM_SPAWN_RATE = 0.25
ITEM_WEIGHTS = {"SHIELD":0.22,"DOUBLE":0.10,"LOCK":0.20,"SWAP":0.14,"CUFF":0.26,"BOMB":0.08}
MAX_SHIELD = 2
LOCK_DURATION = 3

# ───────── Data ─────────
@dataclass
class Config:
    size:int=3
    mode:str="AI"
    difficulty:str="Very Hard"
    items_on:bool=True

@dataclass
class GameState:
    N:int
    board:List[List[str]]=field(init=False)
    turn:str="X"
    winner:Optional[str]=None
    winning_cells:List[Tuple[int,int]]=field(default_factory=list)
    skip_next:Dict[str,bool]=field(default_factory=lambda:{"X":False,"O":False})
    shield:Dict[str,int]=field(default_factory=lambda:{"X":0,"O":0})
    locks:Dict[Tuple[int,int],int]=field(default_factory=dict)
    last_move:Optional[Tuple[int,int]]=None
    items_on:bool=True

    # 이벤트
    toasts:List[Tuple[Optional[str], str, int, Tuple[int,int,int]]]=field(default_factory=list)  # (actor,msg,ttl,color)  ← ttl은 유지하되 소모는 안함
    last_banner:Optional[Tuple[Optional[str],str,Tuple[int,int,int]]]=None
    game_over:bool=False

    # 더블턴: 0=없음, 1=두 번째 수 대기
    double_stage:int=0

    # 타깃 선택(LOCK/SWAP)
    pending:Optional[tuple]=None  # ("LOCK",owner) | ("SWAP_MY",owner) | ("SWAP_OPP",owner,(r,c))

    # AI 딜레이
    ai_pending:bool=False
    ai_wake:int=0
    ai_second_pending:bool=False
    ai_second_wake:int=0

    # “셀 1회 소모” 규칙: 아이템이 한 번이라도 발동된 셀 좌표(영구)
    item_spent_cells:set=field(default_factory=set)

    # AI 트랜스포지션
    tt:dict=field(default_factory=dict)

    def __post_init__(self):
        self.board=[["" for _ in range(self.N)] for _ in range(self.N)]

# ───────── Fonts / Emoji-safe ─────────
font_text=font_small=font_big=font_emoji=None
def init_fonts():
    global font_text, font_small, font_big, font_emoji
    font_text  = pygame.font.SysFont("malgungothic,applegothic,arial,pretendard", 22)
    font_small = pygame.font.SysFont("malgungothic,applegothic,arial,pretendard", 18)
    font_big   = pygame.font.SysFont("malgungothic,applegothic,arial,pretendard", 32, bold=True)
    font_emoji = pygame.font.SysFont("Segoe UI Emoji, Apple Color Emoji, Noto Color Emoji", 26)

ZERO_WIDTH = {0xFE0F,0x200D,0x200C,0x2060,0x034F}
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

# ───────── Utils / Rules ─────────
def in_bounds(N,r,c): return 0<=r<N and 0<=c<N
def neighbors4(N,r,c):
    for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        rr,cc=r+dr,c+dc
        if in_bounds(N,rr,cc): yield rr,cc
def check_victory(board,N,mark):
    dirs=[(0,1),(1,0),(1,1),(1,-1)]
    for r in range(N):
        for c in range(N):
            if board[r][c]!=mark: continue
            for dr,dc in dirs:
                pr,pc=r-dr,c-dc
                if in_bounds(N,pr,pc) and board[pr][pc]==mark: continue
                cnt=0; rr,cc=r,c
                while in_bounds(N,rr,cc) and board[rr][cc]==mark:
                    cnt+=1
                    if cnt==N:
                        return True,[(r+i*dr,c+i*dc) for i in range(N)]
                    rr+=dr; cc+=dc
    return False,[]
def board_full(board):
    N=len(board)
    return all(board[r][c]!="" for r in range(N) for c in range(N))
def empty_cells(state:GameState):
    return [(r,c) for r in range(state.N) for c in range(state.N) if state.board[r][c]=="" and (r,c) not in state.locks]
def get_board_rect(area:pygame.Rect,N:int):
    sz=min(area.w,area.h); return pygame.Rect(area.x, area.y+(area.h-sz)//2, sz, sz)
def point_to_cell(pos,N,area:pygame.Rect):
    grid=get_board_rect(area,N)
    if not grid.collidepoint(pos): return None
    cw=grid.w/N; ch=grid.h/N
    cx=int((pos[0]-grid.x)//cw); cy=int((pos[1]-grid.y)//ch)
    if 0<=cx<N and 0<=cy<N: return (cy,cx)
    return None
def can_place(state:GameState,r,c)->bool:
    return in_bounds(state.N,r,c) and state.board[r][c]=="" and (r,c) not in state.locks

# ───────── Events ─────────
def actor_tag(actor:Optional[str]):
    if actor=="X": return render_mix("[X] ", color=ACCENT), ACCENT
    if actor=="O": return render_mix("[O] ", color=WARN), WARN
    return render_mix("", color=TEXT), TEXT
def push_event(state:GameState, actor:Optional[str], message:str, color=TEXT, ttl=999999):
    # ttl은 보관만 하고 그리기에서 소모하지 않음(클릭 시 한 번에 clear)
    state.toasts.append((actor,message,ttl,color)); state.last_banner=(actor,message,color)

# ───────── Items ─────────
def roll_item(allow_double:bool=True)->Optional[str]:
    if random.random()>=ITEM_SPAWN_RATE: return None
    weights=ITEM_WEIGHTS.copy()
    if not allow_double and "DOUBLE" in weights:
        weights["DOUBLE"]=0.0
    total=sum(weights.values())
    if total<=0: return None
    x=random.random()*total; acc=0.0
    for k,w in weights.items():
        acc+=w
        if x<=acc: return k
    return None

def apply_item(state:GameState, owner:str, item:str, for_ai:bool, origin:Tuple[int,int]):
    opp="O" if owner=="X" else "X"
    if item=="SHIELD":
        if state.shield[owner]<MAX_SHIELD: state.shield[owner]+=1
        push_event(state,owner,f"🛡️ 방패 +1 (현재 {state.shield[owner]}/{MAX_SHIELD})",GOOD)

    elif item=="CUFF":
        if state.shield[opp]>0:
            state.shield[opp]-=1
            push_event(state,owner,f"🛡️ {opp}의 방패가 수갑을 막음 (잔여 {state.shield[opp]})",WARN)
        else:
            state.skip_next[opp]=True
            push_event(state,owner,f"🔗 수갑! {opp}의 다음 턴 스킵",BAD)

    elif item=="DOUBLE":
        # 첫 수일 때만 유효; 두 번째 수에서는 금지되어 들어오지 않음
        if state.double_stage==0:
            state.double_stage=1
            push_event(state,owner,"🦘 더블턴! 인접 칸에 한 번 더",ACCENT)
        else:
            push_event(state,owner,"🦘 더블턴은 2수째에는 무효",SUBTLE)

    elif item=="LOCK":
        if for_ai:
            t=choose_lock_target_ai(state)
            if t:
                state.locks[t]=LOCK_DURATION
                push_event(state,owner,f"🔒 잠금 {t} ({LOCK_DURATION}턴)",LOCK_COL)
            else:
                push_event(state,owner,"🔒 잠글 칸 없음",SUBTLE)
        else:
            # ⬇️ 사람의 락: 타깃 가능한 빈 칸이 하나라도 있어야 pending
            targets = empty_cells(state)
            if not targets:
                push_event(state,owner,"🔒 잠글 칸 없음",SUBTLE)
            else:
                push_event(state,owner,"🔒 잠글 빈 칸을 선택하세요",ACCENT)
                state.pending=("LOCK",owner)

    elif item=="BOMB":
        if origin:
            r,c=origin
            affected={(r,c),*set(neighbors4(state.N,r,c))}
            for rr,cc in affected: state.board[rr][cc]=""  # 락은 유지
            push_event(state,owner,f"💣 폭탄! 십자 {len(affected)}칸 초기화",BAD)
        else:
            push_event(state,owner,"💣 폭탄 발동 위치 없음",SUBTLE)

    elif item=="SWAP":
        # 양쪽 돌 존재여부 사전 확인 (없으면 무효)
        my_has  = any(state.board[r][c]==owner for r in range(state.N) for c in range(state.N))
        opp_has = any(state.board[r][c]==opp   for r in range(state.N) for c in range(state.N))
        if not my_has or not opp_has:
            push_event(state, owner, "♻️ 스왑 타깃 없음 → 아이템 무효", SUBTLE)
            return
        if state.shield[opp]>0:
            state.shield[opp]-=1
            push_event(state,owner,f"🛡️ {opp}의 방패가 스왑을 막음 (잔여 {state.shield[opp]})",WARN)
            return
        if for_ai:
            do_ai_swap(state,owner)
        else:
            push_event(state,owner,"♻️ 스왑: 내 돌 → 상대 돌 순서로 선택",ACCENT)
            state.pending=("SWAP_MY",owner)

def choose_lock_target_ai(state:GameState)->Optional[Tuple[int,int]]:
    opp="O" if state.turn=="X" else "X"
    for r,c in empty_cells(state):
        state.board[r][c]=opp
        w,_=check_victory(state.board,state.N,opp)
        state.board[r][c]=""
        if w: return (r,c)
    cells=empty_cells(state)
    return random.choice(cells) if cells else None

def do_ai_swap(state:GameState, owner:str):
    opp="O" if owner=="X" else "X"
    my=[(r,c) for r in range(state.N) for c in range(state.N) if state.board[r][c]==owner]
    op=[(r,c) for r in range(state.N) for c in range(state.N) if state.board[r][c]==opp]
    if not my or not op:
        push_event(state,owner,"♻️ 스왑 타깃 없음",SUBTLE); return
    a=random.choice(my); b=random.choice(op)
    ra,ca=a; rb,cb=b
    state.board[ra][ca],state.board[rb][cb]=state.board[rb][cb],state.board[ra][ca]
    push_event(state,owner,f"♻️ 스왑: {a} ↔ {b}",ACCENT)

# ───────── AI (강화) ─────────
def find_winning_move(board,N,mark):
    for r in range(N):
        for c in range(N):
            if board[r][c]=="":
                board[r][c]=mark
                w,_=check_victory(board,N,mark)
                board[r][c]=""
                if w: return (r,c)
    return None

def heuristic_score(board,N,mark):
    dirs=[(0,1),(1,0),(1,1),(1,-1)]
    opp="O" if mark=="X" else "X"; score=0
    cx=(N-1)/2; cy=(N-1)/2
    for r in range(N):
        for c in range(N):
            if board[r][c]==mark:
                score += 1.5 - (abs(r-cx)+abs(c-cy))*0.1
                for rr,cc in neighbors4(N,r,c):
                    if board[rr][cc]==mark: score+=0.2
    for r in range(N):
        for c in range(N):
            for dr,dc in dirs:
                cells=[]; rr,cc=r,c
                for _ in range(N):
                    if not (0<=rr<N and 0<=cc<N): cells=[]; break
                    cells.append(board[rr][cc]); rr+=dr; cc+=dc
                if len(cells)<N: continue
                if opp not in cells:
                    k=cells.count(mark)
                    if k==N: score+=20000
                    elif k==N-1: score+=450
                    elif k==N-2: score+=70
                    elif k==1: score+=6
                if mark not in cells:
                    k2=cells.count(opp)
                    if k2==N-1: score-=420
                    elif k2==N-2: score-=65
    return score

def board_key(board): return tuple(tuple(row) for row in board)

def order_moves(state:GameState, me:str, moves:List[Tuple[int,int]]):
    N=state.N; opp="O" if me=="X" else "X"; cx=(N-1)/2; cy=(N-1)/2
    scored=[]
    for r,c in moves:
        s=0.0
        s -= (abs(r-cx)+abs(c-cy))*0.1               # 중앙 성향
        for rr,cc in neighbors4(N,r,c):             # 인접 보너스
            if state.board[rr][cc]==me: s+=0.2
        state.board[r][c]=me; w,_=check_victory(state.board,N,me); state.board[r][c]=""
        if w: s+=10000
        state.board[r][c]=opp; b,_=check_victory(state.board,N,opp); state.board[r][c]=""
        if b: s+=5000
        scored.append(((r,c), s))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [p for p,_ in scored]

def minimax(state:GameState, me:str, depth:int, alpha:float, beta:float, maximizing:bool):
    N=state.N; board=state.board; opp="O" if me=="X" else "X"
    k=(board_key(board), depth, maximizing)
    if k in state.tt: return state.tt[k]
    w,_=check_victory(board,N,me)
    if w: return (20000, None)
    w2,_=check_victory(board,N,opp)
    if w2: return (-20000, None)
    if depth==0 or board_full(board):
        val=heuristic_score(board,N,me)-heuristic_score(board,N,opp)
        state.tt[k]=(val,None); return val,None
    legal=[(r,c) for r in range(N) for c in range(N) if board[r][c]=="" and (r,c) not in state.locks]
    if not legal:
        val=heuristic_score(board,N,me)-heuristic_score(board,N,opp)
        state.tt[k]=(val,None); return val,None
    legal=order_moves(state, me if maximizing else opp, legal)
    best=None
    if maximizing:
        val=-1e18
        for r,c in legal:
            board[r][c]=me
            v,_=minimax(state, me, depth-1, alpha, beta, False)
            board[r][c]=""
            if v>val: val=v; best=(r,c)
            alpha=max(alpha,v)
            if beta<=alpha: break
    else:
        val=1e18
        for r,c in legal:
            board[r][c]=opp
            v,_=minimax(state, me, depth-1, alpha, beta, True)
            board[r][c]=""
            if v<val: val=v; best=(r,c)
            beta=min(beta,v)
            if beta<=alpha: break
    state.tt[k]=(val,best); return val,best

def ai_choose_move(state:GameState, difficulty:str):
    N=state.N; me=state.turn; opp="O" if me=="X" else "X"
    legal=[(r,c) for (r,c) in empty_cells(state) if can_place(state,r,c)]
    if not legal: return None
    mv=find_winning_move(state.board,N,me)
    if mv and can_place(state,*mv): return mv
    bm=find_winning_move(state.board,N,opp)
    if bm and can_place(state,*bm): return bm
    depth_map={"Easy":{3:2,4:2,5:1,6:1},"Medium":{3:4,4:3,5:2,6:2},"Hard":{3:6,4:4,5:3,6:3},"Very Hard":{3:8,4:6,5:4,6:4}}
    d=depth_map[difficulty].get(N,3)
    state.tt.clear()
    _,mv=minimax(state, me, d, -1e18, 1e18, True)
    return mv if (mv and can_place(state,*mv)) else order_moves(state, me, legal)[0]

# ───────── UI ─────────
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

def draw_item_legend(screen,panel_rect):
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

def draw_toasts(screen,state:GameState):
    # 클릭 전까지 계속 유지 (TTL 소모 없음)
    base_x=WINDOW_W-560; base_y=WINDOW_H-40
    for i,(actor,msg,ttl,col) in enumerate(state.toasts):
        tag,_=actor_tag(actor); txt=render_mix(msg,color=col)
        surf=pygame.Surface((tag.get_width()+txt.get_width()+8, max(tag.get_height(),txt.get_height())), pygame.SRCALPHA)
        surf.blit(tag,(0,0)); surf.blit(txt,(tag.get_width()+4,0))
        screen.blit(surf,(base_x, base_y - i*34))

def draw_banner(screen,state:GameState,area:pygame.Rect):
    if not state.last_banner: return
    actor,msg,color=state.last_banner
    tag,_=actor_tag(actor); txt=render_mix(msg,color=color)
    pad=10; w=tag.get_width()+txt.get_width()+pad*3; h=max(tag.get_height(),txt.get_height())+pad*2
    grid=get_board_rect(area,state.N)
    rect=pygame.Rect(grid.x, max(MARGIN, grid.y- h - 16), w, h)
    pygame.draw.rect(screen,(40,40,48),rect,border_radius=10)
    pygame.draw.rect(screen,(80,80,95),rect,1,border_radius=10)
    screen.blit(tag,(rect.x+pad, rect.y+pad)); screen.blit(txt,(rect.x+pad+tag.get_width()+8, rect.y+pad))

def draw_game(screen,state:GameState,cfg:Config,area:pygame.Rect):
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
            if can_place(state,rr,cc):
                rect=pygame.Rect(grid.x+cc*cw+2, grid.y+rr*ch+2, cw-4, ch-4)
                pygame.draw.rect(screen,(120,200,255),rect,2,border_radius=12)

# ───────── Flow ─────────
def finalize_and_maybe_end(state:GameState,player:str)->bool:
    w,cells=check_victory(state.board,state.N,player)
    if w:
        state.winner=player; state.winning_cells=cells; state.game_over=True
        push_event(state, player, f"🏆 {player} 승리!", GOOD); return True
    if board_full(state.board):
        state.game_over=True; push_event(state, None, "🤝 무승부!", SUBTLE); return True
    return False

def end_turn(state:GameState):
    expired=[]
    for pos,t in list(state.locks.items()):
        nt=t-1
        if nt<=0: expired.append(pos)
        else: state.locks[pos]=nt
    for pos in expired: del state.locks[pos]
    state.turn="O" if state.turn=="X" else "X"

def handle_click(state:GameState,cfg:Config,pos,area:pygame.Rect):
    if state.game_over: return

    # 스킵
    if state.skip_next[state.turn]:
        state.skip_next[state.turn]=False
        push_event(state, state.turn, f"🔗 {state.turn} 턴 스킵", WARN)
        end_turn(state); return

    cell=point_to_cell(pos,state.N,area)
    if cell is None: return
    r,c=cell

    # ① 타깃 선택(Lock/Swap) 우선
    if state.pending:
        kind,owner=state.pending[0],state.pending[1]
        opp="O" if owner=="X" else "X"
        if owner!=state.turn: return

        if kind=="LOCK":
            if can_place(state,r,c):
                state.locks[(r,c)]=LOCK_DURATION
                push_event(state, owner, f"🔒 잠금 {(r,c)} ({LOCK_DURATION}턴)", LOCK_COL)
                state.pending=None
                # 타깃 완료 후: 더블턴 대기 중이면 그대로 2수 진행, 아니면 턴 마무리
                if state.double_stage==0:
                    if not finalize_and_maybe_end(state, owner): end_turn(state)
            else:
                push_event(state, owner, "🔒 빈 칸만 가능", WARN)
            return

        if kind=="SWAP_MY":
            # 내 돌 고르기 전에 '상대 돌 존재' 재확인 (없으면 취소)
            opp_has = any(state.board[rr][cc]==opp for rr in range(state.N) for cc in range(state.N))
            if not opp_has:
                state.pending=None
                push_event(state, owner, "♻️ 상대 돌이 없어 스왑 취소", SUBTLE)
                if state.double_stage==0:
                    if not finalize_and_maybe_end(state, owner): end_turn(state)
                return
            if state.board[r][c]==owner:
                state.pending=("SWAP_OPP",owner,(r,c))
                push_event(state, owner, "♻️ 상대 돌을 선택하세요", ACCENT)
            else:
                push_event(state, owner, "♻️ 내 돌부터 선택", WARN)
            return

        if kind=="SWAP_OPP":
            myrc=state.pending[2]
            # 안전장치: 이 순간 상대 돌이 0개면 취소
            if not any(state.board[rr][cc]==opp for rr in range(state.N) for cc in range(state.N)):
                state.pending=None
                push_event(state, owner, "♻️ 상대 돌이 없어 스왑 취소", SUBTLE)
                if state.double_stage==0:
                    if not finalize_and_maybe_end(state, owner): end_turn(state)
                return
            if state.board[r][c]==opp:
                ra,ca=myrc; rb,cb=r,c
                state.board[ra][ca],state.board[rb][cb]=state.board[rb][cb],state.board[ra][ca]
                push_event(state, owner, f"♻️ 스왑: {myrc} ↔ {(r,c)}", ACCENT)
                state.pending=None
                if state.double_stage==0:
                    if not finalize_and_maybe_end(state, owner): end_turn(state)
            else:
                push_event(state, owner, "♻️ 상대 돌을 선택", WARN)
            return

    # ② 정상 착수
    if not can_place(state,r,c):
        push_event(state, state.turn, "🚫 둘 수 없는 칸(잠금/점유)", BAD); return

    # 이번 클릭이 2수째인지 판정
    is_second = (state.double_stage==1 and state.last_move is not None and (r,c) in set(neighbors4(state.N,*state.last_move)))
    if state.double_stage==1 and not is_second:
        push_event(state, state.turn, "🦘 인접 칸만 가능합니다", WARN); return

    me=state.turn
    state.board[r][c]=me; state.last_move=(r,c)

    # ③ 아이템 롤(“셀 1회 소모”): 2수째는 더블턴 금지
    if state.items_on and (r,c) not in state.item_spent_cells:
        it=roll_item(allow_double=not is_second)
        if it:
            apply_item(state,me,it,for_ai=False,origin=(r,c))
            state.item_spent_cells.add((r,c))
            # 타깃 선택으로 진입하면 이 턴 유지
            if state.pending: return

    # ④ 더블턴 소비/대기
    if is_second:
        state.double_stage=0   # ★ 반드시 소비
        if not finalize_and_maybe_end(state, me): end_turn(state)
        return
    else:
        if state.double_stage==1:
            # 2수 대기 — 인접 가능이 없으면 무효
            adj=[(rr,cc) for rr,cc in neighbors4(state.N,r,c) if can_place(state,rr,cc)]
            if not adj:
                push_event(state, me, "🦘 인접 칸 없음 → 더블턴 무효", WARN)
                state.double_stage=0
            else:
                return  # 플레이어가 2수째를 두도록 대기

    # ⑤ 평소 턴 마무리
    if not finalize_and_maybe_end(state, me): end_turn(state)

# ───────── Main ─────────
def main():
    pygame.init()
    pygame.display.set_caption("틱택톡: 아이템 에디션 (Python)")
    screen=pygame.display.set_mode((WINDOW_W,WINDOW_H))
    clock=pygame.time.Clock()
    init_fonts()

    panel=pygame.Rect(MARGIN,MARGIN,340,WINDOW_H-2*MARGIN)
    board_area=pygame.Rect(panel.right+MARGIN, MARGIN, WINDOW_W - panel.width - 3*MARGIN, WINDOW_H - 2*MARGIN)

    btn_start=Button((panel.x+20, panel.bottom-70, 140, 48),"▶ 시작")
    btn_reset=Button((panel.x+180, panel.bottom-70, 140, 48),"↻ 재시작")
    b_mode   =Button((panel.x+20, panel.y+70, 300, 46),"모드",MODES,"AI")
    b_diff   =Button((panel.x+20, panel.y+120,300, 46),"난이도",DIFFS,"Very Hard")
    b_size   =Button((panel.x+20, panel.y+170,300, 46),"보드",BOARD_CHOICES,3)
    b_items  =Button((panel.x+20, panel.y+220,300, 46),"아이템전",["ON","OFF"],"ON")

    def new_config():
        return Config(size=b_size.value, mode=b_mode.value,
                      difficulty=b_diff.value if b_mode.value=="AI" else "Medium",
                      items_on=(b_items.value=="ON"))

    def start_game():
        nonlocal cfg, st
        cfg=new_config()
        st=GameState(N=cfg.size, items_on=cfg.items_on)
        st.turn="X"; st.toasts.clear(); st.last_banner=None
        st.pending=None; st.double_stage=0
        st.ai_pending=False; st.ai_second_pending=False
        st.item_spent_cells.clear(); st.tt.clear()

    cfg=new_config(); st=GameState(N=3, items_on=True); st.pending=None
    start_game()

    running=True
    while running:
        now=pygame.time.get_ticks()
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: running=False
            elif ev.type==pygame.KEYDOWN:
                if ev.key==pygame.K_ESCAPE: running=False
                if ev.key==pygame.K_r: start_game()

            # 👇 클릭하면 기존 토스트/배너를 먼저 지워 줌(새 이벤트는 정상 표시)
            if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                if st:
                    st.toasts.clear()
                    st.last_banner=None

            if b_mode.handle(ev): b_diff.enabled=(b_mode.value=="AI")
            b_diff.handle(ev); b_size.handle(ev); b_items.handle(ev)
            if btn_start.handle(ev): start_game()
            if btn_reset.handle(ev): start_game()

            if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                if cfg.mode=="AI" and st.turn=="O" and not st.game_over:
                    pass
                else:
                    handle_click(st,cfg,ev.pos,board_area)

        # ── AI 턴 ──
        if cfg.mode=="AI" and not st.game_over:
            # 플레이어가 타깃 선택 중이면 AI 금지
            if st.pending and st.pending[1]!="O":
                st.ai_pending=False; st.ai_second_pending=False
            elif st.turn=="O":
                if st.skip_next["O"]:
                    st.skip_next["O"]=False
                    push_event(st,"O","🔗 O 턴 스킵",WARN)
                    end_turn(st)
                else:
                    # 첫 수 대기/실행
                    if not st.ai_pending and not st.ai_second_pending:
                        st.ai_pending=True; st.ai_wake=now+AI_DELAY_MS
                    if st.ai_pending and now>=st.ai_wake:
                        mv=ai_choose_move(st,cfg.difficulty)
                        if mv:
                            r,c=mv
                            if can_place(st,r,c):
                                st.board[r][c]="O"; st.last_move=(r,c)
                                if st.items_on and (r,c) not in st.item_spent_cells:
                                    it=roll_item(allow_double=True)
                                    if it:
                                        apply_item(st,"O",it,for_ai=True,origin=(r,c))
                                        st.item_spent_cells.add((r,c))
                                if st.double_stage==1:
                                    st.ai_second_pending=True; st.ai_second_wake=now+AI_DELAY_MS
                                else:
                                    if not finalize_and_maybe_end(st,"O"): end_turn(st)
                        st.ai_pending=False
                    # 두 번째 수 대기/실행
                    if st.ai_second_pending and now>=st.ai_second_wake:
                        r0,c0=st.last_move if st.last_move else (-1,-1)
                        adj=[(rr,cc) for rr,cc in neighbors4(st.N,r0,c0) if can_place(st,rr,cc)]
                        if adj:
                            rr,cc=random.choice(adj)
                            st.board[rr][cc]="O"; st.last_move=(rr,cc)
                            if st.items_on and (rr,cc) not in st.item_spent_cells:
                                it2=roll_item(allow_double=False)  # 2수째는 DOUBLE 금지
                                if it2:
                                    apply_item(st,"O",it2,for_ai=True,origin=(rr,cc))
                                    st.item_spent_cells.add((rr,cc))
                        else:
                            push_event(st,"O","🦘 인접 칸 없음 → 더블턴 무효",WARN)
                        st.double_stage=0
                        st.ai_second_pending=False
                        if not finalize_and_maybe_end(st,"O"): end_turn(st)

        # draw
        screen.fill(DARK_BG)
        pygame.draw.rect(screen,PANEL_BG,panel,border_radius=18)
        pygame.draw.rect(screen,BORDER,panel,1,border_radius=18)
        screen.blit(render_mix("틱택톡: 아이템 에디션",big=True,color=TEXT),(panel.x+20,panel.y+18))

        b_mode.draw(screen); b_diff.enabled=(b_mode.value=="AI"); b_diff.draw(screen)
        b_size.draw(screen); b_items.draw(screen)
        draw_item_legend(screen,panel)

        btn_start.draw(screen); btn_reset.draw(screen)

        draw_game(screen,st,cfg,board_area)
        draw_banner(screen,st,board_area)
        draw_toasts(screen,st)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit(); sys.exit(0)

if __name__=="__main__":
    main()
