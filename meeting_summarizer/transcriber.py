from __future__ import annotations

import math
import os
from pathlib import Path

import click
from openai import OpenAI
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import MAX_WHISPER_FILE_SIZE, SUPPORTED_AUDIO_FORMATS, get_openai_key


def validate_audio_file(file_path: Path) -> None:
    if not file_path.exists():
        raise click.ClickException(f"File not found: {file_path}")
    if file_path.suffix.lower() not in SUPPORTED_AUDIO_FORMATS:
        raise click.ClickException(
            f"Unsupported format: {file_path.suffix}\n"
            f"Supported: {', '.join(sorted(SUPPORTED_AUDIO_FORMATS))}"
        )


def transcribe_audio(file_path: Path) -> str:
    """Transcribe an audio file using OpenAI Whisper API."""
    validate_audio_file(file_path)
    client = OpenAI(api_key=get_openai_key())
    file_size = file_path.stat().st_size

    if file_size <= MAX_WHISPER_FILE_SIZE:
        return _transcribe_single(client, file_path)
    return _transcribe_chunked(client, file_path, file_size)


def _transcribe_single(client: OpenAI, file_path: Path) -> str:
    with Progress(SpinnerColumn(), TextColumn("[bold blue]Transcribing audio...")) as progress:
        progress.add_task("transcribe", total=None)
        with open(file_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="text",
            )
    return response


def _transcribe_chunked(client: OpenAI, file_path: Path, file_size: int) -> str:
    """Split large files into chunks and transcribe each."""
    try:
        from pydub import AudioSegment
    except ImportError:
        raise click.ClickException(
            "pydub is required for files >25MB. Install with: pip install pydub\n"
            "You also need ffmpeg installed for audio splitting."
        )

    chunk_duration_ms = 10 * 60 * 1000  # 10 minutes per chunk
    audio = AudioSegment.from_file(str(file_path))
    total_chunks = math.ceil(len(audio) / chunk_duration_ms)
    transcripts: list[str] = []

    with Progress(SpinnerColumn(), TextColumn("[bold blue]Transcribing chunk {task.completed}/{task.total}...")) as progress:
        task = progress.add_task("transcribe", total=total_chunks)
        for i in range(total_chunks):
            start = i * chunk_duration_ms
            end = min((i + 1) * chunk_duration_ms, len(audio))
            chunk = audio[start:end]

            chunk_path = file_path.parent / f"_chunk_{i}.mp3"
            chunk.export(str(chunk_path), format="mp3")
            try:
                with open(chunk_path, "rb") as f:
                    response = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=f,
                        response_format="text",
                    )
                transcripts.append(response)
            finally:
                chunk_path.unlink(missing_ok=True)
            progress.advance(task)

    return " ".join(transcripts)
