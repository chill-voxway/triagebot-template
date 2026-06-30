import json
import os

FALLBACK_CLASSIFICATION: dict = {"category": "question", "priority": "P3", "tags": []}

_ALLOWED_CATEGORIES = {"bug", "feature_request", "question", "urgent"}
_ALLOWED_PRIORITIES = {"P1", "P2", "P3"}

_PROMPT = """Classify this support ticket. Return ONLY valid JSON with exactly these keys:
- "category": one of "bug", "feature_request", "question", "urgent"
- "priority": one of "P1", "P2", "P3"
- "tags": a list of 0 to 5 short lowercase strings

Title: {title}
Description: {description}"""


def classify_ticket(title: str, description: str) -> dict:
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=os.environ.get("OPENROUTER_API_KEY", ""),
            base_url="https://openrouter.ai/api/v1",
        )

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": _PROMPT.format(title=title, description=description),
                }
            ],
        )

        result = json.loads(response.choices[0].message.content)

        category = result.get("category")
        priority = result.get("priority")
        tags = result.get("tags", [])

        if category not in _ALLOWED_CATEGORIES or priority not in _ALLOWED_PRIORITIES:
            return FALLBACK_CLASSIFICATION

        if not isinstance(tags, list):
            tags = []

        return {"category": category, "priority": priority, "tags": [str(t) for t in tags]}
    except Exception:
        return FALLBACK_CLASSIFICATION
