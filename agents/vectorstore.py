from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
db = Chroma(persist_directory="meme_db", embedding_function=embeddings)

def store_meme(text_entry: str):
    db.add_texts([text_entry])
    db.persist()
    return "✅ Meme stored in vector DB"
