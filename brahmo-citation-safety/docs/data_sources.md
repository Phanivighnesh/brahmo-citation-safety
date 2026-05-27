# Data Sources

All data is sourced exclusively from the assessment documents.

## Citation Patterns
Source: SETUP_GUIDE.md § "SEED DATA — 6 CITATION REGEX PATTERNS"
6 patterns: SCC, SCC_OnLine, AIR, Cri_LJ, SCR, MANU

## Section Mappings  
Source: SETUP_GUIDE.md § "SEED DATA — 30 SECTION MAPPINGS"
21 IPC→BNS, 8 CrPC→BNSS, 1 IEA→BSA

## Hallucination Rules
Source: SETUP_GUIDE.md § "HALLUCINATION DETECTION RULES"
4 rules: future year, impossible volume, impossible page, pre-modern date

## Indian Kanoon API
Source: SETUP_GUIDE.md § "Indian Kanoon — SAMPLE API RESPONSES"
Endpoints: POST /search/ (₹0.5), GET /docmeta/{id}/ (₹0.3)

## Verification Strategy
Source: SETUP_GUIDE.md § "VERIFICATION STRATEGY"
Extract → pre-filter → IK search → IK docmeta → cache result
