import type { SearchResult } from '../types';
import React from 'react';
import { Button, Card, Row, Col, Space, Layout, Affix } from 'antd';
import { DownloadOutlined, EyeOutlined } from '@ant-design/icons';
import { Link, Element } from 'react-scroll';
import './SearchResults.css';

const API_BASE_URL = 'http://localhost:8000';

interface SearchResultsProps {
  results: SearchResult[];
}

const SearchResults: React.FC<SearchResultsProps> = ({ results }) => {

  if (results.length === 0) {
    return <div className="text-gray-500">No results found</div>;
  }

  return (
    <Layout style={{ marginTop: 20 }}>
      <Layout.Content
        style={{ 
          paddingRight: '24px', 
          minHeight: 280,
          height: 'calc(100vh - 180px)', // 固定検索バー分を考慮した高さ（約120px + 余白）
        }}
      >
        <div id="search-results-container" style={{height: "calc(100vh - 200px)", overflow: 'scroll'}}>
          <Space direction='vertical' size="large" style={{width: "100%"}}>
            {results.map((result, index) => (
              <Element key={result._id} name={`result-${index}`}>
                <Card 
                  className="w-full"
                  title={
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: 10, marginBottom: 10 }}>
                      <div style={{ fontSize: '16px', fontWeight: 'bold' }}>
                        {result._source.name}
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'row', gap: '8px', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                        <Button 
                          icon={<EyeOutlined/>}
                          color='default'
                          variant='filled'
                          onClick={() => window.open(`/documents/${result._id}`, '_blank')}
                        >
                          PDFを表示
                        </Button>
                        <Button 
                          icon={<EyeOutlined/>}
                          color='default'
                          variant='filled'
                          onClick={() => window.open(`/documents/${result._id}?view=markdown`, '_blank')}
                        >
                          マークダウンを表示
                        </Button>
                        <Button 
                          icon={<DownloadOutlined/>} 
                          color='default' 
                          variant='filled'
                          onClick={() => {
                            if (result._source.file_path) {
                              // 保存されたファイルをダウンロード
                              window.open(`${API_BASE_URL}/file/${result._source.file_path}`, '_blank');
                            } else {
                              // 元のURLを開く
                              window.open(result._source.url);
                            }
                          }}
                        >
                          ダウンロード
                        </Button>
                      </div>
                    </div>
                  }
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
                  {result.highlight?.['sections.content'] || result.highlight?.['sections.title'] ? (
                    <div 
                      dangerouslySetInnerHTML={{ 
                        __html: [
                          ...(result.highlight?.['sections.title'] || []),
                          ...(result.highlight?.['sections.content'] || [])
                        ].join(' ... ').replace(/\s\|/g, "") 
                      }} 
                    />
                  ) : (
                    <div className="text-gray-700">
                      {result._source.sections?.[0]?.content?.substring(0, 200) || '内容がありません'}...
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
            <Row style={{ flexDirection: 'column' }}>
              {results.map((result, index) => (
                <Col key={index} span={24}>
                  <Link
                    to={`result-${index}`}
                    smooth={true}
                    duration={500}
                    offset={-80}
                    containerId="search-results-container"
                    className="scrollspy-item"
                    activeClass="scrollspy-current"
                    spy={true}
                  >
                    <div className="scrollspy-title">
                      {result._source.name}
                    </div>
                    <div className="scrollspy-date">
                      {new Date(result._source.updated_at).toLocaleDateString()}
                    </div>
                  </Link>
                </Col>
              ))}
            </Row>
          </div>
        </Affix>
      </Layout.Sider>
    </Layout>
  );
};

export default SearchResults;
