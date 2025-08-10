from markitdown import MarkItDown
import re
import os
import requests

CONVERTIBLE_EXTS = ['docx', 'pptx', 'xlsx', 'xls', 'xlsm']
PDF_CONVERTIBLE_EXTS = ['xlsx', 'xls', '.xlsb', '.xlsm', 'docs', 'doc']
OLD_WORD_EXTS = ['doc']

class FileConverter:
    markitdown = MarkItDown()

    @classmethod
    def is_convertible(cls, file_name: str) -> bool:
        """ファイルが変換可能か判定"""
        ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
        return ext in CONVERTIBLE_EXTS

    @classmethod
    def convert_to_markdown(cls, file_path: str) -> str:
        """ファイルをマークダウンに変換"""
        result = cls.markitdown.convert(file_path)
        content = result.text_content.replace(" NaN |", " |") # 変換で生じる無駄なNaNを削除
        return re.sub(r'^\s*\|+\s*(\|\s*)*$\n?', '', content, flags=re.MULTILINE) # 空行を削除

    @classmethod
    def get_markdown_filename(cls, original_path: str) -> str:
        """元のファイル名からマークダウンファイル名を生成"""
        return original_path.rsplit('.', 1)[0] + '.md'

    @classmethod
    def is_pdf_convertible(cls, file_name: str) -> bool:
        """ファイルがPDFに変換可能か判定"""
        ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
        return ext in PDF_CONVERTIBLE_EXTS

    @classmethod
    def convert_to_pdf_and_save(cls, file_path: str) -> None:
        """OfficeファイルをPDFに変換して保存"""
        # PDF保存ディレクトリが存在しない場合は作成
        pdf_dir = "/var/lib/pdf_storage" # PDF保存用のDockerボリューム
        os.makedirs(pdf_dir, exist_ok=True)
        # PDFファイル名はdoc_id(元ファイルのURLから生成したハッシュ値)
        doc_id = os.path.splitext(os.path.basename(file_path))[0]
        output_file_path = os.path.join(pdf_dir, f"{doc_id}.pdf")
        
        with open(file_path, 'rb') as f:
            response = requests.post(
                'http://unoserver:2004/request',
                files={'file': f},
                data={'convert-to': 'pdf'},
                stream=True
            )
            response.raise_for_status()
            with open(output_file_path, 'wb') as out_f:
                for chunk in response.iter_content(chunk_size=8192):
                    out_f.write(chunk)

        return doc_id

    @classmethod
    def is_old_office_file(cls, file_path: str) -> bool:
        """古い形式のOfficeファイルか判定"""
        ext = file_path.split('.')[-1].lower() if '.' in file_path else ''
        return ext in OLD_WORD_EXTS

    @classmethod
    def convert_to_valid_office_file(cls, file_path: str) -> None:
        """使用できるOfficeファイル形式に変換"""

        # .docを.docxに変換
        new_file_path = os.path.splitext(file_path)[0] + '.docx'
        with open(file_path, 'rb') as f:
            response = requests.post(
                'http://unoserver:2004/request',
                files={'file': f},
                data={'convert-to': 'docx'},
                stream=True
            )
            response.raise_for_status()
            with open(new_file_path, 'wb') as out_f:
                for chunk in response.iter_content(chunk_size=8192):
                    out_f.write(chunk)

        return new_file_path
