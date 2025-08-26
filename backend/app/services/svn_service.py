import os
import tempfile
from typing import Optional, Dict, Any
import hashlib
import base64

from ..logging_config import setup_logging
from .svn_client import (
    build_auth_args,
    get_file_info,
    list_svn_directory,
    download_svn_file
)
from .elasticsearch_service import ESService
from .file_converter import FileConverter
from .queue_service import enqueue_import_file_task, enqueue_svn_explore_task, enqueue_pdf_conversion_task
from ..models.svn_models import SVNImportRequest

logger = setup_logging()
"""
SVNリポジトリ操作サービスモジュール
"""

async def import_resource(request: SVNImportRequest):
    """SVNファイルまたはフォルダをElasticSearchに取り込む"""
    auth_args = build_auth_args(request.username, request.password)  # 認証引数作成
    resource_info = get_file_info(request.url, auth_args, request.ip_address)  # ファイル情報取得
    
    if resource_info["is_folder"]:  # フォルダの場合
        # フォルダ探索タスクをキューに追加
        job = enqueue_svn_explore_task(
            request.url, 
            request.username, 
            request.password, 
            request.ip_address
        )
        
        return {
            "status": "success", 
            "message": f"Enqueued folder exploration task for {request.url}",
            "job_id": job.id
        }
    else:
        # 単一ファイルをキューに追加
        job = enqueue_import_file_task(
            request.url, 
            request.username, 
            request.password, 
            request.ip_address
        )
        
        return {
            "status": "success", 
            "message": f"Enqueued file {request.url} for import",
            "job_id": job.id
        }


