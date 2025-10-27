import os
import re
from typing import Optional, Dict, Any, List

from ..logging_config import setup_logging
from .elasticsearch_service import ESService
from .file_converter import FileConverter
from .queue_service import enqueue_pdf_conversion_task
from .utils import url_to_id

logger = setup_logging()
"""
ファイル処理サービスモジュール
SVNに依存しないファイル操作機能を提供
"""

def process_file(
    file_path: str,
    file_url: str
) -> bool:
    """
    ファイル処理を実行してElasticsearchに保存
    
    Args:
        file_path: 処理するファイルのパス
        file_url: ファイルのURL（ドキュメントID生成用）
    
    Returns:
        bool: 処理成功可否
    """
    try:
        # ファイルを読み込み(必要ならマークダウン化)
        result = _read_file_content(file_path)
        
        if result["status"] != "success":
            logger.error(f"File processing failed for {file_url}: {result.get('error', 'Unknown error')}")
            return False
        
        # 結果から情報を抽出
        file_content = result.get("content", "")
        
        # セクション抽出
        print(file_content)
        sections = divide_toplevel_sections(file_content)
        
        # Elasticsearchにドキュメントを保存
        doc_id = url_to_id(file_url)
        file_name = file_url.split('/')[-1]
        
        ESService().save_document(
            doc_id,
            file_url,
            file_name,
            sections,
            pdf_name=None
        )
        
        # PDF変換が必要な場合は別キューで処理
        file_name = os.path.basename(file_path)
        if FileConverter.is_pdf_convertible(file_name):
            enqueue_pdf_conversion_task(
                file_url,
                file_path
            )
            logger.info(f"Enqueued PDF conversion for {file_url}")
        else:
            # 一時ファイルをクリーンアップ
            try:
                os.remove(file_path)
                temp_dir = os.path.dirname(file_path)
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
    PDF変換タスクを処理し、成功時にElasticsearchを更新
    
    Args:
        file_url: ファイルURL
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
        doc_id = url_to_id(file_url)
        existing_doc = es_service.get_document_by_id(doc_id, include_content=False)
        
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

def _read_file_content(file_path: str) -> Dict[str, Any]:
    """
    ファイルを読み込み内容を返す
    
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

def divide_toplevel_sections(content: str) -> List[Dict[str, str]]:
    """
    マークダウンまたはテキストコンテンツから一番レベルの高い見出しでセクションを抽出
    
    Args:
        content: 抽出元のコンテンツ
    
    Returns:
        List[Dict[str, str]]: セクションのリスト（各セクションはtitleとcontentを持つ）
    """
    if not content:
        return []
    
    # マークダウンの見出しパターン（#から######まで）
    heading_pattern = r'^(#{1,6})\s+(.+)$'
    lines = content.split('\n')
    
    sections = []
    current_title = None
    current_content = []
    highest_level = None
    
    for line in lines:
        # 見出しを検出
        heading_match = re.match(heading_pattern, line.strip())
        if heading_match:
            level = len(heading_match.group(1))  # #の数でレベルを決定
            title = heading_match.group(2).strip()
            
            # 最初の見出しまたは現在より高いレベルの見出しを検出した場合
            if highest_level is None or level <= highest_level:
                # 前のセクションがあれば保存
                if current_title is not None:
                    sections.append({
                        "title": current_title,
                        "content": '\n'.join(current_content).strip()
                    })
                
                # 新しいセクションを開始
                current_title = title
                current_content = []
                highest_level = level
            else:
                # 現在のセクションにコンテンツとして追加（サブ見出し）
                current_content.append(line)
        else:
            # 現在のセクションにコンテンツを追加
            if current_title is not None:
                current_content.append(line)
    
    # 最後のセクションを保存
    if current_title is not None:
        sections.append({
            "title": current_title,
            "content": '\n'.join(current_content).strip()
        })
    
    # 見出しが見つからなかった場合は全体を1つのセクションとして扱う
    if not sections and content.strip():
        sections.append({
            "title": "",  # タイトルなし
            "content": content.strip()
        })
    
    return sections
