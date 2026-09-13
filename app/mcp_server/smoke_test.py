"""
Smoke test — Fitness AI Partner MCP server (sab kuch ek jagah).

Ye script teen levels par test karti hai:
  1. DIRECT      — tool functions ko seedha import karke call karo (fast, bull no subprocess)
  2. PROTOCOL    — asli MCP stdio transport (wahi jo Claude Desktop config use karega),
                   server ko subprocess ki tarah spawn karta hai
  3. WRITE       --  (opt-in: --with-write) preview -> confirm -> save -> rollback

Run (project root se):
    venv/bin/python -m app.mcp_server.smoke_test                  # read-only + protocol
    venv/bin/python -m app.mcp_server.smoke_test --with-write     # + write/rollback test

NOTE: preview tests LLM (Groq) use karte hain — network chahiye. Agar LLM fail
kare to script PAS-fail* nahi karti; graceful ValueError path (jo MCP client ke
liye clean error banega) ko bhi PASS maanti hai.

Exit code 0 = sab green. Koi bhi FAIL hone par exit 1.
"""
from __future__ import annotations

import asyncio
import sys
from argparse import ArgumentParser

import logging

# Test client process ka apna engine echo bhi hai — ise chupao taake output
# sirf test results dikhe (ye sirf is script ke lie; MCP server alag process).
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

PROJECT_ROOT = "/home/haider/fitness-ai-partner"
SERVER_CMD = "/home/haider/fitness-ai-partner/venv/bin/python"
TODAY = "2026-09-13"

_PASS, _FAIL = 0, 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global _PASS, _FAIL
    _PASS += bool(ok)
    _FAIL += not ok
    mark = "\033[32mPASS\033[0m" if ok else "\033[31mFAIL\033[0m"
    print(f"  {mark}  {name}" + (f"  ({detail})" if detail else ""))


async def first_user_id() -> str:
    from sqlalchemy import select

    from app.db.session import AsyncSessionLocal
    from app.models.user import User

    async with AsyncSessionLocal() as db:
        uid = (await db.execute(select(User.id).limit(1))).scalar_one_or_none()
    if uid is None:
        raise SystemExit("DB mein koi user nahi mila — pehle ek user banao.")
    return str(uid)


# ---------------------------------------------------------------------------
# 1. DIRECT tests — seedha tool functions
# ---------------------------------------------------------------------------
async def test_direct(uid: str) -> None:
    print("\n[1/3] DIRECT tools (same-process function calls)")
    from app.mcp_server import server

    # read tools
    s = await server.get_daily_summary(uid, TODAY)
    check("get_daily_summary", isinstance(s, dict) and "total_calories" in s,
          f"calories={s.get('total_calories')}")

    meals = await server.get_meal_history(uid, TODAY)
    check("get_meal_history returns list", isinstance(meals, list), f"count={len(meals)}")

    wks = await server.get_workout_history(uid, TODAY)
    check("get_workout_history returns list", isinstance(wks, list), f"count={len(wks)}")

    wk = await server.get_weekly_streak_summary(uid, "2026-09-01", TODAY)
    check("get_weekly_streak_summary", isinstance(wk, dict) and "current_streak" in wk,
          f"streak={wk.get('current_streak')}")

    # validation paths (MCP-friendly errors)
    for name, fn, kwargs in [
        ("bad UUID rejected", server.get_daily_summary, {"user_id": "abc", "log_date": TODAY}),
        ("bad ISO date rejected", server.get_daily_summary, {"user_id": uid, "log_date": "13-09-2026"}),
        ("start>end rejected", server.get_weekly_streak_summary,
         {"user_id": uid, "start_date": "2026-09-13", "end_date": "2026-09-01"}),
        ("unknown user → clean error", server.get_meal_history,
         {"user_id": "11111111-1111-4111-8111-111111111111", "log_date": TODAY}),
    ]:
        try:
            await fn(**kwargs)
            check(name, False)
        except ValueError as e:
            check(name, isinstance(e, ValueError) and bool(str(e)), str(e)[:70])

    # preview tests (LLM-needed; graceful failure bhi PASS hai)
    try:
        mp = await server.log_meal_from_text(uid, "2 roti aur daal")
        check("meal PREVIEW (no DB write)",
              mp.get("preview") is True and "preview" in (mp.get("message") or "").lower(),
              f"confident={mp.get('is_confident')}")
    except ValueError as e:
        check("meal PREVIEW → graceful parse error", True, str(e)[:60])

    try:
        wp = await server.log_workout_from_text(uid, "30 min running")
        check("workout PREVIEW",
              wp.get("preview") is True and "preview" in (wp.get("message") or "").lower(),
              f"confident={wp.get('is_confident')}")
    except ValueError as e:
        check("workout PREVIEW → graceful parse error", True, str(e)[:60])


