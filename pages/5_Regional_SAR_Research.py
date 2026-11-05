
import csv
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="지역별 SAR 연구 결과", page_icon="??", layout="wide")
st.title("지역별 SAR 연구 결과")
st.caption("Sentinel-1 SAR | 2014?2023 | Faster R-CNN")

region_file = Path("data/westsea_regions.csv")
summary_file = Path("results/final_report/final_detection_summary.csv")
candidate_file = Path("results/final_report/final_ai_candidates.csv")
preview_file = Path("results/region_crops/gunsan_20170507_web.jpg")
detection_file = Path("results/region_crops/gunsan_ai_candidates_web.jpg")

if region_file.exists():
    with region_file.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    cols = st.columns(3)
    for col, region in zip(cols, ["Gunsan", "Eocheongdo", "WestSea"]):
        count = sum(str(r.get(region, "")).strip() == "1" for r in rows)
        col.metric(region, count)
else:
    st.warning("Region classification data not found.")

region = st.selectbox("연구 해역 선택", ["Gunsan", "Eocheongdo", "WestSea"])

if region == "Gunsan":
    st.subheader("군산 SAR 및 AI 탐지 결과")


    st.subheader("SAR / AI Detection Comparison")

    left, right = st.columns(2)

    with left:
        if preview_file.exists():
            st.image(str(preview_file), caption="Original SAR", use_container_width=True)

    with right:
        if detection_file.exists():
            st.image(str(detection_file), caption="AI Detection Candidates", use_container_width=True)
        else:
            st.warning("AI detection visualization not found.")

    st.caption("Detection boxes represent unverified AI candidates.")

    if summary_file.exists():
        with summary_file.open(encoding="utf-8-sig", newline="") as f:
            summary = next(csv.DictReader(f), None)

        if summary:
            st.metric("AI 탐지 후보", summary.get("candidate_count", "-"))
            st.metric("탐지 후보가 있는 타일", summary.get("unique_tiles", "-"))
            st.warning("AI 탐지 후보 are not confirmed internal waves.")

    if candidate_file.exists():
        with candidate_file.open(encoding="utf-8-sig", newline="") as f:
            candidates = list(csv.DictReader(f))
        st.dataframe(candidates, use_container_width=True)

else:
    st.subheader(region)
    st.info("SAR 영상 분류 자료는 확보되었으나 AI 탐지 결과는 추가 검증이 필요합니다.")
