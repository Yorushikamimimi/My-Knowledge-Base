package com.mykb.server.rag.client;

public record RagQueryRequest(String knowledgeBaseId, String query, int topK) {}
