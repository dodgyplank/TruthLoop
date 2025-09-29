import re, json
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate

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

def what_if_bot(narration: str) -> str:
    """
    Converts a narration about a scam into a "what if" scenario,
    explaining the possible consequences if the user falls for it.
    """
    # Initialize the LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    
    # Create a prompt template
    prompt = ChatPromptTemplate.from_messages([
        HumanMessagePromptTemplate.from_template(
            "Given the following narration about a scam, generate a 'what if' scenario "
            "describing the consequences if a person falls for it. Be clear and concise.\n\n"
            "Narration:\n{narration}\n\nWhat if scenario:"
        )
    ])
    
    # Format the prompt with the narration
    messages = prompt.format_messages(narration=narration)
    
    # Get the LLM response
    response = llm.invoke(messages)
    
    return response.content.strip()