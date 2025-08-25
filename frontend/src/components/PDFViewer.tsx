import { useState, useEffect, useCallback } from 'react';
import { useResizeObserver } from '@wojtekmaj/react-hooks';
import { pdfjs, Document, Page } from 'react-pdf';
import type { PDFDocumentProxy } from 'pdfjs-dist';
import { getPDF } from '../services/api';
import ErrorBoundary from './ErrorBoundary';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString();

const resizeObserverOptions = {};
const maxWidth = 10000;

const PDFViewer = ({ documentId }: { documentId: string }) => {
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [numPages, setNumPages] = useState<number>();
  const [containerRef, setContainerRef] = useState<HTMLElement | null>(null);
  const [containerWidth, setContainerWidth] = useState<number>();
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const onResize = useCallback<ResizeObserverCallback>((entries) => {
    const [entry] = entries;

    if (entry) {
      setContainerWidth(entry.contentRect.width);
    }
  }, []);

  useResizeObserver(containerRef, resizeObserverOptions, onResize);

  useEffect(() => {
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
    fetchPDF();

    // コンポーネントアンマウント時にBlob URLを解放
    return () => {
      if (pdfUrl) {
        URL.revokeObjectURL(pdfUrl);
      }
    };
  }, [documentId]);

  function onDocumentLoadSuccess({ numPages: nextNumPages }: PDFDocumentProxy): void {
    setNumPages(nextNumPages);
  }

  return (
    <div style={{ flexGrow: 1, height: 'calc(100vh - 200px)' }}>
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
            height: 'calc(100vh - 200px)',
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
