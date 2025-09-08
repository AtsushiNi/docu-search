# Elasticsearch インデックス再構築手順

## 概要
50音順ソート機能を実装するために、Elasticsearchのマッピングを更新する必要があります。既存のデータがある場合は、再インデックス処理が必要です。

## 手順

### 1. バックエンドコンテナに入る
```bash
docker-compose exec backend bash
```

### 2. 再インデックススクリプトを実行
```bash
cd /app
python -m app.scripts.reindex
```

### 3. スクリプトの動作内容
- 既存の`documents`インデックスをバックアップ
- 新しいマッピングで`documents_new`インデックスを作成
- データを再インデックス（sort_nameフィールドを自動生成）
- 古いインデックスを削除してからエイリアスを切り替え
- 一時インデックスをクリーンアップ

### 4. 確認方法
```bash
# 新しいマッピングが適用されているか確認
curl -X GET "http://elasticsearch:9200/documents/_mapping?pretty"

# 50音順でソートされているか確認
curl -X GET "http://elasticsearch:9200/documents/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "size": 10,
  "sort": [
    {
      "sort_name.sort": {
        "order": "asc"
      }
    }
  ],
  "_source": ["url", "sort_name"]
}'
```

## 注意事項
- 再インデックス中はサービスが一時的に利用できなくなります
- データ量によっては処理に時間がかかる場合があります
- 必ずバックアップを取ってから実行してください

## 新しいデータの場合
既存データがない場合（新規環境）は、自動的に新しいマッピングが適用されます。特別な操作は必要ありません。

## トラブルシューティング
### スクリプトが失敗した場合
1. Elasticsearchが正常に起動しているか確認
2. ICUプラグインがインストールされているか確認
3. 十分なディスク空き容量があるか確認

### よくあるエラーと解決策
#### `invalid_alias_name_exception` エラー
エラーメッセージ: `Invalid alias name [documents]: an index or data stream exists with the same name as the alias`

原因: 既に"documents"という名前のインデックスが存在する状態で、同じ名前のエイリアスを作成しようとしている

解決策:
1. 既存の`documents`インデックスを削除:
```bash
curl -X DELETE "http://elasticsearch:9200/documents?pretty"
```
2. 新しいインデックスにエイリアスを設定:
```bash
curl -X PUT "http://elasticsearch:9200/documents_new/_alias/documents?pretty"
```

### 手動での再インデックス
スクリプトが失敗した場合は、以下の手順で手動実行できます：

```bash
# 新しいインデックス作成
curl -X PUT "http://elasticsearch:9200/documents_new?pretty" -H 'Content-Type: application/json' -d'
{
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
}'
