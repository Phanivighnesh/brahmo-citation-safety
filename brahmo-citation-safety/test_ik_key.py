"""
test_ik_key.py — Verify your Indian Kanoon API key works.
Usage: python test_ik_key.py
"""
import os, pathlib, requests

def _load_env():
    env_path = pathlib.Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            os.environ[key.strip()] = val.strip()

_load_env()

api_key = os.environ.get("INDIAN_KANOON_API_KEY", "").strip()
if not api_key:
    print("ERROR: INDIAN_KANOON_API_KEY not set in .env")
    exit(1)

print(f"Testing IK API key: {api_key[:6]}...{api_key[-4:]}  (length: {len(api_key)})")
print()

try:
    resp = requests.post(
        "https://api.indiankanoon.org/search/",
        headers={
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"formInput": "(2021) 10 SCC 1"},
        timeout=15,
    )
    print(f"HTTP Status : {resp.status_code}")
    data = resp.json()
    print(f"found field : {data.get('found')}")
    docs = data.get("docs", [])
    print(f"docs count  : {len(docs)}")

    if resp.status_code == 200 and docs:
        print(f"\n✅ SUCCESS — Key works!")
        print(f"   First result: {docs[0].get('title', 'n/a')}")
    elif resp.status_code == 200:
        print(f"\n⚠️  Key works but no docs returned for test citation")
    elif resp.status_code == 401:
        print(f"\n❌ 401 — Key rejected. Re-copy from api.indiankanoon.org")
    else:
        print(f"\n⚠️  Unexpected: {resp.status_code} — {resp.text[:200]}")

except Exception as e:
    print(f"\n❌ Error: {e}")
