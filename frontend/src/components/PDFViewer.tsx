import { useState, useEffect, useCallback } from 'react';
import { useResizeObserver } from '@wojtekmaj/react-hooks';
import { pdfjs, Document, Page } from 'react-pdf';
import type { PDFDocumentProxy } from 'pdfjs-dist';
import { getPDF, getDocument } from '../services/api';
import ErrorBoundary from './ErrorBoundary';
import { Card, Button } from 'antd';
import { EyeOutlined, DownloadOutlined } from '@ant-design/icons';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

const API_BASE_URL = 'http://localhost:8000';

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString();

const resizeObserverOptions = {};
const maxWidth = 10000;

interface DocumentMetadata {
  id: string;
  title: string;
  updated_at: string;
  url: string;
  pdf_name?: string | null;
  file_path?: string | null;
}

const PDFViewer = ({ documentId }: { documentId: string }) => {
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [numPages, setNumPages] = useState<number>();
  const [containerRef, setContainerRef] = useState<HTMLElement | null>(null);
  const [containerWidth, setContainerWidth] = useState<number>();
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<DocumentMetadata | null>(null);
  const [metadataLoading, setMetadataLoading] = useState<boolean>(true);

  const onResize = useCallback<ResizeObserverCallback>((entries) => {
    const [entry] = entries;

    if (entry) {
      setContainerWidth(entry.contentRect.width);
    }
  }, []);

  useResizeObserver(containerRef, resizeObserverOptions, onResize);

  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        setMetadataLoading(true);
        const data = await getDocument(documentId, false);
        setMetadata(data);
      } catch (err) {
        console.error('メタデータ取得エラー:', err);
      } finally {
        setMetadataLoading(false);
      }
    };

    const fetchPDF = async () => {
      try {
        setLoading(true);
        setError(null);
        const pdfBlob = await getPDF(documentId);
        const url = URL.createObjectURL(pdfBlob);
        setPdfUrl(url);
      } catch (err) {
        console.error('PDF読み込みエラー:', err);
        setError('PDFの読み込みに失敗しました');
      } finally {
        setLoading(false);
      }
    };

    fetchMetadata();
    fetchPDF();

    // コンポーネントアンマウント時にBlob URLを解放
    return () => {
      if (pdfUrl) {
        URL.revokeObjectURL(pdfUrl);
      }
    };
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

  function onDocumentLoadSuccess({ numPages: nextNumPages }: PDFDocumentProxy): void {
    setNumPages(nextNumPages);
  }

  return (
    <div style={{ flexGrow: 1, height: 'calc(100vh - 200px)' }}>
      {metadata && !metadataLoading && (
        <Card 
          style={{ marginBottom: '16px' }}
          title={metadata.title}
          extra={
            <div>
              <Button 
                icon={<EyeOutlined />}
                style={{ marginRight: 8 }}
                onClick={() => window.open(`/documents/${documentId}?view=markdown`, '_blank')}
              >
                マークダウンを表示
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
      
      {loading && (
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '100%' 
        }}>
          <div>PDFを読み込み中...</div>
        </div>
      )}
      
      {error && (
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '100%',
          color: 'red'
        }}>
          <div>{error}</div>
        </div>
      )}

      {pdfUrl && !loading && !error && (
        <div style={{ 
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          margin: '10px 0',
          padding: '10px'
        }}>
          <div style={{ 
            width: '100%',
            height: 'calc(100vh - 300px)',
            overflowY: 'scroll',
            maxWidth: 'calc(100% - 2em)',
            margin: '1em 0',
            padding: 10,
            border: 'solid 1px silver'
          }} ref={setContainerRef}>
            <Document 
              file={pdfUrl} 
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={(error) => {
                console.error('PDF表示エラー:', error);
                setError('PDFの表示に失敗しました');
              }}
            >
              {Array.from(new Array(numPages), (_el, index) => (
                <div key={`page_container_${index + 1}`} style={{ margin: '1em 0' }}>
                  <Page
                    key={`page_${index + 1}`}
                    pageNumber={index + 1}
                    width={containerWidth ? Math.min(containerWidth, maxWidth) : maxWidth}
                    loading="PDFページを読み込み中..."
                  />
                </div>
              ))}
            </Document>
          </div>
        </div>
      )}
    </div>
  );
};

const PDFViewerWithErrorBoundary = ({ documentId }: { documentId: string }) => (
  <ErrorBoundary>
    <PDFViewer documentId={documentId} />
  </ErrorBoundary>
);

export default PDFViewerWithErrorBoundary;
