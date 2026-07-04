package com.mykb.server.qa.dto;

import java.util.List;

public record QaAnswerResponse(
    String answer, List<QaSourceResponse> sources, int hitCount, long latencyMs, boolean refused) {}
