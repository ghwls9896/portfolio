# Chicken POS · 주문과 재고 관리

PyQt6 화면에서 테이블별 장바구니를 관리하고, 현금·카드 방식의 판매 기록과 영수증을 생성하는 데스크톱 학습 프로젝트입니다. 판매에 따른 재고 차감과 매출 시각화를 포함합니다. 실제 결제망과 연결되지는 않습니다.

## 실행
```bash
python -m pip install -r requirements.txt
python src/main.py
```
공개본에는 가상 메뉴 1개, 가상 재고 20개, 빈 판매 기록을 넣었습니다. 주문 후 `data/sales.json`과 `data/inventory.json`이 변경됩니다.

## 구조
| 파일 | 역할 |
|---|---|
| `src/models.py` | 메뉴·재고·판매 데이터 구조 |
| `src/store.py` | JSON 읽기, 금액 계산, 재고 차감 |
| `src/views.py` | 메인 창과 주문 작업 |
| `src/dialogs.py` | 영수증 등 대화상자 |

## 설계에서 배운 점
화면과 저장 로직을 분리하면 UI를 바꿔도 판매 모델을 재사용할 수 있습니다. 다만 현재 JSON 쓰기는 트랜잭션이 아니며 여러 재료 차감 중 실패할 때 원자적 복구를 보장하지 않습니다. 실제 운영에는 DB 트랜잭션·입력 검증·인증을 추가해야 합니다.

[노션 설명](https://app.notion.com/p/2ae1b45f6f0780b0a183f226dcdb1ce8)
