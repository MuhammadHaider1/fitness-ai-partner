from typing import Literal, TypedDict, cast

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from app.agents.nutrition_agent import ParsedMeal, parse_meal_text
from app.agents.workout_agent import ParsedWorkout, parse_workout_text
from app.core.config import settings


class IntentClassification(BaseModel):
    intent: Literal["meal", "workout"] = Field(description="Classify whether the user's message describes food/eating (meal) or physical exercise/activity (workout)")


class RouterState(TypedDict):
    raw_text: str
    intent: str | None
    parsed_meal: ParsedMeal | None
    parsed_workout: ParsedWorkout | None


llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0,
)

classifier_llm = llm.with_structured_output(IntentClassification)


def classify_intent_node(state: RouterState) -> RouterState:
    prompt = f"""Classify this user message as either "meal" (they ate/drank something) or "workout" (they exercised/did physical activity).

Message: "{state['raw_text']}"
"""
    result = cast(IntentClassification, classifier_llm.invoke(prompt))
    state["intent"] = result.intent
    return state


def route_by_intent(state: RouterState) -> str:
    return "parse_meal" if state["intent"] == "meal" else "parse_workout"


async def parse_meal_node(state: RouterState) -> RouterState:
    """Duplicate logic nahi — seedha nutrition_agent.py ka RAG-enabled parser reuse karta hai"""
    state["parsed_meal"] = await parse_meal_text(state["raw_text"])
    return state


async def parse_workout_node(state: RouterState) -> RouterState:
    """Seedha workout_agent.py ka parser reuse karta hai"""
    state["parsed_workout"] = await parse_workout_text(state["raw_text"])
    return state


def validate_result_node(state: RouterState) -> RouterState:
    """Defensive check: agar is_confident=True hai lekin critical fields missing hain
    (structured output ka rare edge case), to safely downgrade kar do is_confident=False mein
    taake user ko kabhi broken data na mile."""

    if state["intent"] == "meal" and state["parsed_meal"] is not None:
        meal = state["parsed_meal"]
        if meal.is_confident and meal.calories is None:
            meal.is_confident = False
            meal.clarification_question = meal.clarification_question or "Could not confidently estimate this meal — could you describe it with a bit more detail?"

    elif state["intent"] == "workout" and state["parsed_workout"] is not None:
        workout = state["parsed_workout"]
        if workout.is_confident and workout.calories_burned is None:
            workout.is_confident = False
            workout.clarification_question = workout.clarification_question or "Could not confidently estimate this workout — could you share the duration or sets/reps?"

    return state


graph = StateGraph(RouterState)
graph.add_node("classify_intent", classify_intent_node)
graph.add_node("parse_meal", parse_meal_node)
graph.add_node("parse_workout", parse_workout_node)
graph.add_node("validate_result", validate_result_node)

graph.set_entry_point("classify_intent")
graph.add_conditional_edges("classify_intent", route_by_intent, {
    "parse_meal": "parse_meal",
    "parse_workout": "parse_workout",
})
graph.add_edge("parse_meal", "validate_result")
graph.add_edge("parse_workout", "validate_result")
graph.add_edge("validate_result", END)

router_agent = graph.compile()


async def parse_entry(raw_text: str) -> dict:
    result = cast(
        dict,
        await router_agent.ainvoke({
            "raw_text": raw_text,
            "intent": None,
            "parsed_meal": None,
            "parsed_workout": None,
        })
    )
    return {
        "intent": result["intent"],
        "parsed_meal": result["parsed_meal"],
        "parsed_workout": result["parsed_workout"],
    }