import os
import subprocess
import tempfile
import zipfile
from io import BytesIO
from typing import List, Optional
from pydantic import BaseModel
from fastapi import HTTPException
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

class SVNImportRequest(BaseModel):
    """SVNrリソースインポートリクエストモデル"""
    url: str
    username: Optional[str] = None
    password: Optional[str] = None

def handle_unexpected_error(e: Exception, operation: str):
    """予期せぬエラーを処理してHTTPExceptionを発生させる"""
    error_msg = f"Unexpected error during {operation}: {str(e)}"
    raise HTTPException(status_code=500, detail=error_msg)

async def explore_repo(request: SVNExploreRequest):
    """SVNリポジトリを再帰的に探索し、指定タイプのファイルリストを返す"""
    try:
        allowed_types = request.file_types.split(",")  # 許可するファイルタイプをリスト化
        results = []  # 結果格納用リスト
        auth_args = build_auth_args(request.username, request.password)  # 認証引数作成

        def explore(path: str):
            """内部関数: 指定パス以下のディレクトリを再帰的に探索"""
            root = list_svn_directory(path, auth_args)  # SVNディレクトリリスト取得
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
    except subprocess.CalledProcessError as e:
        error_msg = f"SVN explore failed: {e.stderr.strip()}"
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        return handle_unexpected_error(e, "explore")

async def import_resource(request: SVNImportRequest):
    """SVNファイルまたはフォルダをElasticSearchに取り込む"""
    try:
        auth_args = build_auth_args(request.username, request.password)  # 認証引数作成
        resource_info = get_file_info(request.url, auth_args)  # ファイル情報取得
        
        if resource_info["is_folder"]:  # フォルダの場合
            return await _import_folder(request.url, auth_args)
        return await _import_file(request.url, auth_args, resource_info["file_name"])  # ファイルの場合
    except subprocess.CalledProcessError as e:
        error_msg = f"SVN import failed: {e.stderr.strip()}"
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        return handle_unexpected_error(e, "import")

async def _process_file(file_url: str, converter: FileConverter, auth_args: List[str]):
    """内部関数: 単一ファイルを処理してElasticsearchに保存"""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_name = file_url.split('/')[-1]  # パスからファイル名を抽出
        file_path = os.path.join(temp_dir, file_name)
        
        # ファイルをダウンロードして保存
        with open(file_path, 'wb') as f:
            for chunk in download_svn_file(file_url, auth_args):
                f.write(chunk)
        
        # ファイルを処理
        if converter.is_convertible(file_name):
            # MarkItDownでマークダウンに変換できる拡張子の場合は、マークダウン化してElasticSearchに保存
            md_content = converter.convert_to_markdown(file_path)
            ESService().save_document(file_url, file_name, md_content)
            return True
        else:
            # 変換不可の場合はファイルコンテンツをそのまま保存
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(file_path, 'rb') as f:
                    content = f.read().decode('utf-8', errors='replace')
            ESService().save_document(file_url, file_name, content)
            return True

    return False

async def _import_folder(folder_url: str, auth_args: List[str]):
    """SVNフォルダをダウンロードし、Elasticsearchに保存する"""
    converter = FileConverter()
    file_list = []
    
    def explore(path: str):
        root = list_svn_directory(path, auth_args)
        for entry in root.findall(".//entry"):
            kind = entry.get("kind")
            name = entry.find("name").text
            url = f"{path}/{name}" if not path.endswith("/") else f"{path}{name}"
            
            if kind == "dir":
                explore(url)
            else:
                file_list.append(url)
    
    explore(folder_url)
    
    processed_count = 0
    for file_url in file_list:
        if await _process_file(file_url, converter, auth_args):
            processed_count += 1
    
    return {"status": "success", "message": f"Imported {processed_count} files to Elasticsearch"}

async def _import_file(file_url: str, auth_args: List[str]):
    """単一SVNファイルをダウンロードし、Elasticsearchに保存する"""
    converter = FileConverter()
    success = await _process_file(file_url, converter, auth_args)
    
    if success:
        return {"status": "success", "message": f"Imported file {file_url} to Elasticsearch"}
    return {"status": "success", "message": f"Saved file {file_url} (no conversion needed)"}
