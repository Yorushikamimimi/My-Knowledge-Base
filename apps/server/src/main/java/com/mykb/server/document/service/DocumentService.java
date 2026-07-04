package com.mykb.server.document.service;

import com.mykb.server.auth.entity.UserAccount;
import com.mykb.server.auth.repository.UserAccountRepository;
import com.mykb.server.common.exception.AppException;
import com.mykb.server.common.security.AuthenticatedUser;
import com.mykb.server.common.storage.ObjectStorageService;
import com.mykb.server.common.storage.StorageOperationException;
import com.mykb.server.common.storage.StorageProperties;
import com.mykb.server.common.storage.StoredObject;
import com.mykb.server.document.config.DocumentProperties;
import com.mykb.server.document.dto.DocumentUploadResponse;
import com.mykb.server.document.dto.IngestionTaskResponse;
import com.mykb.server.document.dto.KnowledgeDocumentResponse;
import com.mykb.server.document.entity.DocumentIngestionTask;
import com.mykb.server.document.entity.KnowledgeDocument;
import com.mykb.server.document.repository.DocumentIngestionTaskRepository;
import com.mykb.server.document.repository.KnowledgeDocumentRepository;
import com.mykb.server.knowledgebase.entity.KnowledgeBase;
import com.mykb.server.knowledgebase.repository.KnowledgeBaseRepository;
import com.mykb.server.knowledgebase.repository.KnowledgeBaseShareRepository;
import java.io.IOException;
import java.io.InputStream;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

@Service
public class DocumentService {

  private static final Logger log = LoggerFactory.getLogger(DocumentService.class);

  private final KnowledgeBaseRepository knowledgeBaseRepository;
  private final KnowledgeBaseShareRepository knowledgeBaseShareRepository;
  private final UserAccountRepository userAccountRepository;
  private final KnowledgeDocumentRepository knowledgeDocumentRepository;
  private final DocumentIngestionTaskRepository ingestionTaskRepository;
  private final ObjectStorageService objectStorageService;
  private final StorageProperties storageProperties;
  private final Set<String> allowedFileExtensions;
  private final ApplicationEventPublisher eventPublisher;

  public DocumentService(
      KnowledgeBaseRepository knowledgeBaseRepository,
      KnowledgeBaseShareRepository knowledgeBaseShareRepository,
      UserAccountRepository userAccountRepository,
      KnowledgeDocumentRepository knowledgeDocumentRepository,
      DocumentIngestionTaskRepository ingestionTaskRepository,
      ObjectStorageService objectStorageService,
      StorageProperties storageProperties,
      DocumentProperties documentProperties,
      ApplicationEventPublisher eventPublisher) {
    this.knowledgeBaseRepository = knowledgeBaseRepository;
    this.knowledgeBaseShareRepository = knowledgeBaseShareRepository;
    this.userAccountRepository = userAccountRepository;
    this.knowledgeDocumentRepository = knowledgeDocumentRepository;
    this.ingestionTaskRepository = ingestionTaskRepository;
    this.objectStorageService = objectStorageService;
    this.storageProperties = storageProperties;
    this.allowedFileExtensions =
        documentProperties.getAllowedFileExtensions().stream()
            .map(value -> value == null ? "" : value.trim().toLowerCase(Locale.ROOT))
            .filter(value -> !value.isBlank())
            .collect(Collectors.toUnmodifiableSet());
    this.eventPublisher = eventPublisher;
  }

