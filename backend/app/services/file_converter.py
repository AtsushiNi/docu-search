from markitdown import MarkItDown
import re
import os
import requests

CONVERTIBLE_EXTS = ['docx', 'pptx', 'xlsx', 'xls', 'xlsm']
PDF_CONVERTIBLE_EXTS = ['xlsx', 'xls', 'xlsb', 'xlsm', 'docx', 'doc']
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
        content = result.text_content
        content = cls._clean_markdown_content(content)
        return content

    @classmethod
    def is_pdf_convertible(cls, file_name: str) -> bool:
        """ファイルがPDFに変換可能か判定"""
        ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
        return ext in PDF_CONVERTIBLE_EXTS

    @classmethod
    def convert_to_pdf_and_save(cls, file_path: str) -> str:
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

        return output_file_path

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

    @classmethod
    def _clean_markdown_content(cls, content: str) -> str:
        """マークダウンコンテンツをクリーンアップし、表を抽出"""
        # まず表を抽出して個別に処理
        tables = cls._extract_tables(content)
        
        # 抽出した表を修正して元のコンテンツに反映
        if tables:
            # 表を修正（後ろから処理して位置情報がずれないように）
            for table in reversed(tables):
                cleaned_table = cls._clean_table_data(table)
                # 修正した表で元のコンテンツを置換
                start = table['start_pos']
                end = table['end_pos']
                content = content[:start] + cleaned_table + content[end:]
        
        # 余分な空白行を削除
        content = re.sub(r'\n\s*\n', '\n\n', content)
        # 先頭と末尾の空白を削除
        content = content.strip()

        return content

    @classmethod
    def _extract_tables(cls, content: str) -> list:
        """マークダウンコンテンツから表を抽出"""
        tables = []
        
        # マークダウン表のパターン: ヘッダ行 + 区切り行 + データ行
        table_pattern = r'(\|.*\|\s*\n\|[-:| ]+\|\s*\n(?:\|.*\|\s*(?:\n|$))*)'
        matches = re.finditer(table_pattern, content, re.MULTILINE)
        
        for match in matches:
            table_content = match.group(0).strip()
            table_data = cls._parse_markdown_table(table_content)
            if table_data:
                tables.append({
                    'content': table_content,
                    'headers': table_data['headers'],
                    'rows': table_data['rows'],
                    'start_pos': match.start(),
                    'end_pos': match.end()
                })
        
        return tables

    @classmethod
    def _parse_markdown_table(cls, table_content: str) -> dict:
        """マークダウン表を解析してヘッダとデータ行に分割"""
        lines = table_content.strip().split('\n')
        if len(lines) < 2:
            return None
        
        # 区切り行を探す（|---|形式）
        separator_index = -1
        for i, line in enumerate(lines):
            if re.match(r'^\|[-:| ]+\|$', line.strip()):
                separator_index = i
                break
        
        if separator_index == -1:
            return None
        
        # ヘッダ行とデータ行を分離
        headers = []
        rows = []
        
        # ヘッダ行の処理
        if separator_index > 0:
            header_line = lines[separator_index - 1].strip()
            headers = [cell.strip() for cell in header_line.split('|')[1:-1]]
        
        # データ行の処理
        for i in range(separator_index + 1, len(lines)):
            data_line = lines[i].strip()
            if data_line and data_line.startswith('|') and data_line.endswith('|'):
                row_data = [cell.strip() for cell in data_line.split('|')[1:-1]]
                rows.append(row_data)
        
        return {'headers': headers, 'rows': rows}

    @classmethod
    def _clean_table_data(cls, table: dict) -> str:
        """表データをクリーンアップしてマークダウン形式で返す"""
        headers = table['headers']
        rows = table['rows']
        
        # ヘッダと行データをクリーンアップ
        cleaned_headers = cls._clean_row_data(headers)
        cleaned_rows = [cls._clean_row_data(row) for row in rows]
        
        # 空白の行を削除
        cleaned_rows = [row for row in cleaned_rows if any(cell.strip() for cell in row)]
        
        # 空白の列を削除（すべての行が空白の列を特定）
        if cleaned_rows:
            empty_columns = []
            for col_idx in range(len(cleaned_headers)):
                # ヘッダが空白で、すべての行のその列も空白かチェック
                header_empty = not cleaned_headers[col_idx].strip()
                all_rows_empty = all(
                    len(row) > col_idx and not row[col_idx].strip() 
                    for row in cleaned_rows
                )
                if header_empty and all_rows_empty:
                    empty_columns.append(col_idx)
            
            # 後ろから削除してインデックスがずれないように
            for col_idx in reversed(empty_columns):
                # ヘッダから削除
                if col_idx < len(cleaned_headers):
                    cleaned_headers.pop(col_idx)
                # 各行から削除
                for row in cleaned_rows:
                    if col_idx < len(row):
                        row.pop(col_idx)
        
        # マークダウン表形式に変換
        markdown_table = []
        
        # ヘッダ行
        if cleaned_headers:
            header_line = "| " + " | ".join(cleaned_headers) + " |"
            markdown_table.append(header_line)
        
        # 区切り行
        if cleaned_headers:
            separator_line = "| " + " | ".join(["---"] * len(cleaned_headers)) + " |"
            markdown_table.append(separator_line)
        
        # データ行
        for row in cleaned_rows:
            if row:  # 空行でないことを確認
                data_line = "| " + " | ".join(row) + " |"
                markdown_table.append(data_line)
        
        return "\n".join(markdown_table) + "\n"

    @classmethod
    def _clean_row_data(cls, row: list) -> list:
        """行データの各セルをクリーンアップ"""
        cleaned_row = []
        for cell in row:
            # NaNを空白に変換
            if cell == 'NaN':
                cleaned_cell = ''
            # "Unnamed: 数字"形式を空白に変換
            elif re.match(r'^Unnamed:\s*\d+$', cell, re.IGNORECASE):
                cleaned_cell = ''
            else:
                cleaned_cell = cell
            cleaned_row.append(cleaned_cell)
        return cleaned_row
