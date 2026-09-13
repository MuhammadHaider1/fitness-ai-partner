"""
MCP server — Fitness AI Partner

Ye file hamare existing FastAPI backend ko ek MCP (Model Context Protocol)
server ke roop mein expose karti hai. Matlab: koi bhi MCP-compatible client
(Claude Desktop, Claude Code, etc.) hamare fitness data ko query kar sakta hai
aur natural-language logging kar sakta hai — bina koi naya HTTP endpoint
likhe.

Design ke principles (read karo, yehi interview-mein language hai):

1. REUSE, duplicate mat karo.
   Saara business logic already app/services/ aur app/agents/ mein hai.
   Yahan sirf "thin wrappers" hain — ek MCP tool ek service/agent function ko
   call karta hai. Agar logic badlo, yahan kuch change nahi hota.

2. DB session.
   Har tool call ke liye `AsyncSessionLocal()` se ek nayi session khulti hai
   aur automatically close hoti hai (`async with`). Same session jo FastAPI
   endpoints use karte hain.

3. Permission gating on WRITE tools.
   `log_meal_from_text` / `log_workout_from_text` pehle PARSE (preview) karte
   hain, DB kuch nahi likhte. User (AI agent ya human) confirm=True ke saath
   exact values doobara bheje to hi save hota hai. Isse "agent silently data
   mutate kar de" wala risk khatam hota hai.

4. Validation.
   Har tool user_id (UUID) aur dates (ISO) validate karta hai aur clean,
   MCP-friendly errors deta hai — raw stack trace kabhi bhi client tak nahi
   jaata.

Run: python -m app.mcp_server.server
"""

from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID

import logging
import sys

# ---------------------------------------------------------------------------
# CRITICAL: MCP stdio transport me SERVER ka stdout sirf JSON-RPC ke liye
# reserved hota hai — koi bhi extra output protocol ko corrupt kar deta hai
# (client JSON parse kar nahi pata). SQLAlchemy ka `echo=True` (session.py
# mein) INFO-level query logs seedha stdout par likhta hai -> inhe suppress
# karo, aur koi bhi remaining logging stderr par redirect karo. REST API
# process ko nahi chhute — ye sirf MCP subprocess ke liye hai.
# ---------------------------------------------------------------------------
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.basicConfig(stream=sys.stderr, force=True)

from mcp.server.fastmcp import FastMCP

from app.db.session import AsyncSessionLocal

# crafty: SQLAlchemy `echo=True` apna StreamHandler(sys.stdout) attach karta
# hai (engine create hote waqt, `sqlalchemy.engine.Engine` CHILD logger par)
# aur getEffectiveLevel override karta hai, is liye sirf setLevel() kaam nahi
# karta — stdout wale handlers REMOVE karna padte hain. Records phir bhi root
# logger (basicConfig -> stderr) tak propagate hote hain, is liye debug info
# kaam ki rehti hai par stdout sirf JSON-RPC ke liye safe rehta hai.
_sa_root, _sa_all = "sqlalchemy", logging.Logger.manager.loggerDict
for _name in list(_sa_all):
    if _name.startswith(_sa_root):
        for _h in list(logging.getLogger(_name).handlers):
            _logger = logging.getLogger(_name)
            if getattr(_h, "stream", None) is sys.stdout:
                _logger.removeHandler(_h)
del _sa_root, _sa_all

from app.schemas.meal import MealCreate
from app.schemas.workout import WorkoutCreate
from app.services.auth_service import get_user_by_id

# ---------------------------------------------------------------------------
# Server instance — ye identity hai jo Claude Desktop config mein milti hai.
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "fitness-ai-partner",
    instructions=(
        "Fitness AI Partner backend. Pehle get_daily_summary / get_meal_history "
        "se data dekho, phir log_meal_from_text / log_workout_from_text use karo. "
        "Write action ke liye confirm=True zaroori hai — pehla call sirf preview "
        "deta hai, kuch save NAHI hota."
    ),
)


# ---------------------------------------------------------------------------
# Helpers — validation + serialization
# ---------------------------------------------------------------------------
def _parse_user_id(value: str) -> UUID:
    """user_id ko valid UUID banata hai warna clean error deta hai."""
    try:
        return UUID(value)
    except (ValueError, AttributeError, TypeError):
        raise ValueError(
            f"user_id ek valid UUID hona chahiye (e.g. 2f0b6f5e-...), tumne diya: {value!r}"
        )


