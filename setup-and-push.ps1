# PowerShell script to create all project files and push to GitHub
# Run: .\setup-and-push.ps1

$ErrorActionPreference = "Stop"

Write-Host "Creating project files..." -ForegroundColor Cyan

# .gitignore
@'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.venv/
ENV/
env/
.eggs/
*.egg-info/
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Environment & Secrets
.env
.env.local
.env.*.local
*.pem
*.key
secrets/

# SQLite databases
*.db
*.sqlite
*.sqlite3

# Audio/Video files (downloaded content)
*.mp3
*.mp4
*.m4a
*.wav
*.webm
*.opus
audio/
video/
downloads/
temp/
tmp/

# Whisper models (downloaded separately)
models/
*.bin
*.pt

# Ollama (managed by ollama itself)
.ollama/

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Build
dist/
build/
'@ | Out-File -FilePath ".gitignore" -Encoding utf8

# requirements.txt
@'
# Whisper (GPU)
faster-whisper>=1.0.0
torch>=2.0.0

# YouTube download
yt-dlp>=2024.1.0

# Ollama client
ollama>=0.2.0

# HTTP (for future VPS connection)
httpx>=0.27.0
'@ | Out-File -FilePath "requirements.txt" -Encoding utf8

# README.md
@'
# Content Digest Service - Local Standalone

Полностью изолированный тестовый сетап для проверки pipeline на ПК.
Без VPS, без Docker — просто Python + Ollama.

## Требования

- Windows 10/11
- Python 3.10+
- NVIDIA GPU (P106-100 / 6GB)
- Ollama установлен

## Быстрый старт

```powershell
# 1. Создать виртуальное окружение
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Скачать модель Ollama (один раз)
ollama pull mistral:7b-instruct-q4_K_M

# 4. Запустить тест
python test_pipeline.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

## Что тестируется

1. **yt-dlp** — скачивание аудио с YouTube
2. **Whisper** — транскрипция (GPU)
3. **Ollama** — саммаризация (GPU)
4. **SQLite** — сохранение результата

## Структура

```
local-standalone/
├── README.md
├── requirements.txt
├── test_pipeline.py      # Главный тест
├── test_whisper.py       # Только Whisper
├── test_ollama.py        # Только Ollama
└── data/                 # Временные файлы
    ├── audio/
    └── test.db
