import json
from openai import OpenAI
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL
from agent.prompts import get_system_prompt
from agent.tools import TOOL_SCHEMAS, dispatch_tool

MAX_ITERATIONS = 20


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

    for iteration in range(MAX_ITERATIONS):
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )

        message = response.choices[0].message

        if message.tool_calls:
            messages.append(message)

            for tool_call in message.tool_calls:
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
            # Agent finished
            final_text = message.content or ""
            print(f"[agent] Done: {final_text[:200]}")
            return {"status": "complete", "summary": final_text}

    return {"status": "max_iterations_reached"}
