# Content Digest Service - Local Standalone

РџРѕР»РЅРѕСЃС‚СЊСЋ РёР·РѕР»РёСЂРѕРІР°РЅРЅС‹Р№ С‚РµСЃС‚РѕРІС‹Р№ СЃРµС‚Р°Рї РґР»СЏ РїСЂРѕРІРµСЂРєРё pipeline РЅР° РџРљ.
Р‘РµР· VPS, Р±РµР· Docker вЂ” РїСЂРѕСЃС‚Рѕ Python + Ollama.

## РўСЂРµР±РѕРІР°РЅРёСЏ

- Windows 10/11
- Python 3.10+
- NVIDIA GPU (P106-100 / 6GB)
- Ollama СѓСЃС‚Р°РЅРѕРІР»РµРЅ

## Р‘С‹СЃС‚СЂС‹Р№ СЃС‚Р°СЂС‚

```powershell
# 1. РЎРѕР·РґР°С‚СЊ РІРёСЂС‚СѓР°Р»СЊРЅРѕРµ РѕРєСЂСѓР¶РµРЅРёРµ
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. РЈСЃС‚Р°РЅРѕРІРёС‚СЊ Р·Р°РІРёСЃРёРјРѕСЃС‚Рё
pip install -r requirements.txt

# 3. РЎРєР°С‡Р°С‚СЊ РјРѕРґРµР»СЊ Ollama (РѕРґРёРЅ СЂР°Р·)
ollama pull mistral:7b-instruct-q4_K_M

# 4. Р—Р°РїСѓСЃС‚РёС‚СЊ С‚РµСЃС‚
python test_pipeline.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

## Р§С‚Рѕ С‚РµСЃС‚РёСЂСѓРµС‚СЃСЏ

1. **yt-dlp** вЂ” СЃРєР°С‡РёРІР°РЅРёРµ Р°СѓРґРёРѕ СЃ YouTube
2. **Whisper** вЂ” С‚СЂР°РЅСЃРєСЂРёРїС†РёСЏ (GPU)
3. **Ollama** вЂ” СЃР°РјРјР°СЂРёР·Р°С†РёСЏ (GPU)
4. **SQLite** вЂ” СЃРѕС…СЂР°РЅРµРЅРёРµ СЂРµР·СѓР»СЊС‚Р°С‚Р°

## РЎС‚СЂСѓРєС‚СѓСЂР°

```
local-standalone/
в”њв”Ђв”Ђ README.md
в”њв”Ђв”Ђ requirements.txt
в”њв”Ђв”Ђ test_pipeline.py      # Р“Р»Р°РІРЅС‹Р№ С‚РµСЃС‚
в”њв”Ђв”Ђ test_whisper.py       # РўРѕР»СЊРєРѕ Whisper
в”њв”Ђв”Ђ test_ollama.py        # РўРѕР»СЊРєРѕ Ollama
в””в”Ђв”Ђ data/                 # Р’СЂРµРјРµРЅРЅС‹Рµ С„Р°Р№Р»С‹
    в”њв”Ђв”Ђ audio/
    в””в”Ђв”Ђ test.db
```
