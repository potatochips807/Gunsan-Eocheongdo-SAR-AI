import json
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="\uc5b4\uccad\ub3c4 \ub0b4\ubd80\ud30c \ud6c4\ubcf4 \ubd84\uc11d",
    page_icon="\U0001f30a",
    layout="wide"
)

st.title("\uc5b4\uccad\ub3c4 \ud574\uc591 \ub0b4\ubd80\ud30c \ud6c4\ubcf4 \ubd84\uc11d")
st.caption("Sentinel-1 SAR | 2022 | Gunsan / Eocheongdo")

st.warning(
    "\ud604\uc7ac \ud45c\uc2dc\ub418\ub294 \uc790\ub8cc\ub294 "
    "SAR \uc601\uc0c1\uc5d0\uc11c \uc120\uc815\ud55c "
    "\ub0b4\ubd80\ud30c \ud6c4\ubcf4\uc785\ub2c8\ub2e4. "
    "\uc2e4\uc81c \ub0b4\ubd80\ud30c\ub85c \ud655\uc815\ub41c "
    "\uacb0\uacfc\ub294 \uc544\ub2d9\ub2c8\ub2e4."
)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "results" / "website_internal_wave"

geojson_path = DATA / "eocheongdo_2022_candidates.geojson"

if not geojson_path.exists():
    st.error("\ud6c4\ubcf4 GeoJSON \ud30c\uc77c\uc744 \ucc3e\uc744 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4.")
    st.stop()

with geojson_path.open("r", encoding="utf-8") as f:
    geojson = json.load(f)

rows = []

for feature in geojson["features"]:
    props = feature["properties"]
    lon, lat = feature["geometry"]["coordinates"]

    rows.append({
        "candidate": props["id"],
        "latitude": lat,
        "longitude": lon,
        "stage": props["analysis_stage"],
        "peaks": props["peak_count"],
        "spacing_m": props["estimated_profile_spacing_m"],
        "coherence": props["mean_local_coherence"],
        "confirmed": props["internal_wave_confirmed"]
    })

df = pd.DataFrame(rows)

st.subheader("1. \ub0b4\ubd80\ud30c \ud6c4\ubcf4 \uc704\uce58 \uc9c0\ub3c4")

st.map(
    df,
    latitude="latitude",
    longitude="longitude",
    zoom=9
)

st.subheader("2. \ud6c4\ubcf4\ubcc4 \ubd84\uc11d \uacb0\uacfc")

selected = st.selectbox(
    "\ubd84\uc11d\ud560 \ud6c4\ubcf4\ub97c \uc120\ud0dd\ud558\uc138\uc694",
    df["candidate"].tolist()
)

item = df[df["candidate"] == selected].iloc[0]

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("\ud6c4\ubcf4", selected)

with c2:
    st.metric("\uc704\ub3c4", f"{item['latitude']:.6f}")

with c3:
    st.metric("\uacbd\ub3c4", f"{item['longitude']:.6f}")

st.write("\ubd84\uc11d \ub2e8\uacc4:", item["stage"])

if pd.notna(item["peaks"]):
    st.write("\ud53c\ud06c \uc218:", int(item["peaks"]))

if pd.notna(item["spacing_m"]):
    st.write(
        "\ud504\ub85c\ud30c\uc77c \ud53c\ud06c \uac04\uaca9:",
        f"{item['spacing_m']:.2f} m"
    )

if pd.notna(item["coherence"]):
    st.write(
        "\ud3c9\uade0 \uad6d\uc18c \ubc29\ud5a5\uc131 \uc77c\uad00\uc131:",
        round(float(item["coherence"]), 4)
    )

st.info(
    "\ud310\uc815: \ub0b4\ubd80\ud30c \ubbf8\ud655\uc815 "
    "- \ucd94\uac00 \ubb3c\ub9ac\uc801 \uac80\uc99d \ud544\uc694"
)

st.subheader("3. \uc804\uccb4 \ud6c4\ubcf4 \ub370\uc774\ud130")

st.dataframe(
    df,
    width="stretch",
    hide_index=True
)

st.divider()

st.subheader("4. \ud6c4\ubcf4\ubcc4 SAR \uc601\uc0c1 \ubc0f \ud328\ud134 \ubd84\uc11d")

image_root = (
    ROOT
    / "results"
    / "eocheongdo_internal_wave"
    / "additional_scenes"
)

candidate_images = {
    "CANDIDATE_A": [
        ("2022 SAR \ud6c4\ubcf4 \uc601\uc0c1",
         "step689_2022/CANDIDATE_A_2022.png"),
        ("\uc904\ubb34\ub2ac \ud328\ud134 \ubd84\uc11d",
         "step690_2022/CANDIDATE_A_wave_pattern_validation.png"),
        ("\ubc29\ud5a5\uc131 \uc77c\uad00\uc131 \ubd84\uc11d",
         "step692_2022/CANDIDATE_A_directional_coherence.png"),
        ("\ubc18\ubcf5 \uc904\ubb34\ub2ac \uac80\uc99d",
         "step693_2022/candidate_A_repeated_stripe_test.png"),
        ("2021-2022 SAR \ube44\uad50",
         "step694_2022/candidate_A_2021_vs_2022.png"),
    ],
    "CANDIDATE_B": [
        ("2022 SAR \ud6c4\ubcf4 \uc601\uc0c1",
         "step689_2022/CANDIDATE_B_2022.png"),
    ],
    "CANDIDATE_C": [
        ("2022 SAR \ud6c4\ubcf4 \uc601\uc0c1",
         "step689_2022/CANDIDATE_C_2022.png"),
        ("\uc904\ubb34\ub2ac \ud328\ud134 \ubd84\uc11d",
         "step690_2022/CANDIDATE_C_wave_pattern_validation.png"),
        ("\ubc29\ud5a5\uc131 \uc77c\uad00\uc131 \ubd84\uc11d",
         "step692_2022/CANDIDATE_C_directional_coherence.png"),
    ],
}

gallery = candidate_images.get(selected, [])

st.write(
    "\uc120\ud0dd\ud55c \ud6c4\ubcf4:",
    selected
)

if gallery:
    tabs = st.tabs([title for title, _ in gallery])

    for tab, (title, relative_path) in zip(tabs, gallery):
        with tab:
            image_path = image_root / relative_path

            if image_path.exists():
                st.image(
                    str(image_path),
                    caption=f"{selected} - {title}",
                    width="stretch"
                )
            else:
                st.warning(
                    "\uc601\uc0c1 \ud30c\uc77c \ub204\ub77d: "
                    + relative_path
                )

st.caption(
    "\uc904\ubb34\ub2ac \ud328\ud134\uacfc \ubc29\ud5a5\uc131 "
    "\ubd84\uc11d\ub9cc\uc73c\ub85c\ub294 "
    "\ud574\uc591 \ub0b4\ubd80\ud30c\ub97c \ud655\uc815\ud560 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4."
)
