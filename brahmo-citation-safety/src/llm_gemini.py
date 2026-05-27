"""
llm_gemini.py — Gemini client for BRAHMO Citation Safety Engine.
"""

import os, re, time
from typing import Tuple, List
from google import genai
from google.genai import types
from google.genai.errors import ClientError

from .pipeline import run_pipeline
from .citation_annotator import render_report
from .types import PipelineReport
from .database import get_connection

LEGAL_SYSTEM_PROMPT = """You are a senior Indian legal research assistant.
When answering legal questions, you MUST:

1. Always include 5-7 specific case citations in your response.
2. Use FULL citation format inline: case name followed immediately by citation.
   Example: "In Siddharth v. State of UP (2021) 10 SCC 1, the Court held..."
3. Use ONLY these citation formats:
     SCC   : (YYYY) Vol SCC Page        e.g. (2021) 10 SCC 1
     AIR   : AIR YYYY SC Page           e.g. AIR 2023 SC 456  
     OnLine: YYYY SCC OnLine Del NNNN   e.g. 2023 SCC OnLine Del 789
4. Use current law: BNS not IPC, BNSS not CrPC, BSA not IEA.
5. Keep response under 600 words but ALWAYS include all citations.
6. Do NOT truncate or omit citations — they are the most important part.

CRITICAL: Every citation must appear in exactly one of the three formats above.
"""

_PREFER = ["flash-lite", "flash", "pro"]


def _get_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in .env")
    return genai.Client(api_key=api_key)


def _get_model_list(client: genai.Client) -> List[str]:
    override = os.environ.get("GEMINI_MODEL", "").strip()
    if override:
        print(f"  [Gemini] Using GEMINI_MODEL: {override}")
        return [override]

    available = []
    try:
        for m in client.models.list():
            if "generateContent" in (m.supported_actions or []):
                available.append(m.name)
    except Exception as e:
        print(f"  [Gemini] Could not list models: {e}")
        available = ["models/gemini-2.0-flash-lite", "models/gemini-2.0-flash",
                     "models/gemini-2.5-flash", "models/gemini-1.5-flash"]

    def _rank(n):
        n = n.lower()
        for i, kw in enumerate(_PREFER):
            if kw in n: return i
        return len(_PREFER)

    available.sort(key=_rank)
    print(f"  [Gemini] Auto-discovered: {available[:3]}")
    return available


def _parse_retry_delay(msg: str) -> int:
    m = re.search(r"retry in (\d+)", msg, re.IGNORECASE)
    return int(m.group(1)) + 2 if m else 20


def _generate_with_retry(client: genai.Client, query: str) -> str:
    models = _get_model_list(client)
    for model in models:
        for attempt in range(3):
            try:
                print(f"  [Gemini] Trying: {model} (attempt {attempt + 1})")
                response = client.models.generate_content(
                    model=model,
                    config=types.GenerateContentConfig(
                        system_instruction=LEGAL_SYSTEM_PROMPT,
                        max_output_tokens=3000,   # increased — was 1500, cut off citations
                    ),
                    contents=query,
                )
                print(f"  [Gemini] Success")
                return response.text
            except ClientError as e:
                code = e.status_code if hasattr(e, "status_code") else 0
                msg  = str(e)
                if code == 429:
                    delay = _parse_retry_delay(msg)
                    if attempt < 2:
                        print(f"  [Gemini] Rate limited — waiting {delay}s...")
                        time.sleep(delay)
                    else:
                        print(f"  [Gemini] Quota exhausted for {model}, moving on...")
                        break
                elif code == 404:
                    print(f"  [Gemini] {model} not on your account — skipping")
                    break
                else:
                    raise RuntimeError(f"Gemini error {code}: {msg}")

    raise RuntimeError(
        "All Gemini models failed.\n"
        "  Run: python check_models.py  to see available models\n"
        "  Set: GEMINI_MODEL=<name> in .env to force one"
    )


def ask_generic(query: str) -> str:
    return _generate_with_retry(_get_client(), query)


def ask_enhanced(query, ik_api_key=None, mock_ik=False):
    raw = ask_generic(query)
    conn = get_connection()
    annotated, report = run_pipeline(
        text      = raw,
        conn      = conn,
        api_key   = ik_api_key or os.environ.get("INDIAN_KANOON_API_KEY", ""),
        mock_mode = mock_ik,
    )
    conn.close()
    return raw, annotated, report


def compare(query, ik_api_key=None, mock_ik=False):
    raw, annotated, report = ask_enhanced(query, ik_api_key, mock_ik)
    return {
        "query": query, "generic": raw,
        "enhanced": annotated, "report": report,
        "report_text": render_report(report),
    }
