from elasticsearch import Elasticsearch
from typing import Dict, Any
import os
import base64
from pydantic_settings import BaseSettings
from fastapi import HTTPException

class ElasticsearchSettings(BaseSettings):
    """Elasticsearch設定クラス"""
    es_host: str = "elasticsearch"
    es_port: str = "9200"
    verify_certs: bool = False

class ESService:
    """Elasticsearchサービスクラス"""
    def __init__(self):
        settings = ElasticsearchSettings()
        self.es = Elasticsearch(
            hosts=[f"http://{settings.es_host}:{settings.es_port}"],
            verify_certs=settings.verify_certs
        )
        self.index_name = "documents"

    def save_document(self, url: str, name: str, content: str) -> None:
        """ドキュメントを保存（同じURLの場合は更新）"""
        try:
            # URLをbase64エンコードしてドキュメントIDとして使用
            doc_id = base64.urlsafe_b64encode(url.encode('utf-8')).decode('utf-8')
            
            # 同じURLのドキュメントが存在するか確認
            if self.es.exists(index=self.index_name, id=doc_id):
                # 更新処理
                self.es.update(
                    index=self.index_name,
                    id=doc_id,
                    body={
                        "doc": {
                            "name": name,
                            "content": content,
                            "type": "md"
                        }
                    }
                )
            else:
                # 新規挿入処理
                self.es.index(
                    index=self.index_name,
                    id=doc_id,
                    body={
                        "url": url,
                        "name": name,
                        "content": content,
                        "type": "md"
                    }
                )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save to Elasticsearch: {str(e)}"
            )

    def search_documents(self, query: str) -> Dict[str, Any]:
        """ドキュメントを検索"""
        try:
            return self.es.search(
                index=self.index_name,
                body={
                    "query": {
                        "match": {
                            "content": query
                        }
                    }
                }
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Search failed: {str(e)}"
            )
