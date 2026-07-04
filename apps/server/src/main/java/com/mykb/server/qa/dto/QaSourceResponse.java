package com.mykb.server.qa.dto;

public record QaSourceResponse(
    String documentId, String documentName, int chunkIndex, double score, String preview) {}
