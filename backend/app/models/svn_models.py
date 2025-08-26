from typing import Optional
from pydantic import BaseModel

class SVNExploreRequest(BaseModel):
    """SVNリポジトリ探索リクエストモデル"""
    repo_url: str
    file_types: str = "txt,pdf,docx,md,xlsx,xls"  # デフォルトでサポートするファイルタイプ
    username: Optional[str] = None
    password: Optional[str] = None
    ip_address: Optional[str] = None

class SVNImportRequest(BaseModel):
    """SVNリソースインポートリクエストモデル"""
    url: str
    username: Optional[str] = None
    password: Optional[str] = None
    ip_address: Optional[str] = None
