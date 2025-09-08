from typing import Dict, Any
import tempfile
import os

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
        file_hash = url_to_id(absolute_path)
        file_ext = os.path.splitext(file_name)[1]
        temp_file_path = os.path.join(temp_dir, f"{file_hash}{file_ext}")
        
        # ファイルデータを一時ファイルに書き込み
        with open(temp_file_path, "wb") as f:
            f.write(file_data)
        
        # ファイルプロセッササービスを使用してファイルを処理
        success = process_file(temp_file_path, absolute_path)
        
        # 一時ファイルを削除
        os.remove(temp_file_path)
        
        if success:
            logger.info(f"Successfully processed file: {file_name}")
            return {
                "status": "success",
                "message": f"Processed file {file_name}",
                "file_name": file_name,
                "absolute_path": absolute_path
            }
        else:
            logger.error(f"Failed to process file: {file_name}")
            return {
                "status": "error",
                "error": "File processing failed",
                "file_name": file_name,
                "absolute_path": absolute_path
            }
        
    except Exception as e:
        logger.error(f"Failed to process file upload {file_name}: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "file_name": file_name,
            "absolute_path": absolute_path
        }
