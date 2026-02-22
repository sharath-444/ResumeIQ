"""
Quick test: find a working free OpenRouter model.
Run: python test_openrouter.py
"""
import sys
import requests
import json
import os

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://resumeiq.app",
    "X-Title": "ResumeIQ",
}

MODELS = [
    "google/gemma-3-27b-it:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "nousresearch/deephermes-3-llama-3-8b-preview:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
]

MSG = [{"role": "user", "content": "What does ATS stand for in hiring? One sentence."}]

working_model = None
for model in MODELS:
    print(f"\nTrying: {model}")
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=HEADERS,
            json={"model": model, "messages": MSG, "max_tokens": 50},
            timeout=25,
        )
        data = r.json()
        if r.status_code == 200:
            reply = data["choices"][0]["message"]["content"]
            print(f"  SUCCESS! Reply: {reply[:120]}")
            working_model = model
            break
        else:
            err = data.get("error", {}).get("message", str(data))[:100]
            print(f"  FAILED {r.status_code}: {err}")
    except Exception as e:
        print(f"  EXCEPTION: {e}")

print("\n" + "=" * 60)
if working_model:
    print(f"Working model: {working_model}")
else:
    print("No working model found – all rate limited or unavailable.")
