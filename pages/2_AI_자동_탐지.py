import hashlib
import io
import os

import pandas as pd
import streamlit as st
import torch

from PIL import Image, ImageDraw
from torchvision.models.detection import fasterrcnn_mobilenet_v3_large_320_fpn
from torchvision.transforms.functional import to_tensor
from torchvision.ops import nms

st.set_page_config(
    page_title="AI 내부파 자동 탐지",
    layout="wide"
)

st.title("SAR 해양 내부파 AI 자동 탐지")
st.caption("Faster R-CNN 기반 내부파 후보 영역 탐지")

MODEL_PATH = "results/models/faster_rcnn_full_latest.pth"

# STEP_496_ENVIRONMENT
import sys
import torchvision

st.caption(
    "STEP_496 PYTHON: "
    + sys.version.split()[0]
)

st.caption(
    "STEP_496 TORCH: "
    + torch.__version__
)

st.caption(
    "STEP_496 TORCHVISION: "
    + torchvision.__version__
)

st.caption(
    "STEP_496 CUDA: "
    + str(torch.cuda.is_available())
)


# STEP_489_RUNTIME_DIAGNOSTIC
if os.path.isfile(MODEL_PATH):
    with open(MODEL_PATH, "rb") as f:
        model_hash = hashlib.file_digest(
            f, "sha256"
        ).hexdigest()

    st.caption(
        "STEP_489 MODEL_SHA256: " + model_hash
    )
    st.caption(
        "STEP_489 MODEL_SIZE: "
        + str(os.path.getsize(MODEL_PATH))
    )
else:
    st.error(
        "STEP_489 MODEL_FILE_MISSING: "
        + MODEL_PATH
    )


st.info(
    "Deployment diagnostic | "
    "Model: faster_rcnn_full_latest.pth | "
    "Post-NMS IoU: 0.30 | "
    "Code version: STEP_486"
)


# STEP_499_MODEL_DIAGNOSTIC
def load_model():
    torch.set_num_threads(2)

    model = fasterrcnn_mobilenet_v3_large_320_fpn(
        weights=None,
        weights_backbone=None,
        num_classes=2,
        min_size=256,
        max_size=256
    )

    state = torch.load(
        MODEL_PATH,
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
    "탐지 신뢰도 기준",
    min_value=0.0,
    max_value=1.0,
    value=0.3,
    step=0.05
)

if uploaded is not None:

    image = Image.open(uploaded).convert("RGB")

    uploaded.seek(0)
    upload_hash = hashlib.sha256(
        uploaded.getvalue()
    ).hexdigest()

    st.caption(
        "STEP_489 UPLOAD_SHA256: " + upload_hash
    )
    st.caption(
        "STEP_489 IMAGE_SIZE: " + str(image.size)
    )


    st.image(image, caption="원본 SAR 영상", width="stretch")

    if st.button("AI 내부파 탐지 시작"):

        if not os.path.exists(MODEL_PATH):
            st.error("모델 파일을 찾을 수 없습니다.")
            st.stop()

        with st.spinner("Faster R-CNN 분석 중..."):

            model = load_model()

            tensor = to_tensor(image)

            with torch.inference_mode():
                prediction = model([tensor])[0]

                st.caption(
                    "STEP_499 RAW_BOXES: "
                    + str(len(prediction["boxes"]))
                )

                st.caption(
                    "STEP_499 RAW_SCORES_GE_030: "
                    + str(
                        int(
                            (
                                prediction["scores"] >= 0.30
                            ).sum().item()
                        )
                    )
                )

                st.caption(
                    "STEP_499 MODEL_TRAINING: "
                    + str(model.training)
                )

                st.caption(
                    "STEP_499 TENSOR_SHAPE: "
                    + str(tuple(tensor.shape))
                )

            result = image.copy()
            draw = ImageDraw.Draw(result)

            rows = []

            boxes = prediction["boxes"]
            scores = prediction["scores"]

            valid = scores >= threshold
            boxes = boxes[valid]
            scores = scores[valid]

            if len(boxes) > 0:
                keep = nms(
                    boxes,
                    scores,
                    iou_threshold=0.30
                )
                boxes = boxes[keep]
                scores = scores[keep]

            for box, score in zip(boxes, scores):

                confidence = float(score)

                if confidence < threshold:
                    continue

                x1, y1, x2, y2 = box.tolist()

                draw.rectangle(
                    [x1, y1, x2, y2],
                    outline="red",
                    width=3
                )

                draw.text(
                    (x1, y1),
                    f"{confidence:.2f}",
                    fill="red"
                )

                rows.append({
                    "x1": round(x1, 2),
                    "y1": round(y1, 2),
                    "x2": round(x2, 2),
                    "y2": round(y2, 2),
                    "confidence": round(confidence, 4)
                })

        st.caption("STEP_489 AFTER_NMS: " + str(len(rows)))
        st.success(f"AI 탐지 완료: {len(rows)}개 후보")

        st.image(
            result,
            caption="AI 내부파 탐지 결과",
            width="stretch"
        )

        df = pd.DataFrame(
            rows,
            columns=["x1", "y1", "x2", "y2", "confidence"]
        )

        st.dataframe(df, use_container_width=True)

        buffer = io.BytesIO()
        result.save(buffer, format="PNG")

        st.download_button(
            "탐지 결과 이미지 저장",
            data=buffer.getvalue(),
            file_name="ai_detection.png",
            mime="image/png"
        )

        st.download_button(
            "탐지 좌표 CSV 저장",
            data=df.to_csv(index=False).encode("utf-8-sig"),
            file_name="ai_detection.csv",
            mime="text/csv"
        )

        st.info(
            "현재 모델은 20장만 학습한 시험용 모델입니다. "
            "표시된 영역은 검증된 내부파가 아닌 AI 탐지 후보입니다."
        )
