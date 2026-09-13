# 학습 흐름과 자료 지도

## 1. 프로그래밍 기반
Python 작은 프로그램 → 객체와 모듈 분리 → 트리와 알고리즘 → GUI와 이벤트 처리 순서로 확장했습니다. [Python 기초](studies/python-fundamentals), [Huffman](projects/huffman), [POS](projects/chicken-pos)에서 코드 규모가 커질 때의 책임 분리를 볼 수 있습니다.

기존 [1학년 저장소](https://github.com/ghwls9896/1_grade)는 C++ 등 초기 과제를, [2학년 저장소](https://github.com/ghwls9896/2_grade)는 자료구조와 후속 수업 자료를 보관합니다.

## 2. 데이터 분석
확률·통계 → Pandas → 전처리 → 시각화 → 시계열 → 특징 공학 → Streamlit으로 이어집니다. [추가 분석 과제](studies/data-analysis), [DengAI](studies/dengai), [Flu Shot](studies/flu-shot), [주택 가격 앱](projects/house-prices)을 연결해 읽으세요.

공공 API를 활용한 구미 관광·날씨 과제도 로컬에 있습니다. API 연결 설정을 포함할 수 있는 원본은 이 공개 정리본에 넣지 않았습니다.

## 3. 딥러닝 기초
Unit Node 역전파, 선형·로지스틱 회귀, 손실 함수와 학습률 → 프레임워크 비교 → CNN → 데이터 증강과 전이학습 → 객체 검출을 학습했습니다. [기초 노션](https://app.notion.com/p/3d51b45f6f078161a13ad0fab46727b8)에서 개념 설명을 확인할 수 있습니다.

FashionMNIST 저장 결과는 Random Search 검증 89.8438% / 테스트 89.39%, Optuna 검증 90.625% / 테스트 85.13%입니다. 검증 최고 모델이 테스트에서도 반드시 최고인 것은 아니며 튜닝 비교에는 분할·seed·선택 기준을 함께 보아야 합니다.

## 4. 집중 실습 기록
MODAL CLASS 폴더에는 Pandas, Tensor, Iris/MNIST, scheduler/early stopping, CNN, 이미지 정규화·transform, CIFAR-10, AlexNet/VGG/ResNet, fine tuning, relabeling 실습이 있습니다. 날짜별 수업 자료이며 별개의 완성 제품으로 나열하지 않았습니다. 강의 원본과 제공 데이터는 원본 폴더에서 관리합니다.

## 5. 딥러닝 심화
[7편의 해설](studies/deep-learning-advanced)에서 확률분포와 정보량, MLE·MAP, RNN·BPTT, LSTM·GRU, 한글 수사 문자 예측, 임베딩·게이트 해석을 연결합니다.

## 6. 게임과 서비스
[Pygame 카드 게임](projects/number-card), [아이템 틱택토](projects/item-tictactoe), [Unity 결석](projects/project-absence), [Flutter 채팅](projects/realtime-chat)에서 규칙·상태·화면·통신을 다루었습니다.

GitHub의 기존 비공개 `mon_evo`와 `desktop-tutorial`은 공개 자료로 복사하지 않았습니다. 교재 `DataScience`는 원저자 PinkWink의 포크로 구분합니다.
