package com.mykb.server.rag.client;

import java.util.List;

public record RagQueryResponse(
    String answer, List<RagSourceResponse> sources, int hitCount, long latencyMs, boolean refused) {}
