# DocuSearch

## 概要
このプロジェクトはFastAPI、React、Elasticsearchを使用した検索アプリケーションです。

以下の方法でドキュメントをElasticsearchに格納できます:
1. SVNリポジトリ設定: 複数のSVN URLを設定することで、指定したリポジトリ内のドキュメントを自動的に収集・格納
2. ローカルフォルダ指定: Webインターフェースからローカルフォルダを指定し、その中のドキュメントを格納

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

### ドキュメント格納方法
1. SVNリポジトリ設定:
   ```bash
   docker-compose exec backend python app/init_es.py --svn-url <SVN_URL> [--svn-url <SVN_URL2> ...]
   ```
2. ローカルフォルダ指定:
   - フロントエンド(http://localhost:3000)にアクセス
   - 「ドキュメント追加」メニューからローカルフォルダを選択
