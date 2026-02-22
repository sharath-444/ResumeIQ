"""Quick probe: test each model and print the exact status + error."""
import requests, json, os

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
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "nousresearch/deephermes-3-llama-3-8b-preview:free",
    "deepseek/deepseek-r1:free",
    "qwen/qwen3-8b:free",
    "microsoft/phi-4-reasoning-plus:free",
    "openrouter/auto",
]

MSG = [{"role": "user", "content": "Reply with exactly: HELLO"}]

for m in MODELS:
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=HEADERS,
            json={"model": m, "messages": MSG, "max_tokens": 20},
            timeout=20,
        )
        data = r.json()
        if r.status_code == 200:
            reply = data["choices"][0]["message"]["content"][:50]
            model_used = data.get("model", m)
            print(f"OK  [{r.status_code}] {m} => {reply!r} (via {model_used})")
        else:
            err = data.get("error", {}).get("message", str(data))[:90]
            print(f"ERR [{r.status_code}] {m} => {err}")
    except Exception as e:
        print(f"EXC {m} => {str(e)[:80]}")
