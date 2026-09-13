# =============================
# 규칙/판정/좌표 유틸 모듈
# =============================
"""
- N개 연속으로 놓였을 때 승리 판정
- 이웃 좌표 계산
- 보드 안/밖 판정
- 보드가 꽉 찼는지 확인
"""

from typing import List, Tuple

# ------------------------------
# 좌표 유틸
# ------------------------------

def in_bounds(N, r, c) -> bool:
    """좌표 (r,c)가 보드 범위(0~N-1) 안에 있는지 확인"""
    return 0 <= r < N and 0 <= c < N


def neighbors4(N, r, c):
    """
    (r,c)에서 상하좌우 4방향 이웃 좌표를 구한다.
    단, 보드 안에 있는 좌표만 yield(반환).
    """
    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:  # 위, 아래, 왼쪽, 오른쪽
        rr, cc = r + dr, c + dc
        if in_bounds(N, rr, cc):   # 보드 안이면
            yield rr, cc           # 이웃 좌표 반환


# ------------------------------
# 승리 판정
# ------------------------------

def check_victory(board: List[List[str]], N: int, mark: str) -> Tuple[bool, list]:
    """
    주어진 보드에서 mark(X 또는 O)가 정확히 N개 연속으로 놓였는지 판정한다.
    - 수평, 수직, 대각선, 역대각선 모두 검사
    - "정확히 N개" 연속만 인정 (N+1 이상은 무효)
    반환: (승리여부, 승리좌표리스트)
    """
    dirs = [(0,1), (1,0), (1,1), (1,-1)]  # 가로, 세로, 대각, 역대각 방향

    for r in range(N):            # 모든 행 탐색
        for c in range(N):        # 모든 열 탐색
            if board[r][c] != mark:   # 내가 놓은 돌이 아니면 건너뜀
                continue
            for dr, dc in dirs:       # 4방향 검사
                # (r,c) 이전 방향에 같은 돌이 있으면 시작점이 아님 → 무시
                pr, pc = r - dr, c - dc
                if in_bounds(N, pr, pc) and board[pr][pc] == mark:
                    continue

                # 연속 개수 세기
                cnt = 0
                rr, cc = r, c
                while in_bounds(N, rr, cc) and board[rr][cc] == mark:
                    cnt += 1
                    if cnt == N:
                        # N개 연속 달성 → 승리
                        return True, [(r + i*dr, c + i*dc) for i in range(N)]
                    rr += dr; cc += dc

    # 끝까지 돌았는데도 없으면 승리 아님
    return False, []


# ------------------------------
# 보드 꽉 참 여부
# ------------------------------

def board_full(board: List[List[str]]) -> bool:
    """
    보드에 빈칸("")이 하나라도 없으면 True → 꽉 찬 상태.
    """
    N = len(board)
    return all(board[r][c] != "" for r in range(N) for c in range(N))
