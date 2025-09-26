# app.py
import streamlit as st
from PIL import Image
import io
import base64
import tempfile
import os
from concurrent.futures import ThreadPoolExecutor
from agents.llm_utils import generate_narration_from_json, generate_educational_json
from agents.image_utils import encode_image_to_base64, generate_starter_frame
from agents.detect_scam import detect_scam_text, highlight_scam_text, ocr_with_openai

st.set_page_config(page_title="TruthLoop Educational Bot", layout="wide")
st.title("TruthLoop: Educational Scam Analyzer")

# -----------------------------
# Upload Section
# -----------------------------
uploaded_file = st.file_uploader("Upload an image for analysis", type=["jpg", "png", "jpeg"])

if uploaded_file:
    st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)

    # Read file once
    file_bytes = uploaded_file.read()

    # Save uploaded image temporarily
    temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    temp_input.write(file_bytes)
    temp_input.flush()
    input_path = temp_input.name

    st.info("Processing... This may take a few seconds.")

    # -----------------------------
    # OCR + Scam Detection
    # -----------------------------
    extracted_text = ocr_with_openai(file_bytes)
    scam_json = detect_scam_text(extracted_text)
    scam_phrases = scam_json.get("scam_phrases", [])

    st.subheader("Detected Scam Phrases")
    st.json(scam_json)

    # Highlight scam phrases on the image
    highlighted_image_path = highlight_scam_text(input_path, scam_phrases)
    st.subheader("Highlighted Scam Cues")
    st.image(Image.open(highlighted_image_path), use_container_width=True)

    # -----------------------------
    # Parallel Educational Processing
    # -----------------------------
    img_base64 = base64.b64encode(file_bytes).decode("utf-8")

    with ThreadPoolExecutor(max_workers=3) as executor:
        future_edu_json = executor.submit(generate_educational_json, img_base64)
        future_narration = executor.submit(generate_narration_from_json, scam_json)
        future_image = executor.submit(generate_starter_frame, extracted_text)

        edu_json = future_edu_json.result()
        narration = future_narration.result()
        edu_image_path = future_image.result()

    # -----------------------------
    # Display Results
    # -----------------------------
    st.subheader("Educational JSON")
    st.json(edu_json)

    st.subheader("Educational Narration")
    st.text(narration)

    st.subheader("Generated Educational Image")
    st.image(Image.open(edu_image_path), use_container_width=True)

    st.success("✅ Processing Complete!")

    # -----------------------------
    # Cleanup temporary files
    # -----------------------------
    for file_path in [input_path, highlighted_image_path, edu_image_path]:
        try:
            os.unlink(file_path)
        except Exception:
            pass
