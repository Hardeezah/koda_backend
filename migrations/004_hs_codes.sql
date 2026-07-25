create table if not exists hs_codes (
    id uuid primary key default gen_random_uuid(),
    chapter text not null,
    heading text not null,
    code text not null unique,
    description text not null,
    notes text,
    embedding vector(1536),
    created_at timestamptz default now()
);

create index if not exists hs_codes_embedding_idx
    on hs_codes
    using ivfflat (embedding vector_cosine_ops)
    with (lists = 50);

create index if not exists hs_codes_code_idx
    on hs_codes (code);

create or replace function match_hs_codes(
    query_embedding vector(1536),
    match_count int default 5
)
returns table (
    id uuid,
    chapter text,
    heading text,
    code text,
    description text,
    notes text,
    similarity float
)
language plpgsql
as $$
begin
    return query
    select
        h.id,
        h.chapter,
        h.heading,
        h.code,
        h.description,
        h.notes,
        1 - (h.embedding <=> query_embedding) as similarity
    from hs_codes h
    order by h.embedding <=> query_embedding
    limit match_count;
end;
$$;
