"""
check_models.py
---------------
Run this ONCE to see which Gemini models your API key can actually use.
Usage: python check_models.py
"""
import os, pathlib

def _load_env():
    env_path = pathlib.Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

_load_env()

from google import genai

api_key = os.environ.get("GEMINI_API_KEY", "")
if not api_key:
    print("ERROR: GEMINI_API_KEY not set in .env")
    exit(1)

client = genai.Client(api_key=api_key)

print("Models available on your API key:\n")
generative = []
for m in client.models.list():
    if "generateContent" in (m.supported_actions or []):
        generative.append(m.name)
        print(f"  {m.name}")

if not generative:
    print("  (none found — check your API key)")
else:
    print(f"\nRecommended to use: {generative[0]}")
    print("\nCopy the model name above into your .env as:")
    print(f"  GEMINI_MODEL={generative[0]}")
