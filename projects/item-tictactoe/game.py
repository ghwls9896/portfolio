# ===============================
# 게임 엔트리포인트 & 컨트롤러
# ===============================
"""
엔트리포인트 & 게임 컨트롤러
- 이벤트 루프, 입력 처리, 턴 전환, AI 딜레이 실행
- LOCK/SWAP 타깃 중에는 턴 정지
- 토스트/배너: 클릭 시 일괄 숨김(새 메시지는 정상 표시)
"""

import sys, pygame, random  # 표준 종료(sys), 게임 프레임워크(pygame), 무작위 선택(random)
from typing import Optional, Tuple  # 타입 힌트용(선택적/튜플)
from config import *  # 화면/색/아이템 확률 등 전역 상수 로드
from model import Config, GameState  # 설정/게임상태 데이터 클래스 로드
from rules import in_bounds, neighbors4, check_victory, board_full  # 규칙(좌표/승리/가득참) 함수들
from items import roll_item, apply_item, push_event  # 아이템 뽑기/적용/이벤트 푸시
from ai import choose_move  # AI 수 선택 함수
from ui import init_fonts, render_mix, Button, draw_item_legend, draw_game, draw_toasts, draw_banner, point_to_cell
# 폰트 초기화, 텍스트 렌더, UI 버튼, 아이템 설명, 보드/토스트/배너 그리기, 좌표 변환

def can_place(state: GameState, r: int, c: int) -> bool:
    return in_bounds(state.N, r, c) and state.board[r][c]=="" and (r,c) not in state.locks
    # 착수 가능 조건: 보드 안 + 빈칸 + 잠금 아님

def finalize_and_maybe_end(state: GameState, player: str) -> bool:
    w, cells = check_victory(state.board, state.N, player)  # 방금 둔 플레이어 승리 여부 확인
    if w:
        state.winner = player  # 승자 기록
        state.winning_cells = cells  # 승리 라인 좌표 저장(하이라이트용)
        state.game_over = True  # 게임 종료 플래그
        push_event(state, player, f"🏆 {player} 승리!", GOOD); return True  # 축하 토스트 띄우고 종료 알림
    if board_full(state.board):  # 보드가 꽉 찼다면
        state.game_over = True  # 게임 종료
        push_event(state, None, "🤝 무승부!", SUBTLE); return True  # 무승부 토스트
    return False  # 계속 진행

def end_turn(state: GameState):
    expired=[]  # 이번 턴 종료로 만료되는 잠금 칸 모음
    for pos,t in list(state.locks.items()):  # 모든 잠금 칸에 대해
        nt=t-1  # 지속 턴수 감소
        if nt<=0: expired.append(pos)  # 0 이하면 만료 목록에
        else: state.locks[pos]=nt  # 아니면 갱신
    for pos in expired: del state.locks[pos]  # 만료 잠금 제거
    state.turn = "O" if state.turn=="X" else "X"  # 턴 교대

