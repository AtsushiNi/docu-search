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

class ESService:
    """Elasticsearchサービスクラス"""
    def __init__(self):
        settings = ElasticsearchSettings()
        self.es = Elasticsearch(
            hosts=[f"http://{settings.es_host}:{settings.es_port}"],
            verify_certs=settings.verify_certs
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
                            "pdf_name": { "type": "text" }
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
            "updated_at": datetime.datetime.now().astimezone().isoformat()
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

    def search_documents(self, query: str, search_type: str = "exact") -> Dict[str, Any]:
        """ドキュメントを検索"""
        if search_type == "fuzzy":
            # 曖昧検索
            search_body = {
                "query": {
                    "match": {
                        "content": {
                            "query": query,
                            "analyzer": "kuromoji_analyzer"
                        }
                    }
                }
            }
        else:
            # 単語検索
            search_body = {
                "query": {
                    "match_phrase": {
                        "content": {
                            "query": query,
                            "analyzer": "kuromoji_analyzer"
                        }
                    }
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
