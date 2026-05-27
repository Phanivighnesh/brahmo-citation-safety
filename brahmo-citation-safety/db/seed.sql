-- ============================================================
-- BRAHMO Citation Safety Engine — Seed Data
-- Source: SETUP_GUIDE.md
-- ============================================================

-- -------------------------------------------------------
-- CITATION PATTERNS (6 rows)
-- Regex columns use Python re-module syntax (raw strings)
-- Source: SETUP_GUIDE.md § "SEED DATA — 6 CITATION REGEX PATTERNS"
-- -------------------------------------------------------
INSERT INTO citation_patterns (pattern_name, regex, format_template, example, jurisdiction) VALUES
  ('SCC',
   '\((\d{4})\)\s+(\d{1,2})\s+SCC\s+(\d{1,5})',
   '({year}) {vol} SCC {page}',
   '(2024) 5 SCC 123',
   'Supreme Court of India'),

  ('SCC_OnLine',
   '(\d{4})\s+SCC\s+OnLine\s+(SC|Del|Bom|Cal|Mad|All|Kar|Ker|Pat|Raj|MP|AP|Guj)\s+(\d{1,6})',
   '{year} SCC OnLine {court} {num}',
   '2024 SCC OnLine Del 456',
   'Supreme Court / High Courts'),

  ('AIR',
   'AIR\s+(\d{4})\s+(SC|Del|Bom|Cal|Mad|All|Kar|Ker|Pat|Raj|MP|AP|Guj|NOC)\s+(\d{1,5})',
   'AIR {year} {court} {page}',
   'AIR 2024 SC 123',
   'All India Reporter'),

  ('Cri_LJ',
   '[\(]?(\d{4})[\)]?\s+Cri\s+LJ\s+(\d{1,5})',
   '{year} Cri LJ {page}',
   '2024 Cri LJ 789',
   'Criminal Law Journal'),

  ('SCR',
   '\((\d{4})\)\s+(\d{1,2})\s+SCR\s+(\d{1,5})',
   '({year}) {vol} SCR {page}',
   '(2024) 5 SCR 123',
   'Supreme Court Reports'),

  ('MANU',
   'MANU/(SC|DE|MH|KA|KE|WB|TN|AP|GJ|RJ|MP|UP)/\d{4}/\d{4,6}',
   'MANU/{court}/{num}/{year}',
   'MANU/SC/0123/2024',
   'Manupatra');


-- -------------------------------------------------------
-- SECTION MAPPINGS (30 rows)
-- Source: SETUP_GUIDE.md § "SEED DATA — 30 SECTION MAPPINGS"
-- -------------------------------------------------------

-- IPC → BNS (21 mappings)
INSERT INTO section_mappings (old_section, new_section, old_act, new_act) VALUES
  ('Section 302 IPC',    'Section 101 BNS',   'Indian Penal Code', 'Bharatiya Nyaya Sanhita'),
  ('Section 304 IPC',    'Section 105 BNS',   'IPC',               'BNS'),
  ('Section 304A IPC',   'Section 106 BNS',   'IPC',               'BNS'),
  ('Section 304B IPC',   'Section 80 BNS',    'IPC',               'BNS'),
  ('Section 306 IPC',    'Section 108 BNS',   'IPC',               'BNS'),
  ('Section 307 IPC',    'Section 109 BNS',   'IPC',               'BNS'),
  ('Section 323 IPC',    'Section 115 BNS',   'IPC',               'BNS'),
  ('Section 326 IPC',    'Section 119 BNS',   'IPC',               'BNS'),
  ('Section 354 IPC',    'Section 74 BNS',    'IPC',               'BNS'),
  ('Section 376 IPC',    'Section 63 BNS',    'IPC',               'BNS'),
  ('Section 379 IPC',    'Section 303 BNS',   'IPC',               'BNS'),
  ('Section 384 IPC',    'Section 308 BNS',   'IPC',               'BNS'),
  ('Section 392 IPC',    'Section 309 BNS',   'IPC',               'BNS'),
  ('Section 406 IPC',    'Section 316 BNS',   'IPC',               'BNS'),
  ('Section 420 IPC',    'Section 318 BNS',   'IPC',               'BNS'),
  ('Section 467 IPC',    'Section 336 BNS',   'IPC',               'BNS'),
  ('Section 498A IPC',   'Section 85 BNS',    'IPC',               'BNS'),
  ('Section 499 IPC',    'Section 356 BNS',   'IPC',               'BNS'),
  ('Section 506 IPC',    'Section 351 BNS',   'IPC',               'BNS'),
  ('Section 34 IPC',     'Section 3(5) BNS',  'IPC',               'BNS'),
  ('Section 120B IPC',   'Section 61 BNS',    'IPC',               'BNS'),

-- CrPC → BNSS (8 mappings)
  ('Section 125 CrPC',   'Section 144 BNSS',  'Code of Criminal Procedure', 'Bharatiya Nagarik Suraksha Sanhita'),
  ('Section 154 CrPC',   'Section 173 BNSS',  'CrPC',              'BNSS'),
  ('Section 156(3) CrPC','Section 175(3) BNSS','CrPC',             'BNSS'),
  ('Section 167 CrPC',   'Section 187 BNSS',  'CrPC',              'BNSS'),
  ('Section 437 CrPC',   'Section 480 BNSS',  'CrPC',              'BNSS'),
  ('Section 438 CrPC',   'Section 482 BNSS',  'CrPC',              'BNSS'),
  ('Section 439 CrPC',   'Section 483 BNSS',  'CrPC',              'BNSS'),
  ('Section 482 CrPC',   'Section 528 BNSS',  'CrPC',              'BNSS'),

-- IEA → BSA (1 mapping)
  ('Section 65B IEA',    'Section 63 BSA',    'Indian Evidence Act','Bharatiya Sakshya Adhiniyam');
