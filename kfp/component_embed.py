"""
Component 2: Generate Embeddings and Store in Milvus
Downloads Markdown from Minio, generates embeddings via LlamaStack, stores in Milvus.
Completely stateless - uses Minio bucket as input source.
"""

from kfp import dsl


@dsl.component(
    base_image="quay.io/rsriniva/kfp-docling:latest"
)
def generate_embeddings_and_store(
    run_id: str = "v1"
):
    """
    Download all Markdown files from Minio, generate embeddings, store in Milvus.
    All configuration comes from environment variables (ConfigMap/Secrets).
    
    Args:
        run_id: Version identifier for cache busting
    """
    import os
    import sys
    from minio import Minio
    from llama_stack_client import LlamaStackClient
    from llama_stack_client.types import Document
    
    print("=" * 70)
    print("COMPONENT 2: GENERATE EMBEDDINGS AND STORE IN MILVUS")
    print("=" * 70)
    print(f"Run ID: {run_id}")
    
    # Get all configuration from environment variables (injected from ConfigMap/Secret)
    minio_endpoint = os.environ.get('MINIO_ENDPOINT')
    minio_access_key = os.environ.get('MINIO_ACCESS_KEY')
    minio_secret_key = os.environ.get('MINIO_SECRET_KEY')
    minio_secure = os.environ.get('MINIO_SECURE', 'false').lower() in ('true', '1', 'yes')
    
    markdown_bucket = os.environ.get('MARKDOWN_DOCS_BUCKET')
    markdown_prefix = os.environ.get('MARKDOWN_DOCS_PREFIX', 'markdown/')
    
    llamastack_url = os.environ.get('LLAMASTACK_URL')
    vector_db_id = os.environ.get('VECTOR_DB_ID')
    chunk_size = int(os.environ.get('CHUNK_SIZE_IN_TOKENS', '512'))
    
    print(f"\nConfiguration:")
    print(f"  Minio: {minio_endpoint}")
    print(f"  Markdown bucket: {markdown_bucket}")
    print(f"  Markdown prefix: {markdown_prefix}")
    print(f"  LlamaStack: {llamastack_url}")
    print(f"  Vector DB: {vector_db_id}")
    print(f"  Chunk size: {chunk_size} tokens")
    
    markdown_dir = "/tmp/markdown"
    os.makedirs(markdown_dir, exist_ok=True)
    
    try:
        # Step 1: Connect to services
        print(f"\n{'=' * 70}")
        print("STEP 1: CONNECT TO SERVICES")
        print("=" * 70)
        
        minio_client = Minio(
            minio_endpoint,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            secure=minio_secure
        )
        print(f"[OK] Connected to Minio")
        
        llama_client = LlamaStackClient(base_url=llamastack_url)
        print(f"[OK] Connected to LlamaStack")
        
        # Get embedding model from LlamaStack
        print(f"\n[INFO] Fetching available models...")
        models = llama_client.models.list()
        print(f"[OK] Found {len(models)} models")
        
        embedding_model = None
        for model in models:
            if model.model_type == "embedding":
                embedding_model = model
                break
        
        if embedding_model is None:
            raise ValueError("No embedding model found in LlamaStack!")
        
        embedding_model_id = embedding_model.identifier
        embedding_dimension = embedding_model.metadata.get("embedding_dimension", 768)
        print(f"[OK] Embedding model: {embedding_model_id} (dimension: {embedding_dimension})")
        
        # Step 2: Register/find vector database
        print(f"\n{'=' * 70}")
        print("STEP 2: SETUP VECTOR DATABASE")
        print("=" * 70)
        
        actual_vector_db_id = None
        
        try:
            # Check if vector DB already exists
            existing_dbs = llama_client.vector_dbs.list()
            for db in existing_dbs:
                if db.identifier == vector_db_id or getattr(db, 'vector_db_name', None) == vector_db_id:
                    actual_vector_db_id = db.identifier
                    print(f"[OK] Found existing vector DB: {vector_db_id}")
                    print(f"    Using identifier: {actual_vector_db_id}")
                    break
            
            if not actual_vector_db_id:
                # Register new vector DB
                print(f"[INFO] Registering new vector DB: {vector_db_id}")
                
                vector_db = llama_client.vector_dbs.register(
                    vector_db_id=vector_db_id,
                    embedding_model=embedding_model_id,
                    embedding_dimension=embedding_dimension,
                    provider_id="milvus-remote"
                )
                actual_vector_db_id = vector_db.identifier
                print(f"[OK] Registered vector DB: {actual_vector_db_id}")
        
        except Exception as e:
            print(f"[ERROR] Vector DB setup failed: {str(e)}", file=sys.stderr)
            raise
        
        print(f"\n[OK] Vector DB ready: {actual_vector_db_id}")
        print(f"    Embedding model: {embedding_model_id}")
        print(f"    Dimensions: {embedding_dimension}")
        
        # Step 3: Download Markdown files from Minio
        print(f"\n{'=' * 70}")
        print("STEP 3: DOWNLOAD MARKDOWN FILES")
        print("=" * 70)
        
        if not minio_client.bucket_exists(markdown_bucket):
            raise ValueError(f"Markdown bucket '{markdown_bucket}' does not exist!")
        
        objects = minio_client.list_objects(markdown_bucket, prefix=markdown_prefix, recursive=True)
        markdown_files = []
        
        for obj in objects:
            if not obj.object_name.lower().endswith('.md'):
                continue
            
            file_name = os.path.basename(obj.object_name)
            local_path = os.path.join(markdown_dir, file_name)
            
            print(f"\nDownloading: {obj.object_name}")
            print(f"  Size: {obj.size} bytes")
            
            minio_client.fget_object(markdown_bucket, obj.object_name, local_path)
            markdown_files.append({
                'path': local_path,
                'name': file_name,
                'object_name': obj.object_name
            })
            print(f"  [OK] Downloaded")
        
        if len(markdown_files) == 0:
            print("\n[WARNING] No markdown files found!")
            return
        
        print(f"\n[OK] Downloaded {len(markdown_files)} markdown files")
        
        # Step 4: Generate embeddings and store in Milvus
        print(f"\n{'=' * 70}")
        print("STEP 4: GENERATE EMBEDDINGS AND STORE")
        print("=" * 70)
        
        successful = 0
        failed = 0
        
        for idx, md_file in enumerate(markdown_files, 1):
            print(f"\n[{idx}/{len(markdown_files)}] Processing: {md_file['name']}")
            
            try:
                # Read markdown content
                with open(md_file['path'], 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if len(content) == 0:
                    print(f"  [SKIP] Empty file")
                    failed += 1
                    continue
                
                print(f"  Content: {len(content)} characters")
                
                # Create Document object
                document = Document(
                    document_id=md_file['name'],
                    content=content,
                    mime_type="text/markdown",
                    metadata={
                        "source": md_file['object_name'],
                        "bucket": markdown_bucket,
                        "filename": md_file['name']
                    }
                )
                
                # Generate embeddings and insert into Milvus via LlamaStack
                print(f"  Generating embeddings...")
                llama_client.tool_runtime.rag_tool.insert(
                    documents=[document],
                    vector_db_id=actual_vector_db_id,
                    chunk_size_in_tokens=chunk_size
                )
                
                print(f"  [OK] Successfully embedded and stored")
                successful += 1
                
            except Exception as e:
                print(f"  [ERROR] {str(e)}", file=sys.stderr)
                failed += 1
                continue
        
        print(f"\n{'=' * 70}")
        print("SUMMARY")
        print("=" * 70)
        print(f"Markdown files processed: {len(markdown_files)}")
        print(f"Successfully embedded: {successful}")
        print(f"Failed: {failed}")
        print(f"Vector DB: {actual_vector_db_id}")
        print(f"Embedding model: {embedding_model_id}")
        print(f"Chunk size: {chunk_size} tokens")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n[FATAL ERROR] {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise

