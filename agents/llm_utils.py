import re, json
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

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