from elasticsearch import Elasticsearch
import os

es = Elasticsearch(
    hosts=[f"http://{os.getenv('ES_HOST', 'elasticsearch')}:9200"],
    verify_certs=False
)

# サンプルインデックス作成
index_name = "sample_index"

if not es.indices.exists(index=index_name):
    es.indices.create(index=index_name)

# サンプルデータ投入
sample_data = [
    {"content": "FastAPIとReactを使ったWebアプリケーション"},
    {"content": "Elasticsearchを使った全文検索システム"},
    {"content": "Docker Composeを使ったマルチコンテナアプリケーション"},
]

for i, doc in enumerate(sample_data):
    es.index(index=index_name, id=i+1, document=doc)

print("初期データの投入が完了しました")