def _parse_date(value: str, field: str = "log_date") -> date:
    """'YYYY-MM-DD' format ka date parse karta hai (ISO 8601)."""
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        raise ValueError(
            f"{field} ek valid ISO date hona chahiye (YYYY-MM-DD), tumne diya: {value!r}"
        )


async def _require_user(db, user_id: UUID):
    """User exist karta hai? None hai to clean error — FK crash se pehle."""
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise ValueError(f"User with id '{user_id}' nahi mila. Pehle user ka id check karo.")
    return user


def _meal_to_dict(meal: Any) -> dict:
    """Meal ORM object -> JSON-safe dict (datetime ko ISO string kar ke)."""
    return {
        "id": str(meal.id),
        "food_name": meal.food_name,
        "meal_type": meal.meal_type,
        "calories": meal.calories,
        "protein_g": meal.protein_g,
        "carbs_g": meal.carbs_g,
        "fats_g": meal.fats_g,
        "raw_text": meal.raw_text,
        "source": meal.source,
        "logged_at": meal.logged_at.astimezone().isoformat(),
    }


def _workout_to_dict(workout: Any) -> dict:
    """Workout ORM object -> JSON-safe dict."""
    return {
        "id": str(workout.id),
        "workout_type": workout.workout_type,
        "name": workout.name,
        "duration_minutes": workout.duration_minutes,
        "distance_km": workout.distance_km,
        "sets": workout.sets,
        "reps": workout.reps,
        "weight_kg": workout.weight_kg,
        "intensity": workout.intensity,
        "calories_burned": workout.calories_burned,
        "raw_text": workout.raw_text,
        "source": workout.source,
        "logged_at": workout.logged_at.astimezone().isoformat(),
    }


def _model_to_dict(model: Any) -> dict:
    """Generic Pydantic/ORM -> JSON-safe: date/datetime fields ko ISO kar do."""
    return {
        k: (v.isoformat() if isinstance(v, (date, datetime)) else v)
        for k, v in model.model_dump().items()
        if not k.startswith("_")
    }


# ---------------------------------------------------------------------------
# READ-ONLY TOOLS
# ---------------------------------------------------------------------------
@mcp.tool()
async def get_daily_summary(user_id: str, log_date: str) -> dict:
    """
    A user ke ek din ka poora summary return karta hai (read-only).

    Args:
        user_id: User ka UUID (string).
        log_date: Date in ISO format 'YYYY-MM-DD' (Asia/Karachi calendar day).

    Returns:
        dict: calorie_target, total_calories, protein/carbs/fats (grams),
              total_calories_burned, water_intake_ml, mood.
    """
    uid = _parse_user_id(user_id)
    logged = _parse_date(log_date)

    async with AsyncSessionLocal() as db:
        await _require_user(db, uid)
        # get_daily_log get_or_create pattern use karta hai (same jo /coach/daily
        # endpoint karta hai) — agar din ka log nahi hai to empty log bana deta hai.
        from app.services.daily_log_service import get_daily_log

        log = await get_daily_log(db, uid, logged)

    return {
        "log_date": logged.isoformat(),
        "calorie_target": log.calorie_target,
        "total_calories": log.total_calories,
        "total_protein_g": log.total_protein_g,
        "total_carbs_g": log.total_carbs_g,
        "total_fats_g": log.total_fats_g,
        "total_calories_burned": log.total_calories_burned,
        "water_intake_ml": log.water_intake_ml,
        "mood": log.mood,
    }


@mcp.tool()
async def get_meal_history(user_id: str, log_date: str) -> list[dict]:
    """
    Ek din par logged saari meals return karti hai (read-only).

    Args:
        user_id: User ka UUID.
        log_date: ISO date 'YYYY-MM-DD'.

    Returns:
        list[dict]: Har meal ka food_name, meal_type, calories, macros,
                    source aur logged_at timestamp.
    """
    uid = _parse_user_id(user_id)
    logged = _parse_date(log_date)

    async with AsyncSessionLocal() as db:
        await _require_user(db, uid)
        from app.services.meal_service import get_meals_by_user

        meals = await get_meals_by_user(db, uid, logged)

    return [_meal_to_dict(m) for m in meals]


