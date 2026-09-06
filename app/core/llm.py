import json

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from pydantic import SecretStr

from app.core.config import settings

GROQ_MODEL = "openai/gpt-oss-120b"
GEMINI_MODEL = "gemini-3.6-flash"


def json_schema_instruction(model_cls) -> str:
    """Tells the model to reply with a JSON object following the exact schema.

    Used with structured-output in json_mode — without the schema in the prompt
    the model guesses field names, so we always pass it explicitly.
    """
    schema = json.dumps(model_cls.model_json_schema())
    return f"Respond in JSON format with exactly this schema:\n{schema}"


def get_llm(temperature: float = 0.2, model: str = GROQ_MODEL):
    """Primary LLM for all agents: Groq free tier (high rate limits, no card).

    Gemini code kept below as a reference fallback — add GEMINI_API_KEY usage
    only if needed.
    """
    key = settings.GROQ_API_KEY
    if key:
        return ChatGroq(
            model=model,
            groq_api_key=SecretStr(key),
            temperature=temperature,
            max_retries=0,
        )

    # ------------------------------------------------------------------
    # Gemini (previous provider — kept for reference, comment disabled):
    # ------------------------------------------------------------------
    # return ChatGoogleGenerativeAI(
    #     model=GEMINI_MODEL,
    #     google_api_key=settings.GEMINI_API_KEY,
    #     temperature=temperature,
    #     max_retries=0,
    # )

    raise RuntimeError(
        "No AI provider configured. Add GROQ_API_KEY to .env "
        "(or re-enable the Gemini block in app/core/llm.py)."
    )