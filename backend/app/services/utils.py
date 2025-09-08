import hashlib
import base64

def url_to_id(url: str) -> str:
    """
    リソースのURLから一意なIDを生成
    
    Args:
        url: リソースのURL
    
    Returns:
        str: URL-safeなBase64エンコードされたSHA-256ハッシュ値
    """
    # URLをUTF-8でバイト列に変換
    url_bytes = url.encode('utf-8')
    # SHA-256でハッシュ
    digest = hashlib.sha256(url_bytes).digest()
    # URL-safeなBase64に変換し、パディング(=)を除去
    return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip("=")
