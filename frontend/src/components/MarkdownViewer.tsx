import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { getDocument } from '../services/api';
import ErrorBoundary from './ErrorBoundary';
import { Card, Spin, Alert, Tabs } from 'antd';
import { EyeOutlined, DownloadOutlined } from '@ant-design/icons';
import { Button } from 'antd';

const API_BASE_URL = 'http://localhost:8000';

interface MarkdownViewerProps {
  documentId: string;
}

interface DocumentMetadata {
  id: string;
  title: string;
  updated_at: string;
  url: string;
  pdf_name?: string | null;
  file_path?: string | null;
  sections?: Array<{
    title?: string;
    content: string;
  }>;
}

const MarkdownViewer = ({ documentId }: MarkdownViewerProps) => {
  const [metadata, setMetadata] = useState<DocumentMetadata | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('0');

  useEffect(() => {
    const fetchDocumentContent = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // 1回のAPI呼び出しでメタデータとコンテンツの両方を取得
        const documentData = await getDocument(documentId, true);
        setMetadata(documentData);
      } catch (err) {
        console.error('マークダウン読み込みエラー:', err);
        setError('マークダウンの読み込みに失敗しました');
      } finally {
        setLoading(false);
      }
    };
    
    fetchDocumentContent();
  }, [documentId]);

  const handleDownload = () => {
    if (metadata?.file_path) {
      // 保存されたファイルをダウンロード
      window.open(`${API_BASE_URL}/file/${metadata.file_path}`, '_blank');
    } else {
      // 元のURLを開く
      window.open(metadata?.url);
    }
  };

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
                onClick={handleDownload}
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
      
      {metadata?.sections && metadata.sections.length > 0 ? (
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          type="card"
          style={{ 
            height: 'calc(100vh - 300px)',
            display: 'flex',
            flexDirection: 'column'
          }}
          items={metadata.sections.map((section, index) => ({
            key: index.toString(),
            label: section.title || `セクション ${index + 1}`,
            children: (
              <div style={{ 
                height: 'calc(100vh - 400px)',
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
                            return content.split('\\n').map((line, index, array) => (
                              <span key={index}>
                                {line}
                                {index < array.length - 1 && <br />}
                              </span>
                            ));
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
                    {section.content}
                  </ReactMarkdown>
                </div>
              </div>
            )
          }))}
        />
      ) : (
        <div style={{ 
          width: '100%',
          height: 'calc(100vh - 300px)',
          overflowY: 'auto',
          padding: '20px',
          border: '1px solid #d9d9d9',
          borderRadius: '6px',
          backgroundColor: '#fff',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center'
        }}>
          <Alert
            message="コンテンツなし"
            description="このドキュメントには表示可能なセクションがありません"
            type="info"
            showIcon
          />
        </div>
      )}
    </div>
  );
};

const MarkdownViewerWithErrorBoundary = ({ documentId }: { documentId: string }) => (
  <ErrorBoundary>
    <MarkdownViewer documentId={documentId} />
  </ErrorBoundary>
);

export default MarkdownViewerWithErrorBoundary;
