-- Migration: Create all RAG + AfCFTA tables with local embeddings (384d)
-- Run in Supabase SQL Editor

CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- 1. document_chunks (RAG regulatory knowledge)
-- ============================================
CREATE TABLE IF NOT EXISTS document_chunks (
  id bigserial PRIMARY KEY,
  source text NOT NULL,
  agency text NOT NULL,
  doc_date text,
  url text,
  chunk_index int NOT NULL DEFAULT 0,
  content text NOT NULL,
  embedding vector(384) NOT NULL
);

CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx 
  ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10);
CREATE INDEX IF NOT EXISTS document_chunks_source_idx ON document_chunks (source);
CREATE INDEX IF NOT EXISTS document_chunks_agency_idx ON document_chunks (agency);

CREATE OR REPLACE FUNCTION match_document_chunks(
  query_embedding vector(384),
  match_count int DEFAULT 8,
  filter_agency text DEFAULT NULL
)
RETURNS TABLE (
  id bigint, source text, agency text, doc_date text, url text,
  chunk_index int, content text, similarity float
)
LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  SELECT dc.id, dc.source, dc.agency, dc.doc_date, dc.url, dc.chunk_index, dc.content,
    1 - (dc.embedding <=> query_embedding) AS similarity
  FROM document_chunks dc
  WHERE (filter_agency IS NULL OR dc.agency = filter_agency)
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- ============================================
-- 2. hs_codes (HS code vector search)
-- ============================================
CREATE TABLE IF NOT EXISTS hs_codes (
  id bigserial PRIMARY KEY,
  chapter text,
  heading text,
  code text UNIQUE NOT NULL,
  description text NOT NULL,
  notes text,
  embedding vector(384) NOT NULL
);

CREATE INDEX IF NOT EXISTS hs_codes_embedding_idx 
  ON hs_codes USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10);
CREATE INDEX IF NOT EXISTS hs_codes_code_idx ON hs_codes (code);

CREATE OR REPLACE FUNCTION match_hs_codes(
  query_embedding vector(384),
  match_count int DEFAULT 5
)
RETURNS TABLE (
  id bigint, chapter text, heading text, code text, description text, notes text, similarity float
)
LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  SELECT hc.id, hc.chapter, hc.heading, hc.code, hc.description, hc.notes,
    1 - (hc.embedding <=> query_embedding) AS similarity
  FROM hs_codes hc
  ORDER BY hc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- ============================================
-- 3. afcfta_tariff_schedule (tariff rates by HS code + country)
-- ============================================
CREATE TABLE IF NOT EXISTS afcfta_tariff_schedule (
  id bigserial PRIMARY KEY,
  hs_code text NOT NULL,
  destination_country text NOT NULL,
  base_rate numeric NOT NULL DEFAULT 0,
  category_a_rate numeric,      -- Category A: 0% target
  category_b_rate numeric,      -- Category B: reduced
  category_c_rate numeric,      -- Category C: excluded
  phase_out_year int,           -- Year tariff reaches 0
  notes text,
  UNIQUE (hs_code, destination_country)
);

CREATE INDEX IF NOT EXISTS afcfta_tariff_hs_idx ON afcfta_tariff_schedule (hs_code);
CREATE INDEX IF NOT EXISTS afcfta_tariff_country_idx ON afcfta_tariff_schedule (destination_country);

-- ============================================
-- 4. afcfta_roo_requirements (Rules of Origin by HS prefix)
-- ============================================
CREATE TABLE IF NOT EXISTS afcfta_roo_requirements (
  id bigserial PRIMARY KEY,
  hs_code_prefix text NOT NULL,    -- e.g., '0306' for crustaceans
  roo_type text NOT NULL,          -- 'wholly_obtained', 'cth', 'ctsh', 'va_40', 'specific_process'
  roo_description text NOT NULL,
  value_added_threshold numeric,   -- e.g., 40 for 40% VA rule
  specific_process text,           -- For chemical/specific process rules
  notes text
);

CREATE INDEX IF NOT EXISTS afcfta_roo_prefix_idx ON afcfta_roo_requirements (hs_code_prefix);

-- ============================================
-- 5. afcfta_checks (audit log of eligibility checks)
-- ============================================
CREATE TABLE IF NOT EXISTS afcfta_checks (
  id bigserial PRIMARY KEY,
  user_id uuid NOT NULL,
  product_name text NOT NULL,
  hs_code text,
  destination_country text NOT NULL,
  eligible boolean NOT NULL,
  tariff_saving_percent numeric,
  roo_eligible boolean,
  explanation text,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS afcfta_checks_user_idx ON afcfta_checks (user_id);
CREATE INDEX IF NOT EXISTS afcfta_checks_created_idx ON afcfta_checks (created_at DESC);

-- ============================================
-- 6. RLS Policies (service role + authenticated read)
-- ============================================
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE hs_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE afcfta_tariff_schedule ENABLE ROW LEVEL SECURITY;
ALTER TABLE afcfta_roo_requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE afcfta_checks ENABLE ROW LEVEL SECURITY;

-- Service role full access
DO $$
DECLARE
  t text;
BEGIN
  FOR t IN SELECT unnest(ARRAY['document_chunks','hs_codes','afcfta_tariff_schedule','afcfta_roo_requirements','afcfta_checks'])
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS "Service role full access on %s" ON %s', t, t);
    EXECUTE format('CREATE POLICY "Service role full access on %s" ON %s FOR ALL USING (auth.role() = ''service_role'')', t, t);
    EXECUTE format('DROP POLICY IF EXISTS "Authenticated read on %s" ON %s', t, t);
    EXECUTE format('CREATE POLICY "Authenticated read on %s" ON %s FOR SELECT USING (auth.role() = ''authenticated'')', t, t);
  END LOOP;
END;
$$;

-- afcfta_checks: users can only see their own
DROP POLICY IF EXISTS "Users see own afcfta_checks" ON afcfta_checks;
CREATE POLICY "Users see own afcfta_checks" ON afcfta_checks
  FOR SELECT USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "Users insert own afcfta_checks" ON afcfta_checks;
CREATE POLICY "Users insert own afcfta_checks" ON afcfta_checks
  FOR INSERT WITH CHECK (auth.uid() = user_id);