```
'@ | Out-File -FilePath "README.md" -Encoding utf8

# test_whisper.py
@'
"""
Test 1: Whisper на GPU
Проверяет что Whisper загружается и работает на GPU.
"""
import sys
import time

def main():
    print("=" * 50)
    print("TEST: Whisper on GPU")
    print("=" * 50)

    # Check CUDA
    print("\n[1/3] Checking CUDA...")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"  ✓ CUDA available: {torch.cuda.get_device_name(0)}")
            print(f"  ✓ VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        else:
            print("  ✗ CUDA not available, will use CPU (slow!)")
    except ImportError:
        print("  ✗ PyTorch not installed")
        sys.exit(1)

    # Load Whisper
    print("\n[2/3] Loading Whisper medium...")
    try:
        from faster_whisper import WhisperModel

        start = time.time()
        model = WhisperModel(
            "medium",
            device="cuda",
            compute_type="float16"
        )
        load_time = time.time() - start
        print(f"  ✓ Loaded in {load_time:.1f}s")
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        sys.exit(1)

    # Test transcription (synthetic)
    print("\n[3/3] Testing transcription...")
    print("  (Для полного теста запустите test_pipeline.py с YouTube URL)")

    print("\n" + "=" * 50)
    print("✓ Whisper ready!")
    print("=" * 50)

    # Memory info
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1024**3
        print(f"\nVRAM used: {allocated:.2f} GB")

if __name__ == "__main__":
    main()
'@ | Out-File -FilePath "test_whisper.py" -Encoding utf8

# test_ollama.py
@'
"""
Test 2: Ollama LLM
Проверяет что Ollama работает и отвечает.
"""
import sys
import time

MODEL = "mistral:7b-instruct-q4_K_M"

def main():
    print("=" * 50)
    print("TEST: Ollama LLM")
    print("=" * 50)

    # Check Ollama
    print(f"\n[1/3] Checking Ollama ({MODEL})...")
    try:
        import ollama

        # List models
        models = ollama.list()
        model_names = [m['name'] for m in models.get('models', [])]

        if MODEL in model_names or MODEL.split(':')[0] in str(model_names):
            print(f"  ✓ Model available")
        else:
            print(f"  ✗ Model not found. Run: ollama pull {MODEL}")
            print(f"  Available: {model_names}")
            sys.exit(1)

    except Exception as e:
        print(f"  ✗ Ollama not running: {e}")
        print("  Start Ollama first!")
        sys.exit(1)

    # Test generation
    print("\n[2/3] Testing generation...")
    test_prompt = "Explain AI in one sentence."

    start = time.time()
    try:
        response = ollama.generate(
            model=MODEL,
            prompt=test_prompt,
            options={"num_predict": 50}
        )
        gen_time = time.time() - start

        text = response['response'].strip()
        tokens = response.get('eval_count', len(text.split()))
        speed = tokens / gen_time if gen_time > 0 else 0

        print(f"  ✓ Response: {text[:100]}...")
        print(f"  ✓ Speed: {speed:.1f} tokens/sec")
        print(f"  ✓ Time: {gen_time:.1f}s")

    except Exception as e:
        print(f"  ✗ Failed: {e}")
        sys.exit(1)

    # Test summarization prompt
    print("\n[3/3] Testing summarization prompt...")

    test_text = """
    Artificial intelligence is transforming how we work and live.
    Machine learning models can now write code, create art, and have conversations.
    However, there are concerns about job displacement and AI safety.
    Experts recommend careful regulation and ethical guidelines.
    """

    summary_prompt = f"""Summarize this text in Russian. Be concise (2-3 sentences).

Text:
{test_text}

Summary in Russian:"""

    start = time.time()
    response = ollama.generate(
        model=MODEL,
        prompt=summary_prompt,
        options={"num_predict": 150}
    )

    print(f"  ✓ Summary: {response['response'].strip()}")
    print(f"  ✓ Time: {time.time() - start:.1f}s")

    print("\n" + "=" * 50)
    print("✓ Ollama ready!")
    print("=" * 50)

if __name__ == "__main__":
    main()
'@ | Out-File -FilePath "test_ollama.py" -Encoding utf8

# test_pipeline.py
@'
"""
Test 3: Full Pipeline
YouTube URL → yt-dlp → Whisper → Ollama → Result
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

    # yt-dlp выводит путь с .webm, но конвертит в .mp3
    audio_file = audio_file.rsplit('.', 1)[0] + '.mp3'

    print(f"  ✓ Title: {title}")
    print(f"  ✓ File: {audio_file}")

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

    print(f"  ✓ Language: {info.language}")
    print(f"  ✓ Duration: {info.duration:.0f}s audio → {duration:.0f}s processing")
    print(f"  ✓ Speed: {info.duration/duration:.1f}x realtime")
    print(f"  ✓ Words: {len(transcript.split())}")

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

    prompt = f"""Ты — ассистент для создания саммари.
Проанализируй транскрипт и создай структурированное саммари на русском языке.

Формат ответа:
📌 TL;DR
(2-3 предложения, суть)

🔑 Ключевые идеи:
• (идея 1)
• (идея 2)
• (идея 3)

📝 Подробнее:
(развёрнутое описание, 3-5 предложений)

---
Название: {title}

Транскрипт:
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

    print(f"  ✓ Generated {tokens} tokens in {duration:.1f}s")
    print(f"  ✓ Speed: {tokens/duration:.1f} tokens/sec")

    return summary

def save_result(conn, url: str, title: str, transcript: str, summary: str, duration: float):
    """Save to SQLite."""
    print("\n[4/4] Saving result...")

    conn.execute(
        "INSERT INTO results (url, title, transcript, summary, duration_sec) VALUES (?, ?, ?, ?, ?)",
        [url, title, transcript, summary, duration]
    )
    conn.commit()
    print(f"  ✓ Saved to {DB_PATH}")

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
'@ | Out-File -FilePath "test_pipeline.py" -Encoding utf8

Write-Host "✓ Files created!" -ForegroundColor Green

# Git init and push
Write-Host "`nInitializing git..." -ForegroundColor Cyan
git init
git branch -M main
git add .
git commit -m "Initial commit: project structure and test scripts"
git remote add origin https://github.com/galaersh-ai/content-digest-service-.git
git push -u origin main

Write-Host "`n✓ Done! Check: https://github.com/galaersh-ai/content-digest-service-" -ForegroundColor Green
