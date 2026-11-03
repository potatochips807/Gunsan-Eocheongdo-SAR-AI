import io
import csv
import numpy as np
import streamlit as st

from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, sobel

st.set_page_config(
    page_title="SAR 자동 후보 분석",
    page_icon="🔎",
    layout="wide"
)

st.title("🔎 SAR 자동 후보 분석")
st.write("영상의 방향성 패턴을 분석하여 검토할 영역을 표시합니다.")
st.warning(
    "이 기능은 내부파 확정 탐지가 아닙니다. "
    "Faster R-CNN 학습 전의 실험적 후보 선별 기능입니다."
)

def coherence_score(image):
    arr = np.asarray(image, dtype=np.float32) / 255.0

    smooth = gaussian_filter(arr, sigma=3)

    gx = sobel(smooth, axis=1)
    gy = sobel(smooth, axis=0)

    jxx = np.mean(gx * gx)
    jyy = np.mean(gy * gy)
    jxy = np.mean(gx * gy)

    numerator = np.sqrt(
        (jxx - jyy) ** 2 + 4 * jxy ** 2
    )

    denominator = jxx + jyy + 1e-12

    return float(numerator / denominator)


uploaded = st.file_uploader(
    "SAR PNG/JPG 영상 업로드",
    type=["png", "jpg", "jpeg"]
)

tile_size = st.selectbox(
    "분석 영역 크기",
    [64, 128, 256],
    index=1
)

threshold = st.slider(
    "방향성 점수 기준 (실험용)",
    0.0, 1.0, 0.15, 0.01
)

if uploaded is not None:
    image = Image.open(io.BytesIO(uploaded.getvalue())).convert("L")

    width, height = image.size
    st.write(f"영상 크기: {width} × {height}")

    if st.button("자동 후보 분석 시작", type="primary"):

        candidates = []

        for y in range(0, height - tile_size + 1, tile_size):
            for x in range(0, width - tile_size + 1, tile_size):

                patch = image.crop((
                    x, y,
                    x + tile_size,
                    y + tile_size
                ))

                score = coherence_score(patch)

                if score >= threshold:
                    candidates.append({
                        "x_min": x,
                        "y_min": y,
                        "x_max": x + tile_size,
                        "y_max": y + tile_size,
                        "coherence": round(score, 4),
                        "status": "UNVERIFIED"
                    })

        result = image.convert("RGB")
        draw = ImageDraw.Draw(result)

        for item in candidates:
            box = (
                item["x_min"],
                item["y_min"],
                item["x_max"] - 1,
                item["y_max"] - 1
            )

            draw.rectangle(box, outline="lime", width=3)

            draw.text(
                (box[0] + 4, box[1] + 4),
                f'{item["coherence"]:.2f}',
                fill="yellow"
            )

        st.session_state.auto_result = result
        st.session_state.auto_candidates = candidates
        st.session_state.auto_file = uploaded.name
        st.session_state.auto_tile = tile_size
        st.session_state.auto_threshold = threshold

    if (
        "auto_result" in st.session_state
        and st.session_state.get("auto_file") == uploaded.name
        and st.session_state.get("auto_tile") == tile_size
        and st.session_state.get("auto_threshold") == threshold
    ):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("원본 SAR 영상")
            st.image(image, use_container_width=True)

        with col2:
            st.subheader("자동 후보 분석 결과")
            st.image(
                st.session_state.auto_result,
                use_container_width=True
            )

        candidates = st.session_state.auto_candidates

        st.metric("검토 대상 영역", len(candidates))

        if candidates:
            st.dataframe(candidates, use_container_width=True)

        buffer = io.BytesIO()
        st.session_state.auto_result.save(buffer, format="PNG")

        st.download_button(
            "분석 결과 PNG 다운로드",
            data=buffer.getvalue(),
            file_name="sar_auto_candidates.png",
            mime="image/png"
        )

        csv_buffer = io.StringIO()
        fields = [
            "x_min", "y_min", "x_max", "y_max",
            "coherence", "status"
        ]

        writer = csv.DictWriter(csv_buffer, fieldnames=fields)
        writer.writeheader()
        writer.writerows(candidates)

        st.download_button(
            "후보 좌표 CSV 다운로드",
            data=csv_buffer.getvalue().encode("utf-8-sig"),
            file_name="sar_auto_candidates.csv",
            mime="text/csv"
        )

        st.caption(
            "초록색 사각형은 방향성 기준을 통과한 타일입니다. "
            "실제 내부파 위치 또는 AI 탐지 결과가 아닙니다."
        )