def handle_click(state: GameState, cfg: Config, pos, board_area: pygame.Rect):
    if state.game_over: return  # 이미 끝났으면 무시

    # 스킵
    if state.skip_next[state.turn]:  # 수갑 효과로 현재 플레이어 스킵?
        state.skip_next[state.turn] = False  # 스킵 플래그 해제(1회성)
        push_event(state, state.turn, f"🔗 {state.turn} 턴 스킵", WARN)  # 알림
        end_turn(state); return  # 즉시 턴 넘김

    cell = point_to_cell(pos, state.N, board_area)  # 클릭 위치 → 보드 좌표 변환
    if cell is None: return  # 보드 바깥 클릭이면 무시
    r, c = cell  # 변환된 행/열

    # ── ① 타깃 선택 우선 (LOCK/SWAP)
    if state.pending:  # 아이템 타깃 지정 대기 상태인가?
        kind, owner = state.pending[0], state.pending[1]  # 대기 중 종류/아이템 소유자
        opp = "O" if owner=="X" else "X"  # 상대 마크
        if owner != state.turn: return  # 내 차례가 아니면 입력 무시(동기화)

        if kind=="LOCK":  # 잠금 선택 모드
            if can_place(state, r, c):  # 빈칸만 잠금 가능
                state.locks[(r,c)] = LOCK_DURATION  # 잠금 지속 설정
                push_event(state, owner, f"🔒 잠금 {(r,c)} ({LOCK_DURATION}턴)", LOCK_COL)  # 알림
                state.pending = None  # 타깃 선택 종료
                if state.double_stage==0:  # 더블턴 대기 아니면
                    if not finalize_and_maybe_end(state, owner): end_turn(state)  # 판정 후 턴 넘김
            else:
                push_event(state, owner, "🔒 빈 칸만 가능", WARN)  # 잘못된 대상 안내
            return  # LOCK 처리 끝

        if kind=="SWAP_MY":  # 스왑: 내 돌 먼저 선택 단계
            # 상대 돌 존재 재확인(없으면 무효)
            if not any(state.board[rr][cc]==opp for rr in range(state.N) for cc in range(state.N)):
                state.pending=None  # 대기 취소
                push_event(state, owner, "♻️ 상대 돌이 없어 스왑 취소", SUBTLE)  # 안내
                if state.double_stage==0:
                    if not finalize_and_maybe_end(state, owner): end_turn(state)
                return
            if state.board[r][c]==owner:  # 내 돌을 선택했다면
                state.pending=("SWAP_OPP", owner, (r,c))  # 다음 단계: 상대 돌 선택
                push_event(state, owner, "♻️ 상대 돌을 선택하세요", ACCENT)  # 가이드
            else:
                push_event(state, owner, "♻️ 내 돌부터 선택", WARN)  # 순서 안내
            return

        if kind=="SWAP_OPP":  # 스왑: 상대 돌 선택 단계
            myrc = state.pending[2]  # 방금 선택한 내 돌 좌표
            if not any(state.board[rr][cc]==opp for rr in range(state.N) for cc in range(state.N)):
                state.pending=None  # 상대 돌이 사라졌으면 취소
                push_event(state, owner, "♻️ 상대 돌이 없어 스왑 취소", SUBTLE)
                if state.double_stage==0:
                    if not finalize_and_maybe_end(state, owner): end_turn(state)
                return
            if state.board[r][c]==opp:  # 진짜 상대 돌을 찍었으면
                ra,ca = myrc; rb,cb = r,c  # 내/상대 좌표 분해
                state.board[ra][ca], state.board[rb][cb] = state.board[rb][cb], state.board[ra][ca]  # 자리 교환
                push_event(state, owner, f"♻️ 스왑: {myrc} ↔ {(r,c)}", ACCENT)  # 알림
                state.pending=None  # 대기 종료
                if state.double_stage==0:
                    if not finalize_and_maybe_end(state, owner): end_turn(state)
            else:
                push_event(state, owner, "♻️ 상대 돌을 선택", WARN)  # 잘못된 타깃
            return  # SWAP 처리 끝

    # ── ② 정상 착수
    if not can_place(state, r, c):  # 빈칸/미잠금/인바운드 아닐 때
        push_event(state, state.turn, "🚫 둘 수 없는 칸(잠금/점유)", BAD); return  # 안내 후 무시

    is_second = (state.double_stage==1 and state.last_move is not None and (r,c) in set(neighbors4(state.N, *state.last_move)))
    # 더블턴 2수째인지: 직전 착수의 4방 이웃만 허용되는지 확인
    if state.double_stage==1 and not is_second:
        push_event(state, state.turn, "🦘 인접 칸만 가능합니다", WARN); return  # 범위 위반 안내

    me = state.turn  # 현재 플레이어
    state.board[r][c] = me  # 돌 놓기
    state.last_move = (r, c)  # 마지막 수 갱신

    # ── ③ 아이템 스폰/적용 (“셀 1회 소모”, 2수째는 DOUBLE 금지)
    if state.items_on and (r,c) not in state.item_spent_cells:  # 해당 셀에서 아직 아이템 한 번도 안썼으면
        it = roll_item(allow_double=not is_second)  # 2수째면 DOUBLE 비허용
        if it:
            apply_item(state, me, it, for_ai=False, origin=(r,c))  # 아이템 효과 즉시 적용
            state.item_spent_cells.add((r,c))  # 이 셀은 아이템 소모 처리(재스폰 방지)
            if state.pending:  # LOCK/SWAP 타깃 대기 상태면(턴 유지)
                return  # 타깃 선택 끝나고 나서 계속

    # ── ④ 더블턴 처리
    if is_second:  # 2수째 착수였다면
        state.double_stage = 0  # 더블 모드 종료
        if not finalize_and_maybe_end(state, me): end_turn(state)  # 판정 후 턴 넘김
        return
    else:
        if state.double_stage==1:  # 이제 2수째를 기다리는 상태라면
            adj=[(rr,cc) for rr,cc in neighbors4(state.N, r, c) if can_place(state, rr, cc)]  # 인접 가능칸 탐색
            if not adj:  # 둘 곳이 없다면
                push_event(state, me, "🦘 인접 칸 없음 → 더블턴 무효", WARN)  # 무효 안내
                state.double_stage = 0  # 더블 종료
            else:
                return  # 2수째 입력을 기다리며 턴 유지

    # ── ⑤ 평소 턴 종료
    if not finalize_and_maybe_end(state, me): end_turn(state)  # 승/무 판정 후 교대

