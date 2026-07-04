package com.mykb.server.rag.client;

public record RagSourceResponse(
    String documentId, String documentName, int chunkIndex, double score, String preview) {}
