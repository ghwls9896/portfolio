# =========================
# AI 플레이어 로직 (TicTacTok)
# =========================
"""
AI 플레이어:
- 즉시 이길 수 있는 수(즉승) 또는 상대방의 즉승을 막는 수(즉방어)
- 포크(fork) 생성: 다음 턴에 동시에 여러 승리 수를 만들기
- 맥스런/오픈런: 긴 연속줄을 만들고 양 끝이 열린 패턴을 선호
- 알파–베타 탐색(minimax)을 사용해 난이도별로 다른 깊이로 수를 계산
- Very Hard 난이도에서는 깊이를 더 깊게 탐색하고 루트 후보를 제한해 성능과 강도를 균형있게 유지
"""

import random                               # 무작위 선택을 위한 random 모듈
from typing import List, Tuple, Optional    # 타입 힌트용
from model import GameState                 # 게임 상태(보드, 턴, 잠금 등) 데이터 클래스
from rules import check_victory, neighbors4 # 승리 판정 함수와 상하좌우 이웃 좌표 반환 함수


# ------------------------------------
# 승리/방어용 빠른 수 탐지 함수들
# ------------------------------------

def find_winning_move(board, N, mark) -> Optional[Tuple[int,int]]:
    """
    현재 보드에서 'mark'(X 또는 O)를 한 번 두어 바로 승리할 수 있는 좌표를 찾는다.
    """
    for r in range(N):                       # 모든 행을 탐색
        for c in range(N):                   # 모든 열을 탐색
            if board[r][c] == "":            # 빈 칸만 시도
                board[r][c] = mark           # 가상의 수를 둠
                w, _ = check_victory(board, N, mark)  # 승리 여부 확인
                board[r][c] = ""             # 돌을 다시 지움
                if w:                        # 승리 가능하면
                    return (r, c)            # 해당 좌표 반환
    return None                              # 없으면 None


def count_next_wins(board, N, mark) -> int:
    """
    현재 판에서 'mark'를 한 수 둔 후 바로 이길 수 있는 칸의 개수를 센다.
    (포크: 동시에 여러 승리 수를 만들 수 있는지 확인)
    """
    cnt = 0
    for r in range(N):                       # 모든 칸 탐색
        for c in range(N):
            if board[r][c] == "":            # 빈 칸만 시도
                board[r][c] = mark           # 임시로 둠
                w, _ = check_victory(board, N, mark)  # 이기는지 확인
                board[r][c] = ""             # 복구
                if w:                        # 승리 가능
                    cnt += 1
    return cnt                               # 가능한 승리 수 개수 반환


# ------------------------------------
# 라인(연속) 분석 함수
# ------------------------------------

def line_info_after(board, N, r, c, mark):
    """
    (r,c)에 mark를 두었을 때:
    - max_len: 가장 긴 연속 돌 길이
    - open_bonus: 양쪽이 모두 열려 있으면 추가 보너스
    """
    dirs = [(0,1), (1,0), (1,1), (1,-1)]     # 가로, 세로, 대각, 역대각
    max_len = 0                             # 최대 연속 길이
    open_bonus = 0                          # 오픈런 보너스
    for dr, dc in dirs:                     # 각 방향 탐색
        cnt = 1                             # 자기 자신 포함
        rr, cc = r+dr, c+dc
        while 0 <= rr < N and 0 <= cc < N and board[rr][cc] == mark:
            cnt += 1                        # 같은 돌이면 카운트
            rr += dr; cc += dc
        end1 = (0 <= rr < N and 0 <= cc < N and board[rr][cc] == "") # 한쪽 끝 비어있는지

        rr, cc = r-dr, c-dc
        while 0 <= rr < N and 0 <= cc < N and board[rr][cc] == mark:
            cnt += 1
            rr -= dr; cc -= dc
        end2 = (0 <= rr < N and 0 <= cc < N and board[rr][cc] == "") # 반대쪽 끝 비어있는지

        max_len = max(max_len, cnt)         # 가장 긴 연속 길이 갱신
        if end1 and end2:                   # 양쪽 다 열려있으면
            open_bonus += 1                 # 보너스 +1
    return max_len, open_bonus              # 결과 반환


# ------------------------------------
# 휴리스틱 평가 함수
# ------------------------------------

