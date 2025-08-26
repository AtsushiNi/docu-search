import os
from typing import Optional
import redis
from rq import Queue
from rq.job import Job

from ..logging_config import setup_logging
logger = setup_logging()

# Redis接続設定
def get_redis_connection():
    """Redis接続を取得"""
    return redis.Redis(
        host=os.getenv('REDIS_HOST', 'redis'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=int(os.getenv('REDIS_DB', 0))
    )

def get_queue(name: str = 'default') -> Queue:
    """指定された名前のキューを取得"""
    redis_conn = get_redis_connection()
    return Queue(name, connection=redis_conn)

def enqueue_import_file_task(
    url: str, 
    username: Optional[str] = None, 
    password: Optional[str] = None, 
    ip_address: Optional[str] = None
) -> Job:
    """
    SVNインポートタスクをキューに追加
    
    Args:
        url: SVNリソースURL
        username: SVNユーザー名
        password: SVNパスワード
        ip_address: IPアドレス
    
    Returns:
        Job: キューに追加されたジョブ
    """
    # 循環インポートを避けるため、関数名を文字列で指定
    queue = get_queue('import_file')
    job = queue.enqueue(
        'app.services.svn_service.process_file_task',  # モジュールパスを文字列で指定
        url,
        username,
        password,
        ip_address,
        job_timeout='30m'  # 30分のタイムアウト
    )
    
    logger.info(f"Enqueued SVN import task for {url}, job_id: {job.id}")
    return job

def enqueue_svn_explore_task(
    folder_url: str, 
    username: Optional[str] = None, 
    password: Optional[str] = None, 
    ip_address: Optional[str] = None
) -> Job:
    """
    SVNフォルダ探索タスクをキューに追加
    
    Args:
        folder_url: SVNフォルダURL
        username: SVNユーザー名
        password: SVNパスワード
        ip_address: IPアドレス
    
    Returns:
        Job: キューに追加されたジョブ
    """
    # 循環インポートを避けるため、関数名を文字列で指定
    queue = get_queue('explore_folder')
    job = queue.enqueue(
        'app.services.svn_service.process_explore_task',  # モジュールパスを文字列で指定
        folder_url,
        username,
        password,
        ip_address,
        job_timeout='1h'  # 1時間のタイムアウト（大規模フォルダ用）
    )
    
    logger.info(f"Enqueued SVN explore task for {folder_url}, job_id: {job.id}")
    return job

def enqueue_file_conversion_task(
    file_path: str,
    conversion_type: Optional[str] = None,
    output_path: Optional[str] = None,
    sync: bool = False
):
    """
    ファイル変換タスクをキューに追加
    
    Args:
        file_path: 変換するファイルのパス
        conversion_type: 変換タイプ ('office', 'pdf', 'markdown', 'text', 'auto') - Noneの場合は自動判定
        output_path: 出力ファイルパス（オプション）
        sync: 同期実行モード（Trueの場合、即時実行して結果を返す）
    
    Returns:
        Job or dict: 非同期の場合はJobオブジェクト、同期の場合は変換結果
    """
    from .file_processor import FileProcessor  # 循環インポートを避けるため遅延インポート
    
    if sync:
        # 同期実行モード: 直接変換を実行して結果を返す
        return FileProcessor.process_file(file_path, conversion_type)
    else:
        # 非同期実行モード: キューに追加
        if conversion_type is None:
            # 自動判定
            conversion_type = FileProcessor.determine_conversion_type(file_path)
        
        queue = get_queue('file_conversion')
        job = queue.enqueue(
            _process_conversion_task,
            file_path,
            conversion_type,
            output_path,
            job_timeout='10m'  # 10分のタイムアウト
        )
        
        logger.info(f"Enqueued file conversion task for {file_path}, type: {conversion_type}, job_id: {job.id}")
        return job

def _process_conversion_task(
    file_path: str,
    conversion_type: str,
    output_path: Optional[str] = None
):
    """
    RQワーカー用: ファイル変換タスクを処理
    """
    from .file_processor import FileProcessor
    
    try:
        return FileProcessor.process_file(file_path, conversion_type)
    except Exception as e:
        logger.error(f"Failed to process conversion task for {file_path}: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e)}

def get_queue_stats() -> dict:
    """
    キューの統計情報を取得
    
    Returns:
        dict: キュー統計情報
    """
    redis_conn = get_redis_connection()
    queues = ['default', 'import_file', 'file_conversion', 'explore_folder']
    
    stats = {}
    for queue_name in queues:
        queue = Queue(queue_name, connection=redis_conn)
        stats[queue_name] = {
            'count': queue.count,
            'failed_jobs': queue.failed_job_registry.count,
            'scheduled_jobs': queue.scheduled_job_registry.count
        }
    
    return stats

def get_job_list(queue_name: Optional[str] = None, status: Optional[str] = None) -> list:
    """
    ジョブ一覧を取得
    
    Args:
        queue_name: キュー名（指定しない場合は全キュー）
        status: ジョブステータス（'queued', 'started', 'finished', 'failed', 'deferred', 'scheduled'）
    
    Returns:
        list: ジョブ情報のリスト
    """
    redis_conn = get_redis_connection()
    queues_to_check = []
    
    if queue_name:
        queues_to_check = [queue_name]
    else:
        queues_to_check = ['default', 'import_file', 'file_conversion', 'explore_folder']
    
    jobs = []
    
    for q_name in queues_to_check:
        queue = Queue(q_name, connection=redis_conn)
        
        # ステータスに基づいてジョブを取得
        if status:
            if status == 'queued':
                job_ids = queue.get_job_ids()
            elif status == 'started':
                job_ids = queue.started_job_registry.get_job_ids()
            elif status == 'finished':
                job_ids = queue.finished_job_registry.get_job_ids()
            elif status == 'failed':
                job_ids = queue.failed_job_registry.get_job_ids()
            elif status == 'deferred':
                job_ids = queue.deferred_job_registry.get_job_ids()
            elif status == 'scheduled':
                job_ids = queue.scheduled_job_registry.get_job_ids()
            else:
                continue
        else:
            # ステータス指定がない場合は全ジョブを取得
            job_ids = queue.get_job_ids() + \
                     queue.started_job_registry.get_job_ids() + \
                     queue.finished_job_registry.get_job_ids() + \
                     queue.failed_job_registry.get_job_ids() + \
                     queue.deferred_job_registry.get_job_ids() + \
                     queue.scheduled_job_registry.get_job_ids()
        
        # 重複を排除
        job_ids = list(set(job_ids))
        
        for job_id in job_ids:
            try:
                job = Job.fetch(job_id, connection=redis_conn)
                jobs.append({
                    'id': job.id,
                    'queue': q_name,
                    'status': job.get_status(),
                    'created_at': job.created_at.isoformat() if job.created_at else None,
                    'started_at': job.started_at.isoformat() if job.started_at else None,
                    'ended_at': job.ended_at.isoformat() if job.ended_at else None,
                    'result': str(job.result) if job.result else None,
                    'exc_info': job.exc_info,
                    'function': job.func_name,
                    'args': job.args,
                    'kwargs': job.kwargs
                })
            except Exception as e:
                logger.error(f"Failed to fetch job {job_id}: {str(e)}")
                # エラーが発生したジョブも情報として含める
                jobs.append({
                    'id': job_id,
                    'queue': q_name,
                    'status': 'unknown',
                    'error': str(e)
                })
    
    # 作成日時でソート（新しいものから）
    jobs.sort(key=lambda x: x.get('created_at') or '', reverse=True)
    
    return jobs
