
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

        st.subheader("AI confidence filter")

        threshold = st.slider(
            "Minimum AI confidence",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.05
        )

        filtered = [
            c for c in candidates
            if float(c["score"]) >= threshold
        ]

        st.metric("Filtered candidates", len(filtered))

        st.dataframe(
            filtered,
            use_container_width=True
        )

        st.subheader("Candidate detail viewer")

        if filtered:
            import re
            from PIL import Image, ImageDraw

            ids = [c["candidate_id"] for c in filtered]
            selected_id = st.selectbox("Select candidate", ids)

            selected = next(
                c for c in filtered
                if c["candidate_id"] == selected_id
            )

            match = re.search(
                r"_x(\d+)_y(\d+)",
                selected["tile"]
            )

            if match:
                tile_x = int(match.group(1))
                tile_y = int(match.group(2))

                x1 = tile_x + float(selected["x1"])
                y1 = tile_y + float(selected["y1"])
                x2 = tile_x + float(selected["x2"])
                y2 = tile_y + float(selected["y2"])

                raw_path = Path(
                    "results/region_crops/gunsan_20170507_web.jpg"
                )

                if raw_path.exists():
                    with Image.open(raw_path) as im:
                        original = im.convert("RGB")

                    scale_x = original.width / 7206
                    scale_y = original.height / 6491

                    x1 = int(x1 * scale_x)
                    y1 = int(y1 * scale_y)
                    x2 = int(x2 * scale_x)
                    y2 = int(y2 * scale_y)

                    padding = 40

                    crop_box = (
                        max(0, x1 - padding),
                        max(0, y1 - padding),
                        min(original.width, x2 + padding),
                        min(original.height, y2 + padding)
                    )

                    cropped = original.crop(crop_box)

                    draw = ImageDraw.Draw(cropped)
                    draw.rectangle(
                        [
                            (x1 - crop_box[0], y1 - crop_box[1]),
                            (x2 - crop_box[0], y2 - crop_box[1])
                        ],
                        outline="red",
                        width=3
                    )

                    st.image(
                        cropped,
                        caption=selected_id,
                        use_container_width=True
                    )

                    st.metric(
                        "AI confidence",
                        round(float(selected["score"]), 4)
                    )
        else:
            st.info("No candidates match this threshold.")



else:
    st.subheader(region)
    st.info("SAR 영상 분류 자료는 확보되었으나 AI 탐지 결과는 추가 검증이 필요합니다.")