@mcp.tool()
async def get_workout_history(user_id: str, log_date: str) -> list[dict]:
    """
    Ek din par logged saare workouts return karta hai (read-only).

    Args:
        user_id: User ka UUID.
        log_date: ISO date 'YYYY-MM-DD'.

    Returns:
        list[dict]: Har workout ki details (name, type, duration, calories
                    burned, intensity, waghaira).
    """
    uid = _parse_user_id(user_id)
    logged = _parse_date(log_date)

    async with AsyncSessionLocal() as db:
        await _require_user(db, uid)
        from app.services.workout_service import get_workouts_by_user

        workouts = await get_workouts_by_user(db, uid, logged)

    return [_workout_to_dict(w) for w in workouts]


@mcp.tool()
async def get_weekly_streak_summary(user_id: str, start_date: str, end_date: str) -> dict:
    """
    Ek date-range ke liye aggregate summary return karta hai (read-only) —
    consistency tracking ke liye.

    Args:
        user_id: User ka UUID.
        start_date: Range shuru (ISO 'YYYY-MM-DD').
        end_date: Range khatam (ISO 'YYYY-MM-DD', inclusive).

    Returns:
        dict: days_logged, days_on_target, average calories/macros, current_streak.
    """
    uid = _parse_user_id(user_id)
    start = _parse_date(start_date, "start_date")
    end = _parse_date(end_date, "end_date")
    if start > end:
        raise ValueError("start_date end_date se baad nahi ho sakti.")

    async with AsyncSessionLocal() as db:
        await _require_user(db, uid)
        from app.services.daily_log_service import get_daily_log_summary

        summary = await get_daily_log_summary(db, uid, start, end)

    return _model_to_dict(summary)


@mcp.tool()
async def get_daily_coach_insight(user_id: str, log_date: str) -> dict:
    """
    AI coach ka din ka insight (summary/highlights/suggestions) generate karta hai.

    Ye tool LLM call karta hai — rate-limit (429) hit ho to bhi friendly error
    deta hai. Fetch sequence exactly /coach/daily endpoint jaisa hai:
    1. Daily log us date ka. 2. Meals. 3. Workouts. 4. Streak (last 30 days).

    Args:
        user_id: User ka UUID.
        log_date: ISO date 'YYYY-MM-DD'.

    Returns:
        dict: {summary, highlights: list[str], suggestions: list[str]}
    """
    uid = _parse_user_id(user_id)
    logged = _parse_date(log_date)

    async with AsyncSessionLocal() as db:
        user = await _require_user(db, uid)

        from app.agents.coach_agent import generate_daily_coach_insight
        from app.services.daily_log_service import get_daily_log, get_daily_log_summary
        from app.services.meal_service import get_meals_by_user
        from app.services.workout_service import get_workouts_by_user

        daily_log = await get_daily_log(db, uid, logged)
        meals = await get_meals_by_user(db, uid, logged)
        workouts = await get_workouts_by_user(db, uid, logged)

        # Streak ke liye pichle 30 din ka summary (same as existing endpoint).
        summary = await get_daily_log_summary(db, uid, logged - timedelta(days=30), logged)

        try:
            insight = await generate_daily_coach_insight(
                daily_log, meals, workouts, summary.current_streak, user
            )
        except Exception as exc:  # 429 / network / provider errors
            err = str(exc).lower()
            if "429" in err or "resource_exhausted" in err:
                return {
                    "error": "AI coach abhi busy hai (rate limit reached). Ek minute mein dobara try karo.",
                }
            return {
                "error": f"AI coach insight generate nahi kar saka: {exc}",
            }

    return {
        "log_date": logged.isoformat(),
        "summary": insight.summary,
        "highlights": insight.highlights,
        "suggestions": insight.suggestions,
    }


