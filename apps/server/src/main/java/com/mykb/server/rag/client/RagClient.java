package com.mykb.server.rag.client;

public interface RagClient {

  RagIngestResponse ingest(RagIngestRequest request);

  RagQueryResponse query(RagQueryRequest request);
}
