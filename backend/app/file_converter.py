from markitdown import MarkItDown
from typing import Optional
from fastapi import HTTPException

CONVERTIBLE_EXTS = ['docx', 'pptx', 'xlsx', 'xls']

class FileConverter:
    def __init__(self):
        self.markitdown = MarkItDown()

    def is_convertible(self, file_name: str) -> bool:
        """ファイルが変換可能か判定"""
        ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
        return ext in CONVERTIBLE_EXTS

    def convert_to_markdown(self, file_path: str) -> str:
        """ファイルをマークダウンに変換"""
        try:
            result = self.markitdown.convert(file_path)
            return result.text_content
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to convert file: {str(e)}"
            )

    def get_markdown_filename(self, original_path: str) -> str:
        """元のファイル名からマークダウンファイル名を生成"""
        return original_path.rsplit('.', 1)[0] + '.md'
