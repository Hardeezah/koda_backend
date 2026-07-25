create extension if not exists vector;

create table if not exists document_chunks (
    id uuid primary key default gen_random_uuid(),
    source text not null,
    agency text not null,
    doc_date text,
    url text,
    chunk_index integer not null,
    content text not null,
    embedding vector(1536),
    created_at timestamptz default now()
);

create index if not exists document_chunks_embedding_idx
    on document_chunks
    using ivfflat (embedding vector_cosine_ops)
    with (lists = 100);

create index if not exists document_chunks_agency_idx
    on document_chunks (agency);

create or replace function match_document_chunks(
    query_embedding vector(1536),
    match_count int default 8,
    filter_agency text default null
)
returns table (
    id uuid,
    source text,
    agency text,
    doc_date text,
    url text,
    chunk_index integer,
    content text,
    similarity float
)
language plpgsql
as $$
begin
    return query
    select
        dc.id,
        dc.source,
        dc.agency,
        dc.doc_date,
        dc.url,
        dc.chunk_index,
        dc.content,
        1 - (dc.embedding <=> query_embedding) as similarity
    from document_chunks dc
    where (filter_agency is null or dc.agency = filter_agency)
    order by dc.embedding <=> query_embedding
    limit match_count;
end;
$$;
