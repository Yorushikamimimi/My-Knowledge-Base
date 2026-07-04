package com.mykb.server.document.service;

import com.mykb.server.common.exception.AppException;
import com.mykb.server.common.storage.ObjectStorageService;
import com.mykb.server.common.storage.StorageOperationException;
import com.mykb.server.document.entity.DocumentIngestionTask;
import com.mykb.server.document.entity.KnowledgeDocument;
import com.mykb.server.document.repository.DocumentIngestionTaskRepository;
import com.mykb.server.knowledgebase.entity.KnowledgeBase;
import com.mykb.server.knowledgebase.repository.KnowledgeBaseRepository;
import com.mykb.server.ocr.client.OcrClient;
import com.mykb.server.ocr.client.OcrExtractResult;
import com.mykb.server.ocr.client.OcrOperationException;
import com.mykb.server.ocr.config.OcrProperties;
import com.mykb.server.rag.client.RagClient;
import com.mykb.server.rag.client.RagIngestRequest;
import com.mykb.server.rag.client.RagOperationException;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Base64;
import java.util.Locale;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;

@Service
public class DocumentIngestionWorkflowService {

  private static final Logger log = LoggerFactory.getLogger(DocumentIngestionWorkflowService.class);

  private final DocumentIngestionTaskRepository ingestionTaskRepository;
  private final KnowledgeBaseRepository knowledgeBaseRepository;
  private final ObjectStorageService objectStorageService;
  private final OcrClient ocrClient;
  private final OcrProperties ocrProperties;
  private final RagClient ragClient;
  private final TransactionTemplate transactionTemplate;

  public DocumentIngestionWorkflowService(
      DocumentIngestionTaskRepository ingestionTaskRepository,
      KnowledgeBaseRepository knowledgeBaseRepository,
      ObjectStorageService objectStorageService,
      OcrClient ocrClient,
      OcrProperties ocrProperties,
      RagClient ragClient,
      PlatformTransactionManager transactionManager) {
    this.ingestionTaskRepository = ingestionTaskRepository;
    this.knowledgeBaseRepository = knowledgeBaseRepository;
    this.objectStorageService = objectStorageService;
    this.ocrClient = ocrClient;
    this.ocrProperties = ocrProperties;
    this.ragClient = ragClient;
    this.transactionTemplate = new TransactionTemplate(transactionManager);
  }

  @Async("documentTaskExecutor")
  public void ingestAsync(UUID taskId) {
    DocumentIngestionTask.TaskStage failedStage = DocumentIngestionTask.TaskStage.UPLOAD;
    try {
      IngestionContext context = loadContext(taskId);
      boolean ocrRequired = requiresOcr(context);
      failedStage =
          ocrRequired ? DocumentIngestionTask.TaskStage.OCR : DocumentIngestionTask.TaskStage.UPLOAD;
      markRunning(taskId, failedStage);

      byte[] fileBytes =
          objectStorageService.read(context.storageBucket(), context.storageObjectKey());

      String ocrEngine = null;
      byte[] ragBytes = fileBytes;
      String ragContentType = context.contentType();
      if (ocrRequired) {
        OcrExtractResult extractResult =
            ocrClient.extractText(context.originalFilename(), context.contentType(), fileBytes);
        ocrEngine = trimToNull(extractResult.engine());
        ragBytes = (extractResult.text() == null ? "" : extractResult.text()).getBytes(StandardCharsets.UTF_8);
        ragContentType = "text/plain";
        updateStage(taskId, DocumentIngestionTask.TaskStage.UPLOAD);
      }

      failedStage = DocumentIngestionTask.TaskStage.INDEXING;
      updateStage(taskId, DocumentIngestionTask.TaskStage.INDEXING);
      ragClient.ingest(
          new RagIngestRequest(
              context.knowledgeBaseId().toString(),
              context.documentId().toString(),
              context.originalFilename(),
              ragContentType,
              Base64.getEncoder().encodeToString(ragBytes)));

      markSuccess(taskId, ocrEngine);
    } catch (OcrOperationException exception) {
      log.error("OCR ingestion failed. taskId={}", taskId, exception);
      markFailure(taskId, failedStage, "DOCUMENT_OCR_FAILED", exception.getMessage());
    } catch (StorageOperationException exception) {
      log.error("Stored document read failed. taskId={}", taskId, exception);
      markFailure(
          taskId,
          failedStage,
          "DOCUMENT_STORAGE_READ_FAILED",
          "Failed to read the stored document");
    } catch (RagOperationException exception) {
      log.error("RAG ingestion failed. taskId={}", taskId, exception);
      markFailure(taskId, failedStage, "DOCUMENT_RAG_FAILED", exception.getMessage());
    } catch (Exception exception) {
      log.error("Unexpected ingestion workflow failure. taskId={}", taskId, exception);
      markFailure(
          taskId,
          failedStage,
          "DOCUMENT_INGESTION_FAILED",
          "Document ingestion workflow failed");
    }
  }