  @Transactional
  public DocumentUploadResponse upload(
      AuthenticatedUser currentUser, UUID knowledgeBaseId, MultipartFile file) {
    KnowledgeBase knowledgeBase = getOwnedKnowledgeBase(currentUser.userId(), knowledgeBaseId);
    validateFile(file);

    String originalFilename = normalizeFilename(file.getOriginalFilename());
    if (knowledgeDocumentRepository
        .existsByKnowledgeBase_IdAndOriginalFilenameIgnoreCaseAndSizeBytes(
            knowledgeBaseId, originalFilename, file.getSize())) {
      throw new AppException(
          HttpStatus.CONFLICT,
          "DOCUMENT_ALREADY_EXISTS",
          "Duplicate document upload is not allowed");
    }

    UserAccount uploader =
        userAccountRepository
            .findById(currentUser.userId())
            .orElseThrow(
                () ->
                    new AppException(
                        HttpStatus.NOT_FOUND, "USER_NOT_FOUND", "User does not exist"));

    String objectKey = buildObjectKey(knowledgeBaseId, originalFilename, file.getSize());
    StoredObject storedObject = storeFile(objectKey, file);

    KnowledgeDocument document = new KnowledgeDocument();
    document.setKnowledgeBase(knowledgeBase);
    document.setUploader(uploader);
    document.setOriginalFilename(originalFilename);
    document.setContentType(trimToNull(file.getContentType()));
    document.setSizeBytes(file.getSize());
    document.setStorageProvider(KnowledgeDocument.StorageProvider.valueOf(storedObject.provider()));
    document.setStorageBucket(storedObject.bucket());
    document.setStorageObjectKey(storedObject.objectKey());
    document.setProcessingStatus(KnowledgeDocument.ProcessingStatus.QUEUED);
    KnowledgeDocument savedDocument = knowledgeDocumentRepository.save(document);

    DocumentIngestionTask savedTask = createQueuedTask(savedDocument);

    eventPublisher.publishEvent(new DocumentIngestionRequestedEvent(savedTask.getId()));
    log.info(
        "Document uploaded and ingestion requested. kbId={}, documentId={}, taskId={}, uploaderId={}, sizeBytes={}",
        knowledgeBaseId,
        savedDocument.getId(),
        savedTask.getId(),
        currentUser.userId(),
        file.getSize());
    return new DocumentUploadResponse(toDocumentResponse(savedDocument), toTaskResponse(savedTask));
  }

  @Transactional
  public void deleteFailedDocument(
      AuthenticatedUser currentUser, UUID knowledgeBaseId, UUID documentId) {
    KnowledgeDocument document = getOwnedDocument(currentUser.userId(), knowledgeBaseId, documentId);
    if (document.getProcessingStatus() != KnowledgeDocument.ProcessingStatus.FAILED) {
      throw new AppException(
          HttpStatus.CONFLICT,
          "DOCUMENT_DELETE_FAILED_ONLY",
          "Only failed documents can be deleted");
    }

    try {
      objectStorageService.delete(document.getStorageBucket(), document.getStorageObjectKey());
    } catch (StorageOperationException exception) {
      log.error("Document delete failed in object storage. documentId={}", documentId, exception);
      throw new AppException(
          HttpStatus.SERVICE_UNAVAILABLE,
          "DOCUMENT_DELETE_STORAGE_FAILED",
          "Failed to delete stored document content");
    }

    ingestionTaskRepository.deleteAll(ingestionTaskRepository.findByDocument_IdOrderByCreatedAtDesc(documentId));
    knowledgeDocumentRepository.delete(document);
    log.info(
        "Failed document deleted. kbId={}, documentId={}, ownerId={}",
        knowledgeBaseId,
        documentId,
        currentUser.userId());
  }

  @Transactional
  public IngestionTaskResponse retryFailedTask(
      AuthenticatedUser currentUser, UUID knowledgeBaseId, UUID taskId) {
    DocumentIngestionTask failedTask = getOwnedTask(currentUser.userId(), knowledgeBaseId, taskId);
    if (failedTask.getStatus() != DocumentIngestionTask.TaskStatus.FAILED) {
      throw new AppException(
          HttpStatus.CONFLICT,
          "TASK_RETRY_FAILED_ONLY",
          "Only failed ingestion tasks can be retried");
    }

    KnowledgeDocument document = failedTask.getDocument();
    if (document.getProcessingStatus() == KnowledgeDocument.ProcessingStatus.PROCESSING) {
      throw new AppException(
          HttpStatus.CONFLICT,
          "DOCUMENT_ALREADY_PROCESSING",
          "Document ingestion is already in progress");
    }

    document.setProcessingStatus(KnowledgeDocument.ProcessingStatus.QUEUED);
    DocumentIngestionTask retriedTask = createQueuedTask(document);
    eventPublisher.publishEvent(new DocumentIngestionRequestedEvent(retriedTask.getId()));
    log.info(
        "Failed ingestion task retried. kbId={}, documentId={}, oldTaskId={}, newTaskId={}, ownerId={}",
        knowledgeBaseId,
        document.getId(),
        taskId,
        retriedTask.getId(),
        currentUser.userId());
    return toTaskResponse(retriedTask);
  }

