from typing import TypedDict, cast

from dotenv import load_dotenv
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from app.core.llm import get_llm, json_schema_instruction
from app.schemas.workout import WorkoutDraft

load_dotenv()

class ParsedWorkout(BaseModel):
    is_confident: bool = Field(description="True if enough information exists to estimate the workout details and calories burned. False if input is too vague (e.g. 'exercise kiya', 'gym gaya').")
    clarification_question: str | None = Field(default=None, description="If is_confident is False, ask ONE specific question (e.g. duration, exercise name, sets/reps). Otherwise null.")
    workout_type: str | None = Field(default=None, description="'cardio' or 'strength' — only if confident")
    name: str | None = Field(default=None, description="Exercise name, e.g. 'Running', 'Bench Press' — only if confident")
    duration_minutes: float | None = Field(default=None, description="For cardio — only if applicable")
    distance_km: float | None = Field(default=None, description="For cardio — only if applicable and mentioned")
    sets: int | None = Field(default=None, description="For strength — only if applicable")
    reps: int | None = Field(default=None, description="For strength — only if applicable")
    weight_kg: float | None = Field(default=None, description="For strength — only if applicable")
    intensity: str | None = Field(default=None, description="'low', 'moderate', or 'high' — infer from context")
    calories_burned: float | None = Field(default=None, description="Estimated total calories burned — only if confident")
    reasoning: str | None = Field(default=None, description="Brief explanation of the estimate — only if confident")


class AgentState(TypedDict):
    raw_text: str
    parsed_workout: ParsedWorkout | None


llm = get_llm(temperature=0.2)

structured_llm = llm.with_structured_output(ParsedWorkout, method="json_mode")


def parse_workout_node(state: AgentState) -> AgentState:
    prompt = f"""You are a fitness tracking assistant estimating workout details and calories burned.
A user described a workout in natural language (Roman Urdu or English).

User's input: "{state['raw_text']}"

First, decide if there's ENOUGH detail to estimate (exercise name + duration/sets-reps, e.g. "30 min running" or "bench press 3 sets 10 reps 60kg" is enough; "gym gaya" or "exercise kiya" is NOT enough).

If NOT enough: set is_confident=False, ask one specific clarification_question. Leave other fields null.

If enough: set is_confident=True, classify as workout_type "cardio" or "strength", fill relevant fields (cardio: duration/distance; strength: sets/reps/weight), infer intensity, and estimate calories_burned for an average adult based on typical MET values for the activity and duration/effort.

{json_schema_instruction(ParsedWorkout)}
"""
    result = structured_llm.invoke(prompt)
    state["parsed_workout"] = cast(ParsedWorkout, result)
    return state


def build_adjust_prompt(previous_draft: WorkoutDraft, adjustment_text: str) -> str:
    return f"""You are a fitness tracking assistant. You previously estimated this workout:

Original description: "{previous_draft.raw_text}"
Your estimate: {previous_draft.name} ({previous_draft.workout_type}) — {previous_draft.calories_burned} kcal burned, intensity: {previous_draft.intensity}
Your reasoning: {previous_draft.reasoning}

The user now says: "{adjustment_text}"

Adjust your estimate based on this feedback. If clear enough, set is_confident=True with updated values. If still too vague, set is_confident=False and ask ONE clarification_question.

{json_schema_instruction(ParsedWorkout)}
"""


async def parse_workout_text(raw_text: str) -> ParsedWorkout:
    graph = StateGraph(AgentState)
    graph.add_node("parse_workout", parse_workout_node)
    graph.set_entry_point("parse_workout")
    graph.add_edge("parse_workout", END)
    agent = graph.compile()

    result = agent.invoke({"raw_text": raw_text, "parsed_workout": None})
    return result["parsed_workout"]


async def adjust_workout_draft(previous_draft: WorkoutDraft, adjustment_text: str) -> ParsedWorkout:
    prompt = build_adjust_prompt(previous_draft, adjustment_text)
    result = await structured_llm.ainvoke(prompt)
    return cast(ParsedWorkout, result)