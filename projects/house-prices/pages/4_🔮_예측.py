"""
예측 페이지

학습된 모델을 사용하여:
  1. Kaggle 테스트셋 전체에 대한 일괄 예측 → submission.csv 다운로드
  2. 사용자가 직접 주요 특성값을 입력하여 단일 주택 가격 예측
"""

import io
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from utils.data_loader import load_train_data, load_test_data, data_availability_check
from utils.model import predict_test, preprocess

st.set_page_config(page_title="예측 — House Prices", page_icon="🔮", layout="wide")

st.title("🔮 예측")
st.markdown(
    "학습된 모델을 사용하여 새로운 주택 데이터의 가격을 예측합니다. "
    "**Kaggle 테스트셋 전체에 대한 일괄 예측**과, **개별 주택 조건을 입력한 인터랙티브 예측** 두 가지 모드를 제공합니다."
)
st.markdown("---")

# ─────────────────────────────────────────────────────────────
# 사전 체크
# ─────────────────────────────────────────────────────────────
if not data_availability_check():
    st.stop()

if "train_result" not in st.session_state:
    st.warning("⚠️ 먼저 **'모델 학습'** 페이지에서 모델을 학습해주세요.")
    st.stop()

result = st.session_state["train_result"]
model = result["model"]
feature_names = result["feature_names"]
df_train = load_train_data()

# ─────────────────────────────────────────────────────────────
# 탭 구성
# ─────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["📦 일괄 예측 (Kaggle 제출용)", "🏠 개별 주택 예측"])

