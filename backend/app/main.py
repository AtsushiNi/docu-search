from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from elasticsearch import Elasticsearch
import os
import sys
import logging
import subprocess
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    class Config:
        env_file = ".env"

settings = Settings()

# ロギング設定
logging.basicConfig(
    level=settings.log_level,
    format=settings.log_format,
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

app = FastAPI()

# Elasticsearchクライアントの初期化
es = Elasticsearch(
    hosts=[f"http://{os.getenv('ES_HOST', 'elasticsearch')}:9200"],
    verify_certs=False
)

@app.get("/")
def root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to FastAPI + Elasticsearch"}

@app.get("/search")
async def search(query: str):
    logger.info(f"Search request received - query: {query}")
    result = es.search(
        index="sample_index",
        body={
            "query": {
                "match": {
                    "content": query
                }
            }
        }
    )
    return {"results": result["hits"]["hits"]}

@app.post("/svn/auth")
async def svn_auth(
    repo_url: str,
    username: str = None,
    password: str = None,
    ssh_key: str = None
):
    """SVNリポジトリ認証処理"""
    logger.info(f"SVN auth request - repo: {repo_url}, user: {username}")
    try:
        # 認証情報の設定
        auth_args = []
        if username and password:
            auth_args.extend(["--username", username, "--password", password])
        elif ssh_key:
            auth_args.extend(["--username", username, "--ssh-private-key", ssh_key])
        
        # 接続テスト
        result = subprocess.run(
            ["svn", "info", repo_url] + auth_args,
            capture_output=True,
            text=True,
            check=True
        )
        return {"status": "success", "message": "認証に成功しました"}
    except subprocess.CalledProcessError as e:
        logger.error(f"SVN authentication failed - repo: {repo_url}, error: {e.stderr}")
        return {"status": "error", "message": f"SVN認証エラー: {e.stderr}"}
    except Exception as e:
        logger.error(f"Unexpected error in SVN auth - repo: {repo_url}, error: {str(e)}", exc_info=True)
        return {"status": "error", "message": f"予期せぬエラー: {str(e)}"}

@app.get("/svn/explore")
async def explore_repo(
    repo_url: str,
    file_types: str = "txt,pdf,docx,md"
):
    """SVNリポジトリ探索"""
    logger.info(f"SVN explore request - repo: {repo_url}, types: {file_types}")
    try:
        allowed_types = file_types.split(",")
        results = []

        def explore(path):
            # svn listコマンドを実行
            result = subprocess.run(
                ["svn", "list", "--xml", path],
                capture_output=True,
                text=True,
                check=True
            )
            
            # XMLをパースしてエントリを処理
            import xml.etree.ElementTree as ET
            root = ET.fromstring(result.stdout)
            for entry in root.findall(".//entry"):
                kind = entry.get("kind")
                name = entry.find("name").text
                url = f"{path}/{name}" if not path.endswith("/") else f"{path}{name}"
                
                if kind == "dir":
                    explore(url)
                else:
                    ext = name.split(".")[-1].lower() if "." in name else ""
                    if ext in allowed_types:
                        size = entry.find("size").text if entry.find("size") is not None else "0"
                        results.append({
                            "path": url,
                            "name": name,
                            "type": ext,
                            "size": int(size)
                        })

        explore(repo_url)
        return {"status": "success", "files": results}
    except subprocess.CalledProcessError as e:
        logger.error(f"SVN explore failed - repo: {repo_url}, error: {e.stderr}")
        return {"status": "error", "message": f"SVN探索エラー: {e.stderr}"}
    except Exception as e:
        logger.error(f"Unexpected error in SVN explore - repo: {repo_url}, error: {str(e)}", exc_info=True)
        return {"status": "error", "message": f"予期せぬエラー: {str(e)}"}

@app.get("/svn/download")
async def download_file(
    file_url: str,
    chunk_size: int = 1024 * 1024  # 1MB chunks
):
    """SVNファイルダウンロード"""
    logger.info(f"SVN download request - file: {file_url}")
    try:
        # ファイル情報取得
        info_result = subprocess.run(
            ["svn", "info", "--xml", file_url],
            capture_output=True,
            text=True,
            check=True
        )
        
        # XMLをパースしてファイル情報を取得
        import xml.etree.ElementTree as ET
        root = ET.fromstring(info_result.stdout)
        entry = root.find(".//entry")
        file_name = entry.find("name").text
        file_size = entry.find("size").text if entry.find("size") is not None else "0"
        
        # ストリームダウンロード
        def generate():
            process = subprocess.Popen(
                ["svn", "cat", file_url],
                stdout=subprocess.PIPE,
                text=False
            )
            while True:
                chunk = process.stdout.read(chunk_size)
                if not chunk:
                    break
                yield chunk
            process.stdout.close()
            process.wait()

        return StreamingResponse(
            generate(),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{file_name}"',
                "Content-Length": file_size
            }
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"SVN download failed - file: {file_url}, error: {e.stderr}")
        return {"status": "error", "message": f"ダウンロードエラー: {e.stderr}"}
    except Exception as e:
        logger.error(f"Unexpected error in SVN download - file: {file_url}, error: {str(e)}", exc_info=True)
        return {"status": "error", "message": f"予期せぬエラー: {str(e)}"}

