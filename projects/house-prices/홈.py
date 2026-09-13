"""
House Prices Prediction — Streamlit App
메인 홈페이지 (프로젝트 개요)

Kaggle 'House Prices - Advanced Regression Techniques' 대회 데이터를 사용하여
Random Forest 모델로 집값을 예측하는 분석 결과를 소개하는 멀티페이지 앱입니다.
"""

import streamlit as st
from utils.data_loader import load_train_data, data_availability_check

# ─────────────────────────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="House Prices Prediction",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# 커스텀 CSS — 차분한 에디토리얼 톤
# ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .main > div {
        padding-top: 2rem;
    }
    h1, h2, h3 {
        font-family: 'Georgia', 'Times New Roman', serif;
        letter-spacing: -0.01em;
    }
    .hero-title {
        font-size: 3.2rem;
        font-weight: 700;
        line-height: 1.1;
        margin-bottom: 0.5rem;
        color: #1a1a1a;
    }
    .hero-subtitle {
        font-size: 1.15rem;
        color: #555;
        margin-bottom: 2rem;
        line-height: 1.6;
    }
    .accent-bar {
        height: 4px;
        width: 60px;
        background: linear-gradient(90deg, #d97706, #ea580c);
        margin: 0.5rem 0 1.5rem 0;
        border-radius: 2px;
    }
    .step-card {
        background: #fafaf7;
        border-left: 3px solid #d97706;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
        border-radius: 4px;
    }
    .step-card h4 {
        margin: 0 0 0.3rem 0;
        color: #1a1a1a;
        font-size: 1.05rem;
    }
    .step-card p {
        margin: 0;
        color: #555;
        font-size: 0.95rem;
    }
    .metric-pill {
        display: inline-block;
        background: #1a1a1a;
        color: #f5f5f0;
        padding: 0.3rem 0.7rem;
        border-radius: 20px;
        font-size: 0.85rem;
        margin-right: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────
# 헤더
# ─────────────────────────────────────────────────────────────
col_a, col_b = st.columns([3, 1])

with col_a:
    st.markdown('<div class="hero-title">🏡 House Prices Prediction</div>', unsafe_allow_html=True)
    st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-subtitle">'
        "Kaggle <i>House Prices — Advanced Regression Techniques</i> 대회 데이터를 활용한 "
        "탐색적 데이터 분석과 Random Forest 회귀 모델 기반 집값 예측 분석입니다."
        "</div>",
        unsafe_allow_html=True,
    )

with col_b:
    st.markdown(
        """
        <div style="background:#fafaf7; padding:1rem; border-radius:8px; margin-top:1rem;">
        <div style="font-size:0.8rem; color:#888; text-transform:uppercase; letter-spacing:0.05em;">Dataset</div>
        <div style="font-size:1.4rem; font-weight:700; color:#1a1a1a;">1,460 × 81</div>
        <div style="font-size:0.85rem; color:#555;">samples × features</div>
        <hr style="margin:0.7rem 0; border-color:#e5e5e0;">
        <div style="font-size:0.8rem; color:#888; text-transform:uppercase; letter-spacing:0.05em;">Target</div>
        <div style="font-size:1rem; font-weight:600; color:#1a1a1a;">SalePrice (USD)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")

# ─────────────────────────────────────────────────────────────
# 데이터 가용성 체크
# ─────────────────────────────────────────────────────────────
if not data_availability_check():
    st.stop()

df = load_train_data()

# ─────────────────────────────────────────────────────────────
# 프로젝트 소개
# ─────────────────────────────────────────────────────────────
st.markdown("## 프로젝트 개요")

st.markdown(
    """
이 프로젝트는 Iowa주 Ames시의 주택 거래 데이터를 기반으로, 79개의 특성
(주거지 면적, 지하실, 차고, 건축연도 등)을 이용해 주택 판매가격을 예측하는 회귀 문제입니다.
원본 분석은 **TensorFlow Decision Forests의 Random Forest 모델**로 수행되었으며,
이 웹앱에서는 동일한 알고리즘 계열인 **scikit-learn의 RandomForestRegressor**로
재구현하여 어느 환경에서나 실행 가능하도록 했습니다.
"""
)

# ─────────────────────────────────────────────────────────────
# 분석 흐름
# ─────────────────────────────────────────────────────────────
st.markdown("## 분석 흐름")

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        """
        <div class="step-card">
            <h4>📊 1. 탐색적 데이터 분석 (EDA)</h4>
            <p>SalePrice의 분포, 수치형 특성의 분포, 결측치 패턴을 시각화하여
            데이터의 구조를 파악합니다.</p>
        </div>
        <div class="step-card">
            <h4>🌲 2. 모델 학습</h4>
            <p>Random Forest 회귀 모델을 학습하고, 트리 개수에 따른 OOB RMSE 변화를
            관찰하여 수렴 여부를 확인합니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class="step-card">
            <h4>📈 3. 모델 평가</h4>
            <p>검증 데이터셋에 대한 RMSE, MAE, R² 등의 지표와 잔차 분석으로
            모델의 성능을 평가합니다.</p>
        </div>
        <div class="step-card">
            <h4>🔍 4. 변수 중요도 및 예측</h4>
            <p>어떤 특성이 가격 결정에 중요한지 파악하고, 테스트 데이터에 대한
            예측을 수행하여 제출 파일을 생성합니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")

# ─────────────────────────────────────────────────────────────
# 데이터 미리보기
# ─────────────────────────────────────────────────────────────
st.markdown("## 데이터 미리보기")

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("샘플 수", f"{len(df):,}")
with c2:
    st.metric("특성 수", f"{df.shape[1] - 2}")  # Id, SalePrice 제외
with c3:
    st.metric("평균 가격", f"${df['SalePrice'].mean():,.0f}")
with c4:
    st.metric("중앙값 가격", f"${df['SalePrice'].median():,.0f}")

with st.expander("처음 5개 행 보기"):
    st.dataframe(df.head(), use_container_width=True)

# ─────────────────────────────────────────────────────────────
# 네비게이션 안내
# ─────────────────────────────────────────────────────────────
st.markdown("---")
st.info(
    "👈 왼쪽 사이드바의 페이지 메뉴에서 **EDA → 모델 학습 → 모델 평가 → 예측** 순으로 둘러보세요."
)

# 푸터
st.markdown(
    """
    <div style="margin-top:3rem; padding-top:1rem; border-top:1px solid #e5e5e0; color:#888; font-size:0.85rem;">
    Built with Streamlit · Data from <a href="https://www.kaggle.com/competitions/house-prices-advanced-regression-techniques" style="color:#d97706;">Kaggle House Prices Competition</a>
    </div>
    """,
    unsafe_allow_html=True,
)
