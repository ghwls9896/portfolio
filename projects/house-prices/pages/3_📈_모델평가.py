"""
모델 평가 페이지

학습된 모델의 검증셋 성능과 변수 중요도를 시각화합니다.
원본 노트북의 'Variable Importances' 분석을 확장하여 보여줍니다.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from utils.data_loader import data_availability_check

st.set_page_config(page_title="모델 평가 — House Prices", page_icon="📈", layout="wide")

st.title("📈 모델 평가")
st.markdown(
    "학습된 모델을 **검증 데이터셋**에서 평가합니다. "
    "잔차 분석, 오차 분포, 변수 중요도를 종합적으로 살펴봅니다."
)
st.markdown("---")

# ─────────────────────────────────────────────────────────────
# 학습 결과 체크
# ─────────────────────────────────────────────────────────────
if not data_availability_check():
    st.stop()

if "train_result" not in st.session_state:
    st.warning("⚠️ 먼저 **'모델 학습'** 페이지에서 모델을 학습해주세요.")
    st.stop()

result = st.session_state["train_result"]
model = result["model"]
X_valid = result["X_valid"]
y_valid = result["y_valid"]
preds = result["predictions_valid"]
metrics = result["metrics"]
feature_names = result["feature_names"]

# ─────────────────────────────────────────────────────────────
# 1. 평가 지표
# ─────────────────────────────────────────────────────────────
st.header("1. 검증셋 평가 지표")

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("RMSE", f"${metrics['rmse']:,.0f}",
              help="Root Mean Squared Error — 큰 오차에 더 큰 패널티")
with c2:
    st.metric("MAE", f"${metrics['mae']:,.0f}",
              help="Mean Absolute Error — 평균 절대 오차")
with c3:
    st.metric("R²", f"{metrics['r2']:.4f}",
              help="결정계수")
with c4:
    mean_price = y_valid.mean()
    st.metric("RMSE/평균가격", f"{metrics['rmse']/mean_price:.1%}",
              help="평균 가격 대비 RMSE 비율")

st.markdown(
    f"""
    > 검증셋 평균 가격: **${mean_price:,.0f}** · 중앙값: **${np.median(y_valid):,.0f}**
    > RMSE는 평균 가격의 약 **{metrics['rmse']/mean_price:.1%}** 수준입니다.
    """
)

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# 2. 예측 vs 실제 산점도
# ─────────────────────────────────────────────────────────────
st.header("2. 예측값 vs 실제값")

residuals = y_valid - preds

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=y_valid, y=preds, mode="markers",
    marker=dict(
        size=7, color=residuals, colorscale="RdBu_r",
        cmin=-residuals.std()*2, cmax=residuals.std()*2,
        showscale=True, colorbar=dict(title="잔차"),
        opacity=0.7, line=dict(width=0.5, color="white"),
    ),
    text=[f"실제: ${a:,.0f}<br>예측: ${p:,.0f}<br>잔차: ${a-p:,.0f}"
          for a, p in zip(y_valid, preds)],
    hoverinfo="text",
    name="예측",
))
min_val = min(y_valid.min(), preds.min())
max_val = max(y_valid.max(), preds.max())
fig.add_trace(go.Scatter(
    x=[min_val, max_val], y=[min_val, max_val],
    mode="lines", line=dict(color="#1a1a1a", width=2, dash="dash"),
    name="y = x", showlegend=True,
))
fig.update_layout(
    height=550, margin=dict(l=0, r=0, t=20, b=0),
    xaxis_title="실제 SalePrice (USD)", yaxis_title="예측 SalePrice (USD)",
    plot_bgcolor="white",
)
fig.update_xaxes(gridcolor="#eee", tickformat="$,.0f")
fig.update_yaxes(gridcolor="#eee", tickformat="$,.0f")
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# 3. 잔차 분석
# ─────────────────────────────────────────────────────────────
st.header("3. 잔차 분석")

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("**잔차 분포 (예측 오차)**")
    fig = px.histogram(
        x=residuals, nbins=50, color_discrete_sequence=["#d97706"],
    )
    fig.add_vline(x=0, line_dash="dash", line_color="#1a1a1a")
    fig.update_layout(
        height=380, margin=dict(l=0, r=0, t=10, b=0),
        xaxis_title="잔차 (실제 - 예측, USD)", yaxis_title="빈도",
        plot_bgcolor="white", showlegend=False,
    )
    fig.update_xaxes(gridcolor="#eee", tickformat="$,.0f")
    fig.update_yaxes(gridcolor="#eee")
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    st.markdown("**예측값 vs 잔차**")
    fig = px.scatter(
        x=preds, y=residuals,
        color_discrete_sequence=["#d97706"],
    )
    fig.add_hline(y=0, line_dash="dash", line_color="#1a1a1a")
    fig.update_traces(marker=dict(size=6, opacity=0.5))
    fig.update_layout(
        height=380, margin=dict(l=0, r=0, t=10, b=0),
        xaxis_title="예측값 (USD)", yaxis_title="잔차 (USD)",
        plot_bgcolor="white",
    )
    fig.update_xaxes(gridcolor="#eee", tickformat="$,.0f")
    fig.update_yaxes(gridcolor="#eee", tickformat="$,.0f")
    st.plotly_chart(fig, use_container_width=True)

st.markdown(
    """
    > 💡 **잔차 분석 해석**:
    > - 잔차 히스토그램이 0을 중심으로 대체로 대칭적이면 모델에 체계적 편향이 적다는 신호입니다.
    > - 예측값-잔차 산점도에서 잔차가 0 주변에 무작위로 흩어져 있어야 좋습니다.
    >   특정 가격대에서 잔차가 한쪽으로 쏠려있다면, 그 구간에서 모델이 체계적으로 과/저평가하고 있다는 뜻입니다.
    """
)

# 통계 요약
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("잔차 평균", f"${residuals.mean():,.0f}",
              help="이상적으로는 0에 가까워야 함")
with c2:
    st.metric("잔차 표준편차", f"${residuals.std():,.0f}")
with c3:
    pct_within_10pct = ((np.abs(residuals) / y_valid) < 0.1).mean()
    st.metric("10% 이내 정확도", f"{pct_within_10pct:.1%}",
              help="실제 가격의 ±10% 이내로 예측한 비율")

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# 4. 변수 중요도
# ─────────────────────────────────────────────────────────────
st.header("4. 변수 중요도 (Feature Importance)")
st.markdown(
    "각 특성이 모델 예측에 얼마나 기여했는지를 보여줍니다. "
    "여기서는 scikit-learn의 **MDI (Mean Decrease in Impurity)** 기반 중요도를 사용합니다. "
    "원본 노트북의 `NUM_AS_ROOT`와는 측정 방식이 다르지만 유사한 해석을 제공합니다."
)

importances = pd.DataFrame({
    "feature": feature_names,
    "importance": model.feature_importances_,
}).sort_values("importance", ascending=False)

top_n = st.slider("상위 N개 특성", 5, 30, 15)
top_importances = importances.head(top_n)

fig = px.bar(
    top_importances, x="importance", y="feature", orientation="h",
    color="importance", color_continuous_scale="Oranges",
    text=top_importances["importance"].round(4),
)
fig.update_traces(textposition="outside")
fig.update_layout(
    height=max(400, 30 * top_n), margin=dict(l=0, r=0, t=10, b=0),
    yaxis={"categoryorder": "total ascending"},
    xaxis_title="중요도 (Mean Decrease in Impurity)", yaxis_title="",
    coloraxis_showscale=False, plot_bgcolor="white",
)
fig.update_xaxes(gridcolor="#eee")
st.plotly_chart(fig, use_container_width=True)

st.markdown(
    """
    > 💡 **관찰**: `OverallQual`(전반적 자재/마감 품질), `GrLivArea`(지상 거주 면적),
    > `TotalBsmtSF`(지하실 총 면적), `GarageCars/GarageArea`(차고 크기) 등이 일관되게
    > 상위에 위치합니다. 이는 EDA에서 본 상관관계 분석 결과와도 일치합니다.
    >
    > Random Forest의 MDI 중요도는 **고카디널리티 수치형 변수에 편향**될 수 있다는 한계가 있어,
    > 더 엄밀한 분석을 위해서는 Permutation Importance나 SHAP을 함께 보는 것이 좋습니다.
    """
)
