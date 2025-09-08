import os
from typing import Optional
import redis
from rq import Queue
from rq.job import Job

from ..logging_config import setup_logging
logger = setup_logging()

# 利用可能なすべてのキューのリスト
ALL_QUEUES = [
    'default',
    'import_file',
    'convert_pdf', 
    'explore_folder',
    'upload_local'
]

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
        'app.services.svn_service.process_explore_task',
        folder_url,
        username,
        password,
        ip_address,
        job_timeout='1h'  # 1時間のタイムアウト（大規模フォルダ用）
    )
    
    logger.info(f"Enqueued SVN explore task for {folder_url}, job_id: {job.id}")
    return job

def enqueue_pdf_conversion_task(
    file_url: str,
    file_path: str
) -> Job:
    """
    PDF変換タスクをキューに追加
    
    Args:
        file_url: ファイルURL
        file_path: 一時ファイルのパス
    
    Returns:
        Job: キューに追加されたジョブ
    """
    # 循環インポートを避けるため、関数名を文字列で指定
    queue = get_queue('convert_pdf')
    job = queue.enqueue(
        'app.services.file_processor_service.process_pdf_conversion_task',
        file_url,
        file_path,
        job_timeout='30m'  # 30分のタイムアウト
    )
    
    logger.info(f"Enqueued PDF conversion task for {file_url}, job_id: {job.id}")
    return job

def enqueue_local_file_upload_task(
    absolute_path: str,
    file_data: bytes,
    file_name: str,
    job_id: str
) -> Job:
    """
    ローカルファイルアップロードタスクをキューに追加
    
    Args:
        absolute_path: 絶対パス（完全なファイルパス）
        file_data: ファイルデータ（バイト）
        file_name: ファイル名
        job_id: 親ジョブID（進捗追跡用）
    
    Returns:
        Job: キューに追加されたジョブ
    """
    # 循環インポートを避けるため、関数名を文字列で指定
    queue = get_queue('upload_local')
    job = queue.enqueue(
        'app.services.file_upload_service.process_local_file_upload',
        absolute_path,
        file_data,
        file_name,
        job_id,
        job_timeout='10m'  # 10分のタイムアウト
    )
    
    logger.info(f"Enqueued local file upload task for {file_name}, job_id: {job.id}")
    return job

def get_queue_stats() -> dict:
    """
    キューの統計情報を取得
    
    Returns:
        dict: キュー統計情報
    """
    redis_conn = get_redis_connection()
    
    stats = {}
    for queue_name in ALL_QUEUES:
        queue = Queue(queue_name, connection=redis_conn)
        stats[queue_name] = {
            'queued_jobs': queue.count,
            'started_jobs': queue.started_job_registry.count,
            'failed_jobs': queue.failed_job_registry.count,
            'successful_jobs': queue.finished_job_registry.count,
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
        queues_to_check = ALL_QUEUES
    
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
                # ジョブ結果がバイトデータの場合、Base64エンコードして返す
                result_value = None
                if job.result:
                    if isinstance(job.result, bytes):
                        import base64
                        result_value = base64.b64encode(job.result).decode('utf-8')
                    else:
                        result_value = str(job.result)
                
                jobs.append({
                    'id': job.id,
                    'queue': q_name,
                    'status': job.get_status(),
                    'created_at': job.created_at.isoformat() if job.created_at else None,
                    'started_at': job.started_at.isoformat() if job.started_at else None,
                    'ended_at': job.ended_at.isoformat() if job.ended_at else None,
                    'result': result_value,
                    'exc_info': job.exc_info,
                    'function': job.func_name,
                    'first_arg': job.args[0] if job.args and len(job.args) > 0 else None,
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
