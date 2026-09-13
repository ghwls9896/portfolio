# House Prices · Streamlit 분석 앱

주택 가격 데이터를 탐색하고 scikit-learn Random Forest로 학습·평가·예측하는 다중 페이지 앱입니다. EDA, 모델 설정, 잔차와 변수 중요도, CSV 예측 결과 다운로드를 한 흐름으로 연결합니다.

## 실행
공식 House Prices 대회에서 받은 `train.csv`, `test.csv`를 `data/` 폴더에 준비합니다.
```bash
python -m pip install -r requirements.txt
python -m streamlit run 홈.py
```
실제 진입 파일명은 `홈.py`입니다. 원본 설명의 `app.py` 표기를 바로잡았습니다.

## 구조
`pages/`는 EDA → 모델 학습 → 평가 → 예측 화면이고, `utils/`는 데이터 로딩과 모델 처리입니다. 원본 TFDF 노트북과 이 앱의 scikit-learn 구현은 라이브러리가 달라 결과가 동일하다고 보장할 수 없습니다.

트리별 예측 분위수 범위는 모델 내부 예측 분산을 보여 주는 참고 지표입니다. 보정된 통계적 신뢰 구간이나 미래 가격 보장으로 해석하지 않습니다. 이번 정리에서는 Python 구문을 검사했으며 전체 데이터 학습과 웹 화면을 재검증하지 않았습니다.
