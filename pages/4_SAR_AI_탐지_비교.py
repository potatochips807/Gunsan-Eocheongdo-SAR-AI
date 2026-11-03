import streamlit as st
import torch
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw
from pathlib import Path
from io import BytesIO

from torchvision.models.detection import fasterrcnn_mobilenet_v3_large_320_fpn
from torchvision.transforms.functional import to_tensor, resize

st.set_page_config(
    page_title="SAR 내부파 AI 탐지 비교",
    layout="wide"
)

st.title("SAR 해양 내부파 AI 탐지 전후 비교")
st.write("원본 SAR 영상과 Faster R-CNN 탐지 결과를 비교합니다.")

MODEL_PATH = Path("results/models/faster_rcnn_full_latest.pth")

@st.cache_resource
def load_model(path, modified_time):
    model = fasterrcnn_mobilenet_v3_large_320_fpn(
        weights=None,
        weights_backbone=None,
        num_classes=2,
        min_size=256,
        max_size=256
    )

    state = torch.load(
        path,
        map_location="cpu",
        weights_only=True
    )

    model.load_state_dict(state)
    model.eval()
    return model

uploaded = st.file_uploader(
    "SAR 영상 업로드",
    type=["png", "jpg", "jpeg"]
)

threshold = st.slider(
    "탐지 신뢰도",
    min_value=0.0,
    max_value=1.0,
    value=0.3,
    step=0.05
)

if uploaded is not None:
    image = Image.open(uploaded).convert("RGB")

    if st.button("AI 탐지 및 비교"):
        if not MODEL_PATH.exists():
            st.error(f"모델 파일이 없습니다: {MODEL_PATH}")
            st.stop()

        with st.spinner("AI 모델 분석 중..."):
            model = load_model(
                str(MODEL_PATH),
                MODEL_PATH.stat().st_mtime
            )

            original_width, original_height = image.size

            tensor = resize(to_tensor(image), [256, 256])

            with torch.inference_mode():
                prediction = model([tensor])[0]

            result_image = image.copy()
            draw = ImageDraw.Draw(result_image)

            records = []

            for box, score in zip(
                prediction["boxes"].cpu().tolist(),
                prediction["scores"].cpu().tolist()
            ):
                if score < threshold:
                    continue

                x1, y1, x2, y2 = box

                x1 *= original_width / 256
                x2 *= original_width / 256
                y1 *= original_height / 256
                y2 *= original_height / 256

                draw.rectangle(
                    [x1, y1, x2, y2],
                    outline="red",
                    width=3
                )

                records.append({
                    "x1": round(x1, 2),
                    "y1": round(y1, 2),
                    "x2": round(x2, 2),
                    "y2": round(y2, 2),
                    "confidence": round(score, 4)
                })

        st.success("AI 탐지 완료")

        left, right = st.columns(2)

        with left:
            st.subheader("원본 SAR 영상")
            st.image(image, use_container_width=True)

        with right:
            st.subheader("AI 내부파 탐지 결과")
            st.image(result_image, use_container_width=True)

        st.write(f"탐지된 후보 영역: {len(records)}개")

        if records:
            df = pd.DataFrame(records)
            st.dataframe(df, use_container_width=True)

            csv_data = df.to_csv(index=False).encode("utf-8-sig")

            st.download_button(
                "탐지 좌표 CSV 다운로드",
                data=csv_data,
                file_name="sar_detection_comparison.csv",
                mime="text/csv"
            )

        buffer = BytesIO()
        result_image.save(buffer, format="PNG")

        st.download_button(
            "AI 탐지 결과 PNG 다운로드",
            data=buffer.getvalue(),
            file_name="sar_ai_comparison.png",
            mime="image/png"
        )
