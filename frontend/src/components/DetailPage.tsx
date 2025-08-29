import PDFViewer from './PDFViewer';
import MarkdownViewer from './MarkdownViewer';
import { useParams, useSearchParams } from 'react-router-dom';

const DetailPage = () => {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const viewType = searchParams.get('view') || 'pdf';

  if (!id) return null;

  return (
    <>
      {viewType === 'markdown' ? (
        <MarkdownViewer documentId={id} />
      ) : (
        <PDFViewer documentId={id} />
      )}
    </>
  );
};

export default DetailPage;
