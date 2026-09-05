from setuptools import setup, find_packages

setup(
    name="meeting-summarizer",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
        "anthropic>=0.40.0",
        "click>=8.0.0",
        "rich>=13.0.0",
        "pydantic>=2.0.0",
        "pydub>=0.25.1",
    ],
    entry_points={
        "console_scripts": [
            "meeting-summarizer=meeting_summarizer.cli:cli",
        ],
    },
    python_requires=">=3.10",
)
