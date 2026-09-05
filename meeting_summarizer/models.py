from __future__ import annotations

from pydantic import BaseModel


class ActionItem(BaseModel):
    description: str
    assignee: str
    due_date: str | None = None
    priority: str = "medium"


class MeetingSummary(BaseModel):
    title: str
    date: str | None = None
    participants: list[str]
    summary: list[str]
    key_decisions: list[str]
    action_items: list[ActionItem]
    transcript: str = ""
