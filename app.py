import io
from typing import Optional

import streamlit as st
from PIL import Image

from agri.disease_model import analyze_leaf
from agri.advisory import AdvisoryService


st.set_page_config(page_title="AgriDoc Pro", page_icon="🌿", layout="wide")


def load_image(upload) -> Optional[Image.Image]:
    if upload is None:
        return None
    try:
        bytes_data = upload.getvalue()
        return Image.open(io.BytesIO(bytes_data)).convert("RGB")
    except Exception:
        return None


def main() -> None:
    st.title("AgriDoc Pro")
    st.caption("Crop disease detection and advisory – local, private, and fast")

    advisory_service = AdvisoryService()

    with st.sidebar:
        st.header("Settings")
        crop = st.selectbox(
            "Crop (optional)",
            ["Not specified", "Tomato", "Potato", "Wheat", "Rice", "Cotton", "Maize"],
            index=0,
        )
        st.markdown("---")
        st.write("Input options")
        upload = st.file_uploader("Upload leaf image", type=["jpg", "jpeg", "png"])
        st.caption("— or —")
        camera = st.camera_input("Capture from camera (optional)")
        st.markdown("---")
        st.write("About")
        st.caption(
            "This demo uses a simple heuristic for leaf issues. Replace with an ML model in `agri/disease_model.py`."
        )

    image = load_image(camera if camera is not None else upload)

    if image is None:
        st.info("Upload or capture a leaf image to begin.")
        return

    col_left, col_right = st.columns([1, 1])
    with col_left:
        st.subheader("Input")
        st.image(image, caption="Uploaded image", use_column_width=True)

    with col_right:
        st.subheader("Analysis")
        result = analyze_leaf(image)
        label = result.get("label", "Unknown")
        confidence = float(result.get("confidence", 0.0))
        metrics = result.get("metrics", {})

        st.metric("Prediction", label, f"{confidence*100:.0f}% confidence")

        with st.expander("Detection metrics"):
            green = float(metrics.get("green_fraction", 0.0))
            spots = float(metrics.get("spot_fraction", 0.0))
            powdery = float(metrics.get("powdery_fraction", 0.0))
            yellow = float(metrics.get("yellow_fraction", 0.0))

            st.write(f"Green area: {green*100:.1f}%")
            st.progress(min(max(green, 0.0), 1.0))
            st.write(f"Spot coverage: {spots*100:.1f}%")
            st.progress(min(max(spots, 0.0), 1.0))
            st.write(f"Powdery coverage: {powdery*100:.1f}%")
            st.progress(min(max(powdery, 0.0), 1.0))
            st.write(f"Yellowing: {yellow*100:.1f}%")
            st.progress(min(max(yellow, 0.0), 1.0))

        st.markdown("---")
        st.subheader("Advisory")
        crop_value = None if crop == "Not specified" else crop
        advice = advisory_service.get_advice(label, crop=crop_value)

        if advice is None:
            st.warning("No advisory found for this condition.")
        else:
            st.write(f"**Condition:** {advice.get('name', label)}")
            if advice.get("summary"):
                st.caption(advice["summary"])
            if advice.get("symptoms"):
                st.write("Symptoms")
                for s in advice["symptoms"]:
                    st.write(f"- {s}")
            if advice.get("management"):
                st.write("Management")
                for m in advice["management"]:
                    st.write(f"- {m}")
            if advice.get("organic"):
                st.write("Organic options")
                for o in advice["organic"]:
                    st.write(f"- {o}")
            if advice.get("chemicals"):
                st.write("Chemical options (use responsibly)")
                for c in advice["chemicals"]:
                    st.write(f"- {c}")


if __name__ == "__main__":
    main()


