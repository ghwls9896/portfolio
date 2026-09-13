# -*- coding: utf-8 -*-
"""
텍스트 기반 '미로 탈출' 게임 (가독성 강화 버전)
- 완전미로(Perfect Maze) 생성: 입구~출구 경로는 항상 1개
- 입구/출구 무작위 배치(너무 가까우면 재배치)
- W/A/S/D 이동, Q 종료
- 실시간 화면 갱신 + S(입구), E(출구), P(플레이어) 표시
- 지나온 길 '·' 표시(옵션)

권장 터미널: 한 줄 폭 100+ (가독성)
"""

import os
import random
from collections import deque
from typing import List, Tuple, Set

# ====== 설정값 ======
CELL_H: int = 15         # 셀 높이(통로 셀 수) — 실제 출력 격자는 2*H+1
CELL_W: int = 25         # 셀 너비(통로 셀 수)
MIN_DIST_FACTOR: float = 0.6  # 입구~출구 최소 거리 비율 (0~1, 클수록 멀게)
SHOW_BREADCRUMB: bool = True  # 지나온 길에 '·' 찍기
# ====================


# ─────────────────────────────────────────────────────────
# 유틸
# ─────────────────────────────────────────────────────────
def clear_screen() -> None:
    """콘솔 지우기(윈도우/리눅스/맥 호환)."""
    os.system("cls" if os.name == "nt" else "clear")


def in_bounds(r: int, c: int, h: int, w: int) -> bool:
    return 0 <= r < h and 0 <= c < w


# ─────────────────────────────────────────────────────────
# 미로 생성(셀 단위) : 완전미로 (DFS)
# ─────────────────────────────────────────────────────────
DIRS: List[Tuple[int, int]] = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # 상하좌우

def generate_perfect_maze(h: int, w: int) -> List[List[Set[Tuple[int, int]]]]:
    """
    셀 단위 h x w 완전미로 생성.
    반환: 각 셀(r,c)에서 연결된 이웃 셀 좌표 집합의 2D 리스트.
    """
    visited = [[False] * w for _ in range(h)]
    links: List[List[Set[Tuple[int, int]]]] = [[set() for _ in range(w)] for _ in range(h)]

    def dfs(r: int, c: int) -> None:
        visited[r][c] = True
        dirs = DIRS[:]
        random.shuffle(dirs)
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc, h, w) and not visited[nr][nc]:
                # 양방향 연결
                links[r][c].add((nr, nc))
                links[nr][nc].add((r, c))
                dfs(nr, nc)

    # 임의의 시작점에서 DFS
    sr, sc = random.randrange(h), random.randrange(w)
    dfs(sr, sc)
    return links


def cells_to_grid(links: List[List[Set[Tuple[int, int]]]]) -> List[List[str]]:
    """
    '셀' 미로를 화면 출력용 '격자'로 변환.
    - 격자 크기: (2*h+1) x (2*w+1)
    - '#'=벽, ' '=통로
    """
    h, w = len(links), len(links[0])
    gh, gw = 2 * h + 1, 2 * w + 1
    grid = [['#'] * gw for _ in range(gh)]

    for r in range(h):
        for c in range(w):
            gr, gc = 2 * r + 1, 2 * c + 1
            grid[gr][gc] = ' '  # 셀 중심
            for nr, nc in links[r][c]:
                ngr, ngc = 2 * nr + 1, 2 * nc + 1
                # 통로 뚫기(두 중심 사이)
                grid[(gr + ngr) // 2][(gc + ngc) // 2] = ' '
    return grid


# ─────────────────────────────────────────────────────────
# 입구/출구 배치 및 거리 계산
# ─────────────────────────────────────────────────────────
def boundary_cells(h: int, w: int) -> List[Tuple[int, int]]:
    """가장자리(경계)에 위치한 셀 좌표 목록."""
    cells: List[Tuple[int, int]] = []
    for c in range(w):
        cells.append((0, c))
        cells.append((h - 1, c))
    for r in range(1, h - 1):
        cells.append((r, 0))
        cells.append((r, w - 1))
    return cells


def bfs_distance(links, start: Tuple[int, int]) -> List[List[int]]:
    """셀 단위 BFS 거리 테이블."""
    h, w = len(links), len(links[0])
    dist = [[-1] * w for _ in range(h)]
    q = deque([start])
    dist[start[0]][start[1]] = 0

    while q:
        r, c = q.popleft()
        for nr, nc in links[r][c]:
            if dist[nr][nc] == -1:
                dist[nr][nc] = dist[r][c] + 1
                q.append((nr, nc))
    return dist


def carve_gate(grid: List[List[str]], cell: Tuple[int, int], h: int, w: int) -> Tuple[int, int]:
    """
    셀 좌표를 실제 격자 가장자리로 뚫어 입구/출구를 만든다.
    반환: 통로 안쪽의 최초 플레이어가 설 수 있는 위치(행,열)
    """
    r, c = cell
    gr, gc = 2 * r + 1, 2 * c + 1
    gh, gw = len(grid), len(grid[0])

    if r == 0:             # 위쪽
        grid[0][gc] = ' '
        return (1, gc)
    if r == h - 1:         # 아래쪽
        grid[gh - 1][gc] = ' '
        return (gh - 2, gc)
    if c == 0:             # 왼쪽
        grid[gr][0] = ' '
        return (gr, 1)
    if c == w - 1:         # 오른쪽
        grid[gr][gw - 1] = ' '
        return (gr, gw - 2)

    # 이론적으로 도달하지 않음(경계만 줌)
    return (gr, gc)


def choose_start_end(links, grid) -> Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int], Tuple[int, int]]:
    """
    입구/출구를 경계 셀에서 랜덤 선정(너무 가까우면 재선정).
    반환: (start_cell, end_cell, start_pos_in_grid, end_pos_in_grid)
    """
    h, w = len(links), len(links[0])
    bnd = boundary_cells(h, w)

    # 시작 경계 셀 랜덤
    start_cell = random.choice(bnd)

    # 시작에서의 거리 계산
    dist = bfs_distance(links, start_cell)

    # 최소 거리(셀 거리 기준)
    min_required = int((h + w) * MIN_DIST_FACTOR / 2)
    far_candidates = [
        cell for cell in bnd
        if dist[cell[0]][cell[1]] >= max(1, min_required)
    ]

    if not far_candidates:
        # 너무 작거나 조건이 빡세면 가장 먼 후보들 중에서
        maxd = max(dist[r][c] for r, c in bnd)
        far_candidates = [cell for cell in bnd if dist[cell[0]][cell[1]] == maxd]

    end_cell = random.choice(far_candidates)

    # 실제 격자에 입구/출구 뚫고, 입·출구 안쪽 좌표 반환
    start_pos = carve_gate(grid, start_cell, h, w)
    end_pos = carve_gate(grid, end_cell, h, w)
    return start_cell, end_cell, start_pos, end_pos