# ═════════════════════════════════════════════════════════════
# 탭 1: 일괄 예측
# ═════════════════════════════════════════════════════════════
with tab1:
    st.header("Kaggle 테스트 데이터 일괄 예측")
    st.markdown(
        "Kaggle 대회의 `test.csv` 전체에 대해 예측을 수행하고, "
        "제출 형식(`Id, SalePrice`)의 CSV 파일을 생성합니다."
    )

    df_test = load_test_data()

    if df_test is None:
        st.error("test.csv 파일을 찾을 수 없습니다. 데이터 폴더에 test.csv를 배치해주세요.")
    else:
        st.markdown(f"**테스트 샘플 수: {len(df_test):,}개**")

        if st.button("🚀 일괄 예측 실행", type="primary"):
            with st.spinner("테스트 데이터 예측 중..."):
                ids, preds = predict_test(model, df_test, feature_names)
                submission = pd.DataFrame({"Id": ids, "SalePrice": preds})

            st.session_state["submission"] = submission
            st.success(f"✅ {len(submission):,}개 예측 완료!")

        if "submission" in st.session_state:
            submission = st.session_state["submission"]

            # 통계 요약
            st.subheader("예측 결과 요약")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("예측 개수", f"{len(submission):,}")
            with c2:
                st.metric("평균 예측가", f"${submission['SalePrice'].mean():,.0f}")
            with c3:
                st.metric("최소 예측가", f"${submission['SalePrice'].min():,.0f}")
            with c4:
                st.metric("최대 예측가", f"${submission['SalePrice'].max():,.0f}")

            # 예측 분포 비교
            st.subheader("학습셋 vs 예측 분포 비교")

            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=df_train["SalePrice"], name="학습셋 실제 가격",
                marker_color="#1a1a1a", opacity=0.6, nbinsx=50,
            ))
            fig.add_trace(go.Histogram(
                x=submission["SalePrice"], name="테스트셋 예측 가격",
                marker_color="#d97706", opacity=0.6, nbinsx=50,
            ))
            fig.update_layout(
                barmode="overlay", height=400,
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis_title="SalePrice (USD)", yaxis_title="빈도",
                plot_bgcolor="white",
                legend=dict(x=0.7, y=0.95),
            )
            fig.update_xaxes(gridcolor="#eee", tickformat="$,.0f")
            fig.update_yaxes(gridcolor="#eee")
            st.plotly_chart(fig, use_container_width=True)

            st.markdown(
                """
                > 💡 학습셋과 예측 분포가 유사한 형태를 보인다면, 모델이 학습 데이터의 패턴을
                > 잘 일반화하고 있다는 신호입니다. 예측 분포가 학습 분포보다 좁다면(분산이 작다면)
                > 트리 기반 모델의 평균화(averaging) 효과로 인한 보수적 예측일 수 있습니다.
                """
            )

            # 결과 미리보기 및 다운로드
            st.subheader("결과 미리보기 및 다운로드")

            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.dataframe(submission.head(20), use_container_width=True, hide_index=True)

            with col_b:
                csv_buffer = io.StringIO()
                submission.to_csv(csv_buffer, index=False)
                st.download_button(
                    label="📥 submission.csv 다운로드",
                    data=csv_buffer.getvalue(),
                    file_name="submission.csv",
                    mime="text/csv",
                    type="primary",
                    use_container_width=True,
                )
                st.markdown(
                    """
                    <div style="background:#fafaf7; padding:0.8rem; border-radius:6px; font-size:0.85rem; color:#555; margin-top:0.5rem;">
                    이 파일은 Kaggle 대회 페이지에서 그대로 제출할 수 있는 형식입니다.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# ═════════════════════════════════════════════════════════════
# 탭 2: 개별 주택 예측
# ═════════════════════════════════════════════════════════════
with tab2:
    st.header("개별 주택 가격 예측")
    st.markdown(
        "주요 특성값을 직접 입력하여 가격을 예측해봅니다. "
        "**변수 중요도가 높은 상위 특성**만 노출하고, 나머지는 학습셋의 중앙값/최빈값으로 자동 설정됩니다."
    )

    # 상위 중요 특성 추출
    importances = pd.DataFrame({
        "feature": feature_names,
        "importance": model.feature_importances_,
    }).sort_values("importance", ascending=False)

    # 인터랙티브하게 노출할 주요 특성 (상위 + 직관적인 것 위주)
    interactive_features = [
        ("OverallQual", "전반적 품질 (1-10)", "slider", (1, 10, 7)),
        ("GrLivArea", "지상 거주 면적 (sqft)", "number", (300, 6000, 1500)),
        ("TotalBsmtSF", "지하실 총 면적 (sqft)", "number", (0, 6000, 1000)),
        ("GarageCars", "차고 차량 수용 수", "slider", (0, 4, 2)),
        ("GarageArea", "차고 면적 (sqft)", "number", (0, 1500, 480)),
        ("YearBuilt", "건축 연도", "number", (1872, 2010, 2000)),
        ("FullBath", "전체 욕실 수", "slider", (0, 4, 2)),
        ("TotRmsAbvGrd", "지상 총 방 개수", "slider", (2, 14, 7)),
        ("1stFlrSF", "1층 면적 (sqft)", "number", (300, 4700, 1200)),
        ("LotArea", "대지 면적 (sqft)", "number", (1000, 220000, 10000)),
    ]

    # 학습 데이터 전처리해서 기본값 베이스 만들기
    X_default, _ = preprocess(df_train, is_train=True)
    base_values = X_default.median().to_dict()  # 수치는 중앙값, 인코딩된 범주도 중앙값

    st.markdown("### 주요 특성 입력")

    cols = st.columns(3)
    user_inputs = {}
    for i, (fname, label, kind, params) in enumerate(interactive_features):
        with cols[i % 3]:
            if kind == "slider":
                user_inputs[fname] = st.slider(label, params[0], params[1], params[2])
            else:
                user_inputs[fname] = st.number_input(label, params[0], params[1], params[2])

    if st.button("💰 가격 예측", type="primary"):
        # base 값에 사용자 입력 덮어쓰기
        input_row = base_values.copy()
        for k, v in user_inputs.items():
            if k in input_row:
                input_row[k] = v

        # 학습 컬럼 순서에 맞게 정렬
        X_input = pd.DataFrame([input_row])[feature_names]

        predicted = model.predict(X_input)[0]

        # 트리별 예측값으로 신뢰 구간 추정
        # (개별 estimator는 feature_names 없이 학습되므로 ndarray로 전달해 warning 방지)
        X_input_arr = X_input.values
        tree_preds = np.array([tree.predict(X_input_arr)[0] for tree in model.estimators_])
        p10, p90 = np.percentile(tree_preds, [10, 90])

        # 결과 카드
        st.markdown("---")
        st.markdown("### 예측 결과")

        col_main, col_dist = st.columns([1, 2])

        with col_main:
            st.markdown(
                f"""
                <div style="background:linear-gradient(135deg,#fafaf7 0%,#fff 100%);
                            border-left:5px solid #d97706; padding:1.5rem; border-radius:8px;">
                    <div style="font-size:0.85rem; color:#888; text-transform:uppercase; letter-spacing:0.05em;">예측 가격</div>
                    <div style="font-size:2.8rem; font-weight:700; color:#1a1a1a; line-height:1;">
                        ${predicted:,.0f}
                    </div>
                    <div style="font-size:0.95rem; color:#555; margin-top:0.5rem;">
                        80% 예측 구간: ${p10:,.0f} ~ ${p90:,.0f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # 비교 정보
            train_mean = df_train["SalePrice"].mean()
            diff_pct = (predicted - train_mean) / train_mean * 100
            sign = "+" if diff_pct >= 0 else ""
            st.markdown(
                f"""
                <div style="margin-top:1rem; padding:0.8rem 1rem; background:#fafaf7; border-radius:6px;">
                    <div style="font-size:0.85rem; color:#666;">학습셋 평균가 대비</div>
                    <div style="font-size:1.3rem; font-weight:600; color:{'#16a34a' if diff_pct >= 0 else '#dc2626'};">
                        {sign}{diff_pct:.1f}%
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_dist:
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=tree_preds, nbinsx=30,
                marker_color="#d97706", opacity=0.75,
                name="트리별 예측",
            ))
            fig.add_vline(x=predicted, line_color="#1a1a1a", line_width=2.5,
                          annotation_text=f"평균: ${predicted:,.0f}",
                          annotation_position="top")
            fig.add_vrect(x0=p10, x1=p90, fillcolor="#d97706", opacity=0.1, line_width=0,
                          annotation_text="80% 구간", annotation_position="top left")
            fig.update_layout(
                height=380, margin=dict(l=0, r=0, t=30, b=0),
                xaxis_title="예측 SalePrice (USD)", yaxis_title="트리 개수",
                plot_bgcolor="white", showlegend=False,
                title="300개 트리의 개별 예측 분포",
            )
            fig.update_xaxes(gridcolor="#eee", tickformat="$,.0f")
            fig.update_yaxes(gridcolor="#eee")
            st.plotly_chart(fig, use_container_width=True)

        st.markdown(
            """
            > 💡 **신뢰 구간 해석**: Random Forest는 여러 결정 트리의 예측을 평균하므로,
            > 각 트리의 예측이 얼마나 일치하는지를 통해 예측의 불확실성을 가늠할 수 있습니다.
            > 트리들의 예측이 좁게 분포해 있다면 모델이 확신하고 있다는 뜻이며,
            > 넓게 퍼져 있다면 입력 조건이 학습 데이터에서 멀리 떨어진 영역일 수 있습니다.
            """
        )
