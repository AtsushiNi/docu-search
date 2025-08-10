from elasticsearch import Elasticsearch
from typing import Dict, Any
from pydantic_settings import BaseSettings

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

    def save_document(self, doc_id: str, url: str, file_name: str, file_content: str,  
                    pdf_name: str = None) -> None:
        """ドキュメントを保存（同じURLの場合は更新）"""
        doc_body = {
            "url": url,
            "name": file_name,
            "content": file_content
        }
        
        # PDFメタデータがあれば追加
        if pdf_name:
            doc_body.update({
                "pdf_name": pdf_name
            })
        
        # 同じURLのドキュメントが存在するか確認
        if self.es.exists(index=self.index_name, id=doc_id):
            # 更新処理
            self.es.update(
                index=self.index_name,
                id=doc_id,
                body={"doc": doc_body}
            )
        else:
            # 新規挿入処理
            self.es.index(
                index=self.index_name,
                id=doc_id,
                body=doc_body
            )

    def search_documents(self, query: str) -> Dict[str, Any]:
        """ドキュメントを検索"""
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

    def get_url_list(self) -> Dict[str, Any]:
        """登録されている全ドキュメントのURLリストを取得"""
        return self.es.search(
            index=self.index_name,
            body={
                "_source": ["url"],
                "query": {
                    "match_all": {}
                },
                "size": 10000  # 十分大きな数を指定して全件取得
            }
        )
