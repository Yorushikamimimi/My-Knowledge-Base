ALTER TABLE knowledge_bases DROP COLUMN IF EXISTS dify_dataset_id;
ALTER TABLE knowledge_documents DROP COLUMN IF EXISTS dify_document_id;
ALTER TABLE document_ingestion_tasks DROP COLUMN IF EXISTS external_batch_id;