  @Transactional(readOnly = true)
  public List<KnowledgeDocumentResponse> listDocuments(
      AuthenticatedUser currentUser, UUID knowledgeBaseId) {
    getAccessibleKnowledgeBase(currentUser.userId(), knowledgeBaseId);
    return knowledgeDocumentRepository
        .findByKnowledgeBase_IdOrderByCreatedAtDesc(knowledgeBaseId)
        .stream()
        .map(this::toDocumentResponse)
        .toList();
  }

  @Transactional(readOnly = true)
  public List<IngestionTaskResponse> listTasks(
      AuthenticatedUser currentUser, UUID knowledgeBaseId) {
    getAccessibleKnowledgeBase(currentUser.userId(), knowledgeBaseId);
    return ingestionTaskRepository
        .findByDocument_KnowledgeBase_IdOrderByCreatedAtDesc(knowledgeBaseId)
        .stream()
        .map(this::toTaskResponse)
        .toList();
  }

  private DocumentIngestionTask createQueuedTask(KnowledgeDocument document) {
    DocumentIngestionTask task = new DocumentIngestionTask();
    task.setDocument(document);
    task.setTaskType(DocumentIngestionTask.TaskType.DOCUMENT_INGESTION);
    task.setStatus(DocumentIngestionTask.TaskStatus.PENDING);
    task.setCurrentStage(DocumentIngestionTask.TaskStage.QUEUED);
    task.setOcrEngine(null);
    task.setFailureCode(null);
    task.setFailureMessage(null);
    task.setStartedAt(null);
    task.setFinishedAt(null);
    return ingestionTaskRepository.save(task);
  }

  private StoredObject storeFile(String objectKey, MultipartFile file) {
    try (InputStream inputStream = file.getInputStream()) {
      return objectStorageService.store(
          objectKey, inputStream, file.getSize(), file.getContentType());
    } catch (IOException | StorageOperationException exception) {
      log.error("Document storage failed. objectKey={}", objectKey, exception);
      throw new AppException(
          HttpStatus.SERVICE_UNAVAILABLE, "DOCUMENT_STORAGE_FAILED", "Document storage failed");
    }
  }

  private void validateFile(MultipartFile file) {
    if (file == null || file.isEmpty()) {
      throw new AppException(
          HttpStatus.BAD_REQUEST, "FILE_EMPTY", "Uploaded file must not be empty");
    }
    if (file.getSize() > storageProperties.getMaxUploadSizeBytes()) {
      throw new AppException(
          HttpStatus.BAD_REQUEST, "FILE_TOO_LARGE", "Uploaded file exceeds the current size limit");
    }
    String originalFilename = normalizeFilename(file.getOriginalFilename());
    if (originalFilename.isBlank()) {
      throw new AppException(
          HttpStatus.BAD_REQUEST, "FILE_NAME_INVALID", "Filename must not be blank");
    }
    String fileExtension = extractFileExtension(originalFilename);
    if (fileExtension.isBlank() || !allowedFileExtensions.contains(fileExtension)) {
      throw new AppException(
          HttpStatus.BAD_REQUEST,
          "FILE_TYPE_NOT_ALLOWED",
          "Only PDF, Markdown, DOC, and DOCX files are supported");
    }
  }

  private KnowledgeBase getOwnedKnowledgeBase(UUID currentUserId, UUID knowledgeBaseId) {
    KnowledgeBase knowledgeBase =
        knowledgeBaseRepository
            .findById(knowledgeBaseId)
            .orElseThrow(
                () ->
                    new AppException(
                        HttpStatus.NOT_FOUND,
                        "KNOWLEDGE_BASE_NOT_FOUND",
                        "Knowledge base does not exist"));
    if (!knowledgeBase.getOwner().getId().equals(currentUserId)) {
      throw new AppException(
          HttpStatus.FORBIDDEN,
          "KNOWLEDGE_BASE_OWNER_ONLY",
          "Only the knowledge base owner can upload documents");
    }
    return knowledgeBase;
  }

  private KnowledgeDocument getOwnedDocument(UUID currentUserId, UUID knowledgeBaseId, UUID documentId) {
    KnowledgeBase knowledgeBase = getOwnedKnowledgeBase(currentUserId, knowledgeBaseId);
    KnowledgeDocument document =
        knowledgeDocumentRepository
            .findDetailedById(documentId)
            .orElseThrow(
                () ->
                    new AppException(
                        HttpStatus.NOT_FOUND,
                        "DOCUMENT_NOT_FOUND",
                        "Knowledge document does not exist"));
    if (!document.getKnowledgeBase().getId().equals(knowledgeBase.getId())) {
      throw new AppException(
          HttpStatus.NOT_FOUND,
          "DOCUMENT_NOT_FOUND",
          "Knowledge document does not exist in the current knowledge base");
    }
    return document;
  }

