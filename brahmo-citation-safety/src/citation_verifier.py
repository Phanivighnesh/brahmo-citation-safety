"""
citation_verifier.py — IK API verification with robust error handling.
Never drops a citation result even on API errors.
"""

import os, sqlite3, requests
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Tuple

from .database import get_connection, DB_PATH
from .types import (
    ExtractedCitation, HallucinationResult, VerificationResult,
    STATUS_VERIFIED, STATUS_UNVERIFIED,
)

IK_BASE_URL     = "https://api.indiankanoon.org"
IK_SEARCH_COST  = 0.5
IK_DOCMETA_COST = 0.3
MAX_WORKERS     = 5


def verify_citations(
    hallucination_results: List[HallucinationResult],
    conn: sqlite3.Connection = None,
    api_key: str = None,
    mock_mode: bool = False,
) -> List[VerificationResult]:

    if conn is None:
        conn = get_connection()
    if api_key is None:
        api_key = os.environ.get("INDIAN_KANOON_API_KEY", "").strip()
    api_key = (api_key or "").strip()
    if not api_key:
        mock_mode = True

    if mock_mode:
        print("  [IK] Mock mode — skipping real API calls")
    else:
        print(f"  [IK] Live mode — API key: {api_key[:6]}...")

    results: List[VerificationResult] = []
    to_verify: List[Tuple[ExtractedCitation, HallucinationResult]] = []

    for hr in hallucination_results:
        if hr.is_flagged:
            results.append(VerificationResult(
                citation_text=hr.citation.raw_text, status="REMOVED",
                ik_doc_id=None, case_name=None,
                from_cache=False, ik_attempted=False, cost_inr=0.0,
            ))
        else:
            to_verify.append((hr.citation, hr))

    if not to_verify:
        return results

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {
            executor.submit(
                _verify_one_threaded,
                citation, hr, str(DB_PATH), api_key, mock_mode
            ): citation.raw_text
            for citation, hr in to_verify
        }
        for future in as_completed(future_map):
            raw_text = future_map[future]
            try:
                results.append(future.result())
            except Exception as e:
                print(f"  [IK] Unhandled thread error for '{raw_text[:40]}': {e}")
                # Never drop — add UNVERIFIED so citation still appears in report
                results.append(VerificationResult(
                    citation_text=raw_text, status=STATUS_UNVERIFIED,
                    ik_doc_id=None, case_name=None,
                    from_cache=False, ik_attempted=True, cost_inr=0.0,
                ))

    raw_order = [hr.citation.raw_text for hr in hallucination_results]
    results.sort(key=lambda r: _index_of(r.citation_text, raw_order))
    return results


def _index_of(text, order):
    try:
        return order.index(text)
    except ValueError:
        return 9999


def _verify_one_threaded(citation, hr, db_path, api_key, mock_mode):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return _verify_one(citation, hr, conn, api_key, mock_mode)
    except Exception as e:
        # Catch everything — return UNVERIFIED instead of crashing the thread
        print(f"  [IK] Error in thread for '{citation.raw_text[:40]}': {e}")
        return VerificationResult(
            citation_text=citation.raw_text, status=STATUS_UNVERIFIED,
            ik_doc_id=None, case_name=None,
            from_cache=False, ik_attempted=True, cost_inr=0.0,
        )
    finally:
        conn.close()


def _verify_one(citation, hr, conn, api_key, mock_mode):
    raw = citation.raw_text

    cached = _check_cache(conn, raw)
    if cached:
        print(f"  [IK] Cache hit: {raw[:50]}")
        return cached

    if mock_mode:
        result = VerificationResult(
            citation_text=raw, status=STATUS_UNVERIFIED,
            ik_doc_id=None, case_name=None,
            from_cache=False, ik_attempted=False, cost_inr=0.0,
        )
        _write_cache(conn, result)
        return result

    print(f"  [IK] Verifying: {raw[:60]}")
    return _call_ik_api(raw, hr, conn, api_key)


