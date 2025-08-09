from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from .logging_config import setup_logging
from .elasticsearch_service import ESService
from .svn_service import (
    SVNExploreRequest,
    SVNImportRequest,
    explore_repo as svn_explore,
    import_resource as svn_import
)

app = FastAPI()
logger = setup_logging()

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
async def search(query: str):
    """ドキュメント検索"""
    logger.info(f"Search request received - query: {query}")
    es_service = ESService()
    result = es_service.search_documents(query)
    return {"results": result["hits"]["hits"]}

@app.get("/svn/explore")
async def explore_repo(request: SVNExploreRequest = Depends()):
    """SVNリポジトリ探索エンドポイント"""
    return await svn_explore(request)

@app.get("/svn/import")
async def import_svn_resource(request: SVNImportRequest = Depends()):
    """SVNリソースをElasticSearchにインポートするエンドポイント"""
    return await svn_import(request)

@app.get("/files")
async def get_files():
    """登録されている全ドキュメントのURLリストを取得"""
    logger.info("URL list request received")
    es_service = ESService()
    result = es_service.get_url_list()
    return {"urls": [hit["_source"]["url"] for hit in result["hits"]["hits"]]}
