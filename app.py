import csv
import io
import hashlib

import numpy as np
import streamlit as st
import tifffile
from PIL import Image, ImageDraw
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(
    page_title="Ocean IW Detector",
    page_icon="🌊",
    layout="wide"
)

st.title("🌊 Ocean IW Detector")
st.subheader("SAR 위성영상을 활용한 해양 내부파 탐지 시스템")
st.info("현재는 수동 표시 기능입니다. AI 자동 탐지는 아직 구현되지 않았습니다.")


def normalize_image(arr):
    arr = np.asarray(arr, dtype=np.float32)

    if arr.ndim != 2:
        raise ValueError("단일 채널 영상만 지원합니다.")

    valid = arr[np.isfinite(arr)]

    if valid.size == 0:
        raise ValueError("유효한 영상 데이터가 없습니다.")

    low, high = np.percentile(valid, [2, 98])

    if high <= low:
        return Image.fromarray(
            np.zeros(arr.shape, dtype=np.uint8)
        )

    arr = np.nan_to_num(
        arr, nan=low, posinf=high, neginf=low
    )
    arr = np.clip((arr - low) / (high - low), 0, 1)

    return Image.fromarray((arr * 255).astype(np.uint8))


def draw_result(image, boxes, lines, points, mode):
    result = image.convert("RGB").copy()
    draw = ImageDraw.Draw(result)

    for i, box in enumerate(boxes, 1):
        draw.rectangle(box, outline="lime", width=3)
        draw.text(
            (box[0] + 4, box[1] + 4),
            f"ROI {i}",
            fill="lime"
        )

    for line in lines:
        if len(line) >= 2:
            draw.line(line, fill="yellow", width=3)

    if mode == "곡선 그리기" and len(points) >= 2:
        draw.line(points, fill="orange", width=3)

    for x, y in points:
        draw.ellipse(
            (x - 4, y - 4, x + 4, y + 4),
            fill="yellow"
        )

    return result


def refresh_canvas():
    st.session_state.canvas_version += 1
    st.rerun()


uploaded = st.file_uploader(
    "SAR 영상을 업로드하세요",
    type=["png", "jpg", "jpeg", "tif", "tiff"]
)

