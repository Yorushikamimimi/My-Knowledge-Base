package com.mykb.server.rag.client;

public record RagIngestResponse(String documentId, int chunkCount, String provider) {}