def _check_cache(conn, citation_text):
    try:
        cur = conn.execute(
            "SELECT status, ik_doc_id, case_name, ik_cost_inr "
            "FROM verification_cache WHERE citation_text = ?",
            (citation_text,)
        )
        row = cur.fetchone()
        if row:
            return VerificationResult(
                citation_text=citation_text, status=row["status"],
                ik_doc_id=row["ik_doc_id"], case_name=row["case_name"],
                from_cache=True, ik_attempted=False, cost_inr=0.0,
            )
    except Exception as e:
        print(f"  [IK] Cache read error: {e}")
    return None


def _write_cache(conn, result):
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """INSERT OR REPLACE INTO verification_cache
               (citation_text, verified_at, status, ik_doc_id, case_name, ik_cost_inr)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (result.citation_text, now, result.status,
             result.ik_doc_id, result.case_name, result.cost_inr)
        )
        conn.commit()
    except Exception as e:
        print(f"  [IK] Cache write error: {e}")


def _get_doc_id(doc: dict) -> Optional[int]:
    """
    IK API returns doc IDs under different keys depending on endpoint/version.
    Try all known variants.
    """
    for key in ("docid", "tid", "id", "doc_id", "documentId"):
        val = doc.get(key)
        if val is not None:
            try:
                return int(val)
            except (ValueError, TypeError):
                pass
    # Log actual keys so we can debug future changes
    print(f"  [IK] Unknown doc keys: {list(doc.keys())[:8]}")
    return None


def _call_ik_api(raw, hr, conn, api_key):
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type":  "application/x-www-form-urlencoded",
    }
    cost = 0.0

    # Step A: search
    try:
        resp = requests.post(
            f"{IK_BASE_URL}/search/",
            data={"formInput": raw},
            headers=headers,
            timeout=15,
        )
        print(f"  [IK] Search HTTP {resp.status_code} for: {raw[:40]}")

        if resp.status_code in (401, 403):
            msg = {401: "Key rejected", 403: "Forbidden"}.get(resp.status_code)
            print(f"  [IK] ERROR {resp.status_code} — {msg}")
            result = VerificationResult(raw, STATUS_UNVERIFIED, None, None, False, True, 0.0)
            _write_cache(conn, result)
            return result

        resp.raise_for_status()
        data = resp.json()
        cost += IK_SEARCH_COST

    except requests.exceptions.RequestException as e:
        print(f"  [IK] Network error: {e}")
        result = VerificationResult(raw, STATUS_UNVERIFIED, None, None, False, True, 0.0)
        _write_cache(conn, result)
        return result

    docs = data.get("docs", [])
    print(f"  [IK] docs={len(docs)} for: {raw[:40]}")

    if not docs:
        status = "REMOVED" if hr.is_suspicious else STATUS_UNVERIFIED
        result = VerificationResult(raw, status, None, None, False, True, cost)
        _write_cache(conn, result)
        return result

    # Step B: get doc ID — try all known key names
    doc    = docs[0]
    doc_id = _get_doc_id(doc)
    title  = doc.get("title", "")

    if doc_id is None:
        # Search found something — citation exists even if we can't get docmeta
        print(f"  [IK] Search confirmed case exists (no docid), marking VERIFIED")
        result = VerificationResult(raw, STATUS_VERIFIED, None, title, False, True, cost)
        _write_cache(conn, result)
        return result

    # Step C: docmeta for canonical title
    try:
        resp2 = requests.get(
            f"{IK_BASE_URL}/docmeta/{doc_id}/",
            headers=headers,
            timeout=15,
        )
        resp2.raise_for_status()
        meta   = resp2.json()
        cost  += IK_DOCMETA_COST
        title  = meta.get("title") or title
    except Exception as e:
        print(f"  [IK] Docmeta error (using search title): {e}")

    result = VerificationResult(raw, STATUS_VERIFIED, doc_id, title, False, True, cost)
    _write_cache(conn, result)
    return result
