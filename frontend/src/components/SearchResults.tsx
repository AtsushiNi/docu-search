import type { SearchResult } from '../types';
import React from 'react';
import { Button, Card, Row, Col, Space, Layout, Affix } from 'antd';
import { DownloadOutlined, EyeOutlined } from '@ant-design/icons';
import { Link, Element } from 'react-scroll';
import './SearchResults.css';

interface SearchResultsProps {
  results: SearchResult[];
}

const SearchResults: React.FC<SearchResultsProps> = ({ results }) => {

  if (results.length === 0) {
    return <div className="text-gray-500">No results found</div>;
  }

  return (
    <Layout style={{ marginTop: 20 }}>
      <Layout.Content style={{ 
        paddingRight: '24px', 
        minHeight: 280,
        height: 'calc(100vh - 180px)', // 固定検索バー分を考慮した高さ（約120px + 余白）
        overflowY: 'auto' // コンテンツエリアのみスクロール可能に
      }}>
        <div id="search-results-container">
          <Space direction='vertical' size="large" style={{width: "100%"}}>
            {results.map((result, index) => (
              <Element key={result._id} name={`result-${index}`}>
                <Card 
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
              </Element>
            ))}
          </Space>
        </div>
      </Layout.Content>
      
      <Layout.Sider 
        width={300} 
        style={{ 
          background: '#fff',
          padding: '16px',
          borderLeft: '1px solid #f0f0f0'
        }}
      >
        <Affix offsetTop={80}>
          <div>
            <h3 style={{ marginBottom: '16px', color: '#262626' }}>検索結果一覧</h3>
            {results.map((result, index) => (
              <Link
                key={result._id}
                to={`result-${index}`}
                spy={true}
                smooth={true}
                duration={500}
                offset={-80}
                className="scrollspy-item"
                activeClass="scrollspy-current"
              >
                <div className="scrollspy-title">
                  {result._source.name}
                </div>
                <div className="scrollspy-date">
                  {new Date(result._source.updated_at).toLocaleDateString()}
                </div>
              </Link>
            ))}
          </div>
        </Affix>
      </Layout.Sider>
    </Layout>
  );
};

export default SearchResults;
