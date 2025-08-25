from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import os

from .logging_config import setup_logging
from .elasticsearch_service import ESService
from .svn_service import (
    SVNExploreRequest,
    SVNImportRequest,
    explore_repo as svn_explore,
    import_resource as svn_import
)
from .queue_service import get_queue_stats, get_job_list

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
async def search(query: str, search_type: str = "exact"):
    """ドキュメント検索"""
    logger.info(f"Search request received - query: {query}, search_type: {search_type}")
    es_service = ESService()
    result = es_service.search_documents(query, search_type)
    return {"results": result["hits"]["hits"]}

@app.get("/svn/explore")
async def explore_repo(request: SVNExploreRequest = Depends()):
    """SVNリポジトリ探索エンドポイント"""
    return await svn_explore(request)

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
    return es_service.get_document_list()

@app.get("/files/{id}")
async def get_file_by_id(id: str):
    """指定されたIDのドキュメントを取得"""
    logger.info(f"File request received - id: {id}")
    es_service = ESService()
    result = es_service.get_document_by_id(id)
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