@app.get("/svn/log")
async def get_svn_log(
    repo_url: str,
    limit: int = 10
):
    """SVNログ取得"""
    logger.info(f"SVN log request - repo: {repo_url}, limit: {limit}")
    try:
        # svn logコマンドを実行
        result = subprocess.run(
            ["svn", "log", "--xml", "--limit", str(limit), repo_url],
            capture_output=True,
            text=True,
            check=True
        )
        
        # XMLをパースしてログを取得
        import xml.etree.ElementTree as ET
        root = ET.fromstring(result.stdout)
        logs = []
        for logentry in root.findall(".//logentry"):
            logs.append({
                "revision": logentry.get("revision"),
                "author": logentry.find("author").text,
                "date": logentry.find("date").text,
                "msg": logentry.find("msg").text if logentry.find("msg") is not None else ""
            })
            
        return {"status": "success", "logs": logs}
    except subprocess.CalledProcessError as e:
        logger.error(f"SVN log failed - repo: {repo_url}, error: {e.stderr}")
        return {"status": "error", "message": f"ログ取得エラー: {e.stderr}"}
    except Exception as e:
        logger.error(f"Unexpected error in SVN log - repo: {repo_url}, error: {str(e)}", exc_info=True)
        return {"status": "error", "message": f"予期せぬエラー: {str(e)}"}

@app.get("/svn/diff")
async def get_svn_diff(
    repo_url: str,
    start_version: str,
    end_version: str = None
):
    """SVN差分取得"""
    logger.info(f"SVN diff request - repo: {repo_url}, versions: {start_version}..{end_version}")
    try:
        # svn diffコマンドを実行
        cmd = ["svn", "diff", "-r", start_version]
        if end_version:
            cmd.append(end_version)
        cmd.append(repo_url)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return {"status": "success", "diff": result.stdout}
    except subprocess.CalledProcessError as e:
        logger.error(f"SVN diff failed - repo: {repo_url}, error: {e.stderr}")
        return {"status": "error", "message": f"差分取得エラー: {e.stderr}"}
    except Exception as e:
        logger.error(f"Unexpected error in SVN diff - repo: {repo_url}, error: {str(e)}", exc_info=True)
        return {"status": "error", "message": f"予期せぬエラー: {str(e)}"}

@app.get("/svn/numstat")
async def get_svn_numstat(
    repo_url: str,
    start_version: str,
    end_version: str = None
):
    """SVN変更行数統計"""
    logger.info(f"SVN numstat request - repo: {repo_url}, versions: {start_version}..{end_version}")
    try:
        # svn diff --summarizeコマンドを実行
        cmd = ["svn", "diff", "--summarize", "-r", start_version]
        if end_version:
            cmd.append(end_version)
        cmd.append(repo_url)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # 結果をパース
        numstat = []
        for line in result.stdout.splitlines():
            if line:
                parts = line.split()
                if len(parts) >= 4:
                    numstat.append({
                        "status": parts[0],
                        "path": parts[3],
                        "changes": parts[1] if len(parts) > 1 else "0",
                        "additions": parts[2] if len(parts) > 2 else "0"
                    })
        
        return {"status": "success", "numstat": numstat}
    except subprocess.CalledProcessError as e:
        logger.error(f"SVN numstat failed - repo: {repo_url}, error: {e.stderr}")
        return {"status": "error", "message": f"統計取得エラー: {e.stderr}"}
    except Exception as e:
        logger.error(f"Unexpected error in SVN numstat - repo: {repo_url}, error: {str(e)}", exc_info=True)
        return {"status": "error", "message": f"予期せぬエラー: {str(e)}"}
