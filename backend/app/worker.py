#!/usr/bin/env python3
"""
RQワーカープロセス起動スクリプト
SVNインポートタスクを処理するワーカーを起動します
"""

import os
import logging
from rq import Worker
from rq.contrib.sentry import register_sentry

from .logging_config import setup_logging
from .queue_service import get_redis_connection

# ログ設定
logger = setup_logging()

def start_worker():
    """RQワーカーを起動"""
    try:
        # Redis接続を取得
        redis_conn = get_redis_connection()
        
        # 監視するキューを指定（svn_importキューを監視）
        queues = ['svn_import', 'default']
        
        # ワーカーを作成して起動
        worker = Worker(queues, connection=redis_conn)
        
        logger.info(f"Starting RQ worker for queues: {queues}")
        logger.info("Worker is ready to process jobs")
        
        # ワーカーを起動（ブロッキング呼び出し）
        worker.work()
        
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker failed to start: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    start_worker()
