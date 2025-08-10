import { useState, useEffect } from 'react';
import { getPDF } from '../services/api';

const PDFViewer = ({ documentId }: { documentId: string }) => {
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
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

  return (
    <div style={{ flexGrow: 1, height: 'calc(100vh - 200px)' }}>
      {pdfUrl && (
        <iframe 
          src={pdfUrl}
          width="100%"
          height="100%"
          title="PDF Viewer"
          className="border-0"
        />
      )}
    </div>
  );
};

export default PDFViewer;
