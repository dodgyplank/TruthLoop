import re, json
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

def generate_educational_json(img_base64: str) -> dict:
    """
    Analyze uploaded image and generate neutral educational description.
    Returns: caption, tags, scam_type, category.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are an educational assistant. Analyze the given image and return a short, neutral description. "
                "Return caption, tags, scam_type, and category in JSON format ONLY. "
                "Do NOT include humor, emojis, or extra text. "
                "If scam_type is not applicable, set it to 'Unknown'."
            )
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
            ]
        }
    ]

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.3
    )

    raw_output = response.choices[0].message.content
    match = re.search(r"\{.*\}", raw_output, re.DOTALL)
    json_text = match.group() if match else "{}"

    try:
        result = json.loads(json_text)
    except json.JSONDecodeError:
        result = {"caption": raw_output, "tags": [], "scam_type": "Unknown", "category": "Unknown"}

    # Ensure all keys exist
    result = {
        "caption": result.get("caption", ""),
        "tags": result.get("tags", []),
        "scam_type": result.get("scam_type", "Unknown"),
        "category": result.get("category", "Unknown")
    }
    
    return result

def generate_narration_from_json(scam_json: dict) -> str:
    """
    Converts the educational JSON content into TTS-ready narration, 
    highlighting why it is a scam and identifying key words or cues that indicate the scam.
    """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", 
         "You are a narration assistant for educational videos. "
         "Transform the scam JSON content into clear, neutral, and concise narration suitable for TTS. "
         "Explain why the content is obviously a scam, and highlight key words, phrases, or cues that indicate the scam. "
         "Do NOT include humor, emojis, or formatting."),
        ("user", 
         "Use the following scam JSON to generate the narration:\n\n{scam_json}")
    ])
    
    messages = prompt_template.format_messages(scam_json=json.dumps(scam_json, indent=2))
    response = llm.invoke(messages)
    
    return response.content.strip()