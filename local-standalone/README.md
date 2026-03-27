# Local Standalone Test

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
cd local-standalone
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
