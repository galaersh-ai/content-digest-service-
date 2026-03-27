"""
Test 3: Full Pipeline
YouTube URL в†’ yt-dlp в†’ Whisper в†’ Ollama в†’ Result
"""
import sys
import os
import time
import sqlite3
import tempfile
import subprocess
from pathlib import Path

# Config
WHISPER_MODEL = "medium"
OLLAMA_MODEL = "mistral:7b-instruct-q4_K_M"
DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "test.db"

def init_db():
    """Initialize SQLite database."""
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "audio").mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY,
            url TEXT,
            title TEXT,
            transcript TEXT,
            summary TEXT,
            duration_sec REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

def download_audio(url: str) -> tuple[str, str]:
    """Download audio from YouTube using yt-dlp."""
    print("\n[1/4] Downloading audio...")

    output_path = DATA_DIR / "audio" / "%(id)s.%(ext)s"

    cmd = [
        "yt-dlp",
        "-x",                          # Extract audio
        "--audio-format", "mp3",
        "--audio-quality", "5",        # Medium quality (smaller file)
        "-o", str(output_path),
        "--print", "filename",
        "--print", "title",
        "--no-playlist",
        url
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception(f"yt-dlp failed: {result.stderr}")

    lines = result.stdout.strip().split('\n')
    audio_file = lines[-2] if len(lines) >= 2 else lines[0]
    title = lines[-1] if len(lines) >= 2 else "Unknown"

    # yt-dlp РІС‹РІРѕРґРёС‚ РїСѓС‚СЊ СЃ .webm, РЅРѕ РєРѕРЅРІРµСЂС‚РёС‚ РІ .mp3
    audio_file = audio_file.rsplit('.', 1)[0] + '.mp3'

    print(f"  вњ“ Title: {title}")
    print(f"  вњ“ File: {audio_file}")

    return audio_file, title

def transcribe(audio_path: str) -> str:
    """Transcribe audio with Whisper."""
    print("\n[2/4] Transcribing with Whisper...")

    from faster_whisper import WhisperModel
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute = "float16" if device == "cuda" else "int8"

    print(f"  Loading model ({WHISPER_MODEL}) on {device}...")
    start = time.time()

    model = WhisperModel(WHISPER_MODEL, device=device, compute_type=compute)

    print(f"  Transcribing...")
    segments, info = model.transcribe(audio_path, language=None)

    text_parts = []
    for segment in segments:
        text_parts.append(segment.text)

    transcript = " ".join(text_parts)
    duration = time.time() - start

    print(f"  вњ“ Language: {info.language}")
    print(f"  вњ“ Duration: {info.duration:.0f}s audio в†’ {duration:.0f}s processing")
    print(f"  вњ“ Speed: {info.duration/duration:.1f}x realtime")
    print(f"  вњ“ Words: {len(transcript.split())}")

    # Free GPU memory
    del model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return transcript

def summarize(text: str, title: str) -> str:
    """Summarize with Ollama."""
    print("\n[3/4] Summarizing with Ollama...")

    import ollama

    # Truncate if too long
    max_chars = 8000
    if len(text) > max_chars:
        text = text[:max_chars] + "..."
        print(f"  (Truncated to {max_chars} chars)")

    prompt = f"""РўС‹ вЂ” Р°СЃСЃРёСЃС‚РµРЅС‚ РґР»СЏ СЃРѕР·РґР°РЅРёСЏ СЃР°РјРјР°СЂРё.
РџСЂРѕР°РЅР°Р»РёР·РёСЂСѓР№ С‚СЂР°РЅСЃРєСЂРёРїС‚ Рё СЃРѕР·РґР°Р№ СЃС‚СЂСѓРєС‚СѓСЂРёСЂРѕРІР°РЅРЅРѕРµ СЃР°РјРјР°СЂРё РЅР° СЂСѓСЃСЃРєРѕРј СЏР·С‹РєРµ.

Р¤РѕСЂРјР°С‚ РѕС‚РІРµС‚Р°:
рџ“Њ TL;DR
(2-3 РїСЂРµРґР»РѕР¶РµРЅРёСЏ, СЃСѓС‚СЊ)

рџ”‘ РљР»СЋС‡РµРІС‹Рµ РёРґРµРё:
вЂў (РёРґРµСЏ 1)
вЂў (РёРґРµСЏ 2)
вЂў (РёРґРµСЏ 3)

рџ“ќ РџРѕРґСЂРѕР±РЅРµРµ:
(СЂР°Р·РІС‘СЂРЅСѓС‚РѕРµ РѕРїРёСЃР°РЅРёРµ, 3-5 РїСЂРµРґР»РѕР¶РµРЅРёР№)

---
РќР°Р·РІР°РЅРёРµ: {title}

РўСЂР°РЅСЃРєСЂРёРїС‚:
{text}
"""

    start = time.time()
    response = ollama.generate(
        model=OLLAMA_MODEL,
        prompt=prompt,
        options={
            "num_predict": 500,
            "temperature": 0.7
        }
    )

    summary = response['response'].strip()
    duration = time.time() - start
    tokens = response.get('eval_count', len(summary.split()))

    print(f"  вњ“ Generated {tokens} tokens in {duration:.1f}s")
    print(f"  вњ“ Speed: {tokens/duration:.1f} tokens/sec")

    return summary

def save_result(conn, url: str, title: str, transcript: str, summary: str, duration: float):
    """Save to SQLite."""
    print("\n[4/4] Saving result...")

    conn.execute(
        "INSERT INTO results (url, title, transcript, summary, duration_sec) VALUES (?, ?, ?, ?, ?)",
        [url, title, transcript, summary, duration]
    )
    conn.commit()
    print(f"  вњ“ Saved to {DB_PATH}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_pipeline.py <youtube_url>")
        print("Example: python test_pipeline.py https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        sys.exit(1)

    url = sys.argv[1]

    print("=" * 60)
    print("FULL PIPELINE TEST")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"Whisper: {WHISPER_MODEL}")
    print(f"Ollama: {OLLAMA_MODEL}")

    start_total = time.time()

    # Init
    conn = init_db()

    # Pipeline
    audio_path, title = download_audio(url)
    transcript = transcribe(audio_path)
    summary = summarize(transcript, title)

    total_duration = time.time() - start_total

    # Save
    save_result(conn, url, title, transcript, summary, total_duration)

    # Output
    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)
    print(summary)
    print("\n" + "-" * 60)
    print(f"Total time: {total_duration:.0f}s ({total_duration/60:.1f} min)")
    print("=" * 60)

    # Cleanup audio (optional)
    # os.remove(audio_path)

if __name__ == "__main__":
    main()
