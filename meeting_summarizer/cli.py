from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from .analyzer import analyze_transcript
from .formatter import display_terminal, save_json, save_markdown, save_txt
from .transcriber import transcribe_audio

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Meeting Summarizer & Action Item Extractor.

    Transcribe meeting audio, generate summaries, and extract action items.
    """


@cli.command()
@click.argument("audio_file", type=click.Path(exists=True, path_type=Path))
@click.option("--output-dir", "-o", type=click.Path(path_type=Path), default=None, help="Output directory for reports.")
@click.option("--model", "-m", default=None, help="LLM model override (default from LLM_MODEL env var).")
@click.option("--no-json", is_flag=True, help="Skip JSON output.")
@click.option("--no-markdown", is_flag=True, help="Skip Markdown output.")
def summarize(audio_file: Path, output_dir: Path | None, model: str, no_json: bool, no_markdown: bool):
    """Full pipeline: transcribe audio, summarize, and extract action items."""
    audio_file = audio_file.resolve()
    output_dir = (output_dir or audio_file.parent).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_base = output_dir / audio_file.stem

    console.print(f"\n[bold]Processing:[/bold] {audio_file.name}\n")

    # Step 1: Transcribe
    console.rule("[bold blue]Step 1: Transcription")
    transcript = transcribe_audio(audio_file)
    console.print(f"[green]Transcribed {len(transcript.split())} words.[/green]\n")

    # Save transcript
    transcript_path = output_base.with_suffix(".transcript.txt")
    transcript_path.write_text(transcript, encoding="utf-8")
    console.print(f"[dim]Transcript saved: {transcript_path}[/dim]\n")

    # Step 2: Analyze
    console.rule("[bold green]Step 2: Analysis")
    summary = analyze_transcript(transcript, model=model)
    summary.transcript = transcript

    # Step 3: Output
    console.rule("[bold yellow]Step 3: Results")
    display_terminal(summary)
    _save_outputs(summary, output_base, no_json, no_markdown)


@cli.command()
@click.argument("audio_file", type=click.Path(exists=True, path_type=Path))
@click.option("--output-dir", "-o", type=click.Path(path_type=Path), default=None, help="Output directory.")
def transcribe(audio_file: Path, output_dir: Path | None):
    """Transcribe audio to text (no analysis)."""
    audio_file = audio_file.resolve()
    output_dir = (output_dir or audio_file.parent).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"\n[bold]Transcribing:[/bold] {audio_file.name}\n")
    transcript = transcribe_audio(audio_file)

    transcript_path = output_dir / f"{audio_file.stem}.transcript.txt"
    transcript_path.write_text(transcript, encoding="utf-8")

    console.print(f"[green]Done! {len(transcript.split())} words transcribed.[/green]")
    console.print(f"[dim]Saved: {transcript_path}[/dim]")


@cli.command()
@click.argument("transcript_file", type=click.Path(exists=True, path_type=Path))
@click.option("--output-dir", "-o", type=click.Path(path_type=Path), default=None, help="Output directory for reports.")
@click.option("--model", "-m", default=None, help="LLM model override (default from LLM_MODEL env var).")
@click.option("--no-json", is_flag=True, help="Skip JSON output.")
@click.option("--no-markdown", is_flag=True, help="Skip Markdown output.")
def analyze(transcript_file: Path, output_dir: Path | None, model: str, no_json: bool, no_markdown: bool):
    """Analyze an existing transcript file (skip transcription)."""
    transcript_file = transcript_file.resolve()
    output_dir = (output_dir or transcript_file.parent).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    stem = transcript_file.stem
    if stem.endswith(".transcript"):
        stem = stem.removesuffix(".transcript")
    output_base = output_dir / stem

    console.print(f"\n[bold]Analyzing:[/bold] {transcript_file.name}\n")
    transcript = transcript_file.read_text(encoding="utf-8")

    console.rule("[bold green]Analysis")
    summary = analyze_transcript(transcript, model=model)
    summary.transcript = transcript

    console.rule("[bold yellow]Results")
    display_terminal(summary)
    _save_outputs(summary, output_base, no_json, no_markdown)


def _save_outputs(summary, output_base: Path, no_json: bool, no_markdown: bool) -> None:
    console.print()
    txt_path = save_txt(summary, output_base)
    console.print(f"[dim]Text report:     {txt_path}[/dim]")
    if not no_markdown:
        md_path = save_markdown(summary, output_base)
        console.print(f"[dim]Markdown report: {md_path}[/dim]")
    if not no_json:
        json_path = save_json(summary, output_base)
        console.print(f"[dim]JSON data:       {json_path}[/dim]")
    console.print()


if __name__ == "__main__":
    cli()
