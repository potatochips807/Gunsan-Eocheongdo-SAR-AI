
import csv
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="Regional SAR Research", page_icon="??", layout="wide")
st.title("Regional SAR Research")
st.caption("Sentinel-1 SAR | 2014?2023 | Faster R-CNN")

region_file = Path("data/westsea_regions.csv")
summary_file = Path("results/final_report/final_detection_summary.csv")
candidate_file = Path("results/final_report/final_ai_candidates.csv")
preview_file = Path("results/region_crops/gunsan_20170507_web.jpg")

if region_file.exists():
    with region_file.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    cols = st.columns(3)
    for col, region in zip(cols, ["Gunsan", "Eocheongdo", "WestSea"]):
        count = sum(str(r.get(region, "")).strip() == "1" for r in rows)
        col.metric(region, count)
else:
    st.warning("Region classification data not found.")

region = st.selectbox("Select region", ["Gunsan", "Eocheongdo", "WestSea"])

if region == "Gunsan":
    st.subheader("Gunsan SAR and AI Detection Results")

    if preview_file.exists():
        st.image(str(preview_file), caption="Gunsan SAR - 2017-05-07")

    if summary_file.exists():
        with summary_file.open(encoding="utf-8-sig", newline="") as f:
            summary = next(csv.DictReader(f), None)

        if summary:
            st.metric("AI candidates", summary.get("candidate_count", "-"))
            st.metric("Tiles with candidates", summary.get("unique_tiles", "-"))
            st.warning("AI candidates are not confirmed internal waves.")

    if candidate_file.exists():
        with candidate_file.open(encoding="utf-8-sig", newline="") as f:
            candidates = list(csv.DictReader(f))
        st.dataframe(candidates, use_container_width=True)

else:
    st.subheader(region)
    st.info("SAR scene classification is available. AI detection results require verification.")
