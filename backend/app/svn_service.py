import os
import tempfile
import asyncio
from typing import List, Optional
from pydantic import BaseModel
import hashlib
import base64

from .logging_config import setup_logging
logger = setup_logging()
from .svn_client import (
    build_auth_args,
    get_file_info,
    list_svn_directory,
    download_svn_file
)
from .file_converter import FileConverter
from .elasticsearch_service import ESService

"""
SVNリポジトリ操作サービスモジュール
"""
class SVNExploreRequest(BaseModel):
    """SVNリポジトリ探索リクエストモデル"""
    repo_url: str
    file_types: str = "txt,pdf,docx,md,xlsx,xls"  # デフォルトでサポートするファイルタイプ
    username: Optional[str] = None
    password: Optional[str] = None
    ip_address: Optional[str] = None

class SVNImportRequest(BaseModel):
    """SVNrリソースインポートリクエストモデル"""
    url: str
    username: Optional[str] = None
    password: Optional[str] = None
    ip_address: Optional[str] = None

async def explore_repo(request: SVNExploreRequest):
    """SVNリポジトリを再帰的に探索し、指定タイプのファイルリストを返す"""
    allowed_types = request.file_types.split(",")  # 許可するファイルタイプをリスト化
    results = []  # 結果格納用リスト
    auth_args = build_auth_args(request.username, request.password)  # 認証引数作成

    def explore(path: str):
        """内部関数: 指定パス以下のディレクトリを再帰的に探索"""
        root = list_svn_directory(path, auth_args, request.ip_address)  # SVNディレクトリリスト取得
        for entry in root.findall(".//entry"):  # 各エントリを処理
            kind = entry.get("kind")  # エントリ種別 (file/dir)
            name = entry.find("name").text  # ファイル/ディレクトリ名
            # 完全なURLを構築
            url = f"{path}/{name}" if not path.endswith("/") else f"{path}{name}"
            
            if kind == "dir":
                explore(url)  # ディレクトリの場合は再帰的に探索
            else:
                ext = name.split(".")[-1].lower() if "." in name else ""  # 拡張子取得
                if ext in allowed_types:  # 許可されたタイプのみ処理
                    size = entry.find("size").text if entry.find("size") is not None else "0"
                    results.append({
                        "path": url,
                        "name": name,
                        "type": ext,
                        "size": int(size)  # ファイルサイズを整数に変換
                    })

    explore(request.repo_url)  # 探索開始
    return {"status": "success", "files": results}  # 結果を返す

async def import_resource(request: SVNImportRequest):
    """SVNファイルまたはフォルダをElasticSearchに取り込む"""
    auth_args = build_auth_args(request.username, request.password)  # 認証引数作成
    resource_info = get_file_info(request.url, auth_args, request.ip_address)  # ファイル情報取得
    
    if resource_info["is_folder"]:  # フォルダの場合
        return await _import_folder(request.url, auth_args, request.ip_address)
    return await _import_file(request.url, auth_args, request.ip_address)  # ファイルの場合

async def _convert_file(file_path: str) -> tuple:
    """ファイルを適切な形式に変換"""

    """古いOfficeファイルの場合、使用できる形式に変換"""
    if FileConverter.is_old_office_file(file_path):
        file_path = FileConverter.convert_to_valid_office_file(file_path)

    file_name = os.path.basename(file_path) # ファイル名(doc_id + 拡張子)
    pdf_name = None
    
    """PDFファイルを生成・保存"""
    if FileConverter.is_pdf_convertible(file_name):
        pdf_name = FileConverter.convert_to_pdf_and_save(file_path)
    
    """変換できる拡張子のバイナリファイルである合、マークダウン形式に変換"""
    if FileConverter.is_convertible(file_name):
        content = FileConverter.convert_to_markdown(file_path)
        return content, pdf_name
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(file_path, 'rb') as f:
            content = f.read().decode('utf-8', errors='replace')
    return content, pdf_name

async def _process_file(file_url: str, auth_args: List[str], ip_address: Optional[str] = None) -> bool:
    """内部関数: 単一ファイルを処理してElasticsearchに保存"""
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            doc_id = url_to_id(file_url) # URLからユニークなIDを生成

            """SVNからファイルをダウンロードして一時ディレクトリに保存"""
            file_name = file_url.split('/')[-1] # ファイル名(拡張子付き)
            file_ext = os.path.splitext(file_name)[1] # ファイル拡張子
            # ダウンロード先: {一時フォルダ}/{doc_id}.{拡張子}
            temp_file_path = os.path.join(temp_dir, f"{doc_id}{file_ext}")
            with open(temp_file_path, 'wb') as f:
                for chunk in download_svn_file(file_url, auth_args, ip_address):
                    f.write(chunk)

            """ファイルを適切な形式に変換"""
            file_content, pdf_name = await _convert_file(temp_file_path)

            """Elasticsearchにドキュメントを保存（同じURLの場合は更新）"""
            ESService().save_document(
                doc_id, # 主キー. file_urlから生成したハッシュ値.
                file_url,
                file_name,
                file_content,
                pdf_name=pdf_name
            )

            return True
        except Exception as e:
            logger.error(f"Failed to process file {file_url}: {str(e)}", exc_info=True)
            return False

async def _import_folder(folder_url: str, auth_args: List[str], ip_address: Optional[str] = None):
    """SVNフォルダをダウンロードし、Elasticsearchに保存する"""
    file_list = []
    
    # SVNのファイル一覧を取得
    def explore(path: str):
        root = list_svn_directory(path, auth_args, ip_address)
        for entry in root.findall(".//entry"):
            kind = entry.get("kind")
            name = entry.find("name").text
            url = f"{path}/{name}" if not path.endswith("/") else f"{path}{name}"
            
            if kind == "dir":
                explore(url)
            else:
                file_list.append(url)
    
    explore(folder_url)
    
    # 各ファイルを非同期で処理
    for file_url in file_list:
        asyncio.create_task(_process_file(file_url, auth_args, ip_address))
    
    return {"status": "success", "message": "Started background import process"}

async def _import_file(file_url: str, auth_args: List[str], ip_address: Optional[str] = None):
    """単一SVNファイルをダウンロードし、Elasticsearchに保存する"""
    success = await _process_file(file_url, auth_args, ip_address)
    
    if success:
        return {"status": "success", "message": f"Imported file {file_url} to Elasticsearch"}
    return {"status": "success", "message": f"Saved file {file_url} (no conversion needed)"}

def url_to_id(url: str) -> str:
    """リソースのURLからークなIDを生成"""
    # URLをUTF-8でバイト列に変換
    url_bytes = url.encode('utf-8')
    # SHA-256でハッシュ
    digest = hashlib.sha256(url_bytes).digest()
    # URL-safeなBase64に変換し、パディング(=)を除去
    return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip("=")