  private boolean requiresOcr(IngestionContext context) {
    if (!ocrProperties.isEnabled()) {
      return false;
    }
    if (context.contentType() != null
        && context.contentType().equalsIgnoreCase(ocrProperties.getPdfContentType())) {
      return true;
    }
    return context.originalFilename().toLowerCase(Locale.ROOT).endsWith(".pdf");
  }

  private IngestionContext loadContext(UUID taskId) {
    return transactionTemplate.execute(
        status -> {
          DocumentIngestionTask task =
              ingestionTaskRepository
                  .findDetailedById(taskId)
                  .orElseThrow(
                      () ->
                          new AppException(
                              HttpStatus.NOT_FOUND,
                              "TASK_NOT_FOUND",
                              "Document ingestion task does not exist"));
          KnowledgeDocument document = task.getDocument();
          return new IngestionContext(
              taskId,
              document.getId(),
              document.getKnowledgeBase().getId(),
              document.getOriginalFilename(),
              trimToNull(document.getContentType()),
              document.getStorageBucket(),
              document.getStorageObjectKey());
        });
  }

  private void markRunning(UUID taskId, DocumentIngestionTask.TaskStage stage) {
    transactionTemplate.executeWithoutResult(
        status -> {
          DocumentIngestionTask task = getTaskOrThrow(taskId);
          task.setStatus(DocumentIngestionTask.TaskStatus.RUNNING);
          task.setCurrentStage(stage);
          task.setFailedStage(null);
          task.setStartedAt(Instant.now());
          task.setFinishedAt(null);
          task.setFailureCode(null);
          task.setFailureMessage(null);
          task.getDocument().setProcessingStatus(KnowledgeDocument.ProcessingStatus.PROCESSING);
        });
  }

  private void updateStage(UUID taskId, DocumentIngestionTask.TaskStage stage) {
    transactionTemplate.executeWithoutResult(
        status -> {
          DocumentIngestionTask task = getTaskOrThrow(taskId);
          task.setCurrentStage(stage);
        });
  }

  private void markSuccess(UUID taskId, String ocrEngine) {
    transactionTemplate.executeWithoutResult(
        status -> {
          DocumentIngestionTask task = getTaskOrThrow(taskId);
          task.setStatus(DocumentIngestionTask.TaskStatus.SUCCEEDED);
          task.setCurrentStage(DocumentIngestionTask.TaskStage.COMPLETED);
          task.setFailedStage(null);
          task.setFinishedAt(Instant.now());
          task.setFailureCode(null);
          task.setFailureMessage(null);
          task.setOcrEngine(trimToNull(ocrEngine));
          task.getDocument().setProcessingStatus(KnowledgeDocument.ProcessingStatus.SUCCEEDED);
          log.info(
              "Document ingestion completed. taskId={}, documentId={}",
              taskId,
              task.getDocument().getId());
        });
  }

  private void markFailure(
      UUID taskId,
      DocumentIngestionTask.TaskStage failedStage,
      String failureCode,
      String failureMessage) {
    try {
      transactionTemplate.executeWithoutResult(
          status -> {
            DocumentIngestionTask task = getTaskOrThrow(taskId);
            task.setStatus(DocumentIngestionTask.TaskStatus.FAILED);
            task.setCurrentStage(DocumentIngestionTask.TaskStage.FAILED);
            task.setFailedStage(failedStage);
            task.setFinishedAt(Instant.now());
            task.setFailureCode(failureCode);
            task.setFailureMessage(trimMessage(failureMessage));
            task.getDocument().setProcessingStatus(KnowledgeDocument.ProcessingStatus.FAILED);
          });
    } catch (Exception exception) {
      log.error("Failed to persist ingestion failure state. taskId={}", taskId, exception);
    }
  }

  private DocumentIngestionTask getTaskOrThrow(UUID taskId) {
    return ingestionTaskRepository
        .findDetailedById(taskId)
        .orElseThrow(
            () ->
                new AppException(
                    HttpStatus.NOT_FOUND,
                    "TASK_NOT_FOUND",
                    "Document ingestion task does not exist"));
  }

  private String trimToNull(String value) {
    if (value == null) {
      return null;
    }
    String normalized = value.trim();
    return normalized.isEmpty() ? null : normalized;
  }

  private String trimMessage(String message) {
    if (message == null) {
      return null;
    }
    String normalized = message.replaceAll("\\s+", " ").trim();
    return normalized.length() > 500 ? normalized.substring(0, 500) : normalized;
  }

  private record IngestionContext(
      UUID taskId,
      UUID documentId,
      UUID knowledgeBaseId,
      String originalFilename,
      String contentType,
      String storageBucket,
      String storageObjectKey) {}
}