# ---------------------------------------------------------------------------
# WRITE TOOLS (permission-gated: pehle preview, phir confirm)
# ---------------------------------------------------------------------------
@mcp.tool()
async def log_meal_from_text(
    user_id: str,
    raw_text: str,
    confirm: bool = False,
    food_name: str | None = None,
    meal_type: str | None = None,
    calories: float | None = None,
    protein_g: float | None = None,
    carbs_g: float | None = None,
    fats_g: float | None = None,
) -> dict:
    """
    Natural language se meal log karta hai — with confirm/preview gating.

    confirm=False (default): sirf nutrition_agent parse karta hai aur PARSED
    DRAFT return karta hai — database mein KUCH NAHI likha jaata. Preview ko
    save karne ke liye wohi exact values pass kar ke confirm=True ka tool
    dobara call karo.

    confirm=True: meal save hota hai (meal_service.create_meal -> DailyLog
    bhi sync). Values pass nahi ki to dobara parse karke best-estimate use
    hogi; hamesha recommended ye hai ke preview wali exact values pass karo.

    Args:
        user_id: User ka UUID.
        raw_text: User ka natural-language description, e.g. '2 roti aur daal khai'.
        confirm: False = sirf preview. True = actually save.
        food_name/meal_type/calories/protein_g/carbs_g/fats_g: confirm=True
            par preview wali exact values (optional — nahi di to re-parse).

    Returns:
        dict: Preview ho to draft + message; save ho to saved meal + message.
    """
    uid = _parse_user_id(user_id)
    if not raw_text or not raw_text.strip():
        raise ValueError("raw_text khaali nahi ho sakti.")

    async with AsyncSessionLocal() as db:
        await _require_user(db, uid)

        from app.agents.nutrition_agent import parse_meal_text
        from app.services.meal_service import create_meal

        # --- Step 1 (sirf jab zaroorat ho): parse karo ---
        # confirm=True + exact values di hain => LLM parse skip (deterministic,
        # aur 429 rate-limit ka risk bhi zero). Preview ko to LLM hi chahiye.
        needs_parse = not (
            confirm
            and food_name is not None
            and calories is not None
        )
        parsed = await parse_meal_text(raw_text) if needs_parse else None

        # ------------------ PREVIEW MODE (default) ------------------
        if not confirm:
            parsed = parsed or await parse_meal_text(raw_text)  # safety net
            draft = {
                "preview": True,
                "is_confident": parsed.is_confident,
                "clarification_question": parsed.clarification_question,
                "food_name": parsed.food_name,
                "meal_type": parsed.meal_type,
                "calories": parsed.calories,
                "protein_g": parsed.protein_g,
                "carbs_g": parsed.carbs_g,
                "fats_g": parsed.fats_g,
                "reasoning": parsed.reasoning,
            }
            if not parsed.is_confident:
                draft["message"] = (
                    f"Ziyada detail chahiye: {parsed.clarification_question or 'kya khaya, kitna khaya?'}"
                )
            else:
                draft["message"] = (
                    "This is a preview — kuch save NAHI hua. "
                    "Save karne ke liye isi tool ko confirm=True ke saath dobara call "
                    "karo aur yehi exact values pass karo "
                    f"(food_name='{parsed.food_name}', calories={parsed.calories}, ...)."
                )
            return draft

        # ------------------ CONFIRM MODE ------------------
        # Exact preview values di gayi (parsed=None) -> wohi use karo,
        # deterministic save, koi LLM call nahi. Missing values hain ->
        # parsed (already LLM-verify hua) se bharo, sirf jab confident ho.
        if parsed is None:
            pass  # saare required values caller ne diye (food_name + calories)
        else:
            if food_name is None or calories is None:
                if not parsed.is_confident or not parsed.food_name or parsed.calories is None:
                    raise ValueError(
                        "Confirm karne ke liye pehle preview le kar exact values bhejo "
                        "(food_name, calories, ...) — parsed draft confident nahi hai."
                    )
                food_name, calories = parsed.food_name, parsed.calories
            meal_type = meal_type or parsed.meal_type
            protein_g = protein_g if protein_g is not None else parsed.protein_g
            carbs_g = carbs_g if carbs_g is not None else parsed.carbs_g
            fats_g = fats_g if fats_g is not None else parsed.fats_g

        meal_in = MealCreate(
            food_name=food_name,
            meal_type=meal_type,
            calories=calories,
            protein_g=protein_g,
            carbs_g=carbs_g,
            fats_g=fats_g,
        )

        meal = await create_meal(db, uid, meal_in, source="agent")
        await db.refresh(meal)

    saved = _meal_to_dict(meal)
    saved["preview"] = False
    saved["message"] = "Meal save ho gaya — DailyLog totals sync ho gaye."
    return saved


