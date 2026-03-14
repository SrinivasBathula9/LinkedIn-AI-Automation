"""
Connection note personalizer.
Primary: Ollama (local LLM — mistral:7b or llama3:8b).
Fallback: Pre-written A/B-tested templates.
"""
from __future__ import annotations
import random
import httpx
import structlog

from backend.config import settings

log = structlog.get_logger()

PROMPT_TEMPLATE = """You are a professional networking assistant.
Write a short LinkedIn connection note (max 280 chars) for:
- Sender: {sender_name}, {sender_title}
- Recipient: {recipient_name}, {recipient_title} at {company}
- Shared interest: {shared_topic}
Be concise, warm, and professional. No emojis. No generic phrases.
Output only the note text, nothing else."""

# A/B tested fallback templates
FALLBACK_TEMPLATES = [
    "Hi {recipient_name}, I came across your profile and was impressed by your work at {company}. "
    "I'd love to connect and explore potential synergies. Looking forward to connecting.",
    "Hello {recipient_name}, as a fellow professional in the {industry} space, I'd love to add you "
    "to my network. Your experience at {company} is truly impressive.",
    "Hi {recipient_name}, I noticed your strong background in {field}. "
    "I'd be delighted to connect and exchange insights. Thanks for considering!",
]


async def generate_connection_note(
    sender_name: str,
    sender_title: str,
    recipient_name: str,
    recipient_title: str,
    company: str,
    shared_topic: str = "AI and technology",
) -> str:
    """Generate a personalized connection note (≤280 chars)."""
    try:
        note = await _ollama_generate(
            sender_name=sender_name,
            sender_title=sender_title,
            recipient_name=recipient_name,
            recipient_title=recipient_title,
            company=company,
            shared_topic=shared_topic,
        )
        return note[:280]
    except Exception as e:
        log.warning("Ollama generation failed, using fallback", error=str(e))
        return _fallback_template(
            recipient_name=recipient_name,
            company=company,
            industry=shared_topic,
            field=recipient_title,
        )


async def _ollama_generate(**kwargs) -> str:
    prompt = PROMPT_TEMPLATE.format(**kwargs)
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.ollama_url}/api/generate",
            json={
                "model": settings.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": 100},
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["response"].strip()


def _fallback_template(
    recipient_name: str,
    company: str,
    industry: str = "technology",
    field: str = "technology",
) -> str:
    template = random.choice(FALLBACK_TEMPLATES)
    return template.format(
        recipient_name=recipient_name.split()[0],
        company=company,
        industry=industry,
        field=field,
    )[:280]
