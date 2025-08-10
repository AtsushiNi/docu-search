import { useState, useEffect } from 'react';
import { getDocumentMetadata } from '../services/api';
import { Descriptions, Spin, Alert } from 'antd';

interface DocumentMetadata {
  id: string;
  title: string;
  updated_at: string;
  url: string;
  pdf_name?: string;
}

const DocumentMetadata = ({ documentId }: { documentId: string }) => {
  const [metadata, setMetadata] = useState<DocumentMetadata | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await getDocumentMetadata(documentId);
        setMetadata(data);
      } catch (err) {
        setError('メタデータの取得に失敗しました');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (documentId) {
      fetchMetadata();
    }
  }, [documentId]);

  if (loading) return <Spin size="large" />;
  if (error) return <Alert message={error} type="error" showIcon />;
  if (!metadata) return null;

  return (
    <div style={{ marginBottom: '24px' }}>
      <h2 style={{ marginBottom: '16px' }}>{metadata.title}</h2>
      <Descriptions>
        <Descriptions.Item label="URL"><a href={metadata.url} target="_blank" rel="noopener noreferrer">{metadata.url}</a></Descriptions.Item>
        <Descriptions.Item label="更新日時">{new Date(metadata.updated_at).toLocaleString()}</Descriptions.Item>
      </Descriptions>
    </div>
  );
};

export default DocumentMetadata;
