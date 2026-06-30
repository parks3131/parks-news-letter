import json
import uuid
from openai import OpenAI
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL
from agent.prompts import get_system_prompt
from agent.tools import TOOL_SCHEMAS, dispatch_tool

MAX_ITERATIONS = 20

TOOL_NAMES = {t["function"]["name"] for t in TOOL_SCHEMAS}


def _parse_content_tool_calls(content: str) -> list[dict] | None:
    """Some models return tool calls as JSON text instead of structured tool_calls."""
    content = content.strip()
    try:
        data = json.loads(content)

        # Unwrap array of JSON strings (double-encoded)
        if isinstance(data, list) and data and isinstance(data[0], str):
            data = [json.loads(d) for d in data]

        if isinstance(data, list) and all(
            isinstance(d, dict) and d.get("name") in TOOL_NAMES for d in data
        ):
            return data
        if isinstance(data, dict) and data.get("name") in TOOL_NAMES:
            return [data]
    except Exception:
        pass
    return None


def run_newsletter_agent(dry_run: bool = False) -> dict:
    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
    )

    messages = [
        {"role": "system", "content": get_system_prompt()},
        {
            "role": "user",
            "content": (
                "Please run today's newsletter pipeline. "
                + ("DO NOT call send_newsletter — this is a dry run. Stop after compose_newsletter." if dry_run else "")
            ),
        },
    ]

    print(f"[agent] Starting with model: {OPENROUTER_MODEL}")

    for _ in range(MAX_ITERATIONS):
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )

        message = response.choices[0].message
        tool_calls = message.tool_calls

        # Fallback: model output tool calls as JSON text
        if not tool_calls and message.content:
            parsed = _parse_content_tool_calls(message.content)
            if parsed:
                tool_calls = [
                    type("TC", (), {
                        "id": f"call_{uuid.uuid4().hex[:8]}",
                        "function": type("F", (), {
                            "name": t["name"],
                            "arguments": json.dumps(t.get("parameters") or t.get("arguments") or {}),
                        })(),
                    })()
                    for t in parsed
                ]

        if tool_calls:
            messages.append(message)

            for tool_call in tool_calls:
                name = tool_call.function.name
                args = tool_call.function.arguments
                print(f"[agent] → {name}({args[:80]}{'...' if len(args) > 80 else ''})")

                result = dispatch_tool(name, args)
                print(f"[agent] ← {result[:120]}{'...' if len(result) > 120 else ''}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })
        else:
            final_text = message.content or ""
            print(f"[agent] Done: {final_text[:200]}")
            return {"status": "complete", "summary": final_text}

    return {"status": "max_iterations_reached"}
