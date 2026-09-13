"""
EDA — 탐색적 데이터 분석 페이지

원본 노트북의 EDA 단계를 재현합니다:
  - SalePrice 분포
  - 수치형 특성의 분포
  - 결측치 분석
  - 수치형 특성과 SalePrice의 상관관계
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.data_loader import load_train_data, data_availability_check

st.set_page_config(page_title="EDA — House Prices", page_icon="📊", layout="wide")

st.title("📊 탐색적 데이터 분석 (EDA)")
st.markdown(
    "데이터의 구조와 분포를 파악합니다. "
    "주택 가격 분포, 수치형 변수의 패턴, 그리고 가격과의 상관관계를 살펴봅니다."
)
st.markdown("---")

# ─────────────────────────────────────────────────────────────
# 데이터 로드
# ─────────────────────────────────────────────────────────────
if not data_availability_check():
    st.stop()

df = load_train_data()

# ─────────────────────────────────────────────────────────────
# 1. 데이터셋 기본 정보
# ─────────────────────────────────────────────────────────────
st.header("1. 데이터셋 기본 정보")

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("샘플 수 (행)", f"{df.shape[0]:,}")
with c2:
    st.metric("컬럼 수 (열)", f"{df.shape[1]}")
with c3:
    n_missing = df.isnull().sum().sum()
    st.metric("총 결측치 수", f"{n_missing:,}")

# 데이터 타입 분포
dtype_counts = df.dtypes.value_counts().reset_index()
dtype_counts.columns = ["데이터 타입", "컬럼 수"]
dtype_counts["데이터 타입"] = dtype_counts["데이터 타입"].astype(str)

col_left, col_right = st.columns([1, 1])
with col_left:
    st.markdown("**데이터 타입별 컬럼 수**")
    fig = px.bar(
        dtype_counts,
        x="컬럼 수",
        y="데이터 타입",
        orientation="h",
        color="컬럼 수",
        color_continuous_scale="Oranges",
        text="컬럼 수",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=250, showlegend=False, margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False
    )
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.markdown("**SalePrice 기술 통계**")
    stats = df["SalePrice"].describe().round(0).astype(int)
    stats_df = pd.DataFrame(
        {"통계량": stats.index, "값 (USD)": [f"${v:,}" for v in stats.values]}
    )
    st.dataframe(stats_df, use_container_width=True, hide_index=True)

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# 2. SalePrice 분포
# ─────────────────────────────────────────────────────────────
st.header("2. 주택 판매가격(SalePrice) 분포")
st.markdown(
    "타겟 변수인 `SalePrice`의 분포입니다. "
    "오른쪽으로 긴 꼬리를 가지는 우편향(right-skewed) 분포를 보입니다."
)

col_a, col_b = st.columns(2)
with col_a:
    fig = px.histogram(
        df, x="SalePrice", nbins=60, color_discrete_sequence=["#d97706"],
        title="가격 분포 (원본 스케일)",
    )
    fig.update_layout(
        height=380, margin=dict(l=0, r=0, t=40, b=0),
        xaxis_title="SalePrice (USD)", yaxis_title="빈도",
    )
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    fig = px.histogram(
        df, x=np.log1p(df["SalePrice"]), nbins=60, color_discrete_sequence=["#0369a1"],
        title="가격 분포 (로그 변환)",
    )
    fig.update_layout(
        height=380, margin=dict(l=0, r=0, t=40, b=0),
        xaxis_title="log(1 + SalePrice)", yaxis_title="빈도",
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown(
    """
    > 💡 **관찰**: 로그 변환을 적용하면 분포가 정규분포에 가까워집니다.
    > 회귀 모델에서 잔차의 정규성을 가정할 때 유용한 변환이지만,
    > 트리 기반 모델은 분포 변환에 민감하지 않으므로 본 분석에서는 원본 스케일로 학습합니다.
    """
)

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# 3. 결측치 분석
# ─────────────────────────────────────────────────────────────
st.header("3. 결측치 패턴")

missing = df.isnull().sum()
missing = missing[missing > 0].sort_values(ascending=False)
missing_pct = (missing / len(df) * 100).round(2)
missing_df = pd.DataFrame({
    "컬럼": missing.index,
    "결측 개수": missing.values,
    "결측 비율 (%)": missing_pct.values,
})

if len(missing_df) > 0:
    st.markdown(f"**결측치가 있는 컬럼: {len(missing_df)}개**")

    fig = px.bar(
        missing_df, x="결측 비율 (%)", y="컬럼", orientation="h",
        color="결측 비율 (%)", color_continuous_scale="Reds",
        height=max(400, 25 * len(missing_df)),
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0), yaxis={"categoryorder": "total ascending"},
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        """
        > 💡 **관찰**: `PoolQC`, `MiscFeature`, `Alley`, `Fence` 등은 결측 비율이 매우 높습니다.
        > 그러나 이는 실제로 **해당 시설이 없음**을 의미하는 경우가 많습니다 (예: 수영장이 없는 집의 PoolQC는 NaN).
        > Random Forest는 결측치를 자체적으로 처리할 수 있어 별도의 imputation 없이도 동작합니다.
        """
    )
else:
    st.success("결측치가 없습니다.")

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# 4. 수치형 특성 분포
# ─────────────────────────────────────────────────────────────
st.header("4. 수치형 특성 분포")

df_num = df.select_dtypes(include=["int64", "float64"]).drop(columns=["Id"], errors="ignore")
numeric_cols = [c for c in df_num.columns if c != "SalePrice"]

selected_cols = st.multiselect(
    "히스토그램으로 살펴볼 수치형 변수를 선택하세요 (최대 9개)",
    options=numeric_cols,
    default=["LotArea", "GrLivArea", "OverallQual", "YearBuilt", "TotalBsmtSF", "GarageArea"][:6],
    max_selections=9,
)

if selected_cols:
    n_cols = 3
    n_rows = (len(selected_cols) + n_cols - 1) // n_cols
    fig = make_subplots(rows=n_rows, cols=n_cols, subplot_titles=selected_cols)

    for i, col in enumerate(selected_cols):
        row = i // n_cols + 1
        col_idx = i % n_cols + 1
        fig.add_trace(
            go.Histogram(
                x=df[col], marker_color="#d97706", showlegend=False, nbinsx=40
            ),
            row=row, col=col_idx,
        )

    fig.update_layout(height=280 * n_rows, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# 5. SalePrice와의 상관관계
# ─────────────────────────────────────────────────────────────
st.header("5. 가격(SalePrice)과 수치형 특성의 상관관계")

correlations = df_num.corr()["SalePrice"].drop("SalePrice").sort_values(ascending=False)
top_corr = pd.concat([correlations.head(10), correlations.tail(5)])

fig = px.bar(
    x=top_corr.values, y=top_corr.index, orientation="h",
    color=top_corr.values, color_continuous_scale="RdBu_r",
    labels={"x": "Pearson 상관계수", "y": "특성"},
    title="SalePrice와 상관계수가 큰 상위 10개 + 음의 상관 하위 5개",
)
fig.update_layout(
    height=500, margin=dict(l=0, r=0, t=50, b=0),
    yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False,
)
st.plotly_chart(fig, use_container_width=True)

# 산점도
st.markdown("**산점도로 보는 관계**")
top_feature = st.selectbox(
    "특성 선택", options=correlations.head(10).index.tolist(), index=0
)

fig = px.scatter(
    df, x=top_feature, y="SalePrice", trendline="ols",
    color_discrete_sequence=["#d97706"],
    trendline_color_override="#1a1a1a",
    opacity=0.5,
)
fig.update_layout(height=450, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig, use_container_width=True)

st.markdown(
    """
    > 💡 **관찰**: `OverallQual`(전반적 품질), `GrLivArea`(지상 거주 면적),
    > `GarageCars`, `GarageArea`, `TotalBsmtSF` 등이 가격과 강한 양의 상관관계를 보입니다.
    > 직관적으로 "넓고 품질 좋은 집이 비싸다"는 상식과 일치합니다.
    """
)