@mcp.tool()
async def log_workout_from_text(
    user_id: str,
    raw_text: str,
    confirm: bool = False,
    workout_type: str | None = None,
    name: str | None = None,
    duration_minutes: float | None = None,
    distance_km: float | None = None,
    sets: int | None = None,
    reps: int | None = None,
    weight_kg: float | None = None,
    intensity: str | None = None,
    calories_burned: float | None = None,
) -> dict:
    """
    Natural language se workout log karta hai — with confirm/preview gating.

    Same pattern as log_meal_from_text: confirm=False sirf parsed draft return
    karta hai (no DB write); exact values + confirm=True par hi save hota hai.

    Args:
        user_id: User ka UUID.
        raw_text: e.g. '30 min running' ya 'bench press 3 sets 10 reps 60kg'.
        confirm: False = preview only. True = actually save.

    Returns:
        dict: Preview draft ya saved workout.
    """
    uid = _parse_user_id(user_id)
    if not raw_text or not raw_text.strip():
        raise ValueError("raw_text khaali nahi ho sakti.")

    async with AsyncSessionLocal() as db:
        await _require_user(db, uid)

        from app.agents.workout_agent import parse_workout_text
        from app.services.workout_service import create_workout

        # Same optimization as meal tool: confirm + exact values => LLM parse
        # skip (deterministic, 429-free). Preview ko LLM hi chahiye.
        needs_parse = not (
            confirm
            and name is not None
            and workout_type is not None
            and calories_burned is not None
        )
        parsed = await parse_workout_text(raw_text) if needs_parse else None

        # ------------------ PREVIEW MODE ------------------
        if not confirm:
            parsed = parsed or await parse_workout_text(raw_text)  # safety net
            draft = {
                "preview": True,
                "is_confident": parsed.is_confident,
                "clarification_question": parsed.clarification_question,
                "workout_type": parsed.workout_type,
                "name": parsed.name,
                "duration_minutes": parsed.duration_minutes,
                "distance_km": parsed.distance_km,
                "sets": parsed.sets,
                "reps": parsed.reps,
                "weight_kg": parsed.weight_kg,
                "intensity": parsed.intensity,
                "calories_burned": parsed.calories_burned,
                "reasoning": parsed.reasoning,
            }
            if not parsed.is_confident:
                draft["message"] = (
                    f"Ziyada detail chahiye: {parsed.clarification_question or 'exercise ka naam aur duration/sets-reps batao.'}"
                )
            else:
                draft["message"] = (
                    "This is a preview — kuch save NAHI hua. "
                    "Save karne ke liye confirm=True ke saath yehi exact values pass "
                    f"karo (name='{parsed.name}', workouts_type='{parsed.workout_type}', ...)."
                )
            return draft

        # ------------------ CONFIRM MODE ------------------
        if parsed is None:
            pass  # saare required values caller ne diye (name, type, burn)
        else:
            if name is None or workout_type is None or calories_burned is None:
                if not parsed.is_confident or not parsed.name or parsed.calories_burned is None:
                    raise ValueError(
                        "Confirm karne ke liye pehle preview le kar exact values bhejo "
                        "(name, workout_type, calories_burned, ...) — parsed draft confident nahi hai."
                    )
                name, workout_type = parsed.name, parsed.workout_type
                calories_burned = parsed.calories_burned
            duration_minutes = duration_minutes if duration_minutes is not None else parsed.duration_minutes
            distance_km = distance_km if distance_km is not None else parsed.distance_km
            sets = sets if sets is not None else parsed.sets
            reps = reps if reps is not None else parsed.reps
            weight_kg = weight_kg if weight_kg is not None else parsed.weight_kg
            intensity = intensity if intensity is not None else parsed.intensity

        workout_in = WorkoutCreate(
            workout_type=workout_type,
            name=name,
            duration_minutes=duration_minutes,
            distance_km=distance_km,
            sets=sets,
            reps=reps,
            weight_kg=weight_kg,
            intensity=intensity,
            calories_burned=calories_burned,
        )

        workout = await create_workout(db, uid, workout_in, source="agent")
        await db.refresh(workout)

    saved = _workout_to_dict(workout)
    saved["preview"] = False
    saved["message"] = "Workout save ho gaya — DailyLog calories_burned sync ho gayi."
    return saved


# ---------------------------------------------------------------------------
# Entry point — python -m app.mcp_server.server
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Default transport stdio hai — yehi Claude Desktop ke liye chahiye.
    mcp.run()