package com.mykb.server.knowledgebase.entity;

import com.mykb.server.auth.entity.UserAccount;
import com.mykb.server.common.entity.AuditableEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

@Entity
@Table(name = "knowledge_bases")
public class KnowledgeBase extends AuditableEntity {

  public enum Visibility {
    PRIVATE,
    SHARED
  }

  @ManyToOne(fetch = FetchType.LAZY, optional = false)
  @JoinColumn(name = "owner_id", nullable = false)
  private UserAccount owner;

  @Column(nullable = false, length = 80)
  private String name;

  @Column(length = 500)
  private String description;

  @Enumerated(EnumType.STRING)
  @Column(nullable = false, length = 16)
  private Visibility visibility = Visibility.PRIVATE;

  public UserAccount getOwner() {
    return owner;
  }

  public void setOwner(UserAccount owner) {
    this.owner = owner;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public String getDescription() {
    return description;
  }

  public void setDescription(String description) {
    this.description = description;
  }

  public Visibility getVisibility() {
    return visibility;
  }

  public void setVisibility(Visibility visibility) {
    this.visibility = visibility;
  }
}
