"""
모델 학습 및 평가 유틸리티

원본 노트북은 TensorFlow Decision Forests의 RandomForestModel을 사용하지만,
TFDF는 환경 의존성이 매우 까다로워 (Windows 미지원, 특정 TF 버전 필요)
이 앱에서는 동일한 알고리즘 계열인 scikit-learn의 RandomForestRegressor를 사용합니다.
"""

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


def preprocess(df: pd.DataFrame, is_train: bool = True):
    """
    전처리:
      - Id 컬럼 제거
      - 범주형 변수는 category 코드로 변환
      - 결측치는 수치형은 중앙값, 범주형은 'Missing'으로 채움

    is_train=True 인 경우 SalePrice를 y로 분리하여 반환.
    """
    df = df.copy()
    if "Id" in df.columns:
        df = df.drop("Id", axis=1)

    y = None
    if is_train and "SalePrice" in df.columns:
        y = df["SalePrice"].values
        df = df.drop("SalePrice", axis=1)

    # 결측치 처리 — 수치형이 아닌 컬럼은 모두 범주형으로 인코딩
    import pandas.api.types as ptypes
    for col in df.columns:
        if ptypes.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(df[col].median())
        else:
            # object, string, category 등 모든 비수치형
            df[col] = df[col].astype("object").fillna("Missing").astype("category").cat.codes

    return df, y


@st.cache_resource(show_spinner=False)
def train_random_forest(
    _df_train: pd.DataFrame,
    n_estimators: int = 300,
    max_depth: int = None,
    min_samples_split: int = 2,
    test_size: float = 0.3,
    random_state: int = 42,
):
    """
    Random Forest 회귀 모델을 학습한다.

    Returns:
        dict: {
            'model': 학습된 모델,
            'X_train', 'X_valid', 'y_train', 'y_valid': 분할된 데이터,
            'feature_names': 컬럼명 목록,
            'predictions_valid': 검증셋 예측값,
            'metrics': 평가 지표 딕셔너리,
            'training_logs': 트리 개수별 OOB RMSE 로그
        }
    """
    X, y = preprocess(_df_train, is_train=True)
    feature_names = X.columns.tolist()

    X_train, X_valid, y_train, y_valid = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        oob_score=True,
        n_jobs=-1,
        random_state=random_state,
    )
    model.fit(X_train, y_train)

    preds_valid = model.predict(X_valid)

    # 평가 지표
    rmse = float(np.sqrt(mean_squared_error(y_valid, preds_valid)))
    mae = float(mean_absolute_error(y_valid, preds_valid))
    r2 = float(r2_score(y_valid, preds_valid))
    oob_rmse = float(np.sqrt(mean_squared_error(y_train, model.oob_prediction_)))

    # 트리 개수별 OOB RMSE 로그 (점진적으로 계산하기엔 비용이 크므로,
    # 5개 간격으로 부분 모델을 학습해서 학습 곡선을 만든다)
    training_logs = compute_training_logs(
        X_train, y_train, n_estimators, max_depth, min_samples_split, random_state
    )

    return {
        "model": model,
        "X_train": X_train,
        "X_valid": X_valid,
        "y_train": y_train,
        "y_valid": y_valid,
        "feature_names": feature_names,
        "predictions_valid": preds_valid,
        "metrics": {
            "rmse": rmse,
            "mae": mae,
            "r2": r2,
            "oob_rmse": oob_rmse,
        },
        "training_logs": training_logs,
    }


def compute_training_logs(X_train, y_train, n_estimators, max_depth, min_samples_split, random_state):
    """트리 개수에 따른 OOB RMSE 변화를 계산한다 (학습 곡선용)."""
    tree_counts = list(range(10, n_estimators + 1, max(10, n_estimators // 20)))
    if tree_counts[-1] != n_estimators:
        tree_counts.append(n_estimators)

    logs = []
    for nt in tree_counts:
        m = RandomForestRegressor(
            n_estimators=nt,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            oob_score=True,
            n_jobs=-1,
            random_state=random_state,
        )
        m.fit(X_train, y_train)
        oob_rmse = float(np.sqrt(mean_squared_error(y_train, m.oob_prediction_)))
        logs.append({"num_trees": nt, "rmse": oob_rmse})
    return logs


def predict_test(model, df_test: pd.DataFrame, train_columns: list):
    """
    학습된 모델로 test 데이터에 대한 예측을 수행한다.
    train과 컬럼 구성이 같도록 정렬한다.
    """
    ids = df_test["Id"].copy() if "Id" in df_test.columns else None
    X_test, _ = preprocess(df_test, is_train=False)

    # 학습 데이터와 동일한 컬럼/순서로 정렬
    for col in train_columns:
        if col not in X_test.columns:
            X_test[col] = 0
    X_test = X_test[train_columns]

    preds = model.predict(X_test)
    return ids, preds
