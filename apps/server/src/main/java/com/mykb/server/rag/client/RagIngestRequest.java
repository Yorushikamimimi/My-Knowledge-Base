package com.mykb.server.rag.client;

public record RagIngestRequest(
    String knowledgeBaseId,
    String documentId,
    String documentName,
    String contentType,
    String contentBase64) {}