  private DocumentIngestionTask getOwnedTask(UUID currentUserId, UUID knowledgeBaseId, UUID taskId) {
    KnowledgeBase knowledgeBase = getOwnedKnowledgeBase(currentUserId, knowledgeBaseId);
    DocumentIngestionTask task =
        ingestionTaskRepository
            .findDetailedById(taskId)
            .orElseThrow(
                () ->
                    new AppException(
                        HttpStatus.NOT_FOUND,
                        "INGESTION_TASK_NOT_FOUND",
                        "Document ingestion task does not exist"));
    if (!task.getDocument().getKnowledgeBase().getId().equals(knowledgeBase.getId())) {
      throw new AppException(
          HttpStatus.NOT_FOUND,
          "INGESTION_TASK_NOT_FOUND",
          "Document ingestion task does not exist in the current knowledge base");
    }
    return task;
  }

  private KnowledgeBase getAccessibleKnowledgeBase(UUID currentUserId, UUID knowledgeBaseId) {
    KnowledgeBase knowledgeBase =
        knowledgeBaseRepository
            .findById(knowledgeBaseId)
            .orElseThrow(
                () ->
                    new AppException(
                        HttpStatus.NOT_FOUND,
                        "KNOWLEDGE_BASE_NOT_FOUND",
                        "Knowledge base does not exist"));
    boolean owner = knowledgeBase.getOwner().getId().equals(currentUserId);
    boolean shared =
        knowledgeBaseShareRepository.existsByKnowledgeBase_IdAndSharedWith_Id(
            knowledgeBaseId, currentUserId);
    if (!owner && !shared) {
      throw new AppException(
          HttpStatus.FORBIDDEN,
          "KNOWLEDGE_BASE_ACCESS_DENIED",
          "You do not have access to this knowledge base");
    }
    return knowledgeBase;
  }

  private String buildObjectKey(UUID knowledgeBaseId, String originalFilename, long sizeBytes) {
    String sanitizedName = originalFilename.replaceAll("[^a-zA-Z0-9._-]", "_");
    return "knowledge-bases/%s/documents/%d-%s"
        .formatted(knowledgeBaseId, sizeBytes, sanitizedName);
  }

  private String normalizeFilename(String originalFilename) {
    if (originalFilename == null) {
      return "";
    }
    String normalized = originalFilename.replace("\\", "/");
    int lastSlashIndex = normalized.lastIndexOf('/');
    return normalized.substring(lastSlashIndex + 1).trim();
  }

  private String extractFileExtension(String filename) {
    String normalizedFilename = normalizeFilename(filename);
    int lastDotIndex = normalizedFilename.lastIndexOf('.');
    if (lastDotIndex <= 0 || lastDotIndex == normalizedFilename.length() - 1) {
      return "";
    }
    return normalizedFilename.substring(lastDotIndex + 1).trim().toLowerCase(Locale.ROOT);
  }

  private String trimToNull(String value) {
    if (value == null) {
      return null;
    }
    String trimmed = value.trim();
    return trimmed.isEmpty() ? null : trimmed;
  }

  private KnowledgeDocumentResponse toDocumentResponse(KnowledgeDocument document) {
    return new KnowledgeDocumentResponse(
        document.getId(),
        document.getKnowledgeBase().getId(),
        document.getUploader().getId(),
        document.getOriginalFilename(),
        document.getContentType(),
        document.getSizeBytes(),
        document.getStorageProvider().name(),
        document.getProcessingStatus().name(),
        document.getCreatedAt());
  }

  private IngestionTaskResponse toTaskResponse(DocumentIngestionTask task) {
    return new IngestionTaskResponse(
        task.getId(),
        task.getDocument().getId(),
        task.getTaskType().name(),
        task.getStatus().name(),
        task.getCurrentStage().name(),
        task.getFailedStage() == null ? null : task.getFailedStage().name(),
        task.getOcrEngine(),
        task.getFailureCode(),
        task.getFailureMessage(),
        task.getStartedAt(),
        task.getFinishedAt(),
        task.getCreatedAt());
  }
}
