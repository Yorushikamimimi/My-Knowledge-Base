package com.mykb.server.rag.client;

public class RagOperationException extends RuntimeException {

  public RagOperationException(String message) {
    super(message);
  }

  public RagOperationException(String message, Throwable cause) {
    super(message, cause);
  }
}
