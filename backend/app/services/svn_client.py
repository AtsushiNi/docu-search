import os
import subprocess
from typing import List, Optional
from xml.etree import ElementTree
from urllib.parse import urlparse, urlunparse

def build_auth_args(username: Optional[str], password: Optional[str]) -> List[str]:
    """SVN認証引数を構築"""
    auth_args = []
    if username:
        auth_args.extend(["--username", username])
    if password:
        auth_args.extend(["--password", password])
    return auth_args

def get_file_info(file_url: str, auth_args: List[str], ip_address: Optional[str] = None):
    """ファイル情報を取得"""
    # IPアドレスが渡された場合、ドメインの代わりにIPアドレスを用いてSVNにアクセスする
    target_url = _rewrite_svn_url(file_url, ip_address)

    info_result = _run_svn_command(["info", "--xml", target_url], auth_args)
    entry = ElementTree.fromstring(info_result.stdout).find(".//entry")
    return {
        "is_folder": entry.get("kind") == "dir",
        "file_name": entry.find("name").text if entry.find("name") is not None 
                  else os.path.basename(file_url.rstrip('/'))
    }

def list_svn_directory(path: str, auth_args: List[str], ip_address: Optional[str] = None):
    """SVNディレクトリをリスト"""
    # IPアドレスが渡された場合、ドメインの代わりにIPアドレスを用いてSVNにアクセスする
    target_path = _rewrite_svn_url(path, ip_address)

    result = _run_svn_command(["list", "--xml", target_path], auth_args)
    return ElementTree.fromstring(result.stdout)

def download_svn_file(file_url: str, auth_args: List[str], ip_address: Optional[str] = None):
    """SVNファイルをダウンロード (1MBチャンクで処理)"""
    # IPアドレスが渡された場合、ドメインの代わりにIPアドレスを用いてSVNにアクセスする
    target_url = _rewrite_svn_url(file_url, ip_address)

    CHUNK_SIZE = 1024 * 1024  # 1MB固定
    process = subprocess.Popen(
        ["svn", "cat", target_url] + auth_args,
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

def _rewrite_svn_url(url: str, ip_address: Optional[str]) -> str:
    """ドメイン名をIPアドレスで書き換えたSVN URLを返す"""
    if not ip_address:
        return url
    
    parsed_url = urlparse(url)
    # ホスト部分をIPアドレスで置き換え
    new_netloc = ip_address
    if parsed_url.port:
        new_netloc = f"{ip_address}:{parsed_url.port}"
    elif parsed_url.scheme == 'https':
        new_netloc = f"{ip_address}:443"
    elif parsed_url.scheme == 'http':
        new_netloc = f"{ip_address}:80"
    
    return urlunparse((
        parsed_url.scheme,
        new_netloc,
        parsed_url.path,
        parsed_url.params,
        parsed_url.query,
        parsed_url.fragment
    ))
