import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { getDocument } from '../services/api';
import ErrorBoundary from './ErrorBoundary';
import { Card, Spin, Alert } from 'antd';
import { EyeOutlined, DownloadOutlined } from '@ant-design/icons';
import { Button } from 'antd';

interface MarkdownViewerProps {
  documentId: string;
}

interface DocumentMetadata {
  id: string;
  title: string;
  updated_at: string;
  url: string;
  pdf_name?: string | null;
}

const MarkdownViewer = ({ documentId }: MarkdownViewerProps) => {
  const [markdownContent, setMarkdownContent] = useState<string>('');
  const [metadata, setMetadata] = useState<DocumentMetadata | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDocumentContent = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // 1回のAPI呼び出しでメタデータとコンテンツの両方を取得
        const documentData = await getDocument(documentId, true);
        setMetadata(documentData);
        setMarkdownContent(documentData.content || '');
      } catch (err) {
        console.error('マークダウン読み込みエラー:', err);
        setError('マークダウンの読み込みに失敗しました');
      } finally {
        setLoading(false);
      }
    };
    
    fetchDocumentContent();
  }, [documentId]);

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: 'calc(100vh - 200px)' 
      }}>
        <Spin size="large" tip="マークダウンを読み込み中..." />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: 'calc(100vh - 200px)',
        padding: '20px'
      }}>
        <Alert
          message="エラー"
          description={error}
          type="error"
          showIcon
        />
      </div>
    );
  }

  return (
    <div style={{ flexGrow: 1, height: 'calc(100vh - 200px)' }}>
      {metadata && (
        <Card 
          style={{ marginBottom: '16px' }}
          title={metadata.title}
          extra={
            <div>
              <Button 
                icon={<EyeOutlined />}
                style={{ marginRight: 8 }}
                onClick={() => window.open(`/documents/${documentId}?view=pdf`, '_blank')}
              >
                PDFを表示
              </Button>
              <Button 
                icon={<DownloadOutlined />}
                onClick={() => window.open(metadata.url)}
              >
                ダウンロード
              </Button>
            </div>
          }
        >
          <div style={{ marginBottom: '8px' }}>
            <strong>Source URL:</strong> {metadata.url}
          </div>
          <div style={{ color: '#666', fontSize: '0.9em' }}>
            <strong>最終更新:</strong> {new Date(metadata.updated_at).toLocaleString()}
          </div>
        </Card>
      )}
      
      <div style={{ 
        width: '100%',
        height: 'calc(100vh - 300px)',
        overflowY: 'auto',
        padding: '20px',
        border: '1px solid #d9d9d9',
        borderRadius: '6px',
        backgroundColor: '#fff'
      }}>
        <div className="markdown-content">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              table: (props) => (
                <table className="markdown-table" {...props} />
              ),
              th: (props) => (
                <th className="markdown-table-header" {...props} />
              ),
              td: ({ children, ...props }) => {
                // テキスト内の改行を<br>タグに変換
                const processLineBreaks = (content: React.ReactNode): React.ReactNode => {
                  if (typeof content === 'string') {
                    console.log("content: " + content)
                    console.log(content.split("\\n"))
                    console.log(content.split("¥n"))
                    return content.split('\\n').map((line, index, array) => {
                      console.log("line: " + line)
                      return(
                      <span key={index}>
                        {line}
                        {index < array.length - 1 && <br />}
                      </span>
                    )});
                  }
                  if (Array.isArray(content)) {
                    return content.map((item, index) => (
                      <span key={index}>{processLineBreaks(item)}</span>
                    ));
                  }
                  return content;
                };
                
                return (
                  <td className="markdown-table-cell" {...props}>
                    {processLineBreaks(children)}
                  </td>
                );
              }
            }}
          >
            {markdownContent}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
};

const MarkdownViewerWithErrorBoundary = ({ documentId }: { documentId: string }) => (
  <ErrorBoundary>
    <MarkdownViewer documentId={documentId} />
  </ErrorBoundary>
);

export default MarkdownViewerWithErrorBoundary;