def heuristic_score(board, N, mark):
    """
    현재 보드 상태를 점수로 평가:
    - 중앙에 가까울수록 가점
    - 돌끼리 붙어 있으면 가점
    - 한 줄 내 돌 개수에 따라 점수 추가
    - 상대방의 위협은 감점
    """
    dirs = [(0,1), (1,0), (1,1), (1,-1)]     # 4방향
    opp = "O" if mark == "X" else "X"       # 상대 마크
    score = 0
    cx = (N-1)/2; cy = (N-1)/2              # 중앙 좌표

    # --- 위치 기반 + 인접 돌 가점 ---
    for r in range(N):
        for c in range(N):
            if board[r][c] == mark:         # 내 돌일 때
                score += 1.5 - (abs(r-cx) + abs(c-cy)) * 0.08 # 중앙에서 멀면 감점
                for rr, cc in neighbors4(N, r, c):
                    if board[rr][cc] == mark:  # 이웃에 같은 돌 있으면
                        score += 0.25

    # --- 한 줄(승리 가능성) 평가 ---
    for r in range(N):
        for c in range(N):
            for dr, dc in dirs:
                cells = []                  # 해당 방향으로 N칸 수집
                rr, cc = r, c
                for _ in range(N):
                    if not (0 <= rr < N and 0 <= cc < N):
                        cells = []
                        break
                    cells.append(board[rr][cc])
                    rr += dr; cc += dc
                if len(cells) < N:
                    continue

                if opp not in cells:        # 상대 돌이 없으면 내 점수
                    k = cells.count(mark)
                    if k == N: score += 30000
                    elif k == N-1: score += 800
                    elif k == N-2: score += 120
                    elif k == 1: score += 8

                if mark not in cells:       # 내 돌이 없으면 상대 점수(감점)
                    k2 = cells.count(opp)
                    if k2 == N-1: score -= 760
                    elif k2 == N-2: score -= 110
    return score                            # 최종 점수 반환


# ------------------------------------
# 상태 키(트랜스포지션 테이블용)
# ------------------------------------

def board_key(board):
    """현재 보드를 튜플로 변환해 해시 가능하게 만듦 (메모이제이션 키)"""
    return tuple(tuple(row) for row in board)


# ------------------------------------
# 수 정렬 함수 (좋은 수를 먼저 탐색)
# ------------------------------------

def order_moves(state: GameState, me: str, moves: List[Tuple[int,int]]) -> List[Tuple[int,int]]:
    """
    가능한 수를 점수화해 정렬:
    - 승리 수 > 포크 > 연속/오픈런 > 중앙 근처 > 방어 수
    """
    N = state.N
    opp = "O" if me == "X" else "X"
    cx = (N-1)/2; cy = (N-1)/2
    scored = []

    for r, c in moves:
        s = 0.0
        s -= (abs(r-cx) + abs(c-cy)) * 0.08      # 중앙에 가까울수록 점수↑

        state.board[r][c] = me
        win, _ = check_victory(state.board, N, me)
        if win: s += 50000                      # 즉승이면 큰 가점
        ml, ob = line_info_after(state.board, N, r, c, me)
        s += ml * 350 + ob * 180                # 연속 길이와 오픈런 가점
        wins_next = count_next_wins(state.board, N, me)
        s += wins_next * 900                    # 포크 가능성 가점
        opp_wins = count_next_wins(state.board, N, opp)
        s -= opp_wins * 700                     # 상대 위협 커지면 감점
        state.board[r][c] = ""

        state.board[r][c] = opp                 # 상대 돌을 두어
        opp_now, _ = check_victory(state.board, N, opp)
        state.board[r][c] = ""
        if opp_now: s += 4000                   # 상대 즉승 막는 수면 가점

        scored.append(((r, c), s))              # (좌표, 점수) 저장

    scored.sort(key=lambda x: x[1], reverse=True) # 점수 내림차순
    return [p for p, _ in scored]               # 좌표 리스트만 반환


# ------------------------------------
# Minimax + 알파베타 가지치기
# ------------------------------------

