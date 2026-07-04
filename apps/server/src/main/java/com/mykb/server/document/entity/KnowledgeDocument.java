package com.mykb.server.document.entity;

import com.mykb.server.auth.entity.UserAccount;
import com.mykb.server.common.entity.AuditableEntity;
import com.mykb.server.knowledgebase.entity.KnowledgeBase;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

@Entity
@Table(name = "knowledge_documents")
public class KnowledgeDocument extends AuditableEntity {

  public enum ProcessingStatus {
    QUEUED,
    PROCESSING,
    SUCCEEDED,
    FAILED
  }

  public enum StorageProvider {
    LOCAL,
    MINIO
  }

  @ManyToOne(fetch = FetchType.LAZY, optional = false)
  @JoinColumn(name = "knowledge_base_id", nullable = false)
  private KnowledgeBase knowledgeBase;

  @ManyToOne(fetch = FetchType.LAZY, optional = false)
  @JoinColumn(name = "uploader_id", nullable = false)
  private UserAccount uploader;

  @Column(nullable = false, length = 255)
  private String originalFilename;

  @Column(length = 120)
  private String contentType;

  @Column(nullable = false)
  private long sizeBytes;

  @Enumerated(EnumType.STRING)
  @Column(nullable = false, length = 16)
  private StorageProvider storageProvider;

  @Column(nullable = false, length = 80)
  private String storageBucket;

  @Column(nullable = false, length = 255)
  private String storageObjectKey;

  @Enumerated(EnumType.STRING)
  @Column(nullable = false, length = 16)
  private ProcessingStatus processingStatus = ProcessingStatus.QUEUED;

  public KnowledgeBase getKnowledgeBase() {
    return knowledgeBase;
  }

  public void setKnowledgeBase(KnowledgeBase knowledgeBase) {
    this.knowledgeBase = knowledgeBase;
  }

  public UserAccount getUploader() {
    return uploader;
  }

  public void setUploader(UserAccount uploader) {
    this.uploader = uploader;
  }

  public String getOriginalFilename() {
    return originalFilename;
  }

  public void setOriginalFilename(String originalFilename) {
    this.originalFilename = originalFilename;
  }

  public String getContentType() {
    return contentType;
  }

  public void setContentType(String contentType) {
    this.contentType = contentType;
  }

  public long getSizeBytes() {
    return sizeBytes;
  }

  public void setSizeBytes(long sizeBytes) {
    this.sizeBytes = sizeBytes;
  }

  public StorageProvider getStorageProvider() {
    return storageProvider;
  }

  public void setStorageProvider(StorageProvider storageProvider) {
    this.storageProvider = storageProvider;
  }

  public String getStorageBucket() {
    return storageBucket;
  }

  public void setStorageBucket(String storageBucket) {
    this.storageBucket = storageBucket;
  }

  public String getStorageObjectKey() {
    return storageObjectKey;
  }

  public void setStorageObjectKey(String storageObjectKey) {
    this.storageObjectKey = storageObjectKey;
  }

  public ProcessingStatus getProcessingStatus() {
    return processingStatus;
  }

  public void setProcessingStatus(ProcessingStatus processingStatus) {
    this.processingStatus = processingStatus;
  }
}
