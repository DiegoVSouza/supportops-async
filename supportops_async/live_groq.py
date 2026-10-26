"""Provider-backed, fail-closed task plan validation for opt-in live runs."""
import json

ALLOWED_STEPS={"triage","draft_reply"}

def validate_plan(text: str) -> list[str]:
    try: value=json.loads(text)
    except (TypeError,ValueError) as exc: raise ValueError("Groq plan is not valid JSON") from exc
    steps=value.get("steps") if isinstance(value,dict) else None
    if not isinstance(steps,list) or not 1<=len(steps)<=2 or any(step not in ALLOWED_STEPS for step in steps) or len(set(steps))!=len(steps):
        raise ValueError("Groq plan must contain one or two unique allowlisted steps")
    if steps[0]!="triage": raise ValueError("Groq plan must begin with triage")
    return steps
