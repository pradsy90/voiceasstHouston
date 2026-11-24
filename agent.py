# agent.py
import json
import re

from chat import _ask, search_serpapi, summarize_with_gpt, MODEL

AGENT_SYS = (
    "You produce SMALL executable plans. "
    "Return STRICT JSON only, no code fences: "
    "{\"steps\":[{\"tool\":\"ask_gpt|live_search\",\"prompt\":\"...\"}],"
    "\"stop_condition\":\"...\"}. Keep 2-5 steps."
)

KEYWORDS = {
    "plan", "steps", "research", "compare", "pros", "cons", "draft", "outline",
    "summarize", "itinerary", "schedule", "how to", "recipe", "make", "build",
    "create", "design", "prepare", "how can"
}


def is_tasky(text: str) -> bool:
    t = text.lower().strip()
    if t.startswith(("plan:", "task:", "project:", "agent:")):
        return True
    return any(re.search(rf"\b{re.escape(k)}\b", t) for k in KEYWORDS)


def make_plan(user_goal: str) -> dict:
    plan_prompt = (
        f"{AGENT_SYS}\nUser goal: {user_goal}\n"
        "If unclear, assume a reasonable narrow scope."
    )
    fallback = {"steps": [{"tool": "ask_gpt", "prompt": user_goal}],
                "stop_condition": "one useful answer produced"}
    try:
        raw = _ask([{"role": "user", "content": plan_prompt}], MODEL, 1000)
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
        plan = json.loads(raw)
        assert isinstance(plan.get("steps", []), list) and plan["steps"]
        return plan
    except Exception as e:
        print(f"Plan fallback used: {e}")
        return fallback


def run_step(step: dict, prior: str = "") -> str:
    tool = step.get("tool", "ask_gpt")
    prompt = step.get("prompt", "")

    if tool == "live_search":
        raw = search_serpapi(prompt[:300])
        if not raw:
            return "I couldn't find live information on that."
        return summarize_with_gpt(raw, prompt)

    # ask_gpt: include earlier findings (capped) as context
    if prior:
        prompt = f"Earlier findings:\n{prior[:1500]}\n\n{prompt}"
    prompt += "\n\nAnswer in under 500 characters."
    return _ask([{"role": "user", "content": prompt}], MODEL, 1000)


def agent_run(user_goal: str, glbl: dict) -> str:
    mem = glbl.get("agent_memory", [])
    plan = make_plan(user_goal)
    last = ""
    for i, step in enumerate(plan.get("steps", [])[:5], 1):
        try:
            obs = run_step(step, last)
            if obs:
                last = obs
            mem.append({"step": i, "tool": step.get("tool"),
                        "prompt": step.get("prompt"), "observation": obs[:500]})
        except Exception as e:
            print(f"Agent step {i} failed: {e}")
            break
    glbl["agent_memory"] = mem
    return last or "Sorry, I couldn't work that out."
