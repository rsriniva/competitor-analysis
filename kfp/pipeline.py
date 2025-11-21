"""
Master Pipeline: Document Ingestion (PDF -> Markdown -> Embeddings)

Simple, stateless pipeline with two components:
1. Convert PDFs to Markdown
2. Generate embeddings and store in Milvus

No data passing between components - Minio buckets serve as coordination mechanism.
All configuration from ConfigMap/Secrets via environment variables.
"""

from kfp import dsl, compiler, kubernetes

# Import components
from component_convert import convert_pdfs_to_markdown
from component_embed import generate_embeddings_and_store


@dsl.pipeline(
    name="document-ingestion-pipeline",
    description="Unified pipeline: PDF -> Markdown -> Embeddings -> Milvus (stateless, Minio-coordinated)"
)
def document_ingestion_pipeline(
    minio_secret_name: str = "minio-secret",
    pipeline_configmap_name: str = "pipeline-config",
    run_id: str = "v1"
):
    """
    Two-stage document ingestion pipeline.
    
    Stage 1: PDF Conversion
      - Downloads PDFs from Minio input bucket
      - Converts to Markdown using Docling
      - Uploads to Minio intermediate bucket
    
    Stage 2: Embedding Generation
      - Downloads Markdown from Minio intermediate bucket
      - Generates embeddings via LlamaStack
      - Stores in Milvus vector database
    
    Args:
        minio_secret_name: Kubernetes secret containing Minio credentials
        pipeline_configmap_name: Kubernetes ConfigMap with pipeline configuration
        run_id: Version identifier to force fresh execution (bypasses cache)
    """
    
    # ========================================
    # Component 1: Convert PDFs to Markdown
    # ========================================
    convert_task = convert_pdfs_to_markdown(run_id=run_id)
    
    # Inject Minio credentials from Secret
    kubernetes.use_secret_as_env(
        task=convert_task,
        secret_name=minio_secret_name,
        secret_key_to_env={
            'minio_root_user': 'MINIO_ACCESS_KEY',
            'minio_root_password': 'MINIO_SECRET_KEY'
        }
    )
    
    # Inject configuration from ConfigMap
    kubernetes.use_config_map_as_env(
        task=convert_task,
        config_map_name=pipeline_configmap_name,
        config_map_key_to_env={
            'minio_endpoint': 'MINIO_ENDPOINT',
            'minio_secure': 'MINIO_SECURE',
            'input_docs_bucket': 'INPUT_DOCS_BUCKET',
            'markdown_docs_bucket': 'MARKDOWN_DOCS_BUCKET',
            'markdown_docs_prefix': 'MARKDOWN_DOCS_PREFIX',
        }
    )
    
    # ========================================
    # Component 2: Generate Embeddings
    # ========================================
    embed_task = generate_embeddings_and_store(run_id=run_id)
    
    # Inject Minio credentials from Secret
    kubernetes.use_secret_as_env(
        task=embed_task,
        secret_name=minio_secret_name,
        secret_key_to_env={
            'minio_root_user': 'MINIO_ACCESS_KEY',
            'minio_root_password': 'MINIO_SECRET_KEY'
        }
    )
    
    # Inject configuration from ConfigMap
    kubernetes.use_config_map_as_env(
        task=embed_task,
        config_map_name=pipeline_configmap_name,
        config_map_key_to_env={
            'minio_endpoint': 'MINIO_ENDPOINT',
            'minio_secure': 'MINIO_SECURE',
            'markdown_docs_bucket': 'MARKDOWN_DOCS_BUCKET',
            'markdown_docs_prefix': 'MARKDOWN_DOCS_PREFIX',
            'llamastack_url': 'LLAMASTACK_URL',
            'vector_db_id': 'VECTOR_DB_ID',
            'chunk_size_in_tokens': 'CHUNK_SIZE_IN_TOKENS',
        }
    )
    
    # Ensure component 2 runs after component 1 completes
    embed_task.after(convert_task)


if __name__ == "__main__":
    # Compile pipeline to YAML
    output_file = "pipeline.yaml"
    
    print("=" * 70)
    print("COMPILING DOCUMENT INGESTION PIPELINE")
    print("=" * 70)
    print(f"\nPipeline Architecture:")
    print(f"  Component 1: convert_pdfs_to_markdown")
    print(f"    - Downloads PDFs from Minio")
    print(f"    - Converts to Markdown (Docling)")
    print(f"    - Uploads to intermediate bucket")
    print(f"")
    print(f"  Component 2: generate_embeddings_and_store")
    print(f"    - Downloads Markdown from Minio")
    print(f"    - Generates embeddings (LlamaStack)")
    print(f"    - Stores in Milvus vector database")
    print(f"")
    print(f"Data Flow:")
    print(f"  Minio(documents) -> Component 1 -> Minio(intermediate/markdown)")
    print(f"  Minio(intermediate/markdown) -> Component 2 -> Milvus")
    print(f"")
    print(f"Output: {output_file}")
    print(f"\nCompiling...")
    
    compiler.Compiler().compile(
        pipeline_func=document_ingestion_pipeline,
        package_path=output_file
    )
    
    print(f"\n[OK] Pipeline compiled successfully!")
    print("=" * 70)
    print("HOW TO USE")
    print("=" * 70)
    print(f"1. Navigate to Data Science Pipelines in RHOAI")
    print(f"2. Click 'Import pipeline'")
    print(f"3. Upload: {output_file}")
    print(f"4. Create a run:")
    print(f"   - minio_secret_name: minio-secret (default)")
    print(f"   - pipeline_configmap_name: pipeline-config (default)")
    print(f"   - run_id: v1 (change to v2, v3... to bypass cache)")
    print(f"5. Click 'Run'")
    print(f"")
    print(f"All configuration comes from ConfigMap 'pipeline-config':")
    print(f"  - minio_endpoint")
    print(f"  - input_docs_bucket")
    print(f"  - markdown_docs_bucket")
    print(f"  - markdown_docs_prefix")
    print(f"  - llamastack_url")
    print(f"  - vector_db_id")
    print(f"  - chunk_size_in_tokens")
    print("=" * 70)

