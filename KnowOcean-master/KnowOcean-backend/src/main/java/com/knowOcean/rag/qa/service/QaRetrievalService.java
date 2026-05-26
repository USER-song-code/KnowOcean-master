package com.knowOcean.rag.qa.service;

import com.knowOcean.rag.qa.model.vo.AskQuestionResponse;
import com.knowOcean.rag.qa.rag.ReadyChunkDocumentRetriever;
import com.knowOcean.rag.qa.rag.RetrievedEvidenceBundle;
import com.knowOcean.rag.qa.support.CitationAssembler;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * QA 模块对外检索门面，供 assistant 等模块调用。
 */
@Service
public class QaRetrievalService {

    private final ReadyChunkDocumentRetriever documentRetriever;
    private final CitationAssembler citationAssembler;

    public QaRetrievalService(ReadyChunkDocumentRetriever documentRetriever,
                               CitationAssembler citationAssembler) {
        this.documentRetriever = documentRetriever;
        this.citationAssembler = citationAssembler;
    }

    /** 执行知识库检索，返回证据束和引用列表 */
    public QaRetrievalResult retrieveEvidence(Long groupId, String query) {
        RetrievedEvidenceBundle bundle = documentRetriever.retrieveEvidence(groupId, query);
        List<AskQuestionResponse.Citation> citations = citationAssembler.assembleDocuments(bundle.documents());
        return new QaRetrievalResult(bundle, citations);
    }

    public record QaRetrievalResult(
            RetrievedEvidenceBundle bundle,
            List<AskQuestionResponse.Citation> citations
    ) {}
}
