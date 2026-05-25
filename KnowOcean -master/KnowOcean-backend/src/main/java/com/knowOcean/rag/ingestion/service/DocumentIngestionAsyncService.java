package com.knowOcean.rag.ingestion.service;

import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.knowOcean.rag.common.enums.DocumentStatus;
import com.knowOcean.rag.common.exception.BusinessException;
import com.knowOcean.rag.document.mapper.DocumentMapper;
import com.knowOcean.rag.document.model.entity.DocumentEntity;
import com.knowOcean.rag.ingestion.mapper.DocumentChunkMapper;
import com.knowOcean.rag.ingestion.model.entity.DocumentChunkEntity;
import com.knowOcean.rag.ingestion.vector.VectorIngestionService;
import com.knowOcean.rag.engine.elasticsearch.ElasticsearchChunkIndexService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.retry.annotation.Backoff;
import org.springframework.retry.annotation.Recover;
import org.springframework.retry.annotation.Retryable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.TransactionDefinition;
import org.springframework.transaction.support.TransactionTemplate;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 异步文档 ETL（提取-转换-加载）服务。
 *
 * <p>负责在文档上传完成后异步执行以下流程：
 * <ol>
 *   <li>清理上一次处理的中间产物（chunk、向量、ES 索引）</li>
 *   <li>调用 {@link DocumentIngestionProcessor} 进行文档解析和分块</li>
 *   <li>将分块索引同步至 Elasticsearch</li>
 *   <li>将文档状态更新为 READY</li>
 * </ol>
 *
 * <p>通过 {@link Retryable} 注解支持失败自动重试（最多 3 次，退避策略：2s / 4s / 8s）。
 * 全部重试失败后由 {@link #recover} 方法将文档标记为 FAILED。
 *
 * <p><b>事务管理策略：</b>
 * <ul>
 *   <li>清理操作使用独立事务（REQUIRES_NEW），避免单个失败影响整体流程</li>
 *   <li>主 ETL 流程使用 REQUIRED 事务，确保数据一致性</li>
 * </ul>
 *
 * @author KnowOcean-RAG Team
 * @since 1.0.0
 */
@Service
@Slf4j
public class DocumentIngestionAsyncService {

    /** 失败原因字段最大长度 */
    private static final int FAILURE_REASON_MAX_LENGTH = 512;

    /** 文档数据访问 */
    private final DocumentMapper documentMapper;
    /** 文档分块处理引擎 */
    private final DocumentIngestionProcessor documentIngestionProcessor;
    /** 文档分块数据访问 */
    private final DocumentChunkMapper documentChunkMapper;
    /** 向量导入服务 */
    private final VectorIngestionService vectorIngestionService;
    /** Elasticsearch chunk 索引服务 */
    private final ElasticsearchChunkIndexService elasticsearchChunkIndexService;

    /** 编程式事务模板 - 用于清理操作（独立事务） */
    private final TransactionTemplate cleanupTxTemplate;
    /** 编程式事务模板 - 用于主 ETL 流程（必需事务） */
    private final TransactionTemplate etlTxTemplate;

    /**
     * 构造异步 ETL 服务，注入所有依赖。
     *
     * @param documentMapper                 文档数据访问层
     * @param documentIngestionProcessor     文档分块处理引擎
     * @param documentChunkMapper            文档分块数据访问层
     * @param vectorIngestionService         向量导入服务
     * @param elasticsearchChunkIndexService ES chunk 索引服务
     * @param transactionManager             平台事务管理器
     */
    public DocumentIngestionAsyncService(
            DocumentMapper documentMapper,
            DocumentIngestionProcessor documentIngestionProcessor,
            DocumentChunkMapper documentChunkMapper,
            VectorIngestionService vectorIngestionService,
            ElasticsearchChunkIndexService elasticsearchChunkIndexService,
            PlatformTransactionManager transactionManager
    ) {
        this.documentMapper = documentMapper;
        this.documentIngestionProcessor = documentIngestionProcessor;
        this.documentChunkMapper = documentChunkMapper;
        this.vectorIngestionService = vectorIngestionService;
        this.elasticsearchChunkIndexService = elasticsearchChunkIndexService;

        this.cleanupTxTemplate = new TransactionTemplate(transactionManager);
        this.cleanupTxTemplate.setPropagationBehavior(TransactionDefinition.PROPAGATION_REQUIRES_NEW);
        this.cleanupTxTemplate.setTimeout(30);

        this.etlTxTemplate = new TransactionTemplate(transactionManager);
        this.etlTxTemplate.setPropagationBehavior(TransactionDefinition.PROPAGATION_REQUIRED);
        this.etlTxTemplate.setTimeout(120);
    }

    /**
     * 异步执行文档 ETL 流程。
     *
     * <p>带重试机制：遇到 RuntimeException 时最多重试 3 次，
     * 退避策略为首次 2s，后续每次乘以 2（2s / 4s / 8s）。
     * 所有重试耗尽后由 {@link #recover} 兜底。
     *
     * <p><b>事务隔离设计：</b>
     * <ul>
     *   <li>{@code cleanupProcessingArtifacts()} 在独立事务中执行，异常不影响主流程</li>
     *   <li>主 ETL 逻辑在 {@code etlTxTemplate} 中执行，确保原子性</li>
     * </ul>
     *
     * @param documentId 文档 ID
     * @param groupId    文档所属群组 ID
     * @throws BusinessException 文档不存在或状态更新失败时抛出
     */
    @Retryable(
            retryFor = RuntimeException.class,
            maxAttempts = 3,
            backoff = @Backoff(delay = 2000, multiplier = 2.0)
    )
    public void ingestDocument(Long documentId, Long groupId) {
        log.info("开始异步执行文档ETL: documentId={}, groupId={}", documentId, groupId);
        cleanupProcessingArtifacts(documentId);
        etlTxTemplate.execute(status -> {
            DocumentEntity document = requireDocument(documentId, groupId);
            documentIngestionProcessor.process(documentId, groupId);
            syncSearchIndex(document);
            markDocumentStatus(documentId, groupId, DocumentStatus.READY.name(), null, LocalDateTime.now());
            log.info("异步文档ETL完成: documentId={}, groupId={}, status={}", documentId, groupId, DocumentStatus.READY.name());
            return null;
        });
    }

    /**
     * 重试全部失败后的兜底恢复方法。
     *
     * <p>清理中间产物，将文档状态标记为 FAILED 并记录截断后的失败原因。
     * 此方法由 Spring Retry 的 {@link Recover} 机制自动调用。
     *
     * @param exception  导致最终失败的异常
     * @param documentId 文档 ID
     * @param groupId    文档所属群组 ID
     */
    @Recover
    public void recover(RuntimeException exception, Long documentId, Long groupId) {
        log.error("异步文档ETL最终失败: documentId={}, groupId={}, reason={}", documentId, groupId, exception.getMessage(), exception);
        cleanupProcessingArtifacts(documentId);
        etlTxTemplate.execute(status -> {
            markDocumentStatus(
                    documentId,
                    groupId,
                    DocumentStatus.FAILED.name(),
                    truncateFailureReason(exception.getMessage()),
                    LocalDateTime.now()
            );
            return null;
        });
    }

    /**
     * 查询文档实体，不存在时抛出异常。
     *
     * @param documentId 文档 ID
     * @param groupId    文档所属群组 ID
     * @return 文档实体
     * @throws BusinessException 文档不存在时抛出
     */
    private DocumentEntity requireDocument(Long documentId, Long groupId) {
        DocumentEntity document = documentMapper.selectByIdAndGroupId(documentId, groupId);
        if (document == null) {
            throw new BusinessException("待处理文档不存在");
        }
        return document;
    }

    /**
     * 清理上一次处理遗留的中间产物。
     *
     * <p>每个清理操作在独立事务（REQUIRES_NEW）中执行，
     * 确保单个操作的异常不会影响其他清理步骤或主 ETL 事务。
     * 依次删除 chunk 记录、向量数据和 ES 索引。每项清理失败时仅记录日志，不中断后续清理。
     *
     * @param documentId 文档 ID
     */
    private void cleanupProcessingArtifacts(Long documentId) {
        log.info("开始清理上次处理中间产物: documentId={}", documentId);

        cleanupInNewTransaction(() -> {
            documentChunkMapper.deleteByDocumentId(documentId);
            log.debug("chunk 清理完成: documentId={}", documentId);
        }, "chunk", documentId);

        cleanupInNewTransaction(() -> {
            vectorIngestionService.deleteDocumentVectors(documentId);
            log.debug("向量清理完成: documentId={}", documentId);
        }, "向量", documentId);

        cleanupInNewTransaction(() -> {
            elasticsearchChunkIndexService.deleteDocumentChunks(documentId);
            log.debug("ES 索引清理完成: documentId={}", documentId);
        }, "ES 索引", documentId);

        log.info("中间产物清理完成: documentId={}", documentId);
    }

    /**
     * 在独立事务中执行单个清理操作。
     * <p>
     * 使用 REQUIRES_NEW 传播行为确保每个清理操作有独立的事务上下文，
     * 即使操作失败导致 PostgreSQL 事务 abort，也不会影响调用方或其他清理步骤。
     *
     * @param cleanupOperation 清理操作逻辑
     * @param operationName   操作名称（用于日志）
     * @param documentId      文档 ID（用于日志）
     */
    private void cleanupInNewTransaction(Runnable cleanupOperation, String operationName, Long documentId) {
        try {
            cleanupTxTemplate.execute(status -> {
                cleanupOperation.run();
                return null;
            });
        } catch (RuntimeException exception) {
            log.warn("清理旧{}失败: documentId={}, reason={}", operationName, documentId, exception.getMessage());
        }
    }

    /**
     * 将文档的分块数据同步到 Elasticsearch 搜索索引。
     *
     * @param document 文档实体
     */
    private void syncSearchIndex(DocumentEntity document) {
        log.info("开始同步ES搜索索引: documentId={}, fileName={}", document.getId(), document.getFileName());
        List<DocumentChunkEntity> chunks = documentChunkMapper.selectByDocumentId(document.getId());
        elasticsearchChunkIndexService.indexReadyChunks(document.getFileName(), chunks);
        log.info("ES搜索索引同步完成: documentId={}, indexedChunks={}", document.getId(), chunks.size());
    }

    /**
     * 更新文档状态、失败原因和处理时间。
     *
     * @param documentId    文档 ID
     * @param groupId       文档所属群组 ID
     * @param status        目标状态（READY 或 FAILED）
     * @param failureReason 失败原因（成功时为 null）
     * @param processedAt   处理完成时间
     * @throws BusinessException 更新影响行数为 0 时抛出
     */
    private void markDocumentStatus(
            Long documentId,
            Long groupId,
            String status,
            String failureReason,
            LocalDateTime processedAt
    ) {
        int updated = documentMapper.update(null, new LambdaUpdateWrapper<DocumentEntity>()
                .eq(DocumentEntity::getId, documentId)
                .eq(DocumentEntity::getGroupId, groupId)
                .set(DocumentEntity::getStatus, status)
                .set(DocumentEntity::getFailureReason, failureReason)
                .set(DocumentEntity::getProcessedAt, processedAt)
        );
        if (updated == 0) {
            throw new BusinessException("文档状态更新失败");
        }
    }

    /**
     * 截断失败原因字符串至最大长度，空值返回默认消息。
     *
     * @param failureReason 原始失败原因
     * @return 截断后的失败原因
     */
    private String truncateFailureReason(String failureReason) {
        if (failureReason == null || failureReason.isBlank()) {
            return "文档处理失败";
        }
        return failureReason.length() <= FAILURE_REASON_MAX_LENGTH
                ? failureReason
                : failureReason.substring(0, FAILURE_REASON_MAX_LENGTH);
    }
}
