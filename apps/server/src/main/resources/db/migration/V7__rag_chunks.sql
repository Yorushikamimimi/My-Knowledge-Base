create extension if not exists vector;

create table rag_document_chunks (
    id uuid primary key default gen_random_uuid(),
    knowledge_base_id uuid not null,
    document_id uuid not null,
    document_name varchar(255) not null,
    chunk_index integer not null,
    content text not null,
    embedding vector(768) not null,
    created_at timestamp with time zone not null default now(),
    updated_at timestamp with time zone not null default now(),
    constraint uk_rag_document_chunk unique (document_id, chunk_index)
);

create index idx_rag_chunks_kb on rag_document_chunks(knowledge_base_id);
create index idx_rag_chunks_document on rag_document_chunks(document_id);
create index idx_rag_chunks_embedding on rag_document_chunks using ivfflat (embedding vector_cosine_ops) with (lists = 100);
