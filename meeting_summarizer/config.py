import os
import click


def get_api_config() -> dict:
    """Return API configuration from environment variables.

    Set these env vars to configure the LLM provider:
      LLM_API_KEY      - API key for the provider
      LLM_BASE_URL     - Base URL (e.g. https://integrate.api.nvidia.com/v1)
      LLM_MODEL        - Model name (e.g. google/gemma-4-31b-it)

    Falls back to ANTHROPIC_API_KEY / ANTHROPIC_AUTH_TOKEN and Anthropic defaults
    if the LLM_* vars are not set.
    """
    api_key = os.environ.get("LLM_API_KEY", "")
    base_url = os.environ.get("LLM_BASE_URL", "")
    model = os.environ.get("LLM_MODEL", "")

    if api_key and base_url:
        return {
            "api_key": api_key,
            "base_url": base_url,
            "model": model or "gpt-3.5-turbo",
        }

    api_key = (
        os.environ.get("ANTHROPIC_API_KEY", "")
        or os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    )
    if not api_key:
        raise click.ClickException(
            "No LLM API credentials found.\n"
            "Option 1 (any OpenAI-compatible provider):\n"
            "  set LLM_API_KEY=your-key\n"
            "  set LLM_BASE_URL=https://provider.example.com/v1\n"
            "  set LLM_MODEL=model-name\n"
            "Option 2 (Anthropic):\n"
            "  set ANTHROPIC_API_KEY=sk-ant-..."
        )

    base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")

    return {
        "api_key": api_key,
        "base_url": base_url,
        "model": model or "bedrock.anthropic.claude-sonnet-4-6",
        "is_anthropic": True,
    }


def get_openai_key() -> str:
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        raise click.ClickException(
            "OPENAI_API_KEY environment variable is not set.\n"
            "Set it with: set OPENAI_API_KEY=sk-..."
        )
    return key


SUPPORTED_AUDIO_FORMATS = {".mp3", ".mp4", ".m4a", ".wav", ".webm", ".mpeg", ".mpga", ".oga", ".ogg", ".flac"}
MAX_WHISPER_FILE_SIZE = 25 * 1024 * 1024  # 25MB
