from elasticsearch import Elasticsearch
from typing import Dict, Any
from pydantic_settings import BaseSettings
import datetime
import logging

class ElasticsearchSettings(BaseSettings):
    """Elasticsearch設定クラス"""
    es_host: str = "elasticsearch"
    es_port: str = "9200"
    verify_certs: bool = False
    timeout: int = 60  # リクエストタイムアウト（秒）

class ESService:
    """Elasticsearchサービスクラス"""
    def __init__(self):
        settings = ElasticsearchSettings()
        self.es = Elasticsearch(
            hosts=[f"http://{settings.es_host}:{settings.es_port}"],
            verify_certs=settings.verify_certs,
            timeout=settings.timeout,  # 接続タイムアウト（秒）
        )
        self.index_name = "documents"
        self._initialize_index()
        
    def _initialize_index(self):
        """インデックスを初期化（存在しない場合作成）"""
        if not self.es.indices.exists(index=self.index_name):
            try:
                self.es.indices.create(
                    index=self.index_name,
                    body={
                        "settings": {
                            "analysis": {
                                "tokenizer": {
                                    "kuromoji_tokenizer": {
                                        "type": "kuromoji_tokenizer"
                                    }
                                },
                                "char_filter": {
                                    "icu_normalizer": {
                                    "type": "icu_normalizer"
                                    }
                                },
                                "filter": {
                                    "ja_stop": {
                                    "type": "stop",
                                    "stopwords": "_japanese_"
                                    }
                                },
                                "analyzer": {
                                    "kuromoji_analyzer": {
                                        "type": "custom",
                                        "tokenizer": "kuromoji_tokenizer",
                                        "char_filter": ["icu_normalizer"],
                                        "filter": [
                                            "kuromoji_baseform",
                                            "kuromoji_part_of_speech",
                                            "ja_stop",
                                            "kuromoji_number",
                                            "kuromoji_stemmer"
                                        ]
                                    }
                                }
                            }
                        },
                        "mappings": {
                            "properties": {
                            "url": { "type": "keyword" },
                            "name": { "type": "text" },
                            "content": {
                                "type": "text",
                                "analyzer": "kuromoji_analyzer"
                            },
                            "updated_at": { "type": "date" },
                            "pdf_name": { "type": "text" },
                            "sort_name": {
                                "type": "text",
                                "fields": {
                                    "sort": {
                                        "type": "icu_collation_keyword",
                                        "language": "ja",
                                        "country": "JP"
                                    }
                                }
                            }
                            }
                        }
                    }
                )
                logging.info(f"Created index {self.index_name} with kuromoji analyzer")
            except Exception as e:
                logging.error(f"Failed to create index: {e}")
                raise

    def save_document(self, doc_id: str, url: str, file_name: str, file_content: str,  
                    pdf_name: str = None) -> None:
        """ドキュメントを保存（同じURLの場合は更新）"""
        doc_body = {
            "url": url,
            "name": file_name,
            "content": file_content,
            "updated_at": datetime.datetime.now().astimezone().isoformat(),
            "sort_name": url
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

    def search_documents(self, query: str, search_type: str = "exact", url_query: str = None) -> Dict[str, Any]:
        """ドキュメントを検索"""
        # ベースとなるクエリ条件
        must_conditions = []
        
        # コンテンツ検索条件
        if query:
            if search_type == "fuzzy":
                # 曖昧検索
                must_conditions.append({
                    "match": {
                        "content": {
                            "query": query,
                            "analyzer": "kuromoji_analyzer"
                        }
                    }
                })
            else:
                # 単語検索
                must_conditions.append({
                    "match_phrase": {
                        "content": {
                            "query": query,
                            "analyzer": "kuromoji_analyzer"
                        }
                    }
                })
        
        # URL検索条件
        if url_query:
            must_conditions.append({
                "wildcard": {
                    "url": {
                        "value": f"*{url_query}*"
                    }
                }
            })
        
        # 検索クエリの構築
        if must_conditions:
            search_body = {
                "query": {
                    "bool": {
                        "must": must_conditions
                    }
                }
            }
        else:
            # 検索条件がない場合は全件取得
            search_body = {
                "query": {
                    "match_all": {}
                }
            }
        
        # ハイライト設定を追加
        search_body["highlight"] = {
            "fields": {
                "content": {
                    "pre_tags": ["<mark>"],
                    "post_tags": ["</mark>"],
                    "number_of_fragments": 100
                }
            }
        }
        
        return self.es.search(
            index=self.index_name,
            body=search_body
        )

    def get_document_list(self) -> Dict[str, Any]:
        """登録されている全ドキュメントのURLとIDリストを取得"""
        result = self.es.search(
            index=self.index_name,
            body={
                "_source": ["url"],
                "query": {
                    "match_all": {}
                },
                "sort": [
                    {
                        "sort_name.sort": {
                            "order": "asc"
                        }
                    }
                ],
                "size": 10000  # 十分大きな数を指定して全件取得
            }
        )
        return {
            "files": [
                {"url": hit["_source"]["url"], "id": hit["_id"]} 
                for hit in result["hits"]["hits"]
            ]
        }

    def get_document_by_id(self, doc_id: str, include_content: bool = False) -> Dict[str, Any]:
        """指定されたIDのドキュメントを取得
        
        Args:
            doc_id: ドキュメントID
            include_content: コンテンツを含めるかどうか
        """
        source_fields = ["url", "name", "updated_at", "pdf_name"]
        if include_content:
            source_fields.append("content")
            
        try:
            return self.es.get(
                index=self.index_name,
                id=doc_id,
                _source=source_fields
            )
        except Exception:
            return None

    def update_document_pdf_info(self, doc_id: str, pdf_name: str) -> None:
        """ドキュメントのPDF情報を更新"""
        update_body = {
            "doc": {
                "pdf_name": pdf_name,
                "updated_at": datetime.datetime.now().astimezone().isoformat()
            }
        }
        
        self.es.update(
            index=self.index_name,
            id=doc_id,
            body=update_body
        )
        logging.info(f"Updated PDF info for document {doc_id}: {pdf_name}")

    def delete_documents(self, doc_ids: list) -> Dict[str, Any]:
        """指定されたIDのドキュメントを削除
        
        Args:
            doc_ids: 削除するドキュメントIDのリスト
            
        Returns:
            dict: 削除結果
        """
        if not doc_ids:
            return {"deleted": 0, "errors": []}
        
        try:
            # バルク削除リクエストを作成
            operations = []
            for doc_id in doc_ids:
                operations.append({"delete": {"_index": self.index_name, "_id": doc_id}})
            
            # バルク削除を実行
            response = self.es.bulk(operations=operations)
            
            # 結果を集計
            deleted_count = 0
            errors = []
            
            for item in response.get('items', []):
                if 'delete' in item:
                    delete_result = item['delete']
                    if delete_result.get('status') == 200:
                        deleted_count += 1
                    else:
                        errors.append({
                            'id': delete_result.get('_id'),
                            'error': delete_result.get('error', {}).get('reason', 'Unknown error')
                        })
            
            logging.info(f"Deleted {deleted_count} documents, errors: {len(errors)}")
            return {
                "deleted": deleted_count,
                "errors": errors
            }
            
        except Exception as e:
            logging.error(f"Failed to delete documents: {e}")
            raise
