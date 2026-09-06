from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

# Embeddings stay on Google Gemini — Groq does not offer an embeddings API.
# Text generation uses Groq (see app/core/llm.py); embeddings have their own
# generous free quota on Google AI Studio.
embedding_model = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    output_dimensionality=768,

)


async def get_embedding(text: str) -> list[float]:
    result = await embedding_model.aembed_query(text)
    return result