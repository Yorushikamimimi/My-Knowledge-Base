package com.mykb.server.qa.controller;

import com.mykb.server.common.api.ApiResponse;
import com.mykb.server.common.security.AuthenticatedUser;
import com.mykb.server.qa.dto.QaAnswerResponse;
import com.mykb.server.qa.dto.QaStreamRequest;
import com.mykb.server.qa.service.KnowledgeQaService;
import jakarta.validation.Valid;
import java.util.UUID;
import org.springframework.http.MediaType;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@RestController
@RequestMapping("/api/v1/knowledge-bases/{knowledgeBaseId}")
public class KnowledgeQaController {

  private final KnowledgeQaService knowledgeQaService;

  public KnowledgeQaController(KnowledgeQaService knowledgeQaService) {
    this.knowledgeQaService = knowledgeQaService;
  }

  @PostMapping(
      path = "/qa/stream",
      consumes = MediaType.APPLICATION_JSON_VALUE,
      produces = {MediaType.TEXT_EVENT_STREAM_VALUE, MediaType.APPLICATION_JSON_VALUE})
  public SseEmitter streamAnswer(
      @AuthenticationPrincipal AuthenticatedUser user,
      @PathVariable UUID knowledgeBaseId,
      @Valid @RequestBody QaStreamRequest request) {
    return knowledgeQaService.streamAnswer(user, knowledgeBaseId, request);
  }

  @PostMapping(path = "/qa", consumes = MediaType.APPLICATION_JSON_VALUE)
  public ApiResponse<QaAnswerResponse> answer(
      @AuthenticationPrincipal AuthenticatedUser user,
      @PathVariable UUID knowledgeBaseId,
      @Valid @RequestBody QaStreamRequest request) {
    return ApiResponse.success(knowledgeQaService.answer(user, knowledgeBaseId, request));
  }
}

