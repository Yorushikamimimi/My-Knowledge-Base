package com.mykb.server.document.dto;

import java.time.Instant;
import java.util.UUID;

public record IngestionTaskResponse(
    UUID id,
    UUID documentId,
    String taskType,
    String status,
    String currentStage,
    String failedStage,
    String ocrEngine,
    String failureCode,
    String failureMessage,
    Instant startedAt,
    Instant finishedAt,
    Instant createdAt) {}