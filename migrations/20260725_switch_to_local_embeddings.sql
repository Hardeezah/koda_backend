-- Migration: Create RAG tables with local embeddings (fastembed bge-small-en-v1.5, 384d)
-- Run this in Supabase SQL Editor before running ingestion.
-- Requires: CREATE EXTENSION IF NOT EXISTS vector;

-- 0. Ensure pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Create document_chunks table
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

-- 2. Create hs_codes table
CREATE TABLE IF NOT EXISTS hs_codes (
  id bigserial PRIMARY KEY,
  chapter text,
  heading text,
  code text UNIQUE NOT NULL,
  description text NOT NULL,
  notes text,
  embedding vector(384) NOT NULL
);

-- 3. IVFFlat indexes for fast cosine search
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx 
  ON document_chunks 
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 10);

CREATE INDEX IF NOT EXISTS hs_codes_embedding_idx 
  ON hs_codes 
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 10);

-- 4. Additional indexes for filtering
CREATE INDEX IF NOT EXISTS document_chunks_source_idx ON document_chunks (source);
CREATE INDEX IF NOT EXISTS document_chunks_agency_idx ON document_chunks (agency);

-- 5. match_document_chunks RPC function
CREATE OR REPLACE FUNCTION match_document_chunks(
  query_embedding vector(384),
  match_count int DEFAULT 8,
  filter_agency text DEFAULT NULL
)
RETURNS TABLE (
  id bigint,
  source text,
  agency text,
  doc_date text,
  url text,
  chunk_index int,
  content text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    dc.id,
    dc.source,
    dc.agency,
    dc.doc_date,
    dc.url,
    dc.chunk_index,
    dc.content,
    1 - (dc.embedding <=> query_embedding) AS similarity
  FROM document_chunks dc
  WHERE (filter_agency IS NULL OR dc.agency = filter_agency)
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- 6. match_hs_codes RPC function
CREATE OR REPLACE FUNCTION match_hs_codes(
  query_embedding vector(384),
  match_count int DEFAULT 5
)
RETURNS TABLE (
  id bigint,
  chapter text,
  heading text,
  code text,
  description text,
  notes text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    hc.id,
    hc.chapter,
    hc.heading,
    hc.code,
    hc.description,
    hc.notes,
    1 - (hc.embedding <=> query_embedding) AS similarity
  FROM hs_codes hc
  ORDER BY hc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- 7. Enable Row Level Security (optional, but recommended)
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE hs_codes ENABLE ROW LEVEL SECURITY;

-- Allow service role full access
CREATE POLICY "Service role full access on document_chunks" 
  ON document_chunks FOR ALL 
  USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access on hs_codes" 
  ON hs_codes FOR ALL 
  USING (auth.role() = 'service_role');

-- Allow authenticated users read access
CREATE POLICY "Authenticated read on document_chunks" 
  ON document_chunks FOR SELECT 
  USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated read on hs_codes" 
  ON hs_codes FOR SELECT 
  USING (auth.role() = 'authenticated');