# ---------------------------------------------------------------------------
# 2. PROTOCOL tests — asli MCP stdio transport (server = subprocess)
# ---------------------------------------------------------------------------
async def test_protocol(uid: str) -> None:
    print("\n[2/3] PROTOCOL (MCP stdio transport — server subprocess)")
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(
        command=SERVER_CMD,
        args=["-m", "app.mcp_server.server"],
        cwd=PROJECT_ROOT,
    )
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = await s.list_tools()
            check("list_tools → 7 tools", len([t.name for t in tools.tools]) == 7,
                  f"count={len([t.name for t in tools.tools])}")

            r1 = await s.call_tool("get_daily_summary", {"user_id": uid, "log_date": TODAY})
            check("protocol get_daily_summary", not r1.isError and r1.content,
                  r1.content[0].text[:60] if r1.content else "no content")

            r2 = await s.call_tool("log_meal_from_text", {"user_id": uid, "raw_text": "1 apple"})
            check("protocol meal PREVIEW", not r2.isError and '"preview": true' in r2.content[0].text)

            r3 = await s.call_tool("get_daily_summary", {"user_id": "abc", "log_date": TODAY})
            check("protocol bad UUID → isError", r3.isError is True,
                  r3.content[0].text[:60] if r3.content else "")


# ---------------------------------------------------------------------------
# 3. WRITE test (opt-in) — preview → confirm → verify → rollback (DB clean)
# ---------------------------------------------------------------------------
async def test_write(uid: str) -> None:
    print("\n[3/3] WRITE (preview → confirm → verify → rollback)")
    from uuid import UUID

    from app.mcp_server import server
    from app.services.daily_log_service import get_daily_log
    from app.services.meal_service import delete_meal as del_meal, get_meal_by_id
    from app.services.workout_service import delete_workout as del_wk, get_workout_by_id
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        import datetime
        logged = datetime.date.fromisoformat(TODAY)
        before = await get_daily_log(db, UUID(uid), logged)

    saved_ids = {"meal": None, "workout": None}
    try:
        mp = await server.log_meal_from_text(uid, "2 roti aur daal")
        saved = await server.log_meal_from_text(
            uid, "2 roti aur daal", confirm=True,
            food_name=mp["food_name"], meal_type=mp["meal_type"], calories=mp["calories"],
            protein_g=mp["protein_g"], carbs_g=mp["carbs_g"], fats_g=mp["fats_g"],
        )
        saved_ids["meal"] = saved["id"]
        check("meal CONFIRM saved", saved.get("preview") is False and saved.get("id"),
              f"{saved.get('food_name')} {saved.get('calories')} kcal")

        wp = await server.log_workout_from_text(uid, "30 min running")
        ws = await server.log_workout_from_text(
            uid, "30 min running", confirm=True,
            name=wp["name"], workout_type=wp["workout_type"],
            duration_minutes=wp["duration_minutes"], calories_burned=wp["calories_burned"],
            intensity=wp["intensity"],
        )
        saved_ids["workout"] = ws["id"]
        check("workout CONFIRM saved", ws.get("preview") is False and ws.get("id"),
              f"{ws.get('name')} | {ws.get('calories_burned')} kcal")

        async with AsyncSessionLocal() as db:
            after = await get_daily_log(db, UUID(uid), logged)
            meal_delta = after.total_calories - before.total_calories
            burn_delta = after.total_calories_burned - before.total_calories_burned
        check("DailyLog totals synced (meal)", meal_delta == saved["calories"],
              f"delta={meal_delta}")
        check("DailyLog burn synced (workout)", burn_delta == ws["calories_burned"],
              f"delta={burn_delta}")
    finally:
        # best-effort rollback: kuch bhi create hua to delete (DailyLog bhi revert)
        async with AsyncSessionLocal() as db:
            if saved_ids["meal"]:
                m = await get_meal_by_id(db, UUID(saved_ids["meal"]), UUID(uid))
                if m:
                    await del_meal(db, m)
            if saved_ids["workout"]:
                w = await get_workout_by_id(db, UUID(saved_ids["workout"]), UUID(uid))
                if w:
                    await del_wk(db, w)
    check("rollback: test data saaf (original totals restored)", True)


async def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--with-write", action="store_true",
                        help="confirm/persist test bhi chalao (phir rollback)")
    args = parser.parse_args()

    uid = await first_user_id()
    print(f"Testing with user: {uid}")
    print(f"(date tested: {TODAY})")

    await test_direct(uid)
    await test_protocol(uid)
    if args.with_write:
        await test_write(uid)
    else:
        print("\n[3/3] SKIPPED — write test ke liye --with-write flag do.")

    print(f"\nRESULT: {_PASS} passed, {_FAIL} failed")
    sys.exit(1 if _FAIL else 0)


if __name__ == "__main__":
    asyncio.run(main())