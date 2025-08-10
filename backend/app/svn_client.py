import os
import subprocess
from typing import List, Optional
from xml.etree import ElementTree

def build_auth_args(username: Optional[str], password: Optional[str]) -> List[str]:
    """SVN認証引数を構築"""
    auth_args = []
    if username:
        auth_args.extend(["--username", username])
    if password:
        auth_args.extend(["--password", password])
    return auth_args

def get_file_info(file_url: str, auth_args: List[str]):
    """ファイル情報を取得"""
    info_result = _run_svn_command(["info", "--xml", file_url], auth_args)
    entry = ElementTree.fromstring(info_result.stdout).find(".//entry")
    return {
        "is_folder": entry.get("kind") == "dir",
        "file_name": entry.find("name").text if entry.find("name") is not None 
                  else os.path.basename(file_url.rstrip('/'))
    }

def list_svn_directory(path: str, auth_args: List[str]):
    """SVNディレクトリをリスト"""
    result = _run_svn_command(["list", "--xml", path], auth_args)
    return ElementTree.fromstring(result.stdout)

def download_svn_file(file_url: str, auth_args: List[str]):
    """SVNファイルをダウンロード (1MBチャンクで処理)"""
    CHUNK_SIZE = 1024 * 1024  # 1MB固定
    process = subprocess.Popen(
        ["svn", "cat", file_url] + auth_args,
        stdout=subprocess.PIPE,
        text=False
    )
    try:
        while chunk := process.stdout.read(CHUNK_SIZE):
            yield chunk
    finally:
        process.stdout.close()
        process.wait()

def _run_svn_command(cmd: List[str], auth_args: List[str]) -> subprocess.CompletedProcess:
    """SVNコマンドを実行 (プライベートメソッド)"""
    full_cmd = ["svn"] + cmd + auth_args
    return subprocess.run(
        full_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True
    )
