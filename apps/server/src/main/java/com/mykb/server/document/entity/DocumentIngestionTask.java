package com.mykb.server.document.entity;

import com.mykb.server.common.entity.AuditableEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.time.Instant;

@Entity
@Table(name = "document_ingestion_tasks")
public class DocumentIngestionTask extends AuditableEntity {

  public enum TaskType {
    DOCUMENT_INGESTION
  }

  public enum TaskStatus {
    PENDING,
    RUNNING,
    SUCCEEDED,
    FAILED
  }

  public enum TaskStage {
    QUEUED,
    OCR,
    UPLOAD,
    INDEXING,
    COMPLETED,
    FAILED
  }

  @ManyToOne(fetch = FetchType.LAZY, optional = false)
  @JoinColumn(name = "document_id", nullable = false)
  private KnowledgeDocument document;

  @Enumerated(EnumType.STRING)
  @Column(nullable = false, length = 32)
  private TaskType taskType = TaskType.DOCUMENT_INGESTION;

  @Enumerated(EnumType.STRING)
  @Column(nullable = false, length = 16)
  private TaskStatus status = TaskStatus.PENDING;

  @Enumerated(EnumType.STRING)
  @Column(nullable = false, length = 32)
  private TaskStage currentStage = TaskStage.QUEUED;

  @Enumerated(EnumType.STRING)
  @Column(length = 32)
  private TaskStage failedStage;

  @Column(length = 64)
  private String ocrEngine;

  @Column(length = 64)
  private String failureCode;

  @Column(length = 500)
  private String failureMessage;

  private Instant startedAt;

  private Instant finishedAt;

  public KnowledgeDocument getDocument() {
    return document;
  }

  public void setDocument(KnowledgeDocument document) {
    this.document = document;
  }

  public TaskType getTaskType() {
    return taskType;
  }

  public void setTaskType(TaskType taskType) {
    this.taskType = taskType;
  }

  public TaskStatus getStatus() {
    return status;
  }

  public void setStatus(TaskStatus status) {
    this.status = status;
  }

  public TaskStage getCurrentStage() {
    return currentStage;
  }

  public void setCurrentStage(TaskStage currentStage) {
    this.currentStage = currentStage;
  }

  public TaskStage getFailedStage() {
    return failedStage;
  }

  public void setFailedStage(TaskStage failedStage) {
    this.failedStage = failedStage;
  }

  public String getOcrEngine() {
    return ocrEngine;
  }

  public void setOcrEngine(String ocrEngine) {
    this.ocrEngine = ocrEngine;
  }

  public String getFailureCode() {
    return failureCode;
  }

  public void setFailureCode(String failureCode) {
    this.failureCode = failureCode;
  }

  public String getFailureMessage() {
    return failureMessage;
  }

  public void setFailureMessage(String failureMessage) {
    this.failureMessage = failureMessage;
  }

  public Instant getStartedAt() {
    return startedAt;
  }

  public void setStartedAt(Instant startedAt) {
    this.startedAt = startedAt;
  }

  public Instant getFinishedAt() {
    return finishedAt;
  }

  public void setFinishedAt(Instant finishedAt) {
    this.finishedAt = finishedAt;
  }
}