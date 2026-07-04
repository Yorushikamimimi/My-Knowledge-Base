package com.mykb.server;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.mykb.server.rag.client.RagClient;
import com.mykb.server.rag.client.RagIngestRequest;
import com.mykb.server.rag.client.RagIngestResponse;
import com.mykb.server.rag.client.RagQueryRequest;
import com.mykb.server.rag.client.RagQueryResponse;
import com.mykb.server.rag.client.RagSourceResponse;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Import;
import org.springframework.context.annotation.Primary;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Import(KnowledgeQaIntegrationTest.KnowledgeQaTestConfig.class)
class KnowledgeQaIntegrationTest {

  @Autowired private MockMvc mockMvc;

  @Autowired private ObjectMapper objectMapper;

  @Test
  void qaEndpointShouldReturnAnswerSourcesAndMetrics() throws Exception {
    AuthContext owner = register("qa-owner", "qa-owner@example.com");
    String knowledgeBaseId = createKnowledgeBase(owner.token(), "qa-kb");

    mockMvc
        .perform(
            post("/api/v1/knowledge-bases/{knowledgeBaseId}/qa", knowledgeBaseId)
                .header("Authorization", "Bearer " + owner.token())
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(Map.of("query", "项目怎么检索？"))))
        .andExpect(status().isOk())
        .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_JSON))
        .andExpect(jsonPath("$.data.answer").value("项目使用 pgvector 做向量检索。"))
        .andExpect(jsonPath("$.data.hitCount").value(1))
        .andExpect(jsonPath("$.data.latencyMs").value(15))
        .andExpect(jsonPath("$.data.refused").value(false))
        .andExpect(jsonPath("$.data.sources[0].documentName").value("notes.md"))
        .andExpect(jsonPath("$.data.sources[0].preview").value("pgvector 向量检索"));
  }

  @Test
  void unauthorizedViewerShouldBeDenied() throws Exception {
    AuthContext owner = register("qa-deny-owner", "qa-deny-owner@example.com");
    AuthContext viewer = register("qa-deny-viewer", "qa-deny-viewer@example.com");
    String knowledgeBaseId = createKnowledgeBase(owner.token(), "qa-deny-kb");

    mockMvc
        .perform(
            post("/api/v1/knowledge-bases/{knowledgeBaseId}/qa", knowledgeBaseId)
                .header("Authorization", "Bearer " + viewer.token())
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(Map.of("query", "any question"))))
        .andExpect(status().isForbidden())
        .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_JSON))
        .andExpect(content().json("{\"code\":\"KNOWLEDGE_BASE_ACCESS_DENIED\"}", false));
  }

  @Test
  void sharedViewerCanAskQuestion() throws Exception {
    AuthContext owner = register("qa-share-owner", "qa-share-owner@example.com");
    AuthContext viewer = register("qa-share-viewer", "qa-share-viewer@example.com");
    String knowledgeBaseId = createKnowledgeBase(owner.token(), "qa-share-kb");
    shareKnowledgeBase(owner.token(), knowledgeBaseId, viewer.email());

    mockMvc
        .perform(
            post("/api/v1/knowledge-bases/{knowledgeBaseId}/qa", knowledgeBaseId)
                .header("Authorization", "Bearer " + viewer.token())
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(Map.of("query", "项目怎么检索？"))))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.data.answer").value("项目使用 pgvector 做向量检索。"));
  }

  private AuthContext register(String username, String email) throws Exception {
    MvcResult result =
        mockMvc
            .perform(
                post("/api/v1/auth/register")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(
                        objectMapper.writeValueAsString(
                            Map.of(
                                "username", username,
                                "email", email,
                                "password", "Password123!"))))
            .andExpect(status().isCreated())
            .andReturn();

    JsonNode data = readData(result);
    return new AuthContext(data.get("accessToken").asText(), email);
  }

  private String createKnowledgeBase(String token, String name) throws Exception {
    MvcResult result =
        mockMvc
            .perform(
                post("/api/v1/knowledge-bases")
                    .header("Authorization", "Bearer " + token)
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(
                        objectMapper.writeValueAsString(
                            Map.of("name", name, "description", "owner knowledge base"))))
            .andExpect(status().isCreated())
            .andReturn();

    return readData(result).get("id").asText();
  }

  private void shareKnowledgeBase(String token, String knowledgeBaseId, String targetEmail)
      throws Exception {
    mockMvc
        .perform(
            post("/api/v1/knowledge-bases/{knowledgeBaseId}/shares", knowledgeBaseId)
                .header("Authorization", "Bearer " + token)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(Map.of("targetEmail", targetEmail))))
        .andExpect(status().isOk());
  }

  private JsonNode readData(MvcResult result) throws Exception {
    return objectMapper.readTree(result.getResponse().getContentAsString()).get("data");
  }

  private record AuthContext(String token, String email) {}

  @TestConfiguration
  static class KnowledgeQaTestConfig {

    @Bean
    @Primary
    RagClient ragClient() {
      return new RagClient() {
        @Override
        public RagIngestResponse ingest(RagIngestRequest request) {
          throw new UnsupportedOperationException("QA tests do not ingest");
        }

        @Override
        public RagQueryResponse query(RagQueryRequest request) {
          return new RagQueryResponse(
              "项目使用 pgvector 做向量检索。",
              List.of(
                  new RagSourceResponse(
                      "doc-1", "notes.md", 0, 0.82, "pgvector 向量检索")),
              1,
              15,
              false);
        }
      };
    }
  }
}
