-- ============================================================
-- BRAHMO Citation Safety Engine — Database Schema
-- Tables: citation_patterns | section_mappings | verification_cache
-- ============================================================

-- DROP if re-running
DROP TABLE IF EXISTS citation_patterns;
DROP TABLE IF EXISTS section_mappings;
DROP TABLE IF EXISTS verification_cache;

-- -------------------------------------------------------
-- TABLE 1: citation_patterns
-- 6 regex patterns for Indian legal citation formats
-- Source: SETUP_GUIDE.md § "SEED DATA — 6 CITATION REGEX PATTERNS"
-- -------------------------------------------------------
CREATE TABLE citation_patterns (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_name    TEXT    NOT NULL UNIQUE,
    regex           TEXT    NOT NULL,
    format_template TEXT    NOT NULL,
    example         TEXT    NOT NULL,
    jurisdiction    TEXT    NOT NULL
);

-- -------------------------------------------------------
-- TABLE 2: section_mappings
-- 30 old-act → new-act section conversions
-- Source: SETUP_GUIDE.md § "SEED DATA — 30 SECTION MAPPINGS"
-- -------------------------------------------------------
CREATE TABLE section_mappings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    old_section TEXT    NOT NULL UNIQUE,
    new_section TEXT    NOT NULL,
    old_act     TEXT    NOT NULL,
    new_act     TEXT    NOT NULL
);

-- -------------------------------------------------------
-- TABLE 3: verification_cache
-- Cache IK API results to avoid redundant calls
-- Source: SETUP_GUIDE.md § AI STARTER PROMPT → verification_cache
-- -------------------------------------------------------
CREATE TABLE verification_cache (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    citation_text   TEXT    NOT NULL UNIQUE,
    verified_at     TEXT    NOT NULL,   -- ISO-8601 timestamp
    status          TEXT    NOT NULL CHECK(status IN ('VERIFIED','NOT_FOUND','UNVERIFIED')),
    ik_doc_id       INTEGER,            -- NULL when not found
    case_name       TEXT,               -- NULL when not found
    ik_cost_inr     REAL    DEFAULT 0.0 -- cost of the IK API call in ₹
);
