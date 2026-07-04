package com.mykb.server.document.dto;

import java.time.Instant;
import java.util.UUID;

public record KnowledgeDocumentResponse(
    UUID id,
    UUID knowledgeBaseId,
    UUID uploaderId,
    String originalFilename,
    String contentType,
    long sizeBytes,
    String storageProvider,
    String processingStatus,
    Instant createdAt) {}