# ─────────────────────────────────────────────────────────
# 렌더링
# ─────────────────────────────────────────────────────────
def render(grid: List[List[str]],
           player: Tuple[int, int],
           start_pos: Tuple[int, int],
           end_pos: Tuple[int, int],
           steps: int) -> None:
    """현재 상태를 화면에 출력."""
    gh, gw = len(grid), len(grid[0])

    # 상단 정보 바
    print("=== 미로 탈출 (W/A/S/D 이동, Q 종료) ===")
    print(f"좌표: P={player}, S={start_pos}, E={end_pos} | 이동 횟수: {steps}")
    print("-" * gw)

    # 본문 미로
    for r in range(gh):
        row_chars: List[str] = []
        for c in range(gw):
            ch = grid[r][c]
            if (r, c) == player:
                row_chars.append('P')
            elif (r, c) == start_pos:
                row_chars.append('S')
            elif (r, c) == end_pos:
                row_chars.append('E')
            else:
                row_chars.append(ch)
        print("".join(row_chars))


# ─────────────────────────────────────────────────────────
# 메인 루프
# ─────────────────────────────────────────────────────────
def main() -> None:
    # 1) 미로 생성(완전미로)
    links = generate_perfect_maze(CELL_H, CELL_W)
    grid = cells_to_grid(links)

    # 2) 입구/출구 배치(랜덤 & 충분히 멀게)
    _, _, start_pos, end_pos = choose_start_end(links, grid)

    # 3) 플레이 시작
    player = start_pos
    steps = 0

    clear_screen()
    render(grid, player, start_pos, end_pos, steps)

    while True:
        move = input("\n이동(W/A/S/D), 종료(Q): ").strip().lower()
        if not move:
            clear_screen()
            render(grid, player, start_pos, end_pos, steps)
            continue

        cmd = move[0]
        if cmd == 'q':
            clear_screen()
            print("게임을 종료합니다. 👋")
            return

        # 방향 해석
        dr = dc = 0
        if cmd == 'w':
            dr = -1
        elif cmd == 's':
            dr = 1
        elif cmd == 'a':
            dc = -1
        elif cmd == 'd':
            dc = 1
        else:
            clear_screen()
            render(grid, player, start_pos, end_pos, steps)
            print("\nW/A/S/D 또는 Q만 입력하세요.")
            continue

        # 이동 시도
        nr, nc = player[0] + dr, player[1] + dc
        if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and grid[nr][nc] != '#':
            if SHOW_BREADCRUMB and (nr, nc) != end_pos and (nr, nc) != start_pos:
                # 지나온 자리 표시
                grid[player[0]][player[1]] = '·' if grid[player[0]][player[1]] == ' ' else grid[player[0]][player[1]]
            player = (nr, nc)
            steps += 1
        # 벽이면 무시

        clear_screen()
        render(grid, player, start_pos, end_pos, steps)

        # 도착 체크
        if player == end_pos:
            print("\n🎉 축하합니다! 출구(E)에 도착했습니다!")
            print(f"총 이동 횟수: {steps}")
            break


if __name__ == "__main__":
    main()
