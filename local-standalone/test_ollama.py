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
