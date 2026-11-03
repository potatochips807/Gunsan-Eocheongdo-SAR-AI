import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="AI 모델 성능 비교", layout="wide")
st.title("Faster R-CNN 해양 내부파 탐지 성능 비교")

csv_path = Path("results/model_evaluation_results.csv")

if not csv_path.exists():
    st.warning("저장된 평가 결과가 없습니다. 먼저 evaluate_model.py를 실행하세요.")
    st.stop()

df = pd.read_csv(csv_path)

st.subheader("모델 평가 이력")
st.dataframe(df, use_container_width=True)

full_df = df[df["evaluated_images"] == 75].copy()

if full_df.empty:
    st.info("검증 영상 75장 전체 평가 결과가 아직 없습니다.")
    st.stop()

latest = full_df.sort_values("evaluated_at").drop_duplicates(
    subset=["model"], keep="last"
)

chart_df = latest.set_index("model")[
    ["map_50", "map_50_95", "mar_100"]
]

st.subheader("모델별 성능 비교")
st.bar_chart(chart_df)

st.subheader("평가 결과 다운로드")
st.download_button(
    "평가 결과 CSV 다운로드",
    data=df.to_csv(index=False).encode("utf-8-sig"),
    file_name="model_evaluation_results.csv",
    mime="text/csv"
)