def minimax(state: GameState, me: str, depth: int, alpha: float, beta: float, maximizing: bool):
    """
    미니맥스 탐색:
    - maximizing=True : 내 차례 (점수 최대화)
    - maximizing=False: 상대 차례 (점수 최소화)
    - alpha/beta : 가지치기 경계
    - state.tt : 계산된 상태 저장(속도 향상)
    """
    N = state.N
    board = state.board
    opp = "O" if me == "X" else "X"
    k = (board_key(board), depth, maximizing)    # 캐시 키
    if k in state.tt:
        return state.tt[k]                       # 이미 계산된 상태면 반환

    w, _ = check_victory(board, N, me)
    if w: return (30000, None)                   # 내가 이겼으면 큰 점수
    w2, _ = check_victory(board, N, opp)
    if w2: return (-30000, None)                 # 상대가 이겼으면 큰 감점

    from rules import board_full
    if depth == 0 or board_full(board):          # 깊이 다 탐색했거나 무승부
        val = heuristic_score(board, N, me) - heuristic_score(board, N, opp)
        state.tt[k] = (val, None)
        return val, None

    legal = [(r,c) for r in range(N) for c in range(N)
             if board[r][c] == "" and (r,c) not in state.locks]
    if not legal:                                # 둘 곳이 없으면 점수만 반환
        val = heuristic_score(board, N, me) - heuristic_score(board, N, opp)
        state.tt[k] = (val, None)
        return val, None

    legal = order_moves(state, me if maximizing else opp, legal) # 좋은 수 먼저 탐색
    best = None

    if maximizing:                               # 내 차례
        val = -1e18
        for r, c in legal:
            board[r][c] = me
            v, _ = minimax(state, me, depth-1, alpha, beta, False)
            board[r][c] = ""
            if v > val:
                val = v; best = (r, c)
            alpha = max(alpha, v)
            if beta <= alpha: break              # 가지치기
    else:                                        # 상대 차례
        val = 1e18
        for r, c in legal:
            board[r][c] = opp
            v, _ = minimax(state, me, depth-1, alpha, beta, True)
            board[r][c] = ""
            if v < val:
                val = v; best = (r, c)
            beta = min(beta, v)
            if beta <= alpha: break              # 가지치기

    state.tt[k] = (val, best)
    return val, best


# ------------------------------------
# 최종 수 선택 함수
# ------------------------------------

def choose_move(state: GameState, difficulty: str) -> Optional[Tuple[int,int]]:
    """
    난이도별 AI 수 선택:
    1) 즉승 → 2) 즉방어 → 3) 포크 → 4) 미니맥스 탐색
    """
    N = state.N
    me = state.turn
    opp = "O" if me == "X" else "X"

    legal = [(r,c) for r in range(N) for c in range(N)
             if state.board[r][c] == "" and (r,c) not in state.locks]
    if not legal: return None                   # 둘 곳 없으면 None

    mv = find_winning_move(state.board, N, me)  # 즉승
    if mv: return mv

    bm = find_winning_move(state.board, N, opp) # 즉방어
    if bm: return bm

    forks = []                                  # 포크 수집
    for (r, c) in legal:
        state.board[r][c] = me
        wins_next = count_next_wins(state.board, N, me)
        state.board[r][c] = ""
        if wins_next >= 2:
            forks.append((r, c))
    if forks:                                   # 포크가 있으면
        ordered = order_moves(state, me, forks)
        return ordered[0]

    depth_map = {                               # 난이도별 탐색 깊이 설정
        "Easy":      {3:2, 4:2, 5:1, 6:1},
        "Medium":    {3:4, 4:3, 5:2, 6:2},
        "Hard":      {3:7, 4:5, 5:3, 6:3},
        "Very Hard": {3:9, 4:7, 5:5, 6:5}
    }
    d = depth_map[difficulty].get(N, 3)         # 기본 깊이 결정
    state.tt.clear()                            # 캐시 초기화

    ordered = order_moves(state, me, legal)     # 수 정렬
    root = ordered[:min(len(ordered),
                        8 if difficulty in ("Hard","Very Hard") else 5)] # 상위 후보만 탐색

    best = None
    best_val = -1e18
    for (r, c) in root:
        state.board[r][c] = me
        v, _ = minimax(state, me, d-1, -1e18, 1e18, False) # 미니맥스 탐색
        state.board[r][c] = ""

        ml, ob = line_info_after(state.board, N, r, c, me) # 연속/오픈런 보너스
        wins_next = count_next_wins(state.board, N, me)
        v += ml*120 + ob*80 + wins_next*500

        if v > best_val:                        # 최고 점수 갱신
            best_val = v
            best = (r, c)

    return best or ordered[0]                   # 최종 선택 수 반환
