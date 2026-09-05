from __future__ import annotations

import json

import click
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import get_api_config
from .models import ActionItem, MeetingSummary

ANALYSIS_PROMPT = """\
You are a meeting analyst. Analyze the following meeting transcript and extract structured information.

Return a JSON object with exactly these fields:
{
  "title": "A concise title for the meeting (inferred from content)",
  "date": "Meeting date if mentioned, otherwise null",
  "participants": ["List of participant names mentioned in the transcript"],
  "summary": ["Bullet point 1", "Bullet point 2", "...3-5 concise summary bullets"],
  "key_decisions": ["Decision 1", "Decision 2", "...any decisions that were made"],
  "action_items": [
    {
      "description": "What needs to be done",
      "assignee": "Who is responsible (use 'Unassigned' if unclear)",
      "due_date": "Due date if mentioned, otherwise null",
      "priority": "high, medium, or low based on urgency/importance"
    }
  ]
}

Rules:
- Summary bullets should be concise but informative (1-2 sentences each)
- Extract ALL action items, even implicit ones ("I'll look into that" = action item)
- If no participants are identifiable, use ["Unknown"]
- Prioritize action items based on context clues (deadlines, urgency words, blockers)
- Return ONLY the JSON object, no other text

TRANSCRIPT:
"""


def _make_ssl_context():
    import ssl
    ctx = ssl.create_default_context()
    ctx.load_default_certs()
    return ctx


def _call_anthropic(config: dict, model: str, transcript: str) -> str:
    import anthropic
    import httpx

    http_client = httpx.Client(verify=_make_ssl_context())
    client = anthropic.Anthropic(
        api_key=config["api_key"],
        base_url=config["base_url"],
        http_client=http_client,
    )
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": ANALYSIS_PROMPT + transcript}],
    )
    return message.content[0].text.strip()


def _call_openai_compatible(config: dict, model: str, transcript: str) -> str:
    import httpx
    from openai import OpenAI

    client = OpenAI(
        base_url=config["base_url"],
        api_key=config["api_key"],
        http_client=httpx.Client(verify=_make_ssl_context()),
    )
    completion = client.chat.completions.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": ANALYSIS_PROMPT + transcript}],
    )
    return completion.choices[0].message.content.strip()


def analyze_transcript(transcript: str, model: str | None = None) -> MeetingSummary:
    config = get_api_config()
    model = model or config["model"]
    is_anthropic = config.get("is_anthropic", False)
    provider_label = "Claude" if is_anthropic else model.split("/")[-1]

    with Progress(SpinnerColumn(), TextColumn(f"[bold green]Analyzing with {provider_label}...")) as progress:
        progress.add_task("analyze", total=None)
        if is_anthropic:
            response_text = _call_anthropic(config, model, transcript)
        else:
            response_text = _call_openai_compatible(config, model, transcript)

    if response_text.startswith("```"):
        lines = response_text.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        response_text = "\n".join(lines)

    try:
        data = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Failed to parse LLM response as JSON: {e}\nResponse: {response_text[:500]}")

    action_items = [ActionItem(**item) for item in data.get("action_items", [])]

    return MeetingSummary(
        title=data.get("title", "Untitled Meeting"),
        date=data.get("date"),
        participants=data.get("participants", ["Unknown"]),
        summary=data.get("summary", []),
        key_decisions=data.get("key_decisions", []),
        action_items=action_items,
        transcript=transcript,
    )
