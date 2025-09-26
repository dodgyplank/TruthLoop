import base64
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()  # Load .env automatically
client = OpenAI()

def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def generate_starter_frame(script_text: str, output_path="starter_frame.png"):
    """
    Generates a single neutral starter frame for an educational video
    using OpenAI's DALL·E 3 model.
    """
    # Use API key from environment
    client = OpenAI()

    prompt = (
        f"Create a neutral, realistic image representing the following educational scenario: '{script_text}'. "
        "No humor, no memes, no bright colors. "
        "Keep it coherent and factual, suitable as a starter frame for an educational video."
    )

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        response_format="b64_json"
    )

    image_b64 = response.data[0].b64_json

    # Save image to disk
    with open(output_path, "wb") as f:
        f.write(base64.b64decode(image_b64))

    return output_path


