package com.mykb.server.qa.service;

import com.mykb.server.common.exception.AppException;
import com.mykb.server.common.security.AuthenticatedUser;
import com.mykb.server.knowledgebase.repository.KnowledgeBaseRepository;
import com.mykb.server.knowledgebase.repository.KnowledgeBaseShareRepository;
import com.mykb.server.qa.dto.QaAnswerResponse;
import com.mykb.server.qa.dto.QaSourceResponse;
import com.mykb.server.qa.dto.QaStreamRequest;
import com.mykb.server.rag.client.RagClient;
import com.mykb.server.rag.client.RagOperationException;
import com.mykb.server.rag.client.RagQueryRequest;
import com.mykb.server.rag.client.RagQueryResponse;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@Service
public class KnowledgeQaService {

  private static final Logger log = LoggerFactory.getLogger(KnowledgeQaService.class);

  private final KnowledgeBaseRepository knowledgeBaseRepository;
  private final KnowledgeBaseShareRepository knowledgeBaseShareRepository;
  private final RagClient ragClient;

  public KnowledgeQaService(
      KnowledgeBaseRepository knowledgeBaseRepository,
      KnowledgeBaseShareRepository knowledgeBaseShareRepository,
      RagClient ragClient) {
    this.knowledgeBaseRepository = knowledgeBaseRepository;
    this.knowledgeBaseShareRepository = knowledgeBaseShareRepository;
    this.ragClient = ragClient;
  }

  @Transactional(readOnly = true)
  public SseEmitter streamAnswer(
      AuthenticatedUser currentUser, UUID knowledgeBaseId, QaStreamRequest request) {
    verifyAccess(currentUser.userId(), knowledgeBaseId);
    throw new AppException(
        HttpStatus.SERVICE_UNAVAILABLE,
        "QA_NOT_IMPLEMENTED",
        "Q&A feature is being rebuilt with local models. Coming soon.");
  }

  @Transactional(readOnly = true)
  public QaAnswerResponse answer(
      AuthenticatedUser currentUser, UUID knowledgeBaseId, QaStreamRequest request) {
    verifyAccess(currentUser.userId(), knowledgeBaseId);
    try {
      RagQueryResponse response =
          ragClient.query(new RagQueryRequest(knowledgeBaseId.toString(), request.query(), 5));
      return new QaAnswerResponse(
          response.answer(),
          response.sources().stream()
              .map(
                  source ->
                      new QaSourceResponse(
                          source.documentId(),
                          source.documentName(),
                          source.chunkIndex(),
                          source.score(),
                          source.preview()))
              .toList(),
          response.hitCount(),
          response.latencyMs(),
          response.refused());
    } catch (RagOperationException exception) {
      log.error("RAG query failed. kbId={}", knowledgeBaseId, exception);
      throw new AppException(
          HttpStatus.SERVICE_UNAVAILABLE,
          "RAG_QUERY_FAILED",
          "Knowledge base query failed");
    }
  }

  private void verifyAccess(UUID currentUserId, UUID knowledgeBaseId) {
    knowledgeBaseRepository
        .findById(knowledgeBaseId)
        .orElseThrow(
            () ->
                new AppException(
                    HttpStatus.NOT_FOUND,
                    "KNOWLEDGE_BASE_NOT_FOUND",
                    "Knowledge base does not exist"));
    boolean owner =
        knowledgeBaseRepository.findById(knowledgeBaseId)
            .map(kb -> kb.getOwner().getId().equals(currentUserId))
            .orElse(false);
    boolean shared =
        knowledgeBaseShareRepository.existsByKnowledgeBase_IdAndSharedWith_Id(
            knowledgeBaseId, currentUserId);
    if (!owner && !shared) {
      throw new AppException(
          HttpStatus.FORBIDDEN,
          "KNOWLEDGE_BASE_ACCESS_DENIED",
          "You do not have access to this knowledge base");
    }
  }
}
