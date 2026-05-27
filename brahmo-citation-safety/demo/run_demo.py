"""
run_demo.py — BRAHMO Citation Safety Engine live demo.
"""

import sys, os, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

def _load_env():
    env_path = pathlib.Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            os.environ[key.strip()] = val.strip()  # always overwrite

_load_env()

GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
IK_KEY     = os.environ.get("INDIAN_KANOON_API_KEY", "")
MODEL_NAME = os.environ.get("GEMINI_MODEL", "auto-discover")
MOCK_IK    = not bool(IK_KEY)

if not GEMINI_KEY:
    print("ERROR: GEMINI_API_KEY not set in .env")
    sys.exit(1)

# ── If IK key is live, clear stale mock-mode cache entries ───────────────────
if not MOCK_IK:
    from src.database import clear_unverified_cache
    clear_unverified_cache()

from src.llm_gemini import compare

print("=" * 60)
print("  BRAHMO Citation Safety Engine -- Live Demo")
print("=" * 60)
print(f"  Model  : {MODEL_NAME}")
print(f"  Gemini : {GEMINI_KEY[:8]}...")
print(f"  IK API : {'LIVE' if not MOCK_IK else 'MOCK (add INDIAN_KANOON_API_KEY for live)'}")
print()


def run_scenario(number, title, matter, query):
    print("\n" + "=" * 60)
    print(f"  SCENARIO {number} -- {title}")
    print(f"  Matter : {matter}")
    print(f"  Query  : {query}")
    print("=" * 60)

    result = compare(query, ik_api_key=IK_KEY, mock_ik=MOCK_IK)

    print("\n--- GENERIC GEMINI (no verification) ---")
    print(result["generic"])

    print("\n--- YOUR SYSTEM (citation-verified) ---")
    print(result["enhanced"])

    print(result["report_text"])

    if result["report"].section_alerts:
        print("  SECTION ALERTS:")
        for a in result["report"].section_alerts:
            print(f"    {a.old_section} -> {a.new_section}  (x{a.occurrences})")
        print()


run_scenario(1, "The Hallucinated Citation",
    "Rajesh Kumar -- Anticipatory Bail under Section 482 BNSS",
    "List 6 Supreme Court cases on anticipatory bail in economic offences. For each case give the full SCC citation in format (YYYY) Vol SCC Page.")

run_scenario(2, "The Repealed Law Catastrophe",
    "Criminal complaint -- cheating case",
    "Draft a short criminal complaint for cheating under Section 420 IPC and criminal breach of trust under Section 406 IPC. Cite 3 relevant cases with full SCC citations.")

run_scenario(3, "The Impossible Citation",
    "NDPS Act bail research",
    "List 5 Supreme Court cases on bail under NDPS Act from 2019-2024. Give full SCC citations in format (YYYY) Vol SCC Page for each.")

run_scenario(4, "The Format Error",
    "Delhi HC -- criminal revision, Section 482 BNSS",
    "List 4 Delhi High Court decisions on inherent powers under Section 482 CrPC or Section 528 BNSS. Give full SCC OnLine citations.")

print("\n" + "=" * 60)
print("  All 4 scenarios complete.")
if MOCK_IK:
    print("  Tip: Add INDIAN_KANOON_API_KEY to .env for live IK verification.")
print("=" * 60)