if uploaded is not None:

    file_bytes = uploaded.getvalue()
    file_id = hashlib.sha256(file_bytes).hexdigest()

    if st.session_state.get("file_id") != file_id:
        st.session_state.file_id = file_id
        st.session_state.boxes = []
        st.session_state.lines = []
        st.session_state.points = []
        st.session_state.canvas_version = 0
        st.session_state.mode = "사각형 그리기"

    try:
        if uploaded.name.lower().endswith((".tif", ".tiff")):
            with tifffile.TiffFile(io.BytesIO(file_bytes)) as tif:
                page = tif.pages[0]

                if len(page.shape) != 2:
                    raise ValueError("단일 채널 TIFF만 지원합니다.")

                if page.shape[0] * page.shape[1] > 16_000_000:
                    st.warning("대용량 TIFF는 PNG 패치로 시험하세요.")
                    st.stop()

                image = normalize_image(page.asarray())
        else:
            image = Image.open(
                io.BytesIO(file_bytes)
            ).convert("L")

    except Exception as e:
        st.error(f"영상 읽기 오류: {e}")
        st.stop()

    st.success("SAR 영상 업로드 완료!")
    st.write("영상 크기:", image.size)

    mode = st.radio(
        "그리기 도구",
        ["사각형 그리기", "곡선 그리기"],
        horizontal=True,
        key="mode"
    )

    if mode == "사각형 그리기":
        st.write("사각형의 두 모서리를 차례로 클릭하세요.")
    else:
        st.write("선을 따라 여러 점을 클릭하고 '곡선 완성'을 누르세요.")

    left, right = st.columns(2)

    with left:
        st.subheader("영역 선택 화면")

        preview = draw_result(
            image,
            st.session_state.boxes,
            st.session_state.lines,
            st.session_state.points,
            mode
        )

        click = streamlit_image_coordinates(
            preview,
            width=image.width,
            key=f"canvas_{st.session_state.canvas_version}"
        )

        if click is not None:
            x = max(0, min(int(click["x"]), image.width - 1))
            y = max(0, min(int(click["y"]), image.height - 1))

            st.session_state.points.append((x, y))

            if mode == "사각형 그리기" and len(st.session_state.points) == 2:
                (x1, y1), (x2, y2) = st.session_state.points

                box = (
                    min(x1, x2),
                    min(y1, y2),
                    max(x1, x2),
                    max(y1, y2)
                )

                if box[0] < box[2] and box[1] < box[3]:
                    st.session_state.boxes.append(box)

                st.session_state.points = []

            refresh_canvas()

    with right:
        st.subheader("표시 결과")

        result = draw_result(
            image,
            st.session_state.boxes,
            st.session_state.lines,
            st.session_state.points,
            mode
        )

        st.image(result, use_container_width=True)

        st.write("사각형:", len(st.session_state.boxes), "개")
        st.write("완성된 곡선:", len(st.session_state.lines), "개")
        st.write("현재 선택한 점:", len(st.session_state.points), "개")

    st.divider()
    st.subheader("그리기 관리")

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("곡선 완성"):
            if mode == "곡선 그리기" and len(st.session_state.points) >= 2:
                st.session_state.lines.append(
                    st.session_state.points.copy()
                )
                st.session_state.points = []
                refresh_canvas()
            else:
                st.warning("곡선 모드에서 점을 2개 이상 선택하세요.")

    with c2:
        if st.button("마지막 점 되돌리기"):
            if st.session_state.points:
                st.session_state.points.pop()
                refresh_canvas()

    with c3:
        if st.button("현재 선택 취소"):
            st.session_state.points = []
            refresh_canvas()

    st.subheader("개별 표시 삭제")

    if st.session_state.boxes:
        selected_box = st.selectbox(
            "삭제할 사각형",
            range(len(st.session_state.boxes)),
            format_func=lambda i: (
                f"ROI {i+1}: {st.session_state.boxes[i]}"
            )
        )

        if st.button("선택한 사각형 삭제"):
            st.session_state.boxes.pop(selected_box)
            refresh_canvas()

    if st.session_state.lines:
        selected_line = st.selectbox(
            "삭제할 곡선",
            range(len(st.session_state.lines)),
            format_func=lambda i: (
                f"곡선 {i+1}: {len(st.session_state.lines[i])}개 점"
            )
        )

        if st.button("선택한 곡선 삭제"):
            st.session_state.lines.pop(selected_line)
            refresh_canvas()

    if st.button("모든 표시 초기화"):
        st.session_state.boxes = []
        st.session_state.lines = []
        st.session_state.points = []
        refresh_canvas()

    st.divider()
    st.subheader("결과 저장")

    # 저장 시 미완성 점은 제외
    final_result = draw_result(
        image,
        st.session_state.boxes,
        st.session_state.lines,
        [],
        mode
    )

    png_buffer = io.BytesIO()
    final_result.save(png_buffer, format="PNG")

    st.download_button(
        "표시 결과 PNG 다운로드",
        data=png_buffer.getvalue(),
        file_name="sar_detection_result.png",
        mime="image/png"
    )

    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)

    writer.writerow([
        "type", "id", "point_order",
        "x1", "y1", "x2", "y2",
        "verification_status"
    ])

    for i, box in enumerate(st.session_state.boxes, 1):
        writer.writerow([
            "box", i, "",
            box[0], box[1], box[2], box[3],
            "UNVERIFIED"
        ])

    for i, line in enumerate(st.session_state.lines, 1):
        for order, (x, y) in enumerate(line, 1):
            writer.writerow([
                "line", i, order,
                x, y, "", "",
                "UNVERIFIED"
            ])

    st.download_button(
        "영역 및 곡선 CSV 다운로드",
        data=csv_buffer.getvalue().encode("utf-8-sig"),
        file_name="sar_annotations.csv",
        mime="text/csv"
    )

else:
    st.info("먼저 SAR 영상을 업로드해 주세요.")

st.divider()
st.caption("Capstone Design | Ocean Internal Wave Detector")
