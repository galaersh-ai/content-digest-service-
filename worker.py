"""
Local Worker for Content Digest Service.
Polls VPS API, processes tasks with Whisper + Ollama.
"""
import sys
import time
import sqlite3
import subprocess
from pathlib import Path

import httpx

# Config
API_URL = "http://localhost:8000"  # Change to VPS IP in production
POLL_INTERVAL = 10  # seconds
WHISPER_MODEL = "medium"
OLLAMA_MODEL = "mistral:7b-instruct-q4_K_M"
DATA_DIR = Path(__file__).parent / "data"


def download_audio(url: str) -> tuple[str, str]:
    """Download audio from YouTube."""
    print(f"  [1/3] Downloading: {url[:50]}...")

    audio_dir = DATA_DIR / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    output_path = audio_dir / "%(id)s.%(ext)s"

    # First get title
    title_result = subprocess.run(
        ["yt-dlp", "--print", "title", "--no-playlist", url],
        capture_output=True, text=True
    )
    title = title_result.stdout.strip() or "Unknown"

    # Download audio
    cmd = [
        "yt-dlp", "-x",
        "--audio-format", "mp3",
        "--audio-quality", "5",
        "-o", str(output_path),
        "--no-playlist",
        url
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception(f"yt-dlp failed: {result.stderr}")

    # Find the downloaded mp3 file (most recently modified)
    mp3_files = sorted(audio_dir.glob("*.mp3"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not mp3_files:
        raise Exception(f"No mp3 file found in {audio_dir}")

    audio_file = str(mp3_files[0])
    print(f"  ✓ Downloaded: {title[:40]}")
    return audio_file, title


def transcribe(audio_path: str) -> str:
    """Transcribe with Whisper."""
    print("  [2/3] Transcribing...")

    from faster_whisper import WhisperModel
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute = "float16" if device == "cuda" else "int8"

    model = WhisperModel(WHISPER_MODEL, device=device, compute_type=compute)
    segments, info = model.transcribe(audio_path, language=None)

    transcript = " ".join([s.text for s in segments])

    print(f"  ✓ Transcribed: {len(transcript.split())} words ({info.language})")

    # Free memory
    del model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return transcript


def summarize(text: str, title: str) -> str:
    """Summarize with Ollama."""
    print("  [3/3] Summarizing...")

    import ollama

    # Truncate if too long
    if len(text) > 8000:
        text = text[:8000] + "..."

    prompt = f"""Создай краткое саммари на русском языке.

Формат:
📌 TL;DR (2-3 предложения)

🔑 Ключевые идеи:
• идея 1
• идея 2
• идея 3

Название: {title}

Текст:
{text}
"""

    response = ollama.generate(
        model=OLLAMA_MODEL,
        prompt=prompt,
        options={"num_predict": 500, "temperature": 0.7}
    )

    summary = response['response'].strip()
    print(f"  ✓ Summary: {len(summary)} chars")

    return summary


def process_task(task: dict) -> str:
    """Process a single task."""
    url = task['url']
    task_id = task['id']

    print(f"\n{'='*50}")
    print(f"Processing task #{task_id}")
    print(f"URL: {url[:60]}...")
    print('='*50)

    start = time.time()

    # YouTube
    if "youtube.com" in url or "youtu.be" in url:
        audio_path, title = download_audio(url)
        transcript = transcribe(audio_path)
        summary = summarize(transcript, title)
    else:
        # Article (TODO: implement)
        summary = "⚠️ Статьи пока не поддерживаются"

    duration = time.time() - start
    print(f"\n✓ Done in {duration:.0f}s")

    return summary


def poll_and_process():
    """Main worker loop."""
    client = httpx.Client(timeout=30)

    print(f"🔄 Worker started")
    print(f"📡 API: {API_URL}")
    print(f"⏱ Poll interval: {POLL_INTERVAL}s")
    print()

    while True:
        try:
            # Get pending tasks
            response = client.get(f"{API_URL}/tasks/pending")
            tasks = response.json().get("tasks", [])

            if not tasks:
                print(".", end="", flush=True)
                time.sleep(POLL_INTERVAL)
                continue

            print(f"\n📥 Found {len(tasks)} task(s)")

            for task in tasks:
                task_id = task['id']

                # Claim task
                try:
                    client.post(f"{API_URL}/tasks/{task_id}/claim")
                except:
                    continue  # Already claimed

                # Process
                try:
                    result = process_task(task)
                    client.post(
                        f"{API_URL}/tasks/{task_id}/result",
                        json={"task_id": task_id, "status": "completed", "result": result}
                    )
                except Exception as e:
                    print(f"❌ Error: {e}")
                    client.post(
                        f"{API_URL}/tasks/{task_id}/result",
                        json={"task_id": task_id, "status": "failed", "error": str(e)}
                    )

        except httpx.ConnectError:
            print(f"\n⚠️ Cannot connect to {API_URL}")
        except Exception as e:
            print(f"\n❌ Error: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    poll_and_process()
