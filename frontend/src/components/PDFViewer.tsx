import { useState } from 'react';
import { getPDF } from '../services/api';

const PDFViewer = ({ filename }: { filename: string }) => {
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPDF = async () => {
    try {
      setLoading(true);
      setError(null);
      const pdfBlob = await getPDF(filename);
      const url = URL.createObjectURL(pdfBlob);
      setPdfUrl(url);
    } catch (err) {
      setError('PDFの取得に失敗しました');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button 
        onClick={fetchPDF}
        disabled={loading}
        className="px-4 py-2 bg-blue-500 text-white rounded"
      >
        {loading ? '読み込み中...' : 'PDFを表示'}
      </button>

      {error && <p className="text-red-500 mt-2">{error}</p>}

      {pdfUrl && (
        <div className="mt-4">
          <iframe 
            src={pdfUrl}
            width="100%"
            height="600px"
            title="PDF Viewer"
            className="border"
          />
          <div className="mt-2">
            <a 
              href={pdfUrl} 
              download={`${filename}.pdf`}
              className="text-blue-500 underline"
            >
              PDFをダウンロード
            </a>
          </div>
        </div>
      )}
    </div>
  );
};

export default PDFViewer;
