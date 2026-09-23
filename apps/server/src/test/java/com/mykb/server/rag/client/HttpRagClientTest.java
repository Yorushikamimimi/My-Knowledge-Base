package com.mykb.server.rag.client;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

class HttpRagClientTest {

  @Test
  void ingestionFailureMessageExplainsUnprocessableDocumentAndPreservedIndex() {
    assertThat(
            HttpRagClient.ingestionFailureMessage(
                422,
                "{\"detail\":{\"code\":\"DOCUMENT_PARSE_FAILED\",\"message\":\"No text\"}}"))
        .contains("could not parse or extract indexable text")
        .contains("existing indexed chunks were left unchanged");
  }

  @Test
  void ingestionFailureMessageDoesNotMislabelOtherRemoteErrors() {
    assertThat(
            HttpRagClient.ingestionFailureMessage(
                422, "{\"detail\":[{\"type\":\"missing\",\"loc\":[\"body\",\"contentBase64\"]}]}"))
        .isEqualTo("RAG ingestion failed");
    assertThat(HttpRagClient.ingestionFailureMessage(503, "remote details"))
        .isEqualTo("RAG ingestion failed");
  }
}
