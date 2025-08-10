import DocumentMetadata from './DocumentMetadata';
import PDFViewer from './PDFViewer';
import { useParams } from 'react-router-dom';

const DetailPage = () => {
  const { id } = useParams();

  if (!id) return null;

  return (
    <>
      <DocumentMetadata documentId={id} />
      <PDFViewer documentId={id} />
    </>
  );
};

export default DetailPage;
