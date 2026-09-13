# tictactok/items.py
"""
아이템 관리:
- 스폰 확률/가중치에 따라 아이템 롤
- 각 아이템의 즉발 효과 적용
- LOCK/SWAP 타깃 선택 흐름 제어
- “셀 1회 소모” 규칙(한 칸에서 아이템 한 번만) 지원
"""

import random
from typing import Optional, Tuple
from config import ITEM_SPAWN_RATE, ITEM_WEIGHTS, MAX_SHIELD, LOCK_DURATION, LOCK_COL, GOOD, WARN, BAD, SUBTLE, ACCENT
from rules import neighbors4
from model import GameState

def push_event(state: GameState, actor, msg, color):
    """토스트/배너 기록 (클릭 시 일괄 숨김)."""
    state.toasts.append((actor, msg, 999999, color))
    state.last_banner = (actor, msg, color)

def roll_item(allow_double: bool = True) -> Optional[str]:
    """ITEM_SPAWN_RATE와 가중치로 아이템 한 개를 뽑는다. (allow_double=False면 DOUBLE=0)"""
    if random.random() >= ITEM_SPAWN_RATE:
        return None
    weights = ITEM_WEIGHTS.copy()
    if not allow_double and "DOUBLE" in weights:
        weights["DOUBLE"] = 0.0
    total = sum(weights.values())
    if total <= 0:
        return None
    x = random.random() * total
    acc = 0.0
    for k, w in weights.items():
        acc += w
        if x <= acc:
            return k
    return None

def choose_lock_target_ai(state: GameState) -> Optional[Tuple[int, int]]:
    """AI용 락 타깃: 상대 즉승 차단 우선, 없으면 랜덤."""
    opp = "O" if state.turn == "X" else "X"
    from rules import check_victory
    # 즉승 차단
    for r in range(state.N):
        for c in range(state.N):
            if state.board[r][c] == "" and (r, c) not in state.locks:
                state.board[r][c] = opp
                w, _ = check_victory(state.board, state.N, opp)
                state.board[r][c] = ""
                if w:
                    return (r, c)
    # 랜덤
    empties = [(r, c) for r in range(state.N) for c in range(state.N) if state.board[r][c] == "" and (r, c) not in state.locks]
    return random.choice(empties) if empties else None

def do_ai_swap(state: GameState, owner: str):
    """AI 스왑: 단순 휴리스틱(무작위). 필요 시 강화 가능."""
    opp = "O" if owner == "X" else "X"
    my = [(r, c) for r in range(state.N) for c in range(state.N) if state.board[r][c] == owner]
    op = [(r, c) for r in range(state.N) for c in range(state.N) if state.board[r][c] == opp]
    if not my or not op:
        push_event(state, owner, "♻️ 스왑 타깃 없음", SUBTLE); return
    a = random.choice(my); b = random.choice(op)
    ra, ca = a; rb, cb = b
    state.board[ra][ca], state.board[rb][cb] = state.board[rb][cb], state.board[ra][ca]
    push_event(state, owner, f"♻️ 스왑: {a} ↔ {b}", ACCENT)

def apply_item(state: GameState, owner: str, item: str, for_ai: bool, origin: Tuple[int, int]):
    """
    단일 아이템 즉발 처리.
    - DOUBLE은 첫 수에서만 유효 (double_stage==0 → 1)
    - LOCK/SWAP은 타깃 선택 모드 진입(사람), AI는 자동 타깃
    - BOMB은 중심+십자 초기화 (락은 유지)
    - SHIELD는 패시브 스택(+1, 최대 2)
    - CUFF는 상대 턴 스킵(상대 방패가 있으면 차감 후 무효)
    """
    opp = "O" if owner == "X" else "X"

    if item == "SHIELD":
        from config import MAX_SHIELD
        if state.shield[owner] < MAX_SHIELD:
            state.shield[owner] += 1
        push_event(state, owner, f"🛡️ 방패 +1 (현재 {state.shield[owner]}/{MAX_SHIELD})", GOOD)

    elif item == "CUFF":
        if state.shield[opp] > 0:
            state.shield[opp] -= 1
            push_event(state, owner, f"🛡️ {opp}의 방패가 수갑을 막음 (잔여 {state.shield[opp]})", WARN)
        else:
            state.skip_next[opp] = True
            push_event(state, owner, f"🔗 수갑! {opp}의 다음 턴 스킵", BAD)

    elif item == "DOUBLE":
        if state.double_stage == 0:
            state.double_stage = 1
            push_event(state, owner, "🦘 더블턴! 인접 칸에 한 번 더", ACCENT)
        else:
            # 2수째에는 금지되어 들어오지 않지만 안전 메시지
            push_event(state, owner, "🦘 더블턴은 2수째에는 무효", SUBTLE)

    elif item == "LOCK":
        if for_ai:
            t = choose_lock_target_ai(state)
            if t:
                state.locks[t] = LOCK_DURATION
                push_event(state, owner, f"🔒 잠금 {t} ({LOCK_DURATION}턴)", LOCK_COL)
            else:
                push_event(state, owner, "🔒 잠글 칸 없음", SUBTLE)
        else:
            # 빈칸이 0개면 대기하지 않음
            targets = [(r, c) for r in range(state.N) for c in range(state.N) if state.board[r][c]=="" and (r,c) not in state.locks]
            if not targets:
                push_event(state, owner, "🔒 잠글 칸 없음", SUBTLE)
            else:
                push_event(state, owner, "🔒 잠글 빈 칸을 선택하세요", ACCENT)
                state.pending = ("LOCK", owner)

    elif item == "BOMB":
        if origin:
            r, c = origin
            affected = {(r, c), *set(neighbors4(state.N, r, c))}
            for rr, cc in affected:
                state.board[rr][cc] = ""   # 락은 유지
            push_event(state, owner, f"💣 폭탄! 십자 {len(affected)}칸 초기화", BAD)
        else:
            push_event(state, owner, "💣 폭탄 발동 위치 없음", SUBTLE)

    elif item == "SWAP":
        my_has  = any(state.board[r][c]==owner for r in range(state.N) for c in range(state.N))
        opp_has = any(state.board[r][c]==opp   for r in range(state.N) for c in range(state.N))
        if not my_has or not opp_has:
            push_event(state, owner, "♻️ 스왑 타깃 없음 → 아이템 무효", SUBTLE)
            return
        if state.shield[opp] > 0:
            state.shield[opp] -= 1
            push_event(state, owner, f"🛡️ {opp}의 방패가 스왑을 막음 (잔여 {state.shield[opp]})", WARN)
            return
        if for_ai:
            do_ai_swap(state, owner)
        else:
            push_event(state, owner, "♻️ 스왑: 내 돌 → 상대 돌 순서로 선택", ACCENT)
            state.pending = ("SWAP_MY", owner)
