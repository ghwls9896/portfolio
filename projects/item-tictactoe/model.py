# ================================
# 데이터 모델 정의 (게임 설정 / 상태)
# ================================
"""
- Config : 게임을 시작할 때 필요한 설정(보드 크기, AI 난이도 등)을 담는 데이터.
- GameState : 게임이 진행되는 동안 실시간으로 변하는 상태를 모두 저장.
    * 보드 상태
    * 턴(X/O)
    * 승리 정보
    * 아이템 사용 여부, 잠금(lock) 정보
    * AI 탐색용 데이터(tt)
    * UI 표시용 이벤트(토스트, 배너)
"""

from dataclasses import dataclass, field  # dataclass : 데이터만 저장하는 클래스 쉽게 정의
from typing import Dict, List, Optional, Tuple

# -----------------------------------
# 게임 설정(Config)
# -----------------------------------

@dataclass
class Config:
    """
    게임을 시작할 때 사용되는 기본 설정값을 담는 클래스.
    """
    size: int = 3                 # 보드 크기 (3=3x3, 4=4x4 등)
    mode: str = "AI"              # 게임 모드 : "2인용" 또는 "AI"
    difficulty: str = "Very Hard" # AI 난이도 (Easy / Medium / Hard / Very Hard)
    items_on: bool = True         # 아이템 기능 사용 여부


# -----------------------------------
# 게임 상태(GameState)
# -----------------------------------

@dataclass
class GameState:
    """
    게임이 플레이되는 동안 실시간으로 변하는 모든 상태를 저장.
    - 보드, 턴, 승리 상태
    - 아이템 및 잠금 정보
    - 이벤트(UI용)
    - AI가 사용할 탐색 캐시(tt)
    """
    N: int                                        # 보드 크기
    board: List[List[str]] = field(init=False)    # 보드 상태 (초기화는 __post_init__에서 수행)
    turn: str = "X"                               # 현재 턴 ("X" 또는 "O")
    winner: Optional[str] = None                  # 승자 표시 (없으면 None)
    winning_cells: List[Tuple[int, int]] = field(default_factory=list)  # 승리한 라인 좌표들

    # -------- 아이템/락 관련 --------
    skip_next: Dict[str, bool] = field(default_factory=lambda: {"X": False, "O": False})
    # skip_next : 플레이어가 "한 턴 쉬기" 아이템을 당했을 때 True로 표시

    shield: Dict[str, int] = field(default_factory=lambda: {"X": 0, "O": 0})
    # shield : 보호막 아이템 개수 (X, O 각각 몇 개 남았는지)

    locks: Dict[Tuple[int, int], int] = field(default_factory=dict)
    # locks : 잠긴 칸 정보 {(r,c): 턴 수} 형태로 기록

    last_move: Optional[Tuple[int, int]] = None
    # last_move : 가장 최근에 둔 좌표 저장

    items_on: bool = True
    # items_on : 게임 중 아이템 기능 사용 여부

    item_spent_cells: set = field(default_factory=set)
    # item_spent_cells : 아이템으로 "소모된" 칸 저장 (1회성 셀 소모 규칙용)

    # -------- 이벤트(토스트/배너) --------
    toasts: List[Tuple[Optional[str], str, int, Tuple[int, int, int]]] = field(default_factory=list)
    # toasts : 화면에 잠깐 뜨는 알림 메시지 목록
    # (플레이어, 메시지, 지속시간(ms), 색상RGB)

    last_banner: Optional[Tuple[Optional[str], str, Tuple[int, int, int]]] = None
    # last_banner : 가장 최근에 표시된 배너 메시지
    # (플레이어, 메시지, 색상RGB)

    # -------- 흐름 제어 --------
    game_over: bool = False
    # game_over : 게임이 끝났는지 여부

    double_stage: int = 0
    # double_stage : 아이템/특수 규칙으로 한 플레이어가 두 번 연속 둘 수 있을 때 단계 표시
    # (0 = 없음, 1 = 두 번째 수 대기 중)

    pending: Optional[tuple] = None
    # pending : 현재 처리 대기 중인 아이템 액션 상태 저장
    # 예) ("LOCK", owner) / ("SWAP_MY", owner) / ("SWAP_OPP", owner, (r,c))

    # -------- AI 딜레이 / 탐색 캐시 --------
    ai_pending: bool = False
    # ai_pending : AI가 첫 번째 수를 두기 전 대기 중인지 표시

    ai_wake: int = 0
    # ai_wake : AI가 언제 깨어나서 수를 둘지(지연 시간)

    ai_second_pending: bool = False
    # ai_second_pending : AI가 두 번째 수를 두기 전 대기 중인지 표시

    ai_second_wake: int = 0
    # ai_second_wake : AI 두 번째 수 깨어날 시간

    tt: dict = field(default_factory=dict)
    # tt : 트랜스포지션 테이블(이미 계산된 미니맥스 결과 캐싱)

    # -----------------------------------
    # dataclass 초기화 후 자동 실행
    # -----------------------------------
    def __post_init__(self):
        """
        dataclass는 기본값만 넣어주므로
        보드(board)는 여기서 N 크기에 맞게 빈 문자열("")로 채워 초기화한다.
        """
        self.board = [["" for _ in range(self.N)] for _ in range(self.N)]
