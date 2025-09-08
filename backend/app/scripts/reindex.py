#!/usr/bin/env python3
"""
Elasticsearchインデックス再構築スクリプト
新しいマッピングを適用するために使用
"""

from elasticsearch import Elasticsearch
from typing import Dict, Any
import logging
import time

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReindexService:
    def __init__(self):
        self.es = Elasticsearch(
            hosts=["http://elasticsearch:9200"],
            verify_certs=False,
            timeout=60
        )
        self.old_index = "documents"
        self.new_index = "documents_new"
        self.temp_index = "documents_temp"
        
    def create_new_index(self):
        """新しいマッピングでインデックスを作成"""
        mapping = {
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
        
        if self.es.indices.exists(index=self.new_index):
            self.es.indices.delete(index=self.new_index)
            logger.info(f"Deleted existing index: {self.new_index}")
            
        self.es.indices.create(index=self.new_index, body=mapping)
        logger.info(f"Created new index: {self.new_index}")
        
    def reindex_data(self):
        """データを再インデックス"""
        # 再インデックス処理
        reindex_body = {
            "source": {
                "index": self.old_index
            },
            "dest": {
                "index": self.new_index
            },
            "script": {
                "source": """
                    // URLをそのままソート用フィールドとして使用（プロトコルを含むフルパス）
                    ctx._source.sort_name = ctx._source.url;
                """,
                "lang": "painless"
            }
        }
        
        try:
            result = self.es.reindex(body=reindex_body, wait_for_completion=False)
            task_id = result["task"]
            
            # タスクの完了を待機
            while True:
                task_status = self.es.tasks.get(task_id=task_id)
                if task_status["completed"]:
                    break
                logger.info("Reindex in progress...")
                time.sleep(5)
                
            logger.info("Reindex completed successfully")
            
        except Exception as e:
            logger.error(f"Reindex failed: {e}")
            raise
            
    def switch_aliases(self):
        """エイリアスを切り替えて新旧インデックスを入れ替え"""
        # まず古いインデックスを削除（エイリアス設定の前に削除が必要）
        if self.es.indices.exists(index=self.old_index):
            self.es.indices.delete(index=self.old_index)
            logger.info(f"Deleted old index: {self.old_index}")
            time.sleep(1)  # 削除が完了するのを少し待つ
        
        # 新しいインデックスに直接エイリアスを設定
        self.es.indices.put_alias(index=self.new_index, name="documents")
        logger.info(f"Alias 'documents' set for index: {self.new_index}")
        
    def cleanup(self):
        """一時インデックスのクリーンアップ"""
        # 一時インデックスが存在する場合は削除
        if self.es.indices.exists(index=self.temp_index):
            self.es.indices.delete(index=self.temp_index)
            logger.info(f"Deleted temp index: {self.temp_index}")
            
        logger.info("Cleanup completed")

def main():
    """メイン処理"""
    try:
        service = ReindexService()
        
        # 古いインデックスが存在するか確認
        if not service.es.indices.exists(index=service.old_index):
            logger.info("No existing index found. New mapping will be applied on next document save.")
            return
            
        logger.info("Starting reindex process...")
        service.create_new_index()
        service.reindex_data()
        service.switch_aliases()
        service.cleanup()
        logger.info("Reindex process completed successfully!")
        
    except Exception as e:
        logger.error(f"Reindex process failed: {e}")
        raise

if __name__ == "__main__":
    main()
