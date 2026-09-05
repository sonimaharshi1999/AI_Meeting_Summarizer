from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .models import MeetingSummary

console = Console(force_terminal=True)

PRIORITY_COLORS = {"high": "red", "medium": "yellow", "low": "green"}


def display_terminal(summary: MeetingSummary) -> None:
    """Render meeting summary in the terminal with Rich formatting."""
    # Header
    header = Text(summary.title, style="bold white")
    if summary.date:
        header.append(f"  ({summary.date})", style="dim")
    console.print(Panel(header, title="Meeting Summary", border_style="blue"))

    # Participants
    if summary.participants:
        console.print(f"\n[bold]Participants:[/bold] {', '.join(summary.participants)}")

    # Summary bullets
    console.print("\n[bold cyan]Summary[/bold cyan]")
    for bullet in summary.summary:
        console.print(f"  [dim]-[/dim] {bullet}")

    # Key decisions
    if summary.key_decisions:
        console.print("\n[bold magenta]Key Decisions[/bold magenta]")
        for decision in summary.key_decisions:
            console.print(f"  [dim]>[/dim] {decision}")

    # Action items table
    if summary.action_items:
        console.print()
        table = Table(title="Action Items", show_lines=True, border_style="green")
        table.add_column("#", style="dim", width=3)
        table.add_column("Task", min_width=30)
        table.add_column("Assignee", style="bold")
        table.add_column("Due Date")
        table.add_column("Priority")

        for i, item in enumerate(summary.action_items, 1):
            color = PRIORITY_COLORS.get(item.priority, "white")
            priority_text = Text(item.priority.upper(), style=f"bold {color}")
            table.add_row(
                str(i),
                item.description,
                item.assignee,
                item.due_date or "-",
                priority_text,
            )
        console.print(table)
    else:
        console.print("\n[dim]No action items identified.[/dim]")


def save_txt(summary: MeetingSummary, output_path: Path) -> Path:
    """Save the terminal output as a plain text file."""
    txt_path = output_path.parent / f"{output_path.stem}_summary.txt"
    text_console = Console(file=None, force_terminal=False, no_color=True, width=100)

    from io import StringIO
    buf = StringIO()
    text_console = Console(file=buf, force_terminal=False, no_color=True, width=100)

    text_console.print(f"{'=' * 80}")
    text_console.print(f"  {summary.title}")
    if summary.date:
        text_console.print(f"  Date: {summary.date}")
    text_console.print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    text_console.print(f"{'=' * 80}\n")

    if summary.participants:
        text_console.print(f"Participants: {', '.join(summary.participants)}\n")

    text_console.print("SUMMARY")
    text_console.print("-" * 40)
    for bullet in summary.summary:
        text_console.print(f"  - {bullet}")
    text_console.print()

    if summary.key_decisions:
        text_console.print("KEY DECISIONS")
        text_console.print("-" * 40)
        for decision in summary.key_decisions:
            text_console.print(f"  > {decision}")
        text_console.print()

    if summary.action_items:
        text_console.print("ACTION ITEMS")
        text_console.print("-" * 40)
        for i, item in enumerate(summary.action_items, 1):
            due = item.due_date or "N/A"
            text_console.print(f"  {i}. [{item.priority.upper()}] {item.description}")
            text_console.print(f"     Assignee: {item.assignee}  |  Due: {due}")
        text_console.print()

    txt_path.write_text(buf.getvalue(), encoding="utf-8")
    return txt_path


def save_markdown(summary: MeetingSummary, output_path: Path) -> Path:
    """Save meeting summary as a Markdown file."""
    md_path = output_path.with_suffix(".md")
    lines = [
        f"# {summary.title}",
        "",
    ]
    if summary.date:
        lines.append(f"**Date:** {summary.date}  ")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  ")
    if summary.participants:
        lines.append(f"**Participants:** {', '.join(summary.participants)}")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    for bullet in summary.summary:
        lines.append(f"- {bullet}")
    lines.append("")

    if summary.key_decisions:
        lines.append("## Key Decisions")
        lines.append("")
        for decision in summary.key_decisions:
            lines.append(f"- {decision}")
        lines.append("")

    if summary.action_items:
        lines.append("## Action Items")
        lines.append("")
        lines.append("| # | Task | Assignee | Due Date | Priority |")
        lines.append("|---|------|----------|----------|----------|")
        for i, item in enumerate(summary.action_items, 1):
            due = item.due_date or "-"
            lines.append(f"| {i} | {item.description} | {item.assignee} | {due} | {item.priority.upper()} |")
        lines.append("")

    if summary.transcript:
        lines.append("## Transcript")
        lines.append("")
        lines.append("<details>")
        lines.append("<summary>Click to expand full transcript</summary>")
        lines.append("")
        lines.append(summary.transcript)
        lines.append("")
        lines.append("</details>")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path


def save_json(summary: MeetingSummary, output_path: Path) -> Path:
    """Save meeting summary as a JSON file."""
    json_path = output_path.with_suffix(".json")
    data = summary.model_dump()
    data.pop("transcript", None)
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return json_path
