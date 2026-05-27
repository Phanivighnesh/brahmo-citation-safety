"""
api.py
------
FastAPI backend for BRAHMO Citation Safety Engine.
Serves all endpoints consumed by the React frontend.

Endpoints:
  GET  /api/matters          → 8 pre-loaded legal matters
  POST /api/query/generic    → Gemini response only (no verification)
  POST /api/query/enhanced   → Gemini + full citation safety pipeline
  POST /api/query/compare    → both in one call (used by UI)
  GET  /api/health           → health check

Run with:
  uvicorn api:app --reload --port 8000
"""

import os
import sys
import pathlib

# Make src importable
sys.path.insert(0, str(pathlib.Path(__file__).parent))

# Load .env
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

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from src.llm_gemini import ask_generic, ask_enhanced
from src.pipeline import run_pipeline
from src.citation_annotator import render_report
from src.database import get_connection, clear_unverified_cache

app = FastAPI(title="BRAHMO Citation Safety Engine", version="1.0.0")

# Allow React dev server (port 5173) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Pre-loaded legal matters (source: SETUP_GUIDE.md) ─────────────────────────
MATTERS = [
    {
        "id": 1,
        "title": "Rajesh Kumar — Anticipatory Bail",
        "practice": "Criminal",
        "court": "Delhi High Court",
        "query": "List 6 Supreme Court cases on anticipatory bail in economic offences. For each case give the full SCC citation in format (YYYY) Vol SCC Page.",
    },
    {
        "id": 2,
        "title": "Criminal Complaint — Cheating",
        "practice": "Criminal",
        "court": "Delhi Metropolitan Magistrate",
        "query": "Draft a short criminal complaint for cheating under Section 420 IPC and criminal breach of trust under Section 406 IPC. Cite 3 relevant cases with full SCC citations.",
    },
    {
        "id": 3,
        "title": "NDPS Act Bail Research",
        "practice": "Criminal",
        "court": "Supreme Court Research",
        "query": "List 5 Supreme Court cases on bail under NDPS Act from 2019-2024. Give full SCC citations in format (YYYY) Vol SCC Page for each.",
    },
    {
        "id": 4,
        "title": "Delhi HC — Section 482 BNSS",
        "practice": "Criminal",
        "court": "Delhi High Court",
        "query": "List 4 Delhi High Court decisions on inherent powers under Section 482 CrPC or Section 528 BNSS. Give full SCC OnLine citations.",
    },
    {
        "id": 5,
        "title": "Corporate NDA Review",
        "practice": "Corporate",
        "court": "N/A (Transactional)",
        "query": "List 3 key Indian cases on breach of non-disclosure agreements and trade secrets. Give full SCC citations.",
    },
    {
        "id": 6,
        "title": "Shareholders Dispute — NCLT",
        "practice": "Corporate",
        "court": "NCLT Delhi",
        "query": "List 4 Supreme Court cases on oppression and mismanagement under Companies Act. Give full SCC citations.",
    },
    {
        "id": 7,
        "title": "Property Dispute — Specific Performance",
        "practice": "Property",
        "court": "Civil Court Delhi",
        "query": "List 4 Supreme Court cases on specific performance of immovable property sale agreements. Give full SCC citations.",
    },
    {
        "id": 8,
        "title": "Family Law — Contested Divorce",
        "practice": "Family",
        "court": "Family Court Delhi",
        "query": "List 4 Supreme Court cases on grounds for contested divorce under Hindu Marriage Act Section 13. Give full SCC citations.",
    },
]


# ── Request / Response models ──────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    matter_id: Optional[int] = None


class CitationOut(BaseModel):
    original_text: str
    status: str
    case_name: Optional[str]
    halt_reason: Optional[str]
    from_cache: bool
    cost_inr: float


class SectionAlertOut(BaseModel):
    old_section: str
    new_section: str
    old_act: str
    new_act: str
    occurrences: int


class ReportOut(BaseModel):
    total: int
    verified: int
    corrected: int
    unverified: int
    removed: int
    prefilter_caught: int
    ik_calls: int
    total_cost_inr: float
    accuracy_pct: float
    citations: list[CitationOut]
    section_alerts: list[SectionAlertOut]


class CompareResponse(BaseModel):
    query: str
    generic: str
    enhanced: str
    report: ReportOut


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "gemini_key": bool(os.environ.get("GEMINI_API_KEY")),
        "ik_key": bool(os.environ.get("INDIAN_KANOON_API_KEY")),
        "model": os.environ.get("GEMINI_MODEL", "auto-discover"),
    }


@app.get("/api/matters")
def get_matters():
    return MATTERS


@app.post("/api/query/compare", response_model=CompareResponse)
def compare(req: QueryRequest):
    ik_key  = os.environ.get("INDIAN_KANOON_API_KEY", "").strip()
    mock_ik = not bool(ik_key)

    try:
        # Generic — raw Gemini response
        generic_text = ask_generic(req.query)

        # Enhanced — Gemini + pipeline
        conn = get_connection()
        annotated_text, report = run_pipeline(
            text      = generic_text,
            conn      = conn,
            api_key   = ik_key,
            mock_mode = mock_ik,
        )
        conn.close()

        # Serialise report
        citations_out = [
            CitationOut(
                original_text = ac.original_text,
                status        = ac.status,
                case_name     = ac.case_name,
                halt_reason   = ac.halt_reason,
                from_cache    = ac.from_cache,
                cost_inr      = ac.cost_inr,
            )
            for ac in report.annotated
        ]
        alerts_out = [
            SectionAlertOut(
                old_section = a.old_section,
                new_section = a.new_section,
                old_act     = a.old_act,
                new_act     = a.new_act,
                occurrences = a.occurrences,
            )
            for a in report.section_alerts
        ]
        report_out = ReportOut(
            total            = report.total,
            verified         = report.verified,
            corrected        = report.corrected,
            unverified       = report.unverified,
            removed          = report.removed,
            prefilter_caught = report.prefilter_caught,
            ik_calls         = report.ik_calls,
            total_cost_inr   = report.total_cost_inr,
            accuracy_pct     = report.accuracy_pct,
            citations        = citations_out,
            section_alerts   = alerts_out,
        )

        return CompareResponse(
            query    = req.query,
            generic  = generic_text,
            enhanced = annotated_text,
            report   = report_out,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
