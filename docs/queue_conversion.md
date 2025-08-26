# ファイル変換キューシステム

このドキュメントでは、ファイル変換機能をキューシステムで実行する方法について説明します。

## 概要

`convert_to_valid_office_file`, `convert_to_pdf_and_save`, `convert_to_markdown` 関数はすべてキューシステムで実行可能です。これにより、非同期処理によるパフォーマンス向上と、大量のファイル変換処理の効率化が実現できます。

## 対応変換タイプ

以下の変換タイプをサポートしています：

- `'office'` - 古いOfficeファイルを新しい形式に変換
- `'pdf'` - OfficeファイルをPDFに変換
- `'markdown'` - ファイルをマークダウンに変換
- `'text'` - ファイルをテキストとして読み込み
- `'auto'` - ファイルタイプに基づいて自動的に適切な変換を選択

## 使用方法

### 基本的な使用方法

```python
from app.queue_service import enqueue_file_conversion_task

# 同期実行（即時処理）
result = enqueue_file_conversion_task(
    file_path="/path/to/file.docx",
    conversion_type="markdown",
    sync=True
)

# 非同期実行（キュー経由）
job_id = enqueue_file_conversion_task(
    file_path="/path/to/file.docx", 
    conversion_type="markdown",
    sync=False
)
```

### パラメータ

- `file_path`: 変換するファイルのパス
- `conversion_type`: 変換タイプ（'office', 'pdf', 'markdown', 'text', 'auto'）
- `sync`: 同期実行か非同期実行か（デフォルト: False）
- `**kwargs`: その他のオプションパラメータ

### 戻り値

- 同期実行時: 変換結果の辞書
- 非同期実行時: RQジョブID

## 自動判定モード

`conversion_type='auto'` を指定すると、ファイルの拡張子に基づいて適切な変換を自動選択します：

- `.doc` → Office変換 → マークダウン変換
- `.docx`, `.xlsx`, `.pptx` → マークダウン変換
- テキストファイル → テキスト読み込み

## ワーカーの起動

非同期変換を処理するには、ワーカーを起動する必要があります：

```bash
# バックグラウンドワーカーの起動
cd backend
python -m app.worker
```

## テスト方法

### ローカル環境でのテスト

```bash
# Redisの起動
docker-compose up -d redis

# テストスクリプトの実行（同期変換のみ）
cd backend
python -m app.test_conversion_queue
```

### Docker環境での完全テスト

```bash
# 全サービスの起動
docker-compose up -d

# バックエンドコンテナ内でテスト実行
docker-compose exec backend python -m app.test_conversion_docker
```

## エラーハンドリング

変換処理は以下のエラーを適切に処理します：

- ファイルが見つからない場合
- サポートされていないファイル形式
- 変換サービス接続エラー
- 権限エラー

エラー時は `{'status': 'error', 'error': 'エラーメッセージ'}` 形式で返されます。

## パフォーマンス考慮事項

- 大量のファイル変換は非同期モードを使用推奨
- Office/PDF変換はリソースを多く消費するため、キューシステムによる制御が効果的
- ワーカー数を調整して並列処理を最適化可能

## 関連ファイル

- `backend/app/queue_service.py` - キューサービス実装
- `backend/app/file_converter.py` - ファイル変換関数
- `backend/app/worker.py` - RQワーカー
- `backend/app/test_conversion_*.py` - テストスクリプト
