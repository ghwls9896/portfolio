"""
모델 학습 페이지

Random Forest 회귀 모델을 학습하고, 학습 곡선과 OOB 점수를 시각화합니다.
원본 노트북의 TFDF RandomForestModel을 scikit-learn의 RandomForestRegressor로 대체했습니다.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from utils.data_loader import load_train_data, data_availability_check
from utils.model import train_random_forest

st.set_page_config(page_title="모델 학습 — House Prices", page_icon="🌲", layout="wide")

st.title("🌲 모델 학습")
st.markdown(
    "**Random Forest 회귀 모델**을 학습합니다. "
    "Random Forest는 여러 개의 결정 트리를 독립적으로 학습시킨 뒤 예측을 평균내는 앙상블 기법으로, "
    "과적합에 강하고 별도의 전처리가 거의 필요 없는 견고한 알고리즘입니다."
)
st.markdown("---")

# ─────────────────────────────────────────────────────────────
# 데이터 로드
# ─────────────────────────────────────────────────────────────
if not data_availability_check():
    st.stop()

df = load_train_data()

# ─────────────────────────────────────────────────────────────
# 하이퍼파라미터 설정
# ─────────────────────────────────────────────────────────────
st.header("1. 하이퍼파라미터 설정")

with st.sidebar:
    st.markdown("### ⚙️ 모델 설정")
    n_estimators = st.slider("트리 개수 (n_estimators)", 50, 500, 300, 50)
    max_depth_option = st.selectbox("최대 깊이 (max_depth)", ["제한 없음", 5, 10, 15, 20, 30])
    max_depth = None if max_depth_option == "제한 없음" else int(max_depth_option)
    min_samples_split = st.slider("분기 최소 샘플 수", 2, 20, 2)
    test_size = st.slider("검증셋 비율", 0.1, 0.4, 0.3, 0.05)
    st.markdown("---")
    train_button = st.button("🚀 모델 학습 시작", type="primary", use_container_width=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("트리 개수", n_estimators)
with col2:
    st.metric("최대 깊이", max_depth_option)
with col3:
    st.metric("분기 최소 샘플", min_samples_split)
with col4:
    st.metric("검증셋 비율", f"{test_size:.0%}")

st.info(
    "👈 사이드바에서 하이퍼파라미터를 조정한 후 **'모델 학습 시작'** 버튼을 눌러주세요. "
    "학습 결과는 세션 동안 캐싱됩니다."
)

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# 학습 실행
# ─────────────────────────────────────────────────────────────
if train_button or "train_result" in st.session_state:
    if train_button:
        with st.spinner("Random Forest 모델 학습 중... (수십 초 소요)"):
            result = train_random_forest(
                df,
                n_estimators=n_estimators,
                max_depth=max_depth,
                min_samples_split=min_samples_split,
                test_size=test_size,
            )
        st.session_state["train_result"] = result
        st.session_state["train_config"] = {
            "n_estimators": n_estimators,
            "max_depth": max_depth_option,
            "min_samples_split": min_samples_split,
            "test_size": test_size,
        }
        st.success("✅ 학습 완료!")

    result = st.session_state["train_result"]
    config = st.session_state["train_config"]

    # ─────────────────────────────────────────────────────────
    # 2. 학습 결과 요약
    # ─────────────────────────────────────────────────────────
    st.header("2. 학습 결과 요약")

    metrics = result["metrics"]
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("OOB RMSE", f"${metrics['oob_rmse']:,.0f}",
                  help="Out-of-Bag 데이터로 측정한 RMSE")
    with c2:
        st.metric("Validation RMSE", f"${metrics['rmse']:,.0f}",
                  help="검증셋에서의 RMSE")
    with c3:
        st.metric("Validation MAE", f"${metrics['mae']:,.0f}",
                  help="평균 절대 오차")
    with c4:
        st.metric("Validation R²", f"{metrics['r2']:.4f}",
                  help="결정계수 (1에 가까울수록 좋음)")

    st.markdown(
        f"""
        > 학습 데이터: **{len(result['X_train']):,}개** · 검증 데이터: **{len(result['X_valid']):,}개**
        > 특성 수: **{len(result['feature_names'])}개**
        """
    )

    st.markdown("---")

    # ─────────────────────────────────────────────────────────
    # 3. 학습 곡선
    # ─────────────────────────────────────────────────────────
    st.header("3. 학습 곡선 — 트리 개수에 따른 OOB RMSE")

    logs = result["training_logs"]
    log_df = pd.DataFrame(logs)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=log_df["num_trees"], y=log_df["rmse"],
        mode="lines+markers", line=dict(color="#d97706", width=2.5),
        marker=dict(size=6, color="#d97706"), name="OOB RMSE",
    ))
    fig.update_layout(
        height=420, margin=dict(l=0, r=0, t=20, b=0),
        xaxis_title="트리 개수 (num_trees)", yaxis_title="OOB RMSE (USD)",
        plot_bgcolor="white",
    )
    fig.update_xaxes(gridcolor="#eee")
    fig.update_yaxes(gridcolor="#eee")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        """
        > 💡 **해석**: 트리 개수가 증가함에 따라 OOB RMSE가 감소하다가 일정 시점에서 수렴합니다.
        > Random Forest는 트리를 많이 추가해도 과적합되지 않으므로, RMSE가 평탄해진 이후로는
        > 트리를 더 늘려도 큰 이득이 없습니다.
        """
    )

    st.markdown("---")

    # ─────────────────────────────────────────────────────────
    # 4. OOB 예측 vs 실제 (학습 데이터)
    # ─────────────────────────────────────────────────────────
    st.header("4. OOB 예측값 vs 실제값")
    st.markdown(
        "Out-of-Bag 예측: 각 트리는 부트스트랩 샘플로 학습되며, "
        "사용되지 않은 샘플(OOB)로 예측한 결과를 평균합니다. 별도의 검증셋 없이 일반화 성능을 추정할 수 있습니다."
    )

    model = result["model"]
    y_train = result["y_train"]
    oob_pred = model.oob_prediction_

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=y_train, y=oob_pred, mode="markers",
        marker=dict(size=5, color="#d97706", opacity=0.5),
        name="OOB 예측",
    ))
    # y = x 기준선
    min_val = min(y_train.min(), oob_pred.min())
    max_val = max(y_train.max(), oob_pred.max())
    fig.add_trace(go.Scatter(
        x=[min_val, max_val], y=[min_val, max_val],
        mode="lines", line=dict(color="#1a1a1a", width=2, dash="dash"),
        name="y = x (완벽한 예측)",
    ))
    fig.update_layout(
        height=500, margin=dict(l=0, r=0, t=20, b=0),
        xaxis_title="실제 SalePrice (USD)", yaxis_title="OOB 예측 SalePrice (USD)",
        plot_bgcolor="white",
    )
    fig.update_xaxes(gridcolor="#eee", tickformat="$,.0f")
    fig.update_yaxes(gridcolor="#eee", tickformat="$,.0f")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        """
        > 💡 **해석**: 점들이 대각선($y=x$)에 가까울수록 예측이 정확합니다.
        > 고가 주택($300K 이상) 영역에서 예측이 다소 보수적(저평가)으로 나타나는 경향이 있는데,
        > 이는 학습 데이터에 고가 사례가 적기 때문에 일반적인 트리 기반 모델에서 흔히 관찰됩니다.
        """
    )

    st.markdown("---")
    st.success(
        "✅ 학습이 완료되었습니다. 왼쪽 사이드바에서 **'모델 평가'** 페이지로 이동하여 "
        "검증셋에서의 상세 평가를 확인하세요."
    )

else:
    st.info("👈 사이드바에서 하이퍼파라미터를 설정한 뒤 학습 버튼을 눌러주세요.")
