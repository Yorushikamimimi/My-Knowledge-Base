package com.mykb.server.knowledgebase.dto;

import java.time.Instant;
import java.util.UUID;

public record KnowledgeBaseResponse(
    UUID id,
    String name,
    String description,
    String visibility,
    UUID ownerId,
    String ownerUsername,
    String accessType,
    Instant createdAt) {}
