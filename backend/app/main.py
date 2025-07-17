from fastapi import FastAPI
from elasticsearch import Elasticsearch
import os

app = FastAPI()

# Elasticsearchクライアントの初期化
es = Elasticsearch(
    hosts=[os.getenv("ES_HOST", "elasticsearch")],
    verify_certs=False
)

@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI + Elasticsearch"}

@app.get("/search")
async def search(query: str):
    result = es.search(
        index="sample_index",
        body={
            "query": {
                "match": {
                    "content": query
                }
            }
        }
    )
    return {"results": result["hits"]["hits"]}
