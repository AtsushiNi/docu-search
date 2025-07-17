# 環境構築手順

## 開発環境セットアップ

1. DockerとDocker Composeのインストール
2. プロジェクトルートで以下を実行:
```bash
docker-compose up --build
```

## 初期データ投入
```bash
# 基本コマンド
docker-compose exec backend python app/init_es.py

# SVNリポジトリからドキュメントを格納する場合
docker-compose exec backend python app/init_es.py --svn-url <SVN_URL> [--svn-url <SVN_URL2> ...]
```

## ドキュメント格納方法
1. SVNリポジトリ設定: 上記のコマンドでSVN URLを指定
2. ローカルフォルダ指定:
   - フロントエンド(http://localhost:3000)にアクセス
   - 「ドキュメント追加」メニューからローカルフォルダを選択
