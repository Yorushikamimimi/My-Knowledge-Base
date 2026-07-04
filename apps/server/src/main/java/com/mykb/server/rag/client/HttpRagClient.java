package com.mykb.server.rag.client;

import com.mykb.server.rag.config.RagProperties;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

@Component
public class HttpRagClient implements RagClient {

  private final RagProperties properties;
  private final RestTemplate restTemplate;

  public HttpRagClient(RagProperties properties, RestTemplateBuilder builder) {
    this.properties = properties;
    this.restTemplate =
        builder
            .setConnectTimeout(properties.getTimeout())
            .setReadTimeout(properties.getTimeout())
            .rootUri(trimTrailingSlash(properties.getBaseUrl()))
            .build();
  }

  @Override
  public RagIngestResponse ingest(RagIngestRequest request) {
    if (!properties.isEnabled()) {
      return new RagIngestResponse(request.documentId(), 0, "disabled");
    }
    try {
      ResponseEntity<RagIngestResponse> response =
          restTemplate.exchange(
              "/api/v1/rag/ingest",
              HttpMethod.POST,
              new HttpEntity<>(request),
              RagIngestResponse.class);
      return response.getBody();
    } catch (RestClientException exception) {
      throw new RagOperationException("RAG ingestion failed", exception);
    }
  }

  @Override
  public RagQueryResponse query(RagQueryRequest request) {
    try {
      ResponseEntity<RagQueryResponse> response =
          restTemplate.exchange(
              "/api/v1/rag/query", HttpMethod.POST, new HttpEntity<>(request), RagQueryResponse.class);
      return response.getBody();
    } catch (RestClientException exception) {
      throw new RagOperationException("RAG query failed", exception);
    }
  }

  private String trimTrailingSlash(String value) {
    if (value == null || value.isBlank()) {
      return "";
    }
    return value.endsWith("/") ? value.substring(0, value.length() - 1) : value;
  }
}
