
import csv
import io
import re
from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw

st.set_page_config(page_title="Candidate Review", layout="wide")
st.title("\uD574\uC591 \uB0B4\uBD80\uD30C AI \uD0D0\uC9C0 \uD6C4\uBCF4 \uAC80\uC99D")
st.warning("AI detection candidates are not confirmed internal waves.")

csv_path = Path("results/final_report/final_ai_candidates.csv")
image_path = Path("results/region_crops/gunsan_20170507_web.jpg")

if not csv_path.exists() or not image_path.exists():
    st.error("Required research files are missing.")
    st.stop()

with csv_path.open(encoding="utf-8-sig", newline="") as f:
    candidates = list(csv.DictReader(f))

labels = ["UNREVIEWED", "INTERNAL_WAVE", "NOT_INTERNAL_WAVE", "UNCERTAIN"]

if "review_labels" not in st.session_state:
    st.session_state.review_labels = {
        c["candidate_id"]: c.get("review_label", "UNREVIEWED")
        for c in candidates
    }

selected_id = st.selectbox(
    "\uD0D0\uC9C0 \uD6C4\uBCF4 \uC120\uD0DD",
    [c["candidate_id"] for c in candidates]
)

candidate = next(c for c in candidates if c["candidate_id"] == selected_id)

match = re.search(r"_x(\d+)_y(\d+)", candidate["tile"])

if match:
    tx, ty = map(int, match.groups())

    with Image.open(image_path) as im:
        image = im.convert("RGB")

    sx = image.width / 7206
    sy = image.height / 6491

    x1 = int((tx + float(candidate["x1"])) * sx)
    y1 = int((ty + float(candidate["y1"])) * sy)
    x2 = int((tx + float(candidate["x2"])) * sx)
    y2 = int((ty + float(candidate["y2"])) * sy)

    pad = 60
    box = (
        max(0, x1-pad),
        max(0, y1-pad),
        min(image.width, x2+pad),
        min(image.height, y2+pad)
    )

    crop = image.crop(box)
    draw = ImageDraw.Draw(crop)
    draw.rectangle(
        [(x1-box[0], y1-box[1]), (x2-box[0], y2-box[1])],
        outline="red",
        width=3
    )

    st.image(crop, caption=selected_id, use_container_width=True)

st.metric("AI confidence", candidate["score"])

label = st.radio(
    "\uAC80\uC99D \uACB0\uACFC",
    labels,
    index=labels.index(st.session_state.review_labels.get(selected_id, "UNREVIEWED")),
    format_func=lambda x: {
        "UNREVIEWED": "\uBBF8\uAC80\uC99D",
        "INTERNAL_WAVE": "\uB0B4\uBD80\uD30C",
        "NOT_INTERNAL_WAVE": "\uB0B4\uBD80\uD30C \uC544\uB2D8",
        "UNCERTAIN": "\uD310\uB2E8 \uBCF4\uB958"
    }[x],
    key=f"review_{selected_id}"
)

st.session_state.review_labels[selected_id] = label

counts = {
    k: sum(v == k for v in st.session_state.review_labels.values())
    for k in labels
}

cols = st.columns(4)
for col, key in zip(cols, labels):
    col.metric(key, counts[key])

output = []
for c in candidates:
    row = dict(c)
    row["review_label"] = st.session_state.review_labels[c["candidate_id"]]
    output.append(row)

buffer = io.StringIO()
writer = csv.DictWriter(buffer, fieldnames=output[0].keys())
writer.writeheader()
writer.writerows(output)

st.download_button(
    "\uAC80\uC99D \uACB0\uACFC CSV \uB2E4\uC6B4\uB85C\uB4DC",
    data=buffer.getvalue().encode("utf-8-sig"),
    file_name="gunsan_reviewed_candidates.csv",
    mime="text/csv"
)

st.caption("Reviews are stored in this browser session until downloaded. Download the CSV before leaving.")
