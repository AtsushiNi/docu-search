#!/usr/bin/env python3
"""
RQワーカープロセス起動スクリプト
"""

import sys
from rq import Worker

from ..logging_config import setup_logging
from ..services.queue_service import ALL_QUEUES, get_redis_connection

# ログ設定
logger = setup_logging()

def start_worker():
    """RQワーカーを起動"""
    try:
        # Redis接続を取得
        redis_conn = get_redis_connection()
        
        # ワーカーを作成して起動
        worker = Worker(ALL_QUEUES, connection=redis_conn)
        
        logger.info(f"Starting RQ worker for queues: {ALL_QUEUES}")
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
