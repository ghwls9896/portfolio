"""
데이터 로딩 및 캐싱 유틸리티
Kaggle House Prices 데이터셋(train.csv, test.csv)을 로드합니다.
파일이 없을 경우 사용자에게 안내합니다.
"""

import os
import pandas as pd
import streamlit as st

# 데이터 파일 경로 후보 (여러 위치를 순서대로 시도)
DATA_PATH_CANDIDATES = [
    "./data",
    "../data",
    "./input/house-prices-advanced-regression-techniques",
    "../input/house-prices-advanced-regression-techniques",
]


def find_data_dir():
    """train.csv가 존재하는 데이터 디렉토리를 찾는다."""
    for path in DATA_PATH_CANDIDATES:
        if os.path.exists(os.path.join(path, "train.csv")):
            return path
    return None


@st.cache_data
def load_train_data():
    """학습 데이터를 로드한다."""
    data_dir = find_data_dir()
    if data_dir is None:
        return None
    path = os.path.join(data_dir, "train.csv")
    df = pd.read_csv(path)
    return df


@st.cache_data
def load_test_data():
    """테스트 데이터를 로드한다."""
    data_dir = find_data_dir()
    if data_dir is None:
        return None
    path = os.path.join(data_dir, "test.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    return df


def data_availability_check():
    """데이터 파일 존재 여부를 확인하고, 없으면 안내 메시지를 띄운다."""
    data_dir = find_data_dir()
    if data_dir is None:
        st.error("⚠️ 데이터 파일을 찾을 수 없습니다.")
        st.markdown(
            """
            **데이터 준비 방법:**

            1. [Kaggle House Prices 대회 페이지](https://www.kaggle.com/competitions/house-prices-advanced-regression-techniques/data)에서
               `train.csv`, `test.csv`, `sample_submission.csv`를 다운로드합니다.
            2. 다운로드한 파일을 다음 경로 중 하나에 배치합니다:
               - `./data/`
               - `../input/house-prices-advanced-regression-techniques/`
            3. 앱을 다시 실행하면 자동으로 데이터를 인식합니다.
            """
        )
        return False
    return True
