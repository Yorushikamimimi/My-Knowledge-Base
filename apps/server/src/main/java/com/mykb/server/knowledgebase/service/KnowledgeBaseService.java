package com.mykb.server.knowledgebase.service;

import com.mykb.server.auth.entity.UserAccount;
import com.mykb.server.auth.repository.UserAccountRepository;
import com.mykb.server.common.exception.AppException;
import com.mykb.server.common.security.AuthenticatedUser;
import com.mykb.server.knowledgebase.dto.KnowledgeBaseCreateRequest;
import com.mykb.server.knowledgebase.dto.KnowledgeBaseResponse;
import com.mykb.server.knowledgebase.dto.KnowledgeBaseShareRequest;
import com.mykb.server.knowledgebase.entity.KnowledgeBase;
import com.mykb.server.knowledgebase.entity.KnowledgeBaseShare;
import com.mykb.server.knowledgebase.repository.KnowledgeBaseRepository;
import com.mykb.server.knowledgebase.repository.KnowledgeBaseShareRepository;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class KnowledgeBaseService {

  private static final Logger log = LoggerFactory.getLogger(KnowledgeBaseService.class);

  private final KnowledgeBaseRepository knowledgeBaseRepository;
  private final KnowledgeBaseShareRepository knowledgeBaseShareRepository;
  private final UserAccountRepository userAccountRepository;

  public KnowledgeBaseService(
      KnowledgeBaseRepository knowledgeBaseRepository,
      KnowledgeBaseShareRepository knowledgeBaseShareRepository,
      UserAccountRepository userAccountRepository) {
    this.knowledgeBaseRepository = knowledgeBaseRepository;
    this.knowledgeBaseShareRepository = knowledgeBaseShareRepository;
    this.userAccountRepository = userAccountRepository;
  }

  @Transactional
  public KnowledgeBaseResponse create(
      AuthenticatedUser currentUser, KnowledgeBaseCreateRequest request) {
    String normalizedName = request.name().trim();
    if (knowledgeBaseRepository.existsByOwner_IdAndNameIgnoreCase(
        currentUser.userId(), normalizedName)) {
      throw new AppException(
          HttpStatus.CONFLICT, "KNOWLEDGE_BASE_EXISTS", "知识库名称已存在");
    }

    UserAccount owner = getUser(currentUser.userId());
    KnowledgeBase knowledgeBase = new KnowledgeBase();
    knowledgeBase.setOwner(owner);
    knowledgeBase.setName(normalizedName);
    knowledgeBase.setDescription(trimToNull(request.description()));
    KnowledgeBase savedKnowledgeBase = knowledgeBaseRepository.save(knowledgeBase);

    log.info(
        "Knowledge base created. kbId={}, ownerId={}", savedKnowledgeBase.getId(), owner.getId());
    return toResponse(savedKnowledgeBase, currentUser.userId());
  }

  @Transactional(readOnly = true)
  public List<KnowledgeBaseResponse> listAccessible(AuthenticatedUser currentUser) {
    return knowledgeBaseRepository.findAccessibleByUserId(currentUser.userId()).stream()
        .map(knowledgeBase -> toResponse(knowledgeBase, currentUser.userId()))
        .toList();
  }

  @Transactional(readOnly = true)
  public KnowledgeBaseResponse getDetail(AuthenticatedUser currentUser, UUID knowledgeBaseId) {
    return toResponse(
        getAccessibleKnowledgeBase(currentUser.userId(), knowledgeBaseId), currentUser.userId());
  }

  @Transactional
  public KnowledgeBaseResponse share(
      AuthenticatedUser currentUser, UUID knowledgeBaseId, KnowledgeBaseShareRequest request) {
    KnowledgeBase knowledgeBase =
        knowledgeBaseRepository
            .findByIdForUpdate(knowledgeBaseId)
            .orElseThrow(
                () ->
                    new AppException(
                        HttpStatus.NOT_FOUND, "KNOWLEDGE_BASE_NOT_FOUND", "知识库不存在"));

    if (!knowledgeBase.getOwner().getId().equals(currentUser.userId())) {
      throw new AppException(
          HttpStatus.FORBIDDEN, "KNOWLEDGE_BASE_OWNER_ONLY", "只有拥有者可以共享知识库");
    }

    UserAccount targetUser =
        userAccountRepository
            .findByEmailIgnoreCase(normalize(request.targetEmail()))
            .orElseThrow(
                () ->
                    new AppException(HttpStatus.NOT_FOUND, "TARGET_USER_NOT_FOUND", "目标用户不存在"));

    if (targetUser.getId().equals(currentUser.userId())) {
      throw new AppException(HttpStatus.CONFLICT, "INVALID_SHARE_TARGET", "不能共享给自己");
    }

    if (!knowledgeBaseShareRepository.existsByKnowledgeBase_IdAndSharedWith_Id(
        knowledgeBase.getId(), targetUser.getId())) {
      KnowledgeBaseShare share = new KnowledgeBaseShare();
      share.setKnowledgeBase(knowledgeBase);
      share.setSharedWith(targetUser);
      knowledgeBaseShareRepository.save(share);
      log.info(
          "Knowledge base shared. kbId={}, ownerId={}, targetUserId={}",
          knowledgeBase.getId(),
          currentUser.userId(),
          targetUser.getId());
    }

    knowledgeBase.setVisibility(KnowledgeBase.Visibility.SHARED);
    knowledgeBaseRepository.save(knowledgeBase);
    return toResponse(knowledgeBase, currentUser.userId());
  }

  private KnowledgeBase getAccessibleKnowledgeBase(UUID currentUserId, UUID knowledgeBaseId) {
    KnowledgeBase knowledgeBase =
        knowledgeBaseRepository
            .findById(knowledgeBaseId)
            .orElseThrow(
                () ->
                    new AppException(
                        HttpStatus.NOT_FOUND, "KNOWLEDGE_BASE_NOT_FOUND", "知识库不存在"));

    boolean owner = knowledgeBase.getOwner().getId().equals(currentUserId);
    boolean shared =
        knowledgeBaseShareRepository.existsByKnowledgeBase_IdAndSharedWith_Id(
            knowledgeBaseId, currentUserId);
    if (!owner && !shared) {
      throw new AppException(
          HttpStatus.FORBIDDEN, "KNOWLEDGE_BASE_ACCESS_DENIED", "无权访问该知识库");
    }
    return knowledgeBase;
  }

  private UserAccount getUser(UUID userId) {
    return userAccountRepository
        .findById(userId)
        .orElseThrow(() -> new AppException(HttpStatus.NOT_FOUND, "USER_NOT_FOUND", "用户不存在"));
  }

  private KnowledgeBaseResponse toResponse(KnowledgeBase knowledgeBase, UUID currentUserId) {
    String accessType =
        knowledgeBase.getOwner().getId().equals(currentUserId) ? "OWNER" : "SHARED_VIEWER";
    return new KnowledgeBaseResponse(
        knowledgeBase.getId(),
        knowledgeBase.getName(),
        knowledgeBase.getDescription(),
        knowledgeBase.getVisibility().name(),
        knowledgeBase.getOwner().getId(),
        knowledgeBase.getOwner().getUsername(),
        accessType,
        knowledgeBase.getCreatedAt());
  }

  private String normalize(String value) {
    return value == null ? null : value.trim().toLowerCase(Locale.ROOT);
  }

  private String trimToNull(String value) {
    if (value == null) {
      return null;
    }
    String trimmed = value.trim();
    return trimmed.isEmpty() ? null : trimmed;
  }
}
