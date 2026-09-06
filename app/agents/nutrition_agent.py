from typing import TypedDict, cast

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.schemas.meal import MealDraft
from app.services.food_retrieval_service import retrieve_similar_foods

load_dotenv()

class ParsedMeal(BaseModel):
    is_confident: bool = Field(description="True if you have enough information to give a reasonable nutrition estimate. False if the input is too vague (e.g. 'kuch khaya', 'khana khaya') to estimate meaningfully.")
    clarification_question: str | None = Field(default=None, description="If is_confident is False, ask ONE specific question to get the missing detail (e.g. 'Kya khaya tha aur kitni matra mein?'). Otherwise null.")
    food_name: str | None = Field(default=None, description="Combined/summarized name of the meal — only if confident")
    meal_type: str | None = Field(default=None, description="breakfast, lunch, dinner, or snack — infer from context if not given")
    calories: float | None = Field(default=None, description="Total estimated calories — only if confident")
    protein_g: float | None = Field(default=None, description="Total estimated protein in grams — only if confident")
    carbs_g: float | None = Field(default=None, description="Total estimated carbs in grams — only if confident")
    fats_g: float | None = Field(default=None, description="Total estimated fats in grams — only if confident")
    reasoning: str | None = Field(default=None, description="Brief explanation of estimation — only if confident")


class AgentState(TypedDict):
    raw_text: str
    meal_type_hint: str | None
    retrieved_context: str | None 
    parsed_meal: ParsedMeal | None


llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.2,
    max_retries=0,
)

structured_llm = llm.with_structured_output(ParsedMeal)

async def retrieve_context_node(state: AgentState) -> AgentState:
    async with AsyncSessionLocal() as db:
        foods = await retrieve_similar_foods(db, state["raw_text"], limit=3)

    if not foods:
        state["retrieved_context"] = None
        return state

    context_lines = [
        f"- {f.name}: {f.description} → {f.calories} kcal, {f.protein_g}g protein, {f.carbs_g}g carbs, {f.fats_g}g fats"
        for f in foods
    ]
    state["retrieved_context"] = "\n".join(context_lines)
    return state

def parse_meal_node(state: AgentState) -> AgentState:
    meal_type_context = f" (User indicated meal type: {state['meal_type_hint']})" if state.get("meal_type_hint") else ""

    retrieved_section = ""
    if state.get("retrieved_context"):
        retrieved_section = f"""
Here is verified nutrition data for similar foods from a trusted database — use these as reference points for your estimate when they closely match what the user described:
{state['retrieved_context']}
"""

    prompt = f"""You are a nutrition estimation assistant for a fitness app.
A user described what they ate in natural language (likely Pakistani/South Asian food, Roman Urdu or English).
Identify the food items and their approximate quantities, then estimate total nutrition for the ENTIRE meal combined.

User's input: "{state['raw_text']}"{meal_type_context}
{retrieved_section}
First, decide if the input has ENOUGH detail to estimate nutrition. If NOT enough: set is_confident=False, ask a clarification_question. If enough: set is_confident=True and estimate, using the verified reference data above when it closely matches the described food (scale it to the user's stated quantity), and your general knowledge otherwise.
"""

    result = structured_llm.invoke(prompt)
    state["parsed_meal"] = cast(ParsedMeal, result)
    return state

graph = StateGraph(AgentState)
graph.add_node("retrieve_context", retrieve_context_node)
graph.add_node("parse_meal", parse_meal_node)
graph.set_entry_point("retrieve_context")
graph.add_edge("retrieve_context", "parse_meal")
graph.add_edge("parse_meal", END)

nutrition_agent = graph.compile()


async def parse_meal_text(raw_text: str, meal_type_hint: str | None = None) -> ParsedMeal:
    result = await nutrition_agent.ainvoke({
        "raw_text": raw_text,
        "meal_type_hint": meal_type_hint,
        "retrieved_context": None,
        "parsed_meal": None,
    })
    return result["parsed_meal"]


def build_adjust_prompt(previous_draft: "MealDraft", adjustment_text: str) -> str:
    return f"""You are a nutrition estimation assistant for a fitness app.
You previously estimated this meal:

Original description: "{previous_draft.raw_text}"
Your estimate: {previous_draft.food_name} — {previous_draft.calories} kcal, {previous_draft.protein_g}g protein, {previous_draft.carbs_g}g carbs, {previous_draft.fats_g}g fats
Your reasoning: {previous_draft.reasoning}

The user now says: "{adjustment_text}"

Adjust your estimate based on this feedback (e.g. if they say quantity was more/less, or they add/remove an item).
If the feedback is clear enough, set is_confident=True and give the updated estimate.
If the feedback is still too vague to adjust meaningfully, set is_confident=False and ask ONE specific clarification_question.
"""


async def adjust_meal_draft(previous_draft, adjustment_text: str) -> ParsedMeal:
    prompt = build_adjust_prompt(previous_draft, adjustment_text)
    result = await structured_llm.ainvoke(prompt)
    return cast(ParsedMeal, result)