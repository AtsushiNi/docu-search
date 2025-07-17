# DocuSearch

## 概要
このプロジェクトはFastAPI、React、Elasticsearchを使用した検索アプリケーションです。

## システム構成
- バックエンド: FastAPI
- フロントエンド: React (Ant Design)
- 検索エンジン: Elasticsearch
- コンテナ管理: Docker Compose

## 設計ドキュメント
- [API設計](design/api.md)
- [データベース設計](design/db.md)
- [UI設計](design/ui.md)

## セットアップ方法
```bash
docker-compose up --build
```

詳細なセットアップ手順は[setup.md](setup.md)を参照してください。

## アクセス方法
- フロントエンド: http://localhost:3000
- バックエンドAPI: http://localhost:8000
- Elasticsearch: http://localhost:9200
- Kibana: http://localhost:5601

## 開発ガイド
- 初期データ投入: `docker-compose exec backend python app/init_es.py`
- バックエンド再起動: `docker-compose restart backend`
- フロントエンド再ビルド: `docker-compose exec frontend npm run build`