def _process_file(file_path: str) -> Dict[str, Any]:
    """
    ファイルを処理（変換または読み込み）する
    
    Args:
        file_path: 処理するファイルのパス
    
    Returns:
        dict: 処理結果
    """
    try:
        file_name = os.path.basename(file_path)
        
        # 古いOfficeファイルの変換
        if FileConverter.is_old_office_file(file_path):
            file_path = FileConverter.convert_to_valid_office_file(file_path)
            file_name = os.path.basename(file_path)  # ファイル名を更新
        
        # マークダウン変換
        if FileConverter.is_convertible(file_name):
            content = FileConverter.convert_to_markdown(file_path)
            return {
                "status": "success", 
                "content": content, 
                "pdf_path": None,
                "type": "auto"
            }
        else:
            # テキストファイルの読み込み
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(file_path, 'rb') as f:
                    content = f.read().decode('utf-8', errors='replace')
            
            return {
                "status": "success", 
                "content": content, 
                "pdf_path": None,
                "type": "text"
            }
        
    except Exception as e:
        logger.error(f"Failed to process file {file_path}: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e)}

def process_file_task(
    file_url: str, 
    username: Optional[str] = None, 
    password: Optional[str] = None, 
    ip_address: Optional[str] = None
) -> bool:
    """RQワーカー用: 単一ファイルを処理してElasticsearchに保存"""
    try:
        # SVNファイルをダウンロード
        temp_file_path = _download_svn_file_to_temp(file_url, username, password, ip_address)
        
        # ファイルを処理（変換とコンテンツ抽出）
        result = _process_file(temp_file_path)
        
        if result["status"] != "success":
            logger.error(f"File processing failed for {file_url}: {result.get('error', 'Unknown error')}")
            return False
        
        # 結果から情報を抽出
        file_content = result.get("content", "")
        
        # Elasticsearchにドキュメントを保存
        doc_id = _url_to_id(file_url)
        file_name = file_url.split('/')[-1]
        
        ESService().save_document(
            doc_id,
            file_url,
            file_name,
            file_content,
            pdf_name=None
        )
        
        # PDF変換が必要な場合は別キューで処理
        file_name = os.path.basename(temp_file_path)
        if FileConverter.is_pdf_convertible(file_name):
            enqueue_pdf_conversion_task(
                file_url,
                temp_file_path
            )
            logger.info(f"Enqueued PDF conversion for {file_url}")
        else:
            # 一時ファイルをクリーンアップ
            try:
                os.remove(temp_file_path)
                temp_dir = os.path.dirname(temp_file_path)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except OSError:
                pass  # クリーンアップ失敗は無視
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to process file {file_url}: {str(e)}", exc_info=True)
        return False

def process_pdf_conversion_task(
    file_url: str,
    file_path: str
) -> bool:
    """
    RQワーカー用: PDF変換タスクを処理し、成功時にElasticsearchを更新
    
    Args:
        file_url: SVNファイルURL
        file_path: 一時ファイルパス
    
    Returns:
        bool: 処理成功可否
    """
    try:
        logger.info(f"Starting PDF conversion for {file_url}")
        
        # PDF変換を実行
        pdf_path = FileConverter.convert_to_pdf_and_save(file_path)
        
        if not pdf_path or not os.path.exists(pdf_path):
            logger.error(f"PDF conversion failed for {file_url}")
            return False
        
        # PDFファイル名を取得
        pdf_name = os.path.basename(pdf_path)
        
        # 既存のドキュメントを取得してPDF情報を更新
        es_service = ESService()
        doc_id = _url_to_id(file_url)
        existing_doc = es_service.get_document(doc_id)
        
        if existing_doc:
            # 既存ドキュメントを更新
            es_service.update_document_pdf_info(doc_id, pdf_name)
            logger.info(f"Updated PDF info for document {file_url}: {pdf_name}")
        
        # 一時ファイルをクリーンアップ
        try:
            os.remove(file_path)
            temp_dir = os.path.dirname(file_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except OSError as e:
            logger.warning(f"Failed to clean up temporary files: {str(e)}")
        
        logger.info(f"PDF conversion completed successfully for {file_url}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to process PDF conversion for {file_url}: {str(e)}", exc_info=True)
        return False

def process_explore_task(
    folder_url: str, 
    username: Optional[str] = None, 
    password: Optional[str] = None, 
    ip_address: Optional[str] = None
) -> dict:
    """
    RQワーカー用: SVNフォルダ探索タスクを処理
    
    Args:
        folder_url: 探索するSVNフォルダURL
        username: SVNユーザー名
        password: SVNパスワード
        ip_address: IPアドレス
    
    Returns:
        dict: 処理結果
    """
    try:
        auth_args = build_auth_args(username, password)
        
        # SVNディレクトリの内容を取得
        root = list_svn_directory(folder_url, auth_args, ip_address)
        
        processed_count = 0
        enqueued_count = 0
        
        for entry in root.findall(".//entry"):
            kind = entry.get("kind")
            name = entry.find("name").text
            url = f"{folder_url}/{name}" if not folder_url.endswith("/") else f"{folder_url}{name}"
            
            if kind == "dir":
                # サブフォルダの場合、さらに探索タスクをキューに追加
                enqueue_svn_explore_task(url, username, password, ip_address)
                enqueued_count += 1
                logger.info(f"Enqueued subfolder exploration: {url}")
            else:
                # ファイルの場合、インポートタスクをキューに追加
                enqueue_import_file_task(url, username, password, ip_address)
                processed_count += 1
                logger.info(f"Enqueued file import: {url}")
        
        return {
            "status": "success",
            "message": f"Processed {processed_count} files and enqueued {enqueued_count} subfolders",
            "processed_files": processed_count,
            "enqueued_folders": enqueued_count,
            "folder_url": folder_url
        }
        
    except Exception as e:
        logger.error(f"Failed to process explore task for {folder_url}: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "folder_url": folder_url
        }

def _download_svn_file_to_temp(
    file_url: str, 
    username: Optional[str] = None, 
    password: Optional[str] = None, 
    ip_address: Optional[str] = None
) -> str:
    """
    SVNファイルを一時ディレクトリにダウンロード
    
    Args:
        file_url: SVNファイルURL
        username: SVNユーザー名
        password: SVNパスワード
        ip_address: IPアドレス
    
    Returns:
        str: ダウンロードされたファイルのパス
    """
    auth_args = build_auth_args(username, password)
    
    # 一時ディレクトリを作成
    temp_dir = tempfile.mkdtemp()
    doc_id = _url_to_id(file_url)
    file_name = file_url.split('/')[-1]
    file_ext = os.path.splitext(file_name)[1]
    temp_file_path = os.path.join(temp_dir, f"{doc_id}{file_ext}")
    
    # ファイルをダウンロード
    with open(temp_file_path, 'wb') as f:
        for chunk in download_svn_file(file_url, auth_args, ip_address):
            f.write(chunk)
    
    return temp_file_path

def _url_to_id(url: str) -> str:
    """リソースのURLからークなIDを生成"""
    # URLをUTF-8でバイト列に変換
    url_bytes = url.encode('utf-8')
    # SHA-256でハッシュ
    digest = hashlib.sha256(url_bytes).digest()
    # URL-safeなBase64に変換し、パディング(=)を除去
    return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip("=")
