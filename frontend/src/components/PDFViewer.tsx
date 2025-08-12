import { useState, useEffect, useCallback } from 'react';
import { useResizeObserver } from '@wojtekmaj/react-hooks';
import { pdfjs, Document, Page } from 'react-pdf';
import type { PDFDocumentProxy } from 'pdfjs-dist';
import { getPDF } from '../services/api';
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
        const pdfBlob = await getPDF(documentId);
        const url = URL.createObjectURL(pdfBlob);
        setPdfUrl(url);
      } catch (err) {
        console.error(err);
      }
    };
    fetchPDF();
  }, [documentId]);

  function onDocumentLoadSuccess({ numPages: nextNumPages }: PDFDocumentProxy): void {
    setNumPages(nextNumPages);
  }

  return (
    <div style={{ flexGrow: 1, height: 'calc(100vh - 200px)' }}>
      {pdfUrl && (
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
            <Document file={pdfUrl} onLoadSuccess={onDocumentLoadSuccess}>
              {Array.from(new Array(numPages), (_el, index) => (
                <div style={{ margin: '1em 0' }}>
                  <Page
                    key={`page_${index + 1}`}
                    pageNumber={index + 1}
                    width={containerWidth ? Math.min(containerWidth, maxWidth) : maxWidth}
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

export default PDFViewer;
