from openai import OpenAI
import os
import cv2
from PIL import Image
import base64
import json
import re
import numpy as np
client = OpenAI()

def ocr_with_openai(image_bytes):
    # Convert to base64 string
    img_b64 = base64.b64encode(image_bytes).decode("utf-8")
    img_b64 = base64.b64encode(image_bytes).decode("utf-8").replace("\n", "")

    # Wrap it in a proper data URI
    data_uri = f"data:image/png;base64,{img_b64}"

    messages = [
        {
            "role": "system",
            "content": "You are an OCR assistant. Extract all text from the image."
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Extract the text from this image."},
                {"type": "image_url", "image_url": {"url": data_uri}}
            ]
        }
    ]

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0
    )

    return response.choices[0].message.content

def detect_scam_text(extracted_text: str) -> dict:
    """
    Detect scam phrases in the extracted text using OpenAI.
    Safely returns JSON even if the model output is not perfect JSON.
    """
    from openai import OpenAI
    client = OpenAI()
    
    messages = [
        {"role": "system", "content": "You are an assistant that identifies scam text in a message."},
        {"role": "user", "content": f"Identify all scam phrases and return JSON with keys: scam_phrases (list). Text: {extracted_text}"}
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0
    )

    raw_content = response.choices[0].message.content

    # Try to extract JSON from raw text
    match = re.search(r"\{.*\}", raw_content, re.DOTALL)
    json_text = match.group() if match else "{}"

    try:
        result = json.loads(json_text)
    except json.JSONDecodeError:
        # fallback if JSON parsing fails
        result = {"scam_phrases": []}

    # Ensure key exists
    if "scam_phrases" not in result:
        result["scam_phrases"] = []

    return result

import cv2
import numpy as np

def highlight_scam_text(image_path: str, scam_phrases: list, output_path="highlighted.png"):
    """
    Highlights words in the image that match scam phrases using OpenCV only.
    Works by thresholding and contour detection to approximate text bounding boxes.
    """
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not load image at {image_path}")

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Threshold to get binary image
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        roi = image[y:y+h, x:x+w]

        # Optional: Use simple template matching or average intensity heuristics
        # For now, we assume each contour may contain a word
        # Extract the region and do very naive matching using color inversion
        roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        roi_text = ""  # placeholder if you want to run OCR here later

        # Draw box if region is likely a scam word (you can extend with OCR-free heuristics)
        # For demonstration, highlight all contours:
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)

    cv2.imwrite(output_path, image)
    return output_path

