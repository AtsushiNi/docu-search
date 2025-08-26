import os
import logging
from typing import Optional, Dict, Any
from .file_converter import FileConverter
from ..logging_config import setup_logging

logger = setup_logging()

class FileProcessor:
    """ファイル処理サービス - ファイル変換ロジックを一元化"""
    
    @staticmethod
    def process_file(file_path: str) -> Dict[str, Any]:
        """
        ファイルを処理（変換または読み込み）する
        
        Args:
            file_path: 処理するファイルのパス
        
        Returns:
            dict: 処理結果
        """
        try:
            file_name = os.path.basename(file_path)
            
            pdf_path = None
            
            # 古いOfficeファイルの変換
            if FileConverter.is_old_office_file(file_path):
                file_path = FileConverter.convert_to_valid_office_file(file_path)
                file_name = os.path.basename(file_path)  # ファイル名を更新
            
            # PDF変換
            if FileConverter.is_pdf_convertible(file_name):
                pdf_path = FileConverter.convert_to_pdf_and_save(file_path)
            
            # マークダウン変換
            if FileConverter.is_convertible(file_name):
                content = FileConverter.convert_to_markdown(file_path)
                return {
                    "status": "success", 
                    "content": content, 
                    "pdf_path": pdf_path,
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
                    "pdf_path": pdf_path,
                    "type": "text"
                }
            
        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {str(e)}", exc_info=True)
            return {"status": "error", "error": str(e)}
