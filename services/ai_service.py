import json
import re
from typing import List, Dict
from core.config import settings


def _build_messages(context: str, num_questions: int, difficulty: str) -> list:
    difficulty_guidance = {
        "easy": "simple, straightforward questions that test basic recall and understanding",
        "medium": "moderately challenging questions that require comprehension and some analysis",
        "hard": "challenging questions that require deep understanding, critical thinking, and application",
    }

    prompt = f"""Generate exactly {num_questions} multiple choice questions based on the provided content.

Difficulty level: {difficulty} — {difficulty_guidance.get(difficulty, '')}

Content:
{context[:8000]}

Return ONLY a valid JSON array, nothing else:
[
  {{
    "question": "Question text here?",
    "option_a": "First option",
    "option_b": "Second option",
    "option_c": "Third option",
    "option_d": "Fourth option",
    "correct_option": "A",
    "explanation": "Brief explanation of why this answer is correct."
  }}
]

Rules:
- Generate exactly {num_questions} questions
- correct_option must be exactly one of: A, B, C, D
- All 4 options must be plausible but only one correct
- Return ONLY the JSON array — no markdown, no explanation, no preamble"""

    return [{"role": "user", "content": prompt}]


def _build_topic_messages(topic: str, num_questions: int, difficulty: str) -> list:
    difficulty_guidance = {
        "easy": "simple, straightforward questions that test basic recall and understanding",
        "medium": "moderately challenging questions that require comprehension and some analysis",
        "hard": "challenging questions that require deep understanding, critical thinking, and application",
    }

    prompt = f"""Generate exactly {num_questions} multiple choice questions about: "{topic}"

Difficulty level: {difficulty} — {difficulty_guidance.get(difficulty, '')}

Return ONLY a valid JSON array, nothing else:
[
  {{
    "question": "Question text here?",
    "option_a": "First option",
    "option_b": "Second option",
    "option_c": "Third option",
    "option_d": "Fourth option",
    "correct_option": "A",
    "explanation": "Brief explanation of why this answer is correct."
  }}
]

Rules:
- Generate exactly {num_questions} questions
- correct_option must be exactly one of: A, B, C, D
- All 4 options must be plausible but only one correct
- Cover different aspects of the topic
- Return ONLY the JSON array — no markdown, no explanation, no preamble"""

    return [{"role": "user", "content": prompt}]


def _parse_questions(raw_response: str, num_questions: int) -> List[Dict]:
    text = raw_response.strip()
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    text = text.strip()

    start = text.find("[")
    end = text.rfind("]") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON array found in model response")

    json_str = text[start:end]
    questions = json.loads(json_str)

    if not isinstance(questions, list):
        raise ValueError("Expected a JSON array")

    validated = []
    for q in questions[:num_questions]:
        if not all(k in q for k in ["question", "option_a", "option_b", "option_c", "option_d", "correct_option"]):
            continue
        correct = str(q["correct_option"]).strip().upper()
        if correct not in ["A", "B", "C", "D"]:
            correct = "A"
        validated.append({
            "question": str(q["question"]),
            "option_a": str(q["option_a"]),
            "option_b": str(q["option_b"]),
            "option_c": str(q["option_c"]),
            "option_d": str(q["option_d"]),
            "correct_option": correct,
            "explanation": str(q.get("explanation", "")),
        })

    return validated


def _call_chat_api(messages: list) -> str:
    """Call HuggingFace chat completions API via new router endpoint."""
    import httpx

    response = httpx.post(
        f"https://router.huggingface.co/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.HF_API_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.HF_MODEL_ID,
            "messages": messages,
            "max_tokens": 3000,
            "temperature": 0.3,
        },
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


async def generate_questions_from_text(raw_text: str, num_questions: int, difficulty: str) -> List[Dict]:
    messages = _build_messages(raw_text, num_questions, difficulty)
    raw_response = _call_chat_api(messages)
    return _parse_questions(raw_response, num_questions)


async def generate_questions_from_topic(topic: str, num_questions: int, difficulty: str) -> List[Dict]:
    messages = _build_topic_messages(topic, num_questions, difficulty)
    raw_response = _call_chat_api(messages)
    return _parse_questions(raw_response, num_questions)
