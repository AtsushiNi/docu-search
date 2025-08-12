import type { SearchResult } from '../types';
import React from 'react';
import { Button, Card, Row, Col, Space } from 'antd';
import { DownloadOutlined, EyeOutlined } from '@ant-design/icons';

interface SearchResultsProps {
  results: SearchResult[];
}

const SearchResults: React.FC<SearchResultsProps> = ({ results }) => {
  if (results.length === 0) {
    return <div className="text-gray-500">No results found</div>;
  }

  return (
    <div>
      <Space direction='vertical' size="large" style={{width: "100%"}}>
        {results.map((result) => (
          <Card 
            key={result._id}
            className="w-full"
            title={result._source.name}
            extra={<>
              <Button 
                icon={<EyeOutlined/>}
                color='default'
                variant='filled'
                onClick={() => window.open(`/documents/${result._id}`, '_blank')}
                style={{ marginRight: 8 }}
              >
                PDFを表示
              </Button>
              <Button 
                icon={<DownloadOutlined/>} 
                color='default' 
                variant='filled'
                onClick={() => window.open(result._source.url)}
              >
                ダウンロード
              </Button>
            </>}
          >
            <Card.Meta
              description={
                <div style={{ marginBottom: '4px' }}>
                  <Row gutter={8}>
                    <Col span={2} className="text-sm text-gray-600">Source URL:</Col>
                    <Col span={18} className="text-sm text-gray-600">{result._source.url}</Col>
                  </Row>
                  <Row gutter={8}>
                    <Col span={2} className="text-xs text-gray-500">Last updated:</Col>
                    <Col span={18} className="text-xs text-gray-500">
                      {new Date(result._source.updated_at).toLocaleString()}
                    </Col>
                  </Row>
                </div>
              }
            />
            <div className="mt-4">
              {result.highlight?.content ? (
                <div 
                  dangerouslySetInnerHTML={{ 
                    __html: result.highlight.content.join(' ... ').replace(/\s\|/g, "") 
                  }} 
                />
              ) : (
                <div className="text-gray-700">
                  {result._source.content.substring(0, 200)}...
                </div>
              )}
            </div>
          </Card>
        ))}
      </Space>
    </div>
  );
};

export default SearchResults;