def main():
    pygame.init()  # pygame 전역 초기화
    pygame.display.set_caption("틱택톡: 아이템 에디션 (Python)")  # 윈도 타이틀
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))  # 화면 생성(설정된 해상도)
    clock = pygame.time.Clock()  # FPS 제어용 시계

    from ui import init_fonts, Button, draw_item_legend  # 지역 임포트(순환의존 최소화)
    init_fonts()  # 폰트 로더 초기화

    panel = pygame.Rect(MARGIN, MARGIN, 340, WINDOW_H - 2*MARGIN)  # 좌측 옵션 패널 영역
    board_area = pygame.Rect(panel.right + MARGIN, MARGIN, WINDOW_W - panel.width - 3*MARGIN, WINDOW_H - 2*MARGIN)
    # 보드 영역(Rect): 패널 오른쪽의 남은 공간

    btn_start = Button((panel.x+20, panel.bottom-70, 140, 48), "▶ 시작")  # 시작 버튼
    btn_reset = Button((panel.x+180, panel.bottom-70, 140, 48), "↻ 재시작")  # 재시작 버튼
    b_mode   = Button((panel.x+20, panel.y+70, 300, 46), "모드", MODES, "AI")  # 모드 선택(2인용/AI)
    b_diff   = Button((panel.x+20, panel.y+120,300, 46), "난이도", DIFFS, "Very Hard")  # 난이도 선택
    b_size   = Button((panel.x+20, panel.y+170,300, 46), "보드", BOARD_CHOICES, 3)  # 보드 크기 선택
    b_items  = Button((panel.x+20, panel.y+220,300, 46), "아이템전", ["ON","OFF"], "ON")  # 아이템 사용 여부

    def new_config():
        return Config(size=b_size.value,
                      mode=b_mode.value,
                      difficulty=b_diff.value if b_mode.value=="AI" else "Medium",
                      items_on=(b_items.value=="ON"))
        # 현재 UI 버튼 값으로 Config 객체 생성(AI 모드일 때만 난이도 사용)

    def start_game():
        nonlocal cfg, st  # 외부 스코프 변수 갱신
        cfg = new_config()  # 최신 설정 반영
        st = GameState(N=cfg.size, items_on=cfg.items_on)  # 게임 상태 초기화(보드 생성)
        st.turn="X"; st.toasts.clear(); st.last_banner=None  # X부터 시작, 이벤트 초기화
        st.pending=None; st.double_stage=0  # 아이템 대기/더블 상태 초기화
        st.ai_pending=False; st.ai_second_pending=False  # AI 대기 플래그 초기화
        st.item_spent_cells.clear(); st.tt.clear()  # 셀 소모/TT 캐시 초기화

    cfg = new_config(); st = GameState(N=3, items_on=True)  # 기본값으로 초기 객체 확보
    start_game()  # 첫 게임 시작(초기화 적용)

    running = True  # 메인 루프 플래그
    while running:
        now = pygame.time.get_ticks()  # 현재 ms 타임스탬프(딜레이/타이밍에 사용)
        for ev in pygame.event.get():  # 이벤트 큐 처리
            if ev.type == pygame.QUIT: running=False  # 창 닫기 → 루프 종료
            elif ev.type == pygame.KEYDOWN:  # 키 입력
                if ev.key == pygame.K_ESCAPE: running=False  # ESC → 종료
                if ev.key == pygame.K_r: start_game()  # R → 재시작

            # 클릭하면 기존 토스트/배너를 먼저 지움(새 이벤트는 정상 표시)
            if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                st.toasts.clear(); st.last_banner=None  # 화면 메시지 리셋

            if b_mode.handle(ev): b_diff.enabled=(b_mode.value=="AI")  # 모드 변경 시 난이도 버튼 활성/비활성
            b_diff.handle(ev); b_size.handle(ev); b_items.handle(ev)  # 다른 버튼들 입력 처리
            if btn_start.handle(ev): start_game()  # 시작 클릭 → 재초기화
            if btn_reset.handle(ev): start_game()  # 재시작 클릭 → 재초기화

            if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:  # 좌클릭일 때
                if cfg.mode=="AI" and st.turn=="O" and not st.game_over:
                    pass  # AI 차례에는 사용자 입력 무시
                else:
                    handle_click(st, cfg, ev.pos, board_area)  # 사람 차례면 클릭 처리

        # ── AI 턴 ──
        from ai import choose_move  # 지역 임포트(재로드 안전)
        if cfg.mode=="AI" and not st.game_over:  # AI 모드 + 게임 진행 중
            if st.pending and st.pending[1]!="O":  # 아이템 대기 중인데 소유자가 O가 아니면
                st.ai_pending=False; st.ai_second_pending=False  # AI 진행 잠시 정지
            elif st.turn=="O":  # O 차례(컴퓨터)
                if st.skip_next["O"]:  # O 스킵 상태면
                    st.skip_next["O"]=False  # 소진
                    push_event(st, "O", "🔗 O 턴 스킵", WARN)  # 안내
                    end_turn(st)  # 턴 넘김
                else:
                    # 첫 수 딜레이
                    if not st.ai_pending and not st.ai_second_pending:  # 대기 예약 없으면
                        st.ai_pending=True; st.ai_wake=now+AI_DELAY_MS  # 첫 수 딜레이 예약
                    if st.ai_pending and now>=st.ai_wake:  # 딜레이 만료 시
                        mv=choose_move(st, cfg.difficulty)  # AI가 수 선택
                        if mv:
                            r,c=mv  # 제안 좌표
                            if can_place(st,r,c):  # 유효 착수인지 확인
                                st.board[r][c]="O"; st.last_move=(r,c)  # 수 적용
                                if st.items_on and (r,c) not in st.item_spent_cells:  # 아이템 처리
                                    it=roll_item(allow_double=True)  # 첫 수는 DOUBLE 허용
                                    if it:
                                        apply_item(st,"O",it,for_ai=True,origin=(r,c))  # AI용 적용(메시지 톤 등)
                                        st.item_spent_cells.add((r,c))  # 셀 소모 기록
                                if st.double_stage==1:  # 더블턴 발동이면
                                    st.ai_second_pending=True; st.ai_second_wake=now+AI_DELAY_MS  # 2수째 딜레이 예약
                                else:
                                    if not finalize_and_maybe_end(st,"O"): end_turn(st)  # 판정 후 턴 넘김
                        st.ai_pending=False  # 첫 수 대기 플래그 해제
                    # 두 번째 수 딜레이
                    if st.ai_second_pending and now>=st.ai_second_wake:  # 2수째 타이밍 도래
                        r0,c0=st.last_move if st.last_move else (-1,-1)  # 직전 수 기준
                        adj=[(rr,cc) for rr,cc in neighbors4(st.N,r0,c0) if can_place(st,rr,cc)]  # 인접 가능칸 수집
                        if adj:
                            rr,cc=random.choice(adj)  # 랜덤으로 하나 선택(간단 전략)
                            st.board[rr][cc]="O"; st.last_move=(rr,cc)  # 2수째 적용
                            if st.items_on and (rr,cc) not in st.item_spent_cells:  # 아이템 가능
                                it2=roll_item(allow_double=False)  # 2수째는 DOUBLE 금지
                                if it2:
                                    apply_item(st,"O",it2,for_ai=True,origin=(rr,cc))  # 적용
                                    st.item_spent_cells.add((rr,cc))  # 소모 기록
                        else:
                            push_event(st, "O", "🦘 인접 칸 없음 → 더블턴 무효", WARN)  # 2수 불가 안내
                        st.double_stage=0  # 더블 모드 종료
                        st.ai_second_pending=False  # 2수째 대기 해제
                        if not finalize_and_maybe_end(st,"O"): end_turn(st)  # 판정 후 턴 넘김

        # ── 그리기 ──
        screen.fill(DARK_BG)  # 배경색 칠하기
        pygame.draw.rect(screen, PANEL_BG, panel, border_radius=18)  # 좌측 패널 배경
        pygame.draw.rect(screen, BORDER, panel, 1, border_radius=18)  # 패널 테두리
        screen.blit(render_mix("틱택톡: 아이템 에디션", big=True, color=TEXT), (panel.x+20, panel.y+18))  # 타이틀 텍스트

        b_mode.draw(screen); b_diff.enabled=(b_mode.value=="AI"); b_diff.draw(screen)  # 모드/난이도
        b_size.draw(screen); b_items.draw(screen)  # 보드/아이템 옵션
        draw_item_legend(screen, panel)  # 아이템 설명 섹션

        btn_start.draw(screen); btn_reset.draw(screen)  # 시작/재시작 버튼

        draw_game(screen, st, cfg, board_area)  # 보드/말/하이라이트 렌더
        draw_banner(screen, st, board_area)  # 상단 배너(큰 메시지)
        draw_toasts(screen, st)  # 우측하단 토스트들

        pygame.display.flip()  # 프레임 표시 갱신
        clock.tick(FPS)  # FPS 유지(대기)

    pygame.quit(); sys.exit(0)  # pygame 종료 후 프로세스 종료

if __name__ == "__main__":  # 모듈이 아니라 직접 실행될 때만
    main()  # 게임 시작
