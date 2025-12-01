from typing import Dict, Any
import tempfile
import os
import shutil

from ..logging_config import setup_logging
from .utils import url_to_id
from .file_processor_service import process_file

logger = setup_logging()

def process_local_file_upload(
    absolute_path: str,
    file_data: bytes,
    file_name: str,
    job_id: str
) -> Dict[str, Any]:
    """
    ローカルファイルアップロード処理
    
    Args:
        absolute_path: 絶対パス（完全なファイルパス）
        file_data: ファイルデータ（バイト）
        file_name: ファイル名
        job_id: 親ジョブID（進捗追跡用）
    
    Returns:
        dict: 処理結果
    """
    try:
        logger.info(f"Processing file upload: {file_name}, path: {absolute_path}, job_id: {job_id}")
        
        # 一時ファイルを作成
        temp_dir = tempfile.mkdtemp()

        # ファイル保存ディレクトリを作成
        file_storage_dir = "/var/lib/file_storage"
        os.makedirs(file_storage_dir, exist_ok=True)
        
        # ファイル名をパスのハッシュ化したものにする
        file_hash = url_to_id(absolute_path)
        file_ext = os.path.splitext(file_name)[1]
        hashed_file_name = f"{file_hash}{file_ext}"
        temp_file_path = os.path.join(temp_dir, hashed_file_name)
        stored_file_path = os.path.join(file_storage_dir, hashed_file_name)
        
        # ファイルを一時ディレクトリと保存ディレクトリに保存
        with open(stored_file_path, "wb") as f:
            f.write(file_data)
        logger.info(f"File saved to: {stored_file_path}")
        shutil.copy2(stored_file_path, temp_file_path)
        
        # ファイルプロセッササービスを使用してファイルを処理（ファイルパスを渡す）
        success = process_file(temp_file_path, absolute_path, stored_file_path)
        
        # 一時ファイルを削除
        os.remove(temp_file_path)
        try:
            os.rmdir(temp_dir)
        except OSError:
            pass  # ディレクトリが空でない場合は無視
        
        if success:
            logger.info(f"Successfully processed and saved file: {file_name}")
            return {
                "status": "success",
                "message": f"Processed and saved file {file_name}",
                "file_name": file_name,
                "absolute_path": absolute_path,
                "stored_file_path": stored_file_path
            }
        else:
            logger.error(f"Failed to process file: {file_name}")
            # 処理失敗時は保存したファイルも削除
            try:
                os.remove(stored_file_path)
            except OSError:
                pass
            return {
                "status": "error",
                "error": "File processing failed",
                "file_name": file_name,
                "absolute_path": absolute_path
            }
        
    except Exception as e:
        logger.error(f"Failed to process file upload {file_name}: {str(e)}", exc_info=True)
        # エラー時は保存したファイルを削除
        try:
            if 'stored_file_path' in locals():
                os.remove(stored_file_path)
        except (OSError, UnboundLocalError):
            pass
        return {
            "status": "error",
            "error": str(e),
            "file_name": file_name,
            "absolute_path": absolute_path
        }
