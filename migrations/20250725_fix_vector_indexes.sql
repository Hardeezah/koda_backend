-- Fix IVFFlat indexes for small datasets.
-- IVFFlat with lists=100 requires ~10K rows for optimal performance.
-- With few documents, we drop the old index and recreate with smaller lists,
-- or switch to HNSW which performs better at small scales.

-- Drop old IVFFlat indexes (can't alter lists in-place)
DROP INDEX IF EXISTS document_chunks_embedding_idx;
DROP INDEX IF EXISTS hs_codes_embedding_idx;

-- Recreate with smaller lists for initial small-data phase.
-- When the dataset grows past ~5000 rows, recreate with lists=100.
CREATE INDEX document_chunks_embedding_idx
    ON document_chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 10);

CREATE INDEX hs_codes_embedding_idx
    ON hs_codes
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 10);
