"""
Test 1: Whisper РЅР° GPU
РџСЂРѕРІРµСЂСЏРµС‚ С‡С‚Рѕ Whisper Р·Р°РіСЂСѓР¶Р°РµС‚СЃСЏ Рё СЂР°Р±РѕС‚Р°РµС‚ РЅР° GPU.
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
            print(f"  вњ“ CUDA available: {torch.cuda.get_device_name(0)}")
            print(f"  вњ“ VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        else:
            print("  вњ— CUDA not available, will use CPU (slow!)")
    except ImportError:
        print("  вњ— PyTorch not installed")
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
        print(f"  вњ“ Loaded in {load_time:.1f}s")
    except Exception as e:
        print(f"  вњ— Failed: {e}")
        sys.exit(1)

    # Test transcription (synthetic)
    print("\n[3/3] Testing transcription...")
    print("  (Р”Р»СЏ РїРѕР»РЅРѕРіРѕ С‚РµСЃС‚Р° Р·Р°РїСѓСЃС‚РёС‚Рµ test_pipeline.py СЃ YouTube URL)")

    print("\n" + "=" * 50)
    print("вњ“ Whisper ready!")
    print("=" * 50)

    # Memory info
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1024**3
        print(f"\nVRAM used: {allocated:.2f} GB")

if __name__ == "__main__":
    main()
