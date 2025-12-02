import pprint
from fastapi import FastAPI, Depends, HTTPException, Body, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import os
import uuid
from typing import List

from .logging_config import setup_logging
from .services.elasticsearch_service import ESService
from .services.svn_service import (
    import_resource as svn_import
)
from .services.queue_service import get_queue_stats, get_job_list, enqueue_local_file_upload_task
from .models.svn_models import SVNExploreRequest, SVNImportRequest

app = FastAPI()
logger = setup_logging()

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.error(
        f"HTTPException: {exc.status_code} - {exc.detail}",
        extra={"path": request.url.path, "method": request.method}
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(
        f"Unexpected error: {str(exc)}",
        exc_info=True,
        extra={"path": request.url.path, "method": request.method}
    )
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "status_code": 500}
    )

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # フロントエンドのURL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """ルートエンドポイント"""
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to FastAPI + Elasticsearch"}

@app.get("/search")
def search(query: str, search_type: str = "exact", url_query: str = None):
    """ドキュメント検索"""
    logger.info(f"Search request received - query: {query}, search_type: {search_type}, url_query: {url_query}")
    es_service = ESService()
    result = es_service.search_documents(query, search_type, url_query)
    return {"results": result["hits"]["hits"]}

@app.post("/svn/import")
async def import_svn_resource(request: SVNImportRequest = Body(...)):
    """
    SVNリポジトリからドキュメントをElasticSearchにインポート
    """
    return await svn_import(request)

@app.get("/files")
async def get_files():
    """登録されている全ドキュメントのURLとIDリストを取得"""
    logger.info("File list request received")
    es_service = ESService()
    return await es_service.get_document_list()

@app.delete("/files")
def delete_files(file_ids: List[str] = Body(..., embed=True)):
    """指定されたIDのファイルを削除
    
    Args:
        file_ids: 削除するファイルIDのリスト
    """
    logger.info(f"File delete request received - file_ids: {file_ids}")
    es_service = ESService()
    result = es_service.delete_documents(file_ids)
    
    if result["errors"]:
        logger.warning(f"Some files failed to delete: {result['errors']}")
        return JSONResponse(
            status_code=207,  # Multi-Status
            content={
                "message": f"Deleted {result['deleted']} files, {len(result['errors'])} failed",
                "deleted": result["deleted"],
                "errors": result["errors"]
            }
        )
    
    return {"message": f"Successfully deleted {result['deleted']} files", "deleted": result["deleted"]}

@app.get("/documents/{id}")
def get_document(id: str, include_content: bool = False):
    """指定されたIDのドキュメントを取得
    
    Args:
        id: ドキュメントID
        include_content: コンテンツを含めるかどうか（デフォルト: False）
    """
    logger.info(f"Document request received - id: {id}, include_content: {include_content}")
    es_service = ESService()
    result = es_service.get_document_by_id(id, include_content)
    if not result["found"]:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return result["_source"]

@app.get("/pdf/{filename}")
async def get_pdf(filename: str):
    """PDFファイルを取得"""
    file_path = f"/var/lib/pdf_storage/{filename}.pdf"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="application/pdf")

@app.get("/file/{filename}")
async def get_file(filename: str):
    """保存されたファイルを取得"""
    file_path = f"/var/lib/file_storage/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # ファイルのMIMEタイプを判定
    import mimetypes
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "application/octet-stream"
    
    # ファイル名を検索
    es_service = ESService()
    search_query = {
        "query": {
            "match_phrase": {
                "file_path": filename
            }
        }
    }
    
    try:
        result = es_service.es.search(index=es_service.index_name, body=search_query)
        original_filename = filename  # デフォルトはハッシュ化されたファイル名
        
        if result["hits"]["total"]["value"] > 0:
            doc = result["hits"]["hits"][0]["_source"]
            # nameプロパティを使用（元のファイル名が保存されている）
            original_filename = doc.get("name", filename)
        
        # ファイル名を安全な形式にエンコード
        import urllib.parse
        encoded_filename = urllib.parse.quote(original_filename)
        
        # Content-Dispositionヘッダーを明示的に設定
        headers = {
            "Content-Disposition": f"attachment; filename=\"{encoded_filename}\""
        }
        
        return FileResponse(
            path=file_path,
            media_type=mime_type,
            headers=headers
        )
    except Exception as e:
        logger.error(f"Failed to get original filename for {filename}: {str(e)}")
        # エラー時はFileResponseで返す
        return FileResponse(file_path, media_type=mime_type)

@app.get("/jobs/queue/stats")
async def get_queue_stats_endpoint():
    """
    キューの統計情報を取得
    
    Returns:
        dict: キュー統計情報
    """
    logger.info("Queue stats request received")
    return get_queue_stats()

@app.get("/jobs")
async def get_jobs_list_endpoint(queue_name: str = None, status: str = None):
    """
    RQジョブの一覧を取得
    
    Args:
        queue_name: キュー名（オプション）
        status: ジョブステータス（オプション、'queued', 'started', 'finished', 'failed', 'deferred', 'scheduled'）
    
    Returns:
        list: ジョブ情報のリスト
    """
    logger.info(f"Job list request received - queue_name: {queue_name}, status: {status}")
    jobs = get_job_list(queue_name, status)
    return jobs

@app.post("/upload/local-folder")
async def upload_local_folder(
    files: List[UploadFile] = File(...),
    absolute_paths: List[str] = Form(...),
    parent_job_id: str = Form(None)
):
    """
    ローカルフォルダからファイルをアップロード
    
    Args:
        files: アップロードするファイルリスト
        absolute_paths: 各ファイルの絶対パスリスト
        parent_job_id: 親ジョブID（進捗追跡用）
    
    Returns:
        dict: アップロード結果
    """
    logger.info(f"Local folder upload request received - files: {len(files)}, parent_job_id: {parent_job_id}")
    
    # バリデーション
    if len(files) != len(files) != len(absolute_paths):
        raise HTTPException(
            status_code=400,
            detail="Number of files and absolute paths must match"
        )
    
    # 親ジョブIDが指定されていない場合は生成
    if not parent_job_id:
        parent_job_id = str(uuid.uuid4())
    
    results = []
    total_files = len(files)
    
    for i, (file, absolute_path) in enumerate(zip(files, absolute_paths)):
        try:
            file_data = await file.read()
            # ファイルをキューに追加
            job = enqueue_local_file_upload_task(
                absolute_path=absolute_path,
                file_data=file_data,
                file_name=file.filename,
                job_id=parent_job_id
            )
            
            results.append({
                "success": True,
                "file_name": file.filename,
                "absolute_path": absolute_path,
                "job_id": job.id,
                "status": "queued"
            })
            
            logger.info(f"Queued file {i+1}/{total_files}: {file.filename}")
            
        except Exception as e:
            logger.error(f"Failed to process file {file.filename}: {str(e)}")
            results.append({
                "success": False,
                "file_name": file.filename,
                "absolute_path": absolute_path,
                "error": str(e)
            })
    
    return {
        "parent_job_id": parent_job_id,
        "total_files": total_files,
        "successful_uploads": sum(1 for r in results if r["success"]),
        "failed_uploads": sum(1 for r in results if not r["success"]),
        "results": results
    }
