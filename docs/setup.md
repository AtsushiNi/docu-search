# 環境構築手順

## 開発環境セットアップ

1. DockerとDocker Composeのインストール
2. プロジェクトルートで以下を実行:
```bash
docker-compose up --build
```

## 初期データ投入
```bash
docker-compose exec backend python app/init_es.py
```
