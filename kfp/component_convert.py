"""
Component 1: PDF to Markdown Conversion
Downloads PDFs from Minio, converts to Markdown, uploads to intermediate bucket.
Completely stateless - uses Minio buckets as coordination mechanism.
"""

from kfp import dsl


@dsl.component(
    base_image="quay.io/rsriniva/kfp-docling:latest"
)
def convert_pdfs_to_markdown(
    run_id: str = "v1"
):
    """
    Download all PDFs from Minio, convert to Markdown, upload to intermediate bucket.
    All configuration comes from environment variables (ConfigMap/Secrets).
    
    Args:
        run_id: Version identifier for cache busting
    """
    import os
    import sys
    from minio import Minio
    from minio.error import S3Error
    from docling.document_converter import DocumentConverter
    
    print("=" * 70)
    print("COMPONENT 1: PDF TO MARKDOWN CONVERSION")
    print("=" * 70)
    print(f"Run ID: {run_id}")
    
    # Get all configuration from environment variables (injected from ConfigMap/Secret)
    minio_endpoint = os.environ.get('MINIO_ENDPOINT')
    minio_access_key = os.environ.get('MINIO_ACCESS_KEY')
    minio_secret_key = os.environ.get('MINIO_SECRET_KEY')
    minio_secure = os.environ.get('MINIO_SECURE', 'false').lower() in ('true', '1', 'yes')
    
    input_bucket = os.environ.get('INPUT_DOCS_BUCKET')
    output_bucket = os.environ.get('MARKDOWN_DOCS_BUCKET')
    output_prefix = os.environ.get('MARKDOWN_DOCS_PREFIX', 'markdown/')
    
    print(f"\nConfiguration:")
    print(f"  Minio: {minio_endpoint} (secure={minio_secure})")
    print(f"  Input bucket: {input_bucket}")
    print(f"  Output bucket: {output_bucket}")
    print(f"  Output prefix: {output_prefix}")
    
    pdf_dir = "/tmp/pdfs"
    markdown_dir = "/tmp/markdown"
    os.makedirs(pdf_dir, exist_ok=True)
    os.makedirs(markdown_dir, exist_ok=True)
    
    try:
        # Connect to Minio
        client = Minio(
            minio_endpoint,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            secure=minio_secure
        )
        print(f"\n[OK] Connected to Minio")
        
        # Check buckets
        if not client.bucket_exists(input_bucket):
            raise ValueError(f"Input bucket '{input_bucket}' does not exist!")
        
        if not client.bucket_exists(output_bucket):
            print(f"[INFO] Creating output bucket '{output_bucket}'")
            client.make_bucket(output_bucket)
        
        print(f"[OK] Buckets verified")
        
        # Step 1: List and download all PDFs
        print(f"\n{'=' * 70}")
        print("STEP 1: DOWNLOAD PDFs")
        print("=" * 70)
        
        objects = client.list_objects(input_bucket, recursive=True)
        pdf_files = []
        
        for obj in objects:
            if not obj.object_name.lower().endswith('.pdf'):
                continue
            
            file_name = os.path.basename(obj.object_name)
            local_path = os.path.join(pdf_dir, file_name)
            
            print(f"\nDownloading: {obj.object_name}")
            print(f"  Size: {obj.size} bytes")
            
            client.fget_object(input_bucket, obj.object_name, local_path)
            pdf_files.append(local_path)
            print(f"  [OK] Downloaded")
        
        if len(pdf_files) == 0:
            print("\n[WARNING] No PDF files found!")
            return
        
        print(f"\n[OK] Downloaded {len(pdf_files)} PDF files")
        
        # Step 2: Convert PDFs to Markdown
        print(f"\n{'=' * 70}")
        print("STEP 2: CONVERT TO MARKDOWN")
        print("=" * 70)
        
        converter = DocumentConverter()
        successful = 0
        failed = 0
        
        for pdf_path in pdf_files:
            pdf_name = os.path.basename(pdf_path)
            markdown_name = os.path.splitext(pdf_name)[0] + ".md"
            markdown_path = os.path.join(markdown_dir, markdown_name)
            
            print(f"\nConverting: {pdf_name}")
            try:
                result = converter.convert(pdf_path)
                markdown_content = result.document.export_to_markdown()
                
                with open(markdown_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                
                size = os.path.getsize(markdown_path)
                print(f"  [OK] Converted ({size} bytes)")
                successful += 1
                
            except Exception as e:
                print(f"  [ERROR] {str(e)}", file=sys.stderr)
                failed += 1
                continue
        
        print(f"\n[OK] Converted {successful}/{len(pdf_files)} documents")
        if failed > 0:
            print(f"[WARNING] Failed: {failed}", file=sys.stderr)
        
        # Step 3: Upload Markdown files to Minio
        print(f"\n{'=' * 70}")
        print("STEP 3: UPLOAD TO MINIO")
        print("=" * 70)
        
        uploaded = 0
        for md_file in os.listdir(markdown_dir):
            if not md_file.endswith('.md'):
                continue
            
            local_path = os.path.join(markdown_dir, md_file)
            object_name = f"{output_prefix}{md_file}"
            
            print(f"\nUploading: {md_file}")
            try:
                client.fput_object(
                    output_bucket,
                    object_name,
                    local_path,
                    content_type='text/markdown'
                )
                print(f"  [OK] Uploaded to {object_name}")
                uploaded += 1
            except S3Error as e:
                print(f"  [ERROR] {str(e)}", file=sys.stderr)
                continue
        
        print(f"\n{'=' * 70}")
        print("SUMMARY")
        print("=" * 70)
        print(f"PDFs processed: {len(pdf_files)}")
        print(f"Successfully converted: {successful}")
        print(f"Failed conversions: {failed}")
        print(f"Uploaded to Minio: {uploaded}")
        print(f"Location: {output_bucket}/{output_prefix}")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n[FATAL ERROR] {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise

